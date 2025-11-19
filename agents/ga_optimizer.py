import random
from copy import deepcopy

class GAOptimizer:
    def __init__(self, jobs, machines, population_size=20, generations=30, mutation_rate=0.1):
        self.jobs = jobs
        self.machines = machines
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate

    # Step 1: Build a random chromosome (random job order)
    def random_chromosome(self):
        seq = deepcopy(self.jobs)
        random.shuffle(seq)
        return seq

    # Step 2: Fitness = makespan (lower is better)
    def evaluate(self, chromosome):
        machine_time = {m: 0 for m in self.machines}
        for job in chromosome:
            best = min(machine_time, key=machine_time.get)
            machine_time[best] += job["duration"]
        return max(machine_time.values())

    # Step 3: Tournament selection
    def select(self, population):
        a, b = random.sample(population, 2)
        return a if a["fitness"] < b["fitness"] else b

    # Step 4: Order crossover (OX)
    def crossover(self, p1, p2):
        a, b = sorted(random.sample(range(len(p1)), 2))
        child = [None] * len(p1)
        child[a:b] = p1[a:b]
        fill = [j for j in p2 if j not in child]
        idx = 0
        for i in range(len(child)):
            if child[i] is None:
                child[i] = fill[idx]
                idx += 1
        return child

    # Step 5: Mutation (swap two jobs)
    def mutate(self, chromosome):
        if random.random() < self.mutation_rate:
            a, b = random.sample(range(len(chromosome)), 2)
            chromosome[a], chromosome[b] = chromosome[b], chromosome[a]

    # Step 6: Main GA loop
    def optimize(self):
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
