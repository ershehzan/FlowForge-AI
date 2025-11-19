import json

class MemoryBank:
    def __init__(self):
        self.snapshots = []

    def save_snapshot(self, data):
        self.snapshots.append(data)

    def export(self, file="memory_bank.json"):
        with open(file, "w") as f:
            json.dump(self.snapshots, f, indent=4)
