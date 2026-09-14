"""
Smart Excel Parser & Data Converter Engine for FlowForge.

Parses .xlsx and .xls factory production workbooks into internal
Machine and Job models for the autonomous scheduling engine.

Features:
  1. Standard parsing for well-formed Machines and Jobs sheets.
  2. Smart Excel Analyzer: automatically detects non-standard sheet names,
     fuzzy header synonyms, single-sheet spreadsheets, and synthesizes missing
     machine definitions from job table machine assignments.
  3. Transformation audit trail reporting mapping actions performed.
"""
import io
import re
import openpyxl


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
        lower_sheets = {name.lower().strip(): name for name in sheet_names}

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

            if not self.errors:
                return self._build_success_result(machines, jobs, disruptions, filename, auto_converted=False)
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

        # Fallback: if single sheet or unmapped, pick active sheet as Jobs sheet (if not already machines_sheet)
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

        # Ensure all referenced machines exist; synthesize if missing
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

        # Guarantee all jobs have valid eligible_machines
        valid_machine_ids = list(machines.keys())
        for j in jobs:
            if not j["eligible_machines"]:
                j["eligible_machines"] = valid_machine_ids
            else:
                j["eligible_machines"] = [m for m in j["eligible_machines"] if m in machines]
                if not j["eligible_machines"]:
                    j["eligible_machines"] = valid_machine_ids

        return self._build_success_result(machines, jobs, [], filename, auto_converted=True)

    def _fuzzy_parse_jobs(self, sheet):
        jobs = []
        referenced_machines = set()
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return [], set()

        headers = [str(cell).strip() if cell is not None else "" for cell in rows[0]]

        # Map columns using synonyms
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

            # Job ID
            raw_id = row[col_job_id] if col_job_id is not None and col_job_id < len(row) else None
            job_id = str(raw_id).strip() if raw_id is not None and str(raw_id).strip() != "" else f"J{len(jobs)+1}"

            # Processing Time / Duration
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

            # Eligible Machines
            eligible = []
            if col_eligible is not None and col_eligible < len(row):
                raw_em = row[col_eligible]
                if raw_em is not None and str(raw_em).strip() != "":
                    parts = [m.strip() for m in str(raw_em).split(",") if m.strip()]
                    eligible = parts
                    referenced_machines.update(parts)

            # Deadline
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

            # Priority
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

            machines[machine_id] = {
                "id": machine_id,
                "status": status_val,
                "energy_kwh_per_hour": energy_val,
                "capacity": 1,
            }

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

            jobs.append({
                "job_id": job_id,
                "duration": int(proc_time_val) if proc_time_val else 30,
                "deadline": int(deadline_val),
                "priority": priority_val,
                "eligible_machines": eligible_machines,
                "status": "pending",
            })

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
                disruptions.append({
                    "disruption_id": f"D{row_idx-1}",
                    "type": str(dtype).strip(),
                    "target_id": str(target).strip(),
                    "value": row[col_map.get("value", 2)] if "value" in col_map and col_map["value"] < len(row) else None
                })

        return disruptions

    def _build_success_result(self, machines, jobs, disruptions, filename, auto_converted=False):
        total_energy_capacity = sum(m["energy_kwh_per_hour"] for m in machines.values())
        summary = {
            "machines_count": len(machines),
            "jobs_count": len(jobs),
            "available_machines_count": len([m for m in machines.values() if m["status"] == "available"]),
            "unavailable_machines_count": len([m for m in machines.values() if m["status"] != "available"]),
            "total_energy_capacity_kwh": round(total_energy_capacity, 2),
            "high_priority_jobs": len([j for j in jobs if j.get("priority", 3) >= 4]),
            "disruptions_count": len(disruptions),
        }

        return {
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
