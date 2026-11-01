"""
logger.py — Logging utility for MediVault application.

Sets up a rotating file logger with console output so that
every important event (errors, info, debug) is recorded.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(name: str = 'medivault',
                 log_file: str = 'data/medivault.log') -> logging.Logger:
    """
    Create and configure a logger with both file and console handlers.

    Args:
        name:     Name for the logger instance.
        log_file: Path to the log file, relative to the project root.

    Returns:
        A configured logging.Logger object.
    """
    # Resolve the log file path relative to the project root
    # Project root is one level above the 'utils' package
    base_dir = Path(__file__).resolve().parent.parent
    configured_log = os.environ.get("MEDIVAULT_LOG_FILE")
    log_path = Path(configured_log) if configured_log else base_dir / log_file

    # Make sure the directory for the log file exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Get (or create) a named logger
    logger = logging.getLogger(name)

    # Only add handlers if the logger doesn't already have them
    # (prevents duplicate log lines when setup_logger is called twice)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # --- Formatter ---------------------------------------------------
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # --- Rotating file handler ---------------------------------------
        # Max 5 MB per file, keep 3 old backup copies
        file_handler = RotatingFileHandler(
            str(log_path),
            maxBytes=5 * 1024 * 1024,   # 5 MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # --- Console handler ---------------------------------------------
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # Attach handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
