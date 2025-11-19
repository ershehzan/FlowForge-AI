from fastapi import FastAPI, UploadFile, File

from tools.csv_tool import read_jobs_csv
from agents.job_intake import load_jobs_from_list
from agents.scheduler import Scheduler
from agents.machine_sim import MachineSimulator

app = FastAPI()

SESSIONS = {}

@app.post("/upload_jobs")
async def upload_jobs(session_id: str, file: UploadFile = File(...)):
    path = f"data/{session_id}.csv"
    with open(path, "wb") as f:
        f.write(await file.read())

    raw = read_jobs_csv(path)
    jobs = load_jobs_from_list(raw)
    SESSIONS[session_id] = {"jobs": jobs}

    return {"status": "ok", "jobs": len(jobs)}

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
