# agents/scheduler.py
from agents.ga_optimizer import GAOptimizer  # put imports at top-level

class Scheduler:
    def __init__(self, machines):
        self.machines = machines

    def heuristic_schedule(self, jobs, rule='SPT'):
        jobs_sorted = sorted(
            jobs,
            key=lambda j: j['duration'] if rule == 'SPT' else j['due']
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
                'due': job['due']
            })
            machine_available[best_m] = start + job['duration']

        return assignments

    def ga_schedule(self, jobs):
        ga = GAOptimizer(jobs, self.machines)
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
                "due": job["due"]
            })
            machine_available[best_machine] = start + job["duration"]

        return assignments
