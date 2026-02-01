"""
Database Manager for H1B Wage Dashboard
Handles SQLite connections with proper cleanup and error handling
"""

import sqlite3
from contextlib import contextmanager
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages SQLite database connections
    Singleton pattern - only one connection pool throughout app
    """
    
    _instance = None
    
    def __new__(cls, db_path=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path=None):
        """
        Initialize database manager
        
        Args:
            db_path (str): Path to SQLite database file
                          Default: app/data/h1b_wages.db
        """
        if self._initialized:
            return
                
        if db_path is None:
            # Get project root and construct path
            current_dir = Path(__file__).resolve().parent
            project_root = current_dir.parent
            db_path = project_root / 'data' / 'h1b_wages.db'
        
        self.db_path = str(db_path)
        
        # Verify database exists
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                f"Database not found at {self.db_path}. "
                "Run 'python scripts/setup_database.py' first."
            )
        
        logger.info(f"Initializing database at {self.db_path}")
        
        # Test connection
        try:
            with self.get_connection() as conn:
                conn.execute("SELECT 1")
            logger.info("✓ Database connection test successful")
        except Exception as e:
            logger.error(f"✗ Database connection failed: {e}")
            raise
        
        # Enable foreign keys
        self._enable_foreign_keys()
        
        self._initialized = True
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections
        Automatically handles commit/rollback and cleanup
        
        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM geography")
                rows = cursor.fetchall()
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dicts
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _enable_foreign_keys(self):
        """Enable foreign key constraints"""
        with self.get_connection() as conn:
            conn.execute('PRAGMA foreign_keys = ON')
        logger.debug("Foreign keys enabled")
    
    def execute_query(self, query, params=()):
        """
        Execute SELECT query and return all results
        
        Args:
            query (str): SQL SELECT query
            params (tuple): Query parameters for safe interpolation
        
        Returns:
            list: List of sqlite3.Row objects (dict-like)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_single(self, query, params=()):
        """
        Execute SELECT query and return single row
        
        Args:
            query (str): SQL SELECT query
            params (tuple): Query parameters
        
        Returns:
            sqlite3.Row or None: Single row or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def get_table_count(self, table_name):
        """
        Get record count for a table
        
        Args:
            table_name (str): Name of table
        
        Returns:
            int: Number of records
        """
        result = self.execute_single(f"SELECT COUNT(*) FROM {table_name}")
        return result[0] if result else 0
    
    def get_database_info(self):
        """
        Get database size and record counts
        
        Returns:
            dict: Database metadata
        """
        return {
            'path': self.db_path,
            'size_mb': os.path.getsize(self.db_path) / 1024 / 1024,
            'geography_records': self.get_table_count('geography'),
            'occupations_records': self.get_table_count('occupations'),
            'wage_levels_records': self.get_table_count('wage_levels'),
        }
    

# Global singleton instance
db = DatabaseManager()