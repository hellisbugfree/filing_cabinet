from typing import List, Optional, Tuple, Dict, Any
from ..models.file import File
from ..models.incarnation import Incarnation
from ..repositories.file_repository import FileRepository
from ..repositories.incarnation_repository import IncarnationRepository
from ..config import get_config
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

class FileService:
    """Service for managing files and their incarnations."""

    def __init__(self, db_path: str):
        """Initialize FileService with database path."""
        self.file_repo = FileRepository(db_path)
        self.incarnation_repo = IncarnationRepository(db_path)
        self.file_repo.connect()
        self.incarnation_repo.connect()
        self.config = get_config(db_path)
        logger.debug("FileService initialized")

    def __del__(self):
        """Clean up database connections."""
        self.file_repo.close()
        self.incarnation_repo.close()
        logger.debug("FileService connections closed")

    def checkin_file(self, file_path: str) -> str:
        """Check in a file to the filing cabinet."""
        logger.info(f"Checking in file: {file_path}")
        try:
            # Check file size limit
            max_size = self.config.get('file.checkin.max_size')
            if os.path.getsize(file_path) > max_size:
                logger.error(f"File size exceeds maximum allowed size of {max_size:,} bytes")
                raise ValueError(f"File size exceeds maximum allowed size of {max_size:,} bytes")
            
            # Create File instance
            file = File.from_path(file_path)
            
            # Check if file already exists
            existing_file = self.file_repo.get(file.checksum)
            if not existing_file:
                self.file_repo.add(file)
                logger.debug(f"Added new file: {file_path}")
            
            # Create and save incarnation
            incarnation = Incarnation.from_file_path(file_path, file.checksum)
            self.incarnation_repo.add(incarnation)
            logger.debug(f"Added new incarnation: {file_path}")
            
            return file.checksum
        except Exception as e:
            logger.error(f"Failed to check in file {file_path}: {e}")
            raise

    def checkout_file(self, checksum: str, output_path: str) -> Optional[str]:
        """Check out a file from the filing cabinet."""
        logger.info(f"Checking out file with checksum: {checksum}")
        try:
            file = self.file_repo.get(checksum)
            if not file:
                logger.error(f"File not found with checksum: {checksum}")
                return None
            
            return file.save_to(output_path)
        except Exception as e:
            logger.error(f"Failed to check out file with checksum {checksum}: {e}")
            raise

    def get_file_info(self, file_path: str) -> tuple[Optional[File], List[Incarnation]]:
        """Get detailed information about a file and its incarnations."""
        logger.info(f"Getting file info for: {file_path}")
        try:
            # Create temporary file instance to get checksum
            temp_file = File.from_path(file_path)
            
            # Get file and its incarnations
            file = self.file_repo.get(temp_file.checksum)
            incarnations = self.incarnation_repo.get_incarnations_by_checksum(temp_file.checksum)
            
            return file, incarnations
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            raise

    def index_files(self, path: str) -> List[str]:
        """
        Index files in the given path. Adds new paths to file_incarnation table.
        Returns list of newly added paths.
        """
        logger.info(f"Indexing files in path: {path}")
        results = []
        
        try:
            # Get configuration values
            allowed_extensions = self.config.get('file.index.extensions')
            recursive = self.config.get('indexing.recursive')
            follow_symlinks = self.config.get('indexing.follow_symlinks')
            ignore_patterns = self.config.get('indexing.ignore_patterns')
            
            def should_ignore(file_path: str) -> bool:
                """Check if file should be ignored based on patterns."""
                from fnmatch import fnmatch
                return any(fnmatch(file_path, pattern) for pattern in ignore_patterns)
            
            def process_file(file_path: str) -> None:
                """Process a single file."""
                if should_ignore(file_path):
                    return
                    
                _, ext = os.path.splitext(file_path)
                if ext.lower() not in allowed_extensions:
                    return
                    
                # Create incarnation and check if this path exists
                file = File.from_path(file_path)  # Just to get checksum
                incarnation = Incarnation.from_file_path(file_path, file.checksum)
                
                if not self.incarnation_repo.get(incarnation.incarnation_url):
                    self.incarnation_repo.add(incarnation)
                    logger.debug(f"Added new incarnation: {file_path}")
                    results.append(file_path)
            
            # Walk through directory if recursive
            if recursive:
                for root, _, files in os.walk(path, followlinks=follow_symlinks):
                    for file in files:
                        process_file(os.path.join(root, file))
            else:
                # Only process files in the given directory
                if os.path.isfile(path):
                    process_file(path)
                else:
                    for entry in os.scandir(path):
                        if entry.is_file(follow_symlinks=follow_symlinks):
                            process_file(entry.path)
            
            logger.info(f"Indexed {len(results)} files")
            return results
        except Exception as e:
            logger.error(f"Failed to index path {path}: {e}")
            raise

    def get_statistics(self) -> dict:
        """Get statistics about the filing cabinet."""
        logger.info("Getting filing cabinet statistics")
        try:
            cabinet_name = self.config.get('cabinet.name')
            schema_version = self.config.get('database.schema.version')
            
            return {
                'name': cabinet_name,
                'version': schema_version,
                'total_files': self.file_repo.get_file_count(),
                'total_incarnations': self.incarnation_repo.get_incarnation_count()
            }
        except Exception as e:
            logger.error(f"Failed to get filing cabinet statistics: {e}")
            raise
