"""Streamlit interface for the MediVault inventory system."""

from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from database.connection import DatabaseManager
from database.schema import initialize_database
from models.medicine import CATEGORIES, UNIT_TYPES
from services.expiry_service import ExpiryService
from services.inventory_service import InventoryService
from services.medicine_service import MedicineService
from services.report_service import ReportService
from utils.backup import create_backup, export_all_to_csv

st.set_page_config(page_title="MediVault | Inventory workspace", page_icon="💊", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink: #e7edf5; --muted: #9aa8bb; --navy: #0f172a; --panel: #1f2937; --line: #334155; --blue: #2f6feb; --teal: #24c7a5; --coral: #ff6b6b; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: #111827; color: var(--ink); }
    [data-testid="stSidebar"] { background: var(--navy); border-right: 1px solid #263449; }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.6rem; }
    [data-testid="stSidebar"] h1 { font-family: 'Space Grotesk', sans-serif; color: white; font-size: 1.45rem; }
    [data-testid="stSidebar"] p { color: var(--muted); }
    [data-testid="stSidebar"] [role="radiogroup"] { gap: .35rem; }
    [data-testid="stSidebar"] [role="radio"] { border-radius: 6px; padding: .55rem .7rem; color: #b6c2d2; }
    [data-testid="stSidebar"] [role="radio"]:hover { background: #1d3554; color: white; }
    [data-testid="stSidebar"] [role="radio"][aria-checked="true"] { background: var(--blue); color: white; }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; color: white; letter-spacing: 0; }
    h1 { font-size: 2.1rem; }
    h2 { font-size: 1.45rem; }
    h3 { font-size: 1.05rem; }
    [data-testid="stMetric"] { background: var(--panel); border: 1px solid var(--line); border-left: 4px solid var(--blue); padding: 1rem; border-radius: 2px; }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    [data-testid="stMetricValue"] { color: white; font-family: 'Space Grotesk', sans-serif; }
    [data-testid="stDataFrame"] { border: 1px solid var(--line); }
    [data-testid="stExpander"] { background: var(--panel); border: 1px solid var(--line); }
    .stButton > button, .stDownloadButton > button { border-radius: 4px; font-weight: 600; }
    .stButton > button[kind="primary"] { background: var(--blue); border-color: var(--blue); }
    [data-testid="stAlert"] { border-radius: 3px; }
    [data-testid="stHeader"] { background: #111827; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_services():
    db = DatabaseManager()
    initialize_database(db)
    return db, MedicineService(db), InventoryService(db), ExpiryService(db), ReportService(db)


db, medicine_service, inventory_service, expiry_service, report_service = get_services()


def frame(title, subtitle):
    st.title(title)
    st.caption(subtitle)


def show_table(rows, columns=None):
    if not rows:
        st.info("Nothing to show here yet.")
        return
    table = pd.DataFrame(rows)
    if columns:
        table = table[[column for column in columns if column in table.columns]]
    st.dataframe(table, width="stretch", hide_index=True)


def dashboard_page():
    frame("Good morning, keep stock moving.", "Live stock health, expiry risk, and recent activity.")
    stats = report_service.get_dashboard_stats()
    alert_total = stats["expired_batches"] + stats["expiring_7_days"] + stats["low_stock_medicines"]
    if alert_total:
        st.warning(f"{alert_total} items need attention: {stats['expired_batches']} expired, {stats['expiring_7_days']} expiring within 7 days, and {stats['low_stock_medicines']} below threshold.")

    cards = [
        ("Registered medicines", stats["total_medicines"]),
        ("Active batches", stats["total_batches"]),
        ("Available units", f"{stats['total_units']:,}"),
        ("Inventory value", f"₹{stats['total_value']:,.2f}"),
        ("Expired batches", stats["expired_batches"]),
        ("Expiring in 7 days", stats["expiring_7_days"]),
        ("Expiring in 30 days", stats["expiring_30_days"]),
        ("Low-stock medicines", stats["low_stock_medicines"]),
    ]
    columns = st.columns(4)
    for index, (label, value) in enumerate(cards):
        columns[index % 4].metric(label, value)

    left, right = st.columns([1.7, 1])
    with left:
        st.subheader("Recent stock movements")
        show_table(stats["recent_transactions"], ["transaction_date", "medicine_name", "batch_number", "transaction_type", "quantity_changed", "reason"])
    with right:
        st.subheader("Category mix")
        categories = stats["category_distribution"]
        if categories:
            st.bar_chart(pd.Series(categories, name="medicines"))


def medicines_page():
    frame("Medicine catalog", "Search products, monitor thresholds, and add medicines to the shared database.")
    query = st.text_input("Search by medicine or generic name")
    category = st.selectbox("Category", ["All"] + CATEGORIES)
    rows = medicine_service.search_medicines(query, category if category != "All" else None)
    show_table(rows, ["name", "generic_name", "category", "unit_type", "total_stock", "min_stock_threshold", "batch_count"])

    with st.expander("Add medicine"):
        with st.form("add_medicine", clear_on_submit=True):
            name = st.text_input("Medicine name", placeholder="Paracetamol 500mg")
            generic_name = st.text_input("Generic name")
            left, right = st.columns(2)
            with left:
                medicine_category = st.selectbox("Category", CATEGORIES)
                unit_type = st.selectbox("Unit type", UNIT_TYPES)
                manufacturer = st.text_input("Manufacturer")
            with right:
                threshold = st.number_input("Low-stock threshold", min_value=0, step=1, value=10)
                description = st.text_area("Description", height=112)
            if st.form_submit_button("Save medicine", type="primary"):
                try:
                    medicine_service.add_medicine(name, generic_name, medicine_category, manufacturer, description, unit_type, int(threshold))
                    st.success(f"{name.strip()} was saved to the medicines table.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))


def batches_page():
    frame("Batch inventory", "Track every lot, expiry date, supplier, and current quantity.")
    show_table(inventory_service.get_all_batches(), ["medicine_name", "batch_number", "expiry_date", "days_until_expiry", "expiry_status", "current_quantity", "purchase_price", "supplier"])

    with st.expander("Register a batch"):
        medicines = medicine_service.get_all_medicines()
        if not medicines:
            st.info("Add a medicine before registering a batch.")
            return
        lookup = {f"{m['name']} (ID {m['medicine_id']})": m["medicine_id"] for m in medicines}
        with st.form("add_batch", clear_on_submit=True):
            selected = st.selectbox("Medicine", list(lookup))
            batch_number = st.text_input("Batch number")
            left, right = st.columns(2)
            with left:
                mfg_date = st.date_input("Manufacturing date", date.today())
                purchase_date = st.date_input("Purchase date", date.today())
                quantity = st.number_input("Quantity received", min_value=1, step=1, value=10)
            with right:
                expiry_date = st.date_input("Expiry date", date.today() + timedelta(days=365))
                purchase_price = st.number_input("Purchase price / unit", min_value=0.0, step=0.5)
                selling_price = st.number_input("Selling price / unit", min_value=0.0, step=0.5)
            supplier = st.text_input("Supplier")
            notes = st.text_area("Notes")
            if st.form_submit_button("Register batch", type="primary"):
                try:
                    inventory_service.add_batch(lookup[selected], batch_number, mfg_date.isoformat(), expiry_date.isoformat(), purchase_date.isoformat(), int(quantity), float(purchase_price), float(selling_price), supplier, notes)
                    st.success("Batch registered and initial stock audit created.")
                    st.rerun()
                except (ValueError, TypeError) as exc:
                    st.error(str(exc))


def alerts_page():
    frame("Expiry and stock alerts", "Resolve the riskiest inventory items first.")
    tabs = st.tabs(["Expired", "Critical ≤7 days", "Warning 8-15 days", "Upcoming 16-30 days", "Low stock"])
    groups = [
        (expiry_service.get_expired_batches(), tabs[0]),
        (expiry_service.get_critical_batches(), tabs[1]),
        (expiry_service.get_warning_batches(), tabs[2]),
        (expiry_service.get_upcoming_batches(), tabs[3]),
        (medicine_service.get_low_stock_medicines(), tabs[4]),
    ]
    for rows, tab in groups:
        with tab:
            show_table(rows)


def stock_page():
    frame("Stock operations", "Add, remove, correct, or dispense stock using FEFO.")
    batches = inventory_service.get_all_batches()
    medicines = medicine_service.get_all_medicines()
    if not batches:
        st.info("Register a batch before making stock movements.")
        return
    batch_lookup = {f"{b['medicine_name']} · {b['batch_number']} · {b['current_quantity']} units": b["batch_id"] for b in batches}
    med_lookup = {f"{m['name']} (ID {m['medicine_id']})": m["medicine_id"] for m in medicines}
    operation, fefo = st.tabs(["Batch operation", "FEFO dispense"])
    with operation:
        with st.form("stock_operation"):
            action = st.selectbox("Operation", ["Add stock", "Remove stock", "Correct stock"])
            selected_batch = st.selectbox("Batch", list(batch_lookup))
            quantity = st.number_input("Units", min_value=0, step=1, value=1)
            reason = st.text_input("Reason", value="Web stock operation")
            if st.form_submit_button("Apply operation", type="primary"):
                try:
                    batch_id = batch_lookup[selected_batch]
                    if action == "Add stock":
                        inventory_service.add_stock(batch_id, int(quantity), reason)
                    elif action == "Remove stock":
                        inventory_service.reduce_stock(batch_id, int(quantity), reason)
                    else:
                        inventory_service.correct_stock(batch_id, int(quantity), reason)
                    st.success("Stock updated and audit entry created.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
    with fefo:
        with st.form("fefo_operation"):
            selected_medicine = st.selectbox("Medicine", list(med_lookup))
            quantity = st.number_input("Units to dispense", min_value=1, step=1, value=1)
            reason = st.text_input("Dispense reason", value="FEFO dispense")
            if st.form_submit_button("Dispense using FEFO", type="primary"):
                try:
                    reductions = inventory_service.reduce_stock_fefo(med_lookup[selected_medicine], int(quantity), reason)
                    st.success(f"Dispensed across {len(reductions)} batch(es): {reductions}")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))


def audit_page():
    frame("Stock audit log", "Every service-level movement with before and after quantities.")
    limit = st.slider("Rows to show", 10, 500, 100, 10)
    show_table(inventory_service.get_stock_history(limit=limit))


def reports_page():
    frame("Reports and data export", "Generate a clean inventory snapshot for review or spreadsheet work.")
    report = report_service.generate_inventory_report()
    show_table(report, ["medicine_name", "batch_number", "expiry_date", "expiry_status", "current_quantity", "purchase_price", "supplier"])
    if report:
        csv = pd.DataFrame(report).to_csv(index=False).encode("utf-8-sig")
        st.download_button("Download inventory CSV", csv, "medivault_inventory_report.csv", "text/csv")
    if st.button("Export all tables to CSV"):
        files = export_all_to_csv(db)
        st.success(f"Exported {len(files)} table file(s) to the exports folder.")


def settings_page():
    frame("Settings and backups", "Protect the database and inspect the active data file.")
    st.write(f"Database: `{db.db_path}`")
    if st.button("Create database backup", type="primary"):
        try:
            st.success(f"Backup created: {Path(create_backup()).name}")
        except Exception as exc:
            st.error(str(exc))


pages = {
    "Overview": dashboard_page,
    "Medicines": medicines_page,
    "Batches": batches_page,
    "Alerts": alerts_page,
    "Stock operations": stock_page,
    "Stock audit": audit_page,
    "Reports": reports_page,
    "Settings": settings_page,
}

with st.sidebar:
    st.markdown("# 💊 MediVault")
    st.caption("Pharmacy inventory workspace")
    page = st.radio("Navigate", list(pages), label_visibility="collapsed")
    st.divider()
    st.success("Local database connected")

pages[page]()
