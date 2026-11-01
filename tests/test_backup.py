"""
test_backup.py — Unit tests for database backup, snapshot listing, and CSV import in MediVault.
"""

import os
import unittest
from pathlib import Path

from database.connection import DatabaseManager
from database.schema import initialize_database
from utils.backup import (
    create_backup, list_backups, restore_backup, import_medicines_from_csv,
)


class TestBackupAndImport(unittest.TestCase):
    """Test suite for database backups and CSV import routines."""

    TEST_DB = "data/test_backup.db"
    BACKUP_DIR = "data/test_backups"
    SAMPLE_CSV = "data/test_import.csv"

    def setUp(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self._cleanup()

        self.db = DatabaseManager(self.TEST_DB)
        initialize_database(self.db)
        self.db.execute(
            "INSERT INTO medicines (name, category) VALUES ('Backup Test Med', 'General')"
        )

    def tearDown(self):
        self.db.close()
        self._cleanup()

    def _cleanup(self):
        db_file = self.base_dir / self.TEST_DB
        if db_file.exists():
            try:
                os.remove(db_file)
            except OSError:
                pass

        for safety_file in self.base_dir.glob("test_backup_pre_restore_*.db"):
            try:
                os.remove(safety_file)
            except OSError:
                pass

        b_dir = self.base_dir / self.BACKUP_DIR
        if b_dir.exists():
            for f in b_dir.glob("*"):
                try:
                    os.remove(f)
                except OSError:
                    pass
            try:
                b_dir.rmdir()
            except OSError:
                pass

        csv_file = self.base_dir / self.SAMPLE_CSV
        if csv_file.exists():
            try:
                os.remove(csv_file)
            except OSError:
                pass

    def test_create_and_list_backup(self):
        backup_path = create_backup(db_path=self.TEST_DB, backup_dir=self.BACKUP_DIR)
        self.assertTrue(Path(backup_path).exists())

        backups = list_backups(backup_dir=self.BACKUP_DIR)
        self.assertEqual(len(backups), 1)
        self.assertIn("medivault_backup_", backups[0]['filename'])

    def test_import_medicines_from_csv(self):
        csv_path = self.base_dir / self.SAMPLE_CSV
        csv_content = (
            "name,generic_name,category,unit_type,min_stock_threshold\n"
            "Imported Drug A,Generic A,Analgesic,Tablet,20\n"
            "Imported Drug B,Generic B,Antibiotic,Capsule,15\n"
        )
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)

        count, errors = import_medicines_from_csv(self.db, str(csv_path))
        self.assertEqual(count, 2)
        self.assertEqual(len(errors), 0)

        rows = self.db.fetchall("SELECT * FROM medicines WHERE name LIKE 'Imported Drug%'")
        self.assertEqual(len(rows), 2)

    def test_restore_uses_listed_backup_path(self):
        create_backup(db_path=self.TEST_DB, backup_dir=self.BACKUP_DIR)
        self.db.execute("UPDATE medicines SET name = 'Changed After Backup'")

        backups = list_backups(backup_dir=self.BACKUP_DIR)
        self.db.close()
        self.assertTrue(restore_backup(backups[0]['path'], db_path=self.TEST_DB))
        self.db.get_connection()
        restored = self.db.fetchone("SELECT name FROM medicines")
        self.assertEqual(restored['name'], 'Backup Test Med')


if __name__ == '__main__':
    unittest.main()

