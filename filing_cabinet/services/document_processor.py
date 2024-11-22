"""Document processor for extracting information from files."""
import os
import json
import platform
import uuid
from datetime import datetime
import PyPDF2
from typing import Dict, Any, List, Optional

class DocumentProcessor:
    """Processor for extracting information from documents."""
    
    def __init__(self, config):
        """Initialize with configuration."""
        self.config = config
        self._device_id = str(uuid.uuid4())
        
    def process(self, file_path: str) -> Dict[str, Any]:
        """Process a document and extract information."""
        try:
            # First try AI processing
            return self._process_with_ai(file_path)
        except Exception as e:
            # Fallback to traditional processing
            return self._process_traditional(file_path, fallback_error=e)
    
    def _process_with_ai(self, file_path: str) -> Dict[str, Any]:
        """Process document using AI."""
        api_key = self.config.get('openai.api_key')
        if not api_key:
            raise ValueError("OpenAI API key not configured")
            
        # TODO: Implement OpenAI processing
        raise NotImplementedError("AI processing not implemented yet")
    
    def _process_traditional(self, file_path: str, fallback_error: Optional[Exception] = None) -> Dict[str, Any]:
        """Process document using traditional methods."""
        result = {
            "filing_cabinet": {
                "checksum": self._calculate_checksum(file_path),
                "processed_at": datetime.now().isoformat(),
                "version": "0.3.3"  # TODO: Get from package version
            },
            "device_data": self._get_device_data(file_path),
            "content": self._extract_content(file_path),
            "document_info": {
                "type": "unknown",
                "purpose": ""
            },
            "pdf_metadata": self._extract_pdf_metadata(file_path),
            "processing": {
                "method": "traditional",
                "fallback_reason": self._format_error(fallback_error) if fallback_error else None,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        return result
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate file checksum."""
        import hashlib
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _get_device_data(self, file_path: str) -> Dict[str, Any]:
        """Get device and file information."""
        stat = os.stat(file_path)
        return {
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "accessed_at": datetime.fromtimestamp(stat.st_atime).isoformat(),
            "permissions": oct(stat.st_mode)[-3:],
            "device_info": {
                "hostname": platform.node(),
                "platform": platform.system(),
                "platform_version": platform.version(),
                "platform_machine": platform.machine(),
                "device_id": self._device_id
            }
        }
    
    def _extract_content(self, file_path: str) -> Dict[str, Any]:
        """Extract content from file."""
        if file_path.lower().endswith('.pdf'):
            return self._extract_pdf_content(file_path)
        else:
            return self._extract_text_content(file_path)
    
    def _extract_pdf_content(self, file_path: str) -> Dict[str, Any]:
        """Extract content from PDF file."""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            text = f"Failed to extract PDF text: {str(e)}"
        
        return {
            "text": text.strip(),
            "tables": [],
            "key_value_pairs": {},
            "entities": self._extract_entities(text),
            "relationships": [],
            "context": {}
        }
    
    def _extract_text_content(self, file_path: str) -> Dict[str, Any]:
        """Extract content from text file."""
        try:
            with open(file_path, 'r') as file:
                text = file.read()
        except Exception:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
            except Exception as e:
                text = f"Failed to extract text: {str(e)}"
        
        return {
            "text": text.strip(),
            "tables": [],
            "key_value_pairs": {},
            "entities": self._extract_entities(text),
            "relationships": [],
            "context": {}
        }
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text."""
        import re
        
        entities = {
            "people": [],
            "organizations": [],
            "dates": [],
            "amounts": []
        }
        
        # Simple date extraction (YYYY-MM-DD format)
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        entities["dates"] = re.findall(date_pattern, text)
        
        # Simple amount extraction ($ format)
        amount_pattern = r'\$\d+(?:\.\d{2})?(?:\s*(?:USD|EUR|GBP))?'
        entities["amounts"] = re.findall(amount_pattern, text)
        
        return entities
    
    def _extract_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract PDF metadata."""
        if not file_path.lower().endswith('.pdf'):
            return {}
            
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                return dict(reader.metadata or {})
        except Exception:
            return {}
    
    def _format_error(self, error: Exception) -> Dict[str, str]:
        """Format error information."""
        return {
            "error_type": error.__class__.__name__,
            "error_message": str(error)
        }
