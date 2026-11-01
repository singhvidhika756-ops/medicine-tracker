const state = { dashboard: null, medicines: [], batches: [], alerts: null, transactions: [], report: [] };
const alertState = { enabled: localStorage.getItem('medivault_alerts_enabled') === 'true', lastFingerprint: localStorage.getItem('medivault_alert_fingerprint') || '' };
const $ = (selector) => document.querySelector(selector);
const money = (value) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(value || 0);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[char]));
const badge = (value) => `<span class="badge ${(value || '').toLowerCase()}">${esc(value || '-')}</span>`;

async function api(url, options = {}) {
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
  const payload = await response.json();
  if (!response.ok || !payload.ok) throw new Error(payload.error || 'Request failed');
  return payload.data;
}

function showToast(message) {
  const toast = $('#toast'); toast.textContent = message; toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2600);
}

function alertFingerprint(dashboard) {
  return [dashboard.low_stock_medicines, dashboard.expired_batches, dashboard.expiring_7_days].join(':');
}

function playAlertSound() {
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (!AudioContext) return;
  const context = new AudioContext();
  const oscillator = context.createOscillator();
  const gain = context.createGain();
  oscillator.type = 'sine';
  oscillator.frequency.value = 740;
  gain.gain.setValueAtTime(0.001, context.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.16, context.currentTime + 0.03);
  gain.gain.exponentialRampToValueAtTime(0.001, context.currentTime + 0.55);
  oscillator.connect(gain).connect(context.destination);
  oscillator.start();
  oscillator.stop(context.currentTime + 0.55);
  oscillator.addEventListener('ended', () => context.close());
}

function notifyInventoryAlert(dashboard) {
  if (!alertState.enabled || dashboard.low_stock_medicines <= 0) return;
  const fingerprint = alertFingerprint(dashboard);
  if (fingerprint === alertState.lastFingerprint) return;
  alertState.lastFingerprint = fingerprint;
  localStorage.setItem('medivault_alert_fingerprint', fingerprint);
  playAlertSound();
  showToast(`Low stock alert: ${dashboard.low_stock_medicines} medicine(s) need replenishment.`);
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification('MediVault stock alert', { body: `${dashboard.low_stock_medicines} medicine(s) are below their stock threshold.` });
  }
}

function updateAlertButton() {
  const button = $('#alert-toggle');
  if (!button) return;
  button.textContent = alertState.enabled ? 'Alerts enabled' : 'Enable alerts';
  button.classList.toggle('primary', alertState.enabled);
}

function table(headers, rows) {
  if (!rows.length) return '<div class="empty">Nothing to show here yet.</div>';
  return `<div class="table-wrap"><table><thead><tr>${headers.map((header) => `<th>${header}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`;
}

function renderDashboard() {
  const d = state.dashboard;
  const totalAlerts = d.expired_batches + d.expiring_7_days + d.low_stock_medicines;
  const recent = d.recent_transactions || [];
  const categories = Object.entries(d.category_distribution || {});
  const maxCategory = Math.max(...categories.map(([, count]) => count), 1);
  notifyInventoryAlert(d);
  $('#dashboard-view').innerHTML = `
    ${totalAlerts ? `<div class="alert-banner"><strong>${totalAlerts} items need attention: ${d.expired_batches} expired, ${d.expiring_7_days} expiring soon, and ${d.low_stock_medicines} below threshold.</strong><button class="button danger" data-go="alerts">Review alerts</button></div>` : ''}
    <div class="kpi-grid">
      <article class="kpi teal"><div class="kpi-label">Registered medicines</div><div class="kpi-value">${d.total_medicines}</div><div class="kpi-note">Catalog items</div></article>
      <article class="kpi blue"><div class="kpi-label">Active batches</div><div class="kpi-value">${d.total_batches}</div><div class="kpi-note">Tracked lots</div></article>
      <article class="kpi teal"><div class="kpi-label">Available units</div><div class="kpi-value">${d.total_units.toLocaleString()}</div><div class="kpi-note">Across all batches</div></article>
      <article class="kpi amber"><div class="kpi-label">Inventory value</div><div class="kpi-value">${money(d.total_value)}</div><div class="kpi-note">At purchase cost</div></article>
      <article class="kpi coral"><div class="kpi-label">Expired batches</div><div class="kpi-value">${d.expired_batches}</div><div class="kpi-note">Remove from sale</div></article>
      <article class="kpi coral"><div class="kpi-label">Expiring in 7 days</div><div class="kpi-value">${d.expiring_7_days}</div><div class="kpi-note">Critical attention</div></article>
      <article class="kpi amber"><div class="kpi-label">Expiring in 30 days</div><div class="kpi-value">${d.expiring_30_days}</div><div class="kpi-note">Plan replenishment</div></article>
      <article class="kpi blue"><div class="kpi-label">Low-stock medicines</div><div class="kpi-value">${d.low_stock_medicines}</div><div class="kpi-note">Below configured limit</div></article>
    </div>
    <div class="content-grid">
      <section class="panel"><div class="panel-heading"><div><h3>Recent stock movements</h3><p>Latest additions, removals, and corrections</p></div><button class="button secondary" data-go="audit">View audit</button></div>
      ${table(['Date', 'Medicine', 'Batch', 'Type', 'Quantity', 'Reason'], recent.map((row) => `<tr><td>${esc(row.transaction_date)}</td><td><strong>${esc(row.medicine_name)}</strong></td><td>${esc(row.batch_number)}</td><td>${badge(row.transaction_type)}</td><td>${row.transaction_type === 'REMOVED' ? '-' : '+'}${row.quantity_changed}</td><td>${esc(row.reason)}</td></tr>`))}</section>
      <section class="panel"><div class="panel-heading"><div><h3>Category mix</h3><p>Catalog distribution</p></div></div><div class="category-list">${categories.map(([name, count]) => `<div><div class="category-row"><span>${esc(name)}</span><strong>${count}</strong></div><div class="bar"><span style="width:${Math.round(count / maxCategory * 100)}%"></span></div></div>`).join('')}</div></section>
    </div>`;
}

function renderMedicines() {
  const searchValue = $('#medicine-search')?.value || '';
  const categoryValue = $('#medicine-category')?.value || '';
  const rows = state.medicines.map((m) => `<tr><td><strong>${esc(m.name)}</strong><br><span class="kpi-note">${esc(m.generic_name || 'No generic name')}</span></td><td>${esc(m.category)}</td><td>${esc(m.unit_type)}</td><td>${m.total_stock}</td><td>${m.min_stock_threshold}</td><td>${m.total_stock < m.min_stock_threshold ? badge('LOW') : badge('NORMAL')}</td></tr>`);
  $('#medicines-view').innerHTML = `<div class="section-heading"><div><p class="eyebrow">Catalog</p><h2>Medicines</h2><p>Search products, monitor thresholds, and keep the catalog tidy.</p></div><button class="button primary" id="inline-add-medicine">Add medicine</button></div><div class="toolbar"><input id="medicine-search" placeholder="Search name or generic ingredient"><select id="medicine-category"><option value="">All categories</option>${[...new Set(state.medicines.map((m) => m.category))].sort().map((c) => `<option>${esc(c)}</option>`).join('')}</select></div><section class="panel data-panel">${table(['Medicine', 'Category', 'Form', 'Stock', 'Threshold', 'Status'], rows)}</section>`;
  $('#medicine-search').value = searchValue;
  $('#medicine-category').value = categoryValue;
  $('#inline-add-medicine').addEventListener('click', openMedicineDialog);
  $('#medicine-search').addEventListener('input', loadMedicines);
  $('#medicine-category').addEventListener('change', loadMedicines);
}

function renderBatches() {
  const rows = state.batches.map((b) => `<tr><td><strong>${esc(b.medicine_name)}</strong></td><td>${esc(b.batch_number)}</td><td>${esc(b.expiry_date)}</td><td>${b.days_until_expiry < 0 ? `${Math.abs(b.days_until_expiry)}d ago` : `${b.days_until_expiry}d`}</td><td>${badge(b.expiry_status)}</td><td>${b.current_quantity}</td><td>${money(b.purchase_price)}</td><td>${esc(b.supplier || '-')}</td></tr>`);
  $('#batches-view').innerHTML = `<div class="section-heading"><div><p class="eyebrow">Inventory</p><h2>Batch inventory</h2><p>Every lot, expiry date, and current quantity in one view.</p></div><button class="button primary" data-action="refresh">Refresh batches</button></div><section class="panel data-panel">${table(['Medicine', 'Batch', 'Expiry', 'Days left', 'Status', 'Stock', 'Cost / unit', 'Supplier'], rows)}</section>`;
}

function renderAlerts() {
  const a = state.alerts;
  const groups = [['Expired', a.expired, 'expired'], ['Critical, 7 days', a.critical, 'critical'], ['Warning, 8-15 days', a.warning, 'warning'], ['Upcoming, 16-30 days', a.upcoming, 'upcoming'], ['Low stock', a.low_stock, 'low']];
  $('#alerts-view').innerHTML = `<div class="section-heading"><div><p class="eyebrow">Action queue</p><h2>Expiry and stock alerts</h2><p>Resolve the riskiest inventory items first.</p></div><button class="button secondary" data-action="refresh">Refresh alerts</button></div>${groups.map(([title, rows, type]) => `<section class="panel data-panel" style="margin-bottom:16px"><div class="panel-heading"><div><h3>${title} <span class="badge ${type}">${rows.length}</span></h3></div></div>${table(['Medicine', 'Batch', 'Expiry', 'Units', 'Supplier'], rows.map((r) => `<tr><td>${esc(r.medicine_name || r.name)}</td><td>${esc(r.batch_number || '-')}</td><td>${esc(r.expiry_date || '-')}</td><td>${r.current_quantity ?? r.total_stock}</td><td>${esc(r.supplier || '-')}</td></tr>`))}</section>`).join('')}`;
}

function renderAudit() {
  const rows = state.transactions.map((t) => `<tr><td>${esc(t.transaction_date)}</td><td>${esc(t.medicine_name)}</td><td>${esc(t.batch_number)}</td><td>${badge(t.transaction_type)}</td><td>${t.previous_quantity}</td><td>${t.new_quantity}</td><td>${esc(t.reason)}</td></tr>`);
  $('#audit-view').innerHTML = `<div class="section-heading"><div><p class="eyebrow">Traceability</p><h2>Stock audit log</h2><p>Every service-level stock movement with before and after quantities.</p></div><button class="button secondary" data-action="refresh">Refresh log</button></div><section class="panel data-panel">${table(['Timestamp', 'Medicine', 'Batch', 'Type', 'Before', 'After', 'Reason'], rows)}</section>`;
}

function renderReports() {
  const rows = state.report.map((r) => `<tr><td>${esc(r.medicine_name)}</td><td>${esc(r.batch_number)}</td><td>${esc(r.expiry_date)}</td><td>${badge(r.expiry_status)}</td><td>${r.current_quantity}</td><td>${money(r.purchase_price)}</td><td>${esc(r.supplier || '-')}</td></tr>`);
  $('#reports-view').innerHTML = `<div class="section-heading"><div><p class="eyebrow">Data export</p><h2>Inventory report</h2><p>A clean snapshot for review or spreadsheet export.</p></div><button class="button primary" id="download-report">Download CSV</button></div><section class="panel data-panel">${table(['Medicine', 'Batch', 'Expiry', 'Status', 'Units', 'Cost / unit', 'Supplier'], rows)}</section>`;
  $('#download-report').addEventListener('click', downloadReport);
}

async function loadMedicines() { const q = $('#medicine-search')?.value || ''; const category = $('#medicine-category')?.value || ''; state.medicines = await api(`/api/medicines?q=${encodeURIComponent(q)}&category=${encodeURIComponent(category)}`); renderMedicines(); }
async function loadAll() { [state.dashboard, state.batches, state.alerts, state.transactions, state.report] = await Promise.all([api('/api/dashboard'), api('/api/batches'), api('/api/alerts'), api('/api/transactions'), api('/api/reports/inventory')]); state.medicines = await api('/api/medicines'); renderDashboard(); renderMedicines(); renderBatches(); renderAlerts(); renderAudit(); renderReports(); }

function switchView(name) { document.querySelectorAll('.view').forEach((view) => view.classList.remove('active-view')); $(`#${name}-view`).classList.add('active-view'); document.querySelectorAll('.nav-item').forEach((item) => item.classList.toggle('active', item.dataset.view === name)); const titles = { dashboard: 'Good morning, keep stock moving.', medicines: 'Your catalog, without the clutter.', batches: 'Know every lot before it expires.', alerts: 'A clear queue for the next right action.', audit: 'Trace every unit movement.', reports: 'Turn inventory into a useful snapshot.' }; $('#page-title').textContent = titles[name]; }
function openMedicineDialog() { $('#medicine-dialog').showModal(); }

$('#medicine-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
  try {
    await api('/api/medicines', { method: 'POST', body: JSON.stringify(data) });
    $('#medicine-dialog').close();
    event.target.reset();
    showToast('Medicine added to the catalog');
    await loadAll();
    switchView('medicines');
  } catch (error) {
    showToast(error.message);
  }
});
$('#cancel-medicine').addEventListener('click', () => $('#medicine-dialog').close());
$('#add-medicine-button').addEventListener('click', openMedicineDialog);
$('#alert-toggle').addEventListener('click', async () => {
  if ('Notification' in window && Notification.permission === 'default') await Notification.requestPermission();
  alertState.enabled = true;
  localStorage.setItem('medivault_alerts_enabled', 'true');
  playAlertSound();
  updateAlertButton();
  showToast('Low-stock sound and browser alerts are enabled.');
});
$('#refresh-button').addEventListener('click', async () => { await loadAll(); showToast('Workspace refreshed'); });
document.addEventListener('click', (event) => { const nav = event.target.closest('[data-view]'); if (nav) switchView(nav.dataset.view); const go = event.target.closest('[data-go]'); if (go) switchView(go.dataset.go); if (event.target.closest('[data-action="refresh"]')) loadAll(); });

async function downloadReport() { const columns = ['medicine_name', 'batch_number', 'expiry_date', 'expiry_status', 'current_quantity', 'purchase_price', 'supplier']; const csv = [columns.join(','), ...state.report.map((row) => columns.map((column) => `"${String(row[column] ?? '').replaceAll('"', '""')}"`).join(','))].join('\n'); const link = document.createElement('a'); link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); link.download = 'medivault_inventory_report.csv'; link.click(); URL.revokeObjectURL(link.href); }

updateAlertButton();
loadAll().catch((error) => { $('#dashboard-view').innerHTML = `<div class="panel empty">Could not load MediVault: ${esc(error.message)}</div>`; });
