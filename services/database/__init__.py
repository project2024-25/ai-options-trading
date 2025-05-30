# services/database/__init__.py
"""
Database services for AI Options Trading System

This package provides database connectivity and operations for storing:
- Live NIFTY ₹24,833.6 market data
- 30+ Lakh OI options chain data  
- Trading signals and performance metrics
- Technical indicators and analysis results
"""

from .db_service import (
    DatabaseService,
    DatabaseManager,
    get_database_service,
    close_database_service,
    with_database
)

from .migrations import (
    DatabaseMigration,
    run_initial_migration
)

__all__ = [
    'DatabaseService',
    'DatabaseManager', 
    'get_database_service',
    'close_database_service',
    'with_database',
    'DatabaseMigration',
    'run_initial_migration'
]

__version__ = '1.0.0'