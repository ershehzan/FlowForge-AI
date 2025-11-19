import sys
import os

# 🔥 Add project root (shop-floor-agent) to Python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

print("ROOT DIR:", ROOT_DIR)
print("PYTHON PATH:", sys.path[:3])  # show first 3 entries

from tools.gantt import plot_gantt
from tools.csv_tool import read_jobs_csv
from agents.job_intake import load_jobs_from_list
from agents.scheduler import Scheduler

raw = read_jobs_csv("data/sample_jobs.csv")
jobs = load_jobs_from_list(raw)

scheduler = Scheduler(["M1", "M2", "M3"])
assignments = scheduler.heuristic_schedule(jobs, "SPT")

plot_gantt(assignments, title="SPT Gantt")
