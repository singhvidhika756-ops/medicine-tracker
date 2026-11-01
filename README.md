# 💊 MediVault — Medicine Inventory & Expiry Management System

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite3-003B57.svg)](https://www.sqlite.org/)
[![UI Framework](https://img.shields.io/badge/GUI-Tkinter%20%2F%20ttk-orange.svg)](https://docs.python.org/3/library/tkinter.html)
[![Test Suite](https://img.shields.io/badge/Tests-36%20Passed%20(100%25)-brightgreen.svg)](tests/)
[![Offline](https://img.shields.io/badge/Network-100%25%20Offline-success.svg)](#)

A polished, local desktop application built in standard Python designed for small pharmacy stores, clinics, and household medical cabinets to track medicine stocks, monitor batch-level expiry dates, execute **FEFO (First-Expired, First-Out)** stock selection, and maintain an immutable transaction audit log.

---

## 📑 Table of Contents
1. [Project Highlights & Features](#-project-highlights--features)
2. [First-Year Python Concepts Demonstrated](#-first-year-python-concepts-demonstrated)
3. [Project Architecture](#-project-architecture)
4. [Database Design & Schema](#-database-design--schema)
5. [Smart Expiry Classification & FEFO Algorithm](#-smart-expiry-classification--fefo-algorithm)
6. [Installation & Quickstart](#-installation--quickstart)
7. [Step-by-Step College Demo Sequence](#-step-by-step-college-demo-sequence)
8. [Automated Test Suite](#-automated-test-suite)
9. [Viva & Examiner Q&A Guide](#-viva--examiner-qa-guide)

---

## 🌟 Project Highlights & Features

### Level 1 — Core Essentials
- **Medicine Catalog Management**: Register medicines with brand name, generic INN name, therapeutic category, dosage form, manufacturer, and low-stock threshold.
- **Batch Tracking**: Each medicine can have multiple independent batches with distinct manufacturing dates, expiry dates, purchase prices, and suppliers.
- **Stock Movement Logging**: Every addition, removal, sale, or correction is recorded in an immutable audit table.
- **Instant Search & Filtering**: Filter by category, or search across trade and generic names with real-time feedback.
- **Local Persistence**: Zero-dependency SQLite database with active foreign key cascade enforcement.

### Level 2 — Advanced Practical Features
- **Smart Expiry Urgency Tiers**: Automatic categorization into **Expired** ($<0$ days), **Critical** ($0\le\text{days}\le7$), **Warning** ($8\le\text{days}\le15$), **Upcoming** ($16\le\text{days}\le30$), and **Normal** ($>30$ days).
- **FEFO (First-Expired, First-Out) Dispensing**: Automatically deducts units starting from the nearest-expiring non-expired batch to prevent medicine wastage.
- **Analytical Reports & CSV Export**: Generate complete inventory, low-stock deficit, expiry risk, and financial valuation reports, with one-click export to CSV (compatible with Excel).
- **Themes**: Instant toggle between Light Mode and Dark Mode with custom ttk styles.
- **Database Backup & Snapshot Restore**: One-click timestamped database snapshots with JSON metadata and safe rollback before restoring.

---

## 🎓 First-Year Python Concepts Demonstrated

MediVault avoids complicated enterprise frameworks and instead showcases strong, idiomatic Python fundamentals:

| Python Concept | Where It Is Used in MediVault |
|---|---|
| **Classes & Object-Oriented Programming** | `Medicine`, `Batch`, and `StockTransaction` data models (`models/`); `MediVaultApp` (`ui/app.py`). |
| **Relational Database with SQLite3** | Parameterized SQL queries (`?`), schema creation, foreign key enforcement (`PRAGMA foreign_keys = ON`), composite `UNIQUE(medicine_id, batch_number)`. |
| **Data Structures & Slicing** | Lists of dictionaries for table rows, set comprehensions for deduplication, dictionary lookup tables for $O(1)$ ID resolution. |
| **Exception Handling & Validation** | Defensive programming via `validate_medicine_name`, `validate_date_range`, and custom `ValueError` handling for negative stock prevention. |
| **Algorithms (FEFO & Greedy Depletion)** | Sequential consumption of batches ordered by `expiry_date ASC` until requested units are fulfilled (`services/inventory_service.py`). |
| **File Handling & Serialization** | CSV export/import (`csv.DictWriter` with `utf-8-sig` encoding), JSON metadata generation (`json.dump`), safe file copying (`shutil.copy2`). |
| **Event-Driven GUI Programming** | Tkinter widgets, event bindings (`<Configure>`, `<<ComboboxSelected>>`, `<Double-1>`), modal dialog windows (`Toplevel`), frame switching. |
| **Automated Testing** | Standard library `unittest` suite with boundary value analysis and mock test databases. |

---

## 🏗️ Project Architecture

MediVault follows a 3-tier modular architecture:

```
MediVault/
├── main.py                     # Application startup entry point
├── sample_data.py              # Realistic demo data seeder
├── requirements.txt            # Package manifest
├── README.md                   # Complete documentation & viva guide
│
├── database/                   # Data Access Layer
│   ├── connection.py           # Thread-safe SQLite manager & PRAGMA foreign_keys
│   └── schema.py               # DDL table creation and default settings
│
├── models/                     # OOP Domain Entities
│   ├── medicine.py             # Medicine dataclass & constants (Categories, Units)
│   ├── batch.py                # Batch dataclass with computed days_until_expiry
│   └── transaction.py          # StockTransaction dataclass
│
├── services/                   # Business Logic Layer (Pure Python)
│   ├── medicine_service.py     # Medicine CRUD, search, and category queries
│   ├── inventory_service.py    # Batches, stock in/out, adjustments, and FEFO algorithm
│   ├── expiry_service.py       # Expiry date mathematics and urgency classification
│   └── report_service.py       # Statistical aggregations and CSV file export
│
├── ui/                         # Presentation Layer (Tkinter / ttk)
│   ├── app.py                  # Main window, navigation sidebar, and view switcher
│   ├── themes.py               # Light & Dark color palettes and ttk style configs
│   ├── widgets.py              # Reusable components (DataTable, StatCard, SearchBar, FormField)
│   ├── dashboard.py            # KPI metric cards, alert banner, and recent movements
│   ├── medicines.py            # Medicine catalog table + Add/Edit modal dialogs
│   ├── batches.py              # Batch management + Quick stock in/out dialogs
│   ├── alerts.py               # Expiry urgency tabs (Expired, ≤7d, ≤15d, ≤30d, Low-stock)
│   ├── stock.py                # FEFO stock dispenser and complete audit log
│   ├── reports.py              # Multi-report generator with live preview and CSV export
│   └── settings.py             # Theme toggle, database backup snapshots, and CSV import/export
│
├── utils/                      # Helper Utilities
│   ├── validators.py           # String, date, price, and quantity validators
│   ├── backup.py               # Timestamped DB backups, restore safety, and CSV utils
│   └── logger.py               # File and console logger configuration
│
└── tests/                      # Automated Test Suite (Python unittest)
    ├── test_validators.py      # Input validation boundary tests
    ├── test_medicines.py       # Medicine CRUD & cascade deletion tests
    ├── test_batches.py         # Batch unique constraints & relational checks
    ├── test_expiry.py          # Boundary tests for -1, 0, 1, 7, 8, 15, 16, 30, 31 days
    ├── test_stock.py           # Stock bounds, zero limits, FEFO greedy picking, audit logs
    ├── test_reports.py         # Analytics and CSV export verification
    └── test_backup.py          # Database snapshot and CSV import tests
```

---

## 🗄️ Database Design & Schema

```
┌─────────────────────────┐         ┌─────────────────────────────────┐
│        medicines        │ 1     * │             batches             │
├─────────────────────────┤─────────├─────────────────────────────────┤
│ medicine_id (PK)        │         │ batch_id (PK)                   │
│ name                    │         │ medicine_id (FK -> medicines)   │
│ generic_name            │         │ batch_number                    │
│ category                │         │ manufacturing_date              │
│ manufacturer            │         │ expiry_date                     │
│ description             │         │ purchase_date                   │
│ unit_type               │         │ quantity_received               │
│ min_stock_threshold     │         │ current_quantity                │
│ created_at, updated_at  │         │ purchase_price, selling_price   │
└─────────────────────────┘         │ supplier, notes                 │
                                    └────────────────┬────────────────┘
                                                     │ 1
                                                     │ *
                                    ┌────────────────┴────────────────┐
                                    │       stock_transactions        │
                                    ├─────────────────────────────────┤
                                    │ transaction_id (PK)             │
                                    │ batch_id (FK -> batches)        │
                                    │ medicine_id (FK -> medicines)   │
                                    │ transaction_type                │
                                    │ quantity_changed                │
                                    │ previous_quantity               │
                                    │ new_quantity                    │
                                    │ reason                          │
                                    │ transaction_date                │
                                    └─────────────────────────────────┘
```

### Key Relational Safeguards
1. **Foreign Key Enforcement**: `PRAGMA foreign_keys = ON;` is executed on every connection.
2. **Cascade Deletion**: If a medicine is deleted, all its batches and historical transactions are automatically cleared to avoid orphaned rows.
3. **Duplicate Batch Prevention**: SQLite enforces `UNIQUE(medicine_id, batch_number)`. Medicine A can have batch `B1`, but cannot have two batches named `B1`. However, Medicine B can also have a batch named `B1`.
4. **Parameterized Queries**: All queries bind parameters with `?` placeholders, eliminating SQL injection.

---

## ⏱️ Smart Expiry Classification & FEFO Algorithm

### 1. Expiry Mathematical Formula
Stored in ISO format (`YYYY-MM-DD`):
$$\text{days\_remaining} = (\text{expiry\_date} - \text{today}).\text{days}$$

| Status | Condition | Meaning | UI Badge / Color |
|---|---|---|---|
| **EXPIRED** | $\text{days} < 0$ | Past expiry date | Red (`#EF4444`) |
| **CRITICAL** | $0 \le \text{days} \le 7$ | Expiring within 1 week | Dark Orange (`#EA580C`) |
| **WARNING** | $8 \le \text{days} \le 15$ | Expiring within 2 weeks | Amber (`#D97706`) |
| **UPCOMING** | $16 \le \text{days} \le 30$ | Expiring within 1 month | Yellow-Green (`#65A30D`) |
| **NORMAL** | $\text{days} > 30$ | Healthy shelf life | Green (`#10B981`) |

### 2. FEFO Algorithm Pseudocode
When a user sells/dispenses $Q$ units of medicine $M$:
```text
1. Fetch all batches for medicine M where expiry_date >= today and current_quantity > 0.
2. Order by expiry_date ASC (earliest expiring first).
3. If SUM(current_quantity) < Q:
       Raise InsufficientStockError.
4. RemainingToDeduct = Q
5. For each batch B in ordered batches:
       Take = MIN(RemainingToDeduct, B.current_quantity)
       B.current_quantity -= Take
       Record StockTransaction(Type='REMOVED', Quantity=Take, Reason=Reason)
       RemainingToDeduct -= Take
       If RemainingToDeduct == 0:
           Break
```

---

## 🚀 Installation & Quickstart

### Prerequisites
- **Windows 10 or 11**
- **Python 3.10+** (Standard installation with Tkinter selected)

### 1. Run MediVault
Open PowerShell or Command Prompt, navigate to the folder, and run:
```powershell
cd d:\vidhu\MediVault
python main.py
```

### 1b. Run the Streamlit interface

Install the dependencies and start the Streamlit server:
```powershell
py -3.14 -m pip install -r requirements.txt
py -3.14 -m streamlit run app.py
```
Streamlit opens the application in a browser, normally at http://localhost:8501. The interface uses the same
SQLite database and service layer as the desktop application.

### 1c. Deploy the original Flask UI on Vercel

The original custom HTML/CSS/JavaScript interface is Vercel-ready:
1. Open https://vercel.com and sign in with GitHub.
2. Click **Add New Project** and import `singhvidhika756-ops/medicine-tracker`.
3. Keep the detected framework as **Other**.
4. Deploy the project. Vercel uses `vercel.json` and `api/index.py` automatically.

This publishes the original UI from `templates/` and `static/`, not the Streamlit UI.
The Vercel demo uses a temporary SQLite file in `/tmp`; use a hosted PostgreSQL database
for permanent online data. Vercel is configured to seed the sample inventory when that
temporary database is empty, so the public demo starts with example records.

### 2. Populate Sample Data (For Demo)
If you want to immediately explore the system with realistic data:
```powershell
python sample_data.py
```
This populates 10 medicines, 11 batches across all expiry tiers, and sample transactions.

---

## 🎬 Step-by-Step College Demo Sequence

Follow this exact sequence to demonstrate the system to your examiner:

1. **Launch the Application**:
   ```powershell
   python main.py
   ```
   Show the **Dashboard**: Point out the 8 KPI stat cards (Total Medicines, Batches, Units, Value, Expired, Critical, Upcoming, Low Stock).

2. **Add Paracetamol with Two Different Batches**:
   - Go to **Medicines** ➔ Click `➕ Add Medicine`.
   - Name: `Paracetamol 500mg`, Category: `Analgesic`, Unit: `Tablet`, Threshold: `50`. Save it.
   - Go to **Batches** ➔ Click `➕ Register Batch`.
     - Batch 1: Number `PCM-B1`, Expiry: Set date to **5 days from today** (e.g. `2026-11-06`), Qty: `80`.
     - Batch 2: Number `PCM-B2`, Expiry: Set date to **90 days from today** (e.g. `2027-02-01`), Qty: `200`.

3. **Demonstrate Expiry Alerts**:
   - Go to **Expiry Alerts** page.
   - Show that Batch 1 appears under the **⚠️ Critical (≤7d)** tab because it expires in 5 days!
   - Show that Batch 2 is in the **Normal** category and does not raise an alert.

4. **Demonstrate FEFO Stock Dispensing**:
   - Go to **Stock** page ➔ Click `⚡ FEFO Dispense`.
   - Select `Paracetamol 500mg` and request `100 units`.
   - Explain to the examiner: *"Because we use FEFO, MediVault automatically takes all 80 units from the 5-day batch first, and takes the remaining 20 units from the 90-day batch!"*
   - Click Confirm. Show the success breakdown dialog.

5. **Inspect the Immutable Audit Trail**:
   - Look at the **Stock Operations & Audit Log** table on the same page.
   - Show that every transaction logs `Timestamp`, `Medicine`, `Batch #`, `Type (REMOVED)`, `Before`, `After`, and `Reason`.

6. **Search & Filter**:
   - Go to **Medicines** page. Type `Paracetamol` in the search bar. Show real-time filtering.
   - Filter by category `Analgesic`.

7. **Generate & Export CSV Report**:
   - Go to **Reports** page. Select `Complete Inventory Report`.
   - Click `📥 Export to CSV` and save the file. Open it to show Excel compatibility!

8. **Prove Data Persistence**:
   - Close MediVault.
   - Run `python main.py` again.
   - All records, batch quantities, and transactions remain intact!

---

## 🧪 Automated Test Suite

MediVault includes **36 automated unit tests** covering all business rules:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

### Test Coverage Summary
- `test_validators.py`: Input format validation (names, numbers, prices, YYYY-MM-DD dates, date ranges).
- `test_medicines.py`: Medicine CRUD, search, category filters, and ON DELETE CASCADE.
- `test_batches.py`: Batch CRUD, composite `UNIQUE(medicine_id, batch_number)`, date checks.
- `test_expiry.py`: Boundary tests for -10, -1, 0 (today), 1 (tomorrow), 7, 8, 15, 16, 30, 31, 90 days.
- `test_stock.py`: Stock addition, removal, negative stock prevention, and FEFO allocation logic.
- `test_reports.py`: Inventory, low-stock, valuation reports, and CSV file creation.
- `test_backup.py`: Timestamped database snapshots and CSV bulk import.

---

## 💬 Viva & Examiner Q&A Guide

Here are the top questions examiners typically ask for this project, along with your recommended answers:

### Q1: Why did you track stock by batch instead of just by medicine name?
> **Answer**: *"In pharmaceuticals, each production batch has a unique manufacturing and expiry date. If we only stored a single quantity on the medicine record, we couldn't know which units expire first, leading to expired medicines being dispensed or wasted. Batch-level tracking enables FEFO (First-Expired, First-Out) inventory control."*

### Q2: How does your system prevent negative stock?
> **Answer**: *"We enforce this at two levels: First, in the SQLite schema using `CHECK (current_quantity >= 0)`. Second, in `InventoryService.reduce_stock()`, the code checks `if quantity > current_quantity:` and raises a `ValueError` before executing any SQL statement."*

### Q3: How do you prevent duplicate batches?
> **Answer**: *"We use a composite UNIQUE constraint in SQLite: `UNIQUE(medicine_id, batch_number)`. This ensures that a single medicine cannot have two batches with the same lot number, while still allowing two different medicines to share a lot number if produced by the same factory."*

### Q4: How is the expiry status calculated?
> **Answer**: *"Dates are stored in ISO 8601 string format (`YYYY-MM-DD`). We parse them using Python's standard `datetime.strptime()` and compute `(expiry_date - date.today()).days`. If negative, it's Expired; 0 to 7 days is Critical; 8 to 15 days is Warning; 16 to 30 days is Upcoming; and above 30 days is Normal."*

### Q5: What happens if I delete a medicine that has batches?
> **Answer**: *"Because we enable `PRAGMA foreign_keys = ON;` and define `FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id) ON DELETE CASCADE`, deleting a medicine automatically and safely removes all its associated batches and transactions, avoiding orphaned records."*

---

## 👥 Authors & Academic Context
- **Project**: MediVault — Medicine Inventory & Expiry Management System
- **Year**: First-Year College Programming Project (B.Tech / B.Sc / BCA)
- **Language**: Python 3
- **License**: MIT Academic License

