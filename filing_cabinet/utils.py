import uuid
import socket
import os
from datetime import datetime
from pathlib import Path

def get_device_identifier():
    """Get a unique identifier for the current device."""
    try:
        # Try to get the MAC address of the first network interface
        mac = uuid.getnode()
        hostname = socket.gethostname()
        return f"{hostname}-{mac:012x}"
    except:
        # Fallback to hostname if MAC address is not available
        return socket.gethostname()

def get_file_type(file_path):
    """Determine if a file is a physical file or symlink."""
    path = Path(file_path)
    if path.is_symlink():
        return 'symlink', str(path.resolve())
    return 'file', None

def get_absolute_path(file_path):
    """Convert a file path to its absolute form."""
    return str(Path(file_path).resolve())
