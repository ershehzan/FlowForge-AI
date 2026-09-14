"""
JSON Factory Parser for FlowForge.

Parses factory configuration and job shop problem instances from JSON format.
Supports:
1. Operation-level Job Shop format with unavailable periods (as specified by user):
   {
     "machines": [{"machine_id": 0, "unavailable_periods": [[7, 12]]}, ...],
     "jobs": [{"job_id": 0, "due_date": 15, "priority": 2, "operations": [...]}, ...]
   }
2. Standard FlowForge entity JSON format.
"""
import json
import re


def _normalize_machine_id(raw_id):
    """Normalize numeric machine ID (e.g. 0 -> M0) or preserve string ID."""
    if isinstance(raw_id, int) or (isinstance(raw_id, str) and raw_id.isdigit()):
        return f"M{raw_id}"
    return str(raw_id).strip()


def _normalize_job_id(raw_id):
    """Normalize numeric job ID (e.g. 0 -> J0) or preserve string ID."""
    if isinstance(raw_id, int) or (isinstance(raw_id, str) and raw_id.isdigit()):
        return f"J{raw_id}"
    return str(raw_id).strip()


class JsonParser:
    """Parser and validator for JSON factory datasets."""

    def __init__(self):
        self.errors = []
        self.transformations = []

    def parse(self, file_content_or_str, filename="factory.json"):
        """
        Parse JSON content into FlowForge internal Machine and Job representation.

        Args:
            file_content_or_str: bytes, string, or file-like object containing JSON.
            filename: name of source file.

        Returns:
            dict containing success, machines, jobs, disruptions, summary, etc.
        """
        self.errors = []
        self.transformations = []

        try:
            if isinstance(file_content_or_str, (bytes, bytearray)):
                text = file_content_or_str.decode("utf-8")
            elif hasattr(file_content_or_str, "read"):
                text = file_content_or_str.read()
                if isinstance(text, bytes):
                    text = text.decode("utf-8")
            else:
                text = str(file_content_or_str)

            data = json.loads(text)
        except Exception as e:
            return {
                "success": False,
                "errors": [{"sheet": "JSON", "row": 0, "column": "Syntax", "message": f"Invalid JSON syntax: {str(e)}"}],
                "error_messages": [f"JSON Parse Error: {str(e)}"],
                "machines": None,
                "jobs": None,
                "disruptions": None,
                "summary": None,
                "data_source": filename,
                "auto_converted": False,
                "transformations": [],
            }

        if not isinstance(data, dict):
            return {
                "success": False,
                "errors": [{"sheet": "JSON", "row": 0, "column": "Root", "message": "Root JSON element must be an object containing 'machines' and/or 'jobs'."}],
                "error_messages": ["JSON Root must be an object containing 'machines' and/or 'jobs'."],
                "machines": None,
                "jobs": None,
                "disruptions": None,
                "summary": None,
                "data_source": filename,
                "auto_converted": False,
                "transformations": [],
            }

        raw_machines = data.get("machines", [])
        raw_jobs = data.get("jobs", [])

        if not raw_machines and not raw_jobs:
            return {
                "success": False,
                "errors": [{"sheet": "JSON", "row": 0, "column": "Empty", "message": "JSON file contains neither 'machines' nor 'jobs'."}],
                "error_messages": ["No 'machines' or 'jobs' arrays found in JSON."],
                "machines": None,
                "jobs": None,
                "disruptions": None,
                "summary": None,
                "data_source": filename,
                "auto_converted": False,
                "transformations": [],
            }

        # 1. Parse Machines
        machines_dict = {}
        machine_unavail_map = {}
        disruptions = []

        for idx, m in enumerate(raw_machines):
            raw_m_id = m.get("machine_id", m.get("id", idx))
            m_id = _normalize_machine_id(raw_m_id)
            unavail = m.get("unavailable_periods", [])
            machine_unavail_map[m_id] = unavail

            # Energy consumption parameter (kWh/hour)
            energy = float(m.get("energy_kwh_per_hour", 7.5 + (idx * 1.5)))
            capacity = int(m.get("capacity", 1))
            status = m.get("status", "available")

            machines_dict[m_id] = {
                "id": m_id,
                "name": m.get("name", f"Machine {m_id}"),
                "status": status,
                "energy_kwh_per_hour": energy,
                "capacity": capacity,
                "unavailable_periods": unavail,
            }

            # Convert unavailable periods into disruptions for simulation/timeline
            for period in unavail:
                if len(period) >= 2:
                    p_start, p_end = period[0], period[1]
                    disruptions.append({
                        "type": "machine_failure",
                        "machine_id": m_id,
                        "time_window": [p_start, p_end],
                        "start": p_start,
                        "end": p_end,
                        "duration": p_end - p_start,
                        "description": f"{m_id} Unavailable [{p_start}m - {p_end}m]",
                    })

        # 2. Parse Jobs
        jobs_list = []
        for idx, j in enumerate(raw_jobs):
            raw_j_id = j.get("job_id", j.get("id", idx))
            j_id = _normalize_job_id(raw_j_id)
            due = int(j.get("due_date", j.get("deadline", j.get("due", 100))))
            priority = int(j.get("priority", 2))

            operations = j.get("operations", [])
            normalized_ops = []

            for op in operations:
                raw_op_m = op.get("machine_id", op.get("machine", 0))
                op_m = _normalize_machine_id(raw_op_m)
                op_dur = int(op.get("processing_time", op.get("duration", 5)))
                normalized_ops.append({
                    "machine": op_m,
                    "duration": op_dur,
                })

                # If machine was not explicitly listed in machines array, synthesize it
                if op_m not in machines_dict:
                    machines_dict[op_m] = {
                        "id": op_m,
                        "name": f"Machine {op_m}",
                        "status": "available",
                        "energy_kwh_per_hour": 8.0,
                        "capacity": 1,
                        "unavailable_periods": [],
                    }
                    self.transformations.append(f"Auto-synthesized machine {op_m} from job {j_id} operation")

            if normalized_ops:
                total_duration = sum(op["duration"] for op in normalized_ops)
                eligible = list(dict.fromkeys(op["machine"] for op in normalized_ops))
            else:
                total_duration = int(j.get("duration", j.get("processing_time", 30)))
                raw_eligible = j.get("eligible_machines", list(machines_dict.keys()))
                eligible = [_normalize_machine_id(em) for em in raw_eligible]

            jobs_list.append({
                "job_id": j_id,
                "duration": total_duration,
                "deadline": due,
                "due": due,
                "priority": priority,
                "eligible_machines": eligible,
                "operations": normalized_ops,
                "status": "pending",
            })

        # Fallback if machines were empty
        if not machines_dict:
            for i in range(3):
                m_id = f"M{i}"
                machines_dict[m_id] = {
                    "id": m_id,
                    "name": f"Machine {m_id}",
                    "status": "available",
                    "energy_kwh_per_hour": 8.0,
                    "capacity": 1,
                    "unavailable_periods": [],
                }

        self.transformations.append(f"Successfully loaded {len(jobs_list)} jobs and {len(machines_dict)} machines from JSON")

        return {
            "success": True,
            "errors": [],
            "error_messages": [],
            "machines": machines_dict,
            "jobs": jobs_list,
            "disruptions": disruptions,
            "summary": {
                "machines": len(machines_dict),
                "jobs": len(jobs_list),
                "total_work_minutes": sum(j["duration"] for j in jobs_list),
            },
            "data_source": filename,
            "auto_converted": True,
            "transformations": self.transformations,
        }
