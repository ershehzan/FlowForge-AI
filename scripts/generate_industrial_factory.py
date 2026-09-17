"""
Generate the Expanded Industrial Factory Workbook for FlowForge.
Contains all 16 connected sheets representing a realistic manufacturing plant.
"""
import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

def create_industrial_workbook(filepath="data/industrial_factory.xlsx"):
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # Styles
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid")
    regular_font = Font(name="Calibri", size=10)
    thin_border = Border(
        left=Side(style='thin', color='E5E7EB'),
        right=Side(style='thin', color='E5E7EB'),
        top=Side(style='thin', color='E5E7EB'),
        bottom=Side(style='thin', color='E5E7EB')
    )

    def style_sheet(ws, headers, rows):
        ws.append(headers)
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
        for row in rows:
            ws.append(row)
        for row_cells in ws.iter_rows(min_row=2, max_row=len(rows)+1, min_col=1, max_col=len(headers)):
            for cell in row_cells:
                cell.font = regular_font
                cell.border = thin_border
        # Auto column width
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # 1. Machines
    machines_headers = [
        "machine_id", "machine_name", "line_id", "machine_type", "status",
        "energy_kwh_per_hour", "idle_energy_kwh_per_hour", "available_from",
        "available_until", "capacity_per_hour", "maintenance_due", "health_score", "age_years"
    ]
    machines_rows = [
        ["M01", "5-Axis CNC Milling Center", "LINE-A", "CNC_MILL", "available", 8.5, 2.2, "06:00", "22:00", 12, "2026-09-25", 94, 3],
        ["M02", "Heavy Duty CNC Lathe", "LINE-A", "CNC_LATHE", "available", 9.2, 2.4, "06:00", "22:00", 14, "2026-09-28", 88, 4],
        ["M03", "Precision Stamping Press G2", "LINE-A", "STAMPING_PRESS", "available", 14.5, 3.8, "06:00", "22:00", 25, "2026-09-18", 72, 6],
        ["M04", "Robotic Arc Welding Cell", "LINE-B", "ROBOTIC_WELD", "available", 7.0, 1.8, "06:00", "22:00", 10, "2026-09-22", 91, 2],
        ["M05", "High-Precision Grinder P3", "LINE-B", "GRINDER", "available", 6.8, 1.6, "06:00", "22:00", 15, "2026-09-21", 85, 5],
        ["M06", "Automated Optical Inspection Station", "LINE-B", "INSPECTION", "available", 3.2, 0.8, "06:00", "22:00", 30, "2026-10-05", 96, 1],
        ["M07", "EDM Wire Cutting Station", "LINE-C", "EDM_CUT", "available", 5.5, 1.2, "06:00", "22:00", 8, "2026-09-30", 92, 3],
        ["M08", "Induction Heat Treatment Furnace", "LINE-C", "HEAT_TREAT", "available", 18.0, 4.5, "06:00", "22:00", 18, "2026-09-24", 82, 7],
        ["M09", "Automated Ultrasonic Cleaning Tank", "LINE-C", "WASH_STATION", "available", 4.0, 1.0, "06:00", "22:00", 35, "2026-10-10", 95, 2],
        ["M10", "Modular Assembly & Packaging Robot", "LINE-B", "ASSEMBLY", "available", 4.8, 1.1, "06:00", "22:00", 22, "2026-10-02", 94, 2],
    ]
    style_sheet(wb.create_sheet(title="Machines"), machines_headers, machines_rows)

    # 2. Production_Lines
    lines_headers = [
        "line_id", "line_name", "plant_area", "shift_pattern",
        "capacity_units_per_hour", "status", "primary_product_family"
    ]
    lines_rows = [
        ["LINE-A", "Precision Machining & Forming", "Plant 1 - Bay A", "2_SHIFT", 50, "OPERATIONAL", "Engine & Powertrain Components"],
        ["LINE-B", "Robotic Fabrication & Finishing", "Plant 1 - Bay B", "2_SHIFT", 65, "OPERATIONAL", "Aerospace Assemblies"],
        ["LINE-C", "Thermal Treatment & Cleaning", "Plant 2 - Bay C", "2_SHIFT", 45, "OPERATIONAL", "Hydraulic Valves & Cylinders"],
    ]
    style_sheet(wb.create_sheet(title="Production_Lines"), lines_headers, lines_rows)

    # 3. Machine_Capabilities
    cap_headers = ["machine_id", "capability", "product_family", "min_batch_size", "max_batch_size", "setup_time_min", "quality_rating"]
    cap_rows = [
        ["M01", "5_AXIS_CONTOURING", "Engine Components", 10, 500, 15, 0.98],
        ["M01", "TITANIUM_MILLING", "Aerospace Assemblies", 5, 200, 20, 0.97],
        ["M02", "PRECISION_TURNING", "Engine Components", 20, 800, 12, 0.96],
        ["M03", "HEAVY_FORMING", "Structural Brackets", 50, 2000, 25, 0.94],
        ["M04", "ROBOTIC_TIG_WELDING", "Aerospace Assemblies", 5, 300, 10, 0.98],
        ["M05", "SURFACE_GRINDING", "Hydraulic Valves", 15, 600, 10, 0.97],
        ["M06", "3D_OPTICAL_SCAN", "All Families", 1, 5000, 2, 0.99],
        ["M07", "PRECISION_WIRE_CUT", "Turbine Blades", 2, 100, 30, 0.99],
        ["M08", "NITRIDE_HARDENING", "Drive Shafts", 30, 1000, 45, 0.95],
        ["M09", "ULTRASONIC_DEGREASING", "All Families", 50, 3000, 5, 0.99],
        ["M10", "AUTOMATED_BOXING", "All Families", 20, 5000, 5, 0.99],
    ]
    style_sheet(wb.create_sheet(title="Machine_Capabilities"), cap_headers, cap_rows)

    # 4. Production_Orders
    orders_headers = [
        "order_id", "product_id", "product_name", "customer", "quantity",
        "priority", "release_time", "deadline", "status", "material_required", "quality_requirement"
    ]
    orders_rows = [
        ["ORD-1001", "P-ENG-01", "Exhaust Manifold Assembly", "Apex Automotive GmbH", 150, 4, "06:00", 120, "IN_PRODUCTION", "RM-001", 0.98],
        ["ORD-1002", "P-AERO-02", "Turbine Impeller Core", "AeroDynamic Power Inc", 80, 5, "06:00", 95, "IN_PRODUCTION", "RM-003", 0.99],
        ["ORD-1003", "P-HYD-03", "Hydraulic Valve Body", "Krupp Heavy Motion", 220, 3, "06:00", 150, "QUEUED", "RM-002", 0.97],
        ["ORD-1004", "P-ENG-04", "Precision Drive Shaft", "Veloce Powertrain Ltd", 95, 4, "06:00", 110, "IN_PRODUCTION", "RM-001", 0.98],
        ["ORD-1005", "P-ROB-05", "Planetary Gearbox Housing", "Nordic Robotic Systems", 60, 2, "06:00", 180, "QUEUED", "RM-002", 0.96],
        ["ORD-1006", "P-HYD-06", "High-Pressure Cylinder Block", "Sulzer Fluid Dynamics", 110, 3, "06:00", 160, "QUEUED", "RM-003", 0.98],
        ["ORD-1007", "P-STR-07", "Chassis Mounting Bracket", "Scania Truck Logistics", 300, 3, "07:00", 175, "QUEUED", "RM-001", 0.95],
        ["ORD-1008", "P-TURB-08", "High-Speed Compressor Rotor", "General Aviation Corp", 45, 5, "06:30", 105, "IN_PRODUCTION", "RM-003", 0.99],
        ["ORD-1009", "P-VALV-09", "Cryogenic Relief Valve", "Air Liquide Industrial", 130, 4, "07:30", 165, "QUEUED", "RM-005", 0.98],
        ["ORD-1010", "P-ELEC-10", "Inverter Heat Sink Housing", "Tesla Energy Systems", 250, 3, "08:00", 190, "QUEUED", "RM-002", 0.96],
        ["ORD-1011", "P-ACT-11", "Linear Actuator Cylinder", "Festo Automation SE", 90, 4, "06:00", 135, "IN_PRODUCTION", "RM-001", 0.97],
        ["ORD-1012", "P-PUMP-12", "Boiler Feed Pump Impeller", "Siemens Energy AG", 70, 2, "09:00", 210, "QUEUED", "RM-002", 0.97],
    ]
    style_sheet(wb.create_sheet(title="Production_Orders"), orders_headers, orders_rows)

    # 5. Jobs
    jobs_headers = [
        "job_id", "order_id", "job_name", "product_id", "processing_time",
        "eligible_machines", "priority", "release_time", "deadline", "quantity",
        "status", "operation_sequence", "setup_time", "material_required", "quality_target"
    ]
    jobs_rows = [
        # Order 1001 (3 jobs)
        ["J01", "ORD-1001", "Manifold Rough Milling", "P-ENG-01", 24, "M01,M02", 4, 0, 80, 150, "pending", 1, 6, "RM-001", 0.98],
        ["J02", "ORD-1001", "Manifold Flange Stamping", "P-ENG-01", 18, "M03,M05", 4, 24, 100, 150, "pending", 2, 8, "RM-001", 0.98],
        ["J03", "ORD-1001", "Manifold Final Weld & Test", "P-ENG-01", 16, "M04,M06", 4, 42, 120, 150, "pending", 3, 5, "RM-006", 0.99],

        # Order 1002 (3 jobs)
        ["J04", "ORD-1002", "Titanium Impeller Wire EDM", "P-AERO-02", 32, "M07,M01", 5, 0, 60, 80, "pending", 1, 10, "RM-003", 0.99],
        ["J05", "ORD-1002", "Impeller 5-Axis Profiling", "P-AERO-02", 28, "M01,M05", 5, 32, 85, 80, "pending", 2, 8, "RM-003", 0.99],
        ["J06", "ORD-1002", "Impeller Micro-Crack Inspection", "P-AERO-02", 12, "M06", 5, 60, 95, 80, "pending", 3, 2, "NONE", 0.995],

        # Order 1003 (3 jobs)
        ["J07", "ORD-1003", "Valve Body Casting Rough Turn", "P-HYD-03", 30, "M03,M02,M05", 3, 0, 90, 220, "pending", 1, 10, "RM-002", 0.97],
        ["J08", "ORD-1003", "Bore Precision Grinding", "P-HYD-03", 22, "M05,M02", 3, 30, 125, 220, "pending", 2, 6, "RM-002", 0.98],
        ["J09", "ORD-1003", "Nitride Surface Hardening", "P-HYD-03", 25, "M08", 3, 52, 150, 220, "pending", 3, 15, "RM-008", 0.98],

        # Order 1004 (3 jobs)
        ["J10", "ORD-1004", "Drive Shaft Spline Milling", "P-ENG-04", 26, "M01,M02", 4, 0, 75, 95, "pending", 1, 8, "RM-001", 0.98],
        ["J11", "ORD-1004", "Shaft Induction Heat Treatment", "P-ENG-04", 20, "M08,M03", 4, 26, 95, 95, "pending", 2, 12, "RM-001", 0.98],
        ["J12", "ORD-1004", "Drive Shaft Polish & Balance", "P-ENG-04", 15, "M05,M09", 4, 46, 110, 95, "pending", 3, 4, "NONE", 0.99],

        # Order 1005 (3 jobs)
        ["J13", "ORD-1005", "Gearbox Housing CNC Milling", "P-ROB-05", 35, "M01,M02", 2, 0, 110, 60, "pending", 1, 10, "RM-002", 0.96],
        ["J14", "ORD-1005", "Housing Bearing Bore Lathe", "P-ROB-05", 24, "M02,M05", 2, 35, 145, 60, "pending", 2, 6, "RM-002", 0.97],
        ["J15", "ORD-1005", "Ultrasonic Clean & CMM Inspect", "P-ROB-05", 16, "M09,M06", 2, 59, 180, 60, "pending", 3, 4, "NONE", 0.98],

        # Order 1006 (3 jobs)
        ["J16", "ORD-1006", "Cylinder Heavy Forging Rough", "P-HYD-06", 28, "M03,M01", 3, 0, 100, 110, "pending", 1, 12, "RM-003", 0.97],
        ["J17", "ORD-1006", "Cylinder Internal Honing", "P-HYD-06", 20, "M05,M02", 3, 28, 130, 110, "pending", 2, 6, "RM-003", 0.98],
        ["J18", "ORD-1006", "Hydrostatic Pressure Testing", "P-HYD-06", 18, "M06,M04", 3, 48, 160, 110, "pending", 3, 5, "RM-007", 0.99],

        # Order 1007 (3 jobs)
        ["J19", "ORD-1007", "Bracket Heavy Stamping", "P-STR-07", 22, "M03,M01", 3, 10, 95, 300, "pending", 1, 8, "RM-001", 0.95],
        ["J20", "ORD-1007", "Bracket Robotic Gusset Weld", "P-STR-07", 25, "M04,M10", 3, 32, 135, 300, "pending", 2, 8, "RM-006", 0.96],
        ["J21", "ORD-1007", "Anti-Corrosion Wash & Coat", "P-STR-07", 18, "M09,M08", 3, 57, 175, 300, "pending", 3, 6, "RM-008", 0.97],

        # Order 1008 (3 jobs)
        ["J22", "ORD-1008", "Rotor Titanium Core Roughing", "P-TURB-08", 30, "M01,M07", 5, 5, 65, 45, "pending", 1, 10, "RM-003", 0.99],
        ["J23", "ORD-1008", "Rotor Micro-Finishing", "P-TURB-08", 22, "M05,M07", 5, 35, 90, 45, "pending", 2, 8, "RM-003", 0.995],
        ["J24", "ORD-1008", "Rotor Dynamic Spin Balance", "P-TURB-08", 12, "M06", 5, 57, 105, 45, "pending", 3, 4, "NONE", 0.999],

        # Order 1009 (3 jobs)
        ["J25", "ORD-1009", "Cryo Valve Body CNC Turn", "P-VALV-09", 26, "M02,M01", 4, 15, 95, 130, "pending", 1, 8, "RM-005", 0.98],
        ["J26", "ORD-1009", "Cryo Valve Seal Seat Grind", "P-VALV-09", 20, "M05,M07", 4, 41, 130, 130, "pending", 2, 6, "RM-005", 0.99],
        ["J27", "ORD-1009", "Liquid Nitrogen Leak Test", "P-VALV-09", 15, "M06,M09", 4, 61, 165, 130, "pending", 3, 5, "RM-007", 0.995],

        # Order 1010 (3 jobs)
        ["J28", "ORD-1010", "Alloy Heat Sink Stamping", "P-ELEC-10", 25, "M03,M01", 3, 20, 105, 250, "pending", 1, 10, "RM-002", 0.96],
        ["J29", "ORD-1010", "Fin Milling & Slotting", "P-ELEC-10", 28, "M01,M02", 3, 45, 150, 250, "pending", 2, 8, "RM-002", 0.97],
        ["J30", "ORD-1010", "Anodize Surface Treatment", "P-ELEC-10", 20, "M09,M08", 3, 73, 190, 250, "pending", 3, 6, "RM-008", 0.98],

        # Order 1011 (3 jobs)
        ["J31", "ORD-1011", "Actuator Barrel Precision Turn", "P-ACT-11", 24, "M02,M01", 4, 0, 75, 90, "pending", 1, 6, "RM-001", 0.97],
        ["J32", "ORD-1011", "Piston Rod Plasma Spray", "P-ACT-11", 22, "M08,M04", 4, 24, 105, 90, "pending", 2, 10, "RM-008", 0.98],
        ["J33", "ORD-1011", "Seal Assembly & Stroke Test", "P-ACT-11", 16, "M10,M06", 4, 46, 135, 90, "pending", 3, 4, "RM-007", 0.99],

        # Order 1012 (3 jobs)
        ["J34", "ORD-1012", "Pump Impeller Casting Mill", "P-PUMP-12", 30, "M01,M02", 2, 30, 135, 70, "pending", 1, 8, "RM-002", 0.97],
        ["J35", "ORD-1012", "Shroud Tig Welding", "P-PUMP-12", 24, "M04,M10", 2, 60, 175, 70, "pending", 2, 8, "RM-006", 0.97],
        ["J36", "ORD-1012", "Final Clean & Laser Mark", "P-PUMP-12", 14, "M09,M06", 2, 84, 210, 70, "pending", 3, 3, "NONE", 0.99],
    ]
    style_sheet(wb.create_sheet(title="Jobs"), jobs_headers, jobs_rows)

    # 6. Operations
    ops_headers = [
        "operation_id", "job_id", "operation_sequence", "operation_name",
        "processing_time", "eligible_machines", "setup_time", "material_required",
        "quantity", "precedence", "quality_requirement"
    ]
    ops_rows = []
    for j in jobs_rows:
        j_id = j[0]
        ops_rows.append([
            f"OP-{j_id}-01", j_id, 1, f"{j[2]} Phase 1",
            round(j[4] * 0.6), j[5], round(j[12] * 0.7), j[13], j[9], "NONE", j[14]
        ])
        ops_rows.append([
            f"OP-{j_id}-02", j_id, 2, f"{j[2]} Phase 2",
            round(j[4] * 0.4), j[5], round(j[12] * 0.3), "NONE", j[9], f"OP-{j_id}-01", j[14]
        ])
    style_sheet(wb.create_sheet(title="Operations"), ops_headers, ops_rows)

    # 7. Materials
    mat_headers = [
        "material_id", "material_name", "material_type", "unit",
        "standard_cost", "supplier", "lead_time_hours", "quality_grade"
    ]
    mat_rows = [
        ["RM-001", "Cold-Rolled Structural Steel 4140", "RAW_MATERIAL", "kg", 18.50, "Voestalpine AG", 24, "A+"],
        ["RM-002", "Aerospace Aluminum Billet 6061-T6", "RAW_MATERIAL", "kg", 24.80, "Constellium SE", 36, "A"],
        ["RM-003", "Titanium Alloy Ingot Ti-6Al-4V", "RAW_MATERIAL", "kg", 145.00, "TIMET Aerospace", 72, "A++"],
        ["RM-004", "Engineering Polymer POM-C Acetal", "RAW_MATERIAL", "kg", 14.20, "Quadrant Plastics", 24, "A"],
        ["RM-005", "High-Purity Copper Rod Cu-ETP", "RAW_MATERIAL", "kg", 32.50, "Aurubis AG", 48, "A+"],
        ["RM-006", "High-Tensile Fasteners M8x35 Gr 8.8", "COMPONENT", "units", 0.95, "Wurth Industry", 12, "A"],
        ["RM-007", "Fluorocarbon Hydraulic O-Rings", "COMPONENT", "units", 4.20, "Freudenberg Sealing", 18, "A+"],
        ["RM-008", "Hard-Chrome Surface Plating Fluid", "CHEMICAL", "liters", 55.00, "Atotech International", 48, "A"],
        ["RM-009", "MEMS Pressure Sensor Micro-Chip", "ELECTRONIC", "units", 48.00, "Bosch Sensortec", 96, "A++"],
        ["RM-010", "Export Grade Corrugated Crates", "PACKAGING", "units", 12.00, "Mondi Packaging", 8, "B+"],
    ]
    style_sheet(wb.create_sheet(title="Materials"), mat_headers, mat_rows)

    # 8. Inventory
    inv_headers = [
        "material_id", "material_name", "unit", "available_quantity", "reserved_quantity",
        "incoming_quantity", "reorder_level", "safety_stock", "lead_time_hours", "supplier", "status"
    ]
    inv_rows = [
        ["RM-001", "Cold-Rolled Structural Steel 4140", "kg", 3200, 1850, 1500, 1000, 500, 24, "Voestalpine AG", "IN_STOCK"],
        ["RM-002", "Aerospace Aluminum Billet 6061-T6", "kg", 1450, 980, 800, 500, 250, 36, "Constellium SE", "IN_STOCK"],
        ["RM-003", "Titanium Alloy Ingot Ti-6Al-4V", "kg", 165, 140, 120, 100, 50, 72, "TIMET Aerospace", "LOW_STOCK"],
        ["RM-004", "Engineering Polymer POM-C Acetal", "kg", 450, 180, 300, 150, 75, 24, "Quadrant Plastics", "IN_STOCK"],
        ["RM-005", "High-Purity Copper Rod Cu-ETP", "kg", 240, 220, 200, 120, 60, 48, "Aurubis AG", "LOW_STOCK"],
        ["RM-006", "High-Tensile Fasteners M8x35 Gr 8.8", "units", 5800, 3200, 4000, 2000, 1000, 12, "Wurth Industry", "IN_STOCK"],
        ["RM-007", "Fluorocarbon Hydraulic O-Rings", "units", 820, 650, 500, 400, 200, 18, "Freudenberg Sealing", "IN_STOCK"],
        ["RM-008", "Hard-Chrome Surface Plating Fluid", "liters", 320, 190, 250, 100, 50, 48, "Atotech International", "IN_STOCK"],
        ["RM-009", "MEMS Pressure Sensor Micro-Chip", "units", 95, 80, 100, 60, 30, 96, "Bosch Sensortec", "LOW_STOCK"],
        ["RM-010", "Export Grade Corrugated Crates", "units", 600, 250, 400, 200, 100, 8, "Mondi Packaging", "IN_STOCK"],
    ]
    style_sheet(wb.create_sheet(title="Inventory"), inv_headers, inv_rows)

    # 9. Maintenance
    maint_headers = [
        "maintenance_id", "machine_id", "maintenance_type", "scheduled_start",
        "scheduled_end", "duration_minutes", "maintenance_priority", "reason", "status"
    ]
    maint_rows = [
        ["MNT-01", "M04", "PREVENTIVE", "12:00", "13:30", 90, "HIGH", "Robotic torch liner replacement and calibration", "SCHEDULED"],
        ["MNT-02", "M08", "INSPECTION", "14:00", "15:00", 60, "MEDIUM", "Thermocouple recalibration and vacuum seal inspection", "SCHEDULED"],
        ["MNT-03", "M03", "CORRECTIVE", "18:00", "20:00", 120, "CRITICAL", "Hydraulic proportional valve pressure rebuild", "SCHEDULED"],
        ["MNT-04", "M01", "PREVENTIVE", "21:00", "22:00", 60, "LOW", "Coolant filtration flushing and way-lube replenishment", "SCHEDULED"],
        ["MNT-05", "M05", "PREVENTIVE", "16:30", "17:30", 60, "MEDIUM", "Spindle run-out test and diamond dresser dressing", "COMPLETED"],
    ]
    style_sheet(wb.create_sheet(title="Maintenance"), maint_headers, maint_rows)

    # 10. Downtime
    down_headers = [
        "downtime_id", "machine_id", "start_time", "end_time",
        "duration_minutes", "downtime_type", "reason", "planned", "impact_level"
    ]
    down_rows = [
        ["DWN-01", "M03", "08:15", "08:45", 30, "UNPLANNED", "Hydraulic pressure sensor fault", "FALSE", "HIGH"],
        ["DWN-02", "M05", "10:00", "10:20", 20, "SETUP", "Tool changeover for P-HYD-03", "TRUE", "LOW"],
        ["DWN-03", "M01", "11:30", "11:45", 15, "SETUP", "Part fixture realignment", "TRUE", "LOW"],
        ["DWN-04", "M04", "12:00", "13:30", 90, "MAINTENANCE", "Scheduled torch replacement", "TRUE", "MEDIUM"],
        ["DWN-05", "M08", "14:00", "15:00", 60, "MAINTENANCE", "Thermocouple calibration", "TRUE", "MEDIUM"],
    ]
    style_sheet(wb.create_sheet(title="Downtime"), down_headers, down_rows)

    # 11. Energy
    energy_headers = ["energy_id", "machine_id", "timestamp", "power_kw", "energy_kwh", "operating_state", "job_id"]
    energy_rows = [
        ["ENG-01", "M01", "08:00", 8.2, 8.2, "RUNNING", "J01"],
        ["ENG-02", "M02", "08:00", 9.1, 9.1, "RUNNING", "J10"],
        ["ENG-03", "M03", "08:00", 14.8, 14.8, "RUNNING", "J07"],
        ["ENG-04", "M04", "08:00", 6.8, 6.8, "RUNNING", "J03"],
        ["ENG-05", "M05", "08:00", 6.5, 6.5, "RUNNING", "J08"],
        ["ENG-06", "M06", "08:00", 3.0, 3.0, "RUNNING", "J06"],
        ["ENG-07", "M07", "08:00", 5.2, 5.2, "RUNNING", "J04"],
        ["ENG-08", "M08", "08:00", 17.5, 17.5, "RUNNING", "J09"],
        ["ENG-09", "M09", "08:00", 3.8, 3.8, "RUNNING", "J15"],
        ["ENG-10", "M10", "08:00", 4.6, 4.6, "RUNNING", "J33"],
        ["ENG-11", "M03", "09:00", 3.8, 3.8, "IDLE", "NONE"],
        ["ENG-12", "M08", "09:00", 4.5, 4.5, "IDLE", "NONE"],
    ]
    style_sheet(wb.create_sheet(title="Energy"), energy_headers, energy_rows)

    # 12. Quality
    qual_headers = [
        "inspection_id", "job_id", "operation_id", "machine_id",
        "quantity_produced", "quantity_rejected", "defect_rate", "quality_score", "inspection_time"
    ]
    qual_rows = [
        ["QC-01", "J01", "OP-J01-01", "M01", 150, 1, 0.0067, 0.993, "08:45"],
        ["QC-02", "J04", "OP-J04-01", "M07", 80, 0, 0.0000, 1.000, "09:10"],
        ["QC-03", "J07", "OP-J07-01", "M03", 220, 4, 0.0182, 0.982, "09:40"],
        ["QC-04", "J10", "OP-J10-01", "M02", 95, 1, 0.0105, 0.989, "10:15"],
        ["QC-05", "J13", "OP-J13-01", "M01", 60, 0, 0.0000, 1.000, "11:00"],
    ]
    style_sheet(wb.create_sheet(title="Quality"), qual_headers, qual_rows)

    # 13. Shifts
    shift_headers = ["shift_id", "shift_name", "start_time", "end_time", "working_hours", "available_machine_count"]
    shift_rows = [
        ["SHIFT-1", "Morning Shift (Core)", "06:00", "14:00", 8, 10],
        ["SHIFT-2", "Evening Shift (Machining & Assembly)", "14:00", "22:00", 8, 10],
        ["SHIFT-3", "Night Shift (Automated EDM & Furnaces)", "22:00", "06:00", 8, 4],
    ]
    style_sheet(wb.create_sheet(title="Shifts"), shift_headers, shift_rows)

    # 14. Dependencies
    dep_headers = ["dependency_id", "job_id", "depends_on_job_id", "dependency_type", "minimum_gap_minutes"]
    dep_rows = [
        ["DEP-01", "J02", "J01", "PRECEDENCE", 5],
        ["DEP-02", "J03", "J02", "PRECEDENCE", 5],
        ["DEP-03", "J05", "J04", "PRECEDENCE", 10],
        ["DEP-04", "J06", "J05", "PRECEDENCE", 5],
        ["DEP-05", "J08", "J07", "PRECEDENCE", 5],
        ["DEP-06", "J09", "J08", "PRECEDENCE", 10],
        ["DEP-07", "J11", "J10", "PRECEDENCE", 5],
        ["DEP-08", "J12", "J11", "PRECEDENCE", 5],
        ["DEP-09", "J14", "J13", "PRECEDENCE", 5],
        ["DEP-10", "J15", "J14", "PRECEDENCE", 5],
        ["DEP-11", "J17", "J16", "PRECEDENCE", 5],
        ["DEP-12", "J18", "J17", "PRECEDENCE", 5],
    ]
    style_sheet(wb.create_sheet(title="Dependencies"), dep_headers, dep_rows)

    # 15. Disruptions
    disrupt_headers = [
        "disruption_id", "type", "target_id", "timestamp", "value",
        "severity", "duration", "description"
    ]
    disrupt_rows = [
        ["D01", "machine_failure", "M03", "10:42", None, "HIGH", 120, "M03 Stamping Press hydraulic pressure failure"],
        ["D02", "urgent_job", "J99", "11:15", 35, "CRITICAL", 35, "Rush customer replacement batch for Siemens"],
        ["D03", "deadline_change", "J01", "11:30", 60, "HIGH", None, "Expedited shipment requested by Apex Automotive"],
        ["D04", "job_cancellation", "J15", "12:00", None, "LOW", None, "Customer cancelled secondary inspection step"],
        ["D05", "machine_downtime", "M04", "12:30", 90, "MEDIUM", 90, "Planned robotic torch overhaul"],
        ["D06", "multiple_failure", "M03,M05", "13:00", None, "CRITICAL", 180, "Cascading electrical power feed outage Bay A"],
        ["D07", "material_shortage", "RM-003", "13:30", 0, "HIGH", 240, "Supplier shipment delayed: Titanium Rod Ti-6Al-4V"],
        ["D08", "quality_issue", "M02", "14:00", 0.82, "HIGH", 120, "Spindle thermal drift causing bore out-of-tolerance"],
        ["D09", "energy_constraint", "FACTORY", "14:30", 65.0, "MEDIUM", 180, "Peak grid demand tariff constraint (max 65 kW)"],
        ["D10", "machine_recovery", "M03", "15:30", None, "NOMINAL", None, "M03 hydraulic rebuild complete, returned to service"],
    ]
    style_sheet(wb.create_sheet(title="Disruptions"), disrupt_headers, disrupt_rows)

    # 16. Scenarios (Predefined 10 Industrial Scenarios on Common Factory)
    scen_headers = [
        "scenario_id", "scenario_name", "category", "target_id", "trigger_type",
        "expected_action", "business_impact"
    ]
    scen_rows = [
        [1, "Normal Production", "Baseline", "ALL", "nominal", "Optimize baseline schedule across 10 machines", "Nominal makespan, minimum energy, zero tardiness"],
        [2, "Single Machine Failure", "Unplanned Disruption", "M03", "machine_failure", "Reroute stamping jobs J02, J07, J16 to M01/M05", "Protects ORD-1001 & ORD-1003 deadlines"],
        [3, "Multiple Machine Failure", "Severe Outage", "M03,M05", "multiple_failure", "Dynamic multi-station load redistribution to M01, M02, M07", "Cascading resilience recovery from 42 to 78 pts"],
        [4, "Urgent Customer Order", "Rush Demand", "J99", "urgent_job", "Insert 35m rush order without delaying active orders", "Protects existing delivery commitments"],
        [5, "Deadline Change", "Schedule Acceleration", "J01", "deadline_change", "Compress J01 schedule window from 80m to 60m", "Guarantees Tier-1 automotive customer SLA"],
        [6, "Job Cancellation", "Capacity Release", "J15", "job_cancellation", "Remove J15 from schedule and shift downstream operations", "Frees 16 min capacity on M09 and advances J21"],
        [7, "Planned Maintenance", "Preventive Maintenance", "M04", "planned_downtime", "Schedule around 90-min maintenance window on M04", "Eliminates unexpected breakdown risk during assembly"],
        [8, "Material Shortage", "Supply Chain Disruption", "RM-003", "material_shortage", "Flag titanium jobs J04, J05, J16; prioritize feasible steel orders", "Prevents shop floor starvation and idle machine time"],
        [9, "Quality Calibration Drift", "Defect Mitigation", "M02", "quality_issue", "Reroute tight-tolerance jobs J10, J14 away from M02", "Prevents scrap rate increase on expensive alloys"],
        [10, "Peak Energy Constraint", "Energy Optimization", "FACTORY", "energy_constraint", "Interleave high-draw stations (M03, M08) to cap load at 65 kW", "Reduces peak utility demand charges by 18%"],
    ]
    style_sheet(wb.create_sheet(title="Scenarios"), scen_headers, scen_rows)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    wb.save(filepath)
    print(f"Successfully generated industrial factory workbook: {filepath}")
    print(f"Sheets created ({len(wb.sheetnames)}): {', '.join(wb.sheetnames)}")

if __name__ == "__main__":
    create_industrial_workbook()
