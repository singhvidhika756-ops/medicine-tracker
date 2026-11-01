"""
test_batches.py — Unit tests for batch management and unique constraints in MediVault.
"""

import os
import unittest
import sqlite3
from pathlib import Path

from database.connection import DatabaseManager
from database.schema import initialize_database
from services.medicine_service import MedicineService
from services.inventory_service import InventoryService


class TestBatchManagement(unittest.TestCase):
    """Test suite for batch CRUD, unique constraints, and stock creation."""

    TEST_DB = "data/test_batches.db"

    def setUp(self):
        test_db_path = Path(__file__).resolve().parent.parent / self.TEST_DB
        if test_db_path.exists():
            try:
                os.remove(test_db_path)
            except OSError:
                pass

        self.db = DatabaseManager(self.TEST_DB)
        initialize_database(self.db)
        self.med_service = MedicineService(self.db)
        self.inv_service = InventoryService(self.db)

        # Base medicines for testing
        self.med1_id = self.med_service.add_medicine(name="Paracetamol 500mg")
        self.med2_id = self.med_service.add_medicine(name="Cetirizine 10mg")

    def tearDown(self):
        self.db.close()
        test_db_path = Path(__file__).resolve().parent.parent / self.TEST_DB
        if test_db_path.exists():
            try:
                os.remove(test_db_path)
            except OSError:
                pass

    def test_add_batch_success(self):
        batch_id = self.inv_service.add_batch(
            medicine_id=self.med1_id,
            batch_number="BATCH-A1",
            mfg_date="2026-01-01",
            exp_date="2027-01-01",
            purchase_date="2026-01-05",
            qty_received=150,
            purchase_price=2.50,
            selling_price=4.00,
            supplier="Apex Pharma"
        )
        self.assertGreater(batch_id, 0)

        batch = self.inv_service.get_batch(batch_id)
        self.assertEqual(batch['batch_number'], "BATCH-A1")
        self.assertEqual(batch['current_quantity'], 150)
        self.assertEqual(batch['purchase_price'], 2.50)

        # Check that INITIAL stock transaction was automatically created
        txns = self.inv_service.get_transactions(batch_id=batch_id)
        self.assertEqual(len(txns), 1)
        self.assertEqual(txns[0]['transaction_type'], 'INITIAL')
        self.assertEqual(txns[0]['quantity_changed'], 150)
        self.assertEqual(txns[0]['new_quantity'], 150)

    def test_duplicate_batch_number_same_medicine_fails(self):
        # First batch succeeds
        self.inv_service.add_batch(
            medicine_id=self.med1_id,
            batch_number="BATCH-DUP-1",
            mfg_date="2026-01-01",
            exp_date="2027-01-01",
            purchase_date="2026-01-05",
            qty_received=100
        )

        # Second batch with same batch_number and same medicine_id must fail!
        with self.assertRaises(sqlite3.IntegrityError):
            self.inv_service.add_batch(
                medicine_id=self.med1_id,
                batch_number="BATCH-DUP-1",
                mfg_date="2026-02-01",
                exp_date="2027-02-01",
                purchase_date="2026-02-05",
                qty_received=50
            )

    def test_same_batch_number_different_medicine_allowed(self):
        # Batch for medicine 1
        b1 = self.inv_service.add_batch(
            medicine_id=self.med1_id,
            batch_number="COMMON-LOT-01",
            mfg_date="2026-01-01",
            exp_date="2027-01-01",
            purchase_date="2026-01-05",
            qty_received=100
        )
        # Same batch number for medicine 2 should succeed
        b2 = self.inv_service.add_batch(
            medicine_id=self.med2_id,
            batch_number="COMMON-LOT-01",
            mfg_date="2026-01-01",
            exp_date="2027-01-01",
            purchase_date="2026-01-05",
            qty_received=80
        )
        self.assertNotEqual(b1, b2)

    def test_expiry_before_mfg_fails(self):
        with self.assertRaises(ValueError):
            self.inv_service.add_batch(
                medicine_id=self.med1_id,
                batch_number="INV-DATES",
                mfg_date="2026-12-01",
                exp_date="2026-01-01",  # Invalid: before mfg
                purchase_date="2026-12-01",
                qty_received=50
            )

    def test_update_batch(self):
        b_id = self.inv_service.add_batch(
            medicine_id=self.med1_id,
            batch_number="UPD-01",
            mfg_date="2026-01-01",
            exp_date="2027-01-01",
            purchase_date="2026-01-05",
            qty_received=100,
            purchase_price=2.00
        )
        updated = self.inv_service.update_batch(b_id, purchase_price=2.75, supplier="New Supplier")
        self.assertTrue(updated)

        batch = self.inv_service.get_batch(b_id)
        self.assertEqual(batch['purchase_price'], 2.75)
        self.assertEqual(batch['supplier'], "New Supplier")

        self.assertFalse(self.inv_service.update_batch(b_id, current_quantity=1))
        self.assertEqual(self.inv_service.get_batch(b_id)['current_quantity'], 100)

    def test_invalid_purchase_date_fails(self):
        with self.assertRaises(ValueError):
            self.inv_service.add_batch(
                medicine_id=self.med1_id,
                batch_number="INVALID-DATE",
                mfg_date="2026-01-01",
                exp_date="2027-01-01",
                purchase_date="not-a-date",
                qty_received=10,
            )


if __name__ == '__main__':
    unittest.main()

