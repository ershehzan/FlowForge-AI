# scripts/smoke_test.py
import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def get(endpoint):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

def post(endpoint, payload=None):
    url = f"{BASE_URL}{endpoint}"
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

def run():
    print("=== FlowForge AI Comprehensive Smoke Test ===")
    
    # 1. Root page
    with urllib.request.urlopen(f"{BASE_URL}/") as resp:
        assert resp.status == 200
        html = resp.read().decode()
        assert "FLOWFORGE" in html
        assert "Command Center" in html
        assert "Production" in html
        assert "Shop Floor" in html
        assert "Inventory" in html
        assert "Maintenance" in html
        assert "Analytics" in html
        assert "AI Copilot" in html
        assert "Scenarios" in html
        assert "History" in html
        print(" [PASS] 1. Root HTML & 9 Navigation modules present")

    # 2. Factory initialize
    status, data = post("/factory/initialize")
    assert status == 200
    assert "baseline_schedule" in data
    print(" [PASS] 2. POST /factory/initialize")

    # 3. Factory state
    status, data = get("/factory/state")
    assert status == 200
    assert "machines" in data
    assert "erp_state" in data
    print(" [PASS] 3. GET /factory/state with erp_state")

    # 4. ERP State
    status, data = get("/erp/state")
    assert status == 200
    assert len(data["orders"]) >= 4
    assert len(data["inventory"]) >= 5
    assert len(data["maintenance"]) == 6
    assert len(data["capacity"]) == 6
    print(" [PASS] 4. GET /erp/state (orders, inventory, maintenance, capacity)")

    # 5. Orders endpoint
    status, data = get("/orders")
    assert status == 200
    assert isinstance(data, list) and len(data) >= 4
    print(f" [PASS] 5. GET /orders ({len(data)} orders returned)")

    # 6. Inventory endpoint
    status, data = get("/inventory")
    assert status == 200
    assert isinstance(data, list) and len(data) >= 5
    print(f" [PASS] 6. GET /inventory ({len(data)} items returned)")

    # 7. Maintenance endpoint
    status, data = get("/maintenance")
    assert status == 200
    assert isinstance(data, list) and len(data) == 6
    print(f" [PASS] 7. GET /maintenance ({len(data)} machine records returned)")

    # 8. Capacity matrix endpoint
    status, data = get("/capacity")
    assert status == 200
    assert isinstance(data, list) and len(data) == 6
    print(f" [PASS] 8. GET /capacity ({len(data)} machines tracked)")

    # 9. Analytics endpoint
    status, data = get("/analytics")
    assert status == 200
    assert "metrics_comparison" in data
    assert "resilience_comparison" in data
    print(" [PASS] 9. GET /analytics (metrics and resilience comparisons)")

    # 10. AI Copilot inquiry
    status, data = post("/copilot/query", {"question": "Why is production at risk?"})
    assert status == 200
    assert "concise_answer" in data
    assert "explanation" in data
    print(f" [PASS] 10. POST /copilot/query (Provider: {data.get('provider')})")

    # 11. Disruption: Machine Failure M3
    status, data = post("/disruptions", {"type": "machine_failure", "machine_id": "M3"})
    assert status == 200
    assert data["disruption"]["machine_id"] == "M3"
    assert "affected_jobs" in data
    print(" [PASS] 11. POST /disruptions (Machine Failure M3)")

    # 12. History verification
    status, data = get("/history")
    assert status == 200
    assert len(data["history"]) >= 1
    assert data["history"][0]["decision_report"] is not None
    print(f" [PASS] 12. GET /history ({len(data['history'])} recorded with decision report)")

    # 13. AI Copilot after disruption: "Why was J7 moved to M5?"
    status, data = post("/copilot/query", {"question": "Why was J7 moved to M5?"})
    assert status == 200
    assert "M5" in data["explanation"] or "M5" in data["concise_answer"]
    print(" [PASS] 13. POST /copilot/query after disruption reasoning")

    # 14. Disruption: Machine Recovery M3
    status, data = post("/disruptions", {"type": "machine_recovery", "machine_id": "M3"})
    assert status == 200
    print(" [PASS] 14. POST /disruptions (Machine Recovery M3)")

    # 15. Urgent Job
    status, data = post("/disruptions", {"type": "urgent_job", "job_id": "J99", "duration": 30, "deadline": 90, "priority": 5})
    assert status == 200
    print(" [PASS] 15. POST /disruptions (Urgent Job J99)")

    # 16. Deadline Change
    status, data = post("/disruptions", {"type": "deadline_change", "job_id": "J7", "new_deadline": 140})
    assert status == 200
    print(" [PASS] 16. POST /disruptions (Deadline Change J7)")

    # 17. Job Cancellation
    status, data = post("/disruptions", {"type": "job_cancellation", "job_id": "J12"})
    assert status == 200
    print(" [PASS] 17. POST /disruptions (Job Cancellation J12)")

    # 18. Reset factory
    status, data = post("/factory/reset")
    assert status == 200
    assert data["status"] == "reset"
    print(" [PASS] 18. POST /factory/reset")

    print("\nALL 18 END-TO-END SMOKE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run()
