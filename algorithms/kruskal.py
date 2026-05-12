from typing import List, Dict, Tuple, Set


class UnionFind:
    """
    Union-Find (Disjoint Set Union) data structure.
    
    Used to efficiently track which nodes are connected in the MST.
    - find(): Returns the root/representative of a node's set
    - union(): Merges two sets
    """
    
    def __init__(self, nodes: Set[int]):
        """
        Initialize Union-Find with given nodes.
        
        Each node starts as its own parent (separate set).
        """
        self.parent = {node: node for node in nodes}
        self.rank = {node: 0 for node in nodes}
    
    def find(self, node: int) -> int:
        """
        Find the root/representative of the set containing node.
        
        Uses path compression: redirects nodes to point directly to root.
        
        Args:
            node: Node to find
        
        Returns:
            Root of node's set
        """
        if self.parent[node] != node:
            # Path compression: make node point directly to root
            self.parent[node] = self.find(self.parent[node])
        return self.parent[node]
    
    def union(self, node1: int, node2: int) -> bool:
        """
        Union the sets containing node1 and node2.
        
        Uses union by rank: smaller tree attached to larger tree.
        
        Args:
            node1: First node
            node2: Second node
        
        Returns:
            True if union was performed, False if already in same set
        """
        root1 = self.find(node1)
        root2 = self.find(node2)
        
        # Already in same set
        if root1 == root2:
            return False
        
        # Union by rank
        if self.rank[root1] < self.rank[root2]:
            self.parent[root1] = root2
        elif self.rank[root1] > self.rank[root2]:
            self.parent[root2] = root1
        else:
            self.parent[root2] = root1
            self.rank[root1] += 1
        
        return True


def kruskal_mst(warehouses: List[Dict], edges: List[Dict]) -> Tuple[List[Dict], float]:
    """
    Build minimum spanning tree connecting all warehouses using Kruskal's algorithm.
    
    Algorithm steps:
    1. Sort edges by cost (ascending)
    2. For each edge, if it doesn't create a cycle, add it to MST
    3. Stop when we have (n-1) edges for n warehouses
    
    Args:
        warehouses: List of warehouse dictionaries
        edges: List of edge dictionaries {source, destination, cost, delivery_time}
    
    Returns:
        Tuple of (mst_edges, total_cost)
        - mst_edges: List of edges in the MST
        - total_cost: Sum of all edge costs in MST
    """
    
    # Get warehouse IDs only (exclude customers)
    warehouse_ids = {w['id'] for w in warehouses}
    
    # Filter edges to only include those between warehouses
    warehouse_edges = []
    for edge in edges:
        if edge['source'] in warehouse_ids and edge['destination'] in warehouse_ids:
            warehouse_edges.append(edge)
    
    # Sort edges by cost (ascending) - greedy step
    warehouse_edges.sort(key=lambda e: e['cost'])
    
    # Initialize Union-Find
    uf = UnionFind(warehouse_ids)
    
    mst_edges = []
    total_cost = 0
    
    # Add edges one by one
    for edge in warehouse_edges:
        src = edge['source']
        dest = edge['destination']
        cost = edge['cost']
        
        # If this edge doesn't create a cycle, add it to MST
        if uf.union(src, dest):
            mst_edges.append(edge)
            total_cost += cost
            
            # Stop when we have enough edges (n-1 for n nodes)
            if len(mst_edges) == len(warehouse_ids) - 1:
                break
    
    return mst_edges, total_cost
