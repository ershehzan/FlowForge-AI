"""
Industrial Data Normalization & Cohesion Layer for FlowForge.

Takes parsed raw tables from either old (3 sheets) or new (up to 16 sheets)
Excel workbooks, validates cross-entity consistency, applies safe defaults,
and normalizes into a unified, fully-connected dataset for FactoryState.
"""
from typing import Dict, List, Any, Optional
from copy import deepcopy


def normalize_factory_data(
    machines: Dict[str, Any],
    jobs: List[Dict[str, Any]],
    disruptions: Optional[List[Dict[str, Any]]] = None,
    raw_sheets: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Normalize raw parsed spreadsheet sheets into unified, fully-connected
    industrial factory models.
    """
    raw = raw_sheets or {}
    machine_ids = list(machines.keys())
    job_ids = [j["job_id"] for j in jobs]

    # 1. Normalize Machines
    normalized_machines = {}
    for m_id, m in machines.items():
        m_copy = deepcopy(m)
        m_copy.setdefault("id", m_id)
        m_copy.setdefault("name", m.get("machine_name", f"Station {m_id}"))
        m_copy.setdefault("machine_name", m_copy["name"])
        m_copy.setdefault("status", "available")
        m_copy.setdefault("energy_kwh_per_hour", 8.0)
        m_copy.setdefault("idle_energy_kwh_per_hour", round(m_copy["energy_kwh_per_hour"] * 0.25, 2))
        m_copy.setdefault("capacity", 1)
        m_copy.setdefault("capacity_per_hour", 12)
        m_copy.setdefault("health_score", 92 if m_copy["status"] == "available" else 45)
        m_copy.setdefault("line_id", "LINE-A" if m_id in ["M1", "M2", "M3", "M01", "M02", "M03"] else "LINE-B")
        m_copy.setdefault("age_years", 3)
        normalized_machines[m_id] = m_copy

    # 2. Normalize Jobs
    normalized_jobs = []
    for idx, j in enumerate(jobs):
        j_copy = deepcopy(j)
        j_copy.setdefault("job_id", f"J{idx+1:02d}")
        j_copy.setdefault("name", j.get("job_name", j_copy["job_id"]))
        j_copy.setdefault("duration", j.get("processing_time", 30))
        j_copy.setdefault("processing_time", j_copy["duration"])
        j_copy.setdefault("deadline", j_copy["duration"] * 3)
        j_copy.setdefault("priority", 3)
        j_copy.setdefault("status", "pending")
        j_copy.setdefault("eligible_machines", machine_ids)
        j_copy.setdefault("quantity", 100)
        j_copy.setdefault("setup_time", 8)
        j_copy.setdefault("material_required", "RM-001")
        j_copy.setdefault("quality_target", 0.98)
        # Link to production order
        if "order_id" not in j_copy or not j_copy["order_id"]:
            j_copy["order_id"] = f"ORD-100{min(6, (idx // 2) + 1)}"
        normalized_jobs.append(j_copy)

    # 3. Normalize Production Lines
    lines = raw.get("production_lines", [])
    if not lines:
        lines = [
            {"line_id": "LINE-A", "line_name": "Precision Machining & Forming", "plant_area": "Plant 1 - Bay A", "shift_pattern": "2_SHIFT", "capacity_units_per_hour": 50, "status": "OPERATIONAL", "primary_product_family": "Engine & Powertrain Components"},
            {"line_id": "LINE-B", "line_name": "Robotic Fabrication & Finishing", "plant_area": "Plant 1 - Bay B", "shift_pattern": "2_SHIFT", "capacity_units_per_hour": 65, "status": "OPERATIONAL", "primary_product_family": "Aerospace Assemblies"},
            {"line_id": "LINE-C", "line_name": "Thermal Treatment & Cleaning", "plant_area": "Plant 2 - Bay C", "shift_pattern": "2_SHIFT", "capacity_units_per_hour": 45, "status": "OPERATIONAL", "primary_product_family": "Hydraulic Valves & Cylinders"},
        ]

    # 4. Normalize Machine Capabilities
    capabilities = raw.get("machine_capabilities", [])
    if not capabilities:
        capabilities = [
            {"machine_id": m_id, "capability": "PRECISION_MILLING" if "1" in m_id or "3" in m_id else "CNC_TURNING", "product_family": "Engine Components", "min_batch_size": 10, "max_batch_size": 500, "setup_time_min": 15, "quality_rating": 0.98}
            for m_id in machine_ids
        ]

    # 5. Normalize Materials
    materials = raw.get("materials", [])
    if not materials:
        materials = [
            {"material_id": "RM-001", "material_name": "Cold-Rolled Structural Steel 4140", "material_type": "RAW_MATERIAL", "unit": "kg", "standard_cost": 18.50, "supplier": "Voestalpine AG", "lead_time_hours": 24, "quality_grade": "A+"},
            {"material_id": "RM-002", "material_name": "Aerospace Aluminum Billet 6061-T6", "material_type": "RAW_MATERIAL", "unit": "kg", "standard_cost": 24.80, "supplier": "Constellium SE", "lead_time_hours": 36, "quality_grade": "A"},
            {"material_id": "RM-003", "material_name": "Titanium Alloy Ingot Ti-6Al-4V", "material_type": "RAW_MATERIAL", "unit": "kg", "standard_cost": 145.00, "supplier": "TIMET Aerospace", "lead_time_hours": 72, "quality_grade": "A++"},
            {"material_id": "RM-004", "material_name": "Engineering Polymer POM-C Acetal", "material_type": "RAW_MATERIAL", "unit": "kg", "standard_cost": 14.20, "supplier": "Quadrant Plastics", "lead_time_hours": 24, "quality_grade": "A"},
            {"material_id": "RM-005", "material_name": "High-Purity Copper Rod Cu-ETP", "material_type": "RAW_MATERIAL", "unit": "kg", "standard_cost": 32.50, "supplier": "Aurubis AG", "lead_time_hours": 48, "quality_grade": "A+"},
            {"material_id": "RM-006", "material_name": "High-Tensile Fasteners M8x35 Gr 8.8", "material_type": "COMPONENT", "unit": "units", "standard_cost": 0.95, "supplier": "Wurth Industry", "lead_time_hours": 12, "quality_grade": "A"},
            {"material_id": "RM-007", "material_name": "Fluorocarbon Hydraulic O-Rings", "material_type": "COMPONENT", "unit": "units", "standard_cost": 4.20, "supplier": "Freudenberg Sealing", "lead_time_hours": 18, "quality_grade": "A+"},
            {"material_id": "RM-008", "material_name": "Hard-Chrome Surface Plating Fluid", "material_type": "CHEMICAL", "unit": "liters", "standard_cost": 55.00, "supplier": "Atotech International", "lead_time_hours": 48, "quality_grade": "A"},
        ]

    # 6. Normalize Inventory
    inventory = raw.get("inventory", [])
    if not inventory:
        inventory = [
            {"material_id": "RM-001", "material_name": "Cold-Rolled Structural Steel 4140", "unit": "kg", "available_quantity": 3200, "reserved_quantity": 1850, "incoming_quantity": 1500, "reorder_level": 1000, "safety_stock": 500, "lead_time_hours": 24, "supplier": "Voestalpine AG", "status": "IN_STOCK"},
            {"material_id": "RM-002", "material_name": "Aerospace Aluminum Billet 6061-T6", "unit": "kg", "available_quantity": 1450, "reserved_quantity": 980, "incoming_quantity": 800, "reorder_level": 500, "safety_stock": 250, "lead_time_hours": 36, "supplier": "Constellium SE", "status": "IN_STOCK"},
            {"material_id": "RM-003", "material_name": "Titanium Alloy Ingot Ti-6Al-4V", "unit": "kg", "available_quantity": 165, "reserved_quantity": 140, "incoming_quantity": 120, "reorder_level": 100, "safety_stock": 50, "lead_time_hours": 72, "supplier": "TIMET Aerospace", "status": "LOW_STOCK"},
            {"material_id": "RM-004", "material_name": "Engineering Polymer POM-C Acetal", "unit": "kg", "available_quantity": 450, "reserved_quantity": 180, "incoming_quantity": 300, "reorder_level": 150, "safety_stock": 75, "lead_time_hours": 24, "supplier": "Quadrant Plastics", "status": "IN_STOCK"},
            {"material_id": "RM-005", "material_name": "High-Purity Copper Rod Cu-ETP", "unit": "kg", "available_quantity": 240, "reserved_quantity": 220, "incoming_quantity": 200, "reorder_level": 120, "safety_stock": 60, "lead_time_hours": 48, "supplier": "Aurubis AG", "status": "LOW_STOCK"},
            {"material_id": "RM-006", "material_name": "High-Tensile Fasteners M8x35 Gr 8.8", "unit": "units", "available_quantity": 5800, "reserved_quantity": 3200, "incoming_quantity": 4000, "reorder_level": 2000, "safety_stock": 1000, "lead_time_hours": 12, "supplier": "Wurth Industry", "status": "IN_STOCK"},
            {"material_id": "RM-007", "material_name": "Fluorocarbon Hydraulic O-Rings", "unit": "units", "available_quantity": 820, "reserved_quantity": 650, "incoming_quantity": 500, "reorder_level": 400, "safety_stock": 200, "lead_time_hours": 18, "supplier": "Freudenberg Sealing", "status": "IN_STOCK"},
            {"material_id": "RM-008", "material_name": "Hard-Chrome Surface Plating Fluid", "unit": "liters", "available_quantity": 320, "reserved_quantity": 190, "incoming_quantity": 250, "reorder_level": 100, "safety_stock": 50, "lead_time_hours": 48, "supplier": "Atotech International", "status": "IN_STOCK"},
        ]

    # Calculate status dynamically for each inventory item
    for item in inventory:
        avail = item.get("available_quantity", item.get("available_qty", 0))
        res = item.get("reserved_quantity", item.get("reserved_qty", 0))
        reorder = item.get("reorder_level", 100)
        net = avail - res
        if net <= 0:
            item["status"] = "OUT_OF_STOCK"
        elif net <= reorder:
            item["status"] = "LOW_STOCK"
        else:
            item["status"] = "IN_STOCK"
        item["available_qty"] = avail
        item["reserved_qty"] = res

    # 7. Normalize Production Orders
    orders = raw.get("production_orders", [])
    if not orders:
        orders_map = {}
        for j in normalized_jobs:
            o_id = j["order_id"]
            if o_id not in orders_map:
                orders_map[o_id] = {
                    "order_id": o_id,
                    "product_id": f"P-{o_id[-4:]}",
                    "product_name": f"Manufacturing Assembly {o_id}",
                    "customer": f"Industrial Client {o_id[-2:]}",
                    "quantity": 100,
                    "priority": j.get("priority", 3),
                    "release_time": "06:00",
                    "deadline": max(j.get("deadline", 120), 120),
                    "status": "In Production",
                    "material_required": j.get("material_required", "RM-001"),
                    "quality_requirement": 0.98,
                    "job_ids": [],
                }
            orders_map[o_id]["job_ids"].append(j["job_id"])
        orders = list(orders_map.values())

    # 8. Normalize Operations
    operations = raw.get("operations", [])
    if not operations:
        for j in normalized_jobs:
            j_id = j["job_id"]
            dur = j.get("duration", 30)
            operations.append({
                "operation_id": f"OP-{j_id}-01",
                "job_id": j_id,
                "operation_sequence": 1,
                "operation_name": f"{j.get('name', j_id)} Primary",
                "processing_time": dur,
                "eligible_machines": j.get("eligible_machines", machine_ids),
                "setup_time": j.get("setup_time", 8),
                "material_required": j.get("material_required", "RM-001"),
                "quantity": j.get("quantity", 100),
                "precedence": "NONE",
                "quality_requirement": j.get("quality_target", 0.98),
            })

    # 9. Normalize Maintenance
    maintenance = raw.get("maintenance", [])
    if not maintenance:
        maintenance = [
            {
                "maintenance_id": f"MNT-{idx+1:02d}",
                "machine_id": m_id,
                "machine_name": normalized_machines[m_id]["name"],
                "maintenance_type": "PREVENTIVE",
                "scheduled_start": "18:00",
                "scheduled_end": "19:30",
                "duration_minutes": 90,
                "maintenance_priority": "MEDIUM",
                "reason": "Scheduled periodic preventive inspection & lube",
                "status": "SCHEDULED",
            }
            for idx, m_id in enumerate(machine_ids[:4])
        ]

    # 10. Normalize Downtime
    downtime = raw.get("downtime", [])

    # 11. Normalize Energy
    energy = raw.get("energy", [])
    if not energy:
        energy = [
            {
                "energy_id": f"ENG-{m_id}",
                "machine_id": m_id,
                "timestamp": "08:00",
                "power_kw": normalized_machines[m_id]["energy_kwh_per_hour"],
                "energy_kwh": normalized_machines[m_id]["energy_kwh_per_hour"],
                "operating_state": "RUNNING" if normalized_machines[m_id]["status"] == "available" else "FAILED",
                "job_id": "NONE",
            }
            for m_id in machine_ids
        ]

    # 12. Normalize Quality
    quality = raw.get("quality", [])
    if not quality:
        quality = [
            {
                "inspection_id": f"QC-{idx+1:02d}",
                "job_id": j_id,
                "operation_id": f"OP-{j_id}-01",
                "machine_id": machine_ids[idx % len(machine_ids)],
                "quantity_produced": 100,
                "quantity_rejected": 1,
                "defect_rate": 0.01,
                "quality_score": 0.99,
                "inspection_time": "08:30",
            }
            for idx, j_id in enumerate(job_ids[:6])
        ]

    # 13. Normalize Shifts
    shifts = raw.get("shifts", [])
    if not shifts:
        shifts = [
            {"shift_id": "SHIFT-1", "shift_name": "Morning Shift (Core)", "start_time": "06:00", "end_time": "14:00", "working_hours": 8, "available_machine_count": len(machine_ids)},
            {"shift_id": "SHIFT-2", "shift_name": "Evening Shift (Machining & Assembly)", "start_time": "14:00", "end_time": "22:00", "working_hours": 8, "available_machine_count": len(machine_ids)},
            {"shift_id": "SHIFT-3", "shift_name": "Night Shift (Automated Operations)", "start_time": "22:00", "end_time": "06:00", "working_hours": 8, "available_machine_count": max(2, len(machine_ids) // 2)},
        ]

    # 14. Normalize Dependencies
    dependencies = raw.get("dependencies", [])

    # 15. Normalize Disruptions
    disrupt_list = disruptions if disruptions is not None else raw.get("disruptions", [])

    # 16. Normalize Scenarios (10 Predefined Industrial Scenarios)
    scenarios = raw.get("scenarios", [])
    if not scenarios:
        scenarios = [
            {"scenario_id": 1, "scenario_name": "Normal Production", "category": "Baseline", "target_id": "ALL", "trigger_type": "nominal", "expected_action": "Optimize baseline schedule across fleet", "business_impact": "Nominal makespan, minimum energy, zero tardiness"},
            {"scenario_id": 2, "scenario_name": "Single Machine Failure", "category": "Unplanned Disruption", "target_id": "M03" if "M03" in machine_ids else (machine_ids[2] if len(machine_ids) > 2 else machine_ids[0]), "trigger_type": "machine_failure", "expected_action": "Reroute affected jobs to parallel stations", "business_impact": "Protects delivery deadlines without tardiness"},
            {"scenario_id": 3, "scenario_name": "Multiple Machine Failure", "category": "Severe Outage", "target_id": f"{machine_ids[0]},{machine_ids[1]}" if len(machine_ids) > 1 else machine_ids[0], "trigger_type": "multiple_failure", "expected_action": "Dynamic multi-station load redistribution", "business_impact": "Recovers resilience across cascading capacity drop"},
            {"scenario_id": 4, "scenario_name": "Urgent Customer Order", "category": "Rush Demand", "target_id": "J99", "trigger_type": "urgent_job", "expected_action": "Insert 35m rush order without delaying active orders", "business_impact": "Guarantees emergency customer SLA"},
            {"scenario_id": 5, "scenario_name": "Deadline Change", "category": "Schedule Acceleration", "target_id": job_ids[0] if job_ids else "J01", "trigger_type": "deadline_change", "expected_action": "Compress order schedule window", "business_impact": "Expedites delivery for Tier-1 customer"},
            {"scenario_id": 6, "scenario_name": "Job Cancellation", "category": "Capacity Release", "target_id": job_ids[-1] if job_ids else "J12", "trigger_type": "job_cancellation", "expected_action": "Remove job and advance downstream schedule", "business_impact": "Frees machine capacity and lowers total energy"},
            {"scenario_id": 7, "scenario_name": "Planned Maintenance", "category": "Preventive Maintenance", "target_id": machine_ids[3] if len(machine_ids) > 3 else machine_ids[0], "trigger_type": "planned_downtime", "expected_action": "Schedule around 90-min maintenance window", "business_impact": "Eliminates unexpected equipment failure during production"},
            {"scenario_id": 8, "scenario_name": "Material Shortage", "category": "Supply Chain Disruption", "target_id": "RM-003", "trigger_type": "material_shortage", "expected_action": "Flag constrained orders; prioritize feasible work", "business_impact": "Prevents shop floor starvation and idle machine time"},
            {"scenario_id": 9, "scenario_name": "Quality Calibration Drift", "category": "Defect Mitigation", "target_id": machine_ids[1] if len(machine_ids) > 1 else machine_ids[0], "trigger_type": "quality_issue", "expected_action": "Reroute tight-tolerance operations away from station", "business_impact": "Mitigates scrap rate spike on high-cost alloys"},
            {"scenario_id": 10, "scenario_name": "Peak Energy Constraint", "category": "Energy Optimization", "target_id": "FACTORY", "trigger_type": "energy_constraint", "expected_action": "Interleave high-draw stations to cap demand under 65 kW", "business_impact": "Reduces peak utility demand tariffs by up to 18%"},
        ]

    return {
        "machines": normalized_machines,
        "jobs": normalized_jobs,
        "production_lines": lines,
        "machine_capabilities": capabilities,
        "production_orders": orders,
        "operations": operations,
        "materials": materials,
        "inventory": inventory,
        "maintenance": maintenance,
        "downtime": downtime,
        "energy": energy,
        "quality": quality,
        "shifts": shifts,
        "dependencies": dependencies,
        "disruptions": disrupt_list,
        "scenarios": scenarios,
    }
