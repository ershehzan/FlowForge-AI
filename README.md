# ⚡ **FlowForge AI** : *Autonomous Production Resilience & Optimization*

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-success?logo=fastapi&logoColor=white)
![Genetic Algorithm](https://img.shields.io/badge/Genetic%20Algorithm-Multi--Objective-red?logo=dna&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-73%20Passing-brightgreen?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-orange)

> **"When the factory changes, the schedule changes with it."**

**FlowForge AI** is an industrial-grade autonomous production resilience and shop-floor scheduling system. Designed with an Apple-grade editorial interface and high-performance algorithmic backend, FlowForge detects machine failures, rush orders, and bottleneck shifts in real time, computes multi-objective optimized recovery plans, and visualizes shop-floor dynamics through dynamic Gantt charts and interactive machine controls.

---

## 🌟 **Key Features**

### 🎨 1. Apple-Grade Editorial Industrial UI
- **Frame-by-Frame Scroll Storytelling**: Interactive canvas-driven machine assembly animation synchronized to page scroll using high-DPI canvas rendering and smooth interpolation.
- **Industrial Minimalist Design**: Clean light-gray industrial aesthetic, refined typography, and glassmorphic micro-interactions.
- **Real-Time Status Indicator**: Dynamic sticky header status pill (`🟢 OPERATIONAL` / `🔴 DISRUPTED`) providing immediate operational state awareness and 1-click factory reset.

### 🏭 2. Integrated 9 ERP-Lite Operational Modules
FlowForge bridges algorithmic resilience with daily manufacturing operations through 9 interconnected modules:

1. **Command Center**: Real-time operational cockpit aggregating active disruptions, order statuses, machine capacity loads, and factory resilience index.
2. **Production Operations**: End-to-end production orders (`ORD-1001` through `ORD-1006`), customer commitments, quantities, deadline risk flags (*Low*, *Medium*, *Critical*), and completion progress bars.
3. **Shop Floor & Fleet Telemetry**: Station cards displaying real-time machine statuses (`RUNNING`, `STOPPED`, `MAINTENANCE`), live utilization %, power profiles (kW), and single-click failure/recovery simulation toggles.
4. **Inventory & Materials Management**: Raw material stock balances (`RM-001` to `RM-006`), allocated/reserved stock, minimum reorder thresholds, inventory health indicators (`IN STOCK`, `LOW STOCK`, `OUT OF STOCK`), and 1-click replenishment reorders.
5. **Preventative & Corrective Maintenance**: Machine health scores (0–100%), Mean Time Between Failures (MTBF), upcoming scheduled maintenance windows, downtime logs, and interactive maintenance record logging.
6. **Comparative Analytics & Capacity Matrix**: Side-by-side KPI deltas across Baseline, Disrupted, and Recovery states; machine capacity load matrix (available hours, scheduled load, utilization %, remaining capacity); and multi-dimensional resilience score breakdowns.
7. **AI Operations Copilot**: Engineering reasoning layer powered by Anthropic Claude 3.5 Sonnet (with automatic deterministic rule-based fallback). Provides quantitative root-cause analysis, affected entity lists (`M3`, `J07`, `ORD-1004`), and actionable engineering guidance without violating the mathematical integrity of the GA optimizer.
8. **Scenario Simulation Sandbox**: Real-time simulation of unexpected factory events: machine breakdowns (`🔴 Fail M3`), urgent rush orders (`⚡ Urgent Job J99`), customer deadline shifts (`⏳ Shift J7`), job cancellations (`❌ Cancel J12`), and machine recovery (`🟢 Recover M3`).
9. **Audit History & Explainable AI (XAI) Reports**: Chronological audit trail recording disruption events, delta metrics (Makespan, Tardiness, Energy, Resilience), and transparent XAI decision reports explaining rerouting choices, rationale, and operational trade-offs.

### 📥 3. Flexible Multi-Format Ingestion Engine
- **Smart Excel Parser (`.xlsx`, `.xls`)**:
  - **Fuzzy Header Synonym Matching**: Maps columns like `Part Name` ➔ `job_id`, `Cycle Time` ➔ `processing_time`, `Station` ➔ `machine` automatically.
  - **Single-Sheet Auto-Conversion**: Automatically parses job tables and synthesizes machine models if a dedicated machines sheet is omitted.
  - Transactional validation and user error feedback.
- **JSON Job Shop Benchmark Parser (`.json`)**:
  - Accepts standard and custom Job Shop Scheduling Problem (JSSP) benchmark instances.
  - Ingests dynamic machine fleets (`M0`, `M1`, `M2`...) and handles scheduled downtime windows (`unavailable_periods` e.g., `[[7, 12]]`).
  - Automatically parses multi-operation job workflows with explicit sequence precedence.

### ⚙️ 4. Precedence-Aware & Downtime-Resistant Scheduling
- **Operation Sequence Precedence**: Guarantees that step $k+1$ for any multi-operation job strictly starts after step $k$ completes.
- **Downtime & Maintenance Window Avoidance**: Automatically routes jobs around scheduled machine maintenance or unplanned outages without overlap.
- **Multi-Objective Optimization**:
  - ⏱ **Makespan Minimization**: Shortens overall factory completion time.
  - ⏳ **Tardiness Mitigation**: Heavily penalizes overdue delivery commitments.
  - ⚡ **Energy Optimization**: Balances kW power profiles across machines.
  - 🛑 **Utilization & Idle Capacity**: Keeps high-value equipment running efficiently.

### 🛡️ 5. Autonomous Disruption & Recovery Engine
- **Event-Driven Resilience**:
  - **Machine Failures**: Instantly detects station breakdowns and reroutes queued tasks to available backup machines.
  - **Urgent Job Arrivals**: Preemptively slots expedited rush orders (`J99`) while minimizing ripple delays.
  - **Deadline Shifts**: Automatically reschedules when customer order deadlines move forward (`J7`).
  - **Job Cancellations**: Dynamically compacts schedules when orders are removed (`J12`).
  - **Machine Recovery**: Dynamically re-balances active workloads when repaired equipment comes back online.
- **Quantitative Resilience Index (0–100)**: Proprietary composite score benchmarking schedule robustness, tardiness mitigation, capacity retention, and energy stability.

### 📊 6. Real-Time Shop-Floor Observability
- **Dynamic Gantt Chart**: Color-coded operations by status (*On-Time*, *Reassigned*, *At Risk*, *Late*), hatched maintenance window overlays (`Maint 7-12m`), and rich hover inspection cards.
- **Interactive Explanations**: Real-time feedback explaining why specific schedules were selected and how trade-offs were resolved.

---

## 📁 **Project Architecture**

```
FlowForge-AI/
├── agents/
│   ├── copilot/
│   │   ├── __init__.py         # AI Copilot package export
│   │   └── provider.py         # Claude 3.5 Sonnet & deterministic reasoning copilot
│   ├── disruption/
│   │   ├── engine.py           # Autonomous Disruption Engine & event loop
│   │   └── types.py            # Disruption event data structures
│   ├── erp/
│   │   ├── __init__.py         # ERP-lite package export
│   │   ├── engine.py           # ERP operations coordinator & state synchronizer
│   │   └── models.py           # ProductionOrder, InventoryItem, MaintenanceRecord
│   ├── factory/
│   │   ├── excel_parser.py     # Smart Excel parser with fuzzy synonym matching
│   │   ├── json_parser.py      # JSON Job Shop instance & maintenance parser
│   │   ├── job.py              # Job model & operations representation
│   │   ├── machine.py          # Machine model & failure simulation
│   │   └── state.py            # Central FactoryState tracking & erp_state binding
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
│   ├── index.html              # Apple-grade editorial dashboard with 9 ERP modules
│   ├── styles.css              # Custom industrial theme, card layouts & animations
│   ├── app.js                  # Frontend controller, canvas animator & Gantt renderer
│   └── assets/machines/        # Machine hardware reference imagery
├── frames/                     # Cleaned image frames for scroll canvas animation
├── examples/
│   ├── factory_data_template.xlsx  # Production Excel template
│   └── job_shop_sample.json        # Sample JSON job shop problem instance
├── scripts/
│   └── smoke_test.py           # Comprehensive 18-step end-to-end smoke test suite
├── tests/
│   ├── test_erp_modules.py     # Unit tests for ERP models, capacity & AI Copilot
│   ├── test_foundation.py      # Factory, GA, resilience & disruption test suite
│   ├── test_excel_parser.py    # Excel workbook ingestion & fuzzy matching tests
│   └── test_json_parser.py     # JSON parser & maintenance window tests
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Project dependencies
└── .env.example                # Sample environment variables
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
- Python 3.10 or higher (Python 3.11+ recommended)
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

### 3. (Optional) Configure Environment Variables
Copy `.env.example` to `.env` to configure optional settings:
```bash
cp .env.example .env
```
To enable Claude 3.5 Sonnet for the AI Copilot, set your Anthropic API key in `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-...
```
> *Note: If no API key is set, FlowForge automatically runs in **deterministic rule-based reasoning mode**, providing complete offline capability.*

### 4. Run the Automated Test Suite
```bash
pytest
```
*All 80 automated unit and integration tests will execute across factory models, genetic algorithms, disruption handling, Excel parsing, JSON benchmark scheduling, ERP models, and AI Copilot reasoning.*

### 5. Launch the Server
```bash
uvicorn deployment.app:app --reload --port 8000
```

Open your browser and navigate to:
- **Interactive UI**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **FastAPI Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 6. Run Comprehensive Smoke Tests (Optional)
While the server is running, you can execute the end-to-end smoke test suite verifying all 18 API workflows:
```bash
python scripts/smoke_test.py
```

---

## 📡 **REST API Reference**

### Core & Factory Operations
| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Serves the main FlowForge editorial web application |
| `/frames/` | `GET` | Lists and streams frame images for canvas scroll animation |
| `/frames/manifest.json` | `GET` | Auto-detects total available frame count for the animation engine |
| `/factory/initialize` | `POST` | Re-initializes factory state and computes baseline schedule |
| `/factory/state` | `GET` | Retrieves real-time factory state, machine fleet, and ERP state |
| `/factory/upload` | `POST` | Ingests `.xlsx`, `.xls`, or `.json` files, optimizes schedule & returns metrics |
| `/disruptions` | `POST` | Injects disruption events (`machine_failure`, `urgent_job`, `deadline_change`, `job_cancellation`, `machine_recovery`) and triggers autonomous recovery |
| `/metrics` | `GET` | Returns current schedule metrics (makespan, tardiness, energy, utilization) |
| `/resilience` | `GET` | Computes multi-dimensional factory resilience index (0–100) |
| `/factory/reset` | `POST` | Resets factory floor and ERP models to pristine baseline operational state |

### ERP-Lite Operations
| Endpoint | Method | Description |
|---|---|---|
| `/erp/state` | `GET` | Returns full ERP-lite operational state (orders, inventory, maintenance, capacity) |
| `/orders` | `GET` | Returns list of production orders with deadline risk and progress tracking |
| `/inventory` | `GET` | Returns raw material inventory balances, stockout alerts, and reorder levels |
| `/maintenance` | `GET` | Returns machine health indices (0-100%), MTBF, and maintenance records |
| `/capacity` | `GET` | Returns machine fleet capacity matrix (scheduled load, utilization, remaining hours) |
| `/analytics` | `GET` | Returns comparative metrics and resilience scores across Baseline, Disrupted, and Recovery |
| `/history` | `GET` | Returns historical disruption audit log and explainable AI decision reports |

### AI Operations Copilot
| Endpoint | Method | Description |
|---|---|---|
| `/copilot/query` | `POST` | Analyzes operational questions against live factory state using Claude 3.5 Sonnet or deterministic fallback |

---

## 🧪 **Disruption & Resilience Walkthrough**

Try the following interactive flows directly from the dashboard:

1. **Test Machine Breakdown**:
   - Scroll to **Scenarios** and click **`🔴 Fail M3`** (or click a machine card in **Shop Floor**).
   - Watch the status badge switch to `🔴 DISRUPTED`.
   - The engine automatically routes tasks away from `M3` and generates a recovery schedule.
2. **Test Rush Order Injection**:
   - Click **`⚡ Urgent Job`** to introduce priority order `J99` with a tight delivery window.
   - Observe the Gantt chart slotting `J99` ahead of lower-priority jobs while preserving deadlines.
3. **Inspect ERP Operations**:
   - Scroll to **Production** to view active orders and risk status.
   - Review **Inventory** for material availability and click **Reorder** to simulate stock replenishment.
   - Check **Maintenance** for machine health degradation and upcoming service windows.
4. **Ask the AI Operations Copilot**:
   - Navigate to **AI Copilot** and click a suggested prompt (e.g., *"Why was J7 moved to M5?"* or *"What is our current capacity bottleneck?"*).
   - View quantitative root-cause explanations and recommended engineering actions.
5. **Review Audit Trail & Decision Reports**:
   - Scroll to **History** to review the chronologically logged disruption events and side-by-side KPI deltas.
6. **1-Click Reset to Operational**:
   - Click the top-right **`🔴 DISRUPTED`** badge or click **`↺ Reset Factory`** to restore all machines and ERP models to `🟢 OPERATIONAL`.

---

## 🏆 **Authors & License**

**Shehzan Khan**  
**Shorya Agrawal**  
*FlowForge AI — Autonomous Production Resilience & Manufacturing Operations*

Released under the **MIT License**.
