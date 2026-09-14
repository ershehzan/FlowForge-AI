# agents/scheduler.py
from agents.ga_optimizer import GAOptimizer


class Scheduler:
    def __init__(self, machines):
        self.machines = machines

    def schedule_operations(self, jobs, machine_unavail=None):
        """
        Operation-aware job shop scheduling respecting machine bindings,
        operation precedence within each job, and machine unavailable periods.
        """
        machine_unavail = machine_unavail or {}
        machine_available = {m: 0 for m in self.machines}
        job_completion = {j["job_id"]: 0 for j in jobs}
        assignments = []

        # Sort jobs by priority (descending) and deadline (ascending)
        sorted_jobs = sorted(
            jobs,
            key=lambda j: (-j.get("priority", 2), j.get("deadline", j.get("due", 999)))
        )

        for job in sorted_jobs:
            ops = job.get("operations", [])
            j_id = job["job_id"]
            due = job.get("deadline", job.get("due", 999))

            if ops:
                for op_idx, op in enumerate(ops):
                    m = op["machine"]
                    dur = op["duration"]
                    if m not in machine_available:
                        machine_available[m] = 0

                    earliest = max(machine_available[m], job_completion[j_id])

                    # Check unavailable periods for machine m
                    unavail_list = machine_unavail.get(m, [])
                    start = earliest
                    for period in sorted(unavail_list, key=lambda p: p[0] if isinstance(p, (list, tuple)) else 0):
                        if isinstance(period, (list, tuple)) and len(period) >= 2:
                            u_start, u_end = period[0], period[1]
                            if start < u_end and (start + dur) > u_start:
                                start = max(start, u_end)

                    assignments.append({
                        "job_id": f"{j_id}" if len(ops) == 1 else f"{j_id}-O{op_idx+1}",
                        "name": f"Op {op_idx+1} ({dur}m)" if len(ops) > 1 else f"{j_id}",
                        "machine": m,
                        "start": start,
                        "duration": dur,
                        "due": due,
                        "deadline": due,
                        "parent_job": j_id,
                    })
                    machine_available[m] = start + dur
                    job_completion[j_id] = start + dur
            else:
                best_machine = min(machine_available, key=lambda x: machine_available[x])
                dur = job.get("duration", 30)
                start = max(machine_available[best_machine], job_completion[j_id])

                # Check unavailable periods
                for period in machine_unavail.get(best_machine, []):
                    if isinstance(period, (list, tuple)) and len(period) >= 2:
                        if start < period[1] and (start + dur) > period[0]:
                            start = max(start, period[1])

                assignments.append({
                    "job_id": j_id,
                    "name": f"{j_id}",
                    "machine": best_machine,
                    "start": start,
                    "duration": dur,
                    "due": due,
                    "deadline": due,
                })
                machine_available[best_machine] = start + dur
                job_completion[j_id] = start + dur

        return assignments

    def heuristic_schedule(self, jobs, rule='SPT', machine_unavail=None):
        if any(j.get("operations") for j in jobs):
            return self.schedule_operations(jobs, machine_unavail=machine_unavail)

        jobs_sorted = sorted(
            jobs,
            key=lambda j: j['duration'] if rule == 'SPT' else j.get('due', j.get('deadline', 999))
        )

        assignments = []
        machine_available = {m: 0 for m in self.machines}

        for job in jobs_sorted:
            best_m = min(machine_available, key=lambda x: machine_available[x])
            start = machine_available[best_m]
            assignments.append({
                'job_id': job['job_id'],
                'machine': best_m,
                'start': start,
                'duration': job['duration'],
                'due': job.get('due', job.get('deadline', 999))
            })
            machine_available[best_m] = start + job['duration']

        return assignments

    def ga_schedule(self, jobs, machine_energy=None, weights=None, machine_unavail=None):
        """
        Run the GA optimizer (or operation-aware scheduler if multi-op) and return schedule assignments.

        Args:
            jobs: list of job dicts
            machine_energy: optional {machine_id: kwh_per_hour}
            weights: optional fitness weight dict
            machine_unavail: optional {machine_id: [[start, end], ...]}
        """
        if any(j.get("operations") for j in jobs) or machine_unavail:
            return self.schedule_operations(jobs, machine_unavail=machine_unavail)

        ga = GAOptimizer(
            jobs, self.machines,
            machine_energy=machine_energy,
            weights=weights,
        )
        best = ga.optimize()

        # convert into assignment format
        assignments = []
        machine_available = {m: 0 for m in self.machines}

        for job in best["chrom"]:
            best_machine = min(machine_available, key=lambda x: machine_available[x])
            start = machine_available[best_machine]
            assignments.append({
                "job_id": job["job_id"],
                "machine": best_machine,
                "start": start,
                "duration": job["duration"],
                "due": job.get("due", job.get("deadline", 999))
            })
            machine_available[best_machine] = start + job["duration"]

        return assignments
