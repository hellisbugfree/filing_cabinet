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

    def process_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Process a file to extract metadata and content."""
        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist")
            return None
        
        mime_type = magic.Magic(mime=True).from_file(file_path)
        
        if mime_type not in self.supported_mime_types:
            print(f"Unsupported file type: {mime_type}")
            return None

        try:
            # Basic metadata
            metadata = self._get_file_metadata(file_path)
            metadata.update({
                "file_name": os.path.basename(file_path),
                "file_size": os.path.getsize(file_path),
                "mime_type": mime_type,
                "content": {
                    "text": "",
                    "tables": [],
                    "key_value_pairs": {},
                    "entities": {
                        "people": [],
                        "organizations": [],
                        "dates": [],
                        "amounts": []
                    }
                }
            })
            
            # Process based on file type
            if mime_type.startswith('image/'):
                metadata = self._process_image(file_path, metadata)
            elif mime_type == 'application/pdf':
                metadata = self._process_pdf(file_path, metadata)
            
            # Extract entities from the text
            if metadata["content"]["text"]:
                metadata = self._extract_entities(metadata)
            
            return metadata
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            return None

    def _get_file_metadata(self, file_path: str) -> Dict[str, Any]:
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
        metadata["content"]["text"] = pytesseract.image_to_string(
            image,
            lang=('deu' if lang == 'de' else 'eng'),
            config='--psm 6'
        )
        
        return metadata

    def _process_pdf(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a PDF file."""
        pdf = PdfReader(file_path)
        
        # PDF metadata
        metadata["pdf_metadata"] = pdf.metadata if pdf.metadata else {}
        
        # Try direct text extraction first
        all_text = []
        tables = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # Extract text
                text = page.extract_text()
                if text and text.strip():
                    all_text.append(text)
                
                # Extract tables
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend([
                        {
                            "page": page.page_number,
                            "data": table
                        }
                        for table in page_tables
                    ])
        
        # If no text was extracted, try OCR
        if not all_text:
            pdf_images = convert_from_path(file_path)
            for page_num, image in enumerate(pdf_images, 1):
                # Detect language
                sample_text = pytesseract.image_to_string(image)
                lang = self._detect_language(sample_text)
                
                # Perform OCR with detected language
                text = pytesseract.image_to_string(
                    image,
                    lang=('deu' if lang == 'de' else 'eng'),
                    config='--psm 6'
                )
                if text.strip():
                    all_text.append(f"Page {page_num}:\n{text}")
        
        metadata["content"]["text"] = "\n\n".join(all_text)
        metadata["content"]["tables"] = tables
        
        return metadata

    def _detect_language(self, text: str) -> str:
        """Detect text language."""
        try:
            return langdetect.detect(text)
        except:
            return 'en'  # Default to English

    def _extract_entities(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entities from text."""
        text = metadata["content"]["text"]
        
        # Extract dates (various formats)
        date_patterns = [
            r'\d{2}[./-]\d{2}[./-]\d{4}',  # DD.MM.YYYY, DD/MM/YYYY
            r'\d{4}[./-]\d{2}[./-]\d{2}',  # YYYY.MM.DD, YYYY/MM/DD
            r'\d{1,2}\.\s+[A-Za-zäöüÄÖÜß]+\s+\d{4}'  # DD. Month YYYY
        ]
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text))
        metadata["content"]["entities"]["dates"] = list(set(dates))
        
        # Extract amounts (currency values)
        amount_patterns = [
            r'\$\s*\d+(?:\.\d{2})?',  # USD
            r'€\s*\d+(?:,\d{2})?',    # EUR
            r'\d+(?:,\d{2})?\s*€',    # EUR (amount first)
            r'\d+(?:\.\d{2})?\s*USD'  # USD (amount first)
        ]
        amounts = []
        for pattern in amount_patterns:
            amounts.extend(re.findall(pattern, text))
        metadata["content"]["entities"]["amounts"] = list(set(amounts))
        
        # Extract key-value pairs
        key_value_patterns = [
            (r'([A-Za-z\s-]+):\s*([^\n]+)', 1, 2),  # Key: Value
            (r'([A-Za-z\s-]+)\s*=\s*([^\n]+)', 1, 2),  # Key = Value
        ]
        for pattern, key_group, value_group in key_value_patterns:
            for match in re.finditer(pattern, text):
                key = match.group(key_group).strip()
                value = match.group(value_group).strip()
                if key and value:
                    metadata["content"]["key_value_pairs"][key] = value
        
        return metadata

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
