"""Configuration module for the filing cabinet."""
import os
from typing import Dict, Any

def get_config(db_path: str = None) -> Dict[str, Any]:
    """Get configuration settings."""
    if db_path is None:
        db_path = os.path.join(os.path.expanduser("~"), ".filing_cabinet.db")
    
    return {
        'database.path': db_path,
        'file.index.extensions': ['.txt', '.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'],
        'indexing.recursive': True,
        'indexing.follow_symlinks': False,
        'file.checkin.max_size': 100 * 1024 * 1024  # 100MB
    }