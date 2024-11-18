from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import hashlib
import os

@dataclass
class File:
    """Represents a file in the filing cabinet system."""
    checksum: str
    name: str
    size: int
    content: bytes
    url: Optional[str] = None
    filed_timestamp: Optional[datetime] = None
    last_update_timestamp: Optional[datetime] = None

    @classmethod
    def from_path(cls, file_path: str) -> 'File':
        """Create a File instance from a file path."""
        with open(file_path, 'rb') as f:
            content = f.read()
            return cls(
                checksum=hashlib.md5(content).hexdigest(),
                name=os.path.basename(file_path),
                size=os.path.getsize(file_path),
                content=content,
                url=file_path,
                filed_timestamp=datetime.now(),
                last_update_timestamp=datetime.now()
            )

    def save_to(self, output_path: str) -> str:
        """Save the file content to the specified path."""
        full_path = os.path.join(output_path, self.name)
        with open(full_path, 'wb') as f:
            f.write(self.content)
        return full_path

    def update_timestamp(self) -> None:
        """Update the last update timestamp."""
        self.last_update_timestamp = datetime.now()

    @property
    def is_filed(self) -> bool:
        """Check if the file has been filed in the system."""
        return self.filed_timestamp is not None
