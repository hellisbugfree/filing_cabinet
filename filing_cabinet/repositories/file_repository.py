"""File repository for the filing cabinet."""
import sqlite3
from typing import Optional, List, Dict, Any
from ..models.file import File
from .base import BaseRepository

class FileRepository(BaseRepository):
    """Repository for managing files in the database."""

    def __init__(self, db_path: str):
        """Initialize the repository with database path."""
        super().__init__(db_path)
        self.connect()  # Connect immediately
        self.create_table()

    def __del__(self):
        """Cleanup database connection."""
        self.close()

    def create_table(self) -> None:
        """Create the files table if it doesn't exist."""
        self.execute("""
            CREATE TABLE IF NOT EXISTS file (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checksum TEXT NOT NULL,
                name TEXT NOT NULL,
                size INTEGER NOT NULL,
                path TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(checksum, path)
            )
        """)

    def save(self, file: File) -> None:
        """Save a file to the database."""
        self.execute(
            """
            INSERT OR REPLACE INTO file (
                checksum, name, size, path, mime_type
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (file.checksum, file.name, file.size, file.path, file.mime_type)
        )

    def get_by_id(self, file_id: str) -> Optional[File]:
        """Get a file by its ID."""
        row = self.fetch_one(
            "SELECT * FROM file WHERE id = ?",
            (file_id,)
        )
        if row:
            file = File(row['path'])
            return file
        return None

    def get_by_checksum(self, checksum: str) -> Optional[File]:
        """Get a file by its checksum."""
        row = self.fetch_one(
            "SELECT * FROM file WHERE checksum = ?",
            (checksum,)
        )
        if row:
            file = File(row['path'])
            return file
        return None

    def index_file(self, file_path: str) -> None:
        """Index a file's basic information."""
        file = File(file_path)
        self.execute(
            """
            INSERT OR REPLACE INTO file (
                checksum, name, size, path, mime_type
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (file.checksum, file.name, file.size, file.path, file.mime_type)
        )

    def delete(self, file_id: str) -> bool:
        """Delete a file by its ID."""
        self.execute(
            "DELETE FROM file WHERE id = ?",
            (file_id,)
        )
        return True

    def search(self, query: str) -> List[File]:
        """Search for files by name or path."""
        rows = self.fetch_all(
            """
            SELECT * FROM file 
            WHERE name LIKE ? OR path LIKE ?
            ORDER BY created_at DESC
            """,
            (f"%{query}%", f"%{query}%")
        )
        return [File(row['path']) for row in rows]

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the files."""
        stats = self.fetch_one("""
            SELECT 
                COUNT(*) as total_files,
                COALESCE(SUM(size), 0) as total_size
            FROM file
        """)
        return {
            "total_files": stats['total_files'],
            "total_size": stats['total_size']
        }
