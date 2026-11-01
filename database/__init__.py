"""
database — Database package for MediVault.

Exports:
    DatabaseManager    — connection and query helper
    initialize_database — schema creation function
"""

from .connection import DatabaseManager
from .schema import initialize_database
