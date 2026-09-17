import random
from copy import deepcopy


class GAOptimizer:
    def __init__(self, jobs, machines, population_size=20, generations=30,
                 mutation_rate=0.1, machine_energy=None, weights=None):
        self.jobs = jobs
        self.machines = machines
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate

        # Machine energy map: {machine_id: kwh_per_hour}
        # Default to 8.0 kWh/hour if not provided
        self.machine_energy = machine_energy or {}

        # Multi-objective fitness weights (must sum to 1.0)
        # Lower fitness = better schedule
        self.weights = weights or {
            "makespan": 0.30,
            "tardiness": 0.35,
            "downtime": 0.15,
            "energy": 0.20,
        }

    # Step 1: Build a random chromosome (random job order)
    def random_chromosome(self):
        seq = deepcopy(self.jobs)
        random.shuffle(seq)
        return seq

    # Step 2: Multi-objective fitness (lower is better)
    def evaluate(self, chromosome):
        machine_time = {m: 0 for m in self.machines}
        assignments = []

        for job in chromosome:
            best = min(machine_time, key=machine_time.get)
            start = machine_time[best]
            assignments.append({
                "job_id": job["job_id"],
                "machine": best,
                "start": start,
                "duration": job["duration"],
                "due": job.get("due", job.get("deadline", 999)),
            })
            machine_time[best] = start + job["duration"]

        # Calculate individual objectives
        makespan = max(machine_time.values()) if machine_time else 0

        # Total tardiness
        tardiness = 0
        for a in assignments:
            completion = a["start"] + a["duration"]
            tardiness += max(0, completion - a["due"])

        # Machine downtime / idle (sum of gaps)
        downtime = 0
        if makespan > 0:
            for m in self.machines:
                downtime += makespan - machine_time.get(m, 0)

        # Energy consumption
        energy = 0
        for m_id, busy_time in machine_time.items():
            kwh = self.machine_energy.get(m_id, 8.0)
            energy += (busy_time / 60.0) * kwh  # convert minutes to hours

        # Normalize objectives for weighted combination.
        # Use simple scaling: divide by a reasonable reference value
        # to keep all objectives in a comparable range.
        num_jobs = len(chromosome) if chromosome else 1
        norm_makespan = makespan / max(1, num_jobs * 10)
        norm_tardiness = tardiness / max(1, num_jobs * 10)
        norm_downtime = downtime / max(1, makespan * len(self.machines)) if makespan > 0 else 0
        norm_energy = energy / max(1, num_jobs * 2)

        # Weighted sum (lower is better)
        w = self.weights
        fitness = (
            w.get("makespan", 0.30) * norm_makespan
            + w.get("tardiness", 0.35) * norm_tardiness
            + w.get("downtime", 0.15) * norm_downtime
            + w.get("energy", 0.20) * norm_energy
        )

        return fitness

    # Step 3: Tournament selection
    def select(self, population):
        a, b = random.sample(population, 2)
        return a if a["fitness"] < b["fitness"] else b

    # Step 4: Order crossover (OX)
    def crossover(self, p1, p2):
        if len(p1) < 2:
            return list(p1)  # nothing to crossover with 0 or 1 job
        a, b = sorted(random.sample(range(len(p1)), 2))
        child = [None] * len(p1)
        child[a:b] = p1[a:b]
        # Use job_id for membership check instead of dict identity (dicts are not hashable)
        child_ids = {j["job_id"] for j in child if j is not None}
        fill = [j for j in p2 if j["job_id"] not in child_ids]
        idx = 0
        for i in range(len(child)):
            if child[i] is None:
                child[i] = fill[idx]
                idx += 1
        return child

    # Step 5: Mutation (swap two jobs)
    def mutate(self, chromosome):
        if len(chromosome) >= 2 and random.random() < self.mutation_rate:
            a, b = random.sample(range(len(chromosome)), 2)
            chromosome[a], chromosome[b] = chromosome[b], chromosome[a]

    # Step 6: Main GA loop
    def optimize(self):
        if not self.jobs:
            return {"chrom": [], "fitness": 0.0}
        if len(self.jobs) == 1:
            return {"chrom": list(self.jobs), "fitness": self.evaluate(list(self.jobs))}

        population = []

        # initialize population
        for _ in range(self.population_size):
            chrom = self.random_chromosome()
            fitness = self.evaluate(chrom)
            population.append({"chrom": chrom, "fitness": fitness})

        # evolve
        for _ in range(self.generations):
            new_pop = []
            for _ in range(self.population_size):
                p1 = self.select(population)["chrom"]
                p2 = self.select(population)["chrom"]
                child = self.crossover(p1, p2)
                self.mutate(child)
                fit = self.evaluate(child)
                new_pop.append({"chrom": child, "fitness": fit})
            population = new_pop

        # pick best chromosome
        best = min(population, key=lambda x: x["fitness"])
        return best
