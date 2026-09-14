"""
ERP-Lite Data Models for FlowForge Manufacturing Operations.

Defines Production Orders, Inventory Items, and Maintenance Records
that integrate directly with FactoryState and the Genetic Algorithm scheduler.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any


@dataclass
class ProductionOrder:
    order_id: str
    product_name: str
    customer: str
    quantity: int
    priority: int  # 1 (lowest) to 5 (highest/rush)
    deadline: int  # minutes or timeline hours
    status: str  # "In Production", "Queued", "Completed", "At Risk", "Delayed"
    progress: int  # 0 to 100 percentage
    risk_level: str  # "Low", "Medium", "High", "Critical"
    job_ids: List[str] = field(default_factory=list)
    required_materials: Dict[str, int] = field(default_factory=dict)  # {part_id: required_qty}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InventoryItem:
    part_id: str
    part_name: str
    category: str  # "Raw Material", "Component", "Fastener"
    available_qty: int
    reserved_qty: int
    incoming_qty: int
    reorder_level: int
    unit: str  # "sheets", "kg", "units", "meters"
    unit_cost: float
    status: str = "IN STOCK"  # "IN STOCK", "LOW STOCK", "OUT OF STOCK"
    at_risk_orders: List[str] = field(default_factory=list)

    def calculate_status(self) -> str:
        net_available = self.available_qty - self.reserved_qty
        if net_available <= 0:
            self.status = "OUT OF STOCK"
        elif net_available <= self.reorder_level:
            self.status = "LOW STOCK"
        else:
            self.status = "IN STOCK"
        return self.status

    def to_dict(self) -> Dict[str, Any]:
        self.calculate_status()
        d = asdict(self)
        d["available_quantity"] = self.available_qty
        d["reserved_quantity"] = self.reserved_qty
        d["incoming_quantity"] = self.incoming_qty
        return d


@dataclass
class MaintenanceRecord:
    machine_id: str
    machine_name: str
    health_score: int  # 0 to 100
    status: str  # "RUNNING", "IDLE", "MAINTENANCE", "FAILED", "STOPPED"
    last_maintenance: str
    next_maintenance: str
    runtime_hours: float
    downtime_minutes: int
    scheduled_window: List[int] = field(default_factory=list)  # [start_min, end_min]
    active_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["last_maintenance_date"] = self.last_maintenance
        d["next_maintenance_date"] = self.next_maintenance
        return d
