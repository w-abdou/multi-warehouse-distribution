function money(value) {
  return Number(value || 0).toFixed(2);
}

function egp(value) {
  return `EGP ${money(value)}`;
}

function formatClockTime(value) {
  return value || '-';
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

const svgNS = 'http://www.w3.org/2000/svg';

let currentScenario = null;

function createMetricCard(label, value, note) {
  const card = document.createElement('div');
  card.className = 'metric-card';
  card.innerHTML = `
    <span class="metric-label">${label}</span>
    <span class="metric-value">${value}</span>
    <span class="metric-note">${note}</span>
  `;
  return card;
}

function makeSvg(width, height) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  return svg;
}

function scalePoint(node, width, height) {
  const x = Number(node.coordinate_x ?? node.x ?? 0);
  const y = Number(node.coordinate_y ?? node.y ?? 0);
  return {
    x: 50 + (x / 300) * (width - 100),
    y: 40 + (y / 300) * (height - 80),
  };
}

function renderNetworkMap(data) {
  const container = document.getElementById('networkMap');
  const width = 1000;
  const height = 360;
  const svg = makeSvg(width, height);
  const nodes = [...data.scenario.warehouses, ...data.scenario.customers];
  const positions = new Map(nodes.map((node) => [node.id, scalePoint(node, width, height)]));

  const mstGroup = document.createElementNS(svgNS, 'g');
  data.mst.edges.forEach((edge) => {
    const left = positions.get(edge.source);
    const right = positions.get(edge.target);
    const line = document.createElementNS(svgNS, 'line');
    line.setAttribute('x1', left.x);
    line.setAttribute('y1', left.y);
    line.setAttribute('x2', right.x);
    line.setAttribute('y2', right.y);
    line.setAttribute('stroke', '#2d5f8b');
    line.setAttribute('stroke-width', '4');
    mstGroup.appendChild(line);
  });
  svg.appendChild(mstGroup);

  data.exact.assignments.forEach((assignment) => {
    const warehouse = data.scenario.warehouses.find((item) => item.id === assignment.warehouse_id);
    const customer = data.scenario.customers.find((item) => item.id === assignment.customer_id);
    const left = positions.get(warehouse.id);
    const right = positions.get(customer.id);
    const line = document.createElementNS(svgNS, 'line');
    line.setAttribute('x1', left.x);
    line.setAttribute('y1', left.y);
    line.setAttribute('x2', right.x);
    line.setAttribute('y2', right.y);
    line.setAttribute('stroke', '#d9822b');
    line.setAttribute('stroke-width', '2.5');
    line.setAttribute('marker-end', 'url(#arrow)');
    svg.appendChild(line);

    const label = document.createElementNS(svgNS, 'text');
    label.setAttribute('x', (left.x + right.x) / 2 + 6);
    label.setAttribute('y', (left.y + right.y) / 2 - 6);
    label.setAttribute('font-size', '12');
    label.setAttribute('fill', '#8a5310');
    label.textContent = egp(assignment.shipping_cost);
    svg.appendChild(label);
  });

  const defs = document.createElementNS(svgNS, 'defs');
  defs.innerHTML = `
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#d9822b"></path>
    </marker>
  `;
  svg.appendChild(defs);

  nodes.forEach((node) => {
    const point = positions.get(node.id);
    const shape = document.createElementNS(svgNS, node.type === 'warehouse' ? 'rect' : 'circle');
    if (node.type === 'warehouse') {
      shape.setAttribute('x', point.x - 10);
      shape.setAttribute('y', point.y - 10);
      shape.setAttribute('width', '20');
      shape.setAttribute('height', '20');
      shape.setAttribute('rx', '4');
      shape.setAttribute('fill', '#2d5f8b');
    } else {
      shape.setAttribute('cx', point.x);
      shape.setAttribute('cy', point.y);
      shape.setAttribute('r', '8');
      shape.setAttribute('fill', '#d9822b');
    }
    svg.appendChild(shape);

    const label = document.createElementNS(svgNS, 'text');
    label.setAttribute('x', point.x);
    label.setAttribute('y', point.y + 20);
    label.setAttribute('font-size', '12');
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('fill', '#1d232b');
    label.textContent = node.name || node.id;
    svg.appendChild(label);
  });

  const legend = document.createElement('div');
  legend.className = 'legend';
  legend.innerHTML = `
    <span class="legend-item"><span class="legend-swatch blue"></span>MST backbone</span>
    <span class="legend-item"><span class="legend-swatch orange"></span>Assignment arrows</span>
    <span class="legend-item"><span class="legend-swatch gray"></span>Warehouse / customer nodes</span>
  `;

  container.innerHTML = '';
  container.appendChild(svg);
  container.appendChild(legend);
}

function renderSummary(summary) {
  const container = document.getElementById('summaryCards');
  container.innerHTML = '';
  container.appendChild(createMetricCard('Orders processed', summary.orders_processed, 'Selected batch size'));
  container.appendChild(createMetricCard('Exact cost', egp(summary.exact_total_cost), 'Dynamic programming result'));
  container.appendChild(createMetricCard('Greedy cost', egp(summary.greedy_total_cost), 'Simple cheapest-choice result'));
  container.appendChild(createMetricCard('Shipments', summary.shipment_count, `Minimum possible: ${summary.theoretical_min_shipments}`));
  container.appendChild(createMetricCard('Cost difference', egp(summary.cost_difference), 'Greedy minus exact'));
}

function renderAssignments(assignments) {
  const container = document.getElementById('assignmentTable');
  const table = document.createElement('table');
  table.innerHTML = `
    <thead>
      <tr>
        <th>Order</th>
        <th>Customer</th>
        <th>Warehouse</th>
        <th>Cost</th>
        <th>Time</th>
        <th>Shared shipment</th>
      </tr>
    </thead>
  `;
  const body = document.createElement('tbody');
  assignments.forEach((assignment) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${assignment.order_id}</td>
      <td>${assignment.customer_name}<br><span class="badge soft">${assignment.region}</span></td>
      <td>${assignment.warehouse_name}</td>
      <td>${egp(assignment.shipping_cost)}</td>
      <td>${formatClockTime(assignment.estimated_delivery_at)}</td>
      <td>${assignment.consolidated ? `<span class="badge good">Yes ${assignment.shipment_id || ''}</span>` : '<span class="badge warn">No</span>'}</td>
    `;
    body.appendChild(row);
  });
  table.appendChild(body);
  container.innerHTML = '';
  container.appendChild(table);
}

function renderShipments(shipments) {
  const container = document.getElementById('shipmentTable');
  const table = document.createElement('table');
  table.innerHTML = `
    <thead>
      <tr>
        <th>Shipment</th>
        <th>Warehouse</th>
        <th>Region</th>
        <th>Orders</th>
        <th>Cost</th>
        <th>Savings</th>
      </tr>
    </thead>
  `;
  const body = document.createElement('tbody');
  shipments.forEach((shipment) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${shipment.shipment_id}</td>
      <td>${shipment.warehouse_name}</td>
      <td>${shipment.region}</td>
      <td>${shipment.order_ids.join(', ')}</td>
      <td>${egp(shipment.consolidated_cost)}</td>
      <td><span class="badge good">${egp(shipment.savings)}</span></td>
    `;
    body.appendChild(row);
  });
  table.appendChild(body);
  container.innerHTML = '';
  container.appendChild(table);
}

function renderStock(remainingStock) {
  const container = document.getElementById('stockTable');
  const table = document.createElement('table');
  table.innerHTML = `
    <thead>
      <tr>
        <th>Warehouse</th>
        <th>Remaining stock</th>
      </tr>
    </thead>
  `;
  const body = document.createElement('tbody');
  Object.entries(remainingStock).forEach(([warehouseId, value]) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${warehouseId}</td>
      <td>${value}</td>
    `;
    body.appendChild(row);
  });
  table.appendChild(body);
  container.innerHTML = '';
  container.appendChild(table);
}

function renderStockChart(remainingStock, scenario) {
  const chartContainer = document.getElementById('stockChart');
  
  // Create SVG bar chart
  const width = 800;
  const height = 300;
  const svg = makeSvg(width, height);
  
  // Get warehouse data
  const warehouses = Object.entries(remainingStock).map(([whId, remaining]) => {
    const warehouse = scenario.warehouses.find(w => w.id === whId);
    const maxStock = warehouse?.stock ?? 100;
    const used = maxStock - remaining;
    return { id: whId, name: warehouse?.name || whId, remaining, used, maxStock };
  });
  
  const padding = 60;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;
  const barWidth = chartWidth / warehouses.length * 0.6;
  const spacing = chartWidth / warehouses.length;
  
  // Draw axes
  const axisLine = document.createElementNS(svgNS, 'line');
  axisLine.setAttribute('x1', padding);
  axisLine.setAttribute('y1', height - padding);
  axisLine.setAttribute('x2', width - padding);
  axisLine.setAttribute('y2', height - padding);
  axisLine.setAttribute('stroke', '#2d5f8b');
  axisLine.setAttribute('stroke-width', '2');
  svg.appendChild(axisLine);
  
  const verticalAxis = document.createElementNS(svgNS, 'line');
  verticalAxis.setAttribute('x1', padding);
  verticalAxis.setAttribute('y1', padding);
  verticalAxis.setAttribute('x2', padding);
  verticalAxis.setAttribute('y2', height - padding);
  verticalAxis.setAttribute('stroke', '#2d5f8b');
  verticalAxis.setAttribute('stroke-width', '2');
  svg.appendChild(verticalAxis);
  
  // Y-axis label
  const yLabel = document.createElementNS(svgNS, 'text');
  yLabel.setAttribute('x', 20);
  yLabel.setAttribute('y', padding - 10);
  yLabel.setAttribute('font-size', '12');
  yLabel.setAttribute('fill', '#2d5f8b');
  yLabel.textContent = 'Stock Units';
  svg.appendChild(yLabel);
  
  // Draw bars
  warehouses.forEach((wh, index) => {
    const x = padding + index * spacing + spacing / 2 - barWidth / 2;
    const remainingHeight = (wh.remaining / wh.maxStock) * chartHeight;
    const y = height - padding - remainingHeight;
    
    // Remaining stock bar (green)
    const barRemaining = document.createElementNS(svgNS, 'rect');
    barRemaining.setAttribute('x', x);
    barRemaining.setAttribute('y', y);
    barRemaining.setAttribute('width', barWidth);
    barRemaining.setAttribute('height', remainingHeight);
    barRemaining.setAttribute('fill', '#4caf50');
    svg.appendChild(barRemaining);
    
    // Used stock bar (orange) - stacked on top
    const usedHeight = (wh.used / wh.maxStock) * chartHeight;
    const barUsed = document.createElementNS(svgNS, 'rect');
    barUsed.setAttribute('x', x);
    barUsed.setAttribute('y', y - usedHeight);
    barUsed.setAttribute('width', barWidth);
    barUsed.setAttribute('height', usedHeight);
    barUsed.setAttribute('fill', '#d9822b');
    svg.appendChild(barUsed);
    
    // Warehouse label
    const label = document.createElementNS(svgNS, 'text');
    label.setAttribute('x', x + barWidth / 2);
    label.setAttribute('y', height - padding + 20);
    label.setAttribute('font-size', '11');
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('fill', '#1d232b');
    label.textContent = wh.id;
    svg.appendChild(label);
    
    // Stock value label
    const valueLabel = document.createElementNS(svgNS, 'text');
    valueLabel.setAttribute('x', x + barWidth / 2);
    valueLabel.setAttribute('y', y - 5);
    valueLabel.setAttribute('font-size', '12');
    valueLabel.setAttribute('font-weight', 'bold');
    valueLabel.setAttribute('text-anchor', 'middle');
    valueLabel.setAttribute('fill', '#1d232b');
    valueLabel.textContent = wh.remaining;
    svg.appendChild(valueLabel);
  });
  
  // Legend
  const legend = document.createElement('div');
  legend.className = 'legend';
  legend.innerHTML = `
    <span class="legend-item"><span class="legend-swatch good"></span>Remaining stock</span>
    <span class="legend-item"><span class="legend-swatch orange"></span>Used stock</span>
  `;
  
  chartContainer.innerHTML = '';
  chartContainer.appendChild(svg);
  chartContainer.appendChild(legend);
}

function renderComparison(summary, exact, greedy) {
  const container = document.getElementById('comparisonCards');
  container.innerHTML = '';
  container.appendChild(createMetricCard('Exact total cost', egp(summary.exact_total_cost), 'DP-optimal result'));
  container.appendChild(createMetricCard('Greedy total cost', egp(summary.greedy_total_cost), 'Heuristic result'));
  container.appendChild(createMetricCard('Average delivery time', formatClockTime(summary.exact_average_delivery_clock), 'Exact assignment'));
  container.appendChild(createMetricCard('Shipment reduction', `${money(summary.cost_reduction_pct)}%`, 'Cost reduction vs greedy'));
}

function renderNodesList(scenario) {
  const container = document.getElementById('nodesList');
  const table = document.createElement('table');
  table.innerHTML = `
    <thead>
      <tr>
        <th>Type</th>
        <th>ID</th>
        <th>Name</th>
        <th>Region / Stock</th>
        <th>Coordinate X</th>
        <th>Coordinate Y</th>
      </tr>
    </thead>
  `;
  const body = document.createElement('tbody');
  
  // Add all warehouses
  scenario.warehouses.forEach((warehouse) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td><span class="badge soft">Warehouse</span></td>
      <td>${warehouse.id}</td>
      <td>${warehouse.name}</td>
      <td>${warehouse.stock}</td>
      <td>${warehouse.coordinate_x ?? warehouse.x ?? 0}</td>
      <td>${warehouse.coordinate_y ?? warehouse.y ?? 0}</td>
    `;
    body.appendChild(row);
  });
  
  // Add all customers
  scenario.customers.forEach((customer) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td><span class="badge warn">Customer</span></td>
      <td>${customer.id}</td>
      <td>${customer.name}</td>
      <td>${customer.region}</td>
      <td>${customer.coordinate_x ?? customer.x ?? 0}</td>
      <td>${customer.coordinate_y ?? customer.y ?? 0}</td>
    `;
    body.appendChild(row);
  });
  
  table.appendChild(body);
  container.innerHTML = '';
  container.appendChild(table);
}

async function saveScenarioToServer() {
  const response = await fetch('/api/scenario', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario: currentScenario }),
  });
  if (!response.ok) {
    throw new Error(`Failed to save scenario (${response.status})`);
  }
  currentScenario = clone(await response.json());
  currentScenario.warehouses = currentScenario.warehouses.map(normalizeNode);
  currentScenario.customers = currentScenario.customers.map(normalizeNode);
  renderNodesList(currentScenario);
}

async function runAnalysis() {
  const button = document.getElementById('runButton');
  button.disabled = true;
  button.textContent = 'Running...';

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    const data = await response.json();
    renderNetworkMap(data);
    renderSummary(data.summary);
    renderAssignments(data.exact.assignments);
    renderShipments(data.shipments.shipment_manifests);
    renderStockChart(data.summary.remaining_stock, data.scenario);
    renderStock(data.summary.remaining_stock);
    renderComparison(data.summary, data.exact, data.greedy);
  } catch (error) {
    document.getElementById('summaryCards').innerHTML = `<div class="metric-card"><span class="metric-label">Error</span><span class="metric-value">Load failed</span><span class="metric-note">${error.message}</span></div>`;
  } finally {
    button.disabled = false;
    button.textContent = 'Run analysis';
  }
}

function normalizeNode(node) {
  return {
    ...node,
    x: Number(node.coordinate_x ?? node.x ?? 0),
    y: Number(node.coordinate_y ?? node.y ?? 0),
    coordinate_x: Number(node.coordinate_x ?? node.x ?? 0),
    coordinate_y: Number(node.coordinate_y ?? node.y ?? 0),
  };
}

function nextPosition(nodes) {
  if (!nodes.length) {
    return { x: 10, y: 10 };
  }
  const lastNode = nodes[nodes.length - 1];
  const lastX = Number(lastNode.coordinate_x ?? lastNode.x ?? 0);
  const lastY = Number(lastNode.coordinate_y ?? lastNode.y ?? 0);
  const nextX = lastX + 30;
  return {
    x: nextX > 240 ? 10 : nextX,
    y: nextX > 240 ? Math.min(270, lastY + 30) : lastY,
  };
}

function addNodeFromForm() {
  const nodeType = document.getElementById('nodeType').value;
  const nodeId = document.getElementById('nodeId').value.trim();
  const nodeName = document.getElementById('nodeName').value.trim();
  const positionSource = nodeType === 'warehouse' ? currentScenario.warehouses : currentScenario.customers;
  const position = nextPosition(positionSource);

  if (!nodeId || !nodeName) {
    return;
  }

  const baseNode = {
    id: nodeId,
    name: nodeName,
    type: nodeType,
    coordinate_x: position.x,
    coordinate_y: position.y,
    x: position.x,
    y: position.y,
  };

  if (nodeType === 'warehouse') {
    const stock = Number(document.getElementById('nodeStock').value);
    currentScenario.warehouses.push({ ...baseNode, stock });
  } else {
    const region = document.getElementById('nodeRegion').value.trim() || 'Retail';
    currentScenario.customers.push({ ...baseNode, region });
    const orderId = `O${currentScenario.orders.length + 1}`;
    currentScenario.orders.push({ id: orderId, customer_id: nodeId, weight: 1.0, volume: 1.0 });
  }
}

function bindEditor() {
  const nodeType = document.getElementById('nodeType');
  const stockField = document.getElementById('stockField');
  const regionField = document.getElementById('regionField');

  nodeType.addEventListener('change', () => {
    const isWarehouse = nodeType.value === 'warehouse';
    stockField.style.display = isWarehouse ? 'grid' : 'none';
    regionField.style.display = isWarehouse ? 'none' : 'grid';
  });

  document.getElementById('addNodeButton').addEventListener('click', async () => {
    addNodeFromForm();
    await saveScenarioToServer();
    await runAnalysis();
  });

  document.getElementById('resetButton').addEventListener('click', async () => {
    const response = await fetch('/api/scenario/reset', { method: 'POST' });
    if (!response.ok) {
      return;
    }
    currentScenario = clone(await response.json());
    currentScenario.warehouses = currentScenario.warehouses.map(normalizeNode);
    currentScenario.customers = currentScenario.customers.map(normalizeNode);
    renderNodesList(currentScenario);
    await runAnalysis();
  });

  nodeType.dispatchEvent(new Event('change'));
}

async function loadScenario() {
  const response = await fetch('/api/scenario');
  currentScenario = clone(await response.json());
  currentScenario.warehouses = currentScenario.warehouses.map(normalizeNode);
  currentScenario.customers = currentScenario.customers.map(normalizeNode);
  renderNodesList(currentScenario);
  await runAnalysis();
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('runButton').addEventListener('click', runAnalysis);
  bindEditor();
  loadScenario();
});
