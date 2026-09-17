"""
ERP Operations Coordinator for FlowForge Manufacturing Operations.

Binds FactoryState, production schedules, machine fleet states,
orders, inventory balances, and maintenance logs into a cohesive
manufacturing operational view.
"""
from typing import Dict, List, Any, Optional
from copy import deepcopy

from agents.erp.models import ProductionOrder, InventoryItem, MaintenanceRecord


def get_default_orders() -> List[ProductionOrder]:
    """Return default coherent production orders matching default 12 jobs."""
    return [
        ProductionOrder(
            order_id="ORD-1001",
            product_name="Exhaust Manifold Assembly",
            customer="Apex Automotive GmbH",
            quantity=150,
            priority=4,
            deadline=120,
            status="In Production",
            progress=65,
            risk_level="Low",
            job_ids=["J01", "J02"],
            required_materials={"RM-001": 150, "RM-006": 600},
        ),
        ProductionOrder(
            order_id="ORD-1002",
            product_name="Turbine Impeller Core",
            customer="AeroDynamic Power Inc",
            quantity=80,
            priority=5,
            deadline=95,
            status="In Production",
            progress=40,
            risk_level="Medium",
            job_ids=["J03", "J04"],
            required_materials={"RM-002": 160, "RM-005": 80},
        ),
        ProductionOrder(
            order_id="ORD-1003",
            product_name="Hydraulic Valve Body",
            customer="Krupp Heavy Motion",
            quantity=220,
            priority=3,
            deadline=150,
            status="Queued",
            progress=15,
            risk_level="Low",
            job_ids=["J05", "J06"],
            required_materials={"RM-001": 220, "RM-003": 110},
        ),
        ProductionOrder(
            order_id="ORD-1004",
            product_name="Precision Drive Shaft",
            customer="Veloce Powertrain Ltd",
            quantity=95,
            priority=4,
            deadline=110,
            status="In Production",
            progress=55,
            risk_level="Medium",
            job_ids=["J07", "J08"],
            required_materials={"RM-001": 190, "RM-006": 380},
        ),
        ProductionOrder(
            order_id="ORD-1005",
            product_name="Planetary Gearbox Housing",
            customer="Nordic Robotic Systems",
            quantity=60,
            priority=2,
            deadline=180,
            status="Queued",
            progress=0,
            risk_level="Low",
            job_ids=["J09", "J10"],
            required_materials={"RM-002": 120, "RM-004": 60},
        ),
        ProductionOrder(
            order_id="ORD-1006",
            product_name="High-Pressure Cylinder Block",
            customer="Sulzer Fluid Dynamics",
            quantity=110,
            priority=3,
            deadline=160,
            status="Queued",
            progress=10,
            risk_level="Low",
            job_ids=["J11", "J12"],
            required_materials={"RM-001": 220, "RM-005": 55},
        ),
    ]


def get_default_inventory() -> List[InventoryItem]:
    """Return default manufacturing inventory items."""
    return [
        InventoryItem(
            part_id="RM-001",
            part_name="Steel Sheet (Cold Rolled 3mm)",
            category="Raw Material",
            available_qty=950,
            reserved_qty=780,
            incoming_qty=500,
            reorder_level=300,
            unit="sheets",
            unit_cost=42.50,
            at_risk_orders=["ORD-1006"],
        ),
        InventoryItem(
            part_id="RM-002",
            part_name="Aluminum 6061-T6 Extrusion Billet",
            category="Raw Material",
            available_qty=420,
            reserved_qty=280,
            incoming_qty=200,
            reorder_level=150,
            unit="kg",
            unit_cost=18.75,
            at_risk_orders=[],
        ),
        InventoryItem(
            part_id="RM-003",
            part_name="Electrolytic Copper Bar (CW004A)",
            category="Raw Material",
            available_qty=210,
            reserved_qty=110,
            incoming_qty=100,
            reorder_level=80,
            unit="kg",
            unit_cost=34.20,
            at_risk_orders=[],
        ),
        InventoryItem(
            part_id="RM-004",
            part_name="Polymer Granules (POM-C Acetal)",
            category="Component",
            available_qty=180,
            reserved_qty=60,
            incoming_qty=250,
            reorder_level=100,
            unit="kg",
            unit_cost=12.00,
            at_risk_orders=[],
        ),
        InventoryItem(
            part_id="RM-005",
            part_name="Titanium Alloy Rod (Ti-6Al-4V)",
            category="Raw Material",
            available_qty=140,
            reserved_qty=135,
            incoming_qty=150,
            reorder_level=50,
            unit="kg",
            unit_cost=115.00,
            at_risk_orders=["ORD-1002"],
        ),
        InventoryItem(
            part_id="RM-006",
            part_name="High-Tensile Fasteners M8x35 (Gr 8.8)",
            category="Fastener",
            available_qty=2400,
            reserved_qty=980,
            incoming_qty=2000,
            reorder_level=800,
            unit="units",
            unit_cost=0.85,
            at_risk_orders=[],
        ),
    ]


def get_default_maintenance(machines: Optional[Dict[str, Any]] = None) -> List[MaintenanceRecord]:
    """Return default maintenance state for factory machines."""
    specs = {
        "M1": ("CNC Milling Center 5-Axis", 94, "Sep 10", "Sep 25", 84.5, 0, []),
        "M2": ("Robotic Welding Cell", 88, "Sep 08", "Sep 22", 112.0, 15, []),
        "M3": ("Heavy Stamping Press G2", 72, "Sep 05", "Sep 18", 146.2, 45, ["Hydraulic valve pressure drop"]),
        "M4": ("Automated Conveyor Line A1", 91, "Sep 12", "Sep 28", 92.0, 0, []),
        "M5": ("Precision Metal Lathe P3", 85, "Sep 07", "Sep 21", 78.4, 10, []),
        "M6": ("Precision Assembly Station", 96, "Sep 11", "Sep 29", 64.0, 0, []),
    }

    records = []
    keys = list(machines.keys()) if machines else ["M1", "M2", "M3", "M4", "M5", "M6"]
    for m_id in keys:
        name, health, last_m, next_m, runtime, downtime, issues = specs.get(
            m_id, (f"Station {m_id}", 85, "Sep 08", "Sep 22", 80.0, 0, [])
        )
        is_avail = True
        if machines and m_id in machines:
            is_avail = machines[m_id].get("status") == "available"

        status = "RUNNING" if is_avail else "FAILED"
        records.append(
            MaintenanceRecord(
                machine_id=m_id,
                machine_name=name,
                health_score=health if is_avail else 20,
                status=status,
                last_maintenance=last_m,
                next_maintenance=next_m,
                runtime_hours=runtime,
                downtime_minutes=downtime if is_avail else downtime + 35,
                scheduled_window=machines[m_id].get("unavailable_periods", [[]])[0] if (machines and m_id in machines and machines[m_id].get("unavailable_periods")) else [],
                active_issues=issues if is_avail else ["CRITICAL: Spindle drive shutdown / Station offline"],
            )
        )
    return records


class ERPEngine:
    """
    Coordinator of manufacturing operations: orders, capacity,
    materials inventory, and machine maintenance.
    """

    def __init__(self, factory_state):
        self.factory_state = factory_state
        self.rebuild_from_state()

    def rebuild_from_state(self):
        """Rebuild orders, inventory, and maintenance from factory_state if rich data exists."""
        fs = self.factory_state

        # 1. Orders
        if getattr(fs, "production_orders", None):
            self.orders = []
            for o in fs.production_orders:
                prio = o.get("priority", 3)
                if isinstance(prio, str):
                    prio_map = {"CRITICAL": 5, "RUSH": 5, "HIGH": 4, "MEDIUM": 3, "NORMAL": 3, "LOW": 2, "LOWEST": 1}
                    prio = prio_map.get(prio.upper(), 3)
                self.orders.append(
                    ProductionOrder(
                        order_id=o.get("order_id", "ORD-00"),
                        product_name=o.get("product_name", "Product"),
                        customer=o.get("customer", "Customer"),
                        quantity=int(o.get("quantity", 100)),
                        priority=int(prio),
                        deadline=int(o.get("deadline", 120)),
                        status=o.get("status", "In Production"),
                        progress=int(o.get("progress", 25)),
                        risk_level=o.get("risk_level", "Low"),
                        job_ids=o.get("job_ids", []),
                        required_materials=o.get("required_materials", {o.get("material_required", "RM-001"): int(o.get("quantity", 100))}),
                    )
                )
        else:
            self.orders = get_default_orders()

        # 2. Inventory
        if getattr(fs, "inventory_items", None):
            self.inventory = []
            for inv in fs.inventory_items:
                item = InventoryItem(
                    part_id=inv.get("material_id", inv.get("part_id", "RM-001")),
                    part_name=inv.get("material_name", inv.get("part_name", "Material")),
                    category=inv.get("material_type", inv.get("category", "Raw Material")),
                    available_qty=int(inv.get("available_quantity", inv.get("available_qty", 1000))),
                    reserved_qty=int(inv.get("reserved_quantity", inv.get("reserved_qty", 500))),
                    incoming_qty=int(inv.get("incoming_quantity", inv.get("incoming_qty", 500))),
                    reorder_level=int(inv.get("reorder_level", 200)),
                    unit=inv.get("unit", "kg"),
                    unit_cost=float(inv.get("standard_cost", inv.get("unit_cost", 20.0))),
                    status=inv.get("status", "IN STOCK"),
                    at_risk_orders=[],
                )
                item.calculate_status()
                self.inventory.append(item)
        else:
            self.inventory = get_default_inventory()

        # 3. Maintenance
        if getattr(fs, "maintenance_records", None) and fs.maintenance_records:
            self.maintenance = []
            for m in fs.maintenance_records:
                m_id = m.get("machine_id", "M01")
                m_name = fs.machines.get(m_id, {}).get("name", m_id) if hasattr(fs, "machines") else m_id
                self.maintenance.append(
                    MaintenanceRecord(
                        machine_id=m_id,
                        machine_name=m_name,
                        health_score=int(m.get("health_score", 90)),
                        status="MAINTENANCE" if m.get("status") == "SCHEDULED" else "RUNNING",
                        last_maintenance=str(m.get("last_maintenance", "Recent")),
                        next_maintenance=str(m.get("scheduled_start", "Upcoming")),
                        runtime_hours=float(m.get("runtime_hours", 80.0)),
                        downtime_minutes=int(m.get("duration_minutes", 0)),
                        scheduled_window=[0, int(m.get("duration_minutes", 60))] if m.get("scheduled_start") else [],
                        active_issues=[m.get("reason")] if m.get("reason") else [],
                    )
                )
        else:
            self.maintenance = get_default_maintenance(fs.machines)


    def synchronize(self):
        """Sync ERP state with current factory machines and schedule."""
        fs = self.factory_state
        schedule = fs.get_current_schedule() or fs.baseline_schedule or []
        machines = fs.machines

        # 1. Update Maintenance records based on machine status
        for m_rec in self.maintenance:
            m_id = m_rec.machine_id
            if m_id in machines:
                is_avail = machines[m_id].get("status") == "available"
                if not is_avail:
                    m_rec.status = "FAILED"
                    m_rec.health_score = min(m_rec.health_score, 30)
                    if "CRITICAL: Station Offline" not in m_rec.active_issues:
                        m_rec.active_issues.append("CRITICAL: Station Offline")
                else:
                    m_rec.status = "RUNNING"
                    m_rec.active_issues = [iss for iss in m_rec.active_issues if "CRITICAL" not in iss]

        # 2. Update Order progress and risk based on scheduled jobs
        sched_map = {item["job_id"]: item for item in schedule}
        for order in self.orders:
            order_jobs = [sched_map[jid] for jid in order.job_ids if jid in sched_map]
            if order_jobs:
                # If any job finishes after deadline, order is At Risk
                max_end = max(j.get("end", j.get("start", 0) + j.get("duration", 0)) for j in order_jobs)
                any_reassigned = any(j.get("reassigned") for j in order_jobs)
                if max_end > order.deadline:
                    order.status = "At Risk"
                    order.risk_level = "High"
                elif any_reassigned:
                    order.status = "In Production"
                    order.risk_level = "Medium"
                else:
                    order.status = "In Production"
                    order.risk_level = "Low"
                order.progress = min(95, max(15, int((1 - (max_end / max(1, order.deadline * 1.5))) * 100)))

        # 3. Recalculate inventory status
        for inv in self.inventory:
            inv.calculate_status()

    def get_capacity_matrix(self) -> List[Dict[str, Any]]:
        """Return machine capacity, scheduled load, and remaining availability."""
        fs = self.factory_state
        schedule = fs.get_current_schedule() or fs.baseline_schedule or []
        machines = fs.machines

        total_shift_minutes = 480  # 8-hour shift = 480 minutes
        matrix = []

        for m_id, m_data in sorted(machines.items()):
            is_avail = m_data.get("status") == "available"
            assigned_jobs = [item for item in schedule if item.get("machine") == m_id]
            scheduled_load = sum(j.get("duration", 0) for j in assigned_jobs)
            available_capacity = total_shift_minutes if is_avail else 0
            utilization = round((scheduled_load / available_capacity * 100), 1) if available_capacity > 0 else 0
            remaining_cap = max(0, available_capacity - scheduled_load)

            matrix.append({
                "machine_id": m_id,
                "machine_name": m_data.get("name", m_id),
                "status": "RUNNING" if is_avail else "FAILED",
                "available_capacity": available_capacity,
                "scheduled_load": scheduled_load,
                "utilization": min(100.0, utilization),
                "remaining_capacity": remaining_cap,
                "assigned_jobs_count": len(assigned_jobs),
                "power_kwh": m_data.get("power_kwh", 15.0),
            })
        return matrix

    def get_attention_required(self) -> List[Dict[str, Any]]:
        """Return actionable alerts for Command Center."""
        self.synchronize()
        alerts = []
        fs = self.factory_state

        # Machine failures
        for m_id, m_data in fs.machines.items():
            if m_data.get("status") != "available":
                alerts.append({
                    "severity": "CRITICAL",
                    "code": "MACHINE_FAILURE",
                    "title": f"🔴 Station {m_id} Failure",
                    "description": f"{m_data.get('name', m_id)} is offline. Affected tasks have been dynamically reassigned.",
                    "entity": m_id,
                    "target_tab": "shop-floor",
                })

        # Orders at risk
        for order in self.orders:
            if order.risk_level in ["High", "Critical"]:
                alerts.append({
                    "severity": "WARNING",
                    "code": "ORDER_AT_RISK",
                    "title": f"🟡 Order {order.order_id} at Risk",
                    "description": f"{order.product_name} delivery deadline ({order.deadline}m) compressed.",
                    "entity": order.order_id,
                    "target_tab": "production",
                })

        # Inventory low stock
        for inv in self.inventory:
            if inv.status in ["LOW STOCK", "OUT OF STOCK"]:
                alerts.append({
                    "severity": "WARNING",
                    "code": "INVENTORY_LOW",
                    "title": f"🟡 Low Stock: {inv.part_id}",
                    "description": f"{inv.part_name} available ({inv.available_qty} {inv.unit}) is near reorder threshold ({inv.reorder_level}).",
                    "entity": inv.part_id,
                    "target_tab": "inventory",
                })

        # High capacity bottlenecks
        cap_matrix = self.get_capacity_matrix()
        for cap in cap_matrix:
            if cap["utilization"] >= 90 and cap["status"] == "RUNNING":
                alerts.append({
                    "severity": "INFO",
                    "code": "HIGH_UTILIZATION",
                    "title": f"ℹ️ Bottleneck Station: {cap['machine_id']}",
                    "description": f"{cap['machine_name']} scheduled at {cap['utilization']}% utilization.",
                    "entity": cap["machine_id"],
                    "target_tab": "shop-floor",
                })

        return alerts

    def to_dict(self) -> Dict[str, Any]:
        """Serialize full ERP-lite operational state."""
        self.synchronize()
        return {
            "orders": [o.to_dict() for o in self.orders],
            "inventory": [i.to_dict() for i in self.inventory],
            "maintenance": [m.to_dict() for m in self.maintenance],
            "capacity": self.get_capacity_matrix(),
            "attention_required": self.get_attention_required(),
        }
