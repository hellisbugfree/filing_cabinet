import sqlite3
import os
import hashlib
from datetime import datetime
from typing import Optional
from .utils import get_device_identifier, get_file_type, get_absolute_path

class FilingCabinetDB:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close(self):
        if self.conn:
            self.conn.close()

    def create_tables(self):
        """Create the database tables."""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        ''')

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

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_incarnation (
            incarnation_url TEXT UNIQUE,
            incarnation_device TEXT,
            file_checksum TEXT,
            incarnation_type TEXT,
            forward_url TEXT,
            last_update_time_stamp DATETIME
        )
        ''')

        self.conn.commit()

    def insert_file(self, file_path):
        with open(file_path, 'rb') as f:
            content = f.read()
            checksum = hashlib.md5(content).hexdigest()
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            current_time = datetime.now().isoformat()

            self.cursor.execute('''
            INSERT OR REPLACE INTO file (checksum, url, filed_time_stamp, last_update_time_stamp, name, size, content)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (checksum, file_path, current_time, current_time, file_name, file_size, content))

            self.conn.commit()
            return checksum

    def get_file_info(self, file_path):
        if os.path.islink(file_path):
            target_path = os.path.realpath(file_path)
            with open(target_path, 'rb') as f:
                content = f.read()
                checksum = hashlib.md5(content).hexdigest()
        else:
            with open(file_path, 'rb') as f:
                content = f.read()
                checksum = hashlib.md5(content).hexdigest()

        self.cursor.execute('SELECT * FROM file WHERE checksum = ?', (checksum,))
        file_info = self.cursor.fetchone()

        self.cursor.execute('SELECT * FROM file_incarnation WHERE file_checksum = ?', (checksum,))
        incarnations = self.cursor.fetchall()

        return file_info, incarnations

    def checkout_file(self, checksum, output_path):
        self.cursor.execute('SELECT content, name FROM file WHERE checksum = ?', (checksum,))
        result = self.cursor.fetchone()

        if result:
            content, name = result
            full_path = os.path.join(output_path, name)
            with open(full_path, 'wb') as f:
                f.write(content)
            return full_path
        else:
            return None

    def get_file_count(self) -> int:
        """Get the total number of files in the database."""
        self.cursor.execute("SELECT COUNT(*) FROM file")
        count = self.cursor.fetchone()[0]
        return count

    def get_incarnation_count(self) -> int:
        """Get the total number of file incarnations in the database."""
        self.cursor.execute("SELECT COUNT(*) FROM file_incarnation")
        count = self.cursor.fetchone()[0]
        return count

    def get_config(self, key: str) -> Optional[str]:
        """Get configuration value from database."""
        self.cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def put_config(self, key: str, value: str) -> None:
        """Set configuration value in database."""
        self.cursor.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, value)
        )
        self.conn.commit()

    def config_exists(self, key: str) -> bool:
        """Check if configuration key exists."""
        self.cursor.execute("SELECT 1 FROM config WHERE key = ?", (key,))
        return self.cursor.fetchone() is not None

    def insert_file_incarnation(self, file_path, checksum):
        """Insert a new file incarnation record."""
        abs_path = get_absolute_path(file_path)
        device_id = get_device_identifier()
        file_type, forward_url = get_file_type(file_path)
        
        self.cursor.execute('''
            INSERT OR REPLACE INTO file_incarnation 
            (incarnation_url, incarnation_device, file_checksum, incarnation_type, forward_url, last_update_time_stamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (abs_path, device_id, checksum, file_type, forward_url, datetime.now()))
        self.conn.commit()
        return abs_path

    def get_file_incarnations(self, file_path=None, checksum=None):
        """Get all incarnations of a file, either by path or checksum."""
        query = '''
            SELECT 
                incarnation_url,
                incarnation_device,
                file_checksum,
                incarnation_type,
                forward_url,
                last_update_time_stamp
            FROM file_incarnation
        '''
        params = []
        if file_path:
            query += ' WHERE incarnation_url = ?'
            params.append(get_absolute_path(file_path))
        elif checksum:
            query += ' WHERE file_checksum = ?'
            params.append(checksum)
            
        self.cursor.execute(query, params)
        return self.cursor.fetchall()