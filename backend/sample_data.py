from __future__ import annotations

from dataclasses import asdict
from math import hypot
from typing import Dict, List

from .models import Customer, Order, Warehouse


WAREHOUSE_SPECS = [
    {"id": "WH-CA1", "name": "Warehouse CA-01", "stock": 100},
    {"id": "WH-GZ2", "name": "Warehouse GZ-02", "stock": 100},
    {"id": "WH-AL3", "name": "Warehouse QU-03", "stock": 100},
]

CUSTOMER_SPECS = [
    {"id": "C1", "name": "Nike", "region": "Retail"},
    {"id": "C2", "name": "Adidas", "region": "Retail"},
    {"id": "C3", "name": "Zara", "region": "Retail"},
    {"id": "C4", "name": "H&M", "region": "Retail"},
    {"id": "C5", "name": "Puma", "region": "Retail"},
]

ORDERS = [
    Order(id="O1", customer_id="C1", weight=1.0, volume=1.0),
    Order(id="O2", customer_id="C2", weight=1.5, volume=1.2),
    Order(id="O3", customer_id="C3", weight=2.0, volume=1.5),
    Order(id="O4", customer_id="C4", weight=1.0, volume=0.8),
    Order(id="O5", customer_id="C5", weight=1.2, volume=1.0),
]


def _node_dict(node, node_type: str, x: int, y: int) -> Dict[str, object]:
    data = asdict(node)
    data["type"] = node_type
    data["coordinate_x"] = data["x"]
    data["coordinate_y"] = data["y"]
    data["x"] = x
    data["y"] = y
    data["coordinate_x"] = x
    data["coordinate_y"] = y
    return data


def _auto_positions(count: int, start_x: int = 10, start_y: int = 10, step: int = 30) -> List[tuple[int, int]]:
    positions = []
    x = start_x
    y = start_y
    for _ in range(count):
        positions.append((x, y))
        x += step
        if x > 240:
            x = start_x
            y = min(270, y + step)
    return positions


def _distance(source: Dict[str, object], target: Dict[str, object]) -> float:
    return hypot(float(source["x"]) - float(target["x"]), float(source["y"]) - float(target["y"]))


def build_sample_scenario() -> Dict[str, object]:
    warehouse_positions = _auto_positions(len(WAREHOUSE_SPECS), start_x=10, start_y=80)
    customer_positions = _auto_positions(len(CUSTOMER_SPECS), start_x=20, start_y=70)
    warehouses = [
        _node_dict(Warehouse(**spec, x=position[0], y=position[1]), "warehouse", position[0], position[1])
        for spec, position in zip(WAREHOUSE_SPECS, warehouse_positions)
    ]
    customers = [
        _node_dict(Customer(**spec, x=position[0], y=position[1]), "customer", position[0], position[1])
        for spec, position in zip(CUSTOMER_SPECS, customer_positions)
    ]

    return {
        "warehouses": warehouses,
        "customers": customers,
        "orders": [asdict(order) for order in ORDERS],
        "settings": {
            "weight_capacity": 3.0,
            "volume_capacity": 3.0,
            "base_time": "09:00 AM",
        },
        "distance_hint": round(_distance(warehouses[0], customers[0]), 2),
    }
