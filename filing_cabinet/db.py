import sqlite3
import os
import hashlib
from datetime import datetime

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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_checksum TEXT,
            incarnation_url TEXT,
            incarnation_type TEXT,
            forward_url TEXT,
            status TEXT,
            status_last_checked_time_stamp DATETIME,
            FOREIGN KEY (file_checksum) REFERENCES file (checksum)
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