"""
test_validators.py — Unit tests for input validation logic in MediVault.
"""

import unittest
from datetime import date, timedelta
from utils.validators import (
    validate_medicine_name, validate_quantity, validate_price,
    validate_date, validate_date_range, validate_batch_number
)


class TestValidators(unittest.TestCase):
    """Test suite for data validation functions."""

    def test_medicine_name_valid(self):
        valid, msg = validate_medicine_name("Paracetamol 500mg")
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_medicine_name_empty(self):
        valid, msg = validate_medicine_name("")
        self.assertFalse(valid)
        self.assertIn("empty", msg.lower())

        valid_ws, _ = validate_medicine_name("   ")
        self.assertFalse(valid_ws)

    def test_medicine_name_too_long(self):
        long_name = "A" * 105
        valid, msg = validate_medicine_name(long_name)
        self.assertFalse(valid)
        self.assertIn("100 characters", msg)

    def test_quantity_valid(self):
        self.assertTrue(validate_quantity(100)[0])
        self.assertTrue(validate_quantity("50")[0])
        self.assertTrue(validate_quantity(0)[0])

    def test_quantity_negative(self):
        valid, msg = validate_quantity(-5)
        self.assertFalse(valid)
        self.assertIn("negative", msg.lower())

        valid_str, msg_str = validate_quantity("-1")
        self.assertFalse(valid_str)

    def test_quantity_invalid_type(self):
        valid, msg = validate_quantity("abc")
        self.assertFalse(valid)
        self.assertIn("whole number", msg.lower())

        self.assertFalse(validate_quantity(1.9)[0])

    def test_price_valid(self):
        self.assertTrue(validate_price(12.50)[0])
        self.assertTrue(validate_price("99.99")[0])
        self.assertTrue(validate_price(0)[0])

    def test_price_negative(self):
        valid, msg = validate_price(-1.5)
        self.assertFalse(valid)
        self.assertIn("negative", msg.lower())

        self.assertFalse(validate_price(float('nan'))[0])
        self.assertFalse(validate_price(float('inf'))[0])

    def test_date_valid(self):
        self.assertTrue(validate_date("2026-11-01")[0])

    def test_date_invalid_format(self):
        self.assertFalse(validate_date("01-11-2026")[0])
        self.assertFalse(validate_date("2026/11/01")[0])
        self.assertFalse(validate_date("invalid-date")[0])
        self.assertFalse(validate_date("")[0])

    def test_date_range(self):
        mfg = "2026-01-01"
        exp_valid = "2026-12-31"
        exp_invalid = "2025-12-31"

        self.assertTrue(validate_date_range(mfg, exp_valid)[0])
        valid, msg = validate_date_range(mfg, exp_invalid)
        self.assertFalse(valid)
        self.assertIn("after", msg.lower())

        # Equal dates should also fail (expiry must be later than mfg)
        self.assertFalse(validate_date_range(mfg, mfg)[0])

    def test_batch_number(self):
        self.assertTrue(validate_batch_number("BATCH-001")[0])
        self.assertFalse(validate_batch_number("")[0])
        self.assertFalse(validate_batch_number("   ")[0])


if __name__ == '__main__':
    unittest.main()

