"""
report_service.py — Reporting and CSV export for MediVault.

Generates dashboard statistics, inventory reports, expiry reports,
low-stock reports, stock-movement reports, and valuation reports.
"""

import csv
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from database.connection import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger('medivault.report_service')


class ReportService:
    """
    Produces aggregated data for the dashboard and printable reports.
    """

    def __init__(self, db: DatabaseManager) -> None:
        """
        Args:
            db: An active DatabaseManager instance.
        """
        self.db = db

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Compute all numbers shown on the MediVault dashboard.

        Returns:
            Dict with keys:
                total_medicines, total_batches, total_units, total_value,
                expired_batches, expiring_7_days, expiring_30_days,
                low_stock_medicines, recent_transactions,
                category_distribution.
        """
        today_str = date.today().strftime("%Y-%m-%d")
        d7_str = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
        d30_str = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")

        # --- Scalar counts ------------------------------------------------
        total_medicines = self._scalar(
            "SELECT COUNT(*) AS c FROM medicines"
        )
        total_batches = self._scalar(
            "SELECT COUNT(*) AS c FROM batches"
        )
        total_units = self._scalar(
            "SELECT COALESCE(SUM(current_quantity), 0) AS c FROM batches"
        )
        total_value = self._scalar(
            "SELECT COALESCE(SUM(current_quantity * purchase_price), 0) AS c FROM batches"
        )
        expired_batches = self._scalar(
            "SELECT COUNT(*) AS c FROM batches WHERE expiry_date < ?",
            (today_str,),
        )
        expiring_7_days = self._scalar(
            "SELECT COUNT(*) AS c FROM batches "
            "WHERE expiry_date >= ? AND expiry_date <= ?",
            (today_str, d7_str),
        )
        expiring_30_days = self._scalar(
            "SELECT COUNT(*) AS c FROM batches "
            "WHERE expiry_date >= ? AND expiry_date <= ?",
            (today_str, d30_str),
        )

        # Low-stock medicines
        low_stock_medicines = self._scalar("""
            SELECT COUNT(*) AS c FROM (
                SELECT m.medicine_id
                FROM   medicines m
                LEFT JOIN batches b ON b.medicine_id = m.medicine_id
                GROUP BY m.medicine_id
                HAVING COALESCE(SUM(b.current_quantity), 0) < m.min_stock_threshold
            )
        """)

        # --- Recent transactions ------------------------------------------
        recent_transactions = self.db.fetchall("""
            SELECT st.*,
                   m.name          AS medicine_name,
                   b.batch_number  AS batch_number
            FROM   stock_transactions st
            JOIN   medicines m ON m.medicine_id = st.medicine_id
            JOIN   batches   b ON b.batch_id    = st.batch_id
            ORDER BY st.transaction_date DESC
            LIMIT 10
        """)

        # --- Category distribution ----------------------------------------
        cat_rows = self.db.fetchall(
            "SELECT category, COUNT(*) AS count FROM medicines GROUP BY category ORDER BY category"
        )
        category_distribution = {r['category']: r['count'] for r in cat_rows}

        return {
            'total_medicines':     total_medicines,
            'total_batches':       total_batches,
            'total_units':         total_units,
            'total_value':         total_value,
            'expired_batches':     expired_batches,
            'expiring_7_days':     expiring_7_days,
            'expiring_30_days':    expiring_30_days,
            'low_stock_medicines': low_stock_medicines,
            'recent_transactions': recent_transactions,
            'category_distribution': category_distribution,
        }

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------
    def generate_inventory_report(self) -> List[Dict[str, Any]]:
        """
        Full inventory: every medicine with every batch's details.

        Returns:
            List of dicts (one per batch, includes medicine info).
        """
        rows = self.db.fetchall("""
            SELECT m.name            AS medicine_name,
                   m.generic_name,
                   m.category,
                   m.manufacturer,
                   m.unit_type,
                   b.batch_number,
                   b.manufacturing_date,
                   b.expiry_date,
                   b.purchase_date,
                   b.quantity_received,
                   b.current_quantity,
                   b.purchase_price,
                   b.selling_price,
                   b.supplier
            FROM   batches b
            JOIN   medicines m ON m.medicine_id = b.medicine_id
            ORDER BY m.name, b.expiry_date
        """)
        # Add computed expiry fields
        for r in rows:
            r['days_until_expiry'] = self._days_until(r['expiry_date'])
            r['expiry_status'] = self._status_label(r['expiry_date'])
        return rows

    def generate_expiry_report(self) -> List[Dict[str, Any]]:
        """
        List expired + near-expiry (30 days) batches.

        Returns:
            List of batch dicts.
        """
        d30_str = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
        rows = self.db.fetchall("""
            SELECT m.name            AS medicine_name,
                   m.category,
                   b.batch_number,
                   b.expiry_date,
                   b.current_quantity,
                   b.supplier
            FROM   batches b
            JOIN   medicines m ON m.medicine_id = b.medicine_id
            WHERE  b.expiry_date <= ?
            ORDER BY b.expiry_date ASC
        """, (d30_str,))
        for r in rows:
            r['days_until_expiry'] = self._days_until(r['expiry_date'])
            r['expiry_status'] = self._status_label(r['expiry_date'])
        return rows

    def generate_low_stock_report(self) -> List[Dict[str, Any]]:
        """
        Medicines whose total stock is below their threshold.

        Returns:
            List of medicine dicts with total_stock, min_stock_threshold.
        """
        rows = self.db.fetchall("""
            SELECT m.medicine_id,
                   m.name,
                   m.category,
                   m.unit_type,
                   m.min_stock_threshold,
                   COALESCE(SUM(b.current_quantity), 0) AS total_stock
            FROM   medicines m
            LEFT JOIN batches b ON b.medicine_id = m.medicine_id
            GROUP BY m.medicine_id
            HAVING total_stock < m.min_stock_threshold
            ORDER BY total_stock ASC
        """)
        return rows

    def generate_stock_movement_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Stock transactions within a date range.

        Args:
            start_date: Inclusive start (YYYY-MM-DD).  Default: 30 days ago.
            end_date:   Inclusive end (YYYY-MM-DD).    Default: today.

        Returns:
            List of transaction dicts.
        """
        if start_date is None:
            start_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = date.today().strftime("%Y-%m-%d")

        rows = self.db.fetchall("""
            SELECT st.*,
                   m.name          AS medicine_name,
                   b.batch_number  AS batch_number
            FROM   stock_transactions st
            JOIN   medicines m ON m.medicine_id = st.medicine_id
            JOIN   batches   b ON b.batch_id    = st.batch_id
            WHERE  DATE(st.transaction_date) BETWEEN ? AND ?
            ORDER BY st.transaction_date DESC
        """, (start_date, end_date))
        return rows

    def generate_valuation_report(self) -> List[Dict[str, Any]]:
        """
        Per-batch stock valuation: quantity × purchase price.

        Returns:
            List of dicts with medicine, batch, qty, price, value.
        """
        rows = self.db.fetchall("""
            SELECT m.name            AS medicine_name,
                   m.category,
                   b.batch_number,
                   b.current_quantity AS quantity,
                   b.purchase_price  AS unit_price,
                   (b.current_quantity * b.purchase_price) AS value
            FROM   batches b
            JOIN   medicines m ON m.medicine_id = b.medicine_id
            ORDER BY value DESC
        """)
        return rows

    # ------------------------------------------------------------------
    # CSV export
    # ------------------------------------------------------------------
    @staticmethod
    def export_to_csv(data: List[Dict[str, Any]],
                      headers: List[str],
                      filepath: str) -> bool:
        """
        Write a list of dicts to a CSV file.

        Uses utf-8-sig encoding so that Excel opens the file correctly
        (with a BOM).

        Args:
            data:     List of dictionaries to write.
            headers:  Column headers (must match dict keys).
            filepath: Destination file path.

        Returns:
            True on success, False on failure.
        """
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(data)
            logger.info("Exported CSV to %s (%d rows)", filepath, len(data))
            return True
        except Exception as exc:
            logger.error("CSV export failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _scalar(self, query: str, params: tuple = ()) -> Any:
        """Execute a query that returns a single value in column 'c'."""
        row = self.db.fetchone(query, params)
        return row['c'] if row else 0

    @staticmethod
    def _days_until(expiry_date_str: str) -> int:
        """Days from today until the given expiry date."""
        try:
            exp = date.fromisoformat(expiry_date_str)
            return (exp - date.today()).days
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _status_label(expiry_date_str: str) -> str:
        """Return the expiry status label for a date string."""
        try:
            exp = date.fromisoformat(expiry_date_str)
            days = (exp - date.today()).days
        except (ValueError, TypeError):
            days = 0

        if days < 0:
            return 'EXPIRED'
        if days <= 7:
            return 'CRITICAL'
        if days <= 15:
            return 'WARNING'
        if days <= 30:
            return 'UPCOMING'
        return 'NORMAL'
