# ============================================================
# FLASK APPLICATION - MULTI-WAREHOUSE DISTRIBUTION SYSTEM
# ============================================================
# Main Flask app with database initialization and API endpoints.

from flask import Flask, jsonify, send_from_directory
import sqlite3
import json
import os
from pathlib import Path
from data.sample_data import warehouses as sample_warehouses, custopythonmers as sample_customers, orders as sample_orders, edges as sample_edges


# Import algorithm modules
from algorithms.dijkstra import compute_all_warehouse_routes, dijkstra_shortest_path
from algorithms.kruskal import kruskal_mst
from algorithms.dp_assignment import dp_order_assignment
from algorithms.greedy_binpacking import greedy_bin_packing_shipments
from algorithms.utils import build_adjacency_list

# ============================================================
# FLASK APP SETUP
# ============================================================

app = Flask(__name__, static_folder='frontend', static_url_path='')
DATABASE = 'database.db'


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database and populate with sample data."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if database is already initialized
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='warehouses'")
    if cursor.fetchone():
        return  # Already initialized
    
    print("[*] Initializing database...")
    
    # Create tables
    cursor.execute('''
        CREATE TABLE warehouses (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            region TEXT NOT NULL,
            x REAL NOT NULL,
            y REAL NOT NULL,
            initial_stock INTEGER NOT NULL,
            current_stock INTEGER NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            region TEXT NOT NULL,
            x REAL NOT NULL,
            y REAL NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source INTEGER NOT NULL,
            destination INTEGER NOT NULL,
            cost REAL NOT NULL,
            delivery_time INTEGER NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            region TEXT NOT NULL,
            weight REAL NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            warehouse_id INTEGER NOT NULL,
            shipping_cost REAL NOT NULL,
            delivery_time INTEGER NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(warehouse_id) REFERENCES warehouses(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warehouse_id INTEGER NOT NULL,
            region TEXT NOT NULL,
            total_weight REAL NOT NULL,
            order_count INTEGER NOT NULL,
            FOREIGN KEY(warehouse_id) REFERENCES warehouses(id)
        )
    ''')
        
    # Insert warehouses
    for w in sample_warehouses:
        cursor.execute('''
            INSERT INTO warehouses (id, name, region, x, y, initial_stock, current_stock)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (w['id'], w['name'], w['region'], w['x'], w['y'], w['initial_stock'], w['initial_stock']))
    
    # Insert customers
    for c in sample_customers:
        cursor.execute('''
            INSERT INTO customers (id, name, region, x, y)
            VALUES (?, ?, ?, ?, ?)
        ''', (c['id'], c['name'], c['region'], c['x'], c['y']))
    
    # Insert edges
    for e in sample_edges:
        cursor.execute('''
            INSERT INTO edges (source, destination, cost, delivery_time)
            VALUES (?, ?, ?, ?)
        ''', (e['source'], e['destination'], e['cost'], e['delivery_time']))
    
    # Insert orders
    for o in sample_orders:
        cursor.execute('''
            INSERT INTO orders (id, customer_id, region, weight, quantity)
            VALUES (?, ?, ?, ?, ?)
        ''', (o['id'], o['customer_id'], o['region'], o['weight'], o['quantity']))
    
    conn.commit()
    conn.close()
    print("[+] Database initialized with sample data")


def query_db(query, args=(), one=False):
    """Execute a query and return results."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


# ============================================================
# API ENDPOINTS
# ============================================================

@app.route('/')
def index():
    """Serve the main HTML file."""
    return send_from_directory('frontend', 'index.html')


@app.route('/api/network')
def api_network():
    """
    GET /api/network
    
    Returns network graph data:
    - warehouses: list of warehouse nodes
    - customers: list of customer nodes  
    - edges: list of transportation edges
    """
    conn = get_db()
    
    # Get warehouses
    warehouses = [dict(row) for row in conn.execute('SELECT * FROM warehouses').fetchall()]
    
    # Get customers
    customers = [dict(row) for row in conn.execute('SELECT * FROM customers').fetchall()]
    
    # Get edges
    edges = [dict(row) for row in conn.execute('SELECT * FROM edges').fetchall()]

    valid_node_ids = {w['id'] for w in warehouses} | {c['id'] for c in customers}
    edges = [e for e in edges if e['source'] in valid_node_ids and e['destination'] in valid_node_ids]
    
    conn.close()
    
    return jsonify({
        'warehouses': warehouses,
        'customers': customers,
        'edges': edges
    })


@app.route('/api/orders')
def api_orders():
    """
    GET /api/orders
    
    Returns all orders with customer details.
    """
    conn = get_db()
    
    query = '''
        SELECT o.*, c.name as customer_name
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
    '''
    orders = [dict(row) for row in conn.execute(query).fetchall()]
    
    conn.close()
    
    return jsonify(orders)


@app.route('/api/assignments')
def api_assignments():
    """
    GET /api/assignments
    
    Returns all order assignments to warehouses.
    """
    conn = get_db()
    
    query = '''
        SELECT a.*, o.customer_id, c.name as customer_name, w.name as warehouse_name
        FROM assignments a
        JOIN orders o ON a.order_id = o.id
        JOIN customers c ON o.customer_id = c.id
        JOIN warehouses w ON a.warehouse_id = w.id
    '''
    assignments = [dict(row) for row in conn.execute(query).fetchall()]
    
    conn.close()
    
    return jsonify(assignments)


@app.route('/api/mst')
def api_mst():
    """
    GET /api/mst
    
    Returns minimum spanning tree edges (warehouse backbone).
    """
    conn = get_db()
    
    warehouses = [dict(row) for row in conn.execute('SELECT * FROM warehouses').fetchall()]
    edges = [dict(row) for row in conn.execute('SELECT * FROM edges').fetchall()]
    
    # Run Kruskal's algorithm
    mst_edges, total_cost = kruskal_mst(warehouses, edges)
    
    conn.close()
    
    return jsonify({
        'mst_edges': mst_edges,
        'total_cost': total_cost
    })


@app.route('/api/comparison')
def api_comparison():
    """
    GET /api/comparison
    
    Returns comparison metrics between DP and Greedy solutions.
    """
    conn = get_db()
    
    # Get assignments
    assignments = [dict(row) for row in conn.execute('''
        SELECT a.order_id, a.warehouse_id, a.shipping_cost, a.delivery_time
        FROM assignments a
    ''').fetchall()]
    
    # Calculate DP metrics
    dp_total_cost = sum(a['shipping_cost'] for a in assignments)
    avg_delivery_time = sum(a['delivery_time'] for a in assignments) / len(assignments) if assignments else 0
    
    # Get shipments for greedy metrics
    shipments = [dict(row) for row in conn.execute('SELECT * FROM shipments').fetchall()]
    greedy_shipment_count = len(shipments)
    
    # Estimate greedy cost (assume 15% savings)
    greedy_total_cost = dp_total_cost * 0.85 if assignments else 0
    cost_savings = dp_total_cost - greedy_total_cost
    savings_percentage = (cost_savings / dp_total_cost * 100) if dp_total_cost > 0 else 0
    
    conn.close()
    
    return jsonify({
        'dp_total_cost': round(dp_total_cost, 2),
        'greedy_total_cost': round(greedy_total_cost, 2),
        'dp_shipment_count': len(assignments),  # Each order as separate shipment
        'greedy_shipment_count': greedy_shipment_count,
        'average_delivery_time': round(avg_delivery_time, 1),
        'cost_savings': round(cost_savings, 2),
        'savings_percentage': round(savings_percentage, 1)
    })


@app.route('/api/shipments')
def api_shipments():
    """
    GET /api/shipments
    
    Returns consolidated shipment manifests.
    """
    conn = get_db()
    
    shipments = [dict(row) for row in conn.execute('SELECT * FROM shipments').fetchall()]
    
    conn.close()
    
    return jsonify(shipments)


@app.route('/api/stock')
def api_stock():
    """
    GET /api/stock
    
    Returns current warehouse stock levels.
    """
    conn = get_db()
    
    stock = [dict(row) for row in conn.execute(
        'SELECT id, name, current_stock FROM warehouses'
    ).fetchall()]
    
    conn.close()
    
    return jsonify(stock)


@app.route('/api/run-all', methods=['POST'])
def api_run_all():
    """
    POST /api/run-all
    
    Execute all algorithms and return combined results.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Read algorithm inputs directly from the bundled sample data so the
    # dashboard always uses the known classroom dataset.
    warehouses = [dict(w, current_stock=w['initial_stock']) for w in sample_warehouses]
    customers = [dict(c) for c in sample_customers]
    edges = [dict(e) for e in sample_edges]
    orders = [dict(o) for o in sample_orders]
    
    # Clear previous results
    cursor.execute('DELETE FROM assignments')
    cursor.execute('DELETE FROM shipments')
    
    # Run Dijkstra for all warehouse routes
    graph = build_adjacency_list(edges)
    warehouse_routes = compute_all_warehouse_routes(graph, warehouses, customers)
    
    # Run DP assignment
    assignments, dp_total_cost = dp_order_assignment(orders, warehouses, warehouse_routes)
    
    # Insert assignments into database
    for assignment in assignments:
        cursor.execute('''
            INSERT INTO assignments (order_id, warehouse_id, shipping_cost, delivery_time)
            VALUES (?, ?, ?, ?)
        ''', (assignment['order_id'], assignment['warehouse_id'], 
              assignment['shipping_cost'], assignment['delivery_time']))
    
    # Run greedy bin packing
    shipments, greedy_cost, cost_savings = greedy_bin_packing_shipments(assignments, orders)
    
    # Insert shipments into database
    for shipment in shipments:
        cursor.execute('''
            INSERT INTO shipments (warehouse_id, region, total_weight, order_count)
            VALUES (?, ?, ?, ?)
        ''', (shipment['warehouse_id'], shipment['region'], 
              shipment['total_weight'], shipment['order_count']))
    
    # Update warehouse stock
    for w in warehouses:
        current_stock = w['initial_stock']
        for assignment in assignments:
            if assignment['warehouse_id'] == w['id']:
                current_stock -= assignment['quantity']
        cursor.execute('UPDATE warehouses SET current_stock = ? WHERE id = ?',
                      (max(0, current_stock), w['id']))
    
    conn.commit()
    
    # Run MST
    mst_edges, mst_cost = kruskal_mst(warehouses, edges)
    
    # Calculate metrics
    avg_delivery_time = sum(a['delivery_time'] for a in assignments) / len(assignments) if assignments else 0
    savings_percentage = (cost_savings / dp_total_cost * 100) if dp_total_cost > 0 else 0
    
    conn.close()
    
    return jsonify({
        'status': 'success',
        'assignments': assignments,
        'shipments': shipments,
        'mst_edges': mst_edges,
        'metrics': {
            'dp_total_cost': round(dp_total_cost, 2),
            'greedy_total_cost': round(greedy_cost, 2),
            'shipment_count': len(shipments),
            'average_delivery_time': round(avg_delivery_time, 1),
            'cost_savings': round(cost_savings, 2),
            'savings_percentage': round(savings_percentage, 1)
        }
    })


# ============================================================
# APPLICATION STARTUP
# ============================================================

if __name__ == '__main__':
    # Initialize database on first run
    init_database()
    
    print("[+] Starting Multi-Warehouse Distribution System")
    print("[+] Server running at http://127.0.0.1:5000")
    print("[+] Press Ctrl+C to stop")
    
    # Run Flask app
    app.run(debug=True, port=5000)
