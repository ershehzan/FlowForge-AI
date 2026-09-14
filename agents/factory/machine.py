"""
Machine model for FlowForge factory simulation.

Each machine has an ID, operational status, energy consumption rate,
and processing capacity. These are simulation parameters, not real
industrial measurements.
"""
from copy import deepcopy


# Default machine configurations for the simulated factory.
# Energy rates are simulation parameters (kWh/hour).
DEFAULT_MACHINES = {
    "M1": {"id": "M1", "status": "available", "energy_kwh_per_hour": 8.0,  "capacity": 1},
    "M2": {"id": "M2", "status": "available", "energy_kwh_per_hour": 10.5, "capacity": 1},
    "M3": {"id": "M3", "status": "available", "energy_kwh_per_hour": 12.0, "capacity": 1},
    "M4": {"id": "M4", "status": "available", "energy_kwh_per_hour": 7.5,  "capacity": 1},
    "M5": {"id": "M5", "status": "available", "energy_kwh_per_hour": 7.0,  "capacity": 1},
    "M6": {"id": "M6", "status": "available", "energy_kwh_per_hour": 9.0,  "capacity": 1},
}

# Valid machine statuses
MACHINE_STATUS_AVAILABLE = "available"
MACHINE_STATUS_FAILED = "failed"
MACHINE_STATUS_MAINTENANCE = "maintenance"


def create_machine(machine_id, energy_kwh_per_hour=8.0, capacity=1):
    """Create a new machine dict with default available status."""
    return {
        "id": machine_id,
        "status": MACHINE_STATUS_AVAILABLE,
        "energy_kwh_per_hour": energy_kwh_per_hour,
        "capacity": capacity,
    }


def get_default_machines():
    """Return a deep copy of the default 6-machine factory configuration."""
    return deepcopy(DEFAULT_MACHINES)


def get_available_machine_ids(machines):
    """Return list of machine IDs that are currently available."""
    return [
        m_id for m_id, m_data in machines.items()
        if m_data["status"] == MACHINE_STATUS_AVAILABLE
    ]


def get_machine_energy_map(machines):
    """Return {machine_id: energy_kwh_per_hour} for all machines."""
    return {
        m_id: m_data["energy_kwh_per_hour"]
        for m_id, m_data in machines.items()
    }


def fail_machine(machines, machine_id):
    """
    Set a machine to failed status.
    Returns True if the machine was available and is now failed.
    Returns False if the machine was already failed or doesn't exist.
    """
    if machine_id not in machines:
        return False
    if machines[machine_id]["status"] == MACHINE_STATUS_FAILED:
        return False
    machines[machine_id]["status"] = MACHINE_STATUS_FAILED
    return True


def recover_machine(machines, machine_id):
    """
    Restore a failed machine to available status.
    Returns True if the machine was failed and is now available.
    Returns False if the machine was not failed or doesn't exist.
    """
    if machine_id not in machines:
        return False
    if machines[machine_id]["status"] != MACHINE_STATUS_FAILED:
        return False
    machines[machine_id]["status"] = MACHINE_STATUS_AVAILABLE
    return True
