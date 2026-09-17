"""
Disruption event types for FlowForge.

Each disruption type is a dict with a 'type' key and type-specific details.
The model is designed to make it easy to add new disruption types later.

Supported disruption types:
  - machine_failure    : A machine becomes unavailable
  - machine_recovery   : A failed machine returns to service
  - urgent_job         : A high-priority job arrives unexpectedly
  - job_cancellation   : A scheduled job is cancelled
  - deadline_change    : A job's deadline is moved earlier or later
  - machine_downtime   : Planned machine maintenance
"""
import time


# Disruption type constants
MACHINE_FAILURE = "machine_failure"
MACHINE_RECOVERY = "machine_recovery"
URGENT_JOB = "urgent_job"
JOB_CANCELLATION = "job_cancellation"
DEADLINE_CHANGE = "deadline_change"
MACHINE_DOWNTIME = "machine_downtime"
PLANNED_DOWNTIME = "planned_downtime"
MAINTENANCE = "maintenance"
MATERIAL_SHORTAGE = "material_shortage"
QUALITY_ISSUE = "quality_issue"
MULTIPLE_FAILURE = "multiple_failure"
ENERGY_CONSTRAINT = "energy_constraint"

ALL_DISRUPTION_TYPES = [
    MACHINE_FAILURE,
    MACHINE_RECOVERY,
    URGENT_JOB,
    JOB_CANCELLATION,
    DEADLINE_CHANGE,
    MACHINE_DOWNTIME,
    PLANNED_DOWNTIME,
    MAINTENANCE,
    MATERIAL_SHORTAGE,
    QUALITY_ISSUE,
    MULTIPLE_FAILURE,
    ENERGY_CONSTRAINT,
]


def _make_disruption(disruption_type, **details):
    """Create a disruption event dict with timestamp."""
    return {
        "type": disruption_type,
        "timestamp": time.time(),
        **details,
    }


def machine_failure(machine_id):
    """Create a machine failure disruption event."""
    return _make_disruption(
        MACHINE_FAILURE,
        machine_id=machine_id,
        description=f"Machine {machine_id} has failed and is unavailable.",
    )


def machine_recovery(machine_id):
    """Create a machine recovery disruption event."""
    return _make_disruption(
        MACHINE_RECOVERY,
        machine_id=machine_id,
        description=f"Machine {machine_id} has been restored to service.",
    )


def urgent_job(job_id, duration, deadline, priority=5):
    """Create an urgent job arrival disruption event."""
    return _make_disruption(
        URGENT_JOB,
        job_id=job_id,
        duration=duration,
        deadline=deadline,
        priority=priority,
        description=f"Urgent job {job_id} has arrived (duration={duration}, deadline={deadline}).",
    )


def job_cancellation(job_id):
    """Create a job cancellation disruption event."""
    return _make_disruption(
        JOB_CANCELLATION,
        job_id=job_id,
        description=f"Job {job_id} has been cancelled.",
    )


def deadline_change(job_id, new_deadline):
    """Create a deadline change disruption event."""
    return _make_disruption(
        DEADLINE_CHANGE,
        job_id=job_id,
        new_deadline=new_deadline,
        description=f"Job {job_id} deadline changed to {new_deadline}.",
    )


def machine_downtime(machine_id, duration_minutes=60):
    """Create a planned machine downtime disruption event."""
    return _make_disruption(
        MACHINE_DOWNTIME,
        machine_id=machine_id,
        duration_minutes=duration_minutes,
        description=f"Machine {machine_id} scheduled for {duration_minutes}min maintenance.",
    )


def planned_downtime(machine_id, duration_minutes=90, reason="Preventive service"):
    """Create a planned downtime event."""
    return _make_disruption(
        PLANNED_DOWNTIME,
        machine_id=machine_id,
        duration_minutes=duration_minutes,
        reason=reason,
        description=f"Machine {machine_id} scheduled for {duration_minutes}min planned maintenance ({reason}).",
    )


def maintenance(machine_id, duration_minutes=90, reason="Preventive service"):
    """Create a maintenance event."""
    return _make_disruption(
        MAINTENANCE,
        machine_id=machine_id,
        duration_minutes=duration_minutes,
        reason=reason,
        description=f"Machine {machine_id} undergoing {duration_minutes}min maintenance ({reason}).",
    )


def material_shortage(material_id, description=None):
    """Create a material shortage disruption event."""
    desc = description or f"Critical material {material_id} is temporarily unavailable from supplier."
    return _make_disruption(
        MATERIAL_SHORTAGE,
        material_id=material_id,
        description=desc,
    )


def quality_issue(machine_id, defect_rate=0.15, description=None):
    """Create a quality calibration issue event."""
    desc = description or f"Machine {machine_id} experienced quality calibration drift (defect rate {defect_rate*100:.0f}%)."
    return _make_disruption(
        QUALITY_ISSUE,
        machine_id=machine_id,
        defect_rate=defect_rate,
        description=desc,
    )


def multiple_failure(machine_ids, description=None):
    """Create a cascading multiple machine failure event."""
    m_list = machine_ids if isinstance(machine_ids, list) else [m.strip() for m in str(machine_ids).split(",")]
    desc = description or f"Multiple stations ({', '.join(m_list)}) have suffered concurrent mechanical failure."
    return _make_disruption(
        MULTIPLE_FAILURE,
        machine_ids=m_list,
        description=desc,
    )


def energy_constraint(threshold_kw=65.0, description=None):
    """Create a factory peak energy constraint optimization event."""
    desc = description or f"Factory peak electrical draw restricted to {threshold_kw} kW. Shift to energy-aware schedule."
    return _make_disruption(
        ENERGY_CONSTRAINT,
        threshold_kw=threshold_kw,
        description=desc,
    )

