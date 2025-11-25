# <div align="center">

# 🚀 **FlowForge AI**

### *Intelligent Shop-Floor Scheduling System*

<img src="https://img.icons8.com/external-flaticons-flat-flat-icons/64/000000/factory.png"/>

---

### <p align="center">

<img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white">
<img src="https://img.shields.io/badge/FastAPI-Backend-success?logo=fastapi&logoColor=white">
<img src="https://img.shields.io/badge/Genetic%20Algorithm-Optimization-red?logo=dna&logoColor=white">
<img src="https://img.shields.io/badge/Kaggle-Notebook-blue?logo=kaggle&logoColor=white">
<img src="https://img.shields.io/badge/License-MIT-orange">
</p>

---

### <p align="center">

An intelligent **job-shop scheduling engine** combining
classical heuristics, evolutionary optimization, and autonomous supervisor agents
for real-world manufacturing systems.

</p>

</div>

---

# 🧠 Overview

FlowForge AI delivers **dynamic, near-optimal scheduling** using:

* ✔ Shortest Processing Time (SPT)
* ✔ Earliest Due Date (EDD)
* ✔ Genetic Algorithm optimization
* ✔ Real-time machine failure handling
* ✔ Gantt chart visualization
* ✔ Optional FastAPI backend
* ✔ Kaggle notebook version

---

# ✨ **Core Features**

## 🔹 1. Heuristic Scheduling

Classical priority rules:

* **SPT (Shortest Processing Time)**
* **EDD (Earliest Due Date)**

Useful for quick baseline scheduling.

---

## 🔹 2. Genetic Algorithm (GA)

Evolutionary optimization featuring:

* Crossover
* Mutation
* Tournament selection

Produces **significantly lower makespan** than heuristics alone.

---

## 🔹 3. Supervisor Agent

Simulates real manufacturing disruptions:

* Detects **OK / FAIL** machine states
* Initiates **auto rescheduling**
* Saves state snapshots in history

---

## 🔹 4. Gantt Chart Visualization

Generates visual timelines of:

* Machine usage
* Job ordering
* Processing intervals

---

## 🔹 5. Full REST API (Optional)

```
/upload_jobs
/schedule
/ga_schedule
/supervisor_step
/history
```

---

# 📁 **Project Structure**

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

# 🧪 **Run Locally**

### 1. Install requirements

```bash
pip install -r requirements.txt
```

### 2. Start API

```bash
uvicorn deployment.app:app --reload
```

### 3. Visit docs

```
http://127.0.0.1:8000/docs
```

---

# 📊 **Kaggle Notebook**

Includes:

* Job dataset loader
* SPT + EDD scheduling
* GA optimization
* Supervisor simulation
* Gantt chart rendering

Runs fully offline.

---

# 🚧 **Future Improvements**

* Multi-objective GA (makespan + tardiness + energy)
* Machine setup/changeover times
* Worker skill matrices
* OR-Tools constraint solver
* Streamlit dashboard

---

# 🏆 **Author**

### **Shehzan Khan**

*FlowForge AI – Shop Floor Intelligence System*

© 2025 Shehzan Khan. Created as a personal portfolio project.

