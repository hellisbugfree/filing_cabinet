import sqlite3
from typing import Optional, List, Any
from datetime import datetime
from ..models.incarnation import Incarnation
from .base import BaseRepository

class IncarnationRepository(BaseRepository[Incarnation]):
    """Repository for managing Incarnation entities in the database."""

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
        """Create the file_incarnation table if it doesn't exist."""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_incarnation (
            incarnation_url TEXT PRIMARY KEY,
            incarnation_device TEXT,
            file_checksum TEXT,
            incarnation_type TEXT,
            forward_url TEXT,
            last_update_time_stamp DATETIME,
            FOREIGN KEY (file_checksum) REFERENCES file(checksum)
        )
        ''')
        self.conn.commit()

    def get(self, incarnation_url: str) -> Optional[Incarnation]:
        """Retrieve an incarnation by its URL."""
        self.cursor.execute(
            'SELECT incarnation_url, incarnation_device, file_checksum, incarnation_type, '
            'forward_url, last_update_time_stamp FROM file_incarnation WHERE incarnation_url = ?',
            (incarnation_url,)
        )
        row = self.cursor.fetchone()
        if not row:
            return None

        return Incarnation(
            incarnation_url=row[0],
            incarnation_device=row[1],
            file_checksum=row[2],
            incarnation_type=row[3],
            forward_url=row[4],
            last_update_timestamp=datetime.fromisoformat(row[5]) if row[5] else None
        )

    def add(self, incarnation: Incarnation) -> None:
        """Add a new incarnation to the repository. Updates if already exists."""
        existing = self.get(incarnation.incarnation_url)
        if existing:
            self.cursor.execute('''
            UPDATE file_incarnation SET
                incarnation_device = ?,
                file_checksum = ?,
                incarnation_type = ?,
                forward_url = ?,
                last_update_time_stamp = ?
            WHERE incarnation_url = ?
            ''', (
                incarnation.incarnation_device,
                incarnation.file_checksum,
                incarnation.incarnation_type,
                incarnation.forward_url,
                incarnation.last_update_timestamp.isoformat(),
                incarnation.incarnation_url
            ))
        else:
            self.cursor.execute('''
            INSERT INTO file_incarnation (
                incarnation_url, incarnation_device, file_checksum,
                incarnation_type, forward_url, last_update_time_stamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                incarnation.incarnation_url,
                incarnation.incarnation_device,
                incarnation.file_checksum,
                incarnation.incarnation_type,
                incarnation.forward_url,
                incarnation.last_update_timestamp.isoformat()
            ))
        self.conn.commit()

    def update(self, incarnation: Incarnation) -> None:
        """Update an existing incarnation."""
        incarnation.update_timestamp()
        self.cursor.execute('''
        UPDATE file_incarnation
        SET incarnation_device = ?, file_checksum = ?, incarnation_type = ?,
            forward_url = ?, last_update_time_stamp = ?
        WHERE incarnation_url = ?
        ''', (
            incarnation.incarnation_device,
            incarnation.file_checksum,
            incarnation.incarnation_type,
            incarnation.forward_url,
            incarnation.last_update_timestamp.isoformat(),
            incarnation.incarnation_url
        ))
        self.conn.commit()

    def delete(self, incarnation_url: str) -> None:
        """Delete an incarnation by its URL."""
        self.cursor.execute('DELETE FROM file_incarnation WHERE incarnation_url = ?', (incarnation_url,))
        self.conn.commit()

    def list(self, **filters: Any) -> List[Incarnation]:
        """List all incarnations matching the given filters."""
        query = '''
            SELECT incarnation_url, incarnation_device, file_checksum,
                   incarnation_type, forward_url, last_update_time_stamp
            FROM file_incarnation
        '''
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
            Incarnation(
                incarnation_url=row[0],
                incarnation_device=row[1],
                file_checksum=row[2],
                incarnation_type=row[3],
                forward_url=row[4],
                last_update_timestamp=datetime.fromisoformat(row[5]) if row[5] else None
            )
            for row in rows
        ]

    def get_incarnation_count(self) -> int:
        """Get the total number of incarnations in the repository."""
        self.cursor.execute('SELECT COUNT(*) FROM file_incarnation')
        return self.cursor.fetchone()[0]

    def get_incarnations_by_checksum(self, file_checksum: str) -> List[Incarnation]:
        """Get all incarnations for a specific file checksum."""
        return self.list(file_checksum=file_checksum)
