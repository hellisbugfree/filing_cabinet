import os
from typing import Optional
from .config_service import ConfigService
from .configuration import ConfigurationError

def initialize_config(db_path: Optional[str] = None) -> ConfigService:
    """
    Initialize the configuration service.
    
    Args:
        db_path: Optional database path. If not provided, uses default path.
        
    Returns:
        Initialized ConfigService instance
    """
    if db_path is None:
        db_path = os.path.expanduser('~/filing.cabinet')
    
    # Create and initialize the service
    service = ConfigService(db_path)
    if not service.is_initialized:
        service.initialize(db_path)
    
    return service

def get_config() -> ConfigService:
    """
    Get the configuration service instance.
    
    Returns:
        ConfigService instance
        
    Raises:
        ConfigurationError: If configuration service is not initialized
    """
    return ConfigService.get_instance()
