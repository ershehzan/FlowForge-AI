"""
FlowForge Phase 1 — Foundation Test Suite

Tests the core foundation: factory state, machine availability, job scheduling,
multi-objective fitness, schedule generation, machine failure disruption,
metrics calculation, and resilience scoring.
"""
import pytest
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.factory.machine import (
    get_default_machines, get_available_machine_ids,
    get_machine_energy_map, fail_machine, recover_machine,
    MACHINE_STATUS_AVAILABLE, MACHINE_STATUS_FAILED,
)
from agents.factory.job import (
    get_default_jobs, get_active_jobs, cancel_job,
    update_deadline, add_urgent_job,
)
from agents.factory.state import (
    FactoryState, STATE_BASELINE, STATE_DISRUPTED, STATE_RECOVERY,
    FACTORY_OPERATIONAL, FACTORY_DISRUPTED, FACTORY_RECOVERED,
)
from agents.scheduler import Scheduler
from agents.ga_optimizer import GAOptimizer
from agents.disruption.types import (
    machine_failure, machine_recovery, urgent_job,
    job_cancellation, deadline_change,
)
from agents.disruption.engine import DisruptionEngine
from agents.resilience.metrics import (
    calculate_makespan, calculate_total_tardiness, calculate_late_jobs,
    calculate_machine_utilization, calculate_energy_consumption,
    calculate_all_metrics,
)
from agents.resilience.score import calculate_resilience_score
from evaluation.evaluator import Evaluator


# ───────────────────────────────────────────────────────────
# Machine Model Tests
# ───────────────────────────────────────────────────────────

class TestMachineModel:
    def test_default_machines_count(self):
        machines = get_default_machines()
        assert len(machines) == 6

    def test_default_machines_all_available(self):
        machines = get_default_machines()
        for m_id, m_data in machines.items():
            assert m_data["status"] == MACHINE_STATUS_AVAILABLE

    def test_default_machines_have_energy(self):
        machines = get_default_machines()
        for m_id, m_data in machines.items():
            assert "energy_kwh_per_hour" in m_data
            assert m_data["energy_kwh_per_hour"] > 0

    def test_get_available_machine_ids(self):
        machines = get_default_machines()
        available = get_available_machine_ids(machines)
        assert len(available) == 6
        assert "M1" in available

    def test_fail_machine(self):
        machines = get_default_machines()
        result = fail_machine(machines, "M3")
        assert result is True
        assert machines["M3"]["status"] == MACHINE_STATUS_FAILED
        available = get_available_machine_ids(machines)
        assert "M3" not in available
        assert len(available) == 5

    def test_fail_already_failed_machine(self):
        machines = get_default_machines()
        fail_machine(machines, "M3")
        result = fail_machine(machines, "M3")
        assert result is False

    def test_fail_nonexistent_machine(self):
        machines = get_default_machines()
        result = fail_machine(machines, "M99")
        assert result is False

    def test_recover_machine(self):
        machines = get_default_machines()
        fail_machine(machines, "M3")
        result = recover_machine(machines, "M3")
        assert result is True
        assert machines["M3"]["status"] == MACHINE_STATUS_AVAILABLE

    def test_recover_not_failed_machine(self):
        machines = get_default_machines()
        result = recover_machine(machines, "M3")
        assert result is False

    def test_get_machine_energy_map(self):
        machines = get_default_machines()
        energy = get_machine_energy_map(machines)
        assert energy["M1"] == 8.0
        assert energy["M3"] == 12.0
        assert energy["M5"] == 7.0


# ───────────────────────────────────────────────────────────
# Job Model Tests
# ───────────────────────────────────────────────────────────

class TestJobModel:
    def test_default_jobs_count(self):
        jobs = get_default_jobs()
        assert len(jobs) == 12

    def test_default_jobs_have_required_fields(self):
        jobs = get_default_jobs()
        for job in jobs:
            assert "job_id" in job
            assert "duration" in job
            assert "deadline" in job
            assert "priority" in job

    def test_cancel_job(self):
        jobs = get_default_jobs()
        result = cancel_job(jobs, "J5")
        assert result is not None
        assert result["status"] == "cancelled"
        active = get_active_jobs(jobs)
        assert len(active) == 11

    def test_cancel_nonexistent_job(self):
        jobs = get_default_jobs()
        result = cancel_job(jobs, "J99")
        assert result is None

    def test_cancel_already_cancelled_job(self):
        jobs = get_default_jobs()
        cancel_job(jobs, "J5")
        result = cancel_job(jobs, "J5")
        assert result is None

    def test_update_deadline(self):
        jobs = get_default_jobs()
        result = update_deadline(jobs, "J7", 100)
        assert result is not None
        assert result["new_deadline"] == 100
        assert result["old_deadline"] == 220

    def test_add_urgent_job(self):
        jobs = get_default_jobs()
        result = add_urgent_job(jobs, "J13", 35, 130, priority=5)
        assert result["job_id"] == "J13"
        assert len(jobs) == 13


# ───────────────────────────────────────────────────────────
# Factory State Tests
# ───────────────────────────────────────────────────────────

class TestFactoryState:
    def test_initialization(self):
        fs = FactoryState()
        assert len(fs.machines) == 6
        assert len(fs.jobs) == 12
        assert fs.factory_status == FACTORY_OPERATIONAL
        assert fs.schedule_state == STATE_BASELINE

    def test_set_baseline_schedule(self):
        fs = FactoryState()
        schedule = [{"job_id": "J1", "machine": "M1", "start": 0, "duration": 45, "due": 200}]
        fs.set_baseline_schedule(schedule)
        assert fs.baseline_schedule is not None
        assert fs.schedule_state == STATE_BASELINE

    def test_baseline_preserved_after_disruption(self):
        fs = FactoryState()
        schedule = [{"job_id": "J1", "machine": "M1", "start": 0, "duration": 45, "due": 200}]
        fs.set_baseline_schedule(schedule)
        original_baseline = fs.baseline_schedule.copy()

        # Simulate disruption
        fs.set_disrupted_schedule([])
        assert fs.baseline_schedule == original_baseline  # baseline preserved

    def test_schedule_state_transitions(self):
        fs = FactoryState()
        schedule = [{"job_id": "J1", "machine": "M1", "start": 0, "duration": 45, "due": 200}]

        fs.set_baseline_schedule(schedule)
        assert fs.schedule_state == STATE_BASELINE

        fs.set_disrupted_schedule([])
        assert fs.schedule_state == STATE_DISRUPTED
        assert fs.factory_status == FACTORY_DISRUPTED

        fs.set_recovery_schedule(schedule)
        assert fs.schedule_state == STATE_RECOVERY
        assert fs.factory_status == FACTORY_RECOVERED

    def test_reset(self):
        fs = FactoryState()
        fs.set_baseline_schedule([{"job_id": "J1", "machine": "M1", "start": 0, "duration": 45, "due": 200}])
        fail_machine(fs.machines, "M3")
        fs.add_disruption({"type": "test"})

        fs.reset()
        assert fs.factory_status == FACTORY_OPERATIONAL
        assert len(fs.get_available_machine_ids()) == 6
        assert fs.baseline_schedule is None
        assert len(fs.active_disruptions) == 0

    def test_get_machine_count(self):
        fs = FactoryState()
        avail, total = fs.get_machine_count()
        assert total == 6
        assert avail == 6

        fail_machine(fs.machines, "M3")
        avail, total = fs.get_machine_count()
        assert total == 6
        assert avail == 5


# ───────────────────────────────────────────────────────────
# Scheduler Tests
# ───────────────────────────────────────────────────────────

class TestScheduler:
    def setup_method(self):
        self.jobs = get_default_jobs()
        self.machines = ["M1", "M2", "M3", "M4", "M5", "M6"]

    def test_heuristic_schedule_spt(self):
        scheduler = Scheduler(self.machines)
        result = scheduler.heuristic_schedule(self.jobs, "SPT")
        assert len(result) == 12
        for a in result:
            assert a["machine"] in self.machines
            assert "start" in a
            assert "duration" in a

    def test_heuristic_schedule_edd(self):
        scheduler = Scheduler(self.machines)
        result = scheduler.heuristic_schedule(self.jobs, "EDD")
        assert len(result) == 12

    def test_ga_schedule(self):
        scheduler = Scheduler(self.machines)
        result = scheduler.ga_schedule(self.jobs)
        assert len(result) == 12
        for a in result:
            assert a["machine"] in self.machines

    def test_ga_schedule_with_energy(self):
        scheduler = Scheduler(self.machines)
        energy = {"M1": 8.0, "M2": 10.5, "M3": 12.0, "M4": 7.5, "M5": 7.0, "M6": 9.0}
        result = scheduler.ga_schedule(self.jobs, machine_energy=energy)
        assert len(result) == 12

    def test_schedule_with_fewer_machines(self):
        """Test that scheduling works with reduced machine count (failed machines excluded)."""
        scheduler = Scheduler(["M1", "M2", "M4", "M5", "M6"])  # M3 removed
        result = scheduler.ga_schedule(self.jobs)
        assert len(result) == 12
        for a in result:
            assert a["machine"] != "M3"  # M3 should never appear


# ───────────────────────────────────────────────────────────
# GA Optimizer Tests
# ───────────────────────────────────────────────────────────

class TestGAOptimizer:
    def setup_method(self):
        self.jobs = get_default_jobs()
        self.machines = ["M1", "M2", "M3", "M4", "M5", "M6"]

    def test_random_chromosome(self):
        ga = GAOptimizer(self.jobs, self.machines)
        chrom = ga.random_chromosome()
        assert len(chrom) == 12

    def test_evaluate_returns_number(self):
        ga = GAOptimizer(self.jobs, self.machines)
        chrom = ga.random_chromosome()
        fitness = ga.evaluate(chrom)
        assert isinstance(fitness, (int, float))
        assert fitness >= 0

    def test_multi_objective_weights(self):
        ga = GAOptimizer(
            self.jobs, self.machines,
            machine_energy={"M1": 8.0, "M2": 10.5, "M3": 12.0, "M4": 7.5, "M5": 7.0, "M6": 9.0},
            weights={"makespan": 0.30, "tardiness": 0.35, "downtime": 0.15, "energy": 0.20},
        )
        chrom = ga.random_chromosome()
        fitness = ga.evaluate(chrom)
        assert fitness >= 0

    def test_optimize_returns_best(self):
        ga = GAOptimizer(self.jobs, self.machines, population_size=10, generations=5)
        best = ga.optimize()
        assert "chrom" in best
        assert "fitness" in best
        assert len(best["chrom"]) == 12


# ───────────────────────────────────────────────────────────
# Metrics Tests
# ───────────────────────────────────────────────────────────

class TestMetrics:
    def setup_method(self):
        # Create a known schedule for deterministic testing
        self.schedule = [
            {"job_id": "J1", "machine": "M1", "start": 0, "duration": 45, "due": 200},
            {"job_id": "J2", "machine": "M2", "start": 0, "duration": 30, "due": 120},
            {"job_id": "J3", "machine": "M3", "start": 0, "duration": 60, "due": 250},
            {"job_id": "J4", "machine": "M1", "start": 45, "duration": 35, "due": 50},  # late! completes at 80 > 50
            {"job_id": "J5", "machine": "M2", "start": 30, "duration": 50, "due": 180},
        ]
        self.machines = ["M1", "M2", "M3"]
        self.energy_map = {"M1": 8.0, "M2": 10.5, "M3": 12.0}

    def test_makespan(self):
        ms = calculate_makespan(self.schedule)
        assert ms == 80  # max(45+35, 30+50, 60) = max(80, 80, 60) = 80

    def test_total_tardiness(self):
        tard = calculate_total_tardiness(self.schedule)
        # J4 completes at 80, due 50 → tardiness 30
        # All others complete before deadline
        assert tard == 30

    def test_late_jobs(self):
        late = calculate_late_jobs(self.schedule)
        assert late == 1  # only J4

    def test_utilization(self):
        util = calculate_machine_utilization(self.schedule, self.machines)
        # M1: busy 80/80 = 100%, M2: busy 80/80 = 100%, M3: busy 60/80 = 75%
        assert util["M1"] == 100.0
        assert util["M2"] == 100.0
        assert util["M3"] == 75.0

    def test_energy_consumption(self):
        energy = calculate_energy_consumption(self.schedule, self.energy_map)
        # M1: 80min = 1.333h * 8.0 = 10.667 kWh
        # M2: 80min = 1.333h * 10.5 = 14.0 kWh
        # M3: 60min = 1.0h * 12.0 = 12.0 kWh
        # Total ≈ 36.7 kWh
        assert energy > 0
        assert 36 < energy < 38

    def test_all_metrics(self):
        metrics = calculate_all_metrics(self.schedule, self.machines, self.energy_map)
        assert "makespan" in metrics
        assert "late_jobs" in metrics
        assert "energy_kwh" in metrics
        assert "average_utilization" in metrics
        assert metrics["total_jobs"] == 5

    def test_empty_schedule(self):
        assert calculate_makespan([]) == 0
        assert calculate_total_tardiness([]) == 0
        assert calculate_late_jobs([]) == 0


# ───────────────────────────────────────────────────────────
# Evaluator Backwards Compatibility Tests
# ───────────────────────────────────────────────────────────

class TestEvaluator:
    def test_makespan(self):
        assignments = [
            {"job_id": "J1", "machine": "M1", "start": 0, "duration": 4, "due": 10},
            {"job_id": "J2", "machine": "M2", "start": 0, "duration": 3, "due": 8},
        ]
        assert Evaluator.makespan(assignments) == 4

    def test_average_tardiness(self):
        assignments = [
            {"job_id": "J1", "machine": "M1", "start": 0, "duration": 4, "due": 10},
        ]
        assert Evaluator.average_tardiness(assignments) == 0

    def test_machine_idle_time(self):
        assignments = [
            {"job_id": "J1", "machine": "M1", "start": 0, "duration": 4, "due": 10},
            {"job_id": "J2", "machine": "M1", "start": 6, "duration": 3, "due": 10},
        ]
        idle = Evaluator.machine_idle_time(assignments, ["M1"])
        assert idle["M1"] == 2  # gap from 4 to 6

    def test_late_jobs(self):
        assignments = [
            {"job_id": "J1", "machine": "M1", "start": 0, "duration": 4, "due": 3},  # late
            {"job_id": "J2", "machine": "M2", "start": 0, "duration": 3, "due": 8},
        ]
        assert Evaluator.late_jobs(assignments) == 1

    def test_energy_consumption(self):
        assignments = [
            {"job_id": "J1", "machine": "M1", "start": 0, "duration": 60, "due": 100},
        ]
        energy = Evaluator.energy_consumption(assignments, {"M1": 10.0})
        assert energy == 10.0  # 1 hour * 10 kWh

    def test_machine_utilization(self):
        assignments = [
            {"job_id": "J1", "machine": "M1", "start": 0, "duration": 50, "due": 100},
            {"job_id": "J2", "machine": "M2", "start": 0, "duration": 25, "due": 100},
        ]
        util = Evaluator.machine_utilization(assignments, ["M1", "M2"])
        assert util["M1"] == 100.0  # 50/50
        assert util["M2"] == 50.0   # 25/50


# ───────────────────────────────────────────────────────────
# Resilience Score Tests
# ───────────────────────────────────────────────────────────

class TestResilienceScore:
    def test_healthy_factory_high_score(self):
        schedule = [
            {"job_id": "J1", "machine": "M1", "start": 0, "duration": 45, "due": 200},
            {"job_id": "J2", "machine": "M2", "start": 0, "duration": 30, "due": 120},
        ]
        machines = ["M1", "M2", "M3"]
        energy = {"M1": 8.0, "M2": 10.5, "M3": 12.0}

        result = calculate_resilience_score(
            schedule, machines, energy,
            total_machines=3, available_machines=3,
        )
        assert result["score"] >= 60
        assert result["label"] in ["HEALTHY", "STABLE"]

    def test_score_range(self):
        schedule = [
            {"job_id": "J1", "machine": "M1", "start": 0, "duration": 45, "due": 200},
        ]
        result = calculate_resilience_score(
            schedule, ["M1"], {"M1": 8.0},
            total_machines=6, available_machines=1,
        )
        assert 0 <= result["score"] <= 100

    def test_empty_schedule(self):
        result = calculate_resilience_score(
            [], ["M1"], {"M1": 8.0},
            total_machines=6, available_machines=6,
        )
        assert result["score"] == 0


# ───────────────────────────────────────────────────────────
# Disruption Types Tests
# ───────────────────────────────────────────────────────────

class TestDisruptionTypes:
    def test_machine_failure_event(self):
        event = machine_failure("M3")
        assert event["type"] == "machine_failure"
        assert event["machine_id"] == "M3"
        assert "timestamp" in event

    def test_machine_recovery_event(self):
        event = machine_recovery("M3")
        assert event["type"] == "machine_recovery"

    def test_urgent_job_event(self):
        event = urgent_job("J13", 35, 130)
        assert event["type"] == "urgent_job"
        assert event["job_id"] == "J13"
        assert event["duration"] == 35

    def test_job_cancellation_event(self):
        event = job_cancellation("J5")
        assert event["type"] == "job_cancellation"
        assert event["job_id"] == "J5"

    def test_deadline_change_event(self):
        event = deadline_change("J7", 100)
        assert event["type"] == "deadline_change"
        assert event["new_deadline"] == 100


# ───────────────────────────────────────────────────────────
# Disruption Engine Tests
# ───────────────────────────────────────────────────────────

class TestDisruptionEngine:
    def setup_method(self):
        self.fs = FactoryState()
        # Generate baseline
        scheduler = Scheduler(self.fs.get_available_machine_ids())
        baseline = scheduler.ga_schedule(self.fs.get_active_jobs())
        self.fs.set_baseline_schedule(baseline)

    def test_machine_failure_disruption(self):
        engine = DisruptionEngine(self.fs)
        event = machine_failure("M3")
        result = engine.apply(event)

        assert "error" not in result
        assert result["recovery_schedule"] is not None
        assert len(result["recovery_schedule"]) > 0
        assert self.fs.factory_status == FACTORY_RECOVERED

        # M3 should not appear in recovery schedule
        for a in result["recovery_schedule"]:
            assert a["machine"] != "M3"

    def test_machine_failure_preserves_baseline(self):
        engine = DisruptionEngine(self.fs)
        baseline_copy = self.fs.baseline_schedule.copy()
        event = machine_failure("M3")
        engine.apply(event)

        # Baseline should be unchanged
        assert self.fs.baseline_schedule == baseline_copy

    def test_job_cancellation_disruption(self):
        engine = DisruptionEngine(self.fs)
        event = job_cancellation("J5")
        result = engine.apply(event)

        assert "error" not in result
        assert "J5" in result["affected_jobs"]
        # Recovery schedule should have 11 jobs
        assert len(result["recovery_schedule"]) == 11

    def test_urgent_job_disruption(self):
        engine = DisruptionEngine(self.fs)
        event = urgent_job("J13", 35, 130)
        result = engine.apply(event)

        assert "error" not in result
        # Recovery schedule should have 13 jobs
        assert len(result["recovery_schedule"]) == 13

    def test_deadline_change_disruption(self):
        engine = DisruptionEngine(self.fs)
        event = deadline_change("J7", 80)
        result = engine.apply(event)

        assert "error" not in result
        assert result["recovery_schedule"] is not None

    def test_unknown_disruption_type(self):
        engine = DisruptionEngine(self.fs)
        result = engine.apply({"type": "unknown", "timestamp": 0})
        assert "error" in result


# ───────────────────────────────────────────────────────────
# Integration Test — Full Disruption → Recovery Flow
# ───────────────────────────────────────────────────────────

class TestIntegration:
    def test_full_disruption_recovery_flow(self):
        """
        End-to-end test: initialize factory → trigger M3 failure →
        verify recovery schedule → verify metrics → verify resilience score.
        """
        # 1. Initialize factory
        fs = FactoryState()
        available = fs.get_available_machine_ids()
        scheduler = Scheduler(available)
        energy_map = fs.get_machine_energy_map()

        baseline = scheduler.ga_schedule(
            fs.get_active_jobs(), machine_energy=energy_map,
        )
        fs.set_baseline_schedule(baseline)

        # 2. Verify baseline
        assert len(baseline) == 12
        assert fs.schedule_state == STATE_BASELINE

        baseline_metrics = calculate_all_metrics(baseline, available, energy_map)
        assert baseline_metrics["makespan"] > 0
        assert baseline_metrics["energy_kwh"] > 0

        # 3. Trigger M3 failure
        engine = DisruptionEngine(fs)
        event = machine_failure("M3")
        result = engine.apply(event)

        # 4. Verify recovery
        assert fs.schedule_state == STATE_RECOVERY
        assert len(result["recovery_schedule"]) == 12
        for a in result["recovery_schedule"]:
            assert a["machine"] != "M3"

        # 5. Verify metrics are calculated from actual schedules
        recovery_metrics = calculate_all_metrics(
            result["recovery_schedule"],
            fs.get_available_machine_ids(),
            energy_map,
        )
        assert recovery_metrics["makespan"] > 0
        assert recovery_metrics["energy_kwh"] > 0
        assert recovery_metrics["total_jobs"] == 12

        # 6. Verify resilience score
        avail_count, total_count = fs.get_machine_count()
        resilience = calculate_resilience_score(
            result["recovery_schedule"],
            fs.get_available_machine_ids(),
            energy_map,
            total_machines=total_count,
            available_machines=avail_count,
            baseline_schedule=fs.baseline_schedule,
            disrupted_schedule=fs.disrupted_schedule,
        )
        assert 0 <= resilience["score"] <= 100
        assert resilience["label"] in ["HEALTHY", "STABLE", "AT RISK", "CRITICAL", "SEVERE"]

    def test_legacy_scheduler_still_works(self):
        """Verify the original scheduler API still works with old job format."""
        old_jobs = [
            {"job_id": "J1", "duration": 4, "due": 10},
            {"job_id": "J2", "duration": 3, "due": 8},
            {"job_id": "J3", "duration": 2, "due": 7},
        ]
        scheduler = Scheduler(["M1", "M2", "M3"])
        spt = scheduler.heuristic_schedule(old_jobs, "SPT")
        assert len(spt) == 3

        ga = scheduler.ga_schedule(old_jobs)
        assert len(ga) == 3
