import os
from typing import Optional
from .config_service import ConfigService
from .configuration import ConfigurationError

def get_config(db_path: Optional[str] = None) -> ConfigService:
    """
    Get the configuration service instance.
    
    Args:
        db_path: Optional database path. If not provided, uses default path.
        
    Returns:
        ConfigService instance
    """
    if db_path is None:
        db_path = os.path.expanduser('~/filing.cabinet')
    
    return ConfigService(db_path)
