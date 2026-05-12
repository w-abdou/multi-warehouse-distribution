# Multi-Warehouse Distribution System

A Flask web application for a multi-warehouse distribution planning project. It includes:

- Dijkstra shortest-path routing across a directed warehouse/customer network
- Kruskal minimum spanning tree construction for the warehouse backbone
- Exact dynamic programming assignment of orders to warehouses
- Greedy assignment for comparison
- Greedy next-fit shipment consolidation with bin-packing constraints
- A browser UI built with HTML, CSS, and JavaScript

## Run

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

## API

- `GET /api/scenario` returns the generated sample network
- `POST /api/analyze` returns the full analysis dashboard payload
