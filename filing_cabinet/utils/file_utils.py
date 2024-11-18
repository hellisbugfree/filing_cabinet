"""File-related utility functions."""
import os
import platform
import uuid
from pathlib import Path
from typing import Optional, Tuple

def get_device_identifier() -> str:
    """Get a unique identifier for the current device."""
    # Try to get a stable machine ID
    try:
        if platform.system() == 'Darwin':
            # On macOS, use system_profiler
            import subprocess
            result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                 capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'Hardware UUID' in line:
                    return line.split(':')[1].strip()
    except Exception:
        pass
    
    # Fallback to a random UUID that persists for this session
    return str(uuid.uuid4())

def get_file_type(file_path: str) -> Tuple[str, Optional[str]]:
    """
    Get the type of file based on extension and content.
    
    Returns:
        Tuple of (file_type, forward_url). forward_url is only set for symlinks.
    """
    path = Path(file_path)
    
    # Check if it's a symlink
    if path.is_symlink():
        return 'symlink', str(path.resolve())
    
    # Check if it's a hardlink
    try:
        stat = path.stat()
        if stat.st_nlink > 1:
            return 'hardlink', None
    except Exception:
        pass
    
    # Default to extension-based type
    _, ext = os.path.splitext(file_path)
    return ext.lower() if ext else '', None

def get_absolute_path(path: str) -> str:
    """Convert path to absolute path, resolving any symlinks."""
    return str(Path(path).resolve())
