class Evaluator:
    @staticmethod
    def average_tardiness(assignments):
        total = 0
        count = 0
        for t in assignments:
            tard = max(0, t['start'] + t['duration'] - t['due'])
            total += tard
            count += 1
        return total / count if count > 0 else 0

    @staticmethod
    def makespan(assignments):
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
