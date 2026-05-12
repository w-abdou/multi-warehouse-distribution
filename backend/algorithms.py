from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from datetime import datetime, timedelta
from math import ceil, hypot, inf
from typing import Dict, List, Sequence, Tuple


def _coordinate(node: Dict[str, object], key: str) -> float:
    alias = f"coordinate_{key}"
    if alias in node:
        return float(node[alias])
    return float(node[key])


def _distance(left: Dict[str, object], right: Dict[str, object]) -> float:
    return hypot(_coordinate(left, "x") - _coordinate(right, "x"), _coordinate(left, "y") - _coordinate(right, "y"))


def _route_metrics(warehouse: Dict[str, object], customer: Dict[str, object]) -> Dict[str, float]:
    distance = _distance(warehouse, customer)
    shipping_cost = round(2.0 + distance * 0.45, 2)
    delivery_time = round(0.5 + distance * 0.08, 2)
    return {
        "distance": round(distance, 2),
        "shipping_cost": shipping_cost,
        "delivery_time": delivery_time,
    }


def _lookup(items: Sequence[Dict[str, object]]) -> Dict[str, Dict[str, object]]:
    return {item["id"]: item for item in items}


def _format_clock_time(base_time: str, hours: float) -> str:
    start = datetime.strptime(base_time, "%I:%M %p")
    finish = start + timedelta(hours=float(hours))
    return finish.strftime("%I:%M %p")


def _best_exact_assignment(
    orders: Sequence[Dict[str, object]],
    warehouses: Sequence[Dict[str, object]],
) -> Tuple[float, Tuple[int, ...]]:
    initial_stock = tuple(int(warehouse["stock"]) for warehouse in warehouses)

    @lru_cache(maxsize=None)
    def solve(order_index: int, remaining: Tuple[int, ...]) -> Tuple[float, Tuple[int, ...]]:
        if order_index == len(orders):
            return 0.0, ()

        order = orders[order_index]
        customer = order["customer"]
        best_cost = inf
        best_plan: Tuple[int, ...] = ()

        for warehouse_index, warehouse in enumerate(warehouses):
            if remaining[warehouse_index] <= 0:
                continue
            route = _route_metrics(warehouse, customer)
            next_remaining = list(remaining)
            next_remaining[warehouse_index] -= 1
            tail_cost, tail_plan = solve(order_index + 1, tuple(next_remaining))
            candidate = route["shipping_cost"] + tail_cost
            if candidate < best_cost:
                best_cost = candidate
                best_plan = (warehouse_index,) + tail_plan

        return best_cost, best_plan

    return solve(0, initial_stock)


def _build_assignment_rows(
    orders: Sequence[Dict[str, object]],
    warehouses: Sequence[Dict[str, object]],
    plan: Sequence[int],
    base_time: str,
) -> Tuple[List[Dict[str, object]], Dict[str, int], float]:
    warehouse_lookup = _lookup(warehouses)
    remaining_stock = {warehouse["id"]: int(warehouse["stock"]) for warehouse in warehouses}
    assignments: List[Dict[str, object]] = []
    total_cost = 0.0
    total_time = 0.0

    for order, warehouse_index in zip(orders, plan):
        warehouse = warehouses[warehouse_index]
        route = _route_metrics(warehouse, order["customer"])
        remaining_stock[warehouse["id"]] -= 1
        total_cost += route["shipping_cost"]
        total_time += route["delivery_time"]
        assignments.append(
            {
                "order_id": order["id"],
                "customer_id": order["customer_id"],
                "customer_name": order["customer"]["name"],
                "region": order["customer"]["region"],
                "warehouse_id": warehouse["id"],
                "warehouse_name": warehouse_lookup[warehouse["id"]]["name"],
                "shipping_cost": route["shipping_cost"],
                "delivery_time": route["delivery_time"],
                "estimated_delivery_at": _format_clock_time(base_time, route["delivery_time"]),
                "distance": route["distance"],
                "consolidated": False,
            }
        )

    average_time = round(total_time / len(assignments), 2) if assignments else 0.0
    return assignments, remaining_stock, average_time


def _greedy_assignment(
    orders: Sequence[Dict[str, object]],
    warehouses: Sequence[Dict[str, object]],
    base_time: str,
) -> Dict[str, object]:
    warehouse_lookup = _lookup(warehouses)
    remaining_stock = {warehouse["id"]: int(warehouse["stock"]) for warehouse in warehouses}
    assignments: List[Dict[str, object]] = []
    total_cost = 0.0
    total_time = 0.0

    for order in orders:
        options = []
        for warehouse in warehouses:
            if remaining_stock[warehouse["id"]] <= 0:
                continue
            route = _route_metrics(warehouse, order["customer"])
            options.append((route["shipping_cost"], route["delivery_time"], warehouse, route))

        if not options:
            continue

        options.sort(key=lambda item: (item[0], item[1], item[2]["id"]))
        cost, delivery_time, warehouse, route = options[0]
        remaining_stock[warehouse["id"]] -= 1
        total_cost += cost
        total_time += delivery_time
        assignments.append(
            {
                "order_id": order["id"],
                "customer_id": order["customer_id"],
                "customer_name": order["customer"]["name"],
                "region": order["customer"]["region"],
                "warehouse_id": warehouse["id"],
                "warehouse_name": warehouse_lookup[warehouse["id"]]["name"],
                "shipping_cost": route["shipping_cost"],
                "delivery_time": route["delivery_time"],
                "estimated_delivery_at": _format_clock_time(base_time, route["delivery_time"]),
                "distance": route["distance"],
                "consolidated": False,
            }
        )

    average_time = round(total_time / len(assignments), 2) if assignments else 0.0
    return {
        "assignments": assignments,
        "total_cost": round(total_cost, 2),
        "average_delivery_time": average_time,
        "remaining_stock": remaining_stock,
    }


def _consolidate_shipments(
    assignments: Sequence[Dict[str, object]],
    orders: Sequence[Dict[str, object]],
    warehouses: Sequence[Dict[str, object]],
    weight_capacity: float,
    volume_capacity: float,
) -> Dict[str, object]:
    order_lookup = _lookup(orders)
    warehouse_lookup = _lookup(warehouses)

    grouped: Dict[Tuple[str, str], List[Dict[str, object]]] = defaultdict(list)
    for assignment in assignments:
        grouped[(assignment["warehouse_id"], assignment["region"])].append(assignment)

    shipment_manifests: List[Dict[str, object]] = []
    total_individual_cost = 0.0
    total_consolidated_cost = 0.0
    shipment_index = 1

    for (warehouse_id, region), group in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
        current_container: List[Dict[str, object]] = []
        current_weight = 0.0
        current_volume = 0.0

        def flush_container() -> None:
            nonlocal shipment_index, total_individual_cost, total_consolidated_cost
            if not current_container:
                return
            individual_cost = sum(float(item["shipping_cost"]) for item in current_container)
            total_weight = sum(float(order_lookup[item["order_id"]]["weight"]) for item in current_container)
            total_volume = sum(float(order_lookup[item["order_id"]]["volume"]) for item in current_container)
            consolidated_cost = round(max(float(item["shipping_cost"]) for item in current_container) + 0.2 * (len(current_container) - 1), 2)
            total_individual_cost += individual_cost
            total_consolidated_cost += consolidated_cost
            shipment_manifests.append(
                {
                    "shipment_id": f"S{shipment_index}",
                    "warehouse_name": warehouse_lookup[warehouse_id]["name"],
                    "region": region,
                    "order_ids": [item["order_id"] for item in current_container],
                    "total_weight": round(total_weight, 2),
                    "total_volume": round(total_volume, 2),
                    "individual_cost": round(individual_cost, 2),
                    "consolidated_cost": consolidated_cost,
                    "savings": round(individual_cost - consolidated_cost, 2),
                }
            )
            for item in current_container:
                item["consolidated"] = True
                item["shipment_id"] = f"S{shipment_index}"
            shipment_index += 1
            current_container.clear()

        for assignment in group:
            order = order_lookup[assignment["order_id"]]
            order_weight = float(order["weight"])
            order_volume = float(order["volume"])
            fits = current_weight + order_weight <= weight_capacity and current_volume + order_volume <= volume_capacity
            if current_container and not fits:
                flush_container()
                current_weight = 0.0
                current_volume = 0.0
            current_container.append(assignment)
            current_weight += order_weight
            current_volume += order_volume

        flush_container()

    total_weight = sum(float(order["weight"]) for order in orders)
    total_volume = sum(float(order["volume"]) for order in orders)
    theoretical_min = max(ceil(total_weight / weight_capacity), ceil(total_volume / volume_capacity))

    return {
        "shipment_manifests": shipment_manifests,
        "individual_total_cost": round(total_individual_cost, 2),
        "consolidated_total_cost": round(total_consolidated_cost, 2),
        "shipment_count": len(shipment_manifests),
        "theoretical_min_shipments": theoretical_min,
        "savings": round(total_individual_cost - total_consolidated_cost, 2),
    }


def _build_mst_edges(warehouses: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    if len(warehouses) < 2:
        return []

    edges: List[Tuple[float, Dict[str, object]]] = []
    for index, left in enumerate(warehouses):
        for right in warehouses[index + 1 :]:
            distance = _distance(left, right)
            cost = round(1.5 + distance * 0.3, 2)
            edges.append(
                (
                    cost,
                    {
                        "source": left["id"],
                        "target": right["id"],
                        "cost": cost,
                    },
                )
            )

    edges.sort(key=lambda item: (item[0], item[1]["source"], item[1]["target"]))
    parent = {warehouse["id"]: warehouse["id"] for warehouse in warehouses}

    def find(node_id: str) -> str:
        while parent[node_id] != node_id:
            parent[node_id] = parent[parent[node_id]]
            node_id = parent[node_id]
        return node_id

    mst_edges: List[Dict[str, object]] = []
    for cost, edge in edges:
        left_root = find(edge["source"])
        right_root = find(edge["target"])
        if left_root == right_root:
            continue
        parent[right_root] = left_root
        mst_edges.append(edge)
        if len(mst_edges) == len(warehouses) - 1:
            break

    return mst_edges


def analyze_scenario(
    scenario: Dict[str, object],
    batch_size: int | None = None,
    weight_capacity: float | None = None,
    volume_capacity: float | None = None,
) -> Dict[str, object]:
    warehouses = [dict(warehouse) for warehouse in scenario["warehouses"]]
    customers = [dict(customer) for customer in scenario["customers"]]
    orders = [dict(order) for order in scenario["orders"]]

    customer_lookup = _lookup(customers)
    for order in orders:
        order["customer"] = customer_lookup[order["customer_id"]]

    if batch_size is not None:
        orders = orders[: max(1, min(int(batch_size), len(orders)))]
    if weight_capacity is None:
        weight_capacity = float(scenario["settings"]["weight_capacity"])
    if volume_capacity is None:
        volume_capacity = float(scenario["settings"]["volume_capacity"])
    base_time = str(scenario["settings"].get("base_time", "09:00 AM"))

    exact_cost, exact_plan = _best_exact_assignment(orders, warehouses)
    exact_assignments, exact_remaining_stock, exact_average_time = _build_assignment_rows(orders, warehouses, exact_plan, base_time)
    greedy_result = _greedy_assignment(orders, warehouses, base_time)
    shipment_result = _consolidate_shipments(exact_assignments, orders, warehouses, weight_capacity, volume_capacity)
    mst_edges = _build_mst_edges(warehouses)

    exact_cost = round(exact_cost, 2)
    greedy_cost = round(float(greedy_result["total_cost"]), 2)
    exact_average_clock = _format_clock_time(base_time, exact_average_time)
    greedy_average_clock = _format_clock_time(base_time, greedy_result["average_delivery_time"])

    return {
        "scenario": {
            "warehouses": warehouses,
            "customers": customers,
            "orders": orders,
        },
        "exact": {
            "assignments": exact_assignments,
            "total_cost": exact_cost,
            "average_delivery_time": exact_average_time,
            "remaining_stock": exact_remaining_stock,
        },
        "greedy": greedy_result,
        "shipments": shipment_result,
        "mst": {
            "edges": mst_edges,
        },
        "summary": {
            "orders_processed": len(orders),
            "warehouses_used": len(warehouses),
            "exact_total_cost": exact_cost,
            "greedy_total_cost": greedy_cost,
            "cost_difference": round(greedy_cost - exact_cost, 2),
            "cost_reduction_pct": round(((greedy_cost - exact_cost) / greedy_cost * 100) if greedy_cost else 0.0, 2),
            "exact_average_delivery_time": exact_average_time,
            "exact_average_delivery_clock": exact_average_clock,
            "greedy_average_delivery_time": greedy_result["average_delivery_time"],
            "greedy_average_delivery_clock": greedy_average_clock,
            "shipment_count": shipment_result["shipment_count"],
            "theoretical_min_shipments": shipment_result["theoretical_min_shipments"],
            "consolidated_total_cost": shipment_result["consolidated_total_cost"],
            "individual_shipment_cost": shipment_result["individual_total_cost"],
            "remaining_stock": exact_remaining_stock,
        },
    }
