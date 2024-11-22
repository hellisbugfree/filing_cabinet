"""File service for the filing cabinet."""
from typing import List, Optional, Dict, Any
import os
import shutil
import json
import logging
from ..models.file import File
from ..repositories.file_repository import FileRepository
from ..config import get_config
from .document_processor import DocumentProcessor

# Set up logging
logger = logging.getLogger(__name__)

class FileService:
    """Service for managing files."""
    
    def __init__(self, db_path: str):
        """Initialize FileService with database path."""
        self.file_repo = FileRepository(db_path)
        self.config = get_config(db_path)
        self.processor = DocumentProcessor(self.config)
        logger.debug("FileService initialized")
        
    def __del__(self):
        """Clean up database connections."""
        if hasattr(self, 'file_repo'):
            self.file_repo.close()
            
    def add_file(self, path: str) -> Dict[str, Any]:
        """Add a file or directory to the filing cabinet."""
        processed = 0
        skipped = 0
        
        if os.path.isfile(path):
            if not self.should_ignore(path):
                self.process_file(path)
                processed += 1
            else:
                skipped += 1
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if not self.should_ignore(file_path):
                        self.process_file(file_path)
                        processed += 1
                    else:
                        skipped += 1
                        
        return {
            "processed": processed,
            "skipped": skipped
        }
            
    def process_file(self, file_path: str, extract_content: bool = False) -> Dict[str, Any]:
        """Process a file and store its metadata."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file = File(file_path)
        self.file_repo.save(file)
        
        # Process the file and extract information
        result = self.processor.process(file_path)
        
        # Create the metadata file for testing/development
        meta_file_path = f"{file_path}.filing_meta_data"
        with open(meta_file_path, 'w') as f:
            json.dump(result, f, indent=4)
            
        return result
        
    def index_files(self, directory: str) -> Dict[str, Any]:
        """Index files in a directory."""
        processed = 0
        skipped = 0
        
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if not self.should_ignore(file_path):
                    self.file_repo.index_file(file_path)
                    processed += 1
                else:
                    skipped += 1
                    
        return {
            "processed": processed,
            "skipped": skipped
        }
        
    def export_file(self, checksum: str, output_path: Optional[str] = None) -> str:
        """Export a file to the filesystem."""
        file = self.file_repo.get_by_checksum(checksum)
        if not file:
            raise FileNotFoundError(f"No file found with checksum: {checksum}")
            
        if not output_path:
            output_path = os.path.join(os.getcwd(), file.name)
            
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Copy the file
        shutil.copy2(file.path, output_path)
        return output_path
        
    def analyze(self, file_path: str) -> Dict[str, Any]:
        """Analyze a file using AI to extract insights and metadata."""
        file = File(file_path)
        
        # First ensure the file is in our system
        self.file_repo.index_file(file_path)
        
        # Here we would normally do AI analysis
        # For now, just return basic file info
        return {
            "name": file.name,
            "size": file.size,
            "mime_type": file.mime_type,
            "checksum": file.checksum
        }
        
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a file."""
        file = self.file_repo.get_by_id(file_id)
        if file:
            return file.to_dict()
        return None
        
    def remove_file(self, file_id: str) -> bool:
        """Remove a file from the filing cabinet."""
        return self.file_repo.delete(file_id)
        
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for files in the filing cabinet."""
        files = self.file_repo.search(query)
        return [file.to_dict() for file in files]
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the filing cabinet."""
        stats = self.file_repo.get_statistics()
        return {
            "total_files": stats["total_files"],
            "total_size": stats["total_size"],
            "database_path": self.file_repo.db_path
        }
        
    @staticmethod
    def should_ignore(file_path: str) -> bool:
        """Check if file should be ignored based on patterns."""
        ignore_patterns = [
            '.git',
            '__pycache__',
            '.pytest_cache',
            '.DS_Store',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.Python',
            'build',
            'develop-eggs',
            'dist',
            'downloads',
            'eggs',
            '.eggs',
            'lib',
            'lib64',
            'parts',
            'sdist',
            'var',
            'wheels',
            '*.egg-info',
            '.installed.cfg',
            '*.egg',
            '.env',
            '.venv',
            'env',
            'venv',
            'ENV',
            '.idea',
            '.vscode'
        ]
        
        for pattern in ignore_patterns:
            if pattern in file_path:
                return True
        return False
