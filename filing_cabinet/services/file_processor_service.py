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
        
        # PDF metadata with date standardization
        pdf_metadata = pdf.metadata if pdf.metadata else {}
        if "/CreationDate" in pdf_metadata:
            creation_date = pdf_metadata["/CreationDate"]
            if creation_date.startswith("D:"):
                # Convert D:YYYYMMDDHHmmSS to YYYY-MM-DD
                try:
                    date_str = creation_date[2:14]  # Extract YYYYMMDDHHSS
                    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    pdf_metadata["/CreationDate"] = formatted_date
                except:
                    pass
        
        metadata["pdf_metadata"] = pdf_metadata
        
        # Document structure for better organization
        document_structure = {
            "metadata": {
                "author": None,
                "company": None,
                "document_type": None,
                "dates": set(),
                "amounts": [],  # Changed from set() to []
                "account_info": {},
            },
            "content": {
                "text_blocks": [],
                "tables": [],
                "key_value_pairs": {}
            }
        }
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # Extract text
                text = page.extract_text()
                if text and text.strip():
                    # Process text blocks
                    text_blocks = self._process_text_blocks(text)
                    document_structure["content"]["text_blocks"].extend(text_blocks)
                    
                    # Extract document metadata
                    self._extract_document_info(text, document_structure["metadata"])
                    
                    # Extract account information
                    self._extract_account_info(text, document_structure["metadata"]["account_info"])
                
                # Extract and validate tables
                tables = page.extract_tables()
                if tables:
                    processed_tables = self._process_tables(tables, page.page_number)
                    if processed_tables:
                        document_structure["content"]["tables"].extend(processed_tables)
        
        # Update metadata with structured information
        metadata["content"].update({
            "text": "\n\n".join(block["text"] for block in document_structure["content"]["text_blocks"]),
            "tables": document_structure["content"]["tables"],
            "document_info": {
                "author": document_structure["metadata"]["author"],
                "company": document_structure["metadata"]["company"],
                "document_type": document_structure["metadata"]["document_type"],
                "dates": sorted(list(document_structure["metadata"]["dates"])),
                "amounts": document_structure["metadata"]["amounts"],  # Removed sorting since amounts are dictionaries
                "account_info": document_structure["metadata"]["account_info"]
            }
        })
        
        return metadata

    def _process_text_blocks(self, text: str) -> List[Dict[str, Any]]:
        """Process text into meaningful blocks."""
        blocks = []
        current_block = {"type": "text", "text": "", "level": 0}
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                if current_block["text"]:
                    blocks.append(current_block)
                    current_block = {"type": "text", "text": "", "level": 0}
                continue
            
            # Detect headers (all caps or numbered sections)
            if line.isupper() or re.match(r'^\d+\.?\s+[A-Z]', line):
                if current_block["text"]:
                    blocks.append(current_block)
                current_block = {"type": "header", "text": line, "level": 1}
                blocks.append(current_block)
                current_block = {"type": "text", "text": "", "level": 0}
            else:
                if current_block["text"]:
                    current_block["text"] += "\n"
                current_block["text"] += line
        
        if current_block["text"]:
            blocks.append(current_block)
        
        return blocks

    def _process_tables(self, tables: List[List[List[str]]], page_num: int) -> List[Dict[str, Any]]:
        """Process and validate tables."""
        processed_tables = []
        
        for table in tables:
            # Skip empty tables
            if not table or not any(row and any(cell for cell in row) for row in table):
                continue
            
            # Analyze table structure
            col_count = max(len(row) for row in table)
            if col_count <= 1:
                continue  # Skip single-column "tables" as they're likely text blocks
            
            # Clean and validate cells
            cleaned_rows = []
            for row in table:
                # Extend row if needed
                row = row + [""] * (col_count - len(row))
                # Clean cells
                cleaned_row = [cell.strip() if cell else "" for cell in row]
                # Only add rows that have content
                if any(cell for cell in cleaned_row):
                    cleaned_rows.append(cleaned_row)
            
            if cleaned_rows:
                # Try to identify header row
                header_row = cleaned_rows[0]
                data_rows = cleaned_rows[1:]
                
                # Check if it's a real table by analyzing data consistency
                if len(data_rows) > 0:
                    processed_tables.append({
                        "page": page_num,
                        "headers": header_row,
                        "data": data_rows
                    })
        
        return processed_tables

    def _extract_account_info(self, text: str, account_info: Dict[str, Any]) -> None:
        """Extract account-related information."""
        # IBAN pattern
        iban_match = re.search(r'[A-Z]{2}\d{2}\s*(?:\d{4}\s*){4,7}', text)
        if iban_match:
            account_info["iban"] = iban_match.group().replace(" ", "")
        
        # Account number pattern
        account_match = re.search(r'Konto(?:nummer)?[\s:]+(\d{8,10})', text)
        if account_match:
            account_info["account_number"] = account_match.group(1)
        
        # BIC pattern
        bic_match = re.search(r'BIC:?\s*([A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)', text)
        if bic_match:
            account_info["bic"] = bic_match.group(1)

    def _extract_document_info(self, text: str, info: Dict[str, Any]) -> None:
        """Extract document information from text."""
        # Enhanced company detection patterns
        company_patterns = [
            r'((?:[A-Z][A-Za-z\-]+\s+)+(?:AG|GmbH|Inc\.|Ltd\.|SE|KG|OHG|e\.V\.|S\.A\.|N\.V\.|Corp\.|LLC))',
            r'([A-Z][A-Za-z\-]+(?:\s+[A-Z][A-Za-z\-]+)*\s+(?:AG|GmbH|Inc\.|Ltd\.|SE|KG|OHG|e\.V\.|S\.A\.|N\.V\.|Corp\.|LLC))',
            r'([\w\-]+(?:\s+(?:AG|GmbH|Inc\.|Ltd\.|SE|KG|OHG|e\.V\.|S\.A\.|N\.V\.|Corp\.|LLC))+)'
        ]
        
        # Enhanced document type detection with confidence scoring
        doc_type_patterns = {
            "statement": {
                "patterns": [
                    r'(?:Konto)?auszug',
                    r'Statement',
                    r'Account\s+Statement',
                    r'Bank\s+Statement'
                ],
                "score": 0
            },
            "invoice": {
                "patterns": [
                    r'Rechnung',
                    r'Invoice',
                    r'Bill',
                    r'Faktura'
                ],
                "score": 0
            },
            "receipt": {
                "patterns": [
                    r'Quittung',
                    r'Receipt',
                    r'Beleg',
                    r'Kassenbon'
                ],
                "score": 0
            },
            "fee_statement": {
                "patterns": [
                    r'Entgeltaufstellung',
                    r'Fee\s+Statement',
                    r'Gebührenaufstellung',
                    r'Charges\s+Statement'
                ],
                "score": 0
            }
        }
        
        # Enhanced author detection patterns
        author_patterns = [
            r'(?:Vorstand|Board):\s*([^·\n]+?)(?=\s*[·\n])',
            r'(?:Geschäftsführer|CEO|Managing Director):\s*([^·\n]+?)(?=\s*[·\n])',
            r'(?:Verfasser|Author):\s*([^·\n]+?)(?=\s*[·\n])',
            r'(?:Erstellt von|Created by):\s*([^·\n]+?)(?=\s*[·\n])'
        ]
        
        # Enhanced date patterns with validation and standardization
        date_patterns = [
            (r'(\d{2})\.(\d{2})\.(\d{4})', r'\3-\2-\1'),  # DD.MM.YYYY -> YYYY-MM-DD
            (r'(\d{4})-(\d{2})-(\d{2})', r'\1-\2-\3'),    # YYYY-MM-DD stays as is
            (r'(\d{2})/(\d{2})/(\d{4})', r'\3-\2-\1'),    # DD/MM/YYYY -> YYYY-MM-DD
            (r'(\d{1,2})\.\s*(Jan|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez)[a-zäöü]*\.?\s*(\d{4})', 
             lambda m: f"{m.group(3)}-{self._month_to_num(m.group(2))}-{int(m.group(1)):02d}")  # DD. Month YYYY
        ]
        
        # Enhanced amount patterns with currency validation
        amount_patterns = [
            (r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*(?:EUR|€)', 'EUR'),
            (r'(?:EUR|€)\s*(\d+(?:\.\d{3})*(?:,\d{2})?)', 'EUR'),
            (r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*Euro', 'EUR'),
            (r'(\d+(?:\.\d{3})*(?:\.\d{2})?)\s*(?:USD|\$)', 'USD'),
            (r'(?:USD|\$)\s*(\d+(?:\.\d{3})*(?:\.\d{2})?)', 'USD'),
            (r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*(?:CHF)', 'CHF'),
            (r'(?:£)\s*(\d+(?:\.\d{3})*(?:\.\d{2})?)', 'GBP')
        ]
        
        # Extract document type with confidence scoring
        if not info.get("document_type"):
            max_score = 0
            best_type = None
            for doc_type, type_info in doc_type_patterns.items():
                score = 0
                for pattern in type_info["patterns"]:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for _ in matches:
                        score += 1
                if score > max_score:
                    max_score = score
                    best_type = doc_type
            if best_type:
                info["document_type"] = {
                    "type": best_type,
                    "confidence": min(max_score / 3, 1.0)  # Normalize confidence
                }
        
        # Extract company with validation
        if not info.get("company"):
            companies = []
            for pattern in company_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    company = match.group(1).strip()
                    if company and len(company) > 5:  # Avoid short matches
                        companies.append(company)
            
            if companies:
                # Use the most frequently occurring company name
                from collections import Counter
                company_counts = Counter(companies)
                most_common = company_counts.most_common(1)[0]
                info["company"] = {
                    "name": most_common[0],
                    "confidence": min(most_common[1] / 2, 1.0)  # Normalize confidence
                }
        
        # Extract author with validation
        if not info.get("author"):
            authors = []
            for pattern in author_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    author = match.group(1).strip()
                    if author and len(author) > 3:  # Avoid short matches
                        authors.append(author)
            
            if authors:
                # Use the most frequently occurring author name
                from collections import Counter
                author_counts = Counter(authors)
                most_common = author_counts.most_common(1)[0]
                info["author"] = {
                    "name": most_common[0],
                    "confidence": min(most_common[1] / 2, 1.0)  # Normalize confidence
                }
        
        # Extract and standardize dates with validation
        for pattern, format_to in date_patterns:
            for match in re.finditer(pattern, text):
                if callable(format_to):
                    date_str = format_to(match)
                else:
                    date_str = re.sub(pattern, format_to, match.group())
                try:
                    # Validate date
                    parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                    # Only accept dates within reasonable range
                    if 1900 <= parsed_date.year <= datetime.now().year + 1:
                        info["dates"].add(date_str)
                except ValueError:
                    continue
        
        # Extract amounts with currency
        for pattern, currency in amount_patterns:
            for match in re.finditer(pattern, text):
                amount = match.group(1).strip()
                # Standardize amount format (replace comma with dot for decimal)
                amount = amount.replace(".", "").replace(",", ".")
                try:
                    # Validate amount is a valid number
                    float_amount = float(amount)
                    if float_amount > 0:  # Only accept positive amounts
                        info["amounts"].append({  # Changed from add() to append()
                            "amount": float_amount,
                            "currency": currency,
                            "original": match.group()
                        })
                except ValueError:
                    continue

    def _month_to_num(self, month: str) -> str:
        """Convert German month abbreviation to number."""
        month_map = {
            'Jan': '01', 'Feb': '02', 'Mär': '03',
            'Apr': '04', 'Mai': '05', 'Jun': '06',
            'Jul': '07', 'Aug': '08', 'Sep': '09',
            'Okt': '10', 'Nov': '11', 'Dez': '12'
        }
        return month_map.get(month[:3], '01')

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
