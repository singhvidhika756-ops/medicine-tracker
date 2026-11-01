"""
test_stock.py — Unit tests for stock operations, FEFO selection, and audit trail in MediVault.
"""

import os
import unittest
from datetime import date, timedelta
from pathlib import Path

from database.connection import DatabaseManager
from database.schema import initialize_database
from services.medicine_service import MedicineService
from services.inventory_service import InventoryService


class TestStockOperations(unittest.TestCase):
    """Test suite covering stock add, reduce, bounds checking, FEFO dispensing, and audit logging."""

    TEST_DB = "data/test_stock.db"

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

        self.med_id = self.med_service.add_medicine(name="Paracetamol 500mg")
        self.today = date.today()

    def tearDown(self):
        self.db.close()
        test_db_path = Path(__file__).resolve().parent.parent / self.TEST_DB
        if test_db_path.exists():
            try:
                os.remove(test_db_path)
            except OSError:
                pass

    def test_add_stock(self):
        b_id = self.inv_service.add_batch(
            medicine_id=self.med_id,
            batch_number="B-STOCK-01",
            mfg_date="2026-01-01",
            exp_date="2027-01-01",
            purchase_date="2026-01-05",
            qty_received=100
        )
        self.inv_service.add_stock(b_id, 25, reason="Restock")
        batch = self.inv_service.get_batch(b_id)
        self.assertEqual(batch['current_quantity'], 125)

        # Check transaction log
        txns = self.inv_service.get_transactions(batch_id=b_id)
        self.assertEqual(len(txns), 2)  # 1 INITIAL + 1 ADDED
        self.assertEqual(txns[0]['transaction_type'], 'ADDED')  # DESC order
        self.assertEqual(txns[0]['quantity_changed'], 25)
        self.assertEqual(txns[0]['previous_quantity'], 100)
        self.assertEqual(txns[0]['new_quantity'], 125)

    def test_reduce_stock_success(self):
        b_id = self.inv_service.add_batch(
            medicine_id=self.med_id,
            batch_number="B-STOCK-02",
            mfg_date="2026-01-01",
            exp_date="2027-01-01",
            purchase_date="2026-01-05",
            qty_received=100
        )
        self.inv_service.reduce_stock(b_id, 30, reason="Sale")
        batch = self.inv_service.get_batch(b_id)
        self.assertEqual(batch['current_quantity'], 70)

        txns = self.inv_service.get_transactions(batch_id=b_id)
        self.assertEqual(txns[0]['transaction_type'], 'REMOVED')
        self.assertEqual(txns[0]['previous_quantity'], 100)
        self.assertEqual(txns[0]['new_quantity'], 70)

    def test_negative_stock_prevention(self):
        b_id = self.inv_service.add_batch(
            medicine_id=self.med_id,
            batch_number="B-STOCK-03",
            mfg_date="2026-01-01",
            exp_date="2027-01-01",
            purchase_date="2026-01-05",
            qty_received=50
        )
        # Attempting to remove 60 from 50 must raise ValueError
        with self.assertRaises(ValueError) as ctx:
            self.inv_service.reduce_stock(b_id, 60, reason="Invalid removal")
        self.assertIn("only 50 available", str(ctx.exception).lower())

        # Verify stock was untouched
        batch = self.inv_service.get_batch(b_id)
        self.assertEqual(batch['current_quantity'], 50)

    def test_fefo_stock_selection(self):
        """Verify First-Expired, First-Out consumes earliest expiring non-expired batch first."""
        # Batch 1: Expiring in 10 days, Qty 40
        b1_id = self.inv_service.add_batch(
            medicine_id=self.med_id,
            batch_number="FEFO-B1-EARLY",
            mfg_date="2026-01-01",
            exp_date=(self.today + timedelta(days=10)).strftime("%Y-%m-%d"),
            purchase_date="2026-01-05",
            qty_received=40
        )

        # Batch 2: Expiring in 60 days, Qty 60
        b2_id = self.inv_service.add_batch(
            medicine_id=self.med_id,
            batch_number="FEFO-B2-LATER",
            mfg_date="2026-01-01",
            exp_date=(self.today + timedelta(days=60)).strftime("%Y-%m-%d"),
            purchase_date="2026-01-05",
            qty_received=60
        )

        # Batch 3: Already expired (must be ignored by FEFO)
        b3_id = self.inv_service.add_batch(
            medicine_id=self.med_id,
            batch_number="FEFO-B3-EXPIRED",
            mfg_date="2025-01-01",
            exp_date=(self.today - timedelta(days=5)).strftime("%Y-%m-%d"),
            purchase_date="2025-01-05",
            qty_received=20
        )

        # Dispense 55 units via FEFO:
        # Should consume all 40 from Batch 1, and 15 from Batch 2!
        allocations = self.inv_service.reduce_stock_fefo(self.med_id, 55, reason="Prescription Dispense")
        self.assertEqual(len(allocations), 2)
        self.assertEqual(allocations[0], (b1_id, 40))
        self.assertEqual(allocations[1], (b2_id, 15))

        # Check resulting quantities
        b1 = self.inv_service.get_batch(b1_id)
        b2 = self.inv_service.get_batch(b2_id)
        b3 = self.inv_service.get_batch(b3_id)

        self.assertEqual(b1['current_quantity'], 0)
        self.assertEqual(b2['current_quantity'], 45)
        self.assertEqual(b3['current_quantity'], 20)  # Expired batch untouched

    def test_fefo_insufficient_stock_fails(self):
        b1_id = self.inv_service.add_batch(
            medicine_id=self.med_id,
            batch_number="FEFO-LIMIT-01",
            mfg_date="2026-01-01",
            exp_date=(self.today + timedelta(days=30)).strftime("%Y-%m-%d"),
            purchase_date="2026-01-05",
            qty_received=25
        )
        with self.assertRaises(ValueError) as ctx:
            self.inv_service.reduce_stock_fefo(self.med_id, 30)
        self.assertIn("insufficient stock", str(ctx.exception).lower())


if __name__ == '__main__':
    unittest.main()

