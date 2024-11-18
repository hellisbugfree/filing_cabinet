"""Configuration management for Filing Cabinet."""
import json
import sqlite3
from typing import Any, Dict, Optional

class ConfigurationError(Exception):
    """Configuration-related errors."""
    pass

class Configuration:
    """Configuration management class."""
    
    def __init__(self, db_path: str):
        """Initialize configuration with database path."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._create_tables()
    
    def _connect(self) -> None:
        """Connect to the database."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
    
    def _create_tables(self) -> None:
        """Create configuration tables."""
        try:
            self._connect()
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                default_value TEXT,
                description TEXT
            )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            raise ConfigurationError(f"Failed to create tables: {str(e)}")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value for the given key.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value
        """
        try:
            self._connect()
            self.cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
            row = self.cursor.fetchone()
            
            if row is None:
                if default is not None:
                    return default
                raise ConfigurationError(f"Configuration key '{key}' not found")
            
            # Try to parse as JSON, fallback to string if not valid JSON
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return row[0]
                
        except sqlite3.Error as e:
            raise ConfigurationError(f"Database error: {str(e)}")
    
    def put_config(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        try:
            self._connect()
            # Convert value to JSON string if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)
                
            self.cursor.execute('''
            UPDATE config SET value = ? WHERE key = ?
            ''', (value, key))
            self.conn.commit()
            
            if self.cursor.rowcount == 0:
                raise ConfigurationError(f"Configuration key '{key}' not found")
                
        except sqlite3.Error as e:
            raise ConfigurationError(f"Database error: {str(e)}")
    
    def create_config(self, key: str, value: Any, default: Any = None, description: str = '') -> None:
        """
        Create a new configuration entry.
        
        Args:
            key: Configuration key
            value: Initial value
            default: Default value
            description: Description of the configuration
        """
        try:
            self._connect()
            # Convert values to JSON strings if they're not strings
            if not isinstance(value, str):
                value = json.dumps(value)
            if default is not None and not isinstance(default, str):
                default = json.dumps(default)
                
            self.cursor.execute('''
            INSERT INTO config (key, value, default_value, description)
            VALUES (?, ?, ?, ?)
            ''', (key, value, default, description))
            self.conn.commit()
            
        except sqlite3.IntegrityError:
            raise ConfigurationError(f"Configuration key '{key}' already exists")
        except sqlite3.Error as e:
            raise ConfigurationError(f"Database error: {str(e)}")
    
    def reset_config(self, key: str) -> None:
        """
        Reset configuration to default value.
        
        Args:
            key: Configuration key
        """
        try:
            self._connect()
            self.cursor.execute('''
            UPDATE config SET value = default_value
            WHERE key = ? AND default_value IS NOT NULL
            ''', (key,))
            self.conn.commit()
            
            if self.cursor.rowcount == 0:
                raise ConfigurationError(f"Configuration key '{key}' not found or has no default value")
                
        except sqlite3.Error as e:
            raise ConfigurationError(f"Database error: {str(e)}")
    
    def list_config(self) -> Dict[str, Dict[str, Any]]:
        """
        List all configuration entries.
        
        Returns:
            Dictionary of configuration entries
        """
        try:
            self._connect()
            self.cursor.execute('SELECT key, value, default_value, description FROM config')
            rows = self.cursor.fetchall()
            
            config_dict = {}
            for key, value, default, description in rows:
                try:
                    config_dict[key] = {
                        'value': json.loads(value),
                        'default': json.loads(default) if default else None,
                        'description': description
                    }
                except json.JSONDecodeError:
                    config_dict[key] = {
                        'value': value,
                        'default': default,
                        'description': description
                    }
            
            return config_dict
            
        except sqlite3.Error as e:
            raise ConfigurationError(f"Database error: {str(e)}")
    
    def export_config(self, file_path: str) -> None:
        """
        Export configuration to a file.
        
        Args:
            file_path: Path to export file
        """
        try:
            config = self.list_config()
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            raise ConfigurationError(f"Failed to export configuration: {str(e)}")
    
    def import_config(self, file_path: str) -> None:
        """
        Import configuration from a file.
        
        Args:
            file_path: Path to import file
        """
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
                
            for key, entry in config.items():
                self.create_config(
                    key,
                    entry['value'],
                    entry.get('default'),
                    entry.get('description', '')
                )
        except Exception as e:
            raise ConfigurationError(f"Failed to import configuration: {str(e)}")
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
