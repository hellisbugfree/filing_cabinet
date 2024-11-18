from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from ..utils import get_device_identifier, get_file_type, get_absolute_path

@dataclass
class Incarnation:
    """Represents a specific instance or copy of a file in the system."""
    incarnation_url: str
    file_checksum: str
    incarnation_device: str
    incarnation_type: str
    last_update_timestamp: datetime
    forward_url: Optional[str] = None

    @classmethod
    def from_file_path(cls, file_path: str, file_checksum: str) -> 'Incarnation':
        """Create an Incarnation instance from a file path and checksum."""
        abs_path = get_absolute_path(file_path)
        device_id = get_device_identifier()
        file_type, forward_url = get_file_type(file_path)
        
        return cls(
            incarnation_url=abs_path,
            file_checksum=file_checksum,
            incarnation_device=device_id,
            incarnation_type=file_type,
            forward_url=forward_url,
            last_update_timestamp=datetime.now()
        )

    def update_timestamp(self) -> None:
        """Update the last update timestamp."""
        self.last_update_timestamp = datetime.now()

    @property
    def is_symlink(self) -> bool:
        """Check if this incarnation is a symbolic link."""
        return self.incarnation_type == 'symlink'

    @property
    def is_hardlink(self) -> bool:
        """Check if this incarnation is a hard link."""
        return self.incarnation_type == 'hardlink'
