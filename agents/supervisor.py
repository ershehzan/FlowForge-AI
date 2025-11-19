class SupervisorAgent:
    def check_and_reschedule(self, machine_status, jobs, scheduler):
        """
        machine_status: {"M1": "OK", "M2": "FAIL", "M3": "OK"}
        jobs: job list
        scheduler: Scheduler instance
        """
        if "FAIL" in machine_status.values():
            # If any machine fails → reschedule using SPT
            return scheduler.heuristic_schedule(jobs, "SPT")
        return None
