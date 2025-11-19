# **FlowForge AI – Intelligent Shop-Floor Scheduling System**

FlowForge AI is an **intelligent job-shop scheduling engine** designed for real-world manufacturing environments.
It integrates:

* ✔ Classical heuristics (SPT, EDD)
* ✔ Genetic Algorithm optimization
* ✔ Supervisor agent for machine failure handling
* ✔ Gantt chart visualization
* ✔ FastAPI backend + Kaggle notebook

---

## 🚀 Features

### 🔹 1. Heuristic Scheduling

Implements classic rules:

* **SPT (Shortest Processing Time)**
* **EDD (Earliest Due Date)**

### 🔹 2. Genetic Algorithm (GA)

Searches for near-optimal sequences by:

* Chromosome crossover
* Mutation
* Tournament selection

Achieves **lower makespan** compared to heuristics.

### 🔹 3. Supervisor Agent

Simulates machine breakdown:

* Detects `"OK"` / `"FAIL"` events
* Automatically triggers **re-scheduling**
* Stores history snapshots

### 🔹 4. Gantt Chart Visualization

Plots:

* Machine usage
* Job sequencing
* Timeline

### 🔹 5. Full REST API (optional)

Endpoints:

* `/upload_jobs`
* `/schedule`
* `/ga_schedule`
* `/supervisor_step`
* `/history`

---

## 📂 Project Structure

```
shop-floor-agent/
│
├── agents/
│   ├── scheduler.py
│   ├── ga_optimizer.py
│   ├── supervisor.py
│   └── machine_sim.py
│
├── tools/
│   ├── csv_tool.py
│   └── gantt.py
│
├── data/
├── memory/
├── scripts/
├── deployment/
│   └── app.py
└── notebooks/
```

---

## 🧪 Running Locally

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start API

```bash
uvicorn deployment.app:app --reload
```

### 3. Open docs

```
http://127.0.0.1:8000/docs
```

---

## 📊 Kaggle Notebook

The notebook includes:

* Job loading
* SPT / EDD scheduling
* GA optimization
* Supervisor simulation
* Gantt charts

It runs fully offline without FastAPI.

---

## 📈 Future Improvements

* Multi-objective GA (tardiness + energy + makespan)
* Machine setup times
* Worker skill matrices
* Constraint-based optimization (OR-Tools)
* Live dashboard with Streamlit

---

## 🏆 Author

**Shehzan Khan**
FlowForge AI – Shop Floor Intelligence System


