"""
MediVault — Medicine Inventory & Expiry Management System
A locally running Python application for managing medicine inventory,
tracking expiry dates, and monitoring stock levels.

Run with: python main.py
"""

import sys
import os
import ctypes
from pathlib import Path

# Ensure High DPI awareness on Windows for razor-sharp typography
if sys.platform == 'win32':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import DatabaseManager
from database.schema import initialize_database
from utils.logger import setup_logger
from ui.app import MediVaultApp


def main():
    """Main entry point for MediVault application."""
    # Setup logging
    logger = setup_logger()
    logger.info("Starting MediVault application...")
    
    try:
        # Initialize database
        db = DatabaseManager()
        initialize_database(db)
        logger.info("Database initialized successfully.")
        
        # Launch GUI
        app = MediVaultApp(db)
        app.mainloop()
        
        # Cleanup
        db.close()
        logger.info("MediVault application closed.")
        
    except Exception as e:
        logger.critical(f"Failed to start MediVault: {e}", exc_info=True)
        print(f"\nError: Failed to start MediVault.\n{e}")
        print("\nPlease check the log file at data/medivault.log for details.")
        sys.exit(1)


if __name__ == '__main__':
    main()
