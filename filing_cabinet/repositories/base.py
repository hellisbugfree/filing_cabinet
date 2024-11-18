from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Any

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Base repository interface defining common operations."""
    
    @abstractmethod
    def get(self, id: str) -> Optional[T]:
        """Retrieve an entity by its ID."""
        pass
    
    @abstractmethod
    def add(self, entity: T) -> None:
        """Add a new entity to the repository."""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> None:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    def delete(self, id: str) -> None:
        """Delete an entity by its ID."""
        pass
    
    @abstractmethod
    def list(self, **filters: Any) -> List[T]:
        """List all entities matching the given filters."""
        pass
