class Evaluator:
    @staticmethod
    def average_tardiness(assignments):
        total = 0
        count = 0
        for t in assignments:
            tard = max(0, t['start'] + t['duration'] - t.get('due', t.get('deadline', 999)))
            total += tard
            count += 1
        return total / count if count > 0 else 0

    @staticmethod
    def makespan(assignments):
        if not assignments:
            return 0
        return max(t['start'] + t['duration'] for t in assignments)

    @staticmethod
    def machine_idle_time(assignments, machines):
        idle = {m: 0 for m in machines}
        tasks_by_machine = {m: [] for m in machines}

        for t in assignments:
            tasks_by_machine[t['machine']].append(t)

        for m in machines:
            tasks = sorted(tasks_by_machine[m], key=lambda x: x['start'])
            prev_end = 0
            for t in tasks:
                idle[m] += max(0, t['start'] - prev_end)
                prev_end = t['start'] + t['duration']

        return idle

    @staticmethod
    def late_jobs(assignments):
        """Count of jobs where completion_time > deadline."""
        count = 0
        for t in assignments:
            completion = t['start'] + t['duration']
            due = t.get('due', t.get('deadline', 999))
            if completion > due:
                count += 1
        return count

    @staticmethod
    def energy_consumption(assignments, machine_energy_map):
        """
        Total energy consumption in kWh.
        energy = Σ(machine_operating_hours × machine_kwh_per_hour)
        """
        machine_busy = {}
        for t in assignments:
            m = t['machine']
            if m not in machine_busy:
                machine_busy[m] = 0
            machine_busy[m] += t['duration']

        total = 0.0
        for m_id, minutes in machine_busy.items():
            hours = minutes / 60.0
            kwh = machine_energy_map.get(m_id, 8.0)
            total += hours * kwh
        return round(total, 1)

    @staticmethod
    def machine_utilization(assignments, machines, makespan=None):
        """Machine utilization as percentage: busy_time / makespan."""
        if not assignments:
            return {m: 0.0 for m in machines}

        if makespan is None:
            makespan = Evaluator.makespan(assignments)
        if makespan == 0:
            return {m: 0.0 for m in machines}

        busy = {m: 0 for m in machines}
        for t in assignments:
            if t['machine'] in busy:
                busy[t['machine']] += t['duration']

        return {
            m: round((busy[m] / makespan) * 100, 1)
            for m in machines
        }
