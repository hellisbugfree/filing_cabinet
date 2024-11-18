from typing import Optional, Any
from pathlib import Path
from .configuration import Configuration, ConfigurationError

class ConfigService:
    """Singleton service for managing configuration."""
    
    _instance: Optional['ConfigService'] = None
    _config: Optional[Configuration] = None
    
    def __new__(cls, db_path: Optional[str] = None) -> 'ConfigService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            if db_path:
                cls._instance._init(db_path)
        return cls._instance

    def _init(self, db_path: str) -> None:
        """Internal initialization method."""
        if self._config is None:
            self._config = Configuration(db_path)

    @classmethod
    def initialize(cls, db_path: str) -> None:
        """Initialize the configuration service with a database path."""
        if cls._instance is None:
            cls._instance = cls(db_path)
        elif cls._config is None:
            cls._instance._init(db_path)

    @classmethod
    def get_instance(cls) -> 'ConfigService':
        """Get the singleton instance of the configuration service."""
        if cls._instance is None:
            raise ConfigurationError("Configuration service not initialized. Call ConfigService(db_path) first.")
        return cls._instance

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        if self._config is None:
            raise ConfigurationError("Configuration not initialized")
        return self._config.get_config(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        if self._config is None:
            raise ConfigurationError("Configuration not initialized")
        self._config.put_config(key, value)

    def create(self, key: str, value: Any, default: Any = None, description: str = '') -> None:
        """Create new configuration entry."""
        if self._config is None:
            raise ConfigurationError("Configuration not initialized")
        self._config.create_config(key, value, default, description)

    def reset(self, key: str) -> None:
        """Reset configuration to default value."""
        if self._config is None:
            raise ConfigurationError("Configuration not initialized")
        self._config.reset_config(key)

    def list_all(self) -> dict:
        """List all configuration entries."""
        if self._config is None:
            raise ConfigurationError("Configuration not initialized")
        return self._config.list_config()

    def export_to_file(self, file_path: str) -> None:
        """Export configuration to a file."""
        if self._config is None:
            raise ConfigurationError("Configuration not initialized")
        self._config.export_config(file_path)

    def import_from_file(self, file_path: str) -> None:
        """Import configuration from a file."""
        if self._config is None:
            raise ConfigurationError("Configuration not initialized")
        self._config.import_config(file_path)

    @property
    def is_initialized(self) -> bool:
        """Check if the configuration service is initialized."""
        return self._config is not None
