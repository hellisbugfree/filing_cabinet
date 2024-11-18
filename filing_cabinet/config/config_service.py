from typing import Any, Dict, Optional
from .configuration import Configuration, ConfigurationError
from ..utils import logger

class ConfigService:
    """Service for managing application configuration."""
    
    # Default configuration values
    DEFAULT_CONFIG = {
        'cabinet.name': ('Filing Cabinet', 'Name of the filing cabinet'),
        'database.schema.version': ('1.0.0', 'Database schema version'),
        'file.index.extensions': (['.txt', '.pdf', '.doc', '.docx'], 'List of file extensions to index'),
        'file.checkin.max_size': (100 * 1024 * 1024, 'Maximum file size in bytes (100MB)'),
        'storage.compression': ('none', 'Storage compression method'),
        'storage.encryption': ('none', 'Storage encryption method'),
        'indexing.recursive': (True, 'Whether to recursively index subdirectories'),
        'indexing.follow_symlinks': (False, 'Whether to follow symbolic links during indexing'),
        'indexing.ignore_patterns': (['.git/*', '*.pyc', '__pycache__/*'], 'Patterns to ignore during indexing')
    }
    
    _instance = None
    
    def __new__(cls, db_path: str):
        """Create or return singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = None
            cls._instance._db_path = db_path
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """Initialize configuration."""
        try:
            self._config = Configuration(self._db_path)
            self._ensure_defaults()
        except Exception as e:
            logger.error(f"Failed to initialize configuration: {e}")
            raise ConfigurationError(f"Failed to initialize configuration: {e}")
    
    def _ensure_defaults(self) -> None:
        """Ensure default configuration values exist."""
        try:
            for key, (value, description) in self.DEFAULT_CONFIG.items():
                try:
                    self._config.get_config(key)
                except ConfigurationError:
                    self._config.create_config(key, value, value, description)
                    logger.debug(f"Created default configuration: {key} = {value}")
        except Exception as e:
            logger.error(f"Failed to ensure default configuration: {e}")
            raise ConfigurationError(f"Failed to ensure default configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        if self._config is None:
            raise ConfigurationError("Configuration not initialized")
        try:
            return self._config.get_config(key, default)
        except Exception as e:
            logger.error(f"Failed to get configuration {key}: {e}")
            raise ConfigurationError(f"Failed to get configuration: {e}")
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        if self._config is None:
            raise ConfigurationError("Configuration not initialized")
        try:
            self._config.put_config(key, value)
            logger.info(f"Updated configuration: {key} = {value}")
        except Exception as e:
            logger.error(f"Failed to set configuration {key}: {e}")
            raise ConfigurationError(f"Failed to set configuration: {e}")
    
    def create(self, key: str, value: Any, default: Any = None, description: str = '') -> None:
        """Create new configuration entry."""
        if self._config is None:
            raise ConfigurationError("Configuration not initialized")
        try:
            self._config.create_config(key, value, default, description)
            logger.info(f"Created configuration: {key} = {value} (default: {default})")
        except Exception as e:
            logger.error(f"Failed to create configuration {key}: {e}")
            raise ConfigurationError(f"Failed to create configuration: {e}")
    
    def reset(self, key: str) -> None:
        """Reset configuration to default value."""
        if self._config is None:
            raise ConfigurationError("Configuration not initialized")
        try:
            self._config.reset_config(key)
            logger.info(f"Reset configuration: {key}")
        except Exception as e:
            logger.error(f"Failed to reset configuration {key}: {e}")
            raise ConfigurationError(f"Failed to reset configuration: {e}")
    
    def list_all(self) -> Dict[str, Dict[str, Any]]:
        """List all configuration values."""
        if self._config is None:
            raise ConfigurationError("Configuration not initialized")
        try:
            return self._config.list_config()
        except Exception as e:
            logger.error(f"Failed to list configuration: {e}")
            raise ConfigurationError(f"Failed to list configuration: {e}")
    
    def export_to_file(self, file_path: str) -> None:
        """Export configuration to file."""
        if self._config is None:
            raise ConfigurationError("Configuration not initialized")
        try:
            self._config.export_config(file_path)
            logger.info(f"Exported configuration to {file_path}")
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            raise ConfigurationError(f"Failed to export configuration: {e}")
    
    def import_from_file(self, file_path: str) -> None:
        """Import configuration from file."""
        if self._config is None:
            raise ConfigurationError("Configuration not initialized")
        try:
            self._config.import_config(file_path)
            logger.info(f"Imported configuration from {file_path}")
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            raise ConfigurationError(f"Failed to import configuration: {e}")
    
    def close(self) -> None:
        """Close configuration service."""
        if self._config is not None:
            self._config.close()
            self._config = None
            
    @property
    def is_initialized(self) -> bool:
        """Check if the configuration service is initialized."""
        return self._config is not None
