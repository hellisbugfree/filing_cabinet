"""Base repository class for the filing cabinet."""
import sqlite3
from typing import List, Dict, Any, Optional

class BaseRepository:
    """Base repository class with common database operations."""

    def __init__(self, db_path: str):
        """Initialize with database path."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self) -> None:
        """Connect to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def execute(self, query: str, params: tuple = ()) -> None:
        """Execute a query and commit changes."""
        self.cursor.execute(query, params)
        self.conn.commit()

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch a single row as a dictionary."""
        self.cursor.execute(query, params)
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows as a list of dictionaries."""
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
