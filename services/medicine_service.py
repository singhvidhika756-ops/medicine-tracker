"""
medicine_service.py — Business logic for managing medicines in MediVault.

All database access for the medicines table goes through this service.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from database.connection import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger('medivault.medicine_service')


class MedicineService:
    """
    Provides CRUD operations and queries for the medicines table.

    Every public method validates its inputs before touching the database
    and returns clean Python data structures (dicts / lists).
    """

    def __init__(self, db: DatabaseManager) -> None:
        """
        Args:
            db: An active DatabaseManager instance.
        """
        self.db = db

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------
    def add_medicine(
        self,
        name: str,
        generic_name: str = '',
        category: str = 'General',
        manufacturer: str = '',
        description: str = '',
        unit_type: str = 'Tablet',
        min_stock_threshold: int = 10,
    ) -> int:
        """
        Insert a new medicine into the database.

        Args:
            name:                Brand / trade name (required, non-empty).
            generic_name:        Generic / INN name.
            category:            Therapeutic category.
            manufacturer:        Manufacturing company.
            description:         Optional free-text note.
            unit_type:           Dosage form.
            min_stock_threshold: Low-stock alert level (>= 0).

        Returns:
            The auto-generated medicine_id of the new row.

        Raises:
            ValueError: If name is empty or threshold is negative.
        """
        # --- Validation ---
        if not name or not name.strip():
            raise ValueError("Medicine name cannot be empty.")
        if min_stock_threshold < 0:
            raise ValueError("Minimum stock threshold cannot be negative.")

        cursor = self.db.execute(
            """INSERT INTO medicines
               (name, generic_name, category, manufacturer,
                description, unit_type, min_stock_threshold)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name.strip(), generic_name.strip(), category.strip(),
             manufacturer.strip(), description.strip(), unit_type.strip(),
             min_stock_threshold),
        )
        medicine_id = cursor.lastrowid
        logger.info("Added medicine id=%d name='%s'", medicine_id, name.strip())
        return medicine_id

    # ------------------------------------------------------------------
    # READ — all medicines
    # ------------------------------------------------------------------
    def get_all_medicines(self) -> List[Dict[str, Any]]:
        """
        Retrieve every medicine with aggregated stock information.

        Each returned dict contains all medicine columns plus:
            total_stock  — SUM of current_quantity across batches (0 if none)
            batch_count  — number of batches

        Returns:
            List of medicine dicts, ordered by name.
        """
        rows = self.db.fetchall("""
            SELECT m.*,
                   COALESCE(SUM(b.current_quantity), 0) AS total_stock,
                   COUNT(b.batch_id)                     AS batch_count
            FROM   medicines m
            LEFT JOIN batches b ON b.medicine_id = m.medicine_id
            GROUP BY m.medicine_id
            ORDER BY m.name
        """)
        return rows

    def get_all_medicines_with_stock(self) -> List[Dict[str, Any]]:
        """Alias for get_all_medicines which already computes total stock."""
        return self.get_all_medicines()

    # ------------------------------------------------------------------
    # READ — single medicine
    # ------------------------------------------------------------------
    def get_medicine(self, medicine_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single medicine by its ID.

        Args:
            medicine_id: Primary key.

        Returns:
            Dict with medicine fields + total_stock + batch_count,
            or None if not found.
        """
        row = self.db.fetchone("""
            SELECT m.*,
                   COALESCE(SUM(b.current_quantity), 0) AS total_stock,
                   COUNT(b.batch_id)                     AS batch_count
            FROM   medicines m
            LEFT JOIN batches b ON b.medicine_id = m.medicine_id
            WHERE  m.medicine_id = ?
            GROUP BY m.medicine_id
        """, (medicine_id,))
        return row

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    def update_medicine(self, medicine_id: int, **kwargs) -> bool:
        """
        Update one or more fields of an existing medicine.

        Only the keys present in *kwargs* are modified; other columns
        remain unchanged.  The updated_at timestamp is refreshed
        automatically.

        Args:
            medicine_id: Primary key of the medicine to update.
            **kwargs:    Column-name=value pairs to change.

        Returns:
            True if a row was actually updated, False otherwise.
        """
        if not kwargs:
            return False

        # Build SET clause dynamically
        allowed = {
            'name', 'generic_name', 'category', 'manufacturer',
            'description', 'unit_type', 'min_stock_threshold',
        }
        set_parts = []
        values = []
        for key, value in kwargs.items():
            if key in allowed:
                set_parts.append(f"{key} = ?")
                values.append(value)

        if not set_parts:
            return False

        # Always refresh updated_at
        set_parts.append("updated_at = datetime('now', 'localtime')")
        values.append(medicine_id)

        query = f"UPDATE medicines SET {', '.join(set_parts)} WHERE medicine_id = ?"
        cursor = self.db.execute(query, tuple(values))
        updated = cursor.rowcount > 0
        if updated:
            logger.info("Updated medicine id=%d fields=%s", medicine_id, list(kwargs.keys()))
        return updated

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    def delete_medicine(self, medicine_id: int) -> bool:
        """
        Delete a medicine by ID.  CASCADE removes related batches & transactions.

        Args:
            medicine_id: Primary key.

        Returns:
            True if a row was deleted, False otherwise.
        """
        cursor = self.db.execute(
            "DELETE FROM medicines WHERE medicine_id = ?",
            (medicine_id,),
        )
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info("Deleted medicine id=%d", medicine_id)
        return deleted

    # ------------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------------
    def search_medicines(self, query: str = '', category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search medicines by name or generic name, and optionally filter by category.

        Args:
            query:    Search string (case-insensitive LIKE).
            category: Optional therapeutic category to filter by.

        Returns:
            List of matching medicine dicts with total_stock & batch_count.
        """
        base = """
            SELECT m.*,
                   COALESCE(SUM(b.current_quantity), 0) AS total_stock,
                   COUNT(b.batch_id)                     AS batch_count
            FROM   medicines m
            LEFT JOIN batches b ON b.medicine_id = m.medicine_id
        """
        conditions = []
        params = []

        if query and query.strip():
            pattern = f"%{query.strip()}%"
            conditions.append("(m.name LIKE ? OR m.generic_name LIKE ?)")
            params.extend([pattern, pattern])

        if category and category.strip() and category != 'All':
            conditions.append("m.category = ?")
            params.append(category.strip())

        if conditions:
            base += " WHERE " + " AND ".join(conditions)

        base += " GROUP BY m.medicine_id ORDER BY m.name"

        rows = self.db.fetchall(base, tuple(params))
        return rows

    # ------------------------------------------------------------------
    # Filter by category
    # ------------------------------------------------------------------
    def get_medicines_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all medicines in a specific category.

        Args:
            category: Category string to match exactly.

        Returns:
            List of medicine dicts with total_stock & batch_count.
        """
        rows = self.db.fetchall("""
            SELECT m.*,
                   COALESCE(SUM(b.current_quantity), 0) AS total_stock,
                   COUNT(b.batch_id)                     AS batch_count
            FROM   medicines m
            LEFT JOIN batches b ON b.medicine_id = m.medicine_id
            WHERE  m.category = ?
            GROUP BY m.medicine_id
            ORDER BY m.name
        """, (category,))
        return rows

    # ------------------------------------------------------------------
    # Distinct categories
    # ------------------------------------------------------------------
    def get_categories(self) -> List[str]:
        """
        Return a sorted list of distinct categories currently in use.

        Returns:
            List of category strings.
        """
        rows = self.db.fetchall(
            "SELECT DISTINCT category FROM medicines ORDER BY category"
        )
        return [r['category'] for r in rows]

    # ------------------------------------------------------------------
    # Low-stock medicines
    # ------------------------------------------------------------------
    def get_low_stock_medicines(self) -> List[Dict[str, Any]]:
        """
        Find medicines whose total stock is below their threshold.

        Returns:
            List of medicine dicts with total_stock & batch_count.
        """
        rows = self.db.fetchall("""
            SELECT m.*,
                   COALESCE(SUM(b.current_quantity), 0) AS total_stock,
                   COUNT(b.batch_id)                     AS batch_count
            FROM   medicines m
            LEFT JOIN batches b ON b.medicine_id = m.medicine_id
            GROUP BY m.medicine_id
            HAVING total_stock < m.min_stock_threshold
            ORDER BY total_stock ASC
        """)
        return rows

    # ------------------------------------------------------------------
    # Duplicate check
    # ------------------------------------------------------------------
    def medicine_exists(self, name: str) -> bool:
        """
        Check if a medicine with the given name already exists.

        The comparison is case-insensitive.

        Args:
            name: Medicine name to check.

        Returns:
            True if a medicine with this name is already in the database.
        """
        row = self.db.fetchone(
            "SELECT 1 FROM medicines WHERE LOWER(name) = LOWER(?)",
            (name.strip(),),
        )
        return row is not None
