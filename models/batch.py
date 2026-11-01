"""
batch.py — Batch data model for MediVault.

Each medicine can have multiple batches, each with its own expiry date,
quantities, and pricing.
"""

from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from typing import Any, Dict, Optional


@dataclass
class Batch:
    """
    Represents a single batch of a medicine.

    Attributes:
        batch_id:          Database primary key (None for new records).
        medicine_id:       Foreign key → medicines table.
        batch_number:      Manufacturer's batch / lot number.
        manufacturing_date: Date the batch was manufactured (YYYY-MM-DD).
        expiry_date:       Date the batch expires (YYYY-MM-DD).
        purchase_date:     Date this batch was purchased (YYYY-MM-DD).
        quantity_received: Number of units originally received.
        current_quantity:  Number of units currently in stock.
        purchase_price:    Cost price per unit.
        selling_price:     Selling price per unit.
        supplier:          Supplier / vendor name.
        notes:             Optional remarks.
        created_at:        Record creation timestamp.
    """
    medicine_id: int = 0
    batch_number: str = ''
    manufacturing_date: str = ''
    expiry_date: str = ''
    purchase_date: str = ''
    quantity_received: int = 0
    current_quantity: int = 0
    purchase_price: float = 0.0
    selling_price: float = 0.0
    supplier: str = ''
    notes: str = ''
    batch_id: Optional[int] = None
    created_at: str = ''

    # ----- Computed properties -----

    @property
    def days_until_expiry(self) -> int:
        """
        Number of days from today until the batch expires.

        Negative values mean the batch is already expired.
        """
        try:
            exp = datetime.strptime(self.expiry_date, "%Y-%m-%d").date()
            return (exp - date.today()).days
        except (ValueError, TypeError):
            return 0

    @property
    def expiry_status(self) -> str:
        """
        Human-readable expiry status label.

        Returns one of:
            'EXPIRED'  — already past expiry
            'CRITICAL' — 7 days or fewer remaining
            'WARNING'  — 8–15 days remaining
            'UPCOMING' — 16–30 days remaining
            'NORMAL'   — more than 30 days remaining
        """
        days = self.days_until_expiry
        if days < 0:
            return 'EXPIRED'
        if days <= 7:
            return 'CRITICAL'
        if days <= 15:
            return 'WARNING'
        if days <= 30:
            return 'UPCOMING'
        return 'NORMAL'

    @property
    def is_expired(self) -> bool:
        """True if the batch has passed its expiry date."""
        return self.days_until_expiry < 0

    @property
    def stock_value(self) -> float:
        """Total monetary value of remaining stock at purchase price."""
        return self.current_quantity * self.purchase_price

    # ----- Serialisation helpers -----

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Batch to a plain dictionary (includes computed fields)."""
        d = asdict(self)
        # Add computed properties so they travel with the dict
        d['days_until_expiry'] = self.days_until_expiry
        d['expiry_status'] = self.expiry_status
        d['is_expired'] = self.is_expired
        d['stock_value'] = self.stock_value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Batch":
        """
        Create a Batch instance from a dictionary.

        Unknown keys (e.g. computed columns from SQL JOINs) are ignored.

        Args:
            data: Dictionary of field values.

        Returns:
            A new Batch instance.
        """
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)
