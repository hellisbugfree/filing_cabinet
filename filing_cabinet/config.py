"""Configuration management for Filing Cabinet."""
import os
from typing import Any, Optional
from filing_cabinet.db import FilingCabinetDB

__all__ = ['Config', 'ConfigurationError', 'get_config']

class ConfigurationError(Exception):
    """Custom exception for configuration related errors."""
    pass

DEFAULT_CONFIG = {
    # Cabinet settings
    "cabinet.path": None,  # Will be set during initialization
    "cabinet.name": None,  # Will be set based on path
    
    # Database settings
    "database.schema.version": "0.1.0",
    
    # File settings
    "file.checkin.max_size": 5 * 1024 * 1024,  # 5MB in bytes
    "file.checkin.max_files_at_once.warning": 10,
    "file.index.extensions": ".pdf,.png,.jpg,.jpeg",
    "file.index.max_size": 5 * 1024 * 1024,  # 5MB in bytes
    "file.index.date_range_days": 30,
}

class Config:
    _instance = None

    @classmethod
    def get_instance(cls, db_path: Optional[str] = None) -> 'Config':
        if cls._instance is None:
            if db_path is None:
                db_path = os.path.expanduser('~/filing.cabinet')
            cls._instance = Config(db_path)
        return cls._instance

    def __init__(self, db_path: str):
        """Initialize Config with database path."""
        self.db = FilingCabinetDB(db_path)
        self.db.connect()
        self.db.create_tables()
        self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        """Initialize default configuration values in database."""
        for key, default_value in DEFAULT_CONFIG.items():
            self.create_config(key, default_value, default_value)

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value for key.
        
        For user.* keys:
        - Creates the key with default value if it doesn't exist
        
        For system keys:
        - Raises ConfigurationError if key doesn't exist and no default provided
        """
        value = self.db.get_config(key)
        
        if value is not None:
            return self._convert_value(value)
            
        if key.startswith("user."):
            return self.create_config(key, default, default)
            
        if default is not None:
            return default
            
        raise ConfigurationError(f"Configuration key '{key}' not found")

    def put_config(self, key: str, value: Any) -> None:
        """
        Set configuration value for key.
        Key must exist, use create_config for new keys.
        """
        if not self.db.config_exists(key):
            raise ConfigurationError(f"Configuration key '{key}' does not exist")
            
        self.db.put_config(key, str(value))

    def create_config(self, key: str, value: Any, default: Any) -> Any:
        """
        Create a new configuration entry.
        For user.* keys, always creates or updates.
        For system keys, only creates if doesn't exist.
        """
        if not key.startswith("user.") and self.db.config_exists(key):
            return self._convert_value(self.db.get_config(key))
            
        self.db.put_config(key, str(value))
        return value

    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type."""
        # Handle booleans
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Handle lists (comma-separated strings)
        if ',' in value:
            return [item.strip() for item in value.split(',')]
            
        # Handle numbers
        try:
            if value.isdigit():
                return int(value)
            if value.replace('.', '', 1).isdigit():
                return float(value)
        except (ValueError, AttributeError):
            pass
            
        return value

    def close(self) -> None:
        """Close database connection."""
        self.db.close()

def get_config() -> Config:
    """Get the global configuration instance."""
    return Config.get_instance()
