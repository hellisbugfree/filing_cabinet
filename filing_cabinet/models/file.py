"""File model for the filing cabinet."""
import os
import hashlib
from typing import Dict, Any

class File:
    """Represents a file in the filing cabinet."""

    def __init__(self, file_path: str):
        """Initialize a file from a path."""
        self.path = os.path.abspath(file_path)
        self.name = os.path.basename(file_path)
        self.size = os.path.getsize(file_path)
        self.checksum = self._calculate_checksum()
        self.mime_type = self._get_mime_type()

    def _calculate_checksum(self) -> str:
        """Calculate SHA-256 checksum of the file."""
        sha256_hash = hashlib.sha256()
        with open(self.path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _get_mime_type(self) -> str:
        """Get the MIME type of the file."""
        import magic
        return magic.from_file(self.path, mime=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert file to dictionary representation."""
        return {
            "path": self.path,
            "name": self.name,
            "size": self.size,
            "checksum": self.checksum,
            "mime_type": self.mime_type
        }
