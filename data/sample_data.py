# ============================================================
# PYTHON SAMPLE DATA (used by app.py during DB initialization)
# ============================================================

# Warehouse seed records
warehouses = [
    {"id": 1, "name": "North Warehouse", "region": "North", "x": 100, "y": 400, "initial_stock": 500},
    {"id": 2, "name": "South Warehouse", "region": "South", "x": 100, "y": 100, "initial_stock": 400},
    {"id": 3, "name": "East Warehouse", "region": "East", "x": 400, "y": 250, "initial_stock": 450},
    {"id": 4, "name": "West Warehouse", "region": "West", "x": 250, "y": 250, "initial_stock": 350},
]

# Customer seed records
customers = [
    {"id": 1, "name": "Customer A", "region": "North", "x": 150, "y": 450},
    {"id": 2, "name": "Customer B", "region": "North", "x": 200, "y": 380},
    {"id": 3, "name": "Customer C", "region": "South", "x": 120, "y": 50},
    {"id": 4, "name": "Customer D", "region": "South", "x": 180, "y": 120},
    {"id": 5, "name": "Customer E", "region": "East", "x": 450, "y": 300},
    {"id": 6, "name": "Customer F", "region": "East", "x": 500, "y": 200},
    {"id": 7, "name": "Customer G", "region": "West", "x": 280, "y": 350},
    {"id": 8, "name": "Customer H", "region": "West", "x": 220, "y": 200},
    {"id": 9, "name": "Customer I", "region": "Center", "x": 300, "y": 250},
    {"id": 10, "name": "Customer J", "region": "Center", "x": 350, "y": 350},
]

# Transportation edge seed records
edges = [
    {"source": 1, "destination": 2, "cost": 50, "delivery_time": 2},
    {"source": 1, "destination": 3, "cost": 80, "delivery_time": 3},
    {"source": 1, "destination": 4, "cost": 60, "delivery_time": 2},
    {"source": 2, "destination": 1, "cost": 50, "delivery_time": 2},
    {"source": 2, "destination": 3, "cost": 90, "delivery_time": 4},
    {"source": 2, "destination": 4, "cost": 70, "delivery_time": 3},
    {"source": 3, "destination": 1, "cost": 80, "delivery_time": 3},
    {"source": 3, "destination": 2, "cost": 90, "delivery_time": 4},
    {"source": 3, "destination": 4, "cost": 55, "delivery_time": 2},
    {"source": 4, "destination": 1, "cost": 60, "delivery_time": 2},
    {"source": 4, "destination": 2, "cost": 70, "delivery_time": 3},
    {"source": 4, "destination": 3, "cost": 55, "delivery_time": 2},
    # Keep edge endpoints aligned with existing customer IDs (1..10)
    {"source": 1, "destination": 9, "cost": 25, "delivery_time": 1},
    {"source": 2, "destination": 10, "cost": 30, "delivery_time": 1},
    {"source": 3, "destination": 5, "cost": 40, "delivery_time": 1},
]

# Order seed records
orders = [
    {"id": 1, "customer_id": 1, "region": "North", "weight": 10, "quantity": 2},
    {"id": 2, "customer_id": 2, "region": "North", "weight": 15, "quantity": 3},
    {"id": 3, "customer_id": 3, "region": "South", "weight": 8, "quantity": 1},
    {"id": 4, "customer_id": 4, "region": "South", "weight": 12, "quantity": 2},
    {"id": 5, "customer_id": 5, "region": "East", "weight": 20, "quantity": 4},
    {"id": 6, "customer_id": 6, "region": "East", "weight": 18, "quantity": 3},
    {"id": 7, "customer_id": 7, "region": "West", "weight": 14, "quantity": 2},
    {"id": 8, "customer_id": 8, "region": "West", "weight": 11, "quantity": 2},
    {"id": 9, "customer_id": 9, "region": "Center", "weight": 16, "quantity": 3},
    {"id": 10, "customer_id": 10, "region": "Center", "weight": 13, "quantity": 2},
    {"id": 11, "customer_id": 1, "region": "North", "weight": 9, "quantity": 1},
    {"id": 12, "customer_id": 5, "region": "East", "weight": 17, "quantity": 3},
]
