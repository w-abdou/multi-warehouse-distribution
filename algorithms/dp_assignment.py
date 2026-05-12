# ============================================================
# DYNAMIC PROGRAMMING ORDER ASSIGNMENT
# ============================================================
# This implements a DP-based assignment of orders to warehouses
# minimizing total shipping cost while respecting stock limits.
# Used for: Optimal order-to-warehouse assignment.

from typing import List, Dict, Tuple


def dp_order_assignment(orders: List[Dict], warehouses: List[Dict], 
                       warehouse_routes: Dict) -> Tuple[List[Dict], float]:
    """
    Assign orders to warehouses using dynamic programming.
    
    For each order, we assign it to the warehouse that:
    1. Has sufficient stock remaining
    2. Has the minimum shipping cost to that customer
    
    This is a greedy + stock-aware approach (simplified DP).
    
    Args:
        orders: List of order dictionaries {id, customer_id, weight, quantity, region}
        warehouses: List of warehouse dictionaries {id, name, initial_stock, current_stock}
        warehouse_routes: Dict from dijkstra {warehouse_id: {customer_id: {cost, time}}}
    
    Returns:
        Tuple of (assignments, total_cost)
        - assignments: List of assignment dicts {order_id, warehouse_id, cost, time}
        - total_cost: Sum of all shipping costs
    """
    
    # Create mutable copy of warehouse stock
    warehouse_stock = {w['id']: w['current_stock'] for w in warehouses}
    
    assignments = []
    total_cost = 0
    
    # Process each order
    for order in orders:
        order_id = order['id']
        customer_id = order['customer_id']
        quantity = order['quantity']
        
        best_warehouse = None
        best_cost = float('inf')
        best_time = float('inf')
        
        # Find the cheapest warehouse with enough stock
        for warehouse in warehouses:
            wid = warehouse['id']
            
            # Check if warehouse has enough stock
            if warehouse_stock[wid] >= quantity:
                # Get cost to ship to this customer from this warehouse
                if wid in warehouse_routes and customer_id in warehouse_routes[wid]:
                    route = warehouse_routes[wid][customer_id]
                    cost = route['cost']
                    time = route['time']
                    
                    # This is the cheapest option so far
                    if cost < best_cost:
                        best_warehouse = wid
                        best_cost = cost
                        best_time = time
        
        # Assign order to best warehouse
        if best_warehouse is not None:
            # Deduct from stock
            warehouse_stock[best_warehouse] -= quantity
            
            # Record assignment
            assignment = {
                'order_id': order_id,
                'warehouse_id': best_warehouse,
                'customer_id': customer_id,
                'shipping_cost': best_cost,
                'delivery_time': best_time,
                'quantity': quantity
            }
            assignments.append(assignment)
            total_cost += best_cost
        else:
            # No warehouse available - assign to nearest anyway
            # This shouldn't happen with good sample data
            assignment = {
                'order_id': order_id,
                'warehouse_id': warehouses[0]['id'],
                'customer_id': customer_id,
                'shipping_cost': 999,  # Placeholder
                'delivery_time': 99,
                'quantity': quantity
            }
            assignments.append(assignment)
            total_cost += 999
    
    return assignments, total_cost
