"""
test_expiry.py — Boundary tests for expiry classification and alerts in MediVault.
"""

import os
import unittest
from datetime import date, timedelta
from pathlib import Path

from database.connection import DatabaseManager
from database.schema import initialize_database
from services.medicine_service import MedicineService
from services.inventory_service import InventoryService
from services.expiry_service import ExpiryService


class TestExpiryClassification(unittest.TestCase):
    """Test suite covering exact boundary dates for expiry categorization."""

    TEST_DB = "data/test_expiry.db"

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
        self.expiry_service = ExpiryService(self.db)

        self.today = date.today()

    def tearDown(self):
        self.db.close()
        test_db_path = Path(__file__).resolve().parent.parent / self.TEST_DB
        if test_db_path.exists():
            try:
                os.remove(test_db_path)
            except OSError:
                pass

    def test_pure_logic_boundaries(self):
        """Test get_expiry_status static boundary calculations."""
        # Expired: past dates
        exp_yesterday = (self.today - timedelta(days=1)).strftime("%Y-%m-%d")
        status, days = ExpiryService.get_expiry_status(exp_yesterday)
        self.assertEqual(status, 'EXPIRED')
        self.assertEqual(days, -1)

        exp_past_10 = (self.today - timedelta(days=10)).strftime("%Y-%m-%d")
        status, days = ExpiryService.get_expiry_status(exp_past_10)
        self.assertEqual(status, 'EXPIRED')
        self.assertEqual(days, -10)

        # Critical: 0 to 7 days
        exp_today = self.today.strftime("%Y-%m-%d")
        status, days = ExpiryService.get_expiry_status(exp_today)
        self.assertEqual(status, 'CRITICAL')
        self.assertEqual(days, 0)

        exp_tomorrow = (self.today + timedelta(days=1)).strftime("%Y-%m-%d")
        status, days = ExpiryService.get_expiry_status(exp_tomorrow)
        self.assertEqual(status, 'CRITICAL')
        self.assertEqual(days, 1)

        exp_day_7 = (self.today + timedelta(days=7)).strftime("%Y-%m-%d")
        status, days = ExpiryService.get_expiry_status(exp_day_7)
        self.assertEqual(status, 'CRITICAL')
        self.assertEqual(days, 7)

        # Warning: 8 to 15 days
        exp_day_8 = (self.today + timedelta(days=8)).strftime("%Y-%m-%d")
        status, days = ExpiryService.get_expiry_status(exp_day_8)
        self.assertEqual(status, 'WARNING')
        self.assertEqual(days, 8)

        exp_day_15 = (self.today + timedelta(days=15)).strftime("%Y-%m-%d")
        status, days = ExpiryService.get_expiry_status(exp_day_15)
        self.assertEqual(status, 'WARNING')
        self.assertEqual(days, 15)

        # Upcoming: 16 to 30 days
        exp_day_16 = (self.today + timedelta(days=16)).strftime("%Y-%m-%d")
        status, days = ExpiryService.get_expiry_status(exp_day_16)
        self.assertEqual(status, 'UPCOMING')
        self.assertEqual(days, 16)

        exp_day_30 = (self.today + timedelta(days=30)).strftime("%Y-%m-%d")
        status, days = ExpiryService.get_expiry_status(exp_day_30)
        self.assertEqual(status, 'UPCOMING')
        self.assertEqual(days, 30)

        # Normal: > 30 days
        exp_day_31 = (self.today + timedelta(days=31)).strftime("%Y-%m-%d")
        status, days = ExpiryService.get_expiry_status(exp_day_31)
        self.assertEqual(status, 'NORMAL')
        self.assertEqual(days, 31)

        exp_day_90 = (self.today + timedelta(days=90)).strftime("%Y-%m-%d")
        status, days = ExpiryService.get_expiry_status(exp_day_90)
        self.assertEqual(status, 'NORMAL')
        self.assertEqual(days, 90)

    def test_database_queries_for_expiry_tiers(self):
        """Test database query methods for expired, critical, warning, upcoming batches."""
        med_id = self.med_service.add_medicine(name="Test Med")

        offsets = {
            "B-EXPIRED": -5,
            "B-CRIT-0": 0,
            "B-CRIT-7": 7,
            "B-WARN-8": 8,
            "B-WARN-15": 15,
            "B-UPCOM-16": 16,
            "B-UPCOM-30": 30,
            "B-NORMAL-60": 60,
        }

        for b_no, offset in offsets.items():
            exp = (self.today + timedelta(days=offset)).strftime("%Y-%m-%d")
            mfg = (self.today + timedelta(days=offset - 100)).strftime("%Y-%m-%d")
            pur = (self.today + timedelta(days=offset - 50)).strftime("%Y-%m-%d")
            self.inv_service.add_batch(
                medicine_id=med_id,
                batch_number=b_no,
                mfg_date=mfg,
                exp_date=exp,
                purchase_date=pur,
                qty_received=50
            )

        # Verify query results
        expired = self.expiry_service.get_expired_batches()
        self.assertEqual(len(expired), 1)
        self.assertEqual(expired[0]['batch_number'], "B-EXPIRED")

        crit = self.expiry_service.get_critical_batches()
        crit_nos = {b['batch_number'] for b in crit}
        self.assertEqual(crit_nos, {"B-CRIT-0", "B-CRIT-7"})

        warn = self.expiry_service.get_warning_batches()
        warn_nos = {b['batch_number'] for b in warn}
        self.assertEqual(warn_nos, {"B-WARN-8", "B-WARN-15"})

        upcom = self.expiry_service.get_upcoming_batches()
        upcom_nos = {b['batch_number'] for b in upcom}
        self.assertEqual(upcom_nos, {"B-UPCOM-16", "B-UPCOM-30"})


if __name__ == '__main__':
    unittest.main()

