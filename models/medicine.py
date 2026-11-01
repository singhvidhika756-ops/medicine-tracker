"""
medicine.py — Medicine data model for MediVault.

Uses Python dataclasses so that creating and converting Medicine
objects is simple and transparent.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Constants — used by the UI for dropdown menus
# ---------------------------------------------------------------------------

CATEGORIES: List[str] = [
    'General',
    'Antibiotic',
    'Analgesic',
    'Antacid',
    'Antiseptic',
    'Antifungal',
    'Antiviral',
    'Cardiovascular',
    'Diabetes',
    'Dermatology',
    'ENT',
    'Eye Care',
    'Gastrointestinal',
    'Hormones',
    'Neurological',
    'Nutritional',
    'Respiratory',
    'Vitamins & Supplements',
    'Other',
]

UNIT_TYPES: List[str] = [
    'Tablet',
    'Capsule',
    'Syrup',
    'Injection',
    'Cream',
    'Ointment',
    'Drops',
    'Inhaler',
    'Powder',
    'Gel',
    'Spray',
    'Patch',
    'Sachet',
    'Other',
]


# ---------------------------------------------------------------------------
# Medicine dataclass
# ---------------------------------------------------------------------------

@dataclass
class Medicine:
    """
    Represents a single medicine in the inventory.

    Attributes:
        medicine_id:         Database primary key (None for new records).
        name:                Brand or trade name.
        generic_name:        Generic / INN name.
        category:            Therapeutic category.
        manufacturer:        Manufacturing company.
        description:         Optional free-text description.
        unit_type:           Dosage form (Tablet, Syrup, etc.).
        min_stock_threshold: Low-stock alert trigger quantity.
        created_at:          Record creation timestamp.
        updated_at:          Last-update timestamp.
    """
    name: str
    medicine_id: Optional[int] = None
    generic_name: str = ''
    category: str = 'General'
    manufacturer: str = ''
    description: str = ''
    unit_type: str = 'Tablet'
    min_stock_threshold: int = 10
    created_at: str = ''
    updated_at: str = ''

    # ----- Serialisation helpers -----

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Medicine to a plain dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Medicine":
        """
        Create a Medicine instance from a dictionary.

        Unknown keys are silently ignored so this works with
        SELECT * rows that may contain extra computed columns.

        Args:
            data: Dictionary of field values.

        Returns:
            A new Medicine instance.
        """
        # Only pass keys that match dataclass fields
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)
