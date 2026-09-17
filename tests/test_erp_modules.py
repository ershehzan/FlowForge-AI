"""
Unit tests for FlowForge ERP-Lite Manufacturing Operations System.

Tests Production Orders, Inventory balances, Maintenance health,
Capacity matrix, and AI Operations Copilot reasoning.
"""
import pytest
from fastapi.testclient import TestClient

from agents.factory.state import FactoryState
from agents.erp.models import ProductionOrder, InventoryItem, MaintenanceRecord
from agents.erp.engine import ERPEngine, get_default_orders, get_default_inventory, get_default_maintenance
from agents.copilot.provider import AICopilotProvider
from deployment.app import app


client = TestClient(app)


def test_production_order_model():
    order = ProductionOrder(
        order_id="ORD-TEST",
        product_name="Test Impeller",
        customer="Test Aero Corp",
        quantity=50,
        priority=4,
        deadline=100,
        status="Queued",
        progress=0,
        risk_level="Low",
        job_ids=["J01", "J02"],
        required_materials={"RM-001": 50},
    )
    d = order.to_dict()
    assert d["order_id"] == "ORD-TEST"
    assert d["quantity"] == 50
    assert d["risk_level"] == "Low"


def test_inventory_item_status_calculation():
    item = InventoryItem(
        part_id="RM-TEST",
        part_name="Titanium Alloy Rod",
        category="Raw Material",
        available_qty=200,
        reserved_qty=50,
        incoming_qty=100,
        reorder_level=60,
        unit="kg",
        unit_cost=85.0,
    )
    assert item.calculate_status() == "IN STOCK"

    # Low stock test
    item.reserved_qty = 150
    assert item.calculate_status() == "LOW STOCK"

    # Out of stock test
    item.reserved_qty = 210
    assert item.calculate_status() == "OUT OF STOCK"


def test_erp_engine_capacity_matrix():
    fs = FactoryState()
    erp = ERPEngine(fs)
    matrix = erp.get_capacity_matrix()

    assert len(matrix) == 6
    machine_ids = [m["machine_id"] for m in matrix]
    assert "M1" in machine_ids
    assert "M6" in machine_ids
    for row in matrix:
        assert "utilization" in row
        assert "remaining_capacity" in row
        assert "scheduled_load" in row


def test_erp_engine_attention_required():
    fs = FactoryState()
    erp = ERPEngine(fs)
    alerts = erp.get_attention_required()
    assert isinstance(alerts, list)

    # Fail M3 and check critical alert
    fs.machines["M3"]["status"] = "failed"
    alerts_after_fail = erp.get_attention_required()
    critical_alerts = [a for a in alerts_after_fail if a["severity"] == "CRITICAL"]
    assert len(critical_alerts) >= 1
    assert any("M3" in a["title"] for a in critical_alerts)


def test_ai_copilot_deterministic_queries():
    fs = FactoryState()
    fs.machines["M3"]["status"] = "failed"
    context = {
        "factory_status": "DISRUPTED",
        "machines": fs.machines,
        "schedule": [{"job_id": "J07", "machine": "M5", "start": 10, "end": 45, "deadline": 110, "reassigned": True}],
        "metrics": {"makespan": 145, "energy_consumption": 112.5},
        "resilience": {"score": 81},
        "orders": [o.to_dict() for o in get_default_orders()],
        "inventory": [i.to_dict() for i in get_default_inventory()],
        "capacity": ERPEngine(fs).get_capacity_matrix(),
    }

    copilot = AICopilotProvider()

    # Bottleneck question
    res_b = copilot.query("Which machine is currently the bottleneck?", context)
    assert "bottleneck" in res_b["answer"].lower()
    assert "recommended_action" in res_b

    # Risk question
    res_r = copilot.query("Why is production at risk?", context)
    assert len(res_r["affected_entities"]) >= 1

    # M3 failure question
    res_m = copilot.query("What happened to M3?", context)
    assert "m3" in res_m["answer"].lower()

    # Energy question
    res_e = copilot.query("How much energy is consumed?", context)
    assert "kwh" in res_e["answer"].lower()

    # Inventory question
    res_i = copilot.query("Are raw materials in stock?", context)
    assert "inventory" in res_i["answer"].lower() or "stock" in res_i["answer"].lower()


def test_erp_api_endpoints():
    # 1. Reset factory
    res = client.post("/factory/reset")
    assert res.status_code == 200

    # 2. Get ERP State
    res_erp = client.get("/erp/state")
    assert res_erp.status_code == 200
    data = res_erp.json()
    assert "orders" in data
    assert "inventory" in data
    assert "maintenance" in data
    assert "capacity" in data
    assert "attention_required" in data

    # 3. Get Orders
    res_ord = client.get("/orders")
    assert res_ord.status_code == 200
    assert len(res_ord.json()) >= 6

    # 4. Get Inventory
    res_inv = client.get("/inventory")
    assert res_inv.status_code == 200
    assert len(res_inv.json()) >= 6

    # 5. Get Maintenance
    res_maint = client.get("/maintenance")
    assert res_maint.status_code == 200
    assert len(res_maint.json()) >= 5

    # 6. Get Capacity
    res_cap = client.get("/capacity")
    assert res_cap.status_code == 200
    assert len(res_cap.json()) >= 6

    # 7. Get Analytics
    res_ana = client.get("/analytics")
    assert res_ana.status_code == 200
    ana_data = res_ana.json()
    assert "metrics_comparison" in ana_data
    assert "resilience_comparison" in ana_data

    # 8. Copilot Query Endpoint
    res_cop = client.post("/copilot/query", json={"query": "Which machine is the bottleneck?"})
    assert res_cop.status_code == 200
    cop_data = res_cop.json()
    assert "answer" in cop_data
    assert "recommended_action" in cop_data


def test_disruption_records_history_entry():
    # Initialize factory first
    client.post("/factory/initialize")

    # Apply disruption
    res = client.post("/disruptions", json={"type": "machine_failure", "machine_id": "M3"})
    assert res.status_code == 200
    data = res.json()
    assert "history" in data
    assert len(data["history"]) >= 1
    latest = data["history"][0]
    assert latest["event_type"] == "machine_failure"
    assert "decision_report" in latest
    assert "impact" in latest["decision_report"]
