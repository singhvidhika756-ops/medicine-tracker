"""
backup.py — Database backup, restore, CSV export/import for MediVault.

All backup paths are resolved relative to the project root directory.
"""

import csv
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from utils.logger import setup_logger

# Project root is one level above the 'utils' package
BASE_DIR = Path(__file__).resolve().parent.parent

logger = setup_logger('medivault.backup')


# ---------------------------------------------------------------------------
# Backup & Restore
# ---------------------------------------------------------------------------
def create_backup(db_path: str = 'data/medivault.db',
                  backup_dir: str = 'backups') -> str:
    """
    Create a timestamped copy of the database file.

    A small JSON metadata file is saved alongside the backup.

    Args:
        db_path:    Path to the live database (relative to project root).
        backup_dir: Directory for backups (relative to project root).

    Returns:
        Absolute path to the new backup file.

    Raises:
        FileNotFoundError: If the source database does not exist.
    """
    source = BASE_DIR / db_path
    dest_dir = BASE_DIR / backup_dir

    if not source.exists():
        raise FileNotFoundError(f"Database not found: {source}")

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Build timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"medivault_backup_{timestamp}.db"
    backup_path = dest_dir / backup_name

    # Copy the database file
    shutil.copy2(str(source), str(backup_path))

    # Write metadata JSON next to the backup
    meta = {
        "backup_file": backup_name,
        "source_db": str(source),
        "created_at": datetime.now().isoformat(),
        "size_bytes": backup_path.stat().st_size,
    }
    meta_path = dest_dir / f"medivault_backup_{timestamp}.json"
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)

    logger.info("Backup created: %s", backup_path)
    return str(backup_path)


def restore_backup(backup_path: str, db_path: str = 'data/medivault.db') -> bool:
    """
    Restore a database from a backup file.

    A safety backup of the current database is created first.

    Args:
        backup_path: Absolute or relative path to the backup file.
        db_path:     Path to the live database (relative to project root).

    Returns:
        True on success, False on failure.
    """
    backup_src = Path(backup_path)
    if not backup_src.is_absolute():
        backup_src = BASE_DIR / backup_src

    if not backup_src.exists():
        logger.error("Backup file not found: %s", backup_src)
        return False

    target = BASE_DIR / db_path

    try:
        # Create a safety backup of the current DB (if it exists)
        if target.exists():
            safety_name = target.stem + "_pre_restore_" + \
                          datetime.now().strftime("%Y%m%d_%H%M%S") + target.suffix
            safety_path = target.parent / safety_name
            shutil.copy2(str(target), str(safety_path))
            logger.info("Safety backup created: %s", safety_path)

        # Overwrite live DB with the backup
        shutil.copy2(str(backup_src), str(target))
        logger.info("Database restored from: %s", backup_src)
        return True

    except Exception as exc:
        logger.error("Restore failed: %s", exc)
        return False


def list_backups(backup_dir: str = 'backups') -> List[Dict]:
    """
    List all backup files in the backup directory.

    Args:
        backup_dir: Backup directory path (relative to project root).

    Returns:
        List of dicts with keys: filename, date, size (human-readable).
    """
    dest_dir = BASE_DIR / backup_dir
    if not dest_dir.exists():
        return []

    backups: List[Dict] = []
    for entry in sorted(dest_dir.iterdir()):
        if entry.suffix == '.db' and entry.name.startswith('medivault_backup_'):
            stat = entry.stat()
            backups.append({
                "filename": entry.name,
                "path": str(entry),
                "date": datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "size": f"{stat.st_size / 1024:.1f} KB",
                "size_bytes": stat.st_size,
            })
    return backups


# ---------------------------------------------------------------------------
# CSV Export
# ---------------------------------------------------------------------------
def export_all_to_csv(db, export_dir: str = 'exports') -> List[str]:
    """
    Export medicines, batches, and transactions to separate CSV files.

    Args:
        db:         A DatabaseManager instance.
        export_dir: Directory for CSV files (relative to project root).

    Returns:
        List of absolute file paths that were created.
    """
    dest = BASE_DIR / export_dir
    dest.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exported: List[str] = []

    # --- Medicines --------------------------------------------------------
    try:
        medicines = db.fetchall("SELECT * FROM medicines")
        if medicines:
            path = dest / f"medicines_{timestamp}.csv"
            _write_csv(path, medicines)
            exported.append(str(path))
            logger.info("Exported medicines to %s", path)
    except Exception as exc:
        logger.error("Failed to export medicines: %s", exc)

    # --- Batches ----------------------------------------------------------
    try:
        batches = db.fetchall("SELECT * FROM batches")
        if batches:
            path = dest / f"batches_{timestamp}.csv"
            _write_csv(path, batches)
            exported.append(str(path))
            logger.info("Exported batches to %s", path)
    except Exception as exc:
        logger.error("Failed to export batches: %s", exc)

    # --- Stock transactions -----------------------------------------------
    try:
        txns = db.fetchall("SELECT * FROM stock_transactions")
        if txns:
            path = dest / f"transactions_{timestamp}.csv"
            _write_csv(path, txns)
            exported.append(str(path))
            logger.info("Exported transactions to %s", path)
    except Exception as exc:
        logger.error("Failed to export transactions: %s", exc)

    return exported


def _write_csv(filepath: Path, rows: List[Dict]) -> None:
    """Write a list of dicts to a CSV file (utf-8-sig for Excel)."""
    if not rows:
        return
    headers = list(rows[0].keys())
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# CSV Import
# ---------------------------------------------------------------------------
def import_medicines_from_csv(db, filepath: str) -> Tuple[int, List[str]]:
    """
    Import medicines from a CSV file into the database.

    Expected CSV columns (at minimum): name, category.
    Optional columns: generic_name, manufacturer, description,
                      unit_type, min_stock_threshold.

    Args:
        db:       A DatabaseManager instance.
        filepath: Path to the CSV file.

    Returns:
        Tuple of (success_count, list_of_error_messages).
    """
    from utils.validators import validate_medicine_name, validate_threshold

    csv_path = Path(filepath)
    if not csv_path.exists():
        return 0, [f"File not found: {filepath}"]

    success = 0
    errors: List[str] = []

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):  # row 1 is header
                # --- Validate name ---
                name = row.get('name', '').strip()
                ok, msg = validate_medicine_name(name)
                if not ok:
                    errors.append(f"Row {row_num}: {msg}")
                    continue

                # --- Validate threshold (if provided) ---
                threshold_raw = row.get('min_stock_threshold', '10').strip()
                ok, msg = validate_threshold(threshold_raw)
                if not ok:
                    errors.append(f"Row {row_num}: {msg}")
                    continue
                threshold = int(threshold_raw)

                # Build parameters with safe defaults
                params = (
                    name,
                    row.get('generic_name', '').strip(),
                    row.get('category', 'General').strip() or 'General',
                    row.get('manufacturer', '').strip(),
                    row.get('description', '').strip(),
                    row.get('unit_type', 'Tablet').strip() or 'Tablet',
                    threshold,
                )

                try:
                    db.execute(
                        """INSERT INTO medicines
                           (name, generic_name, category, manufacturer,
                            description, unit_type, min_stock_threshold)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        params,
                    )
                    success += 1
                except Exception as exc:
                    errors.append(f"Row {row_num}: DB error — {exc}")

    except Exception as exc:
        errors.append(f"Could not read CSV: {exc}")

    logger.info("CSV import: %d succeeded, %d errors", success, len(errors))
    return success, errors
