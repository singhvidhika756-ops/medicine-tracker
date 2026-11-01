"""
transaction.py — Stock-transaction data model for MediVault.

Every stock change (add, remove, adjust) is recorded as a transaction
so that a full audit trail is available.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


@dataclass
class StockTransaction:
    """
    Represents a single stock-change event.

    Attributes:
        transaction_id:   Database primary key (None for new records).
        batch_id:         Foreign key → batches table.
        medicine_id:      Foreign key → medicines table.
        transaction_type: One of 'ADDED', 'REMOVED', 'ADJUSTED', 'INITIAL'.
        quantity_changed:  Number of units involved (always positive).
        previous_quantity: Stock level before this transaction.
        new_quantity:      Stock level after this transaction.
        reason:           Free-text reason / note.
        transaction_date: Timestamp of the transaction.
    """
    batch_id: int = 0
    medicine_id: int = 0
    transaction_type: str = 'ADDED'
    quantity_changed: int = 0
    previous_quantity: int = 0
    new_quantity: int = 0
    reason: str = ''
    transaction_id: Optional[int] = None
    transaction_date: str = ''

    # ----- Serialisation helpers -----

    def to_dict(self) -> Dict[str, Any]:
        """Convert the StockTransaction to a plain dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StockTransaction":
        """
        Create a StockTransaction instance from a dictionary.

        Unknown keys are silently ignored.

        Args:
            data: Dictionary of field values.

        Returns:
            A new StockTransaction instance.
        """
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)
