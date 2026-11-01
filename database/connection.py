"""
connection.py — SQLite database connection manager for MediVault.

Provides a DatabaseManager class that handles opening, closing, and
querying the SQLite database with automatic foreign-key enforcement.
"""

import sqlite3
import threading
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from utils.logger import setup_logger

# Project root is one level above the 'database' package
BASE_DIR = Path(__file__).resolve().parent.parent

logger = setup_logger('medivault.db')


class DatabaseManager:
    """
    Manages a single SQLite connection with convenience helpers.

    Usage:
        db = DatabaseManager()              # uses default path
        db = DatabaseManager('data/test.db')

        # As a context manager (auto-closes on exit):
        with DatabaseManager() as db:
            rows = db.fetchall("SELECT * FROM medicines")
    """

    def __init__(self, db_path: str = "data/medivault.db") -> None:
        """
        Initialise the manager.

        Args:
            db_path: Database file path relative to the project root.
        """
        configured_path = os.environ.get("MEDIVAULT_DB_PATH")
        self.db_path: Path = Path(configured_path) if configured_path else BASE_DIR / db_path
        # Ensure the parent directory exists (e.g. 'data/')
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Connection is created lazily by get_connection()
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()
        logger.debug("DatabaseManager initialised — path: %s", self.db_path)

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------
    def get_connection(self) -> sqlite3.Connection:
        """
        Return an open SQLite connection, creating one if necessary.

        The connection uses sqlite3.Row as row_factory so that rows
        behave like dictionaries. Foreign-key enforcement is enabled.

        Returns:
            An open sqlite3.Connection.
        """
        with self._lock:
            if self._connection is None:
                self._connection = sqlite3.connect(
                    str(self.db_path), check_same_thread=False
                )
            # Rows accessible by column name
                self._connection.row_factory = sqlite3.Row
                # Enforce foreign-key constraints
                self._connection.execute("PRAGMA foreign_keys = ON")
                logger.debug("Opened database connection: %s", self.db_path)
            return self._connection

    def close(self) -> None:
        """Close the database connection if it is open."""
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None
                logger.debug("Closed database connection.")

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """
        Execute a single SQL statement and commit.

        Args:
            query:  SQL query string with '?' placeholders.
            params: Tuple of parameters to bind.

        Returns:
            The sqlite3.Cursor after execution.
        """
        with self._lock:
            conn = self.get_connection()
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor

    def executemany(self, query: str, params_list: List[Tuple]) -> sqlite3.Cursor:
        """
        Execute a SQL statement for each set of parameters and commit.

        Args:
            query:       SQL query string with '?' placeholders.
            params_list: List of parameter tuples.

        Returns:
            The sqlite3.Cursor after execution.
        """
        with self._lock:
            conn = self.get_connection()
            cursor = conn.executemany(query, params_list)
            conn.commit()
            return cursor

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Run multiple statements as one commit-or-rollback unit."""
        with self._lock:
            conn = self.get_connection()
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def fetchone(self, query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Execute a query and return the first row as a dict, or None.

        Args:
            query:  SQL query string.
            params: Tuple of parameters.

        Returns:
            A dict representing the row, or None if no rows matched.
        """
        with self._lock:
            conn = self.get_connection()
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            if row is None:
                return None
            return dict(row)

    def fetchall(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a query and return all rows as a list of dicts.

        Args:
            query:  SQL query string.
            params: Tuple of parameters.

        Returns:
            List of dicts (one per row).  Empty list if no rows.
        """
        with self._lock:
            conn = self.get_connection()
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Context-manager support
    # ------------------------------------------------------------------
    def __enter__(self) -> "DatabaseManager":
        """Enter the context — return self."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context — close the connection."""
        self.close()
