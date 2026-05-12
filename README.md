# Multi-Warehouse Distribution System

A beginner-friendly full-stack project that simulates a warehouse distribution network using Python Flask and SQLite.

## Project Overview

This system manages:
- **Warehouses & Customers**: Network nodes for distribution
- **Transportation Routes**: Edges with costs and delivery times
- **Order Processing**: Assignment to optimal warehouses
- **Shipment Consolidation**: Grouping orders for efficiency
- **Optimization Algorithms**: Dijkstra, Kruskal, Dynamic Programming, and Greedy Bin Packing

## Tech Stack

### Backend
- Python Flask
- Pure Python algorithms (no external algorithm libraries)

### Frontend
- Single HTML file
- Vanilla JavaScript
- Chart.js for charts
- Cytoscape.js for graph visualization

## Project Structure

```
project/
├── app.py                    # Flask application
├── requirements.txt          # Dependencies
├── README.md                 # This file
├── database.db              # SQLite database (auto-created)
│
├── algorithms/
│   ├── dijkstra.py          # Shortest path algorithm
│   ├── kruskal.py           # Minimum spanning tree
│   ├── dp_assignment.py     # Dynamic programming order assignment
│   ├── greedy_binpacking.py # Greedy shipment consolidation
│   └── utils.py             # Helper functions
│
└── frontend/
    └── index.html           # Single-file frontend
```

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python app.py
```

The app will start at `http://127.0.0.1:5000`

### 3. First Run
- Database creates automatically with sample data
- No manual setup required

## Algorithms Implemented

### 1. Dijkstra's Shortest Path
Computes shortest paths from each warehouse to all customers.
- **Input**: Graph with weighted edges
- **Output**: Shortest path, total cost, delivery time

### 2. Kruskal's Minimum Spanning Tree
Builds warehouse backbone network using MST.
- **Input**: All warehouse nodes and edges
- **Output**: MST edges (shown in blue on map)

### 3. Dynamic Programming Assignment
Assigns orders to warehouses optimally respecting stock limits.
- **Input**: Orders and warehouse availability
- **Output**: Warehouse assignment with cost

### 4. Greedy Bin Packing
Consolidates orders into shared shipments.
- **Input**: Assigned orders
- **Output**: Shipment manifests with cost savings

## Sample Data

- **4 Warehouses**: Located in different regions
- **10 Customers**: Distributed across the network
- **15 Transportation Edges**: Routes between nodes
- **12 Orders**: Ready for processing

## Features

### Frontend Dashboard
1. **Network Visualization**: Interactive graph showing:
   - Warehouses (blue circles)
   - Customers (green circles)
   - Routes (gray edges)
   - MST backbone (blue edges)
   - Assignments (orange arrows)

2. **Order Assignment Table**: Complete order details with:
   - Customer name
   - Assigned warehouse
   - Shipping cost
   - Delivery time
   - Consolidation status

3. **Shipment Manifests**: Grouped shipment details with:
   - Included orders
   - Total weight
   - Cost savings

4. **Comparison Dashboard**: Side-by-side metrics:
   - DP total cost vs Greedy cost
   - Number of shipments
   - Average delivery time
   - Cost reduction percentage

5. **Stock Level Tracker**: Bar chart showing remaining inventory

## Database Schema

### warehouses
- id, name, region, x, y, initial_stock, current_stock

### customers
- id, name, region, x, y

### edges
- id, source, destination, cost, delivery_time

### orders
- id, customer_id, region, weight, quantity

### assignments
- id, order_id, warehouse_id, shipping_cost, delivery_time

### shipments
- id, source_warehouse, destination_region, total_weight, cost_savings

## Notes for Students

- All algorithms are implemented **without external libraries**
- Each algorithm file has clear comments explaining each step
- The Flask app uses simple routes and no advanced patterns
- SQLite is used directly with basic SQL (no complex ORM)
- Frontend is pure HTML/CSS/JS for maximum clarity
- Sample data is loaded automatically on first run


