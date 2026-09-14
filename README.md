# ⚡ FlowForge AI — *Autonomous Production Resilience & Optimization*

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.121-success?logo=fastapi&logoColor=white)
![Claude](https://img.shields.io/badge/AI%20Copilot-Claude%203.5%20Sonnet-blueviolet?logo=anthropic&logoColor=white)
![Genetic Algorithm](https://img.shields.io/badge/Optimizer-Multi--Objective%20GA-red)
![Tests](https://img.shields.io/badge/Tests-73%20Passing-brightgreen?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-orange)

> **"When the factory changes, the schedule changes with it."**

**FlowForge AI** is an industrial-grade autonomous production resilience and shop-floor scheduling system. It detects machine failures, rush orders, and bottleneck shifts in real time, computes multi-objective optimized recovery plans, and visualizes shop-floor dynamics through dynamic Gantt charts and interactive machine controls — all backed by a Genetic Algorithm optimizer and an AI-powered Operations Copilot.

---

## 📑 Table of Contents

- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [Technologies Used](#-technologies-used)
- [AI Tools & Models](#-ai-tools--models)
- [Project Structure](#-project-structure)
- [Supported Data Formats](#-supported-data-formats)
- [Setup & Installation](#-setup--installation)
- [Environment Configuration](#-environment-configuration)
- [Usage](#-usage)
- [REST API Reference](#-rest-api-reference)
- [Running Tests](#-running-tests)
- [Scripts & Utilities](#-scripts--utilities)
- [Disruption & Resilience Walkthrough](#-disruption--resilience-walkthrough)
- [Authors & License](#-authors--license)

---

## 🏭 Project Overview

FlowForge AI solves a core challenge in modern manufacturing: **how does a factory stay productive when reality diverges from the plan?**

It combines:
- A **Multi-Objective Genetic Algorithm** (GA) scheduler that optimizes makespan, tardiness, energy, and utilization simultaneously.
- An **Autonomous Disruption Engine** that reacts to machine failures, rush orders, and deadline shifts in real time.
- An **AI Operations Copilot** (powered by Claude 3.5 Sonnet) that reasons over live factory state and answers engineering questions in natural language.
- An **ERP-lite Coordination Layer** that tracks production orders, raw material inventory, machine maintenance, and capacity in a unified view.
- An **Apple-grade editorial web UI** with scroll-driven canvas animation, real-time Gantt rendering, and a full Factory Explorer.

---

## 🌟 Key Features

### 🎨 1. Apple-Grade Editorial Industrial UI
- **Frame-by-Frame Scroll Storytelling**: Interactive canvas-driven machine assembly animation synchronized to page scroll using GSAP ScrollTrigger and high-DPI canvas rendering.
- **Minimalist Aesthetic**: Clean light-gray industrial design, refined typography, and glassmorphic micro-interactions.
- **Clickable Status Indicator**: Live top-right status pill (`🟢 OPERATIONAL` / `🔴 DISRUPTED`) that displays the active factory condition and allows 1-click factory reset.

### 📥 2. Flexible Multi-Format Ingestion Engine
- **Smart Excel Parser (`.xlsx`, `.xls`)**:
  - **Fuzzy Header Synonym Matching**: Maps columns like `Part Name` ➔ `job_id`, `Cycle Time` ➔ `processing_time`, `Station` ➔ `machine` automatically.
  - **Single-Sheet Auto-Conversion**: Automatically parses job tables and synthesizes machine models if a dedicated machines sheet is omitted.
  - Transactional validation and user error feedback.
- **JSON Job Shop Benchmark Parser (`.json`)**:
  - Accepts standard and custom Job Shop Scheduling Problem (JSSP) instances.
  - Ingests dynamic machine fleets (`M0`, `M1`, `M2`...) and handles scheduled downtime windows (`unavailable_periods` e.g., `[[7, 12]]`).
  - Automatically parses multi-operation job workflows with explicit sequence precedence.

### ⚙️ 3. Precedence-Aware & Downtime-Resistant Scheduling
- **Operation Sequence Precedence**: Guarantees that step $k+1$ for any multi-operation job strictly starts after step $k$ completes.
- **Downtime & Maintenance Window Avoidance**: Automatically routes jobs around scheduled machine maintenance or unplanned outages without overlap.
- **Multi-Objective Optimization**:
  - ⏱ **Makespan Minimization**: Shortens overall factory completion time.
  - ⏳ **Tardiness Mitigation**: Heavily penalizes overdue delivery commitments.
  - ⚡ **Energy Optimization**: Balances kW power profiles across machines.
  - 🛑 **Utilization & Idle Capacity**: Keeps high-value equipment running efficiently.

### 🛡️ 4. Autonomous Disruption & Recovery Engine
- **Event-Driven Resilience**:
  - **Machine Failures**: Instantly detects station breakdowns and reroutes queued tasks to available backup machines.
  - **Urgent Job Arrivals**: Preemptively slots expedited rush orders (`J99`) while minimizing ripple delays.
  - **Deadline Shifts**: Automatically reschedules when customer order deadlines move forward (`J7`).
  - **Machine Recovery**: Dynamically re-balances active workloads when repaired equipment comes back online.
- **Quantitative Resilience Index (0–100)**: Proprietary composite score benchmarking schedule robustness, tardiness mitigation, capacity retention, and energy stability.

### 📊 5. Real-Time Shop-Floor Observability
- **Dynamic Gantt Chart**: Color-coded operations by status (*On-Time*, *Reassigned*, *At Risk*, *Late*), hatched maintenance window overlays (`Maint 7-12m`), and rich hover inspection cards.
- **Factory Explorer**: Interactive machine station cards displaying live status (`RUNNING`, `STOPPED`, `MAINT`), real-time utilization, and 1-click failure simulation toggles.
- **Before-vs-After Comparison**: Side-by-side KPI deltas highlighting impact on Makespan, Tardiness, Energy Consumption, and Resilience.
- **Explainable AI Decision Reports**: Transparent audit summaries detailing exactly which jobs were rerouted and why.

---

## 📁 **Project Architecture**

```
FlowForge-AI/
├── agents/
│   ├── disruption/
│   │   ├── engine.py           # Autonomous Disruption Engine & event loop
│   │   └── types.py            # Disruption event data structures
│   ├── factory/
│   │   ├── excel_parser.py     # Smart Excel parser with fuzzy synonym matching
│   │   ├── json_parser.py      # JSON Job Shop instance & maintenance parser
│   │   ├── job.py              # Job model & operations representation
│   │   ├── machine.py          # Machine model & failure simulation
│   │   └── state.py            # Central FactoryState tracking
│   ├── resilience/
│   │   ├── metrics.py          # Makespan, tardiness, utilization & energy metrics
│   │   └── score.py            # Multi-dimensional resilience index (0-100)
│   ├── ga_optimizer.py         # Multi-objective Genetic Algorithm
│   ├── scheduler.py            # Precedence & downtime-aware schedulers (GA, SPT, EDD)
│   ├── supervisor.py           # Factory coordination supervisor
│   └── machine_sim.py          # Machine lifecycle simulator
├── deployment/
│   └── app.py                  # FastAPI server, REST routes & static frame streaming
├── frontend/
│   ├── index.html              # Apple-grade editorial dashboard markup
│   ├── styles.css              # Custom light industrial theme & canvas styles
│   ├── app.js                  # Frontend controller, canvas animator & Gantt renderer
│   └── assets/machines/        # Machine hardware reference imagery
├── frames/                     # Cleaned image frames for scroll canvas animation
├── examples/
│   ├── factory_data_template.xlsx  # Production Excel template
│   └── job_shop_sample.json        # Sample JSON job shop problem instance
├── tests/
│   ├── test_foundation.py      # Factory, GA, resilience & disruption test suite
│   ├── test_excel_parser.py    # Excel workbook ingestion & fuzzy matching tests
│   └── test_json_parser.py     # JSON parser & maintenance window tests
└── requirements.txt            # Project dependencies
```

---

## 📋 **Supported Data Formats**

FlowForge AI supports direct file upload via drag-and-drop or file picker:

### 1. JSON Job Shop Specification (`.json`)
Supports custom and benchmark job shop problems with planned maintenance periods:
```json
{
  "machines": [
    { "machine_id": "M0", "unavailable_periods": [[7, 12]] },
    { "machine_id": "M1", "unavailable_periods": [] },
    { "machine_id": "M2", "unavailable_periods": [] }
  ],
  "jobs": [
    {
      "job_id": "J0",
      "priority": 3,
      "due_date": 50,
      "operations": [
        { "operation_id": "J0_op0", "machine_id": "M0", "processing_time": 10 },
        { "operation_id": "J0_op1", "machine_id": "M1", "processing_time": 15 },
        { "operation_id": "J0_op2", "machine_id": "M2", "processing_time": 8 }
      ]
    }
  ]
}
```

### 2. Production Excel Workbook (`.xlsx`, `.xls`)
Accepts two formats:
1. **Multi-Sheet Workbook**: Contains a `Jobs` sheet (Job ID, Processing Time, Deadline, Priority, Machine) and a `Machines` sheet (Machine ID, Power kW, Idle Power kW).
2. **Single-Sheet Table**: Upload any flat production schedule table; FlowForge automatically synthesizes machine models and maps ambiguous column headers (e.g. `Order #` ➔ `job_id`, `Duration` ➔ `processing_time`).

---

## 🚀 **Getting Started**

### Prerequisites
- Python 3.10 or higher
- pip & virtual environment tool

### 1. Clone & Setup Virtual Environment
```bash
git clone https://github.com/ershehzan/FlowForge-AI.git
cd FlowForge-AI

# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Automated Test Suite
```bash
pytest
```
*All 73 automated tests should pass across factory models, genetic algorithms, disruption handling, Excel parsing, and JSON scheduling.*

### 4. Launch the Server
```bash
uvicorn deployment.app:app --reload --port 8000
```

Open your browser and navigate to:
- **Interactive UI**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **FastAPI Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📡 **REST API Reference**

| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Serves the main FlowForge editorial web application |
| `/frames/` | `GET` | Lists and streams frame images for canvas scroll animation |
| `/frames/manifest.json` | `GET` | Auto-detects total available frame count for the animation engine |
| `/factory/initialize` | `POST` | Re-initializes factory state and computes baseline schedule |
| `/factory/state` | `GET` | Retrieves real-time factory state, machine statuses, and schedules |
| `/factory/upload` | `POST` | Ingests `.xlsx`, `.xls`, or `.json` files, optimizes schedule & returns metrics |
| `/disruptions` | `POST` | Injects disruption events (`machine_failure`, `urgent_job`, `deadline_change`, `machine_recovery`) and triggers autonomous recovery |
| `/metrics` | `GET` | Returns current schedule metrics (makespan, tardiness, energy, utilization) |
| `/resilience` | `GET` | Computes multi-dimensional factory resilience index (0–100) |
| `/factory/reset` | `POST` | Resets factory floor to pristine baseline operational state |

---

## 🧪 **Disruption & Resilience Walkthrough**

Try the following interactive flows directly from the dashboard:

1. **Test Machine Breakdown**:
   - Scroll to **Scenarios** and click **`🔴 Fail M3`** (or click a machine card in the **Factory Explorer**).
   - Watch the status badge switch to `🔴 DISRUPTED`.
   - The engine automatically routes tasks away from `M3` and generates a recovery schedule.
2. **Test Rush Order Injection**:
   - Click **`⚡ Urgent Job`** to introduce priority order `J99` with a tight delivery window.
   - Observe the Gantt chart slotting `J99` ahead of lower-priority jobs while preserving deadlines.
3. **Test Maintenance & Precedence (`.json`)**:
   - In **Factory Data**, click **Load Sample JSON** and click **Run FlowForge Optimization**.
   - Notice hatched maintenance blocks (`Maint 7-12m`) on `M0` and strictly sequenced operations across `M0` ➔ `M1` ➔ `M2`.
4. **1-Click Reset to Operational**:
   - Click the top-right **`🔴 DISRUPTED`** badge or click **`↺ Reset Factory`** to restore all machines to `🟢 OPERATIONAL`.

---

## 🏆 **Author & License**

**Shehzan Khan**
**Shorya Agrawal**  
*FlowForge AI — Autonomous Production Resilience & Optimization*

Released under the **MIT License**.
