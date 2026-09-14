"""
Job model for FlowForge factory simulation.

Each job has an ID, processing duration, deadline, priority,
eligible machines, and current status.
"""
from copy import deepcopy


# Default 12-job dataset for the simulated factory.
# Durations and deadlines produce visible scheduling conflicts.
DEFAULT_JOBS = [
    {"job_id": "J1",  "duration": 45, "deadline": 200, "priority": 2, "eligible_machines": ["M1", "M2", "M3", "M4", "M5", "M6"], "status": "pending"},
    {"job_id": "J2",  "duration": 30, "deadline": 120, "priority": 3, "eligible_machines": ["M1", "M2", "M3", "M4", "M5", "M6"], "status": "pending"},
    {"job_id": "J3",  "duration": 60, "deadline": 250, "priority": 1, "eligible_machines": ["M1", "M2", "M3", "M4", "M5", "M6"], "status": "pending"},
    {"job_id": "J4",  "duration": 35, "deadline": 150, "priority": 2, "eligible_machines": ["M1", "M2", "M3", "M4", "M5", "M6"], "status": "pending"},
    {"job_id": "J5",  "duration": 50, "deadline": 180, "priority": 3, "eligible_machines": ["M1", "M2", "M3", "M4", "M5", "M6"], "status": "pending"},
    {"job_id": "J6",  "duration": 25, "deadline": 100, "priority": 4, "eligible_machines": ["M1", "M2", "M3", "M4", "M5", "M6"], "status": "pending"},
    {"job_id": "J7",  "duration": 55, "deadline": 220, "priority": 2, "eligible_machines": ["M1", "M2", "M3", "M4", "M5", "M6"], "status": "pending"},
    {"job_id": "J8",  "duration": 40, "deadline": 160, "priority": 3, "eligible_machines": ["M1", "M2", "M3", "M4", "M5", "M6"], "status": "pending"},
    {"job_id": "J9",  "duration": 20, "deadline": 90,  "priority": 5, "eligible_machines": ["M1", "M2", "M3", "M4", "M5", "M6"], "status": "pending"},
    {"job_id": "J10", "duration": 65, "deadline": 300, "priority": 1, "eligible_machines": ["M1", "M2", "M3", "M4", "M5", "M6"], "status": "pending"},
    {"job_id": "J11", "duration": 30, "deadline": 140, "priority": 3, "eligible_machines": ["M1", "M2", "M3", "M4", "M5", "M6"], "status": "pending"},
    {"job_id": "J12", "duration": 45, "deadline": 260, "priority": 2, "eligible_machines": ["M1", "M2", "M3", "M4", "M5", "M6"], "status": "pending"},
]

# Valid job statuses
JOB_STATUS_PENDING = "pending"
JOB_STATUS_SCHEDULED = "scheduled"
JOB_STATUS_CANCELLED = "cancelled"


def get_default_jobs():
    """Return a deep copy of the default 12-job factory dataset."""
    return deepcopy(DEFAULT_JOBS)


def get_active_jobs(jobs):
    """Return jobs that are not cancelled."""
    return [j for j in jobs if j.get("status") != JOB_STATUS_CANCELLED]


def cancel_job(jobs, job_id):
    """
    Mark a job as cancelled.
    Returns the cancelled job dict, or None if not found.
    """
    for job in jobs:
        if job["job_id"] == job_id:
            if job["status"] == JOB_STATUS_CANCELLED:
                return None  # already cancelled
            job["status"] = JOB_STATUS_CANCELLED
            return job
    return None


def update_deadline(jobs, job_id, new_deadline):
    """
    Update a job's deadline.
    Returns the updated job dict, or None if not found.
    """
    for job in jobs:
        if job["job_id"] == job_id:
            old_deadline = job["deadline"]
            job["deadline"] = new_deadline
            return {"job": job, "old_deadline": old_deadline, "new_deadline": new_deadline}
    return None


def add_urgent_job(jobs, job_id, duration, deadline, priority=5):
    """
    Add an urgent job to the job list.
    Returns the new job dict.
    """
    new_job = {
        "job_id": job_id,
        "duration": duration,
        "deadline": deadline,
        "priority": priority,
        "eligible_machines": ["M1", "M2", "M3", "M4", "M5", "M6"],
        "status": JOB_STATUS_PENDING,
    }
    jobs.append(new_job)
    return new_job


def filter_jobs_for_machines(jobs, available_machine_ids):
    """
    Return jobs that have at least one eligible machine available.
    Jobs with no eligible machines remaining are flagged.
    """
    feasible = []
    infeasible = []
    for job in jobs:
        eligible = job.get("eligible_machines", available_machine_ids)
        if any(m in available_machine_ids for m in eligible):
            feasible.append(job)
        else:
            infeasible.append(job)
    return feasible, infeasible
