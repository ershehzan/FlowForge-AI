"""
Industrial Data Expansion & Scenario Verification Test Suite.

Covers:
  - Old Excel format backward compatibility (3 sheets: Machines, Jobs, Disruptions)
  - New Industrial Excel format (16 connected sheets from data/industrial_factory.xlsx)
  - Cross-entity validation & normalization layer
  - Missing optional sheets & safe defaults
  - Execution of all 10 industrial scenarios against base factory
  - AI Copilot deterministic reasoning for all 15 operational questions
  - GA runtime performance benchmarks on 36 jobs
  - REST API endpoints for scenarios & rich factory upload
"""
import os
import time
import pytest
from fastapi.testclient import TestClient

from agents.factory.excel_parser import ExcelParser
from agents.factory.normalizer import normalize_factory_data
from agents.factory.state import FactoryState
from agents.disruption.engine import DisruptionEngine
from agents.disruption.scenarios import ScenarioRunner, INDUSTRIAL_SCENARIOS_META
from agents.copilot.provider import AICopilotProvider
from agents.scheduler import Scheduler
from deployment.app import app


client = TestClient(app)
SAMPLE_WORKBOOK_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "industrial_factory.xlsx")


def test_industrial_excel_file_exists():
    """Verify that data/industrial_factory.xlsx exists and has content."""
    assert os.path.exists(SAMPLE_WORKBOOK_PATH), "data/industrial_factory.xlsx must exist"
    assert os.path.getsize(SAMPLE_WORKBOOK_PATH) > 1000, "File must not be empty"


def test_parse_new_industrial_excel():
    """Test parsing the 16-sheet industrial factory workbook."""
    parser = ExcelParser()
    with open(SAMPLE_WORKBOOK_PATH, "rb") as f:
        content = f.read()

    result = parser.parse(content, filename="industrial_factory.xlsx")
    assert result["success"] is True
    assert len(result["errors"]) == 0

    # Verify key entity counts
    assert len(result["machines"]) == 10
    assert len(result["jobs"]) == 36
    assert len(result.get("production_lines", [])) >= 3
    assert len(result.get("production_orders", [])) >= 10
    assert len(result.get("operations", [])) >= 50
    assert len(result.get("materials", [])) >= 8
    assert len(result.get("inventory", [])) >= 8
    assert len(result.get("maintenance", [])) >= 4
    assert len(result.get("downtime", [])) >= 4
    assert len(result.get("scenarios", [])) == 10


def test_backward_compatibility_old_3_sheet_excel():
    """Verify that a legacy 3-sheet Excel file (Machines, Jobs, Disruptions) parses and normalizes cleanly."""
    import openpyxl
    wb = openpyxl.Workbook()

    # Sheet 1: Machines
    ws_m = wb.active
    ws_m.title = "Machines"
    ws_m.append(["machine_id", "machine_name", "status", "energy_kwh_per_hour"])
    ws_m.append(["M1", "Milling Center 1", "available", 12.0])
    ws_m.append(["M2", "Turning Lathe 2", "available", 9.5])
    ws_m.append(["M3", "Press 3", "available", 22.0])

    # Sheet 2: Jobs
    ws_j = wb.create_sheet(title="Jobs")
    ws_j.append(["job_id", "duration", "deadline", "priority"])
    ws_j.append(["J1", 25, 80, 4])
    ws_j.append(["J2", 35, 120, 3])
    ws_j.append(["J3", 40, 150, 5])

    # Sheet 3: Disruptions
    ws_d = wb.create_sheet(title="Disruptions")
    ws_d.append(["type", "target_id", "value"])
    ws_d.append(["machine_failure", "M2", 1])

    import io
    buf = io.BytesIO()
    wb.save(buf)
    legacy_bytes = buf.getvalue()

    parser = ExcelParser()
    res = parser.parse(legacy_bytes, filename="legacy_factory.xlsx")

    assert res["success"] is True
    assert len(res["machines"]) == 3
    assert len(res["jobs"]) == 3
    # Normalizer should synthesize safe defaults for optional entities
    assert len(res["production_lines"]) >= 1
    assert len(res["inventory"]) >= 1
    assert len(res["materials"]) >= 1
    assert len(res["scenarios"]) == 10


def test_factory_state_loading_and_erp_sync():
    """Verify FactoryState integrates rich models and synchronizes ERP engine."""
    parser = ExcelParser()
    with open(SAMPLE_WORKBOOK_PATH, "rb") as f:
        parsed = parser.parse(f.read(), filename="industrial_factory.xlsx")

    fs = FactoryState()
    fs.load_normalized_data(parsed, data_source="industrial_factory.xlsx")

    assert len(fs.machines) == 10
    assert len(fs.jobs) == 36
    assert len(fs.production_lines) == 3
    assert len(fs.production_orders) >= 10
    assert len(fs.operations) >= 50

    # Check ERP Engine sync
    fs.erp_engine.synchronize()
    erp_dict = fs.erp_engine.to_dict()
    assert len(erp_dict["orders"]) >= 10
    assert len(erp_dict["inventory"]) >= 8
    assert len(erp_dict["capacity"]) == 10

    # Serialization in to_dict()
    state_dict = fs.to_dict()
    assert "production_lines" in state_dict
    assert "machine_capabilities" in state_dict
    assert "scenarios" in state_dict
    assert len(state_dict["scenarios"]) == 10


def test_all_10_industrial_scenarios_execute():
    """Execute all 10 industrial scenarios on the common factory state and check results."""
    parser = ExcelParser()
    with open(SAMPLE_WORKBOOK_PATH, "rb") as f:
        parsed = parser.parse(f.read(), filename="industrial_factory.xlsx")

    fs = FactoryState()
    fs.load_normalized_data(parsed, data_source="industrial_factory.xlsx")

    engine = DisruptionEngine(fs)
    runner = ScenarioRunner(engine)

    scenarios = runner.get_available_scenarios()
    assert len(scenarios) == 10

    results = []
    for sc in scenarios:
        res = runner.run(sc["id"])
        assert res["scenario_id"] == sc["id"]
        assert "baseline" in res
        assert "event" in res
        assert "impact" in res
        assert "flowforge_response" in res
        assert "recovery_schedule" in res
        assert "result" in res
        assert res["result"]["status"] == sc["expected_result"]
        results.append(res)

    assert len(results) == 10


def test_ai_copilot_answers_all_15_operational_questions():
    """Verify AI Copilot deterministic reasoning answers all 15 questions from Section 32."""
    parser = ExcelParser()
    with open(SAMPLE_WORKBOOK_PATH, "rb") as f:
        parsed = parser.parse(f.read(), filename="industrial_factory.xlsx")

    fs = FactoryState()
    fs.load_normalized_data(parsed, data_source="industrial_factory.xlsx")

    # Generate baseline schedule
    avail = fs.get_available_machine_ids()
    scheduler = Scheduler(avail)
    baseline = scheduler.ga_schedule(fs.get_active_jobs(), machine_energy=fs.get_machine_energy_map())
    fs.set_baseline_schedule(baseline)
    fs.erp_engine.synchronize()

    copilot = AICopilotProvider()  # Uses deterministic fallback
    ctx = {
        "factory_status": fs.factory_status,
        "machines": fs.machines,
        "schedule": baseline,
        "metrics": {"makespan": 140, "energy_consumption": 842.5},
        "resilience": {"score": 87},
        "orders": [o.to_dict() for o in fs.erp_engine.orders],
        "inventory": [i.to_dict() for i in fs.erp_engine.inventory],
        "maintenance": [m.to_dict() for m in fs.erp_engine.maintenance],
        "downtime": fs.downtime_records,
        "capacity": fs.erp_engine.get_capacity_matrix(),
    }

    questions_and_expectations = [
        ("Which machine is currently the bottleneck?", ["bottleneck", "m"]),
        ("Why is M03 at risk?", ["m03", "health"]),
        ("Which orders are at risk?", ["order"]),
        ("What happens if M03 fails?", ["m03", "impact"]),
        ("Which jobs are affected by this maintenance window?", ["maintenance", "m04"]),
        ("Which material is limiting production?", ["rm-003", "titanium", "rm-005", "copper", "limiting"]),
        ("Which machine consumes the most energy?", ["energy", "kwh"]),
        ("Which production order has the highest deadline risk?", ["order", "ord"]),
        ("How much downtime occurred today?", ["downtime", "minute"]),
        ("Which machines have upcoming maintenance?", ["maintenance", "m"]),
        ("What changed after M03 failed?", ["m03", "reallocated"]),
        ("Why was J17 moved to M05?", ["j17", "m05"]),
        ("Which schedule is more energy efficient?", ["energy", "schedule"]),
        ("What are the top three current factory risks?", ["top", "risk"]),
        ("Summarize the current factory state.", ["factory", "resilience"]),
    ]

    for q, expected_substrings in questions_and_expectations:
        resp = copilot.query(q, ctx)
        ans = resp["answer"].lower()
        assert resp["answer"] != "", f"Empty answer for query: {q}"
        assert "recommended_action" in resp, f"Missing recommendation for query: {q}"
        assert "metrics" in resp, f"Missing metrics for query: {q}"
        assert any(sub in ans for sub in expected_substrings), (
            f"Query '{q}' expected one of {expected_substrings}, got: '{resp['answer']}'"
        )


def test_ga_performance_benchmark():
    """Benchmark GA runtime on the full 36-job industrial factory dataset."""
    parser = ExcelParser()
    with open(SAMPLE_WORKBOOK_PATH, "rb") as f:
        parsed = parser.parse(f.read(), filename="industrial_factory.xlsx")

    fs = FactoryState()
    fs.load_normalized_data(parsed)

    avail = fs.get_available_machine_ids()
    assert len(avail) == 10
    active_jobs = fs.get_active_jobs()
    assert len(active_jobs) == 36

    scheduler = Scheduler(avail)
    energy_map = fs.get_machine_energy_map()

    t0 = time.perf_counter()
    sched = scheduler.ga_schedule(active_jobs, machine_energy=energy_map)
    elapsed = time.perf_counter() - t0

    assert len(sched) == 36
    # GA must complete in under 3.5 seconds to guarantee snappy live demo responsiveness
    assert elapsed < 3.5, f"GA took {elapsed:.2f}s, which exceeds demo target of 3.5s"


def test_api_scenarios_endpoints():
    """Verify FastAPI /scenarios and /scenarios/run endpoints work end-to-end."""
    # 1. GET /scenarios
    res = client.get("/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert "scenarios" in data
    assert len(data["scenarios"]) == 10

    # 2. POST /scenarios/run for Scenario 2 (M03 Failure)
    res_run = client.post("/scenarios/run", json={"scenario_id": 2})
    assert res_run.status_code == 200
    run_data = res_run.json()
    assert run_data["success"] is True
    assert run_data["scenario_id"] == 2
    assert "result" in run_data
    assert "baseline" in run_data["result"]
    assert "flowforge_response" in run_data["result"]

    # 3. POST /copilot/query after scenario run
    res_cop = client.post("/copilot/query", json={"question": "What happened to M3?"})
    assert res_cop.status_code == 200
    cop_data = res_cop.json()
    assert "answer" in cop_data
    assert "m3" in cop_data["answer"].lower() or "m03" in cop_data["answer"].lower()
