"""
test_reports.py — Unit tests for reporting and CSV generation in MediVault.
"""

import os
import csv
import unittest
from datetime import date, timedelta
from pathlib import Path

from database.connection import DatabaseManager
from database.schema import initialize_database
from services.medicine_service import MedicineService
from services.inventory_service import InventoryService
from services.report_service import ReportService


class TestReportsAndExports(unittest.TestCase):
    """Test suite for analytical report compilation and CSV exports."""

    TEST_DB = "data/test_reports.db"
    EXPORT_CSV = "data/test_export.csv"

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
        self.report_service = ReportService(self.db)

        # Create sample medicine & batches
        self.med_id = self.med_service.add_medicine(
            name="Test Capsule",
            category="Antibiotic",
            min_stock_threshold=50
        )
        self.inv_service.add_batch(
            medicine_id=self.med_id,
            batch_number="REP-B1",
            mfg_date="2026-01-01",
            exp_date=(date.today() + timedelta(days=20)).strftime("%Y-%m-%d"),
            purchase_date="2026-01-10",
            qty_received=30,  # Below threshold 50 -> low stock!
            purchase_price=5.00
        )

    def tearDown(self):
        self.db.close()
        for filename in (self.TEST_DB, self.EXPORT_CSV):
            p = Path(__file__).resolve().parent.parent / filename
            if p.exists():
                try:
                    os.remove(p)
                except OSError:
                    pass

    def test_inventory_report(self):
        report = self.report_service.generate_inventory_report()
        self.assertEqual(len(report), 1)
        self.assertEqual(report[0]['medicine_name'], "Test Capsule")
        self.assertEqual(report[0]['batch_number'], "REP-B1")
        self.assertEqual(report[0]['current_quantity'], 30)

    def test_low_stock_report(self):
        low_stock = self.report_service.generate_low_stock_report()
        self.assertEqual(len(low_stock), 1)
        self.assertEqual(low_stock[0]['name'], "Test Capsule")
        self.assertEqual(low_stock[0]['total_stock'], 30)
        self.assertEqual(low_stock[0]['min_stock_threshold'], 50)

    def test_valuation_report(self):
        valuation = self.report_service.generate_valuation_report()
        self.assertEqual(len(valuation), 1)
        self.assertEqual(valuation[0]['medicine_name'], "Test Capsule")
        self.assertEqual(valuation[0]['value'], 150.0)  # 30 * 5.00

    def test_csv_export_file(self):
        report = self.report_service.generate_inventory_report()
        headers = ['medicine_name', 'batch_number', 'current_quantity', 'purchase_price']
        export_path = Path(__file__).resolve().parent.parent / self.EXPORT_CSV

        success = ReportService.export_to_csv(report, headers, str(export_path))
        self.assertTrue(success)
        self.assertTrue(export_path.exists())

        # Read back and verify CSV content
        with open(export_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['medicine_name'], "Test Capsule")
            self.assertEqual(rows[0]['batch_number'], "REP-B1")
            self.assertEqual(int(rows[0]['current_quantity']), 30)


if __name__ == '__main__':
    unittest.main()

