# FlowForge AI - Autonomous Production Resilience & Optimization

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.121-success?logo=fastapi&logoColor=white)
![Claude](https://img.shields.io/badge/AI%20Copilot-Claude%203.5%20Sonnet-blueviolet?logo=anthropic&logoColor=white)
![Genetic Algorithm](https://img.shields.io/badge/Optimizer-Multi--Objective%20GA-red)
![Tests](https://img.shields.io/badge/Tests-73%20Passing-brightgreen?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-orange)

> **"When the factory changes, the schedule changes with it."**

**FlowForge AI** is an industrial-grade autonomous production resilience and shop-floor scheduling system. It detects machine failures, rush orders, and bottleneck shifts in real time, computes multi-objective optimized recovery plans, and visualizes shop-floor dynamics through dynamic Gantt charts and interactive machine controls -- all backed by a Genetic Algorithm optimizer and an AI-powered Operations Copilot.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Technologies Used](#technologies-used)
- [AI Tools and Models](#ai-tools-and-models)
- [Project Structure](#project-structure)
- [Supported Data Formats](#supported-data-formats)
- [Setup and Installation](#setup-and-installation)
- [Environment Configuration](#environment-configuration)
- [Usage](#usage)
- [REST API Reference](#rest-api-reference)
- [Running Tests](#running-tests)
- [Scripts and Utilities](#scripts-and-utilities)
- [Disruption and Resilience Walkthrough](#disruption-and-resilience-walkthrough)
- [Authors and License](#authors-and-license)

---

## Project Overview

FlowForge AI solves a core challenge in modern manufacturing: **how does a factory stay productive when reality diverges from the plan?**

It combines:
- A **Multi-Objective Genetic Algorithm** (GA) scheduler that optimizes makespan, tardiness, energy, and utilization simultaneously.
- An **Autonomous Disruption Engine** that reacts to machine failures, rush orders, and deadline shifts in real time.
- An **AI Operations Copilot** (powered by Claude 3.5 Sonnet) that reasons over live factory state and answers engineering questions in natural language.
- An **ERP-lite Coordination Layer** that tracks production orders, raw material inventory, machine maintenance, and capacity in a unified view.
- An **Apple-grade editorial web UI** with scroll-driven canvas animation, real-time Gantt rendering, and a full Factory Explorer.

---

## Key Features

### 1. Apple-Grade Editorial Industrial UI
- **Frame-by-Frame Scroll Storytelling**: Canvas-driven machine assembly animation synchronized to page scroll using GSAP ScrollTrigger and high-DPI canvas rendering.
- **Minimalist Aesthetic**: Clean light-gray industrial design with refined typography and glassmorphic micro-interactions.
- **Clickable Status Indicator**: Live top-right status pill (OPERATIONAL / DISRUPTED) allowing 1-click factory reset.

### 2. Flexible Multi-Format Ingestion Engine
- **Smart Excel Parser** (`.xlsx`, `.xls`):
  - **Fuzzy Header Synonym Matching**: Maps columns like `Part Name` to `job_id`, `Cycle Time` to `processing_time`, `Station` to `machine` automatically.
  - **Single-Sheet Auto-Conversion**: Parses flat job tables and synthesizes machine models if a dedicated machines sheet is absent.
- **JSON Job Shop Benchmark Parser** (`.json`):
  - Accepts standard and custom Job Shop Scheduling Problem (JSSP) instances.
  - Ingests dynamic machine fleets (`M0`, `M1`, `M2`...) with scheduled downtime windows (`unavailable_periods`, e.g., `[[7, 12]]`).
  - Parses multi-operation job workflows with explicit sequence precedence.

### 3. Precedence-Aware and Downtime-Resistant Scheduling
- **Operation Sequence Precedence**: Guarantees that step k+1 for any multi-operation job strictly starts after step k completes.
- **Downtime and Maintenance Window Avoidance**: Automatically routes jobs around scheduled maintenance or unplanned outages.
- **Multi-Objective Optimization**:
  - **Makespan Minimization** -- Shortens overall factory completion time.
  - **Tardiness Mitigation** -- Heavily penalizes overdue delivery commitments.
  - **Energy Optimization** -- Balances kW power profiles across machines.
  - **Utilization and Idle Capacity** -- Keeps high-value equipment running efficiently.

### 4. Autonomous Disruption and Recovery Engine
- **Event-Driven Resilience**:
  - **Machine Failures**: Instantly detects station breakdowns and reroutes queued tasks to backup machines.
  - **Urgent Job Arrivals**: Preemptively slots expedited rush orders (`J99`) while minimizing ripple delays.
  - **Deadline Shifts**: Automatically reschedules when customer order deadlines compress (`J7`).
  - **Machine Recovery**: Dynamically re-balances workloads when repaired equipment comes back online.
- **Quantitative Resilience Index (0-100)**: A composite score benchmarking schedule robustness, tardiness mitigation, capacity retention, and energy stability.

### 5. AI Operations Copilot
- Natural-language engineering Q&A over live factory state.
- Powered by **Claude 3.5 Sonnet** (Anthropic) with a robust deterministic fallback engine.
- Returns structured JSON answers with `answer`, `metrics`, `affected_entities`, and `recommended_action`.

### 6. ERP-Lite Coordination Layer
- **Production Orders**: Tracks 6 active orders with customer, product, priority, deadline, progress, and risk level.
- **Raw Material Inventory**: Manages 6 material SKUs with live status (IN STOCK / LOW STOCK / OUT OF STOCK).
- **Machine Maintenance**: Health scores, last/next maintenance dates, runtime hours, and active issue logs per station.
- **Capacity Matrix**: Per-machine scheduled load, available capacity, and utilization percentage per 8-hour shift.
- **Attention Alerts**: Auto-generated CRITICAL/WARNING/INFO alerts for machine failures, at-risk orders, low stock, and bottlenecks.

### 7. Real-Time Shop-Floor Observability
- **Dynamic Gantt Chart**: Color-coded operations by status (On-Time, Reassigned, At Risk, Late), hatched maintenance window overlays, and rich hover inspection cards.
- **Factory Explorer**: Interactive machine station cards displaying live status (RUNNING, STOPPED, MAINT), real-time utilization, and 1-click failure simulation.
- **Before-vs-After Comparison**: Side-by-side KPI deltas highlighting impact on Makespan, Tardiness, Energy Consumption, and Resilience.
- **Explainable AI Decision Reports**: Audit summaries detailing exactly which jobs were rerouted and why.

---

## Technologies Used

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | Python 3.10+ | Core runtime |
| **API Server** | FastAPI 0.121 + Uvicorn | REST API and static file serving |
| **Data Validation** | Pydantic v2 | Request/response schema validation |
| **Optimization** | Custom Multi-Objective Genetic Algorithm | Schedule optimization |
| **Data Ingestion** | pandas + openpyxl | Excel parsing and data manipulation |
| **Numerical** | NumPy | Array operations and fitness computation |
| **Visualization** | Matplotlib | Gantt chart generation (server-side) |
| **HTTP Client** | httpx | Internal service calls |
| **Frontend** | Vanilla HTML5 + CSS3 + JavaScript (ES6+) | UI -- no framework dependencies |
| **Animation** | GSAP ScrollTrigger + HTML5 Canvas | Scroll-driven machine assembly animation |
| **Testing** | pytest | Automated test suite (73 tests) |

---

## AI Tools and Models

FlowForge AI integrates AI at multiple levels:

### Claude 3.5 Sonnet -- Operations Copilot

| Attribute | Detail |
|---|---|
| **Provider** | Anthropic |
| **Model** | `claude-3-5-sonnet-20241022` |
| **API Key** | `ANTHROPIC_API_KEY` (optional) |
| **Role** | Engineering reasoning layer over structured factory state |
| **Input** | Natural-language operator question + full factory state JSON |
| **Output** | Structured JSON: `answer`, `metrics`, `affected_entities`, `recommended_action` |
| **Fallback** | High-precision deterministic rule-based engine (no API key required) |

**Design principle**: The Copilot *explains and reasons*; it never mutates schedules. The Genetic Algorithm optimizer is always the deterministic decision-maker for scheduling.

**Supported question types** (handled by both Claude and the deterministic fallback):
- Bottleneck identification ("Which station is the bottleneck?")
- Production risk analysis ("Why is production at risk?")
- Job rerouting explanations ("Why was J7 moved to M5?")
- Machine status queries ("What is the status of M3?")
- Energy consumption analysis ("What is our current energy consumption?")
- Inventory and material alerts ("Are there any inventory shortages?")

### Optional AI Integration Keys
The following additional LLM keys are supported via `.env` for future integrations:
```
OPENAI_API_KEY=
GEMINI_API_KEY=
```

> **Note**: FlowForge AI is fully functional without any AI API key. All scheduling, disruption handling, and resilience scoring run on pure algorithmic backends. The Copilot gracefully degrades to deterministic reasoning.

---

## Project Structure

```
FlowForge-AI/
+-- agents/
|   +-- copilot/
|   |   +-- __init__.py
|   |   +-- provider.py         # AI Operations Copilot (Claude 3.5 Sonnet + deterministic fallback)
|   +-- disruption/
|   |   +-- engine.py           # Autonomous Disruption Engine and event loop
|   |   +-- types.py            # Disruption event data structures
|   +-- erp/
|   |   +-- engine.py           # ERP-lite Coordinator (orders, inventory, maintenance, capacity)
|   |   +-- models.py           # ProductionOrder, InventoryItem, MaintenanceRecord models
|   +-- factory/
|   |   +-- excel_parser.py     # Smart Excel parser with fuzzy synonym matching
|   |   +-- json_parser.py      # JSON Job Shop instance and maintenance parser
|   |   +-- job.py              # Job model and operations representation
|   |   +-- machine.py          # Machine model and failure simulation
|   |   +-- state.py            # Central FactoryState tracking
|   +-- resilience/
|   |   +-- metrics.py          # Makespan, tardiness, utilization and energy metrics
|   |   +-- score.py            # Multi-dimensional resilience index (0-100)
|   +-- ga_optimizer.py         # Multi-objective Genetic Algorithm optimizer
|   +-- job_intake.py           # Job intake and normalization layer
|   +-- machine_sim.py          # Machine lifecycle simulator
|   +-- scheduler.py            # Precedence and downtime-aware schedulers (GA, SPT, EDD)
|   +-- supervisor.py           # Factory coordination supervisor
|
+-- deployment/
|   +-- app.py                  # FastAPI server, REST routes and static frame streaming
|
+-- evaluation/
|   +-- evaluator.py            # Schedule quality evaluator and benchmark scoring
|
+-- frontend/
|   +-- index.html              # Apple-grade editorial dashboard markup
|   +-- styles.css              # Custom light industrial theme and canvas styles
|   +-- app.js                  # Frontend controller, canvas animator and Gantt renderer
|   +-- assets/machines/        # Machine hardware reference imagery
|
+-- memory/
|   +-- memory_bank.py          # Factory memory bank for state persistence
|
+-- tools/
|   +-- csv_tool.py             # CSV export utility
|   +-- gantt.py                # Gantt chart rendering tool
|
+-- scripts/
|   +-- generate_template.py    # Excel production schedule template generator
|   +-- remove_watermark.py     # Animation frame preprocessing utility
|   +-- security_check.py       # API key and environment security scanner
|   +-- show_gantt.py           # Local Gantt chart preview script
|   +-- smoke_test.py           # End-to-end smoke test runner
|
+-- tests/
|   +-- test_foundation.py      # Factory, GA, resilience and disruption test suite
|   +-- test_excel_parser.py    # Excel workbook ingestion and fuzzy matching tests
|   +-- test_json_parser.py     # JSON parser and maintenance window tests
|
+-- examples/
|   +-- factory_data_template.xlsx  # Production Excel template
|   +-- job_shop_sample.json        # Sample JSON job shop problem instance
|
+-- data/                       # Runtime data directory
+-- Animation-jpg/              # Source animation frames (pre-processed)
+-- Sample DATA - 1.xlsx        # Sample production dataset 1
+-- Sample DATA - 2.xlsx        # Sample production dataset 2
+-- Sample DATA - 3.xlsx        # Sample production dataset 3
+-- .env.example                # Environment variable template
+-- .gitignore
+-- requirements.txt            # Python dependencies
+-- pytest.ini                  # pytest configuration
+-- DESIGN.md                   # UI/UX design specification
+-- PRD.md                      # Product Requirements Document
+-- LICENSE                     # MIT License
```

---

## Supported Data Formats

FlowForge AI supports direct file upload via drag-and-drop or file picker:

### 1. JSON Job Shop Specification (`.json`)
Supports custom and benchmark JSSP instances with planned maintenance periods:
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
1. **Multi-Sheet Workbook**: A `Jobs` sheet (Job ID, Processing Time, Deadline, Priority, Machine) and an optional `Machines` sheet (Machine ID, Power kW, Idle Power kW).
2. **Single-Sheet Table**: Any flat production schedule table. FlowForge auto-maps ambiguous column headers using fuzzy synonym matching (e.g., `Order #` to `job_id`, `Duration` to `processing_time`).

Three sample datasets are included in the project root (`Sample DATA - 1.xlsx`, `Sample DATA - 2.xlsx`, `Sample DATA - 3.xlsx`).

---

## Setup and Installation

### Prerequisites
- Python **3.10** or higher
- `pip` and virtual environment tool
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/ershehzan/FlowForge-AI.git
cd FlowForge-AI
```

### 2. Create and Activate a Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API keys (all optional -- see Environment Configuration below)
```

### 5. Run the Automated Test Suite
```bash
pytest
```
All 73 automated tests should pass across factory models, Genetic Algorithm correctness, disruption handling, Excel parsing, and JSON scheduling.

### 6. Launch the Server
```bash
uvicorn deployment.app:app --reload --port 8000
```

Open your browser:
- **Interactive UI**: http://127.0.0.1:8000
- **Swagger API Docs**: http://127.0.0.1:8000/docs

---

## Environment Configuration

Copy `.env.example` to `.env` and configure the following variables:

```env
# Application Server Settings
HOST=127.0.0.1
PORT=8000
ENVIRONMENT=development   # development | production

# AI Copilot -- Optional (system works without this key)
ANTHROPIC_API_KEY=sk-ant-...

# Future LLM integrations -- Optional
OPENAI_API_KEY=
GEMINI_API_KEY=

# Optional API Base URL (leave empty for same-origin requests)
API_BASE_URL=
```

> **No API keys are required** for full scheduling and disruption-handling functionality. API keys only enable the Claude-powered Copilot; without them, the system automatically uses the built-in deterministic reasoning engine.

---

## Usage

### Loading Factory Data
1. Navigate to the **Factory Data** section on the dashboard.
2. Drag-and-drop or select a `.xlsx`, `.xls`, or `.json` file.
3. Click **Run FlowForge Optimization** to compute the optimal schedule.
4. Alternatively, click **Load Sample JSON** to use the built-in JSSP benchmark.

### Simulating Disruptions
Use the **Scenarios** panel or the **Factory Explorer** machine cards to:
- **Fail a machine** -- Click "Fail M3" or toggle any machine card.
- **Inject a rush order** -- Click "Urgent Job" to insert priority job `J99`.
- **Shift a deadline** -- Trigger a deadline compression on job `J7`.
- **Recover a machine** -- Click "Recover" to bring a station back online.

### Querying the AI Copilot
Type engineering questions into the **Copilot** panel, for example:
- "Which station is the current bottleneck?"
- "Why was J7 reassigned to M5?"
- "What is our current energy consumption?"
- "Are there any inventory shortages?"

### Resetting the Factory
Click the **DISRUPTED** status badge in the top-right corner or the **Reset Factory** button to restore all machines to OPERATIONAL state.

---

## REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Serves the main FlowForge editorial web application |
| `/frames/` | `GET` | Lists and streams frame images for canvas scroll animation |
| `/frames/manifest.json` | `GET` | Auto-detects total available frame count for the animation engine |
| `/factory/initialize` | `POST` | Re-initializes factory state and computes baseline schedule |
| `/factory/state` | `GET` | Retrieves real-time factory state, machine statuses, and schedules |
| `/factory/upload` | `POST` | Ingests `.xlsx`, `.xls`, or `.json` files, optimizes schedule and returns metrics |
| `/factory/reset` | `POST` | Resets factory floor to pristine baseline operational state |
| `/disruptions` | `POST` | Injects disruption events and triggers autonomous recovery |
| `/metrics` | `GET` | Returns current schedule metrics (makespan, tardiness, energy, utilization) |
| `/resilience` | `GET` | Computes multi-dimensional factory resilience index (0-100) |
| `/erp` | `GET` | Returns full ERP-lite state (orders, inventory, maintenance, capacity, alerts) |
| `/copilot` | `POST` | Queries the AI Operations Copilot with a natural-language question |

### Disruption Event Types (`POST /disruptions`)
```json
{
  "event_type": "machine_failure",
  "machine_id": "M3",
  "job_id": "J99",
  "new_deadline": 80
}
```

Supported `event_type` values: `machine_failure`, `urgent_job`, `deadline_change`, `machine_recovery`

---

## Running Tests

FlowForge AI has a comprehensive automated test suite using **pytest**.

```bash
# Run all 73 tests
pytest

# Run with verbose output
pytest -v

# Run a specific test module
pytest tests/test_foundation.py
pytest tests/test_excel_parser.py
pytest tests/test_json_parser.py
```

### Test Coverage

| Module | Covers |
|---|---|
| `test_foundation.py` | Factory model, GA optimizer, resilience scoring, disruption engine |
| `test_excel_parser.py` | Workbook parsing, fuzzy header matching, single-sheet conversion |
| `test_json_parser.py` | JSSP parsing, maintenance windows, multi-operation precedence |

---

## Scripts and Utilities

Helper scripts are located in the `scripts/` directory:

| Script | Purpose |
|---|---|
| `generate_template.py` | Generates a blank Excel production schedule template |
| `show_gantt.py` | Renders a local Gantt chart preview from current factory state |
| `smoke_test.py` | End-to-end smoke test: starts server and validates all major API endpoints |
| `security_check.py` | Scans environment and codebase for exposed API keys or unsafe configurations |
| `remove_watermark.py` | Preprocesses animation frame images for clean canvas playback |

```bash
# Generate a fresh Excel template
python scripts/generate_template.py

# Run end-to-end smoke tests
python scripts/smoke_test.py
```

---

## Disruption and Resilience Walkthrough

Try the following interactive flows directly from the dashboard:

1. **Machine Breakdown**:
   - Scroll to **Scenarios** and click **Fail M3** (or click the M3 card in **Factory Explorer**).
   - The status badge switches to DISRUPTED.
   - The engine automatically reroutes tasks away from M3 and computes a recovery schedule.

2. **Rush Order Injection**:
   - Click **Urgent Job** to introduce priority order `J99` with a tight delivery window.
   - Observe the Gantt chart slotting `J99` ahead of lower-priority jobs while preserving deadlines.

3. **Maintenance and Precedence (JSON)**:
   - In **Factory Data**, click **Load Sample JSON**, then click **Run FlowForge Optimization**.
   - Notice hatched maintenance blocks (Maint 7-12m) on `M0` and strictly sequenced operations across M0 -> M1 -> M2.

4. **1-Click Reset**:
   - Click the **DISRUPTED** badge or **Reset Factory** to restore all machines to OPERATIONAL.

---

## Authors and License

**Shehzan Khan** | **Shorya Agrawal**

*FlowForge AI -- Autonomous Production Resilience & Optimization*

Released under the **[MIT License](./LICENSE)**.

---

> Built by engineers who believe the factory should always adapt -- not just survive.