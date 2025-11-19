import matplotlib.pyplot as plt

def plot_gantt(assignments, title="Schedule Gantt Chart"):
    fig, ax = plt.subplots(figsize=(10, 6))

    for task in assignments:
        start = task["start"]
        dur = task["duration"]
        machine = task["machine"]
        job = task["job_id"]

        ax.barh(machine, dur, left=start)
        ax.text(start + dur/2, machine, job, color="white",
                ha="center", va="center")

    ax.set_xlabel("Time")
    ax.set_ylabel("Machines")
    ax.set_title(title)
    plt.show()
