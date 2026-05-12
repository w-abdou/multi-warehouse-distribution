import heapq
from typing import Dict, List, Tuple


def dijkstra_shortest_path(graph: Dict, start: int, all_nodes: List[int]) -> Dict:
    """
    Find shortest path from start node to all other nodes using Dijkstra's algorithm.
    
    This is a GREEDY algorithm that always expands the nearest unvisited node.
    
    Args:
        graph: Adjacency list representation {node_id: [{'neighbor': id, 'cost': x, 'time': y}]}
        start: Starting warehouse ID
        all_nodes: List of all node IDs (warehouses + customers)
    
    Returns:
        Dictionary with keys:
        - 'distances': {end_node: shortest_distance}
        - 'times': {end_node: estimated_delivery_time}
        - 'paths': {end_node: [path_of_nodes]}
    """
    
    # Initialize distances and tracking structures
    distances = {node: float('inf') for node in all_nodes}
    times = {node: float('inf') for node in all_nodes}
    visited = set()
    paths = {node: [] for node in all_nodes}
    
    # Start node has distance 0
    distances[start] = 0
    times[start] = 0
    paths[start] = [start]
    
    # Priority queue: (distance, current_node)
    pq = [(0, start)]
    
    # Main algorithm loop
    while pq:
        current_dist, current_node = heapq.heappop(pq)
        
        # Skip if already processed
        if current_node in visited:
            continue
        
        visited.add(current_node)
        
        # Skip if node not in graph (no outgoing edges)
        if current_node not in graph:
            continue
        
        # Check all neighbors
        for edge in graph[current_node]:
            neighbor = edge['neighbor']
            edge_cost = edge['cost']
            edge_time = edge['time']

            # Ignore edges that point to nodes outside the current dataset.
            # Sample data includes a few extra edges that are not part of the
            # warehouse/customer graph used by the dashboard.
            if neighbor not in distances:
                continue
            
            # Calculate new distance if we go through current_node
            new_distance = distances[current_node] + edge_cost
            new_time = times[current_node] + edge_time
            
            # If we found a shorter path, update it
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                times[neighbor] = new_time
                paths[neighbor] = paths[current_node] + [neighbor]
                
                # Add to queue for processing
                heapq.heappush(pq, (new_distance, neighbor))
    
    return {
        'distances': distances,
        'times': times,
        'paths': paths
    }


def compute_all_warehouse_routes(graph: Dict, warehouses: List[Dict], 
                                customers: List[Dict]) -> Dict:
    """
    Compute shortest paths from each warehouse to all customers.
    
    Args:
        graph: Adjacency list representation
        warehouses: List of warehouse dictionaries
        customers: List of customer dictionaries
    
    Returns:
        Dictionary: {warehouse_id: {customer_id: {'cost': x, 'time': y, 'path': [...]}}}
    """
    # Create mapping of customer id in original data to node id in graph
    # (customers get offset by 100 in graph)
    all_nodes = set()
    for w in warehouses:
        all_nodes.add(w['id'])
    for c in customers:
        all_nodes.add(c['id'])  # Use customer id directly
    
    warehouse_routes = {}
    
    # Run Dijkstra from each warehouse
    for warehouse in warehouses:
        wid = warehouse['id']
        result = dijkstra_shortest_path(graph, wid, list(all_nodes))
        
        warehouse_routes[wid] = {}
        
        # Store routes to each customer
        for customer in customers:
            cid = customer['id']
            warehouse_routes[wid][cid] = {
                'cost': result['distances'].get(cid, float('inf')),
                'time': result['times'].get(cid, float('inf')),
                'path': result['paths'].get(cid, [])
            }
    
    return warehouse_routes
