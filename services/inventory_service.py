"""
inventory_service.py — Business logic for batches and stock in MediVault.

Handles batch CRUD, stock add/remove/correct, FEFO (First-Expiry-First-Out)
dispensing, and stock transaction history.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from database.connection import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger('medivault.inventory_service')


def _compute_expiry_fields(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add 'days_until_expiry' and 'expiry_status' to a batch dict.

    This is a helper called after fetching rows from the database
    so the computation happens in Python (not SQL).

    Args:
        row: A dict that must contain an 'expiry_date' key (YYYY-MM-DD).

    Returns:
        The same dict with two extra keys added.
    """
    try:
        exp = datetime.strptime(row['expiry_date'], "%Y-%m-%d").date()
        days = (exp - date.today()).days
    except (ValueError, TypeError, KeyError):
        days = 0

    row['days_until_expiry'] = days

    if days < 0:
        row['expiry_status'] = 'EXPIRED'
    elif days <= 7:
        row['expiry_status'] = 'CRITICAL'
    elif days <= 15:
        row['expiry_status'] = 'WARNING'
    elif days <= 30:
        row['expiry_status'] = 'UPCOMING'
    else:
        row['expiry_status'] = 'NORMAL'

    return row


class InventoryService:
    """
    Manages batches and stock transactions.

    Every stock change creates an auditable StockTransaction row.
    """

    def __init__(self, db: DatabaseManager) -> None:
        """
        Args:
            db: An active DatabaseManager instance.
        """
        self.db = db

    # ------------------------------------------------------------------
    # Batch CRUD
    # ------------------------------------------------------------------
    def add_batch(
        self,
        medicine_id: int,
        batch_number: str,
        mfg_date: str,
        exp_date: str,
        purchase_date: str,
        qty_received: int,
        purchase_price: float = 0.0,
        selling_price: float = 0.0,
        supplier: str = '',
        notes: str = '',
    ) -> int:
        """
        Insert a new batch and record an INITIAL stock transaction.

        Args:
            medicine_id:    FK to medicines table.
            batch_number:   Manufacturer's batch/lot number (non-empty).
            mfg_date:       Manufacturing date (YYYY-MM-DD).
            exp_date:       Expiry date (YYYY-MM-DD, must be after mfg).
            purchase_date:  Purchase date (YYYY-MM-DD).
            qty_received:   Number of units received (> 0).
            purchase_price: Cost per unit (>= 0).
            selling_price:  Sell price per unit (>= 0).
            supplier:       Supplier / vendor name.
            notes:          Optional remarks.

        Returns:
            The auto-generated batch_id.

        Raises:
            ValueError: On any validation failure.
        """
        # --- Validation ---
        batch_number = batch_number.strip()
        if not batch_number:
            raise ValueError("Batch number cannot be empty.")
        mfg = datetime.strptime(mfg_date, "%Y-%m-%d").date()
        exp = datetime.strptime(exp_date, "%Y-%m-%d").date()
        datetime.strptime(purchase_date, "%Y-%m-%d")
        if exp <= mfg:
            raise ValueError("Expiry date must be after manufacturing date.")
        if qty_received <= 0:
            raise ValueError("Quantity received must be greater than zero.")
        if purchase_price < 0:
            raise ValueError("Purchase price cannot be negative.")
        if selling_price < 0:
            raise ValueError("Selling price cannot be negative.")

        with self.db.transaction() as conn:
            insert_query = (
                """INSERT INTO batches
                   (medicine_id, batch_number, manufacturing_date, expiry_date,
                    purchase_date, quantity_received, current_quantity,
                    purchase_price, selling_price, supplier, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            )
            if self.db._postgres:
                insert_query += " RETURNING batch_id"
            cursor = conn.execute(
                insert_query,
                (medicine_id, batch_number, mfg_date, exp_date,
                 purchase_date, qty_received, qty_received,
                 purchase_price, selling_price, supplier.strip(), notes.strip()),
            )
            batch_id = cursor.fetchone()['batch_id'] if self.db._postgres else cursor.lastrowid

            conn.execute(
                """INSERT INTO stock_transactions
                   (batch_id, medicine_id, transaction_type,
                    quantity_changed, previous_quantity, new_quantity, reason)
                   VALUES (?, ?, 'INITIAL', ?, 0, ?, 'Initial stock entry')""",
                (batch_id, medicine_id, qty_received, qty_received),
            )

        logger.info(
            "Added batch id=%d medicine_id=%d batch_number='%s' qty=%d",
            batch_id, medicine_id, batch_number, qty_received,
        )
        return batch_id

    def get_batches(self, medicine_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve batches, optionally filtered by medicine.

        Each returned dict includes the medicine name and computed
        expiry fields (days_until_expiry, expiry_status).

        Args:
            medicine_id: If given, return only batches for this medicine.

        Returns:
            List of batch dicts.
        """
        if medicine_id is not None:
            rows = self.db.fetchall("""
                SELECT b.*, m.name AS medicine_name
                FROM   batches b
                JOIN   medicines m ON m.medicine_id = b.medicine_id
                WHERE  b.medicine_id = ?
                ORDER BY b.expiry_date ASC
            """, (medicine_id,))
        else:
            rows = self.db.fetchall("""
                SELECT b.*, m.name AS medicine_name
                FROM   batches b
                JOIN   medicines m ON m.medicine_id = b.medicine_id
                ORDER BY b.expiry_date ASC
            """)

        return [_compute_expiry_fields(r) for r in rows]

    def get_batch(self, batch_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single batch by ID.

        Args:
            batch_id: Primary key.

        Returns:
            Batch dict with computed expiry fields, or None.
        """
        row = self.db.fetchone("""
            SELECT b.*, m.name AS medicine_name
            FROM   batches b
            JOIN   medicines m ON m.medicine_id = b.medicine_id
            WHERE  b.batch_id = ?
        """, (batch_id,))
        if row is None:
            return None
        return _compute_expiry_fields(row)

    def get_all_batches(self) -> List[Dict[str, Any]]:
        """
        Retrieve all batches across every medicine.

        Convenience alias for get_batches() with no filter.

        Returns:
            List of batch dicts with medicine_name and expiry fields.
        """
        return self.get_batches()

    def update_batch(self, batch_id: int, **kwargs) -> bool:
        """
        Update one or more fields of an existing batch.

        Args:
            batch_id: Primary key.
            **kwargs: Column-name=value pairs to update.

        Returns:
            True if a row was updated, False otherwise.
        """
        if not kwargs:
            return False

        allowed = {
            'batch_number', 'manufacturing_date', 'expiry_date',
            'purchase_date',
            'purchase_price', 'selling_price', 'supplier', 'notes',
        }
        set_parts = []
        values = []
        for key, value in kwargs.items():
            if key in allowed:
                set_parts.append(f"{key} = ?")
                values.append(value)

        if not set_parts:
            return False

        values.append(batch_id)
        query = f"UPDATE batches SET {', '.join(set_parts)} WHERE batch_id = ?"
        cursor = self.db.execute(query, tuple(values))
        updated = cursor.rowcount > 0
        if updated:
            logger.info("Updated batch id=%d fields=%s", batch_id, list(kwargs.keys()))
        return updated

    def delete_batch(self, batch_id: int) -> bool:
        """
        Delete a batch by ID.  CASCADE removes related transactions.

        Args:
            batch_id: Primary key.

        Returns:
            True if a row was deleted, False otherwise.
        """
        cursor = self.db.execute(
            "DELETE FROM batches WHERE batch_id = ?",
            (batch_id,),
        )
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info("Deleted batch id=%d", batch_id)
        return deleted

    # ------------------------------------------------------------------
    # Stock operations
    # ------------------------------------------------------------------
    def add_stock(self, batch_id: int, quantity: int,
                  reason: str = 'Stock added') -> bool:
        """
        Increase the stock of a batch and record an ADDED transaction.

        Args:
            batch_id: Batch to add stock to.
            quantity: Number of units to add (> 0).
            reason:   Free-text reason.

        Returns:
            True on success.

        Raises:
            ValueError: If quantity is not positive or batch not found.
        """
        if quantity <= 0:
            raise ValueError("Quantity to add must be greater than zero.")

        batch = self.get_batch(batch_id)
        if batch is None:
            raise ValueError(f"Batch {batch_id} not found.")

        prev_qty = batch['current_quantity']
        new_qty = prev_qty + quantity

        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE batches SET current_quantity = ? WHERE batch_id = ?",
                (new_qty, batch_id),
            )
            conn.execute(
                """INSERT INTO stock_transactions
                   (batch_id, medicine_id, transaction_type,
                    quantity_changed, previous_quantity, new_quantity, reason)
                   VALUES (?, ?, 'ADDED', ?, ?, ?, ?)""",
                (batch_id, batch['medicine_id'], quantity, prev_qty, new_qty, reason),
            )
        logger.info("Added %d units to batch %d (now %d)", quantity, batch_id, new_qty)
        return True

    def reduce_stock(self, batch_id: int, quantity: int,
                     reason: str = 'Stock removed') -> bool:
        """
        Decrease the stock of a batch and record a REMOVED transaction.

        Args:
            batch_id: Batch to remove stock from.
            quantity: Number of units to remove (> 0).
            reason:   Free-text reason.

        Returns:
            True on success.

        Raises:
            ValueError: If quantity exceeds available stock.
        """
        if quantity <= 0:
            raise ValueError("Quantity to remove must be greater than zero.")

        batch = self.get_batch(batch_id)
        if batch is None:
            raise ValueError(f"Batch {batch_id} not found.")

        prev_qty = batch['current_quantity']
        if quantity > prev_qty:
            raise ValueError(
                f"Cannot remove {quantity} units — only {prev_qty} available."
            )

        new_qty = prev_qty - quantity
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE batches SET current_quantity = ? WHERE batch_id = ?",
                (new_qty, batch_id),
            )
            conn.execute(
                """INSERT INTO stock_transactions
                   (batch_id, medicine_id, transaction_type,
                    quantity_changed, previous_quantity, new_quantity, reason)
                   VALUES (?, ?, 'REMOVED', ?, ?, ?, ?)""",
                (batch_id, batch['medicine_id'], quantity, prev_qty, new_qty, reason),
            )
        logger.info("Removed %d units from batch %d (now %d)", quantity, batch_id, new_qty)
        return True

    def correct_stock(self, batch_id: int, new_quantity: int,
                      reason: str = 'Stock correction') -> bool:
        """
        Set a batch's stock to an exact quantity (manual adjustment).

        Args:
            batch_id:     Batch to correct.
            new_quantity:  Desired stock level (>= 0).
            reason:       Free-text reason.

        Returns:
            True on success.

        Raises:
            ValueError: If new_quantity is negative or batch not found.
        """
        if new_quantity < 0:
            raise ValueError("New quantity cannot be negative.")

        batch = self.get_batch(batch_id)
        if batch is None:
            raise ValueError(f"Batch {batch_id} not found.")

        prev_qty = batch['current_quantity']
        qty_changed = abs(new_quantity - prev_qty)

        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE batches SET current_quantity = ? WHERE batch_id = ?",
                (new_quantity, batch_id),
            )
            conn.execute(
                """INSERT INTO stock_transactions
                   (batch_id, medicine_id, transaction_type,
                    quantity_changed, previous_quantity, new_quantity, reason)
                   VALUES (?, ?, 'ADJUSTED', ?, ?, ?, ?)""",
                (batch_id, batch['medicine_id'], qty_changed, prev_qty, new_quantity, reason),
            )
        logger.info("Corrected batch %d: %d → %d", batch_id, prev_qty, new_quantity)
        return True

    # ------------------------------------------------------------------
    # FEFO — First Expiry, First Out
    # ------------------------------------------------------------------
    def reduce_stock_fefo(
        self,
        medicine_id: int,
        quantity: int,
        reason: str = 'FEFO removal',
    ) -> List[Tuple[int, int]]:
        """
        Remove *quantity* units using First-Expiry-First-Out logic.

        Non-expired batches are consumed starting from the one expiring
        soonest.

        Args:
            medicine_id: Medicine to deduct from.
            quantity:    Total units to remove (> 0).
            reason:      Free-text reason.

        Returns:
            List of (batch_id, qty_reduced) tuples showing which
            batches were affected and by how much.

        Raises:
            ValueError: If total available stock is insufficient.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        today_str = date.today().strftime("%Y-%m-%d")

        reductions: List[Tuple[int, int]] = []
        with self.db.transaction() as conn:
            # Keep the availability check and deductions in one transaction.
            batches = [dict(row) for row in conn.execute("""
                SELECT batch_id, current_quantity
                FROM   batches
                WHERE  medicine_id = ?
                  AND  expiry_date >= ?
                  AND  current_quantity > 0
                ORDER BY expiry_date ASC
            """, (medicine_id, today_str)).fetchall()]

            total_available = sum(b['current_quantity'] for b in batches)
            if total_available < quantity:
                raise ValueError(
                    f"Insufficient stock: need {quantity}, only {total_available} available."
                )

            remaining = quantity
            for b in batches:
                if remaining <= 0:
                    break

                take = min(remaining, b['current_quantity'])
                prev_qty = b['current_quantity']
                new_qty = prev_qty - take

                conn.execute(
                    "UPDATE batches SET current_quantity = ? WHERE batch_id = ?",
                    (new_qty, b['batch_id']),
                )
                conn.execute(
                    """INSERT INTO stock_transactions
                       (batch_id, medicine_id, transaction_type,
                        quantity_changed, previous_quantity, new_quantity, reason)
                       VALUES (?, ?, 'REMOVED', ?, ?, ?, ?)""",
                    (b['batch_id'], medicine_id, take, prev_qty, new_qty, reason),
                )
                reductions.append((b['batch_id'], take))
                remaining -= take

        logger.info(
            "FEFO removal: medicine_id=%d qty=%d batches=%s",
            medicine_id, quantity, reductions,
        )
        return reductions

    # ------------------------------------------------------------------
    # Transaction history
    # ------------------------------------------------------------------
    def get_stock_history(
        self,
        batch_id: Optional[int] = None,
        medicine_id: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve stock transaction history with medicine and batch details.

        Args:
            batch_id:    Filter to a specific batch (optional).
            medicine_id: Filter to a specific medicine (optional).
            limit:       Maximum rows to return.

        Returns:
            List of transaction dicts, newest first.
        """
        base = """
            SELECT st.*,
                   m.name          AS medicine_name,
                   b.batch_number  AS batch_number
            FROM   stock_transactions st
            JOIN   medicines m ON m.medicine_id = st.medicine_id
            JOIN   batches   b ON b.batch_id    = st.batch_id
        """
        conditions = []
        params: list = []

        if batch_id is not None:
            conditions.append("st.batch_id = ?")
            params.append(batch_id)
        if medicine_id is not None:
            conditions.append("st.medicine_id = ?")
            params.append(medicine_id)

        if conditions:
            base += " WHERE " + " AND ".join(conditions)

        base += " ORDER BY st.transaction_date DESC, st.transaction_id DESC LIMIT ?"
        params.append(limit)

        return self.db.fetchall(base, tuple(params))

    def get_transactions(
        self,
        batch_id: Optional[int] = None,
        medicine_id: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Alias for get_stock_history."""
        return self.get_stock_history(batch_id=batch_id, medicine_id=medicine_id, limit=limit)

    def get_transactions_by_type(
        self,
        transaction_type: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve stock transactions filtered by type (INITIAL, ADDED, REMOVED, ADJUSTED).
        """
        query = """
            SELECT st.*,
                   m.name          AS medicine_name,
                   b.batch_number  AS batch_number
            FROM   stock_transactions st
            JOIN   medicines m ON m.medicine_id = st.medicine_id
            JOIN   batches   b ON b.batch_id    = st.batch_id
            WHERE  st.transaction_type = ?
            ORDER BY st.transaction_date DESC, st.transaction_id DESC
            LIMIT ?
        """
        return self.db.fetchall(query, (transaction_type, limit))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def get_total_stock(self, medicine_id: int) -> int:
        """
        Get the sum of current_quantity across all batches for a medicine.

        Args:
            medicine_id: Medicine primary key.

        Returns:
            Total units in stock (0 if no batches exist).
        """
        row = self.db.fetchone(
            "SELECT COALESCE(SUM(current_quantity), 0) AS total "
            "FROM batches WHERE medicine_id = ?",
            (medicine_id,),
        )
        return row['total'] if row else 0

    def batch_number_exists(self, medicine_id: int, batch_number: str) -> bool:
        """
        Check whether a batch number already exists for a medicine.

        Args:
            medicine_id:  Medicine FK.
            batch_number: Batch/lot number to check.

        Returns:
            True if it already exists.
        """
        row = self.db.fetchone(
            "SELECT 1 FROM batches WHERE medicine_id = ? AND batch_number = ?",
            (medicine_id, batch_number.strip()),
        )
        return row is not None
