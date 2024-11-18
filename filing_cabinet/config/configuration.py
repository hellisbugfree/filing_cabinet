from typing import Any, Optional, Dict
import sqlite3
from pathlib import Path
import json

class ConfigurationError(Exception):
    """Base exception for configuration related errors."""
    pass

class Configuration:
    """Manages application configuration settings."""
    
    # Default configuration values
    DEFAULT_CONFIG = {
        'cabinet.name': 'Filing Cabinet',
        'database.schema.version': '1.0.0',
        'file.index.extensions': ['.txt', '.pdf', '.doc', '.docx'],
        'file.checkin.max_size': 100 * 1024 * 1024,  # 100MB
        'storage.compression': 'none',
        'storage.encryption': 'none',
        'indexing.recursive': True,
        'indexing.follow_symlinks': False,
        'indexing.ignore_patterns': ['.git/*', '*.pyc', '__pycache__/*']
    }

    def __init__(self, db_path: str):
        """Initialize configuration with database path."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._ensure_config_table()

    def _connect(self) -> None:
        """Establish database connection."""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()

    def _close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def _ensure_config_table(self) -> None:
        """Ensure configuration table exists and has default values."""
        try:
            self._connect()
            # Create config table if it doesn't exist
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                default_value TEXT,
                description TEXT
            )
            ''')
            self.conn.commit()

            # Initialize default configuration
            for key, value in self.DEFAULT_CONFIG.items():
                self.create_config(key, value, value)

        except sqlite3.Error as e:
            raise ConfigurationError(f"Database error: {str(e)}")
        finally:
            self._close()

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
        finally:
            self._close()

    def put_config(self, key: str, value: Any) -> None:
        """
        Update configuration value for the given key.
        
        Args:
            key: Configuration key
            value: New value
        """
        try:
            self._connect()
            # Check if key exists
            self.cursor.execute('SELECT 1 FROM config WHERE key = ?', (key,))
            if not self.cursor.fetchone():
                raise ConfigurationError(f"Configuration key '{key}' not found")
            
            # Convert value to JSON string if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            self.cursor.execute(
                'UPDATE config SET value = ? WHERE key = ?',
                (value, key)
            )
            self.conn.commit()
            
        except sqlite3.Error as e:
            raise ConfigurationError(f"Database error: {str(e)}")
        finally:
            self._close()

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
            INSERT OR IGNORE INTO config (key, value, default_value, description)
            VALUES (?, ?, ?, ?)
            ''', (key, value, default, description))
            self.conn.commit()
            
        except sqlite3.Error as e:
            raise ConfigurationError(f"Database error: {str(e)}")
        finally:
            self._close()

    def reset_config(self, key: str) -> None:
        """
        Reset configuration value to its default.
        
        Args:
            key: Configuration key
        """
        try:
            self._connect()
            self.cursor.execute(
                'UPDATE config SET value = default_value WHERE key = ?',
                (key,)
            )
            self.conn.commit()
            
        except sqlite3.Error as e:
            raise ConfigurationError(f"Database error: {str(e)}")
        finally:
            self._close()

    def list_config(self) -> Dict[str, Dict[str, Any]]:
        """
        List all configuration entries.
        
        Returns:
            Dictionary of configuration entries with their values and metadata
        """
        try:
            self._connect()
            self.cursor.execute('SELECT key, value, default_value, description FROM config')
            rows = self.cursor.fetchall()
            
            config_dict = {}
            for key, value, default, description in rows:
                try:
                    parsed_value = json.loads(value)
                except json.JSONDecodeError:
                    parsed_value = value
                    
                try:
                    parsed_default = json.loads(default) if default else None
                except json.JSONDecodeError:
                    parsed_default = default
                
                config_dict[key] = {
                    'value': parsed_value,
                    'default': parsed_default,
                    'description': description
                }
                
            return config_dict
            
        except sqlite3.Error as e:
            raise ConfigurationError(f"Database error: {str(e)}")
        finally:
            self._close()

    def export_config(self, file_path: str) -> None:
        """
        Export configuration to a JSON file.
        
        Args:
            file_path: Path to export the configuration
        """
        config_dict = self.list_config()
        
        try:
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=4)
        except IOError as e:
            raise ConfigurationError(f"Failed to export configuration: {str(e)}")

    def import_config(self, file_path: str) -> None:
        """
        Import configuration from a JSON file.
        
        Args:
            file_path: Path to import the configuration from
        """
        try:
            with open(file_path, 'r') as f:
                config_dict = json.load(f)
            
            for key, data in config_dict.items():
                if 'value' in data:
                    self.create_config(
                        key,
                        data['value'],
                        data.get('default'),
                        data.get('description', '')
                    )
                    
        except IOError as e:
            raise ConfigurationError(f"Failed to import configuration: {str(e)}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid configuration file: {str(e)}")
