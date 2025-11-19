import random

class MachineSimulator:
    def simulate_status(self, machines):
        """
        Randomly return 'OK' or 'FAIL' for each machine
        """
        status = {}
        for m in machines:
            status[m] = random.choice(["OK", "OK", "OK", "FAIL"])  # 25% failure
        return status
