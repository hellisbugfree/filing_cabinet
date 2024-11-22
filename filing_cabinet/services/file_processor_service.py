import os
import json
import stat
from datetime import datetime
from PIL import Image
import pytesseract
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import magic
from typing import Dict, Any, Optional, List
import re
from pathlib import Path
import langdetect
import tabula
import pdfplumber
from importlib.metadata import version, PackageNotFoundError
from .document_template_service import DocumentTemplateService
from ..config import get_config
from ..errors import (
    FilingError, FileNotFoundError, UnsupportedFileTypeError,
    ProcessingError, ConfigurationError, AIServiceError
)
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class FileProcessorService:
    def __init__(self, db_path: str):
        """Initialize the file processor service."""
        self.db_path = db_path
        self.supported_mime_types = {
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/tiff'
        }
        self.template_service = DocumentTemplateService()
        self.config = get_config(db_path)
        self.openai_client = None
        
        # Try to initialize OpenAI client, but don't fail if key is missing
        try:
            api_key = self.config.get('openai.api_key', None)
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.debug("OpenAI client initialized successfully")
            else:
                logger.debug("OpenAI API key not found. AI-powered features will be disabled.")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}. AI-powered features will be disabled.")

    def process_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Process a file to extract metadata and content."""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(file_path)

            # Get file mime type
            mime_type = magic.from_file(file_path, mime=True)
            if mime_type not in self.supported_mime_types:
                raise UnsupportedFileTypeError(mime_type)

            # Extract basic file metadata
            metadata = self._extract_basic_metadata(file_path)
            
            # Initialize content structure if not present
            if 'content' not in metadata:
                metadata['content'] = {
                    'text': '',
                    'tables': [],
                    'key_value_pairs': {},
                    'entities': {
                        'people': [],
                        'organizations': [],
                        'dates': [],
                        'amounts': []
                    },
                    'relationships': [],
                    'context': {}
                }
            
            # Initialize document info if not present
            if 'document_info' not in metadata:
                metadata['document_info'] = {
                    'type': 'unknown',
                    'purpose': ''
                }

            # Process based on file type
            if mime_type == 'application/pdf':
                self._process_pdf(file_path, metadata)
            else:
                self._process_image(file_path, metadata)

            # Try AI-powered extraction if available
            if self.openai_client:
                try:
                    enhanced_metadata = self.template_service.process_with_ai(
                        metadata['content']['text'],
                        metadata
                    )
                    metadata = enhanced_metadata  # Update with AI results or fallback
                except Exception as e:
                    logger.warning(f"OpenAI extraction failed: {str(e)}. Falling back to traditional methods.")
                    if 'processing' not in metadata:
                        metadata['processing'] = {
                            'method': 'traditional',
                            'fallback_reason': {
                                'error_type': type(e).__name__,
                                'error_message': str(e)
                            },
                            'timestamp': datetime.now().isoformat()
                        }
            else:
                metadata['processing'] = {
                    'method': 'traditional',
                    'reason': 'OpenAI client not configured',
                    'timestamp': datetime.now().isoformat()
                }

            # Ensure we have at least basic entity extraction
            if not any(metadata['content']['entities'].values()):
                self._extract_entities(metadata)

            # Save the processing method in metadata
            self.save_metadata(file_path, metadata)
            return metadata

        except FilingError:
            raise
        except Exception as e:
            raise ProcessingError(f"Failed to process file: {str(e)}", original_error=e)

    def _extract_basic_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get file system metadata."""
        stat_info = os.stat(file_path)
        import hashlib
        import platform
        import uuid
        import socket

        # Get package version
        try:
            pkg_version = version('filing-cabinet')
        except PackageNotFoundError:
            pkg_version = "0.1.0"  # Default version if package is not installed

        # Calculate file checksum
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        # Get device information
        device_info = {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "platform_machine": platform.machine(),
            "device_id": str(uuid.UUID(int=uuid.getnode()))
        }

        return {
            "filing_cabinet": {
                "checksum": sha256_hash.hexdigest(),
                "processed_at": datetime.now().isoformat(),
                "version": pkg_version
            },
            "device_data": {
                "created_at": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "accessed_at": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
                "permissions": stat.filemode(stat_info.st_mode),
                "device_info": device_info
            }
        }

    def _process_image(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process an image file."""
        image = Image.open(file_path)
        
        # Image metadata
        metadata["image_metadata"] = {
            "format": image.format,
            "mode": image.mode,
            "size": image.size,
            "dpi": image.info.get('dpi'),
            "exif": {k: str(v) for k, v in image.getexif().items()} if hasattr(image, 'getexif') else {}
        }
        
        # Detect language and perform OCR
        sample_text = pytesseract.image_to_string(image)
        lang = self._detect_language(sample_text)
        
        # Perform OCR with detected language
        metadata["content"] = {
            "text": pytesseract.image_to_string(
                image,
                lang=('deu' if lang == 'de' else 'eng'),
                config='--psm 6'
            ),
            "tables": [],
            "key_value_pairs": {},
            "entities": {
                "people": [],
                "organizations": [],
                "dates": [],
                "amounts": []
            },
            "relationships": [],
            "context": {}
        }
        
        return metadata

    def _process_pdf(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a PDF file."""
        # First get basic PDF metadata
        pdf = PdfReader(file_path)
        pdf_metadata = pdf.metadata if pdf.metadata else {}
        metadata["pdf_metadata"] = pdf_metadata

        # Extract metadata using template-based processing
        template_results = self.template_service.process_document(file_path)
        
        if "error" not in template_results:
            metadata.update({
                "document_info": {
                    "type": template_results["document_type"],
                    "confidence": template_results["confidence"],
                    "purpose": template_results["metadata"].get("purpose", ""),
                    "filing_relevance": template_results["metadata"].get("filing_relevance", {})
                }
            })

            # Extract content from template results
            content_text = []
            content_tables = []
            
            for zone_name, zone_data in template_results["zones"].items():
                if zone_data.get("text"):
                    content_text.append(f"[{zone_name}]\n{zone_data['text']}")
                if zone_data.get("tables"):
                    content_tables.extend(zone_data["tables"])

            metadata["content"] = {
                "text": "\n\n".join(content_text),
                "tables": content_tables,
                "key_value_pairs": template_results["metadata"].get("key_value_pairs", {}),
                "entities": template_results["metadata"].get("entities", {
                    "people": [],
                    "organizations": [],
                    "dates": [],
                    "amounts": []
                }),
                "relationships": template_results["metadata"].get("relationships", []),
                "context": template_results["metadata"].get("context", {})
            }

            # Extract additional entities from the text content
            metadata = self._extract_entities(metadata)
        else:
            # Fallback to basic processing if template matching fails
            with pdfplumber.open(file_path) as pdf:
                text_content = []
                tables = []
                
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                    
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table in page_tables:
                            if table and any(row and any(cell for cell in row) for row in table):
                                tables.append({
                                    "headers": table[0] if table else [],
                                    "data": table[1:] if table and len(table) > 1 else []
                                })
                
                metadata["content"] = {
                    "text": "\n\n".join(text_content),
                    "tables": tables,
                    "key_value_pairs": {},
                    "entities": {
                        "people": [],
                        "organizations": [],
                        "dates": [],
                        "amounts": []
                    },
                    "relationships": [],
                    "context": {}
                }
                
                # Basic metadata extraction
                metadata = self._extract_entities(metadata)

        return metadata

    def _extract_entities(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entities from text using traditional methods."""
        text = metadata["content"]["text"]
        if not text:
            return metadata

        # Extract dates using regex
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}\.\d{2}\.\d{4}',  # DD.MM.YYYY
            r'\d{2}/\d{2}/\d{4}'   # DD/MM/YYYY
        ]
        
        for pattern in date_patterns:
            metadata["content"]["entities"]["dates"].extend(
                [match.group() for match in re.finditer(pattern, text)]
            )

        # Extract amounts using regex
        amount_patterns = [
            r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # USD
            r'€\s*\d+(?:,\d{3})*(?:\.\d{2})?',   # EUR
            r'\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:EUR|USD|€|\$)'  # Amount followed by currency
        ]
        
        for pattern in amount_patterns:
            metadata["content"]["entities"]["amounts"].extend(
                [match.group() for match in re.finditer(pattern, text)]
            )

        return metadata

    def _detect_language(self, text: str) -> str:
        """Detect text language."""
        try:
            return langdetect.detect(text)
        except:
            return 'en'  # Default to English

    def save_metadata(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """Save metadata to a file."""
        output_path = f"{file_path}.filing_meta_data"
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving metadata: {str(e)}")
            return False
