"""
test_medicines.py — Unit and integration tests for Medicine CRUD operations in MediVault.
"""

import os
import unittest
from pathlib import Path

from database.connection import DatabaseManager
from database.schema import initialize_database
from services.medicine_service import MedicineService
from services.inventory_service import InventoryService


class TestMedicineService(unittest.TestCase):
    """Test suite for MedicineService CRUD and filtering."""

    TEST_DB = "data/test_medicines.db"

    def setUp(self):
        # Remove any previous test DB
        test_db_path = Path(__file__).resolve().parent.parent / self.TEST_DB
        if test_db_path.exists():
            try:
                os.remove(test_db_path)
            except OSError:
                pass

        self.db = DatabaseManager(self.TEST_DB)
        initialize_database(self.db)
        self.service = MedicineService(self.db)
        self.inv_service = InventoryService(self.db)

    def tearDown(self):
        self.db.close()
        test_db_path = Path(__file__).resolve().parent.parent / self.TEST_DB
        if test_db_path.exists():
            try:
                os.remove(test_db_path)
            except OSError:
                pass

    def test_add_medicine(self):
        med_id = self.service.add_medicine(
            name="Ibuprofen 400mg",
            generic_name="Ibuprofen",
            category="Analgesic",
            manufacturer="Abbott",
            description="Pain and inflammation relief",
            unit_type="Tablet",
            min_stock_threshold=20
        )
        self.assertIsInstance(med_id, int)
        self.assertGreater(med_id, 0)

        # Retrieve and verify
        med = self.service.get_medicine(med_id)
        self.assertIsNotNone(med)
        self.assertEqual(med['name'], "Ibuprofen 400mg")
        self.assertEqual(med['category'], "Analgesic")
        self.assertEqual(med['min_stock_threshold'], 20)

    def test_add_medicine_empty_name_fails(self):
        with self.assertRaises(ValueError):
            self.service.add_medicine(name="")

        with self.assertRaises(ValueError):
            self.service.add_medicine(name="   ")

    def test_add_medicine_negative_threshold_fails(self):
        with self.assertRaises(ValueError):
            self.service.add_medicine(name="Aspirin", min_stock_threshold=-5)

    def test_update_medicine(self):
        med_id = self.service.add_medicine(name="Aspirin 75mg", category="Analgesic")
        success = self.service.update_medicine(
            medicine_id=med_id,
            name="Aspirin Cardio 75mg",
            category="Cardiovascular",
            min_stock_threshold=50
        )
        self.assertTrue(success)

        med = self.service.get_medicine(med_id)
        self.assertEqual(med['name'], "Aspirin Cardio 75mg")
        self.assertEqual(med['category'], "Cardiovascular")
        self.assertEqual(med['min_stock_threshold'], 50)

    def test_delete_medicine_cascades_batches(self):
        med_id = self.service.add_medicine(name="Amoxicillin 500mg")
        batch_id = self.inv_service.add_batch(
            medicine_id=med_id,
            batch_number="AMX-001",
            mfg_date="2026-01-01",
            exp_date="2027-01-01",
            purchase_date="2026-01-10",
            qty_received=100
        )

        # Verify batch exists
        self.assertIsNotNone(self.inv_service.get_batch(batch_id))

        # Delete medicine
        deleted = self.service.delete_medicine(med_id)
        self.assertTrue(deleted)

        # Medicine should be gone
        self.assertIsNone(self.service.get_medicine(med_id))

        # Associated batch must be deleted automatically via ON DELETE CASCADE
        self.assertIsNone(self.inv_service.get_batch(batch_id))

    def test_search_and_filter_medicines(self):
        self.service.add_medicine(name="Paracetamol 500mg", generic_name="Acetaminophen", category="Analgesic")
        self.service.add_medicine(name="Paracetamol 650mg", generic_name="Acetaminophen", category="Analgesic")
        self.service.add_medicine(name="Amoxicillin 250mg", generic_name="Amoxicillin", category="Antibiotic")

        # Search by name
        results = self.service.search_medicines(query="Paracetamol")
        self.assertEqual(len(results), 2)

        # Search by generic name
        results_gen = self.service.search_medicines(query="Acetaminophen")
        self.assertEqual(len(results_gen), 2)

        # Filter by category
        results_cat = self.service.search_medicines(category="Antibiotic")
        self.assertEqual(len(results_cat), 1)
        self.assertEqual(results_cat[0]['name'], "Amoxicillin 250mg")


if __name__ == '__main__':
    unittest.main()

