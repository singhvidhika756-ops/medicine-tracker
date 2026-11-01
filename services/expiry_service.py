"""
expiry_service.py — Expiry tracking and alerting for MediVault.

Categorises batches by how close they are to expiring and provides
summary counts for the dashboard.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Tuple

from database.connection import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger('medivault.expiry_service')


class ExpiryService:
    """
    Provides expiry-date queries and status classification.

    Status labels:
        EXPIRED  — past expiry date
        CRITICAL — 0–7 days remaining
        WARNING  — 8–15 days remaining
        UPCOMING — 16–30 days remaining
        NORMAL   — > 30 days remaining
    """

    def __init__(self, db: DatabaseManager) -> None:
        """
        Args:
            db: An active DatabaseManager instance.
        """
        self.db = db

    # ------------------------------------------------------------------
    # Status computation (pure logic, no DB)
    # ------------------------------------------------------------------
    @staticmethod
    def get_expiry_status(expiry_date_str: str) -> Tuple[str, int]:
        """
        Determine the expiry status label and days remaining.

        Args:
            expiry_date_str: Expiry date in YYYY-MM-DD format.

        Returns:
            Tuple of (status_label, days_remaining).
            days_remaining is negative for expired items.
        """
        try:
            exp = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
            days = (exp - date.today()).days
        except (ValueError, TypeError):
            days = 0

        if days < 0:
            return ('EXPIRED', days)
        if days <= 7:
            return ('CRITICAL', days)
        if days <= 15:
            return ('WARNING', days)
        if days <= 30:
            return ('UPCOMING', days)
        return ('NORMAL', days)

    # ------------------------------------------------------------------
    # Filtered queries
    # ------------------------------------------------------------------
    def _fetch_batches_with_status(self) -> List[Dict[str, Any]]:
        """Fetch all batches with medicine name, add computed fields."""
        rows = self.db.fetchall("""
            SELECT b.*, m.name AS medicine_name
            FROM   batches b
            JOIN   medicines m ON m.medicine_id = b.medicine_id
            ORDER BY b.expiry_date ASC
        """)
        for r in rows:
            status, days = self.get_expiry_status(r['expiry_date'])
            r['expiry_status'] = status
            r['days_until_expiry'] = days
        return rows

    def get_expired_batches(self) -> List[Dict[str, Any]]:
        """
        Return batches whose expiry date is in the past.

        Returns:
            List of batch dicts with medicine_name, expiry_status, days_until_expiry.
        """
        today_str = date.today().strftime("%Y-%m-%d")
        rows = self.db.fetchall("""
            SELECT b.*, m.name AS medicine_name
            FROM   batches b
            JOIN   medicines m ON m.medicine_id = b.medicine_id
            WHERE  b.expiry_date < ?
            ORDER BY b.expiry_date ASC
        """, (today_str,))
        for r in rows:
            status, days = self.get_expiry_status(r['expiry_date'])
            r['expiry_status'] = status
            r['days_until_expiry'] = days
        return rows

    def get_critical_batches(self) -> List[Dict[str, Any]]:
        """
        Return batches expiring within 7 days (not already expired).

        Returns:
            List of batch dicts.
        """
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")
        from datetime import timedelta
        end_str = (today + timedelta(days=7)).strftime("%Y-%m-%d")

        rows = self.db.fetchall("""
            SELECT b.*, m.name AS medicine_name
            FROM   batches b
            JOIN   medicines m ON m.medicine_id = b.medicine_id
            WHERE  b.expiry_date >= ? AND b.expiry_date <= ?
            ORDER BY b.expiry_date ASC
        """, (today_str, end_str))
        for r in rows:
            status, days = self.get_expiry_status(r['expiry_date'])
            r['expiry_status'] = status
            r['days_until_expiry'] = days
        return rows

    def get_warning_batches(self) -> List[Dict[str, Any]]:
        """
        Return batches expiring in 8–15 days.

        Returns:
            List of batch dicts.
        """
        today = date.today()
        from datetime import timedelta
        start_str = (today + timedelta(days=8)).strftime("%Y-%m-%d")
        end_str = (today + timedelta(days=15)).strftime("%Y-%m-%d")

        rows = self.db.fetchall("""
            SELECT b.*, m.name AS medicine_name
            FROM   batches b
            JOIN   medicines m ON m.medicine_id = b.medicine_id
            WHERE  b.expiry_date >= ? AND b.expiry_date <= ?
            ORDER BY b.expiry_date ASC
        """, (start_str, end_str))
        for r in rows:
            status, days = self.get_expiry_status(r['expiry_date'])
            r['expiry_status'] = status
            r['days_until_expiry'] = days
        return rows

    def get_upcoming_batches(self) -> List[Dict[str, Any]]:
        """
        Return batches expiring in 16–30 days.

        Returns:
            List of batch dicts.
        """
        today = date.today()
        from datetime import timedelta
        start_str = (today + timedelta(days=16)).strftime("%Y-%m-%d")
        end_str = (today + timedelta(days=30)).strftime("%Y-%m-%d")

        rows = self.db.fetchall("""
            SELECT b.*, m.name AS medicine_name
            FROM   batches b
            JOIN   medicines m ON m.medicine_id = b.medicine_id
            WHERE  b.expiry_date >= ? AND b.expiry_date <= ?
            ORDER BY b.expiry_date ASC
        """, (start_str, end_str))
        for r in rows:
            status, days = self.get_expiry_status(r['expiry_date'])
            r['expiry_status'] = status
            r['days_until_expiry'] = days
        return rows

    def get_near_expiry_batches(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Return all batches expiring within *days* days (not already expired).

        Args:
            days: Look-ahead window in days.

        Returns:
            List of batch dicts.
        """
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")
        from datetime import timedelta
        end_str = (today + timedelta(days=days)).strftime("%Y-%m-%d")

        rows = self.db.fetchall("""
            SELECT b.*, m.name AS medicine_name
            FROM   batches b
            JOIN   medicines m ON m.medicine_id = b.medicine_id
            WHERE  b.expiry_date >= ? AND b.expiry_date <= ?
            ORDER BY b.expiry_date ASC
        """, (today_str, end_str))
        for r in rows:
            status, d = self.get_expiry_status(r['expiry_date'])
            r['expiry_status'] = status
            r['days_until_expiry'] = d
        return rows

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    def get_expiry_summary(self) -> Dict[str, int]:
        """
        Compute counts for each expiry status category.

        Returns:
            Dict with keys: expired_count, critical_count,
            warning_count, upcoming_count, normal_count.
        """
        all_batches = self._fetch_batches_with_status()
        summary = {
            'expired_count':  0,
            'critical_count': 0,
            'warning_count':  0,
            'upcoming_count': 0,
            'normal_count':   0,
        }
        for b in all_batches:
            status = b['expiry_status']
            if status == 'EXPIRED':
                summary['expired_count'] += 1
            elif status == 'CRITICAL':
                summary['critical_count'] += 1
            elif status == 'WARNING':
                summary['warning_count'] += 1
            elif status == 'UPCOMING':
                summary['upcoming_count'] += 1
            else:
                summary['normal_count'] += 1
        return summary

    def get_all_batches_with_status(self) -> List[Dict[str, Any]]:
        """
        Return every batch with its expiry status label and days remaining.

        Returns:
            List of batch dicts sorted by expiry_date ascending.
        """
        return self._fetch_batches_with_status()
