"""
sample_data.py — Demonstration Data Seeder for MediVault.

Populates the database with realistic medicines, suppliers, multiple batches
with various expiry profiles (expired, critical, warning, upcoming, healthy),
and stock movement histories for college demonstration and testing.

Run directly with:
    python sample_data.py
"""

from datetime import date, timedelta
from database.connection import DatabaseManager
from database.schema import initialize_database
from services.medicine_service import MedicineService
from services.inventory_service import InventoryService
from utils.logger import setup_logger

logger = setup_logger('medivault.sample_data')


def seed_sample_data(db: DatabaseManager, reset: bool = False):
    """
    Seed realistic demonstration data into the database.

    Args:
        db: An active DatabaseManager instance.
        reset: If True, clears existing tables before seeding.
    """
    initialize_database(db)

    if reset:
        logger.info("Clearing existing data...")
        db.execute("DELETE FROM stock_transactions")
        db.execute("DELETE FROM batches")
        db.execute("DELETE FROM medicines")
        db.execute("DELETE FROM suppliers")

    med_svc = MedicineService(db)
    inv_svc = InventoryService(db)

    # Check if data already exists
    existing = db.fetchone("SELECT COUNT(*) as c FROM medicines")
    if existing and existing['c'] > 0 and not reset:
        logger.info("Database already contains %d medicines. Skipping seed.", existing['c'])
        return

    today = date.today()

    # 1. Suppliers
    suppliers = [
        ("Apex Pharma Distributors", "Rajesh Sharma", "Mumbai, Maharashtra"),
        ("MedLife Healthcare Supply", "Anita Desai", "Bengaluru, Karnataka"),
        ("SunRise Generic Logistics", "Vikas Patel", "Ahmedabad, Gujarat"),
    ]
    for s_name, contact, addr in suppliers:
        db.execute(
            "INSERT OR IGNORE INTO suppliers (name, contact, address) VALUES (?, ?, ?)",
            (s_name, contact, addr)
        )

    # 2. Registered Medicines
    medicines = [
        {
            "name": "Paracetamol 500mg",
            "generic_name": "Acetaminophen",
            "category": "Analgesic",
            "manufacturer": "Cipla Ltd",
            "unit_type": "Tablet",
            "min_stock_threshold": 50,
            "description": "Standard pain relief and antipyretic medication.",
        },
        {
            "name": "Amoxicillin 250mg",
            "generic_name": "Amoxicillin Trihydrate",
            "category": "Antibiotic",
            "manufacturer": "Sun Pharma",
            "unit_type": "Capsule",
            "min_stock_threshold": 30,
            "description": "Broad-spectrum penicillin antibiotic.",
        },
        {
            "name": "Cetirizine 10mg",
            "generic_name": "Cetirizine Hydrochloride",
            "category": "ENT",
            "manufacturer": "Dr. Reddy's",
            "unit_type": "Tablet",
            "min_stock_threshold": 25,
            "description": "Second-generation antihistamine for allergic rhinitis.",
        },
        {
            "name": "Pantoprazole 40mg",
            "generic_name": "Pantoprazole Sodium",
            "category": "Antacid",
            "manufacturer": "Alkem Labs",
            "unit_type": "Tablet",
            "min_stock_threshold": 40,
            "description": "Proton-pump inhibitor for acid reflux and GERD.",
        },
        {
            "name": "Azithromycin 500mg",
            "generic_name": "Azithromycin",
            "category": "Antibiotic",
            "manufacturer": "Zydus Cadila",
            "unit_type": "Tablet",
            "min_stock_threshold": 20,
            "description": "Macrolide antibiotic for respiratory bacterial infections.",
        },
        {
            "name": "Metformin 500mg",
            "generic_name": "Metformin HCl",
            "category": "Diabetes",
            "manufacturer": "Torrent Pharma",
            "unit_type": "Tablet",
            "min_stock_threshold": 60,
            "description": "First-line oral antidiabetic for type 2 diabetes.",
        },
        {
            "name": "Ascoril-D Cough Syrup",
            "generic_name": "Dextromethorphan + Chlorpheniramine",
            "category": "Respiratory",
            "manufacturer": "Glenmark Pharma",
            "unit_type": "Syrup",
            "min_stock_threshold": 15,
            "description": "Sugar-free dry cough syrup 100ml.",
        },
        {
            "name": "Betadine 10% Ointment",
            "generic_name": "Povidone Iodine",
            "category": "Antiseptic",
            "manufacturer": "Win-Medicare",
            "unit_type": "Ointment",
            "min_stock_threshold": 10,
            "description": "Topical antiseptic microbicide 20g tube.",
        },
        {
            "name": "Neurobion Forte",
            "generic_name": "Vitamin B-Complex + B12",
            "category": "Vitamins & Supplements",
            "manufacturer": "Procter & Gamble Health",
            "unit_type": "Tablet",
            "min_stock_threshold": 50,
            "description": "Daily multivitamin supplement for nerve health.",
        },
        {
            "name": "Amlodipine 5mg",
            "generic_name": "Amlodipine Besylate",
            "category": "Cardiovascular",
            "manufacturer": "Lupin Ltd",
            "unit_type": "Tablet",
            "min_stock_threshold": 30,
            "description": "Calcium channel blocker for hypertension management.",
        },
    ]

    med_ids = {}
    for m in medicines:
        m_id = med_svc.add_medicine(
            name=m["name"],
            generic_name=m["generic_name"],
            category=m["category"],
            manufacturer=m["manufacturer"],
            description=m["description"],
            unit_type=m["unit_type"],
            min_stock_threshold=m["min_stock_threshold"],
        )
        med_ids[m["name"]] = m_id

    # 3. Batches with calculated dates matching demo scenarios
    batches = [
        # --- Paracetamol: Batch 1 (Expiring in 5 days — CRITICAL) ---
        {
            "med_name": "Paracetamol 500mg",
            "batch_number": "PCM-2024-B1",
            "mfg_offset": -360,
            "exp_offset": 5,      # 5 days from today (Critical alert!)
            "pur_offset": -180,
            "qty": 80,
            "purchase_price": 1.20,
            "selling_price": 2.50,
            "supplier": "Apex Pharma Distributors",
            "notes": "College demo batch: expiring in 5 days"
        },
        # --- Paracetamol: Batch 2 (Expiring in 90 days — HEALTHY/NORMAL) ---
        {
            "med_name": "Paracetamol 500mg",
            "batch_number": "PCM-2024-B2",
            "mfg_offset": -60,
            "exp_offset": 90,     # 90 days from today (Normal)
            "pur_offset": -30,
            "qty": 200,
            "purchase_price": 1.15,
            "selling_price": 2.50,
            "supplier": "Apex Pharma Distributors",
            "notes": "College demo batch: expiring in 90 days"
        },
        # --- Amoxicillin: Batch Expired 14 days ago (EXPIRED) ---
        {
            "med_name": "Amoxicillin 250mg",
            "batch_number": "AMX-EXP-01",
            "mfg_offset": -400,
            "exp_offset": -14,    # Expired 14 days ago!
            "pur_offset": -250,
            "qty": 15,
            "purchase_price": 4.50,
            "selling_price": 7.00,
            "supplier": "MedLife Healthcare Supply",
            "notes": "Expired demonstration batch for disposal flow"
        },
        # --- Cetirizine: Expiring in 3 days (CRITICAL) ---
        {
            "med_name": "Cetirizine 10mg",
            "batch_number": "CTZ-24-009",
            "mfg_offset": -300,
            "exp_offset": 3,      # 3 days remaining!
            "pur_offset": -120,
            "qty": 45,
            "purchase_price": 1.80,
            "selling_price": 3.50,
            "supplier": "SunRise Generic Logistics",
            "notes": "Urgent alert batch"
        },
        # --- Pantoprazole: Expiring in 11 days (WARNING: 8-15 days) ---
        {
            "med_name": "Pantoprazole 40mg",
            "batch_number": "PAN-24-331",
            "mfg_offset": -240,
            "exp_offset": 11,     # Warning bucket!
            "pur_offset": -90,
            "qty": 60,
            "purchase_price": 5.00,
            "selling_price": 9.00,
            "supplier": "Apex Pharma Distributors",
            "notes": "Warning tier demonstration batch"
        },
        # --- Azithromycin: Expiring in 24 days (UPCOMING: 16-30 days) ---
        {
            "med_name": "Azithromycin 500mg",
            "batch_number": "AZI-24-812",
            "mfg_offset": -180,
            "exp_offset": 24,     # Upcoming bucket!
            "pur_offset": -45,
            "qty": 30,
            "purchase_price": 18.00,
            "selling_price": 28.00,
            "supplier": "MedLife Healthcare Supply",
            "notes": "Upcoming expiry bucket"
        },
        # --- Metformin: Healthy Batch (180 days) ---
        {
            "med_name": "Metformin 500mg",
            "batch_number": "MET-24-101",
            "mfg_offset": -90,
            "exp_offset": 270,
            "pur_offset": -30,
            "qty": 150,
            "purchase_price": 2.10,
            "selling_price": 4.00,
            "supplier": "SunRise Generic Logistics",
            "notes": "Standard stock"
        },
        # --- Ascoril-D: Low Stock (only 5 units remaining, threshold is 15) ---
        {
            "med_name": "Ascoril-D Cough Syrup",
            "batch_number": "ASC-24-002",
            "mfg_offset": -120,
            "exp_offset": 160,
            "pur_offset": -60,
            "qty": 5,             # Under threshold of 15 (Low stock!)
            "purchase_price": 65.00,
            "selling_price": 95.00,
            "supplier": "Apex Pharma Distributors",
            "notes": "Low stock alert demonstration"
        },
        # --- Betadine Ointment: 8 units (Threshold is 10) ---
        {
            "med_name": "Betadine 10% Ointment",
            "batch_number": "BTD-24-555",
            "mfg_offset": -150,
            "exp_offset": 200,
            "pur_offset": -70,
            "qty": 8,
            "purchase_price": 40.00,
            "selling_price": 62.00,
            "supplier": "MedLife Healthcare Supply",
            "notes": "Antiseptic low stock"
        },
        # --- Neurobion Forte: 500 units (Normal) ---
        {
            "med_name": "Neurobion Forte",
            "batch_number": "NBF-24-909",
            "mfg_offset": -40,
            "exp_offset": 320,
            "pur_offset": -10,
            "qty": 500,
            "purchase_price": 1.60,
            "selling_price": 3.00,
            "supplier": "SunRise Generic Logistics",
            "notes": "High volume supplement stock"
        },
        # --- Amlodipine: 100 units (Normal) ---
        {
            "med_name": "Amlodipine 5mg",
            "batch_number": "AML-24-404",
            "mfg_offset": -100,
            "exp_offset": 250,
            "pur_offset": -50,
            "qty": 100,
            "purchase_price": 1.90,
            "selling_price": 3.80,
            "supplier": "Apex Pharma Distributors",
            "notes": "Cardio regular batch"
        },
    ]

    batch_ids = {}
    for b in batches:
        m_id = med_ids[b["med_name"]]
        mfg_d = (today + timedelta(days=b["mfg_offset"])).strftime("%Y-%m-%d")
        exp_d = (today + timedelta(days=b["exp_offset"])).strftime("%Y-%m-%d")
        pur_d = (today + timedelta(days=b["pur_offset"])).strftime("%Y-%m-%d")

        b_id = inv_svc.add_batch(
            medicine_id=m_id,
            batch_number=b["batch_number"],
            mfg_date=mfg_d,
            exp_date=exp_d,
            purchase_date=pur_d,
            qty_received=b["qty"],
            purchase_price=b["purchase_price"],
            selling_price=b["selling_price"],
            supplier=b["supplier"],
            notes=b["notes"]
        )
        batch_ids[b["batch_number"]] = b_id

    # 4. Perform a sample demonstration sale and stock adjustment
    # Dispense 10 units from Paracetamol Batch 1
    pcm_b1_id = batch_ids["PCM-2024-B1"]
    inv_svc.reduce_stock(pcm_b1_id, 10, reason="Over-the-counter sale to walk-in customer")

    # Add 50 units restock to Metformin
    met_id = batch_ids["MET-24-101"]
    inv_svc.add_stock(met_id, 50, reason="Vendor replenishment delivery")

    logger.info("Successfully seeded database with %d medicines and %d batches.", len(medicines), len(batches))
    print(f"\n[MediVault] Seed complete!")
    print(f" -> {len(medicines)} medicines added.")
    print(f" -> {len(batches)} batches registered across all expiry tiers.")
    print(f" -> Paracetamol: 2 batches (Batch 1 expiring in 5 days, Batch 2 expiring in 90 days).")
    print(f" -> 1 expired batch, 2 critical batches, 1 warning, 1 upcoming, 2 low-stock medicines.")


if __name__ == "__main__":
    db = DatabaseManager()
    seed_sample_data(db, reset=True)
    db.close()

