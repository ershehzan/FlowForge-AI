"""
Smart Excel Parser & Normalization Engine for FlowForge.

Parses .xlsx and .xls factory production workbooks into internal
Machine, Job, and rich ERP models for the autonomous scheduling engine.

Features:
  1. Standard parsing for well-formed Machines, Jobs, and Disruptions sheets.
  2. Industrial schema expansion: parses 13 additional sheets (Production_Lines,
     Machine_Capabilities, Production_Orders, Operations, Materials, Inventory,
     Maintenance, Downtime, Energy, Quality, Shifts, Dependencies, Scenarios).
  3. Strict backward-compatibility normalization: safe defaults for missing optional sheets.
  4. Smart Excel Analyzer: automatically detects non-standard sheet names,
     fuzzy header synonyms, single-sheet spreadsheets, and synthesizes missing
     machine definitions from job table machine assignments.
  5. Transformation audit trail reporting mapping actions performed.
"""
import io
import re
import openpyxl
from agents.factory.normalizer import normalize_factory_data


PRIORITY_MAP = {
    "CRITICAL": 5,
    "HIGH": 4,
    "MEDIUM": 3,
    "LOW": 2,
    "MINIMAL": 1,
}

# Fuzzy synonym dictionaries
SYNONYMS_MACHINE_ID = ["machine_id", "machine id", "machine", "machine_name", "machine name", "equipment_id", "equipment id", "equipment", "asset_id", "asset id", "asset", "station_id", "station", "line", "cell", "code", "id", "name"]
SYNONYMS_ENERGY = ["energy_kwh_per_hour", "energy kwh per hour", "energy", "kwh", "kwh/h", "kwh/hr", "power", "consumption", "rate", "energy_rate", "kw"]
SYNONYMS_MACHINE_STATUS = ["status", "state", "condition", "availability"]

SYNONYMS_JOB_ID = ["job_id", "job id", "job", "job_name", "task_id", "task id", "task", "order_id", "order id", "order", "part_number", "part_no", "part no", "part", "work_order", "wo", "item", "id", "code"]
SYNONYMS_DURATION = ["processing_time", "processing time", "duration", "process_time", "process time", "cycle_time", "cycle time", "run_time", "run time", "time_mins", "time (min)", "time (mins)", "time", "mins", "minutes", "hours"]
SYNONYMS_ELIGIBLE = ["eligible_machines", "eligible machines", "machines", "machine", "eligible", "allowed_machines", "allowed machines", "allowed_station", "allowed station", "stations", "station", "lines", "line", "cell", "cells", "assigned_machine", "assigned machine", "assigned_station", "workstation"]
SYNONYMS_PRIORITY = ["priority", "urgency", "rank", "importance", "level", "prio"]
SYNONYMS_DEADLINE = ["deadline", "due_date", "due date", "due", "target_date", "target date", "finish_by", "delivery"]


def _match_synonym(header_text, synonym_list):
    """Match header text against synonym list using clean string comparison."""
    if not header_text:
        return False
    clean = re.sub(r'[^a-z0-9]', '', str(header_text).lower())
    for syn in synonym_list:
        clean_syn = re.sub(r'[^a-z0-9]', '', syn.lower())
        if clean == clean_syn or clean_syn in clean or (len(clean) >= 3 and clean in clean_syn):
            return True
    return False


class ExcelParser:
    """Parser, validator, and smart structure converter for FlowForge Excel datasets."""

    def __init__(self):
        self.errors = []
        self.transformations = []

    def parse(self, file_content_or_path, filename="uploaded.xlsx"):
        """
        Parse an Excel file and return normalized factory data.
        Fails back to Smart Excel Analyzer if standard sheets are missing.
        """
        self.errors = []
        self.transformations = []

        try:
            if isinstance(file_content_or_path, (bytes, bytearray)):
                workbook = openpyxl.load_workbook(io.BytesIO(file_content_or_path), data_only=True)
            elif hasattr(file_content_or_path, "read"):
                content = file_content_or_path.read()
                workbook = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
            else:
                workbook = openpyxl.load_workbook(file_content_or_path, data_only=True)
        except Exception as e:
            return {
                "success": False,
                "errors": [{"sheet": "File", "row": 0, "column": "Workbook", "message": f"Failed to open Excel workbook: {str(e)}"}],
                "error_messages": [f"File error: Failed to open Excel workbook: {str(e)}"],
                "machines": None,
                "jobs": None,
                "disruptions": None,
                "summary": None,
                "data_source": filename,
                "auto_converted": False,
                "transformations": [],
            }

        sheet_names = workbook.sheetnames
        lower_sheets = {name.lower().strip().replace(" ", "_"): name for name in sheet_names}

        # Check if standard Machines & Jobs sheets exist
        has_std_machines = "machines" in lower_sheets
        has_std_jobs = "jobs" in lower_sheets

        if has_std_machines and has_std_jobs:
            # Standard Mode Parsing
            machines_sheet = workbook[lower_sheets["machines"]]
            machines, machine_ids = self._parse_machines(machines_sheet)

            jobs_sheet = workbook[lower_sheets["jobs"]]
            jobs = self._parse_jobs(jobs_sheet, machine_ids)

            disruptions = []
            if "disruptions" in lower_sheets:
                disruptions_sheet = workbook[lower_sheets["disruptions"]]
                disruptions = self._parse_disruptions(disruptions_sheet, machine_ids, [j["job_id"] for j in jobs])

            raw_sheets = {}
            valid_job_ids = [j["job_id"] for j in jobs]

            # Optional sheets parsing
            if "production_lines" in lower_sheets:
                raw_sheets["production_lines"] = self._parse_production_lines(workbook[lower_sheets["production_lines"]])
            if "machine_capabilities" in lower_sheets:
                raw_sheets["machine_capabilities"] = self._parse_machine_capabilities(workbook[lower_sheets["machine_capabilities"]], machine_ids)
            if "production_orders" in lower_sheets:
                raw_sheets["production_orders"] = self._parse_production_orders(workbook[lower_sheets["production_orders"]])
            if "operations" in lower_sheets:
                raw_sheets["operations"] = self._parse_operations(workbook[lower_sheets["operations"]], valid_job_ids, machine_ids)
            if "materials" in lower_sheets:
                raw_sheets["materials"] = self._parse_materials(workbook[lower_sheets["materials"]])
            valid_mat_ids = [m["material_id"] for m in raw_sheets.get("materials", [])]
            if "inventory" in lower_sheets:
                raw_sheets["inventory"] = self._parse_inventory(workbook[lower_sheets["inventory"]], valid_mat_ids)
            if "maintenance" in lower_sheets:
                raw_sheets["maintenance"] = self._parse_maintenance(workbook[lower_sheets["maintenance"]], machine_ids)
            if "downtime" in lower_sheets:
                raw_sheets["downtime"] = self._parse_downtime(workbook[lower_sheets["downtime"]], machine_ids)
            if "energy" in lower_sheets:
                raw_sheets["energy"] = self._parse_energy(workbook[lower_sheets["energy"]], machine_ids)
            if "quality" in lower_sheets:
                raw_sheets["quality"] = self._parse_quality(workbook[lower_sheets["quality"]], valid_job_ids, machine_ids)
            if "shifts" in lower_sheets:
                raw_sheets["shifts"] = self._parse_shifts(workbook[lower_sheets["shifts"]])
            if "dependencies" in lower_sheets:
                raw_sheets["dependencies"] = self._parse_dependencies(workbook[lower_sheets["dependencies"]], valid_job_ids)
            if "scenarios" in lower_sheets:
                raw_sheets["scenarios"] = self._parse_scenarios(workbook[lower_sheets["scenarios"]])

            if not self.errors:
                normalized = normalize_factory_data(machines, jobs, disruptions, raw_sheets)
                return self._build_success_result(
                    normalized["machines"], normalized["jobs"], normalized["disruptions"],
                    filename, auto_converted=False, normalized_data=normalized
                )
            else:
                return self._build_error_result(filename)

        if has_std_machines and not has_std_jobs:
            self.add_error("Workbook", 0, "Jobs", "Missing required sheet: 'Jobs'")
            return self._build_error_result(filename)

        if has_std_jobs and not has_std_machines:
            self.add_error("Workbook", 0, "Machines", "Missing required sheet: 'Machines'")
            return self._build_error_result(filename)

        # Reset errors and attempt Smart Auto-Conversion
        self.errors = []
        return self._smart_parse(workbook, filename)

    def _smart_parse(self, workbook, filename):
        """Smart Excel Analyzer: auto-detects non-standard layout and converts to factory state."""
        sheet_names = workbook.sheetnames
        self.transformations.append(f"Analyzing {len(sheet_names)} sheet(s) in workbook '{filename}'")

        machines_sheet = None
        jobs_sheet = None

        # 1. Identify sheet roles by content inspection
        for sheet_name in sheet_names:
            sheet = workbook[sheet_name]
            rows = list(sheet.iter_rows(values_only=True))
            if not rows:
                continue

            headers = [str(cell).strip().lower() for cell in rows[0] if cell is not None]

            is_machine_sheet = any(_match_synonym(h, SYNONYMS_MACHINE_ID) for h in headers) and any(_match_synonym(h, SYNONYMS_ENERGY) for h in headers)
            is_job_sheet = any(_match_synonym(h, SYNONYMS_JOB_ID) for h in headers) and any(_match_synonym(h, SYNONYMS_DURATION) for h in headers)

            if is_machine_sheet and not machines_sheet:
                machines_sheet = sheet
                self.transformations.append(f"Mapped sheet '{sheet_name}' -> Machines dataset")
            elif is_job_sheet and not jobs_sheet:
                jobs_sheet = sheet
                self.transformations.append(f"Mapped sheet '{sheet_name}' -> Jobs dataset")

        # Fallback: if single sheet or unmapped, pick active sheet as Jobs sheet
        if not jobs_sheet:
            for s_name in sheet_names:
                s = workbook[s_name]
                if s != machines_sheet:
                    jobs_sheet = s
                    self.transformations.append(f"Defaulted sheet '{jobs_sheet.title}' -> Jobs dataset")
                    break
            if not jobs_sheet and not machines_sheet:
                jobs_sheet = workbook.active
                self.transformations.append(f"Defaulted sheet '{jobs_sheet.title}' -> Jobs dataset")

        # 2. Parse Jobs sheet using Fuzzy Mapping
        jobs, referenced_machines = self._fuzzy_parse_jobs(jobs_sheet)

        if not jobs:
            self.add_error(jobs_sheet.title, 0, "Jobs", "Could not extract valid jobs from spreadsheet")
            return self._build_error_result(filename)

        # 3. Parse or Synthesize Machines
        machines = {}
        if machines_sheet:
            machines, _ = self._fuzzy_parse_machines(machines_sheet)

        if not machines:
            self.transformations.append("No Machines sheet found; synthesizing machine models from job assignments")
            all_referenced = set()
            for j in jobs:
                all_referenced.update(j["eligible_machines"])

            if not all_referenced:
                all_referenced = {"M1", "M2", "M3", "M4", "M5", "M6"}

            default_energies = [8.0, 10.5, 12.0, 7.5, 7.0, 9.0]
            for idx, m_id in enumerate(sorted(all_referenced)):
                energy_rate = default_energies[idx % len(default_energies)]
                machines[m_id] = {
                    "id": m_id,
                    "status": "available",
                    "energy_kwh_per_hour": energy_rate,
                    "capacity": 1,
                }
            self.transformations.append(f"Auto-generated {len(machines)} machine(s) with default energy profiles ({', '.join(sorted(all_referenced))})")

        valid_machine_ids = list(machines.keys())
        for j in jobs:
            if not j["eligible_machines"]:
                j["eligible_machines"] = valid_machine_ids
            else:
                j["eligible_machines"] = [m for m in j["eligible_machines"] if m in machines]
                if not j["eligible_machines"]:
                    j["eligible_machines"] = valid_machine_ids

        normalized = normalize_factory_data(machines, jobs, [], {})
        return self._build_success_result(
            normalized["machines"], normalized["jobs"], normalized["disruptions"],
            filename, auto_converted=True, normalized_data=normalized
        )

    def _fuzzy_parse_jobs(self, sheet):
        jobs = []
        referenced_machines = set()
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return [], set()

        headers = [str(cell).strip() if cell is not None else "" for cell in rows[0]]

        col_job_id = self._find_col(headers, SYNONYMS_JOB_ID)
        col_duration = self._find_col(headers, SYNONYMS_DURATION)
        col_eligible = self._find_col(headers, SYNONYMS_ELIGIBLE)
        col_priority = self._find_col(headers, SYNONYMS_PRIORITY)
        col_deadline = self._find_col(headers, SYNONYMS_DEADLINE)

        if col_job_id is not None:
            self.transformations.append(f"Mapped column '{headers[col_job_id]}' -> job_id")
        if col_duration is not None:
            self.transformations.append(f"Mapped column '{headers[col_duration]}' -> processing_time")
        if col_eligible is not None:
            self.transformations.append(f"Mapped column '{headers[col_eligible]}' -> eligible_machines")

        for row_idx, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue

            raw_id = row[col_job_id] if col_job_id is not None and col_job_id < len(row) else None
            job_id = str(raw_id).strip() if raw_id is not None and str(raw_id).strip() != "" else f"J{len(jobs)+1}"

            proc_time = 30.0
            if col_duration is not None and col_duration < len(row):
                raw_dur = row[col_duration]
                if raw_dur is not None and str(raw_dur).strip() != "":
                    try:
                        proc_time = float(raw_dur)
                        if proc_time <= 0:
                            proc_time = 30.0
                    except ValueError:
                        proc_time = 30.0

            eligible = []
            if col_eligible is not None and col_eligible < len(row):
                raw_em = row[col_eligible]
                if raw_em is not None and str(raw_em).strip() != "":
                    parts = [m.strip() for m in str(raw_em).split(",") if m.strip()]
                    eligible = parts
                    referenced_machines.update(parts)

            deadline = proc_time * 3
            if col_deadline is not None and col_deadline < len(row):
                raw_dl = row[col_deadline]
                if raw_dl is not None and str(raw_dl).strip() != "":
                    raw_str = str(raw_dl).strip()
                    if ":" in raw_str:
                        try:
                            parts = raw_str.split(":")
                            deadline = float(int(parts[0]) * 60 + int(parts[1]))
                        except Exception:
                            deadline = proc_time * 3
                    else:
                        try:
                            deadline = float(raw_dl)
                        except ValueError:
                            deadline = proc_time * 3

            priority = 3
            if col_priority is not None and col_priority < len(row):
                raw_p = row[col_priority]
                if raw_p is not None and str(raw_p).strip() != "":
                    p_str = str(raw_p).strip().upper()
                    if p_str in PRIORITY_MAP:
                        priority = PRIORITY_MAP[p_str]
                    else:
                        try:
                            priority = max(1, min(5, int(float(raw_p))))
                        except ValueError:
                            priority = 3

            jobs.append({
                "job_id": job_id,
                "name": job_id,
                "duration": int(proc_time),
                "deadline": int(deadline),
                "priority": priority,
                "eligible_machines": eligible,
                "status": "pending",
            })

        return jobs, referenced_machines

    def _fuzzy_parse_machines(self, sheet):
        machines = {}
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return {}, set()

        headers = [str(cell).strip() if cell is not None else "" for cell in rows[0]]

        col_id = self._find_col(headers, SYNONYMS_MACHINE_ID)
        col_energy = self._find_col(headers, SYNONYMS_ENERGY)
        col_status = self._find_col(headers, SYNONYMS_MACHINE_STATUS)

        if col_id is not None:
            self.transformations.append(f"Mapped column '{headers[col_id]}' -> machine_id")
        if col_energy is not None:
            self.transformations.append(f"Mapped column '{headers[col_energy]}' -> energy_kwh_per_hour")

        default_energies = [8.0, 10.5, 12.0, 7.5, 7.0, 9.0]

        for row_idx, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue

            raw_id = row[col_id] if col_id is not None and col_id < len(row) else None
            m_id = str(raw_id).strip() if raw_id is not None and str(raw_id).strip() != "" else f"M{len(machines)+1}"

            energy = default_energies[len(machines) % len(default_energies)]
            if col_energy is not None and col_energy < len(row):
                raw_e = row[col_energy]
                if raw_e is not None and str(raw_e).strip() != "":
                    try:
                        e_val = float(raw_e)
                        if e_val >= 0:
                            energy = e_val
                    except ValueError:
                        pass

            status_val = "available"
            if col_status is not None and col_status < len(row):
                raw_s = row[col_status]
                if raw_s is not None and str(raw_s).strip() != "":
                    s_clean = str(raw_s).strip().lower()
                    if s_clean in ["failed", "down", "broken"]:
                        status_val = "failed"

            machines[m_id] = {
                "id": m_id,
                "name": f"Station {m_id}",
                "status": status_val,
                "energy_kwh_per_hour": energy,
                "capacity": 1,
            }

        return machines, set(machines.keys())

    def _find_col(self, headers, synonym_list):
        for idx, h in enumerate(headers):
            if _match_synonym(h, synonym_list):
                return idx
        return None

    def add_error(self, sheet, row, column, message):
        self.errors.append({
            "sheet": sheet,
            "row": row,
            "column": column,
            "message": message,
        })

    def _parse_machines(self, sheet):
        machines = {}
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            self.add_error("Machines", 0, "Sheet", "Machines sheet is empty")
            return {}, set()

        headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
        col_map = {h: idx for idx, h in enumerate(headers) if h}

        if "machine_id" not in col_map:
            self.add_error("Machines", 1, "machine_id", "Missing required column 'machine_id'")
            return {}, set()

        seen_ids = set()
        for row_idx, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue
            machine_id_val = row[col_map["machine_id"]] if col_map["machine_id"] < len(row) else None
            if not machine_id_val:
                self.add_error("Machines", row_idx, "machine_id", "machine_id is missing or empty")
                continue

            machine_id = str(machine_id_val).strip()
            if machine_id in seen_ids:
                self.add_error("Machines", row_idx, "machine_id", f"Duplicate machine_id '{machine_id}'")
                continue
            seen_ids.add(machine_id)

            energy_val = 8.0
            if "energy_kwh_per_hour" in col_map and col_map["energy_kwh_per_hour"] < len(row):
                raw_e = row[col_map["energy_kwh_per_hour"]]
                if raw_e is not None and str(raw_e).strip() != "":
                    try:
                        energy_val = float(raw_e)
                        if energy_val < 0:
                            self.add_error("Machines", row_idx, "energy_kwh_per_hour", "energy_kwh_per_hour cannot be negative")
                    except ValueError:
                        self.add_error("Machines", row_idx, "energy_kwh_per_hour", f"Invalid numeric value '{raw_e}'")

            status_val = "available"
            if "status" in col_map and col_map["status"] < len(row):
                raw_s = row[col_map["status"]]
                if raw_s is not None and str(raw_s).strip() != "":
                    s_clean = str(raw_s).strip().lower()
                    if s_clean in ["failed", "down", "broken"]:
                        status_val = "failed"

            name_val = str(row[col_map["machine_name"]]).strip() if "machine_name" in col_map and col_map["machine_name"] < len(row) and row[col_map["machine_name"]] else f"Station {machine_id}"

            m_data = {
                "id": machine_id,
                "name": name_val,
                "machine_name": name_val,
                "status": status_val,
                "energy_kwh_per_hour": energy_val,
                "capacity": 1,
            }

            # Optional industrial attributes
            if "line_id" in col_map and col_map["line_id"] < len(row) and row[col_map["line_id"]]:
                m_data["line_id"] = str(row[col_map["line_id"]]).strip()
            if "machine_type" in col_map and col_map["machine_type"] < len(row) and row[col_map["machine_type"]]:
                m_data["machine_type"] = str(row[col_map["machine_type"]]).strip()
            if "idle_energy_kwh_per_hour" in col_map and col_map["idle_energy_kwh_per_hour"] < len(row):
                try:
                    m_data["idle_energy_kwh_per_hour"] = float(row[col_map["idle_energy_kwh_per_hour"]])
                except (ValueError, TypeError):
                    pass
            if "health_score" in col_map and col_map["health_score"] < len(row):
                try:
                    m_data["health_score"] = int(float(row[col_map["health_score"]]))
                except (ValueError, TypeError):
                    pass
            if "maintenance_due" in col_map and col_map["maintenance_due"] < len(row) and row[col_map["maintenance_due"]]:
                m_data["maintenance_due"] = str(row[col_map["maintenance_due"]]).strip()
            if "age_years" in col_map and col_map["age_years"] < len(row):
                try:
                    m_data["age_years"] = int(float(row[col_map["age_years"]]))
                except (ValueError, TypeError):
                    pass

            machines[machine_id] = m_data

        return machines, set(machines.keys())

    def _parse_jobs(self, sheet, valid_machine_ids):
        jobs = []
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            self.add_error("Jobs", 0, "Sheet", "Jobs sheet is empty")
            return []

        headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
        col_map = {h: idx for idx, h in enumerate(headers) if h}

        if "job_id" not in col_map:
            self.add_error("Jobs", 1, "job_id", "Missing required column 'job_id'")
            return []

        proc_col = "processing_time" if "processing_time" in col_map else ("duration" if "duration" in col_map else None)
        if not proc_col:
            self.add_error("Jobs", 1, "processing_time", "Missing required column 'processing_time' or 'duration'")
            return []

        seen_job_ids = set()
        for row_idx, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue
            job_id_val = row[col_map["job_id"]] if col_map["job_id"] < len(row) else None
            if not job_id_val:
                self.add_error("Jobs", row_idx, "job_id", "job_id is missing or empty")
                continue

            job_id = str(job_id_val).strip()
            if job_id in seen_job_ids:
                self.add_error("Jobs", row_idx, "job_id", f"Duplicate job_id '{job_id}'")
                continue
            seen_job_ids.add(job_id)

            proc_time_val = None
            raw_duration = row[col_map[proc_col]] if col_map[proc_col] < len(row) else None
            if raw_duration is not None and str(raw_duration).strip() != "":
                try:
                    proc_time_val = float(raw_duration)
                    if proc_time_val <= 0:
                        self.add_error("Jobs", row_idx, proc_col, f"{proc_col} must be greater than 0")
                except ValueError:
                    self.add_error("Jobs", row_idx, proc_col, f"Invalid numeric value '{raw_duration}'")
            else:
                self.add_error("Jobs", row_idx, proc_col, f"{proc_col} is missing")

            deadline_val = proc_time_val * 3 if proc_time_val else 100
            if "deadline" in col_map and col_map["deadline"] < len(row):
                raw_dl = row[col_map["deadline"]]
                if raw_dl is not None and str(raw_dl).strip() != "":
                    raw_str = str(raw_dl).strip()
                    if ":" in raw_str:
                        try:
                            parts = raw_str.split(":")
                            deadline_val = float(int(parts[0]) * 60 + int(parts[1]))
                        except Exception:
                            deadline_val = 150.0
                    else:
                        try:
                            deadline_val = float(raw_dl)
                            if deadline_val <= 0:
                                self.add_error("Jobs", row_idx, "deadline", "deadline must be positive")
                        except ValueError:
                            self.add_error("Jobs", row_idx, "deadline", f"Invalid deadline value '{raw_dl}'")

            eligible_machines = list(valid_machine_ids)
            if "eligible_machines" in col_map and col_map["eligible_machines"] < len(row):
                raw_em = row[col_map["eligible_machines"]]
                if raw_em is not None and str(raw_em).strip() != "":
                    em_list = [m.strip() for m in str(raw_em).split(",") if m.strip()]
                    if em_list:
                        invalid_ref = [m for m in em_list if m not in valid_machine_ids]
                        if invalid_ref:
                            self.add_error(
                                "Jobs", row_idx, "eligible_machines",
                                f"Machine(s) {', '.join(invalid_ref)} do not exist in Machines sheet"
                            )
                        eligible_machines = em_list

            priority_val = 3
            if "priority" in col_map and col_map["priority"] < len(row):
                raw_p = row[col_map["priority"]]
                if raw_p is not None and str(raw_p).strip() != "":
                    raw_p_str = str(raw_p).strip().upper()
                    if raw_p_str in PRIORITY_MAP:
                        priority_val = PRIORITY_MAP[raw_p_str]
                    else:
                        try:
                            priority_val = max(1, min(5, int(float(raw_p))))
                        except ValueError:
                            priority_val = 3

            j_name = str(row[col_map["job_name"]]).strip() if "job_name" in col_map and col_map["job_name"] < len(row) and row[col_map["job_name"]] else job_id

            job_dict = {
                "job_id": job_id,
                "name": j_name,
                "duration": int(proc_time_val) if proc_time_val else 30,
                "deadline": int(deadline_val),
                "priority": priority_val,
                "eligible_machines": eligible_machines,
                "status": "pending",
            }

            if "order_id" in col_map and col_map["order_id"] < len(row) and row[col_map["order_id"]]:
                job_dict["order_id"] = str(row[col_map["order_id"]]).strip()
            if "product_id" in col_map and col_map["product_id"] < len(row) and row[col_map["product_id"]]:
                job_dict["product_id"] = str(row[col_map["product_id"]]).strip()
            if "setup_time" in col_map and col_map["setup_time"] < len(row):
                try:
                    job_dict["setup_time"] = int(float(row[col_map["setup_time"]]))
                except (ValueError, TypeError):
                    pass
            if "quantity" in col_map and col_map["quantity"] < len(row):
                try:
                    job_dict["quantity"] = int(float(row[col_map["quantity"]]))
                except (ValueError, TypeError):
                    pass
            if "material_required" in col_map and col_map["material_required"] < len(row) and row[col_map["material_required"]]:
                job_dict["material_required"] = str(row[col_map["material_required"]]).strip()
            if "quality_target" in col_map and col_map["quality_target"] < len(row):
                try:
                    job_dict["quality_target"] = float(row[col_map["quality_target"]])
                except (ValueError, TypeError):
                    pass

            jobs.append(job_dict)

        return jobs

    def _parse_disruptions(self, sheet, valid_machine_ids, valid_job_ids):
        disruptions = []
        rows = list(sheet.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            return []

        headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
        col_map = {h: idx for idx, h in enumerate(headers) if h}

        for row_idx, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue
            dtype = row[col_map.get("type", 0)] if "type" in col_map and col_map["type"] < len(row) else None
            target = row[col_map.get("target_id", 1)] if "target_id" in col_map and col_map["target_id"] < len(row) else None

            if dtype and target:
                d_dict = {
                    "disruption_id": f"D{row_idx-1}",
                    "type": str(dtype).strip(),
                    "target_id": str(target).strip(),
                    "value": row[col_map.get("value", 2)] if "value" in col_map and col_map["value"] < len(row) else None,
                }
                if "severity" in col_map and col_map["severity"] < len(row):
                    d_dict["severity"] = str(row[col_map["severity"]]).strip()
                if "duration" in col_map and col_map["duration"] < len(row) and row[col_map["duration"]] is not None:
                    try:
                        d_dict["duration"] = int(float(row[col_map["duration"]]))
                    except (ValueError, TypeError):
                        pass
                if "description" in col_map and col_map["description"] < len(row):
                    d_dict["description"] = str(row[col_map["description"]]).strip()

                disruptions.append(d_dict)

        return disruptions

    # ── Industrial Optional Sheet Parsers ──

    def _parse_production_lines(self, sheet):
        lines = []
        rows = list(sheet.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            return []
        headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
        col_map = {h: idx for idx, h in enumerate(headers) if h}
        for row in rows[1:]:
            if not any(row):
                continue
            l_id = str(row[col_map.get("line_id", 0)]).strip() if "line_id" in col_map else f"LINE-{len(lines)+1}"
            lines.append({
                "line_id": l_id,
                "line_name": str(row[col_map["line_name"]]).strip() if "line_name" in col_map and col_map["line_name"] < len(row) else l_id,
                "plant_area": str(row[col_map["plant_area"]]).strip() if "plant_area" in col_map and col_map["plant_area"] < len(row) else "Main Bay",
                "shift_pattern": str(row[col_map["shift_pattern"]]).strip() if "shift_pattern" in col_map and col_map["shift_pattern"] < len(row) else "2_SHIFT",
                "capacity_units_per_hour": int(float(row[col_map["capacity_units_per_hour"]])) if "capacity_units_per_hour" in col_map and col_map["capacity_units_per_hour"] < len(row) and row[col_map["capacity_units_per_hour"]] is not None else 50,
                "status": str(row[col_map["status"]]).strip() if "status" in col_map and col_map["status"] < len(row) else "OPERATIONAL",
                "primary_product_family": str(row[col_map["primary_product_family"]]).strip() if "primary_product_family" in col_map and col_map["primary_product_family"] < len(row) else "Precision Parts",
            })
        return lines

    def _parse_machine_capabilities(self, sheet, valid_machine_ids):
        caps = []
        rows = list(sheet.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            return []
        headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
        col_map = {h: idx for idx, h in enumerate(headers) if h}
        for row_idx, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue
            m_id = str(row[col_map.get("machine_id", 0)]).strip() if "machine_id" in col_map and col_map["machine_id"] < len(row) else None
            if not m_id:
                continue
            if m_id not in valid_machine_ids:
                self.add_error("Machine_Capabilities", row_idx, "machine_id", f"Machine '{m_id}' not found in Machines sheet")
                continue
            caps.append({
                "machine_id": m_id,
                "capability": str(row[col_map["capability"]]).strip() if "capability" in col_map and col_map["capability"] < len(row) else "GENERAL",
                "product_family": str(row[col_map["product_family"]]).strip() if "product_family" in col_map and col_map["product_family"] < len(row) else "Components",
                "min_batch_size": int(float(row[col_map["min_batch_size"]])) if "min_batch_size" in col_map and col_map["min_batch_size"] < len(row) and row[col_map["min_batch_size"]] is not None else 10,
                "max_batch_size": int(float(row[col_map["max_batch_size"]])) if "max_batch_size" in col_map and col_map["max_batch_size"] < len(row) and row[col_map["max_batch_size"]] is not None else 500,
                "setup_time_min": int(float(row[col_map["setup_time_min"]])) if "setup_time_min" in col_map and col_map["setup_time_min"] < len(row) and row[col_map["setup_time_min"]] is not None else 15,
                "quality_rating": float(row[col_map["quality_rating"]]) if "quality_rating" in col_map and col_map["quality_rating"] < len(row) and row[col_map["quality_rating"]] is not None else 0.98,
            })
        return caps

    def _parse_production_orders(self, sheet):
        orders = []
        rows = list(sheet.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            return []
        headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
        col_map = {h: idx for idx, h in enumerate(headers) if h}
        seen_order_ids = set()
        for row_idx, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue
            o_id = str(row[col_map.get("order_id", 0)]).strip() if "order_id" in col_map and col_map["order_id"] < len(row) else f"ORD-{len(orders)+1}"
            if o_id in seen_order_ids:
                self.add_error("Production_Orders", row_idx, "order_id", f"Duplicate order_id '{o_id}'")
                continue
            seen_order_ids.add(o_id)

            orders.append({
                "order_id": o_id,
                "product_id": str(row[col_map["product_id"]]).strip() if "product_id" in col_map and col_map["product_id"] < len(row) else "P-01",
                "product_name": str(row[col_map["product_name"]]).strip() if "product_name" in col_map and col_map["product_name"] < len(row) else o_id,
                "customer": str(row[col_map["customer"]]).strip() if "customer" in col_map and col_map["customer"] < len(row) else "Commercial Client",
                "quantity": int(float(row[col_map["quantity"]])) if "quantity" in col_map and col_map["quantity"] < len(row) and row[col_map["quantity"]] is not None else 100,
                "priority": int(float(row[col_map["priority"]])) if "priority" in col_map and col_map["priority"] < len(row) and row[col_map["priority"]] is not None else 3,
                "release_time": str(row[col_map["release_time"]]).strip() if "release_time" in col_map and col_map["release_time"] < len(row) else "06:00",
                "deadline": int(float(row[col_map["deadline"]])) if "deadline" in col_map and col_map["deadline"] < len(row) and row[col_map["deadline"]] is not None else 120,
                "status": str(row[col_map["status"]]).strip() if "status" in col_map and col_map["status"] < len(row) else "In Production",
                "material_required": str(row[col_map["material_required"]]).strip() if "material_required" in col_map and col_map["material_required"] < len(row) else "RM-001",
                "quality_requirement": float(row[col_map["quality_requirement"]]) if "quality_requirement" in col_map and col_map["quality_requirement"] < len(row) and row[col_map["quality_requirement"]] is not None else 0.98,
            })
        return orders

    def _parse_operations(self, sheet, valid_job_ids, valid_machine_ids):
        ops = []
        rows = list(sheet.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            return []
        headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
        col_map = {h: idx for idx, h in enumerate(headers) if h}
        seen_op_ids = set()
        for row_idx, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue
            op_id = str(row[col_map.get("operation_id", 0)]).strip() if "operation_id" in col_map and col_map["operation_id"] < len(row) else f"OP-{len(ops)+1}"
            if op_id in seen_op_ids:
                self.add_error("Operations", row_idx, "operation_id", f"Duplicate operation_id '{op_id}'")
                continue
            seen_op_ids.add(op_id)

            j_id = str(row[col_map.get("job_id", 1)]).strip() if "job_id" in col_map and col_map["job_id"] < len(row) else None
            if j_id and j_id not in valid_job_ids:
                self.add_error("Operations", row_idx, "job_id", f"job_id '{j_id}' not found in Jobs sheet")

            ops.append({
                "operation_id": op_id,
                "job_id": j_id or "J01",
                "operation_sequence": int(float(row[col_map["operation_sequence"]])) if "operation_sequence" in col_map and col_map["operation_sequence"] < len(row) and row[col_map["operation_sequence"]] is not None else 1,
                "operation_name": str(row[col_map["operation_name"]]).strip() if "operation_name" in col_map and col_map["operation_name"] < len(row) else op_id,
                "processing_time": int(float(row[col_map["processing_time"]])) if "processing_time" in col_map and col_map["processing_time"] < len(row) and row[col_map["processing_time"]] is not None else 20,
                "eligible_machines": [m.strip() for m in str(row[col_map["eligible_machines"]]).split(",") if m.strip()] if "eligible_machines" in col_map and col_map["eligible_machines"] < len(row) and row[col_map["eligible_machines"]] else valid_machine_ids,
                "setup_time": int(float(row[col_map["setup_time"]])) if "setup_time" in col_map and col_map["setup_time"] < len(row) and row[col_map["setup_time"]] is not None else 5,
                "material_required": str(row[col_map["material_required"]]).strip() if "material_required" in col_map and col_map["material_required"] < len(row) else "RM-001",
                "quantity": int(float(row[col_map["quantity"]])) if "quantity" in col_map and col_map["quantity"] < len(row) and row[col_map["quantity"]] is not None else 100,
                "precedence": str(row[col_map["precedence"]]).strip() if "precedence" in col_map and col_map["precedence"] < len(row) else "NONE",
                "quality_requirement": float(row[col_map["quality_requirement"]]) if "quality_requirement" in col_map and col_map["quality_requirement"] < len(row) and row[col_map["quality_requirement"]] is not None else 0.98,
            })
        return ops

    def _parse_materials(self, sheet):
        mats = []
        rows = list(sheet.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            return []
        headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
        col_map = {h: idx for idx, h in enumerate(headers) if h}
        seen_mat_ids = set()
        for row_idx, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue
            m_id = str(row[col_map.get("material_id", 0)]).strip() if "material_id" in col_map and col_map["material_id"] < len(row) else f"RM-{len(mats)+1:03d}"
            if m_id in seen_mat_ids:
                self.add_error("Materials", row_idx, "material_id", f"Duplicate material_id '{m_id}'")
                continue
            seen_mat_ids.add(m_id)

            cost = 15.0
            if "standard_cost" in col_map and col_map["standard_cost"] < len(row) and row[col_map["standard_cost"]] is not None:
                try:
                    cost = float(row[col_map["standard_cost"]])
                    if cost < 0:
                        self.add_error("Materials", row_idx, "standard_cost", "standard_cost cannot be negative")
                except ValueError:
                    self.add_error("Materials", row_idx, "standard_cost", "Invalid numeric value")

            mats.append({
                "material_id": m_id,
                "material_name": str(row[col_map["material_name"]]).strip() if "material_name" in col_map and col_map["material_name"] < len(row) else m_id,
                "material_type": str(row[col_map["material_type"]]).strip() if "material_type" in col_map and col_map["material_type"] < len(row) else "RAW_MATERIAL",
                "unit": str(row[col_map["unit"]]).strip() if "unit" in col_map and col_map["unit"] < len(row) else "kg",
                "standard_cost": cost,
                "supplier": str(row[col_map["supplier"]]).strip() if "supplier" in col_map and col_map["supplier"] < len(row) else "Primary Supplier",
                "lead_time_hours": int(float(row[col_map["lead_time_hours"]])) if "lead_time_hours" in col_map and col_map["lead_time_hours"] < len(row) and row[col_map["lead_time_hours"]] is not None else 24,
                "quality_grade": str(row[col_map["quality_grade"]]).strip() if "quality_grade" in col_map and col_map["quality_grade"] < len(row) else "A",
            })
        return mats

    def _parse_inventory(self, sheet, valid_material_ids):
        inv = []
        rows = list(sheet.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            return []
        headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
        col_map = {h: idx for idx, h in enumerate(headers) if h}
        seen_inv_ids = set()
        for row_idx, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue
            m_id = str(row[col_map.get("material_id", 0)]).strip() if "material_id" in col_map and col_map["material_id"] < len(row) else None
            if not m_id:
                continue
            if m_id in seen_inv_ids:
                self.add_error("Inventory", row_idx, "material_id", f"Duplicate material_id '{m_id}' in Inventory")
                continue
            seen_inv_ids.add(m_id)

            avail = 1000
            if "available_quantity" in col_map and col_map["available_quantity"] < len(row) and row[col_map["available_quantity"]] is not None:
                try:
                    avail = int(float(row[col_map["available_quantity"]]))
                    if avail < 0:
                        self.add_error("Inventory", row_idx, "available_quantity", "available_quantity cannot be negative")
                except ValueError:
                    self.add_error("Inventory", row_idx, "available_quantity", "Invalid integer value")

            res = 0
            if "reserved_quantity" in col_map and col_map["reserved_quantity"] < len(row) and row[col_map["reserved_quantity"]] is not None:
                try:
                    res = int(float(row[col_map["reserved_quantity"]]))
                    if res < 0:
                        self.add_error("Inventory", row_idx, "reserved_quantity", "reserved_quantity cannot be negative")
                except ValueError:
                    pass

            inv.append({
                "material_id": m_id,
                "material_name": str(row[col_map["material_name"]]).strip() if "material_name" in col_map and col_map["material_name"] < len(row) else m_id,
                "unit": str(row[col_map["unit"]]).strip() if "unit" in col_map and col_map["unit"] < len(row) else "units",
                "available_quantity": avail,
                "reserved_quantity": res,
                "incoming_quantity": int(float(row[col_map["incoming_quantity"]])) if "incoming_quantity" in col_map and col_map["incoming_quantity"] < len(row) and row[col_map["incoming_quantity"]] is not None else 500,
                "reorder_level": int(float(row[col_map["reorder_level"]])) if "reorder_level" in col_map and col_map["reorder_level"] < len(row) and row[col_map["reorder_level"]] is not None else 300,
                "safety_stock": int(float(row[col_map["safety_stock"]])) if "safety_stock" in col_map and col_map["safety_stock"] < len(row) and row[col_map["safety_stock"]] is not None else 100,
                "lead_time_hours": int(float(row[col_map["lead_time_hours"]])) if "lead_time_hours" in col_map and col_map["lead_time_hours"] < len(row) and row[col_map["lead_time_hours"]] is not None else 24,
                "supplier": str(row[col_map["supplier"]]).strip() if "supplier" in col_map and col_map["supplier"] < len(row) else "Vendor",
                "status": str(row[col_map["status"]]).strip() if "status" in col_map and col_map["status"] < len(row) else "IN_STOCK",
            })
        return inv

    def _parse_maintenance(self, sheet, valid_machine_ids):
        maint = []
        rows = list(sheet.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            return []
        headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
        col_map = {h: idx for idx, h in enumerate(headers) if h}
        seen_m_ids = set()
        for row_idx, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue
            m_id = str(row[col_map.get("maintenance_id", 0)]).strip() if "maintenance_id" in col_map and col_map["maintenance_id"] < len(row) else f"MNT-{len(maint)+1:02d}"
            if m_id in seen_m_ids:
                self.add_error("Maintenance", row_idx, "maintenance_id", f"Duplicate maintenance_id '{m_id}'")
                continue
            seen_m_ids.add(m_id)

            mach_id = str(row[col_map.get("machine_id", 1)]).strip() if "machine_id" in col_map and col_map["machine_id"] < len(row) else None
            if mach_id and mach_id not in valid_machine_ids:
                self.add_error("Maintenance", row_idx, "machine_id", f"machine_id '{mach_id}' not found in Machines sheet")

            dur = 60
            if "duration_minutes" in col_map and col_map["duration_minutes"] < len(row) and row[col_map["duration_minutes"]] is not None:
                try:
                    dur = int(float(row[col_map["duration_minutes"]]))
                    if dur <= 0:
                        self.add_error("Maintenance", row_idx, "duration_minutes", "duration_minutes must be positive")
                except ValueError:
                    self.add_error("Maintenance", row_idx, "duration_minutes", "Invalid integer duration")

            maint.append({
                "maintenance_id": m_id,
                "machine_id": mach_id or "M01",
                "maintenance_type": str(row[col_map["maintenance_type"]]).strip() if "maintenance_type" in col_map and col_map["maintenance_type"] < len(row) else "PREVENTIVE",
                "scheduled_start": str(row[col_map["scheduled_start"]]).strip() if "scheduled_start" in col_map and col_map["scheduled_start"] < len(row) else "12:00",
                "scheduled_end": str(row[col_map["scheduled_end"]]).strip() if "scheduled_end" in col_map and col_map["scheduled_end"] < len(row) else "13:00",
                "duration_minutes": dur,
                "maintenance_priority": str(row[col_map["maintenance_priority"]]).strip() if "maintenance_priority" in col_map and col_map["maintenance_priority"] < len(row) else "MEDIUM",
                "reason": str(row[col_map["reason"]]).strip() if "reason" in col_map and col_map["reason"] < len(row) else "Scheduled maintenance",
                "status": str(row[col_map["status"]]).strip() if "status" in col_map and col_map["status"] < len(row) else "SCHEDULED",
            })
        return maint

    def _parse_downtime(self, sheet, valid_machine_ids):
        dt = []
        rows = list(sheet.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            return []
        headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
        col_map = {h: idx for idx, h in enumerate(headers) if h}
        seen_d_ids = set()
        for row_idx, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue
            d_id = str(row[col_map.get("downtime_id", 0)]).strip() if "downtime_id" in col_map and col_map["downtime_id"] < len(row) else f"DWN-{len(dt)+1:02d}"
            if d_id in seen_d_ids:
                self.add_error("Downtime", row_idx, "downtime_id", f"Duplicate downtime_id '{d_id}'")
                continue
            seen_d_ids.add(d_id)

            mach_id = str(row[col_map.get("machine_id", 1)]).strip() if "machine_id" in col_map and col_map["machine_id"] < len(row) else None
            if mach_id and mach_id not in valid_machine_ids:
                self.add_error("Downtime", row_idx, "machine_id", f"machine_id '{mach_id}' not found in Machines sheet")

            dt.append({
                "downtime_id": d_id,
                "machine_id": mach_id or "M01",
                "start_time": str(row[col_map["start_time"]]).strip() if "start_time" in col_map and col_map["start_time"] < len(row) else "08:00",
                "end_time": str(row[col_map["end_time"]]).strip() if "end_time" in col_map and col_map["end_time"] < len(row) else "09:00",
                "duration_minutes": int(float(row[col_map["duration_minutes"]])) if "duration_minutes" in col_map and col_map["duration_minutes"] < len(row) and row[col_map["duration_minutes"]] is not None else 30,
                "downtime_type": str(row[col_map["downtime_type"]]).strip() if "downtime_type" in col_map and col_map["downtime_type"] < len(row) else "UNPLANNED",
                "reason": str(row[col_map["reason"]]).strip() if "reason" in col_map and col_map["reason"] < len(row) else "Station stoppage",
                "planned": str(row[col_map["planned"]]).strip() if "planned" in col_map and col_map["planned"] < len(row) else "FALSE",
                "impact_level": str(row[col_map["impact_level"]]).strip() if "impact_level" in col_map and col_map["impact_level"] < len(row) else "LOW",
            })
        return dt

    def _parse_energy(self, sheet, valid_machine_ids):
        energy = []
        rows = list(sheet.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            return []
        headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
        col_map = {h: idx for idx, h in enumerate(headers) if h}
        for row_idx, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue
            mach_id = str(row[col_map.get("machine_id", 1)]).strip() if "machine_id" in col_map and col_map["machine_id"] < len(row) else None
            if mach_id and mach_id not in valid_machine_ids:
                self.add_error("Energy", row_idx, "machine_id", f"machine_id '{mach_id}' not found in Machines sheet")

            energy.append({
                "energy_id": str(row[col_map.get("energy_id", 0)]).strip() if "energy_id" in col_map and col_map["energy_id"] < len(row) else f"ENG-{len(energy)+1}",
                "machine_id": mach_id or "M01",
                "timestamp": str(row[col_map["timestamp"]]).strip() if "timestamp" in col_map and col_map["timestamp"] < len(row) else "08:00",
                "power_kw": float(row[col_map["power_kw"]]) if "power_kw" in col_map and col_map["power_kw"] < len(row) and row[col_map["power_kw"]] is not None else 8.0,
                "energy_kwh": float(row[col_map["energy_kwh"]]) if "energy_kwh" in col_map and col_map["energy_kwh"] < len(row) and row[col_map["energy_kwh"]] is not None else 8.0,
                "operating_state": str(row[col_map["operating_state"]]).strip() if "operating_state" in col_map and col_map["operating_state"] < len(row) else "RUNNING",
                "job_id": str(row[col_map["job_id"]]).strip() if "job_id" in col_map and col_map["job_id"] < len(row) else "NONE",
            })
        return energy

    def _parse_quality(self, sheet, valid_job_ids, valid_machine_ids):
        quality = []
        rows = list(sheet.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            return []
        headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
        col_map = {h: idx for idx, h in enumerate(headers) if h}
        for row_idx, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue
            mach_id = str(row[col_map.get("machine_id", 3)]).strip() if "machine_id" in col_map and col_map["machine_id"] < len(row) else None
            if mach_id and mach_id not in valid_machine_ids:
                self.add_error("Quality", row_idx, "machine_id", f"machine_id '{mach_id}' not found in Machines sheet")

            quality.append({
                "inspection_id": str(row[col_map.get("inspection_id", 0)]).strip() if "inspection_id" in col_map and col_map["inspection_id"] < len(row) else f"QC-{len(quality)+1}",
                "job_id": str(row[col_map["job_id"]]).strip() if "job_id" in col_map and col_map["job_id"] < len(row) else "J01",
                "operation_id": str(row[col_map["operation_id"]]).strip() if "operation_id" in col_map and col_map["operation_id"] < len(row) else "OP-01",
                "machine_id": mach_id or "M01",
                "quantity_produced": int(float(row[col_map["quantity_produced"]])) if "quantity_produced" in col_map and col_map["quantity_produced"] < len(row) and row[col_map["quantity_produced"]] is not None else 100,
                "quantity_rejected": int(float(row[col_map["quantity_rejected"]])) if "quantity_rejected" in col_map and col_map["quantity_rejected"] < len(row) and row[col_map["quantity_rejected"]] is not None else 0,
                "defect_rate": float(row[col_map["defect_rate"]]) if "defect_rate" in col_map and col_map["defect_rate"] < len(row) and row[col_map["defect_rate"]] is not None else 0.0,
                "quality_score": float(row[col_map["quality_score"]]) if "quality_score" in col_map and col_map["quality_score"] < len(row) and row[col_map["quality_score"]] is not None else 1.0,
                "inspection_time": str(row[col_map["inspection_time"]]).strip() if "inspection_time" in col_map and col_map["inspection_time"] < len(row) else "08:00",
            })
        return quality

    def _parse_shifts(self, sheet):
        shifts = []
        rows = list(sheet.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            return []
        headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
        col_map = {h: idx for idx, h in enumerate(headers) if h}
        for row in rows[1:]:
            if not any(row):
                continue
            s_id = str(row[col_map.get("shift_id", 0)]).strip() if "shift_id" in col_map and col_map["shift_id"] < len(row) else f"SHIFT-{len(shifts)+1}"
            shifts.append({
                "shift_id": s_id,
                "shift_name": str(row[col_map["shift_name"]]).strip() if "shift_name" in col_map and col_map["shift_name"] < len(row) else s_id,
                "start_time": str(row[col_map["start_time"]]).strip() if "start_time" in col_map and col_map["start_time"] < len(row) else "06:00",
                "end_time": str(row[col_map["end_time"]]).strip() if "end_time" in col_map and col_map["end_time"] < len(row) else "14:00",
                "working_hours": float(row[col_map["working_hours"]]) if "working_hours" in col_map and col_map["working_hours"] < len(row) and row[col_map["working_hours"]] is not None else 8.0,
                "available_machine_count": int(float(row[col_map["available_machine_count"]])) if "available_machine_count" in col_map and col_map["available_machine_count"] < len(row) and row[col_map["available_machine_count"]] is not None else 6,
            })
        return shifts

    def _parse_dependencies(self, sheet, valid_job_ids):
        deps = []
        rows = list(sheet.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            return []
        headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
        col_map = {h: idx for idx, h in enumerate(headers) if h}
        for row_idx, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue
            j_id = str(row[col_map.get("job_id", 1)]).strip() if "job_id" in col_map and col_map["job_id"] < len(row) else None
            dep_id = str(row[col_map.get("depends_on_job_id", 2)]).strip() if "depends_on_job_id" in col_map and col_map["depends_on_job_id"] < len(row) else None

            if j_id and j_id not in valid_job_ids:
                self.add_error("Dependencies", row_idx, "job_id", f"job_id '{j_id}' not found in Jobs sheet")
            if dep_id and dep_id not in valid_job_ids:
                self.add_error("Dependencies", row_idx, "depends_on_job_id", f"depends_on_job_id '{dep_id}' not found in Jobs sheet")

            deps.append({
                "dependency_id": str(row[col_map.get("dependency_id", 0)]).strip() if "dependency_id" in col_map and col_map["dependency_id"] < len(row) else f"DEP-{len(deps)+1}",
                "job_id": j_id or "J02",
                "depends_on_job_id": dep_id or "J01",
                "dependency_type": str(row[col_map["dependency_type"]]).strip() if "dependency_type" in col_map and col_map["dependency_type"] < len(row) else "PRECEDENCE",
                "minimum_gap_minutes": int(float(row[col_map["minimum_gap_minutes"]])) if "minimum_gap_minutes" in col_map and col_map["minimum_gap_minutes"] < len(row) and row[col_map["minimum_gap_minutes"]] is not None else 5,
            })
        return deps

    def _parse_scenarios(self, sheet):
        scenarios = []
        rows = list(sheet.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            return []
        headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
        col_map = {h: idx for idx, h in enumerate(headers) if h}
        for row in rows[1:]:
            if not any(row):
                continue
            scenarios.append({
                "scenario_id": int(float(row[col_map["scenario_id"]])) if "scenario_id" in col_map and col_map["scenario_id"] < len(row) and row[col_map["scenario_id"]] is not None else len(scenarios) + 1,
                "scenario_name": str(row[col_map["scenario_name"]]).strip() if "scenario_name" in col_map and col_map["scenario_name"] < len(row) else f"Scenario {len(scenarios)+1}",
                "category": str(row[col_map["category"]]).strip() if "category" in col_map and col_map["category"] < len(row) else "Operational",
                "target_id": str(row[col_map["target_id"]]).strip() if "target_id" in col_map and col_map["target_id"] < len(row) else "M03",
                "trigger_type": str(row[col_map["trigger_type"]]).strip() if "trigger_type" in col_map and col_map["trigger_type"] < len(row) else "machine_failure",
                "expected_action": str(row[col_map["expected_action"]]).strip() if "expected_action" in col_map and col_map["expected_action"] < len(row) else "Reroute affected jobs",
                "business_impact": str(row[col_map["business_impact"]]).strip() if "business_impact" in col_map and col_map["business_impact"] < len(row) else "Protects delivery deadlines",
            })
        return scenarios

    def _build_success_result(self, machines, jobs, disruptions, filename, auto_converted=False, normalized_data=None):
        total_energy_capacity = sum(m["energy_kwh_per_hour"] for m in machines.values())
        norm = normalized_data or {}
        summary = {
            "machines_count": len(machines),
            "jobs_count": len(jobs),
            "available_machines_count": len([m for m in machines.values() if m["status"] == "available"]),
            "unavailable_machines_count": len([m for m in machines.values() if m["status"] != "available"]),
            "total_energy_capacity_kwh": round(total_energy_capacity, 2),
            "high_priority_jobs": len([j for j in jobs if j.get("priority", 3) >= 4]),
            "disruptions_count": len(disruptions),
            "production_lines_count": len(norm.get("production_lines", [])),
            "production_orders_count": len(norm.get("production_orders", [])),
            "operations_count": len(norm.get("operations", [])),
            "inventory_items_count": len(norm.get("inventory", [])),
            "scenarios_count": len(norm.get("scenarios", [])),
        }

        res = {
            "success": True,
            "errors": [],
            "error_messages": [],
            "machines": machines,
            "jobs": jobs,
            "disruptions": disruptions,
            "summary": summary,
            "data_source": filename,
            "auto_converted": auto_converted,
            "transformations": self.transformations,
        }
        res.update(norm)
        res["machines"] = machines
        res["jobs"] = jobs
        res["disruptions"] = disruptions
        return res

    def _build_error_result(self, filename="uploaded.xlsx"):
        formatted_messages = [
            f"• [{e['sheet']}] Row {e['row']}: {e['column']} — {e['message']}" if e['row'] > 0
            else f"• [{e['sheet']}]: {e['message']}"
            for e in self.errors
        ]
        return {
            "success": False,
            "errors": self.errors,
            "error_messages": formatted_messages,
            "machines": None,
            "jobs": None,
            "disruptions": None,
            "summary": None,
            "data_source": filename,
            "auto_converted": False,
            "transformations": self.transformations,
        }
