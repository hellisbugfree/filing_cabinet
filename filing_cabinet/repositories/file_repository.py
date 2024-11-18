import sqlite3
from typing import Optional, List, Any
from datetime import datetime
from ..models.file import File
from .base import BaseRepository

class FileRepository(BaseRepository[File]):
    """Repository for managing File entities in the database."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self) -> None:
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def _create_table(self) -> None:
        """Create the file table if it doesn't exist."""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS file (
            checksum TEXT PRIMARY KEY,
            url TEXT,
            filed_time_stamp DATETIME,
            last_update_time_stamp DATETIME,
            name TEXT,
            size INTEGER,
            content BLOB
        )
        ''')
        self.conn.commit()

    def get(self, checksum: str) -> Optional[File]:
        """Retrieve a file by its checksum."""
        self.cursor.execute(
            'SELECT checksum, url, filed_time_stamp, last_update_time_stamp, name, size, content '
            'FROM file WHERE checksum = ?',
            (checksum,)
        )
        row = self.cursor.fetchone()
        if not row:
            return None

        return File(
            checksum=row[0],
            url=row[1],
            filed_timestamp=datetime.fromisoformat(row[2]) if row[2] else None,
            last_update_timestamp=datetime.fromisoformat(row[3]) if row[3] else None,
            name=row[4],
            size=row[5],
            content=row[6]
        )

    def add(self, file: File) -> None:
        """Add a new file to the repository."""
        self.cursor.execute('''
        INSERT INTO file (checksum, url, filed_time_stamp, last_update_time_stamp, name, size, content)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            file.checksum,
            file.url,
            file.filed_timestamp.isoformat() if file.filed_timestamp else None,
            file.last_update_timestamp.isoformat() if file.last_update_timestamp else None,
            file.name,
            file.size,
            file.content
        ))
        self.conn.commit()

    def update(self, file: File) -> None:
        """Update an existing file."""
        file.update_timestamp()
        self.cursor.execute('''
        UPDATE file
        SET url = ?, last_update_time_stamp = ?, name = ?, size = ?, content = ?
        WHERE checksum = ?
        ''', (
            file.url,
            file.last_update_timestamp.isoformat(),
            file.name,
            file.size,
            file.content,
            file.checksum
        ))
        self.conn.commit()

    def delete(self, checksum: str) -> None:
        """Delete a file by its checksum."""
        self.cursor.execute('DELETE FROM file WHERE checksum = ?', (checksum,))
        self.conn.commit()

    def list(self, **filters: Any) -> List[File]:
        """List all files matching the given filters."""
        query = 'SELECT checksum, url, filed_time_stamp, last_update_time_stamp, name, size, content FROM file'
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f'{key} = ?')
                params.append(value)
            query += ' WHERE ' + ' AND '.join(conditions)

        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()

        return [
            File(
                checksum=row[0],
                url=row[1],
                filed_timestamp=datetime.fromisoformat(row[2]) if row[2] else None,
                last_update_timestamp=datetime.fromisoformat(row[3]) if row[3] else None,
                name=row[4],
                size=row[5],
                content=row[6]
            )
            for row in rows
        ]

    def get_file_count(self) -> int:
        """Get the total number of files in the repository."""
        self.cursor.execute('SELECT COUNT(*) FROM file')
        return self.cursor.fetchone()[0]
