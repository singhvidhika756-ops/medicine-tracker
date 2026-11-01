"""Generate a teacher-ready MediVault project report PDF."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "MediVault_Project_Report.pdf"

NAVY = colors.HexColor("#14233A")
BLUE = colors.HexColor("#2F6FEB")
TEAL = colors.HexColor("#008F83")
CORAL = colors.HexColor("#DC6555")
PALE = colors.HexColor("#F3F6FA")
MUTED = colors.HexColor("#5F6B7A")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=28, leading=34, alignment=TA_CENTER, textColor=NAVY, spaceAfter=12,
))
styles.add(ParagraphStyle(
    name="CoverSubtitle", parent=styles["Normal"], fontSize=14, leading=20,
    alignment=TA_CENTER, textColor=MUTED, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="Section", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=19, leading=24, textColor=NAVY, spaceBefore=8, spaceAfter=10,
))
styles.add(ParagraphStyle(
    name="Subsection", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=13, leading=17, textColor=TEAL, spaceBefore=9, spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="BodyClean", parent=styles["BodyText"], fontSize=9.5, leading=14,
    textColor=colors.HexColor("#263445"), spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="Small", parent=styles["BodyText"], fontSize=8, leading=11,
    textColor=MUTED, spaceAfter=3,
))
styles.add(ParagraphStyle(
    name="Callout", parent=styles["BodyText"], fontSize=10, leading=15,
    textColor=NAVY, backColor=PALE, borderColor=BLUE, borderWidth=1,
    borderPadding=9, spaceBefore=7, spaceAfter=10,
))
styles.add(ParagraphStyle(
    name="CodeBlock", parent=styles["Code"], fontName="Courier",
    fontSize=8.5, leading=12, textColor=colors.HexColor("#17324D"),
    backColor=colors.HexColor("#EEF3F8"), borderPadding=8, spaceBefore=4, spaceAfter=8,
))


def p(text, style="BodyClean"):
    return Paragraph(text, styles[style])


def bullet(text):
    return Paragraph(f"&#8226; {text}", styles["BodyClean"])


def section(title):
    return [Spacer(1, 6), Paragraph(title, styles["Section"])]


def table(data, widths=None, header=True):
    converted = []
    for row in data:
        converted.append([cell if isinstance(cell, Paragraph) else p(str(cell), "Small") for cell in row])
    result = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8E0EA")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        commands += [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white)]
    for row in range(1 if header else 0, len(converted)):
        if row % 2:
            commands.append(("BACKGROUND", (0, row), (-1, row), PALE))
    result.setStyle(TableStyle(commands))
    return result


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D8E0EA"))
    canvas.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 8 * mm, "MediVault | Medicine Inventory and Expiry Management System")
    canvas.drawRightString(192 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


story = []
story += [Spacer(1, 35 * mm), Paragraph("MediVault", styles["CoverTitle"]),
          Paragraph("Medicine Inventory and Expiry Management System", styles["CoverSubtitle"]),
          Spacer(1, 8 * mm),
          p("Project explanation report for academic presentation", "CoverSubtitle"),
          Spacer(1, 18 * mm),
          table([["Project type", "Desktop and browser-based inventory application"],
                 ["Language", "Python 3"],
                 ["Database", "SQLite3"],
                 ["Interfaces", "Tkinter, Streamlit, and custom Flask web UI"],
                 ["Testing", "Python unittest suite"],
                 ["Storage", "Local SQLite database at data/medivault.db"]], [45 * mm, 115 * mm], header=False),
          Spacer(1, 18 * mm),
          p("Prepared as a clear guide for explaining the project to a teacher, examiner, or evaluator.", "Callout"),
          PageBreak()]

story += section("1. Project Overview")
story += [p("MediVault is a medicine inventory management system designed for small pharmacies, clinics, medical stores, and personal medicine cabinets. It solves the problem of managing medicines only by name, which is unsafe because the same medicine can arrive in multiple batches with different expiry dates and quantities."),
          p("The system stores each batch separately, monitors expiry risk, calculates low-stock conditions, supports FEFO dispensing, records stock movements, generates reports, and creates database backups."),
          p("The core design separates the user interface, business logic, and database access. This makes the application easier to test, maintain, and extend."),
          p("One-sentence explanation:", "Subsection"),
          p("MediVault is a batch-aware medicine inventory system that helps a store know what stock it has, which stock should be used first, which stock is expiring, and why the quantity changed.", "Callout")]

story += section("2. Problem Statement and Objectives")
story += [p("A basic medicine list is not enough for real inventory control. A store needs to know the exact batch, expiry date, supplier, purchase price, and remaining quantity. Manual records can cause expired medicines to remain in stock, incorrect quantities, missed replenishment, and no explanation for stock changes."),
          Paragraph("Project objectives", styles["Subsection"]),
          bullet("Maintain a searchable medicine catalog."),
          bullet("Track multiple independent batches for one medicine."),
          bullet("Detect expired and near-expiry batches."),
          bullet("Warn when total medicine stock is below its threshold."),
          bullet("Use FEFO to dispense the batch that expires first."),
          bullet("Record every stock movement with before and after quantities."),
          bullet("Provide reports, CSV export, backups, and multiple user interfaces."),
          Paragraph("Expected benefits", styles["Subsection"]),
          p("The system reduces expiry-related waste, improves stock visibility, makes stock changes traceable, and demonstrates practical Python concepts such as classes, validation, SQL, file handling, exception handling, and automated testing.")]

story += section("3. Technology Stack")
story += [table([
    ["Technology", "Why it is used"],
    ["Python 3", "Main programming language; readable, fast to develop, and suitable for desktop, web, database, and testing work."],
    ["SQLite3", "Embedded relational database; no separate database server is required for a local application."],
    ["Tkinter and ttk", "Original desktop interface with navigation, dialogs, tables, themes, and keyboard shortcuts."],
    ["Streamlit", "Python-based browser interface with dashboard, forms, alerts, stock operations, reports, and downloads."],
    ["Flask", "Custom HTML/CSS/JavaScript browser interface with a REST-style API."],
    ["HTML, CSS, JavaScript", "Custom web UI layout, responsive styling, search, navigation, notifications, and CSV download."],
    ["unittest", "Automated tests for validation, CRUD, expiry boundaries, stock rules, FEFO, reports, and backups."],
    ["ReportLab", "Used to generate this project explanation PDF."],
], [38 * mm, 122 * mm]),
          Paragraph("Why SQLite instead of a larger database?", styles["Subsection"]),
          p("MediVault is designed as a local offline-first application. SQLite is included with Python, stores everything in one file, supports relationships and constraints, and is simple to back up. A future multi-user online version could move the data layer to PostgreSQL.")]

story += section("4. How the Application Runs")
story += [p("The application has three available interfaces. All interfaces use the same service layer and the same SQLite database, so data created through one interface can be read by another."),
          table([
              ["Interface", "Command", "Purpose"],
              ["Desktop", "python main.py", "Tkinter application with the full original desktop workflow."],
              ["Streamlit", "py -3.14 -m streamlit run app.py", "Python-generated browser interface."],
              ["Custom web", "py -3.14 web_app.py", "Custom HTML/CSS/JavaScript browser interface."],
          ], [28 * mm, 65 * mm, 67 * mm]),
          p("Shared request flow", "Subsection"),
          p("User interface -> service layer -> DatabaseManager -> SQLite database", "CodeBlock"),
          p("Example: when a user adds a medicine, the form collects the fields, the service validates the name and threshold, DatabaseManager executes a parameterized INSERT statement, and SQLite stores the record in the medicines table.", "Callout")]

story += section("5. Project Architecture")
story += [table([
    ["Layer", "Main files", "Responsibility"],
    ["Presentation", "ui/, app.py, web_app.py, templates/, static/", "Displays screens, forms, dashboards, tables, alerts, and reports."],
    ["Business services", "services/", "Contains medicine CRUD, stock movement, FEFO, expiry classification, reports, and aggregation rules."],
    ["Data access", "database/connection.py", "Opens SQLite, enables foreign keys, runs queries, commits statements, and supports transactions."],
    ["Schema", "database/schema.py", "Creates tables, relationships, indexes, constraints, and default settings."],
    ["Models", "models/", "Dataclasses representing medicines, batches, and stock transactions."],
    ["Utilities", "utils/", "Validation, backup, CSV import/export, and logging."],
    ["Tests", "tests/", "Automated checks for important business rules."],
], [30 * mm, 55 * mm, 75 * mm]),
          Paragraph("Why use a service layer?", styles["Subsection"]),
          p("The UI should not contain database rules everywhere. Services provide one controlled place for validation and business logic. For example, desktop, Streamlit, and Flask can all call InventoryService.add_stock(), so stock rules remain consistent across interfaces.")]

story += section("6. Database Design")
story += [p("The main relational tables are medicines, batches, stock_transactions, suppliers, and application_settings."),
          table([
              ["Table", "Important fields", "Purpose"],
              ["medicines", "medicine_id, name, generic_name, category, unit_type, min_stock_threshold", "Stores the medicine catalog."],
              ["batches", "batch_id, medicine_id, batch_number, expiry_date, current_quantity, prices", "Stores stock as independent production or purchase lots."],
              ["stock_transactions", "transaction_type, quantity_changed, previous_quantity, new_quantity, reason", "Stores the stock audit history."],
              ["suppliers", "supplier_id, name, contact, address", "Stores supplier information."],
              ["application_settings", "key, value", "Stores preferences such as theme and currency."],
          ], [33 * mm, 67 * mm, 60 * mm]),
          Paragraph("Database safeguards", styles["Subsection"]),
          bullet("Foreign keys are enabled with PRAGMA foreign_keys = ON."),
          bullet("A medicine cannot have duplicate batch numbers because of UNIQUE(medicine_id, batch_number)."),
          bullet("New schemas enforce nonnegative quantities and prices with CHECK constraints."),
          bullet("SQL parameters use ? placeholders instead of string concatenation."),
          bullet("Stock update plus audit insert runs in a transaction and rolls back together on failure."),
          p("Important design note: the current schema uses cascade deletion for medicines and batches. That avoids orphan rows, but a production compliance system should use archival or soft deletion if historical audit records must never be removed.", "Callout")]

story += section("7. Medicine and Batch Workflow")
story += [Paragraph("Adding a medicine", styles["Subsection"]),
          p("The user enters the name, generic name, category, dosage form, manufacturer, description, and low-stock threshold. MedicineService checks that the name is not empty and the threshold is not negative. The record is saved in data/medivault.db, inside the medicines table."),
          Paragraph("Registering a batch", styles["Subsection"]),
          p("The user selects a medicine and enters a batch number, manufacturing date, expiry date, purchase date, quantity received, prices, supplier, and notes. InventoryService checks the dates, quantity, prices, and batch number. The new batch starts with current_quantity equal to quantity_received, and an INITIAL transaction is created."),
          Paragraph("Why batch-level stock matters", styles["Subsection"]),
          p("If Paracetamol has one batch expiring in five days and another expiring in ninety days, the application must not treat them as one anonymous quantity. Batch records allow safe expiry decisions and FEFO dispensing.")]

story += section("8. Expiry and Low-Stock Logic")
story += [p("Expiry status is calculated from the ISO date format YYYY-MM-DD:"),
          p("days_remaining = expiry_date - today", "CodeBlock"),
          table([
              ["Status", "Condition", "Meaning"],
              ["EXPIRED", "days < 0", "The batch is past its expiry date."],
              ["CRITICAL", "0 to 7 days", "Immediate attention is needed."],
              ["WARNING", "8 to 15 days", "Plan usage or replenishment."],
              ["UPCOMING", "16 to 30 days", "Monitor upcoming expiry."],
              ["NORMAL", "More than 30 days", "Healthy remaining shelf life."],
          ], [35 * mm, 42 * mm, 83 * mm]),
          Paragraph("Low-stock calculation", styles["Subsection"]),
          p("For each medicine, the system sums current_quantity across all of its batches. If the total is lower than min_stock_threshold, the medicine appears as low stock on the dashboard and alert pages."),
          p("The custom web interface also supports an Enable alerts control. After the user enables it, a changed low-stock alert can produce an in-page popup, a short browser sound, and a browser notification when permission is granted.")]

story += section("9. FEFO Dispensing")
story += [p("FEFO means First Expiry, First Out. It is more appropriate for medicines than simply removing from the oldest database row or the newest stock entry."),
          p("Algorithm", "Subsection"),
          p("1. Find non-expired batches for the selected medicine with current_quantity > 0.\n2. Sort by expiry_date ascending.\n3. Check that the total available quantity is sufficient.\n4. Remove as much as possible from the earliest batch.\n5. Continue with later batches until the requested quantity is complete.\n6. Record an audit transaction for every affected batch.", "CodeBlock"),
          p("The availability check and deductions occur inside one database transaction. If the requested amount is not available, the operation raises an error and no partial deduction is committed."),
          p("Example: if batch A has 80 units and expires in 5 days, while batch B has 200 units and expires in 90 days, dispensing 100 units removes 80 from A and 20 from B.", "Callout")]

story += section("10. Stock Audit and Data Integrity")
story += [p("Every stock change creates a stock_transactions row. The record contains the type of operation, quantity changed, previous quantity, new quantity, reason, batch, medicine, and timestamp."),
          p("The system supports four transaction types: INITIAL, ADDED, REMOVED, and ADJUSTED."),
          p("Stock operations are atomic. The quantity update and transaction insert are inside one transaction context. If the audit insert fails, the quantity update is rolled back, preventing the database from showing a stock change with no explanation."),
          p("The database manager also uses a re-entrant lock and a thread-compatible SQLite connection so the shared data layer can serve Flask requests safely.")]

story += section("11. Reports, CSV, and Backups")
story += [Paragraph("Reports", styles["Subsection"]),
          bullet("Complete inventory report with medicine, batch, expiry, quantity, price, and supplier."),
          bullet("Expiry report for expired and near-expiry batches."),
          bullet("Low-stock report grouped by medicine threshold."),
          bullet("Stock movement report filtered by date."),
          bullet("Valuation report using current quantity multiplied by purchase price."),
          Paragraph("CSV", styles["Subsection"]),
          p("The project exports medicines, batches, and transactions as CSV. UTF-8 with a BOM is used for compatibility with Excel. Medicines can also be imported from CSV with validation."),
          Paragraph("Backup", styles["Subsection"]),
          p("A backup is a timestamped copy of the SQLite database. Metadata is written as JSON. Before restore, the current database receives a safety copy. This makes it possible to return to a previous snapshot without immediately losing the current state.")]

story += section("12. Validation, Errors, and Security")
story += [bullet("Medicine names cannot be empty."),
          bullet("Batch numbers cannot be empty."),
          bullet("Expiry must be after manufacturing date."),
          bullet("Quantities must be whole, nonnegative values."),
          bullet("Prices must be finite and nonnegative."),
          bullet("Stock removal cannot exceed available stock."),
          bullet("Parameterized SQL reduces SQL injection risk."),
          bullet("Service exceptions are shown as user-facing error messages in forms."),
          p("This is a local application and is not an authentication system. A production online deployment would need login, role-based permissions, HTTPS, a managed database, and a proper deployment server.", "Callout")]

story += section("13. Testing")
story += [p("The project uses Python unittest. The tests use separate temporary SQLite databases so normal test execution does not overwrite the user database."),
          table([
              ["Test area", "What is checked"],
              ["Validators", "Names, quantities, prices, dates, date ranges, batch numbers."],
              ["Medicines", "Create, update, search, category filtering, threshold validation."],
              ["Batches", "Creation, duplicate batch prevention, date checks, update protection."],
              ["Expiry", "Boundary values such as -1, 0, 7, 8, 15, 16, 30, and 31 days."],
              ["Stock", "Add, remove, correction, negative-stock prevention, FEFO, audit rows."],
              ["Reports", "Inventory, low-stock, valuation, and CSV export."],
              ["Backup", "Database snapshot creation, listing, restore path, and CSV import."],
          ], [37 * mm, 123 * mm]),
          p("The current project validation result is 38 tests passed, with all Python modules compiling successfully.", "Callout")]

story += section("14. Suggested Demonstration Sequence")
story += [p("Use this sequence during the presentation:"),
          table([
              ["Step", "Demonstration", "What to explain"],
              ["1", "Open the dashboard", "The dashboard aggregates live database values."],
              ["2", "Open Medicines", "Search, categories, thresholds, and catalog records."],
              ["3", "Add or show a medicine", "The record is saved in the medicines table."],
              ["4", "Open Batches", "One medicine can have multiple lots and expiry dates."],
              ["5", "Open Alerts", "The application classifies expiry risk and low stock."],
              ["6", "Use FEFO dispense", "The earliest-expiring valid batch is consumed first."],
              ["7", "Open Stock audit", "Before, after, quantity, reason, and timestamp are visible."],
              ["8", "Open Reports", "Inventory can be exported to CSV."],
              ["9", "Open Settings or backup workflow", "The SQLite database can be snapshotted and restored."],
              ["10", "Show tests", "Automated tests verify the important business rules."],
          ], [14 * mm, 58 * mm, 88 * mm])]

story += section("15. Viva Questions and Short Answers")
viva = [
    ("Why did you use batch-level inventory?", "Because batches have different expiry dates, suppliers, prices, and quantities. Batch tracking makes FEFO and expiry control possible."),
    ("Why SQLite?", "It is included with Python, works offline, stores the project in one file, supports relational constraints, and is easy to back up."),
    ("What is FEFO?", "First Expiry, First Out. The system dispenses from the valid batch with the earliest expiry date first."),
    ("How do you prevent negative stock?", "The service checks available quantity, the database has nonnegative checks for new schemas, and stock operations are transactional."),
    ("How is expiry status calculated?", "The system subtracts today's date from the stored ISO expiry date and maps the number of days to five urgency tiers."),
    ("How do you maintain an audit trail?", "Every initial entry, addition, removal, and correction inserts a stock transaction with previous and new quantities."),
    ("What happens if an operation fails?", "The transaction rolls back, so the quantity update and its audit row do not become inconsistent."),
    ("Can the system be used online?", "The Flask and Streamlit interfaces can run in a browser. For production, authentication and a managed database would be required."),
    ("What did you learn?", "Layered architecture, Python classes, SQL relationships, validation, transactions, algorithms, testing, file handling, and UI design."),
]
story.append(table([["Question", "Answer"]] + list(viva), [55 * mm, 105 * mm]))

story += section("16. Limitations and Future Improvements")
story += [bullet("Add authentication and user roles for online use."),
          bullet("Move from local SQLite to PostgreSQL for multi-user deployment."),
          bullet("Use soft deletion or archival for legally immutable audit history."),
          bullet("Add scheduled background notifications and email or WhatsApp alerts."),
          bullet("Add barcode or QR-code scanning."),
          bullet("Add supplier purchase orders and sales invoices."),
          bullet("Add charts for monthly stock movement and expiry loss."),
          bullet("Add PDF report export from the application itself."),
          p("These are future improvements; the current implementation already demonstrates the main inventory, expiry, FEFO, audit, reporting, backup, and testing workflows.")]

story += section("17. Final Presentation Summary")
story += [p("MediVault is not just a form that stores medicine names. It is a structured inventory system. The database separates medicines from batches, the services enforce rules, the FEFO algorithm reduces expiry waste, the alert system highlights risk, and the audit table explains every stock movement. Multiple interfaces demonstrate that the same business logic can support desktop and browser applications."),
          p("The strongest technical points to emphasize are: batch-level modeling, FEFO allocation, transactional stock operations, SQLite relational design, service-layer separation, input validation, CSV and backup utilities, notification support, and automated tests.", "Callout")]


doc = SimpleDocTemplate(
    str(OUTPUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
    topMargin=16 * mm, bottomMargin=20 * mm,
    title="MediVault Project Explanation Report",
    author="MediVault Project Team",
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUTPUT)
