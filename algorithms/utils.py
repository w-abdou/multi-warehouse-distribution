import heapq
from typing import Dict, List, Tuple, Set


def build_adjacency_list(edges: List[Dict]) -> Dict:
    """
    Convert edge list to adjacency list representation.
    
    Args:
        edges: List of edge dictionaries with keys: source, destination, cost, delivery_time
    
    Returns:
        Dictionary mapping node -> list of (neighbor, cost, delivery_time)
    """
    graph = {}
    for edge in edges:
        src = edge['source']
        dest = edge['destination']
        cost = edge['cost']
        time = edge['delivery_time']
        
        if src not in graph:
            graph[src] = []
        graph[src].append({
            'neighbor': dest,
            'cost': cost,
            'time': time
        })
    
    return graph


def get_all_nodes(warehouses: List[Dict], customers: List[Dict]) -> Set[int]:
    """
    Get all node IDs (warehouse + customer).
    
    Args:
        warehouses: List of warehouse dictionaries
        customers: List of customer dictionaries
    
    Returns:
        Set of all node IDs
    """
    nodes = set()
    for w in warehouses:
        nodes.add(w['id'])
    for c in customers:
        nodes.add(c['id'] + 100)  # Customer IDs offset by 100 to avoid collision
    
    return nodes


def find_nearest_warehouse(customer_id: int, warehouse_ids: List[int], 
                          distances: Dict) -> Tuple[int, float]:
    """
    Find the nearest warehouse to a customer.
    
    Args:
        customer_id: ID of customer node
        warehouse_ids: List of warehouse IDs
        distances: Dictionary of all shortest distances
    
    Returns:
        (warehouse_id, distance) of nearest warehouse
    """
    min_warehouse = None
    min_distance = float('inf')
    
    for wid in warehouse_ids:
        key = (wid, customer_id)
        if key in distances and distances[key] < min_distance:
            min_distance = distances[key]
            min_warehouse = wid
    
    return min_warehouse, min_distance
