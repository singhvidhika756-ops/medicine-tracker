"""MediVault browser application."""

from flask import Flask, jsonify, render_template, request

from database.connection import DatabaseManager
from database.schema import initialize_database
from services.expiry_service import ExpiryService
from services.inventory_service import InventoryService
from services.medicine_service import MedicineService
from services.report_service import ReportService
from utils.backup import export_all_to_csv

app = Flask(__name__)
db = DatabaseManager()
initialize_database(db)
medicine_service = MedicineService(db)
inventory_service = InventoryService(db)
expiry_service = ExpiryService(db)
report_service = ReportService(db)


def success(data=None):
    return jsonify({"ok": True, "data": data})


def failure(message, status=400):
    return jsonify({"ok": False, "error": str(message)}), status


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/dashboard")
def dashboard():
    return success(report_service.get_dashboard_stats())


@app.get("/api/medicines")
def medicines():
    query = request.args.get("q", "").strip()
    category = request.args.get("category")
    if query or category:
        rows = medicine_service.search_medicines(query, category)
    else:
        rows = medicine_service.get_all_medicines_with_stock()
    return success(rows)


@app.post("/api/medicines")
def create_medicine():
    payload = request.get_json(silent=True) or {}
    try:
        medicine_id = medicine_service.add_medicine(
            name=payload.get("name", ""),
            generic_name=payload.get("generic_name", ""),
            category=payload.get("category", "General"),
            manufacturer=payload.get("manufacturer", ""),
            description=payload.get("description", ""),
            unit_type=payload.get("unit_type", "Tablet"),
            min_stock_threshold=int(payload.get("min_stock_threshold", 10)),
        )
        return success({"medicine_id": medicine_id}), 201
    except (TypeError, ValueError) as exc:
        return failure(exc)


@app.get("/api/batches")
def batches():
    medicine_id = request.args.get("medicine_id", type=int)
    return success(inventory_service.get_batches(medicine_id))


@app.post("/api/batches")
def create_batch():
    payload = request.get_json(silent=True) or {}
    try:
        batch_id = inventory_service.add_batch(
            medicine_id=int(payload["medicine_id"]),
            batch_number=payload.get("batch_number", ""),
            mfg_date=payload["mfg_date"],
            exp_date=payload["exp_date"],
            purchase_date=payload["purchase_date"],
            qty_received=int(payload["qty_received"]),
            purchase_price=float(payload.get("purchase_price", 0)),
            selling_price=float(payload.get("selling_price", 0)),
            supplier=payload.get("supplier", ""),
            notes=payload.get("notes", ""),
        )
        return success({"batch_id": batch_id}), 201
    except (KeyError, TypeError, ValueError) as exc:
        return failure(exc)


@app.get("/api/alerts")
def alerts():
    return success({
        "expired": expiry_service.get_expired_batches(),
        "critical": expiry_service.get_critical_batches(),
        "warning": expiry_service.get_warning_batches(),
        "upcoming": expiry_service.get_upcoming_batches(),
        "low_stock": medicine_service.get_low_stock_medicines(),
    })


@app.get("/api/transactions")
def transactions():
    limit = min(request.args.get("limit", 100, type=int), 500)
    return success(inventory_service.get_stock_history(limit=limit))


@app.post("/api/stock")
def stock_action():
    payload = request.get_json(silent=True) or {}
    action = payload.get("action")
    try:
        if action == "fefo":
            result = inventory_service.reduce_stock_fefo(
                int(payload["medicine_id"]), int(payload["quantity"]), payload.get("reason", "Web dispense")
            )
        else:
            batch_id = int(payload["batch_id"])
            quantity = int(payload.get("quantity", 0))
            reason = payload.get("reason", "Web stock operation")
            if action == "add":
                result = inventory_service.add_stock(batch_id, quantity, reason)
            elif action == "remove":
                result = inventory_service.reduce_stock(batch_id, quantity, reason)
            elif action == "correct":
                result = inventory_service.correct_stock(batch_id, quantity, reason)
            else:
                return failure("Unknown stock action")
        return success(result)
    except (KeyError, TypeError, ValueError) as exc:
        return failure(exc)


@app.get("/api/reports/inventory")
def inventory_report():
    return success(report_service.generate_inventory_report())


@app.get("/api/export")
def export_data():
    return success(export_all_to_csv(db))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
