"""
Central Disruption Engine for FlowForge.

Receives disruption events, updates factory state, identifies affected jobs,
triggers re-optimization, and produces impact summaries with recovery schedules.

This is the core autonomous resilience component:
  Disruption → State Update → Impact Analysis → Re-optimization → Recovery
"""
import time

from agents.factory.machine import fail_machine, recover_machine
from agents.factory.job import (
    get_active_jobs, cancel_job, update_deadline, add_urgent_job
)
from agents.factory.state import (
    FACTORY_DISRUPTED, FACTORY_RECOVERING, FACTORY_RECOVERED
)
from agents.disruption.types import (
    MACHINE_FAILURE, MACHINE_RECOVERY, URGENT_JOB,
    JOB_CANCELLATION, DEADLINE_CHANGE, MACHINE_DOWNTIME,
)
from agents.scheduler import Scheduler


class DisruptionEngine:
    """
    Central disruption processor.

    Applies disruptions to factory state, identifies affected jobs,
    runs recovery optimization, and returns structured impact results.
    """

    def __init__(self, factory_state, ga_weights=None):
        """
        Args:
            factory_state: FactoryState instance
            ga_weights: optional dict of GA fitness weights
        """
        self.factory_state = factory_state
        self.ga_weights = ga_weights or {
            "makespan": 0.30,
            "tardiness": 0.35,
            "downtime": 0.15,
            "energy": 0.20,
        }

    def apply(self, disruption):
        """
        Apply a disruption event to the factory.

        Steps:
          1. Preserve baseline if not already saved.
          2. Update factory state based on disruption type.
          3. Identify affected jobs.
          4. Calculate disruption impact.
          5. Run recovery optimization.
          6. Return structured result.

        Args:
            disruption: dict from agents.disruption.types

        Returns:
            dict with disruption details, impact, and recovery schedule
        """
        start_time = time.time()
        fs = self.factory_state

        # Record the disruption
        fs.add_disruption(disruption)
        fs.factory_status = FACTORY_DISRUPTED
        dtype = disruption["type"]

        # Step 1: Apply state change based on disruption type
        affected_jobs = []
        impact = {}

        if dtype == MACHINE_FAILURE:
            result = self._apply_machine_failure(disruption)
            affected_jobs = result["affected_jobs"]
            impact = result["impact"]

        elif dtype == MACHINE_RECOVERY:
            result = self._apply_machine_recovery(disruption)
            affected_jobs = result["affected_jobs"]
            impact = result["impact"]

        elif dtype == URGENT_JOB:
            result = self._apply_urgent_job(disruption)
            affected_jobs = result["affected_jobs"]
            impact = result["impact"]

        elif dtype == JOB_CANCELLATION:
            result = self._apply_job_cancellation(disruption)
            affected_jobs = result["affected_jobs"]
            impact = result["impact"]

        elif dtype == DEADLINE_CHANGE:
            result = self._apply_deadline_change(disruption)
            affected_jobs = result["affected_jobs"]
            impact = result["impact"]

        elif dtype == MACHINE_DOWNTIME:
            # Treat as machine failure for now
            result = self._apply_machine_failure(disruption)
            affected_jobs = result["affected_jobs"]
            impact = result["impact"]

        else:
            return {"error": f"Unknown disruption type: {dtype}"}

        # Step 2: Calculate disrupted schedule (what happens if we don't act)
        disrupted_schedule = self._calculate_disrupted_schedule()
        fs.set_disrupted_schedule(disrupted_schedule)

        # Step 3: Run recovery optimization
        fs.factory_status = FACTORY_RECOVERING
        recovery_schedule = self._run_recovery_optimization()
        fs.set_recovery_schedule(recovery_schedule)

        recovery_time = time.time() - start_time

        return {
            "disruption": disruption,
            "affected_jobs": affected_jobs,
            "impact": impact,
            "disrupted_schedule": disrupted_schedule,
            "recovery_schedule": recovery_schedule,
            "baseline_schedule": fs.baseline_schedule,
            "recovery_time_seconds": round(recovery_time, 3),
        }

    def _apply_machine_failure(self, disruption):
        """Handle machine failure: mark machine as failed, find affected jobs."""
        machine_id = disruption["machine_id"]
        fs = self.factory_state

        success = fail_machine(fs.machines, machine_id)
        if not success:
            return {
                "affected_jobs": [],
                "impact": {"error": f"Machine {machine_id} not found or already failed."},
            }

        # Find jobs that were assigned to the failed machine in the baseline
        affected = []
        if fs.baseline_schedule:
            affected = [
                a["job_id"] for a in fs.baseline_schedule
                if a.get("machine") == machine_id
            ]

        # Count deadline risks
        deadline_risks = 0
        if fs.baseline_schedule:
            for a in fs.baseline_schedule:
                if a.get("machine") == machine_id:
                    completion = a["start"] + a["duration"]
                    if completion > a["due"] * 0.8:  # within 80% of deadline
                        deadline_risks += 1

        return {
            "affected_jobs": affected,
            "impact": {
                "failed_machine": machine_id,
                "affected_job_count": len(affected),
                "deadline_risks": deadline_risks,
                "description": f"{machine_id} failed. {len(affected)} jobs affected, {deadline_risks} deadline risks.",
            },
        }

    def _apply_machine_recovery(self, disruption):
        """Handle machine recovery: restore machine, re-optimize with added capacity."""
        machine_id = disruption["machine_id"]
        fs = self.factory_state

        success = recover_machine(fs.machines, machine_id)
        if not success:
            return {
                "affected_jobs": [],
                "impact": {"error": f"Machine {machine_id} not found or not failed."},
            }

        return {
            "affected_jobs": [],
            "impact": {
                "recovered_machine": machine_id,
                "description": f"{machine_id} restored. Capacity increased.",
            },
        }

    def _apply_urgent_job(self, disruption):
        """Handle urgent job arrival: add job and re-optimize."""
        fs = self.factory_state
        new_job = add_urgent_job(
            fs.jobs,
            disruption["job_id"],
            disruption["duration"],
            disruption["deadline"],
            disruption.get("priority", 5),
        )
        return {
            "affected_jobs": [new_job["job_id"]],
            "impact": {
                "new_job": new_job["job_id"],
                "duration": new_job["duration"],
                "deadline": new_job["deadline"],
                "priority": new_job["priority"],
                "description": f"Urgent job {new_job['job_id']} arrived (duration={new_job['duration']}, deadline={new_job['deadline']}).",
            },
        }

    def _apply_job_cancellation(self, disruption):
        """Handle job cancellation: remove job and re-optimize."""
        fs = self.factory_state
        job_id = disruption["job_id"]
        cancelled = cancel_job(fs.jobs, job_id)

        if not cancelled:
            return {
                "affected_jobs": [],
                "impact": {"error": f"Job {job_id} not found or already cancelled."},
            }

        return {
            "affected_jobs": [job_id],
            "impact": {
                "cancelled_job": job_id,
                "description": f"Job {job_id} cancelled. Capacity released.",
            },
        }

    def _apply_deadline_change(self, disruption):
        """Handle deadline change: update deadline and re-optimize."""
        fs = self.factory_state
        job_id = disruption["job_id"]
        new_deadline = disruption["new_deadline"]
        result = update_deadline(fs.jobs, job_id, new_deadline)

        if not result:
            return {
                "affected_jobs": [],
                "impact": {"error": f"Job {job_id} not found."},
            }

        return {
            "affected_jobs": [job_id],
            "impact": {
                "job_id": job_id,
                "old_deadline": result["old_deadline"],
                "new_deadline": result["new_deadline"],
                "description": f"Job {job_id} deadline changed: {result['old_deadline']} → {result['new_deadline']}.",
            },
        }

    def _calculate_disrupted_schedule(self):
        """
        Calculate what the schedule looks like if we don't re-optimize.
        This is the baseline schedule with failed machines removed
        but no re-ordering — just drop jobs on failed machines.
        """
        fs = self.factory_state
        if not fs.baseline_schedule:
            return []

        available_ids = fs.get_available_machine_ids()

        # Keep only assignments on available machines
        disrupted = [
            a for a in fs.baseline_schedule
            if a.get("machine") in available_ids
        ]
        return disrupted

    def _run_recovery_optimization(self):
        """
        Run the GA optimizer with updated constraints
        (only available machines, active jobs).
        """
        fs = self.factory_state
        available_ids = fs.get_available_machine_ids()
        active_jobs = fs.get_active_jobs()

        if not available_ids:
            return []
        if not active_jobs:
            return []

        # Create scheduler with only available machines
        scheduler = Scheduler(available_ids)

        # Build machine energy map
        energy_map = fs.get_machine_energy_map()

        # Run GA with multi-objective fitness
        recovery = scheduler.ga_schedule(
            active_jobs,
            machine_energy=energy_map,
            weights=self.ga_weights,
        )

        return recovery
