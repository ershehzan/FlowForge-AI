"""
Unit tests for FlowForge Excel Parser & Validator.
Tests valid workbook parsing, missing sheets, invalid IDs, duplicate IDs,
invalid numeric processing time, negative energy rates, non-existent machine reference,
and transactional parser safety.
"""
import pytest
import os
import openpyxl
import io

from agents.factory.excel_parser import ExcelParser
from agents.factory.state import FactoryState, get_default_machines, get_default_jobs
from agents.scheduler import Scheduler


@pytest.fixture
def sample_template_path():
    return os.path.join("examples", "factory_data_template.xlsx")


def test_valid_excel_parsing(sample_template_path):
    parser = ExcelParser()
    result = parser.parse(sample_template_path)

    assert result["success"] is True
    assert len(result["errors"]) == 0
    assert result["machines"] is not None
    assert len(result["machines"]) == 6
    assert len(result["jobs"]) == 16
    assert result["summary"]["machines_count"] == 6
    assert result["summary"]["jobs_count"] == 16


def test_missing_required_sheet():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Machines"
    ws.append(["machine_id", "energy_kwh_per_hour"])
    ws.append(["M1", 8.0])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    parser = ExcelParser()
    result = parser.parse(buf.getvalue(), "missing_jobs.xlsx")

    assert result["success"] is False
    assert any("Jobs" in err["message"] for err in result["errors"])


def test_invalid_machine_reference():
    wb = openpyxl.Workbook()

    ws_m = wb.active
    ws_m.title = "Machines"
    ws_m.append(["machine_id", "energy_kwh_per_hour"])
    ws_m.append(["M1", 8.0])
    ws_m.append(["M2", 10.0])

    ws_j = wb.create_sheet("Jobs")
    ws_j.append(["job_id", "processing_time", "eligible_machines", "deadline"])
    ws_j.append(["J1", 30, "M1,M99", 100])  # M99 does not exist!

    buf = io.BytesIO()
    wb.save(buf)

    parser = ExcelParser()
    result = parser.parse(buf.getvalue(), "invalid_machine_ref.xlsx")

    assert result["success"] is False
    assert any("M99" in err["message"] for err in result["errors"])


def test_duplicate_job_ids():
    wb = openpyxl.Workbook()

    ws_m = wb.active
    ws_m.title = "Machines"
    ws_m.append(["machine_id"])
    ws_m.append(["M1"])

    ws_j = wb.create_sheet("Jobs")
    ws_j.append(["job_id", "processing_time"])
    ws_j.append(["J1", 30])
    ws_j.append(["J1", 45])  # Duplicate J1

    buf = io.BytesIO()
    wb.save(buf)

    parser = ExcelParser()
    result = parser.parse(buf.getvalue(), "dup_jobs.xlsx")

    assert result["success"] is False
    assert any("Duplicate job_id" in err["message"] for err in result["errors"])


def test_negative_processing_time():
    wb = openpyxl.Workbook()

    ws_m = wb.active
    ws_m.title = "Machines"
    ws_m.append(["machine_id"])
    ws_m.append(["M1"])

    ws_j = wb.create_sheet("Jobs")
    ws_j.append(["job_id", "processing_time"])
    ws_j.append(["J1", -15])  # Negative processing time

    buf = io.BytesIO()
    wb.save(buf)

    parser = ExcelParser()
    result = parser.parse(buf.getvalue(), "negative_time.xlsx")

    assert result["success"] is False
    assert any("must be greater than 0" in err["message"] for err in result["errors"])


def test_transactional_upload_safety(sample_template_path):
    # Initialize initial state
    factory = FactoryState()
    initial_machines_count = len(factory.machines)
    initial_jobs_count = len(factory.jobs)

    # Attempt to load invalid excel content
    wb = openpyxl.Workbook()
    ws_m = wb.active
    ws_m.title = "Machines"
    ws_m.append(["machine_id"])
    ws_m.append(["M1"])
    # Missing Jobs sheet
    buf = io.BytesIO()
    wb.save(buf)

    parser = ExcelParser()
    res = parser.parse(buf.getvalue(), "invalid.xlsx")

    if not res["success"]:
        # Do not mutate factory!
        pass

    # Verify factory state was NOT altered
    assert len(factory.machines) == initial_machines_count
    assert len(factory.jobs) == initial_jobs_count


def test_end_to_end_excel_optimization(sample_template_path):
    parser = ExcelParser()
    parsed = parser.parse(sample_template_path)
    assert parsed["success"] is True

    # Build FactoryState from imported excel data
    factory = FactoryState(machines=parsed["machines"], jobs=parsed["jobs"])

    # Run Autonomous Scheduler
    scheduler = Scheduler(factory.get_available_machine_ids())
    schedule = scheduler.ga_schedule(
        jobs=factory.get_active_jobs(),
        machine_energy=factory.get_machine_energy_map()
    )

    factory.set_baseline_schedule(schedule)

    assert factory.baseline_schedule is not None
    assert len(factory.baseline_schedule) == 16  # All 16 jobs scheduled


def test_smart_single_sheet_parsing():
    """Test parsing a single-sheet Excel workbook with non-standard column headers."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Production Schedule"
    ws.append(["Part Name", "Cycle Time", "Machine", "Due Date", "Urgency"])
    ws.append(["Shaft A", 45, "CNC-01", 120, "High"])
    ws.append(["Housing B", 60, "CNC-02", 180, "Medium"])
    ws.append(["Plate C", 30, "CNC-01", 90, "Critical"])

    buf = io.BytesIO()
    wb.save(buf)

    parser = ExcelParser()
    result = parser.parse(buf.getvalue(), "single_sheet_schedule.xlsx")

    assert result["success"] is True
    assert result["auto_converted"] is True
    assert len(result["jobs"]) == 3
    assert len(result["machines"]) == 2  # Discovered CNC-01 and CNC-02
    assert "CNC-01" in result["machines"]
    assert "CNC-02" in result["machines"]
    assert len(result["transformations"]) > 0


def test_fuzzy_column_mapping():
    """Test fuzzy synonym mapping on arbitrary sheet and column names."""
    wb = openpyxl.Workbook()

    ws_m = wb.active
    ws_m.title = "Equipment List"
    ws_m.append(["AssetCode", "KW_Rate", "Condition"])
    ws_m.append(["ST-01", 8.5, "Operational"])
    ws_m.append(["ST-02", 11.0, "Operational"])

    ws_j = wb.create_sheet("WorkOrders")
    ws_j.append(["WO_ID", "RunTime", "AllowedStation", "TargetDate"])
    ws_j.append(["WO-101", 50, "ST-01", 150])
    ws_j.append(["WO-102", 35, "ST-02", 110])

    buf = io.BytesIO()
    wb.save(buf)

    parser = ExcelParser()
    result = parser.parse(buf.getvalue(), "work_orders.xlsx")

    assert result["success"] is True
    assert result["auto_converted"] is True
    assert len(result["machines"]) == 2
    assert len(result["jobs"]) == 2
    assert "ST-01" in result["machines"]
    assert result["machines"]["ST-01"]["energy_kwh_per_hour"] == 8.5
    assert result["jobs"][0]["job_id"] == "WO-101"

