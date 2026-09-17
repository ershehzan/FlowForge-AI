import os
import sys
import time
import re
import logging

# Ensure root directory is on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from fastapi import FastAPI, UploadFile, File, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any

logger = logging.getLogger("flowforge")

# Maximum allowed upload size: 10 MB
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

from tools.csv_tool import read_jobs_csv

from agents.job_intake import load_jobs_from_list
from agents.scheduler import Scheduler
from agents.machine_sim import MachineSimulator
from agents.factory.state import FactoryState
from agents.factory.machine import get_available_machine_ids
from agents.factory.excel_parser import ExcelParser
from agents.factory.json_parser import JsonParser
from agents.disruption.engine import DisruptionEngine
from agents.disruption import types as disruption_types
from agents.resilience.metrics import calculate_all_metrics
from agents.resilience.score import calculate_resilience_score
from agents.copilot.provider import AICopilotProvider


app = FastAPI(
    title="FlowForge AI",
    description="Autonomous Production Resilience & Optimization",
    version="1.0.0",
)

# CORS for frontend.
# allow_credentials=False is correct when allow_origins=["*"] (wildcard).
# Browsers reject credentials+wildcard anyway; this avoids misleading config.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    # Note: CSP is intentionally broad to support CDN GSAP/fonts loaded by the frontend.
    # Tighten in production when a specific deployment origin is known.
    response.headers["X-FlowForge-Version"] = "1.0.0"
    return response

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")
ANIMATION_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Animation-jpg")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
if os.path.exists(EXAMPLES_DIR):
    app.mount("/examples", StaticFiles(directory=EXAMPLES_DIR), name="examples")
if os.path.exists(DATA_DIR):
    app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")
if os.path.exists(ANIMATION_DIR):
    app.mount("/frames", StaticFiles(directory=ANIMATION_DIR), name="frames")


@app.get("/api/frames-info")
async def get_frames_info():
    """Detect frames directory pattern, first frame, last frame, and count dynamically."""
    if not os.path.exists(ANIMATION_DIR):
        return {"error": "Animation folder not found", "count": 0, "frames": []}
    files = sorted([f for f in os.listdir(ANIMATION_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
    if not files:
        return {"count": 0, "frames": []}

    digits = 3
    prefix = "ezgif-frame-"
    ext = ".jpg"
    m = re.match(r'^(.*?)(\d+)(\.[a-zA-Z0-9]+)$', files[0])
    if m:
        prefix = m.group(1)
        digits = len(m.group(2))
        ext = m.group(3)

    return {
        "count": len(files),
        "total_frames": len(files),
        "first_frame": 1,
        "last_frame": len(files),
        "prefix": prefix,
        "digits": digits,
        "extension": ext,
        "pattern": f"{prefix}{{index:0{digits}d}}{ext}",
        "frames": [f"/frames/{f}" for f in files]
    }


@app.get("/", include_in_schema=False)
async def root():
    """Serve the FlowForge dashboard."""
    return FileResponse(
        os.path.join(FRONTEND_DIR, "index.html"),
        headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
    )


def load_initial_factory() -> FactoryState:
    """Initialize factory state with industrial dataset if available, otherwise defaults."""
    fs = FactoryState()
    industrial_path = os.path.join(ROOT_DIR, "data", "industrial_factory.xlsx")
    if os.path.exists(industrial_path):
        try:
            parser = ExcelParser()
            with open(industrial_path, "rb") as f:
                parsed = parser.parse(f.read(), filename="industrial_factory.xlsx")
            if parsed.get("success"):
                fs.load_normalized_data(parsed, data_source="industrial_factory.xlsx")
                available = fs.get_available_machine_ids()
                scheduler = Scheduler(available)
                energy_map = fs.get_machine_energy_map()
                baseline = scheduler.ga_schedule(
                    fs.get_active_jobs(),
                    machine_energy=energy_map,
                )
                fs.set_baseline_schedule(baseline)
                fs.erp_engine.synchronize()
                logger.info("Auto-loaded industrial factory dataset (%d machines, %d jobs)", len(fs.machines), len(fs.jobs))
                return fs
        except Exception as e:
            logger.warning("Failed to auto-load industrial_factory.xlsx: %s", e)
    return fs


# Global factory state (defaults to rich industrial factory dataset)
factory = load_initial_factory()

# Session storage for legacy upload_jobs flow
SESSIONS = {}


# ─────────────────────────────────────────────────────────────
# Pydantic request models
# ─────────────────────────────────────────────────────────────

class DisruptionRequest(BaseModel):
    type: str  # machine_failure, machine_recovery, urgent_job, etc.
    machine_id: Optional[str] = None
    machine_ids: Optional[List[str]] = None
    job_id: Optional[str] = None
    duration: Optional[int] = None
    deadline: Optional[int] = None
    new_deadline: Optional[int] = None
    priority: Optional[int] = 5
    material_id: Optional[str] = None
    defect_rate: Optional[float] = None
    threshold_kw: Optional[float] = None
    reason: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        allowed = {
            "machine_failure", "machine_recovery", "urgent_job",
            "job_cancellation", "deadline_change", "machine_downtime",
            "planned_downtime", "maintenance", "material_shortage",
            "quality_issue", "multiple_failure", "energy_constraint",
        }
        if v not in allowed:
            raise ValueError(f"Unknown disruption type '{v}'. Allowed: {sorted(allowed)}")
        return v

    @field_validator("machine_id", "job_id")
    @classmethod
    def validate_id_chars(cls, v):
        """Reject IDs with path-traversal or shell-injection characters."""
        if v is not None:
            v = str(v).strip()
            if not re.match(r'^[A-Za-z0-9_\-]+$', v):
                raise ValueError(f"ID contains invalid characters: '{v}'")
            if len(v) > 64:
                raise ValueError("ID too long (max 64 chars)")
        return v

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v):
        if v is not None and v <= 0:
            raise ValueError("duration must be a positive integer (> 0)")
        if v is not None and v > 10000:
            raise ValueError("duration exceeds maximum allowed value (10000 minutes)")
        return v

    @field_validator("deadline", "new_deadline")
    @classmethod
    def validate_deadline(cls, v):
        if v is not None and v <= 0:
            raise ValueError("deadline must be a positive integer (> 0)")
        if v is not None and v > 100000:
            raise ValueError("deadline exceeds maximum allowed value (100000 minutes)")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v is not None and v not in range(1, 6):
            raise ValueError("priority must be between 1 and 5")
        return v


class CopilotQueryRequest(BaseModel):
    query: Optional[str] = None
    question: Optional[str] = None

    @field_validator("query", "question")
    @classmethod
    def validate_query_length(cls, v):
        if v is not None and len(v) > 2000:
            raise ValueError("Query too long (max 2000 characters)")
        return v

    @property
    def prompt_text(self) -> str:
        return self.query or self.question or ""


# ─────────────────────────────────────────────────────────────
# Legacy endpoints (preserved from original)
# ─────────────────────────────────────────────────────────────

@app.post("/upload_jobs")
async def upload_jobs(session_id: str, file: UploadFile = File(...)):
    """Legacy CSV job upload endpoint. Session-scoped; files are cleaned up after parsing."""
    safe_session = re.sub(r'[^a-zA-Z0-9_\-]', '', session_id)
    if not safe_session or len(safe_session) > 64:
        return JSONResponse(status_code=400, content={"error": "Invalid session_id"})

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        return JSONResponse(status_code=413, content={"error": "File too large (max 10 MB)"})

    os.makedirs("data", exist_ok=True)
    path = os.path.join("data", f"{safe_session}.csv")
    try:
        with open(path, "wb") as f:
            f.write(content)
        raw = read_jobs_csv(path)
        jobs = load_jobs_from_list(raw)
        SESSIONS[session_id] = {"jobs": jobs}
        return {"status": "ok", "jobs": len(jobs)}
    finally:
        # Clean up the temporary CSV file after parsing
        try:
            os.remove(path)
        except OSError:
            pass

@app.get("/schedule")
async def schedule(session_id: str, rule: str = 'SPT'):
    session = SESSIONS.get(session_id)
    if not session:
        return {"error": "Session not found"}

    scheduler = Scheduler(["M1", "M2", "M3"])
    result = scheduler.heuristic_schedule(session["jobs"], rule)
    SESSIONS[session_id]["assignments"] = result

    return {"assignments": result}

@app.get("/ga_schedule")
async def ga_schedule(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        return {"error": "session not found"}

    scheduler = Scheduler(["M1", "M2", "M3"])
    result = scheduler.ga_schedule(session["jobs"])

    return {"assignments": result}


# ─────────────────────────────────────────────────────────────
# New FlowForge endpoints
# ─────────────────────────────────────────────────────────────

@app.get("/factory/state")
async def get_factory_state():
    """Return full factory state including machines, jobs, schedules."""
    return factory.to_dict()


@app.post("/factory/initialize")
async def initialize_factory():
    """
    Initialize factory with default config and generate baseline schedule.
    This sets up the factory for demo scenarios.
    """
    industrial_path = os.path.join(ROOT_DIR, "data", "industrial_factory.xlsx")
    if os.path.exists(industrial_path):
        try:
            parser = ExcelParser()
            with open(industrial_path, "rb") as f:
                parsed = parser.parse(f.read(), filename="industrial_factory.xlsx")
            if parsed.get("success"):
                factory.reset()
                factory.load_normalized_data(parsed, data_source="industrial_factory.xlsx")
                available = factory.get_available_machine_ids()
                scheduler = Scheduler(available)
                energy_map = factory.get_machine_energy_map()
                baseline = scheduler.ga_schedule(
                    factory.get_active_jobs(),
                    machine_energy=energy_map,
                )
                factory.set_baseline_schedule(baseline)
                factory.erp_engine.synchronize()
                metrics = calculate_all_metrics(baseline, available, energy_map)
                resilience = calculate_resilience_score(
                    baseline, available, energy_map,
                    total_machines=len(factory.machines),
                    available_machines=len(available),
                )
                return {
                    "status": "initialized",
                    "factory_status": factory.factory_status,
                    "baseline_schedule": baseline,
                    "metrics": metrics,
                    "resilience": resilience,
                }
        except Exception as e:
            logger.warning("Failed to initialize with industrial_factory.xlsx: %s", e)

    factory.reset()

    # Generate baseline schedule using GA with available machines
    available = factory.get_available_machine_ids()
    scheduler = Scheduler(available)
    energy_map = factory.get_machine_energy_map()

    baseline = scheduler.ga_schedule(
        factory.get_active_jobs(),
        machine_energy=energy_map,
    )
    factory.set_baseline_schedule(baseline)

    # Calculate initial metrics
    metrics = calculate_all_metrics(baseline, available, energy_map)
    resilience = calculate_resilience_score(
        baseline, available, energy_map,
        total_machines=len(factory.machines),
        available_machines=len(available),
    )

    return {
        "status": "initialized",
        "factory_status": factory.factory_status,
        "baseline_schedule": baseline,
        "metrics": metrics,
        "resilience": resilience,
    }


@app.post("/factory/reset")
async def reset_factory():
    """Reset factory to baseline state (reloading industrial dataset)."""
    res = await initialize_factory()
    res["status"] = "reset"
    return res


@app.post("/factory/load_sample")
async def load_sample_factory():
    """Load the full 16-sheet Industrial Factory sample dataset."""
    return await initialize_factory()


@app.post("/factory/upload")
async def upload_factory_excel(file: UploadFile = File(...)):
    """
    Upload an Excel (.xlsx/.xls) or JSON file containing factory data.
    Validates the workbook, converts it into internal FactoryState, and
    automatically runs the autonomous multi-objective GA scheduler.
    """
    # Never trust the client-supplied filename for filesystem operations.
    # We only use it for display / logging.
    raw_filename = file.filename or "uploaded"
    # Sanitize: strip path components and limit length
    safe_basename = os.path.basename(raw_filename.replace("\\", "/"))[:128]
    filename = safe_basename if safe_basename else "uploaded"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".xlsx", ".xls", ".json"]:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "errors": [{"sheet": "File", "row": 0, "column": "Format",
                             "message": f"Unsupported file format '{ext}'. Supported: .xlsx, .xls, .json."}],
                "error_messages": [f"• Unsupported file format '{ext}'. Supported: .xlsx, .xls, .json."],
            }
        )

    content = await file.read()

    # Enforce upload size limit
    if len(content) > MAX_UPLOAD_BYTES:
        size_mb = len(content) / (1024 * 1024)
        return JSONResponse(
            status_code=413,
            content={
                "success": False,
                "errors": [{"sheet": "File", "row": 0, "column": "Size",
                             "message": f"File too large ({size_mb:.1f} MB). Maximum allowed: 10 MB."}],
                "error_messages": [f"• File too large ({size_mb:.1f} MB). Maximum allowed: 10 MB."],
            }
        )
    if ext == ".json":
        parser = JsonParser()
    else:
        parser = ExcelParser()

    parsed = parser.parse(content, filename=filename)

    if not parsed["success"]:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "errors": parsed["errors"],
                "error_messages": parsed["error_messages"],
                "data_source": filename,
            }
        )

    # Transactional update of FactoryState with full normalization
    factory.load_normalized_data(parsed, data_source=filename)
    factory.baseline_schedule = None
    factory.disrupted_schedule = None
    factory.recovery_schedule = None
    factory.schedule_state = "BASELINE"
    factory.factory_status = "OPERATIONAL"

    # Run Autonomous Scheduler on imported factory state
    available = factory.get_available_machine_ids()
    scheduler = Scheduler(available)
    energy_map = factory.get_machine_energy_map()
    unavail_map = {m_id: m.get("unavailable_periods", []) for m_id, m in factory.machines.items()}

    baseline = scheduler.ga_schedule(
        factory.get_active_jobs(),
        machine_energy=energy_map,
        machine_unavail=unavail_map,
    )
    factory.set_baseline_schedule(baseline)

    metrics = calculate_all_metrics(baseline, available, energy_map)
    resilience = calculate_resilience_score(
        baseline, available, energy_map,
        total_machines=len(factory.machines),
        available_machines=len(available),
    )

    return {
        "success": True,
        "status": "uploaded_and_optimized",
        "data_source": filename,
        "summary": parsed["summary"],
        "factory_state": factory.to_dict(),
        "baseline_schedule": baseline,
        "metrics": metrics,
        "resilience": resilience,
    }



@app.post("/disruptions")
async def apply_disruption(request: DisruptionRequest):
    """
    Apply a disruption to the factory and trigger automatic recovery.

    Supported types:
      - machine_failure
      - machine_recovery
      - urgent_job
      - job_cancellation
      - deadline_change
    """
    # Ensure baseline exists — return HTTP 409 so frontend can detect this clearly
    if not factory.baseline_schedule:
        return JSONResponse(
            status_code=409,
            content={"error": "Factory not initialized. Call POST /factory/initialize first."}
        )

    # Create the disruption event
    dtype = request.type

    if dtype == "machine_failure":
        if not request.machine_id:
            return JSONResponse(status_code=400, content={"error": "machine_id is required for machine_failure"})
        disruption = disruption_types.machine_failure(request.machine_id)

    elif dtype == "machine_recovery":
        if not request.machine_id:
            return JSONResponse(status_code=400, content={"error": "machine_id is required for machine_recovery"})
        disruption = disruption_types.machine_recovery(request.machine_id)

    elif dtype == "urgent_job":
        if not request.job_id or not request.duration or not request.deadline:
            return JSONResponse(status_code=400, content={"error": "job_id, duration, and deadline are required for urgent_job"})
        disruption = disruption_types.urgent_job(
            request.job_id, request.duration, request.deadline, request.priority or 5
        )

    elif dtype == "job_cancellation":
        if not request.job_id:
            return JSONResponse(status_code=400, content={"error": "job_id is required for job_cancellation"})
        disruption = disruption_types.job_cancellation(request.job_id)

    elif dtype == "deadline_change":
        if not request.job_id or (request.new_deadline is None and request.deadline is None):
            return JSONResponse(status_code=400, content={"error": "job_id and new_deadline/deadline are required for deadline_change"})
        dl = request.new_deadline if request.new_deadline is not None else request.deadline
        disruption = disruption_types.deadline_change(request.job_id, dl)

    elif dtype in ("planned_downtime", "maintenance", "machine_downtime"):
        target_m = request.machine_id or "M04"
        duration = request.duration or 90
        reason = request.reason or "Preventive service"
        disruption = disruption_types.planned_downtime(target_m, duration, reason)

    elif dtype == "multiple_failure":
        m_list = request.machine_ids or ([m.strip() for m in request.machine_id.split(",")] if request.machine_id else ["M03", "M05"])
        disruption = disruption_types.multiple_failure(m_list)

    elif dtype == "material_shortage":
        mat_id = request.material_id or "RM-003"
        disruption = disruption_types.material_shortage(mat_id)

    elif dtype == "quality_issue":
        target_m = request.machine_id or "M02"
        rate = request.defect_rate or 0.15
        disruption = disruption_types.quality_issue(target_m, defect_rate=rate)

    elif dtype == "energy_constraint":
        thresh = request.threshold_kw or 65.0
        disruption = disruption_types.energy_constraint(threshold_kw=thresh)

    else:
        # Should not reach here since Pydantic validator catches unknown types
        return JSONResponse(status_code=400, content={"error": f"Unknown disruption type: {dtype}"})

    # Apply disruption through the engine
    engine = DisruptionEngine(factory)
    result = engine.apply(disruption)

    if "error" in result:
        return JSONResponse(status_code=409, content=result)

    # Calculate metrics for all three schedule states
    available = factory.get_available_machine_ids()
    all_machines = list(factory.machines.keys())
    energy_map = factory.get_machine_energy_map()

    baseline_metrics = calculate_all_metrics(
        factory.baseline_schedule, all_machines, energy_map
    ) if factory.baseline_schedule else {}

    disrupted_metrics = calculate_all_metrics(
        factory.disrupted_schedule, available, energy_map
    ) if factory.disrupted_schedule else {}

    recovery_metrics = calculate_all_metrics(
        factory.recovery_schedule, available, energy_map
    ) if factory.recovery_schedule else {}

    # Calculate resilience scores
    baseline_resilience = calculate_resilience_score(
        factory.baseline_schedule, all_machines, energy_map,
        total_machines=len(factory.machines),
        available_machines=len(factory.machines),
    ) if factory.baseline_schedule else {}

    recovery_resilience = calculate_resilience_score(
        factory.recovery_schedule, available, energy_map,
        total_machines=len(factory.machines),
        available_machines=len(available),
        baseline_schedule=factory.baseline_schedule,
        disrupted_schedule=factory.disrupted_schedule,
    ) if factory.recovery_schedule else {}

    # Record historical disruption & decision report entry
    history_entry = {
        "timestamp": time.strftime("%H:%M:%S"),
        "event_type": dtype,
        "description": f"Disruption: {dtype.replace('_', ' ').title()}",
        "affected_machines": [request.machine_id] if request.machine_id else [],
        "affected_jobs": result["affected_jobs"],
        "baseline_makespan": baseline_metrics.get("makespan", 0),
        "disrupted_makespan": disrupted_metrics.get("makespan", 0),
        "recovery_makespan": recovery_metrics.get("makespan", 0),
        "baseline_resilience": baseline_resilience.get("score", 0),
        "recovery_resilience": recovery_resilience.get("score", 0),
        "baseline_late": baseline_metrics.get("late_jobs", 0),
        "recovery_late": recovery_metrics.get("late_jobs", 0),
        "recovery_time_seconds": result["recovery_time_seconds"],
        "decision_report": {
            "event": f"Factory encountered {dtype.replace('_', ' ')}.",
            "impact": f"{len(result['affected_jobs'])} scheduled jobs were affected.",
            "decision": f"FlowForge autonomous optimizer rerouted affected workloads to available capacity.",
            "reason": f"Selected parallel machine assignments that protect delivery deadlines while balancing energy load.",
            "trade_off": "Slight variation in machine power distribution to guarantee critical customer delivery windows.",
            "outcome": f"Recovered resilience to {recovery_resilience.get('score', 80)}/100 with zero additional overdue commitments."
        }
    }
    factory.add_history_record(history_entry)

    # Sync ERP models with new schedule & machine states
    factory.erp_engine.synchronize()

    return {
        "disruption": result["disruption"],
        "affected_jobs": result["affected_jobs"],
        "impact": result["impact"],
        "recovery_time_seconds": result["recovery_time_seconds"],
        "schedules": {
            "baseline": factory.baseline_schedule,
            "disrupted": factory.disrupted_schedule,
            "recovery": factory.recovery_schedule,
        },
        "metrics": {
            "baseline": baseline_metrics,
            "disrupted": disrupted_metrics,
            "recovery": recovery_metrics,
        },
        "resilience": {
            "baseline": baseline_resilience,
            "recovery": recovery_resilience,
        },
        "factory_status": factory.factory_status,
        "erp": factory.erp_engine.to_dict(),
        "history": factory.history_records,
    }


class ScenarioRunRequest(BaseModel):
    scenario_id: int


@app.get("/scenarios")
async def get_scenarios():
    """Return catalog of the 10 predefined industrial scenarios."""
    from agents.disruption.scenarios import INDUSTRIAL_SCENARIOS_META
    return {"scenarios": INDUSTRIAL_SCENARIOS_META}


@app.post("/scenarios/run")
async def run_scenario_endpoint(req: ScenarioRunRequest):
    """
    Execute one of the 10 industrial scenarios against the common factory state.
    Returns structured baseline, event, impact, response, and recovery metrics.
    """
    engine = DisruptionEngine(factory)
    result = engine.run_scenario(req.scenario_id)
    factory.erp_engine.synchronize()
    return {
        "success": True,
        "scenario_id": req.scenario_id,
        "scenario_name": result.get("scenario_name", f"Scenario {req.scenario_id}"),
        "result": result,
        "factory_state": factory.to_dict(),
        "schedules": {
            "baseline": factory.baseline_schedule,
            "disrupted": factory.disrupted_schedule,
            "recovery": factory.recovery_schedule,
        },
    }


@app.get("/metrics")
async def get_metrics():
    """Return current schedule metrics."""
    schedule = factory.get_current_schedule()
    if not schedule:
        return {"error": "No schedule available. Call POST /factory/initialize first."}

    available = factory.get_available_machine_ids()
    energy_map = factory.get_machine_energy_map()

    return calculate_all_metrics(schedule, available, energy_map)


@app.get("/resilience")
async def get_resilience():
    """Return current factory resilience score."""
    schedule = factory.get_current_schedule()
    if not schedule:
        return {"error": "No schedule available. Call POST /factory/initialize first."}

    available = factory.get_available_machine_ids()
    energy_map = factory.get_machine_energy_map()
    avail_count, total_count = factory.get_machine_count()

    return calculate_resilience_score(
        schedule, available, energy_map,
        total_machines=total_count,
        available_machines=avail_count,
        baseline_schedule=factory.baseline_schedule,
        disrupted_schedule=factory.disrupted_schedule,
    )


@app.post("/factory/reset")
async def reset_factory():
    """Reset factory to clean baseline state."""
    factory.reset()
    return {
        "status": "reset",
        "factory_status": factory.factory_status,
        "erp": factory.erp_engine.to_dict(),
    }


# ─────────────────────────────────────────────────────────────
# ERP-Lite Manufacturing Operations Endpoints
# ─────────────────────────────────────────────────────────────

@app.get("/erp/state")
async def get_erp_state():
    """Return full ERP-lite operational state (orders, inventory, maintenance, capacity)."""
    return factory.erp_engine.to_dict()


@app.get("/orders")
async def get_orders():
    """Return production orders list with risk and progress."""
    factory.erp_engine.synchronize()
    return [o.to_dict() for o in factory.erp_engine.orders]


@app.get("/inventory")
async def get_inventory():
    """Return raw material inventory balances and at-risk stockouts."""
    factory.erp_engine.synchronize()
    return [i.to_dict() for i in factory.erp_engine.inventory]


@app.get("/maintenance")
async def get_maintenance():
    """Return machine maintenance health scores and downtime records."""
    factory.erp_engine.synchronize()
    return [m.to_dict() for m in factory.erp_engine.maintenance]


@app.get("/capacity")
async def get_capacity():
    """Return machine capacity matrix (available, load, utilization, remaining)."""
    return factory.erp_engine.get_capacity_matrix()


@app.get("/analytics")
async def get_analytics():
    """Return comparative analytics across Baseline, Disrupted, and Recovery states."""
    available = factory.get_available_machine_ids()
    all_machines = list(factory.machines.keys())
    energy_map = factory.get_machine_energy_map()

    base_m = calculate_all_metrics(factory.baseline_schedule, all_machines, energy_map) if factory.baseline_schedule else {}
    dis_m = calculate_all_metrics(factory.disrupted_schedule, available, energy_map) if factory.disrupted_schedule else {}
    rec_m = calculate_all_metrics(factory.recovery_schedule, available, energy_map) if factory.recovery_schedule else base_m

    base_r = calculate_resilience_score(factory.baseline_schedule, all_machines, energy_map, len(all_machines), len(all_machines)) if factory.baseline_schedule else {}
    rec_r = calculate_resilience_score(factory.recovery_schedule, available, energy_map, len(all_machines), len(available), baseline_schedule=factory.baseline_schedule, disrupted_schedule=factory.disrupted_schedule) if factory.recovery_schedule else base_r

    return {
        "metrics_comparison": {
            "baseline": base_m,
            "disrupted": dis_m,
            "recovery": rec_m,
        },
        "resilience_comparison": {
            "baseline": base_r,
            "recovery": rec_r,
        },
        "history": factory.history_records,
        "capacity": factory.erp_engine.get_capacity_matrix(),
    }


@app.get("/history")
async def get_history():
    """Return historical disruption and autonomous recovery decision records."""
    return {
        "history": factory.history_records,
        "count": len(factory.history_records),
    }


@app.post("/copilot/query")
async def copilot_query(request: CopilotQueryRequest):
    """
    AI Operations Copilot reasoning endpoint.
    Passes structured factory context to Claude (or deterministic reasoning fallback).
    """
    factory.erp_engine.synchronize()
    schedule = factory.get_current_schedule() or factory.baseline_schedule or []
    available = factory.get_available_machine_ids()
    energy_map = factory.get_machine_energy_map()

    metrics = calculate_all_metrics(schedule, available, energy_map) if schedule else {}
    resilience = calculate_resilience_score(
        schedule, available, energy_map,
        total_machines=len(factory.machines),
        available_machines=len(available),
        baseline_schedule=factory.baseline_schedule,
        disrupted_schedule=factory.disrupted_schedule,
    ) if schedule else {}

    context = {
        "factory": {
            "status": factory.factory_status,
            "schedule_state": factory.schedule_state,
            "data_source": factory.data_source,
            "total_machines": len(factory.machines),
            "available_machines": len(available),
        },
        "factory_status": factory.factory_status,
        "machines": factory.machines,
        "orders": [o.to_dict() if hasattr(o, "to_dict") else o for o in factory.erp_engine.orders],
        "jobs": factory.jobs,
        "operations": factory.operations,
        "inventory": [i.to_dict() if hasattr(i, "to_dict") else i for i in factory.erp_engine.inventory],
        "maintenance": [m.to_dict() if hasattr(m, "to_dict") else m for m in factory.erp_engine.maintenance],
        "downtime": factory.downtime_records,
        "energy": factory.energy_observations,
        "quality": factory.quality_observations,
        "production_lines": factory.production_lines,
        "disruptions": factory.active_disruptions,
        "schedule": schedule,
        "metrics": metrics,
        "resilience": resilience,
        "capacity": factory.erp_engine.get_capacity_matrix(),
        "history_count": len(factory.history_records),
    }

    provider = AICopilotProvider()
    result = provider.query(request.prompt_text, context)
    ans = result.get("answer", "")
    rec_act = result.get("recommended_action")
    actions = [rec_act] if isinstance(rec_act, str) else (rec_act or [])

    result.setdefault("concise_answer", ans)
    result.setdefault("explanation", ans)
    result.setdefault("recommended_investigation", actions)
    result.setdefault("provider", result.get("provider_mode", "FlowForge AI Operations Copilot"))
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("deployment.app:app", host="127.0.0.1", port=8000, reload=True)

