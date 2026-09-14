"""
Factory Resilience Score for FlowForge.

Score range: 0-100
Higher = more resilient factory.

Components (all normalized to 0-100):
  - Deadline protection  (0.30) — How well deadlines are being met
  - Utilization          (0.20) — Machine utilization efficiency
  - Recovery performance (0.25) — How well recovery improved over disrupted state
  - Remaining capacity   (0.15) — Available machine capacity
  - Disruption impact    (0.10) — Severity of active disruptions

The formula is intentionally simple and easy to modify later.
"""
from agents.resilience.metrics import (
    calculate_makespan,
    calculate_late_jobs,
    calculate_average_utilization,
    calculate_total_tardiness,
)


# Default component weights
DEFAULT_WEIGHTS = {
    "deadline_protection": 0.30,
    "utilization": 0.20,
    "recovery_performance": 0.25,
    "remaining_capacity": 0.15,
    "disruption_impact": 0.10,
}


def calculate_resilience_score(
    current_schedule,
    machine_ids,
    machine_energy_map,
    total_machines,
    available_machines,
    baseline_schedule=None,
    disrupted_schedule=None,
    weights=None,
):
    """
    Calculate the Factory Resilience Score (0-100).

    Args:
        current_schedule: the active schedule assignments
        machine_ids: list of all machine IDs
        machine_energy_map: {machine_id: kwh_per_hour}
        total_machines: total number of machines in the factory
        available_machines: number of currently available machines
        baseline_schedule: optional baseline schedule for comparison
        disrupted_schedule: optional disrupted schedule for comparison
        weights: optional component weight overrides

    Returns:
        dict with score, components, and label
    """
    w = weights or DEFAULT_WEIGHTS

    if not current_schedule:
        return {"score": 0, "components": {}, "label": "NO SCHEDULE"}

    # --- Component 1: Deadline Protection (0-100) ---
    # 100 = no late jobs, 0 = all jobs late
    total_jobs = len(current_schedule)
    late = calculate_late_jobs(current_schedule)
    deadline_protection = max(0, (1 - late / max(1, total_jobs)) * 100)

    # --- Component 2: Machine Utilization (0-100) ---
    utilization = calculate_average_utilization(current_schedule, machine_ids)

    # --- Component 3: Recovery Performance (0-100) ---
    # How much the recovery improved over the disrupted state
    recovery_performance = 50  # neutral default if no comparison available
    if disrupted_schedule and current_schedule and disrupted_schedule != current_schedule:
        disrupted_tardiness = calculate_total_tardiness(disrupted_schedule)
        current_tardiness = calculate_total_tardiness(current_schedule)
        disrupted_makespan = calculate_makespan(disrupted_schedule)
        current_makespan = calculate_makespan(current_schedule)

        # Improvement ratio based on tardiness reduction
        if disrupted_tardiness > 0:
            tard_improvement = max(0, 1 - current_tardiness / disrupted_tardiness)
        else:
            tard_improvement = 1.0 if current_tardiness == 0 else 0.0

        # Improvement ratio based on makespan
        if disrupted_makespan > 0:
            make_improvement = max(0, 1 - (current_makespan / max(1, disrupted_makespan)))
        else:
            make_improvement = 0.0

        recovery_performance = min(100, (tard_improvement * 70 + make_improvement * 30 + 30))

    # --- Component 4: Remaining Capacity (0-100) ---
    if total_machines > 0:
        remaining_capacity = (available_machines / total_machines) * 100
    else:
        remaining_capacity = 0

    # --- Component 5: Disruption Impact (0-100) ---
    # 100 = no disruption impact, lower = more severe
    # Based on how much tardiness exists relative to total schedule time
    total_tardiness = calculate_total_tardiness(current_schedule)
    makespan = calculate_makespan(current_schedule)
    if makespan > 0 and total_jobs > 0:
        tardiness_ratio = total_tardiness / (makespan * total_jobs)
        disruption_impact = max(0, (1 - min(1, tardiness_ratio * 5)) * 100)
    else:
        disruption_impact = 100

    # --- Weighted Score ---
    components = {
        "deadline_protection": round(deadline_protection, 1),
        "utilization": round(utilization, 1),
        "recovery_performance": round(recovery_performance, 1),
        "remaining_capacity": round(remaining_capacity, 1),
        "disruption_impact": round(disruption_impact, 1),
    }

    score = (
        w["deadline_protection"] * deadline_protection
        + w["utilization"] * utilization
        + w["recovery_performance"] * recovery_performance
        + w["remaining_capacity"] * remaining_capacity
        + w["disruption_impact"] * disruption_impact
    )
    score = round(min(100, max(0, score)), 0)

    # Label
    if score >= 80:
        label = "HEALTHY"
    elif score >= 60:
        label = "STABLE"
    elif score >= 40:
        label = "AT RISK"
    elif score >= 20:
        label = "CRITICAL"
    else:
        label = "SEVERE"

    return {
        "score": int(score),
        "components": components,
        "label": label,
    }
