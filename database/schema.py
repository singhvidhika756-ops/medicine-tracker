"""
schema.py — Database schema initialisation for MediVault.

Creates all tables, indexes, and default settings when the application
starts for the first time (uses IF NOT EXISTS so it is safe to call
repeatedly).
"""

from database.connection import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger('medivault.schema')


def initialize_database(db: DatabaseManager) -> None:
    """
    Create all required tables, indexes, and default rows.

    This function is idempotent — it can be called every time the
    application starts without causing errors or duplicating data.

    Args:
        db: An active DatabaseManager instance.
    """
    conn = db.get_connection()
    cursor = conn.cursor()

    # ------------------------------------------------------------------
    # Tables
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            medicine_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name                TEXT    NOT NULL,
            generic_name        TEXT    DEFAULT '',
            category            TEXT    NOT NULL DEFAULT 'General',
            manufacturer        TEXT    DEFAULT '',
            description         TEXT    DEFAULT '',
            unit_type           TEXT    NOT NULL DEFAULT 'Tablet',
            min_stock_threshold INTEGER NOT NULL DEFAULT 10,
            created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            batch_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_id       INTEGER NOT NULL,
            batch_number      TEXT    NOT NULL,
            manufacturing_date TEXT   NOT NULL,
            expiry_date       TEXT    NOT NULL,
            purchase_date     TEXT    NOT NULL,
            quantity_received INTEGER NOT NULL CHECK(quantity_received >= 0),
            current_quantity  INTEGER NOT NULL DEFAULT 0 CHECK(current_quantity >= 0),
            purchase_price    REAL    NOT NULL DEFAULT 0.0 CHECK(purchase_price >= 0),
            selling_price     REAL    NOT NULL DEFAULT 0.0 CHECK(selling_price >= 0),
            supplier          TEXT    DEFAULT '',
            notes             TEXT    DEFAULT '',
            created_at        TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id) ON DELETE CASCADE,
            UNIQUE(medicine_id, batch_number)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_transactions (
            transaction_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id         INTEGER NOT NULL,
            medicine_id      INTEGER NOT NULL,
            transaction_type TEXT    NOT NULL
                             CHECK(transaction_type IN ('ADDED', 'REMOVED', 'ADJUSTED', 'INITIAL')),
            quantity_changed INTEGER NOT NULL CHECK(quantity_changed >= 0),
            previous_quantity INTEGER NOT NULL CHECK(previous_quantity >= 0),
            new_quantity     INTEGER NOT NULL CHECK(new_quantity >= 0),
            reason           TEXT    DEFAULT '',
            transaction_date TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (batch_id)    REFERENCES batches(batch_id)       ON DELETE CASCADE,
            FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id)  ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            contact     TEXT DEFAULT '',
            address     TEXT DEFAULT '',
            created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS application_settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # ------------------------------------------------------------------
    # Indexes
    # ------------------------------------------------------------------
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_batches_medicine_id  ON batches(medicine_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_batches_expiry_date  ON batches(expiry_date)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_batch_id     ON stock_transactions(batch_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_medicine_id  ON stock_transactions(medicine_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_date         ON stock_transactions(transaction_date)"
    )

    # ------------------------------------------------------------------
    # Default application settings (INSERT OR IGNORE = skip if present)
    # ------------------------------------------------------------------
    default_settings = [
        ('theme',               'light'),
        ('low_stock_threshold', '10'),
        ('near_expiry_days',    '30'),
        ('backup_on_exit',      'false'),
        ('currency_symbol',     '₹'),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO application_settings (key, value) VALUES (?, ?)",
        default_settings,
    )

    conn.commit()
    logger.info("Database schema initialised successfully.")
