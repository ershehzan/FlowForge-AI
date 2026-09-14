"""
Comprehensive metrics calculator for FlowForge.

All metrics are calculated from actual schedule assignments,
not hard-coded demo numbers.
"""


def calculate_makespan(assignments):
    """Total time until the last scheduled job completes."""
    if not assignments:
        return 0
    return max(a["start"] + a["duration"] for a in assignments)


def calculate_total_tardiness(assignments):
    """
    Sum of tardiness across all jobs.
    tardiness = max(0, completion_time - deadline)
    """
    total = 0
    for a in assignments:
        completion = a["start"] + a["duration"]
        due = a.get("due", a.get("deadline", 999))
        total += max(0, completion - due)
    return total


def calculate_average_tardiness(assignments):
    """Average tardiness per job."""
    if not assignments:
        return 0
    return calculate_total_tardiness(assignments) / len(assignments)


def calculate_late_jobs(assignments):
    """Count of jobs completing after their deadline."""
    count = 0
    for a in assignments:
        completion = a["start"] + a["duration"]
        due = a.get("due", a.get("deadline", 999))
        if completion > due:
            count += 1
    return count


def calculate_machine_utilization(assignments, machine_ids):
    """
    Machine utilization as a percentage.
    utilization = busy_time / available_time
    available_time = makespan for each machine
    """
    if not assignments or not machine_ids:
        return {}

    makespan = calculate_makespan(assignments)
    if makespan == 0:
        return {m: 0.0 for m in machine_ids}

    busy = {m: 0 for m in machine_ids}
    for a in assignments:
        m = a.get("machine")
        if m in busy:
            busy[m] += a["duration"]

    utilization = {}
    for m in machine_ids:
        utilization[m] = round((busy[m] / makespan) * 100, 1) if makespan > 0 else 0.0

    return utilization


def calculate_average_utilization(assignments, machine_ids):
    """Average machine utilization percentage across all machines."""
    util = calculate_machine_utilization(assignments, machine_ids)
    if not util:
        return 0.0
    return round(sum(util.values()) / len(util), 1)


def calculate_energy_consumption(assignments, machine_energy_map):
    """
    Total energy consumption in kWh.
    energy = Σ(machine_operating_hours × machine_kwh_per_hour)

    Args:
        assignments: schedule assignment list
        machine_energy_map: {machine_id: kwh_per_hour}
    """
    if not assignments:
        return 0.0

    # Sum busy time per machine (in minutes)
    machine_busy_minutes = {}
    for a in assignments:
        m = a.get("machine")
        if m not in machine_busy_minutes:
            machine_busy_minutes[m] = 0
        machine_busy_minutes[m] += a["duration"]

    # Convert to energy
    total_kwh = 0.0
    for m_id, minutes in machine_busy_minutes.items():
        hours = minutes / 60.0
        kwh_rate = machine_energy_map.get(m_id, 8.0)
        total_kwh += hours * kwh_rate

    return round(total_kwh, 1)


def calculate_all_metrics(assignments, machine_ids, machine_energy_map):
    """
    Calculate all metrics from a schedule.

    Returns a dict with all key metrics.
    """
    makespan = calculate_makespan(assignments)
    total_tardiness = calculate_total_tardiness(assignments)
    avg_tardiness = calculate_average_tardiness(assignments)
    late_jobs = calculate_late_jobs(assignments)
    utilization = calculate_machine_utilization(assignments, machine_ids)
    avg_utilization = calculate_average_utilization(assignments, machine_ids)
    energy = calculate_energy_consumption(assignments, machine_energy_map)

    return {
        "makespan": makespan,
        "total_tardiness": total_tardiness,
        "average_tardiness": round(avg_tardiness, 1),
        "late_jobs": late_jobs,
        "machine_utilization": utilization,
        "average_utilization": avg_utilization,
        "energy_kwh": energy,
        "total_jobs": len(assignments),
    }
