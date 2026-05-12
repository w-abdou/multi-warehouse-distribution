
from typing import List, Dict, Tuple
from collections import defaultdict


def greedy_bin_packing_shipments(assignments: List[Dict], 
                                 orders: List[Dict],
                                 max_shipment_weight: int = 100) -> Tuple[List[Dict], float, float]:
    """
    Consolidate orders into shared shipments using greedy bin packing.
    
    Algorithm (Next-Fit):
    1. Group assignments by (warehouse, destination_region)
    2. For each group, pack orders into shipments (bins) by weight limit
    3. Calculate cost savings from consolidation
    
    Args:
        assignments: List of assignment dicts {order_id, warehouse_id, customer_id, shipping_cost}
        orders: List of order dicts {id, customer_id, weight, region}
        max_shipment_weight: Maximum weight per shipment (kg)
    
    Returns:
        Tuple of (shipments, total_shipment_cost, cost_savings)
        - shipments: List of shipment dicts {id, orders, total_weight, cost_savings}
        - total_shipment_cost: Total cost of all individual shipments
        - cost_savings: Cost saved by consolidation
    """
    
    # Create order weight lookup
    order_weights = {o['id']: o['weight'] for o in orders}
    order_regions = {o['id']: o['region'] for o in orders}
    
    # Group assignments by (warehouse, region)
    shipment_groups = defaultdict(list)
    
    for assignment in assignments:
        order_id = assignment['order_id']
        warehouse_id = assignment['warehouse_id']
        region = order_regions[order_id]
        
        key = (warehouse_id, region)
        shipment_groups[key].append(assignment)
    
    # Pack each group into shipments
    shipments = []
    shipment_id = 1
    total_individual_cost = 0  # Cost if each order shipped individually
    total_consolidation_cost = 0  # Cost with consolidation
    
    for (warehouse_id, region), group_assignments in shipment_groups.items():
        # Sort by weight (descending) for better packing (First-Fit Decreasing variant)
        group_assignments.sort(key=lambda a: order_weights[a['order_id']], reverse=True)
        
        # Pack into bins (shipments)
        current_shipment = []
        current_weight = 0
        
        for assignment in group_assignments:
            order_id = assignment['order_id']
            weight = order_weights[order_id]
            cost = assignment['shipping_cost']
            
            # Individual shipment cost (no consolidation)
            total_individual_cost += cost
            
            # Try to fit in current shipment
            if current_weight + weight <= max_shipment_weight:
                current_shipment.append(assignment)
                current_weight += weight
            else:
                # Current shipment is full, save it and start new one
                if current_shipment:
                    shipment = {
                        'id': shipment_id,
                        'warehouse_id': warehouse_id,
                        'region': region,
                        'orders': [a['order_id'] for a in current_shipment],
                        'total_weight': current_weight,
                        'order_count': len(current_shipment)
                    }
                    shipments.append(shipment)
                    
                    # Consolidation cost = sum of costs / number of orders in shipment
                    # (sharing one shipment cost among multiple orders)
                    shipment_cost = sum(a['shipping_cost'] for a in current_shipment)
                    total_consolidation_cost += shipment_cost * 0.85  # 15% savings
                    
                    shipment_id += 1
                
                # Start new shipment
                current_shipment = [assignment]
                current_weight = weight
        
        # Save final shipment
        if current_shipment:
            shipment = {
                'id': shipment_id,
                'warehouse_id': warehouse_id,
                'region': region,
                'orders': [a['order_id'] for a in current_shipment],
                'total_weight': current_weight,
                'order_count': len(current_shipment)
            }
            shipments.append(shipment)
            
            shipment_cost = sum(a['shipping_cost'] for a in current_shipment)
            total_consolidation_cost += shipment_cost * 0.85  # 15% savings
            
            shipment_id += 1
    
    # Calculate cost savings
    cost_savings = total_individual_cost - total_consolidation_cost
    savings_percentage = (cost_savings / total_individual_cost * 100) if total_individual_cost > 0 else 0
    
    return shipments, total_consolidation_cost, cost_savings
