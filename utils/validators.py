"""
validators.py — Input validation helpers for MediVault.

Every public function returns a tuple (is_valid: bool, error_message: str).
If validation passes, error_message is an empty string.
"""

from datetime import datetime, date
import math
from typing import Tuple, Optional


# ---------------------------------------------------------------------------
# Medicine name
# ---------------------------------------------------------------------------
def validate_medicine_name(name: str) -> Tuple[bool, str]:
    """
    Check that a medicine name is not empty and at most 100 characters.

    Args:
        name: The medicine name string to validate.

    Returns:
        (True, '') on success, or (False, '<reason>') on failure.
    """
    if not name or not name.strip():
        return False, "Medicine name cannot be empty."
    if len(name.strip()) > 100:
        return False, "Medicine name must be 100 characters or fewer."
    return True, ""


# ---------------------------------------------------------------------------
# Quantity
# ---------------------------------------------------------------------------
def validate_quantity(qty) -> Tuple[bool, str]:
    """
    Ensure *qty* is a non-negative integer.

    Args:
        qty: Value to validate (int, str, or float accepted).

    Returns:
        (True, '') or (False, '<reason>').
    """
    try:
        if isinstance(qty, bool):
            raise ValueError
        qty_int = int(qty)
        if isinstance(qty, float) and not qty.is_integer():
            raise ValueError
        if isinstance(qty, str) and str(qty).strip() != str(qty_int):
            raise ValueError
    except (TypeError, ValueError):
        return False, "Quantity must be a whole number."
    if qty_int < 0:
        return False, "Quantity cannot be negative."
    return True, ""


# ---------------------------------------------------------------------------
# Price
# ---------------------------------------------------------------------------
def validate_price(price) -> Tuple[bool, str]:
    """
    Ensure *price* is a non-negative number (int or float).

    Args:
        price: Value to validate.

    Returns:
        (True, '') or (False, '<reason>').
    """
    try:
        price_float = float(price)
    except (TypeError, ValueError):
        return False, "Price must be a number."
    if not math.isfinite(price_float):
        return False, "Price must be finite."
    if price_float < 0:
        return False, "Price cannot be negative."
    return True, ""


# ---------------------------------------------------------------------------
# Single date
# ---------------------------------------------------------------------------
def validate_date(date_str: str) -> Tuple[bool, str]:
    """
    Check that *date_str* is a valid date in YYYY-MM-DD format.

    Args:
        date_str: Date string to validate.

    Returns:
        (True, '') or (False, '<reason>').
    """
    if not date_str or not date_str.strip():
        return False, "Date cannot be empty."
    try:
        datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD."
    return True, ""


# ---------------------------------------------------------------------------
# Date range (manufacturing vs. expiry)
# ---------------------------------------------------------------------------
def validate_date_range(mfg_date: str, exp_date: str) -> Tuple[bool, str]:
    """
    Ensure *exp_date* comes strictly after *mfg_date*.

    Args:
        mfg_date: Manufacturing date string (YYYY-MM-DD).
        exp_date: Expiry date string (YYYY-MM-DD).

    Returns:
        (True, '') or (False, '<reason>').
    """
    # Validate each date individually first
    ok, msg = validate_date(mfg_date)
    if not ok:
        return False, f"Manufacturing date error: {msg}"
    ok, msg = validate_date(exp_date)
    if not ok:
        return False, f"Expiry date error: {msg}"

    mfg = datetime.strptime(mfg_date.strip(), "%Y-%m-%d").date()
    exp = datetime.strptime(exp_date.strip(), "%Y-%m-%d").date()
    if exp <= mfg:
        return False, "Expiry date must be after manufacturing date."
    return True, ""


# ---------------------------------------------------------------------------
# Batch number
# ---------------------------------------------------------------------------
def validate_batch_number(batch_num: str) -> Tuple[bool, str]:
    """
    Ensure a batch number is not empty.

    Args:
        batch_num: Batch number string.

    Returns:
        (True, '') or (False, '<reason>').
    """
    if not batch_num or not batch_num.strip():
        return False, "Batch number cannot be empty."
    return True, ""


# ---------------------------------------------------------------------------
# Threshold
# ---------------------------------------------------------------------------
def validate_threshold(threshold) -> Tuple[bool, str]:
    """
    Ensure *threshold* is a non-negative integer.

    Args:
        threshold: Threshold value.

    Returns:
        (True, '') or (False, '<reason>').
    """
    try:
        val = int(threshold)
    except (TypeError, ValueError):
        return False, "Threshold must be a whole number."
    if val < 0:
        return False, "Threshold cannot be negative."
    return True, ""


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
def parse_date(date_str: str) -> Optional[date]:
    """
    Parse a YYYY-MM-DD string into a datetime.date object.

    Args:
        date_str: Date string to parse.

    Returns:
        A date object, or None if parsing fails.
    """
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


def format_date(date_obj: date) -> str:
    """
    Format a datetime.date object as a YYYY-MM-DD string.

    Args:
        date_obj: The date to format.

    Returns:
        Formatted date string, e.g. '2025-06-15'.
    """
    return date_obj.strftime("%Y-%m-%d")


def format_currency(amount: float, symbol: str = '₹') -> str:
    """
    Format a numeric amount as a currency string.

    Args:
        amount: The monetary amount.
        symbol: Currency symbol to prepend (defaults to Indian Rupee).

    Returns:
        Formatted string like '₹1,234.50'.
    """
    try:
        return f"{symbol}{amount:,.2f}"
    except (TypeError, ValueError):
        return f"{symbol}0.00"
