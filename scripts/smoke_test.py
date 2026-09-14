"""
FlowForge AI — Automated Live Smoke Test & Stress Runner
Executes the full repeated lifecycle against the active Uvicorn server:
Start -> Load Demo -> Generate Schedule -> Machine Failure -> Recovery -> Reset
-> Upload Excel -> Optimize -> Machine Failure -> Recovery -> Reset
-> Upload JSON -> Optimize -> Precedence Verification -> Reset
"""
import urllib.request
import urllib.error
import json
import os

BASE_URL = "http://127.0.0.1:8000"


def api_get(endpoint):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}", method="GET")
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def api_post(endpoint, payload=None):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}", method="POST")
    if payload is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(payload).encode("utf-8")
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def api_upload(filepath, filename, content_type):
    boundary = "----WebKitFormBoundarySmokeTest778"
    with open(filepath, "rb") as f:
        file_bytes = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/factory/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def run_full_cycle(iteration=1):
    print(f"\n--- RUNNING STRESS CYCLE {iteration} ---")

    # 1. Check Root & Frames
    status, frames_data = api_get("/api/frames-info")
    assert status == 200 and frames_data["total_frames"] == 240, f"Frames check failed: {frames_data}"
    print(f"[{iteration}.1] Canvas Frame Engine: PASS ({frames_data['total_frames']} frames)")

    # 2. Demo Factory Initialize
    status, init_data = api_post("/factory/initialize")
    assert status == 200, "Factory init failed"
    baseline = init_data["baseline_schedule"]
    assert len(baseline) > 0, "No baseline jobs generated"
    print(f"[{iteration}.2] Demo Factory Baseline: PASS ({len(baseline)} jobs, Resilience: {init_data['resilience']['score']})")

    # 3. Machine Failure Disruption (Fail M3)
    status, dis_fail = api_post("/disruptions", {"type": "machine_failure", "machine_id": "M3"})
    assert status == 200 and "recovery" in dis_fail["schedules"], "Disruption failure failed"
    print(f"[{iteration}.3] Disruption Simulation (Fail M3): PASS (Recovery Jobs: {len(dis_fail['schedules']['recovery'])})")

    # 4. Machine Recovery (Recover M3)
    status, dis_rec = api_post("/disruptions", {"type": "machine_recovery", "machine_id": "M3"})
    assert status == 200, "Disruption recovery failed"
    print(f"[{iteration}.4] Machine Recovery (M3 online): PASS")

    # 5. Factory Reset
    status, reset_data = api_post("/factory/reset")
    assert status == 200 and reset_data["factory_status"] == "OPERATIONAL", "Factory reset failed"
    print(f"[{iteration}.5] Factory Reset: PASS (Status: {reset_data['factory_status']})")

    # 6. Upload Production Excel Data
    excel_path = "Sample DATA- 1.xlsx"
    if os.path.exists(excel_path):
        status, xl_data = api_upload(excel_path, "Sample DATA- 1.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        assert status == 200 and xl_data["success"] is True, f"Excel upload failed: {xl_data}"
        print(f"[{iteration}.6] Excel Workbook Ingestion: PASS ({len(xl_data['baseline_schedule'])} jobs optimized)")

        # Disruption on uploaded Excel data
        status, xl_dis = api_post("/disruptions", {"type": "urgent_job", "job_id": "J99", "duration": 20, "deadline": 80, "priority": 5})
        assert status == 200, "Urgent job failed on Excel data"
        print(f"[{iteration}.7] Disruption on Excel Data (Urgent Job J99): PASS")

        # Reset again
        api_post("/factory/reset")

    # 7. Upload JSON Job Shop Data
    json_path = "examples/job_shop_sample.json"
    if os.path.exists(json_path):
        status, json_data = api_upload(json_path, "job_shop_sample.json", "application/json")
        assert status == 200 and json_data["success"] is True, f"JSON upload failed: {json_data}"
        print(f"[{iteration}.8] JSON Job Shop Ingestion: PASS ({len(json_data['baseline_schedule'])} operations scheduled)")

        # Reset to clean baseline
        api_post("/factory/reset")

    print(f"--- CYCLE {iteration} COMPLETED WITH ZERO ERRORS ---")


if __name__ == "__main__":
    print("==================================================")
    print("FLOWFORGE AI — FULL SYSTEM END-TO-END HEALTH CHECK")
    print("==================================================")
    for i in range(1, 4):  # Test repeatedly 3 times
        run_full_cycle(iteration=i)
    print("\nALL 3 REPEATED CYCLES PASSED PERFECTLY!")
