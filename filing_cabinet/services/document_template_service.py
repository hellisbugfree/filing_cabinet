from typing import Dict, List, Tuple, Optional, Any, Set
import pdfplumber
import re
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import os
from openai import OpenAI
from ..config import get_config
import logging

logger = logging.getLogger(__name__)

@dataclass
class DocumentZone:
    name: str
    bounds: Tuple[float, float, float, float]  # x1, y1, x2, y2 in percentage
    content_type: str  # "text", "table", "amount", "date", "metadata"
    patterns: List[str]  # regex patterns for this zone
    required: bool = False

@dataclass
class DocumentTemplate:
    name: str
    identifier_patterns: List[str]  # patterns to identify this document type
    zones: List[DocumentZone]
    metadata_patterns: Dict[str, str]  # patterns for extracting metadata

@dataclass
class DocumentContext:
    """Rich context about the document."""
    document_type: str
    purpose: str
    relevance: List[str]  # List of relevant aspects (e.g., "tax", "insurance", "banking")
    temporal_context: Dict[str, Any]  # Time-related context (period, validity, etc.)
    confidence: float

@dataclass
class ExtractedEntity:
    """Entity with context and relationships."""
    value: Any
    entity_type: str
    confidence: float
    relationships: List[Dict[str, Any]]
    source_context: str

class DocumentTemplateService:
    def __init__(self):
        """Initialize the document template service with AI capabilities."""
        self.templates = self._initialize_templates()
        
        # Get configuration
        self.config = get_config()
        self.openai_client = None
        
        # Try to initialize OpenAI client, but don't fail if key is missing
        try:
            api_key = self.config.get('openai.api_key', None)
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
            else:
                logger.debug("OpenAI API key not found. AI-powered extraction will be disabled.")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}. AI-powered extraction will be disabled.")

    def _initialize_templates(self) -> Dict[str, DocumentTemplate]:
        """Initialize document templates for different document types."""
        return {
            "bank_statement": self._create_bank_statement_template(),
            "fee_statement": self._create_fee_statement_template(),
        }

    def _create_bank_statement_template(self) -> DocumentTemplate:
        """Create template for bank statements."""
        return DocumentTemplate(
            name="bank_statement",
            identifier_patterns=[
                r"Kontoauszug",
                r"Girokonto",
                r"ING-DiBa AG"
            ],
            zones=[
                DocumentZone(
                    name="header",
                    bounds=(0, 0, 1, 0.2),
                    content_type="metadata",
                    patterns=[
                        r"Girokonto\s+(?:Nummer|Nr\.?)\s*(\d+)",
                        r"IBAN[:\s]+([A-Z]{2}\d{2}\s*(?:\d{4}\s*){4,7})",
                        r"BIC[:\s]+([A-Z0-9]{8,11})",
                        r"Kontoauszug\s+([A-Za-zäöüÄÖÜß]+\s+\d{4})",
                        r"Auszugsnummer\s+(\d+)",
                        r"Datum\s+(\d{2}\.\d{2}\.\d{4})"
                    ],
                    required=True
                ),
                DocumentZone(
                    name="balance",
                    bounds=(0, 0.1, 1, 0.4),
                    content_type="metadata",
                    patterns=[
                        r"Alter Saldo\s+([\d.,]+)\s*Euro",
                        r"Neuer Saldo\s+([\d.,]+)\s*Euro",
                        r"Eingeräumte Kontoüberziehung\s+([\d.,]+)\s*Euro"
                    ],
                    required=True
                ),
                DocumentZone(
                    name="transactions",
                    bounds=(0, 0.2, 1, 1),
                    content_type="table",
                    patterns=[
                        r"(\d{2}\.\d{2}\.\d{4})\s+([^-\d].*?)(?:\s+|$)(?:[-\d.,]+)?\s*$",
                        r"Buchung\s+(?:\/\s*)?Verwendungszweck\s+Betrag\s*\(EUR\)",
                        r"Mandat:([^\n]+)",
                        r"Referenz:([^\n]+)"
                    ],
                    required=True
                )
            ],
            metadata_patterns={
                "account_number": r"Girokonto\s+(?:Nummer|Nr\.?)\s*(\d+)",
                "iban": r"IBAN[:\s]+([A-Z]{2}\d{2}\s*(?:\d{4}\s*){4,7})",
                "bic": r"BIC[:\s]+([A-Z0-9]{8,11})",
                "statement_period": r"Kontoauszug\s+([A-Za-zäöüÄÖÜß]+\s+\d{4})",
                "statement_number": r"Auszugsnummer\s+(\d+)"
            }
        )

    def _create_fee_statement_template(self) -> DocumentTemplate:
        """Create template for fee statements."""
        return DocumentTemplate(
            name="fee_statement",
            identifier_patterns=[
                r"Entgeltaufstellung",
                r"Entgelt-\s*und\s*Zinsübersicht",
                r"gezahlte\s+Entgelte"
            ],
            zones=[
                DocumentZone(
                    name="header",
                    bounds=(0, 0, 1, 0.2),
                    content_type="metadata",
                    patterns=[
                        r"Kontobezeichnung\s+([^\n]+)",
                        r"Kontokennung\s+([A-Z]{2}\d{2}\s*(?:\d{4}\s*){4,7})",
                        r"Zeitraum\s+Von\s+(\d{2}\.\d{2}\.\d{4})\s+bis\s+(\d{2}\.\d{2}\.\d{4})",
                        r"Datum\s+(\d{2}\.\d{2}\.\d{4})"
                    ],
                    required=True
                ),
                DocumentZone(
                    name="account_holder",
                    bounds=(0, 0.1, 0.5, 0.3),
                    content_type="metadata",
                    patterns=[
                        r"([A-Za-zäöüÄÖÜß]+\s+[A-Za-zäöüÄÖÜß]+)\s*\n",
                        r"([A-Za-zäöüÄÖÜß]+[^\n]+)\s*\n\d{5}\s+[A-Za-zäöüÄÖÜß]+"  # Address
                    ],
                    required=True
                ),
                DocumentZone(
                    name="summary",
                    bounds=(0, 0.2, 1, 0.4),
                    content_type="amount",
                    patterns=[
                        r"Insgesamt\s+gezahlte\s+Entgelte\s*(-?[\d.,]+)\s*EUR",
                        r"Insgesamt\s+gezahlte\s+Zinsen\s*(-?[\d.,]+)\s*EUR",
                        r"Insgesamt\s+erhaltene\s+Zinsen\s*(-?[\d.,]+)\s*EUR"
                    ],
                    required=True
                ),
                DocumentZone(
                    name="fees",
                    bounds=(0, 0.4, 1, 0.9),
                    content_type="table",
                    patterns=[
                        r"Dienst\s+Entgelt",
                        r"Dienstleistungspaket\s+Entgelt",
                        r"(\d+,\d{2})\s*EUR"
                    ],
                    required=True
                )
            ],
            metadata_patterns={
                "account_type": r"Kontobezeichnung\s+([^\n]+)",
                "iban": r"Kontokennung\s+([A-Z]{2}\d{2}\s*(?:\d{4}\s*){4,7})",
                "period_start": r"Zeitraum\s+Von\s+(\d{2}\.\d{2}\.\d{4})",
                "period_end": r"Zeitraum\s+Von\s+\d{2}\.\d{2}\.\d{4}\s+bis\s+(\d{2}\.\d{2}\.\d{4})",
                "statement_date": r"Datum\s+(\d{2}\.\d{2}\.\d{4})",
                "account_holder": r"([A-Za-zäöüÄÖÜß]+\s+[A-Za-zäöüÄÖÜß]+)\s*\n",
                "address": r"([A-Za-zäöüÄÖÜß]+[^\n]+)\s*\n\d{5}\s+[A-Za-zäöüÄÖÜß]+",
                "total_fees": r"Insgesamt\s+gezahlte\s+Entgelte\s*(-?[\d.,]+)\s*EUR",
                "total_interest_paid": r"Insgesamt\s+gezahlte\s+Zinsen\s*(-?[\d.,]+)\s*EUR",
                "total_interest_received": r"Insgesamt\s+erhaltene\s+Zinsen\s*(-?[\d.,]+)\s*EUR"
            }
        )

    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process document with enhanced AI-powered extraction."""
        try:
            # First try AI-based extraction if available
            if self.openai_client:
                try:
                    ai_results = self._process_with_ai(file_path)
                    if ai_results and "error" not in ai_results:
                        logger.info("Successfully processed with AI")
                        return ai_results
                except Exception as e:
                    logger.warning(f"AI processing failed: {str(e)}")

            # Fall back to template matching
            return self._process_with_template(file_path)

        except Exception as e:
            return {"error": str(e)}

    def _process_with_ai(self, file_path: str) -> Dict[str, Any]:
        """Process document using AI-based extraction."""
        try:
            # Extract text from PDF
            with pdfplumber.open(file_path) as pdf:
                pages = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
                full_text = "\n\n".join(pages)

            if not full_text:
                logger.warning("No text content found in PDF")
                return {"error": "No text content found"}

            metadata = {"content": {"text": full_text}}
            return self.process_with_ai(full_text, metadata)

        except Exception as e:
            logger.warning(f"AI processing error: {str(e)}")
            return {"error": f"AI processing failed: {str(e)}"}

    def process_with_ai(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process document with AI, with enhanced error handling."""
        if not text:
            metadata['processing'] = {
                'method': 'traditional',
                'reason': 'No text content available',
                'timestamp': datetime.now().isoformat()
            }
            return metadata

        if not self.openai_client:
            metadata['processing'] = {
                'method': 'traditional',
                'reason': 'OpenAI client not configured',
                'timestamp': datetime.now().isoformat()
            }
            return metadata

        try:
            # Initialize document info if not present
            if 'document_info' not in metadata:
                metadata['document_info'] = {}

            # Prepare the system prompt
            prompt = self._prepare_ai_prompt(text)
            
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text[:4000]}  # Limit text to first 4000 chars
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Process the response
            ai_result = self._process_ai_response(response)
            
            # Update metadata with AI results
            if 'error' not in ai_result:
                metadata.update(ai_result)
                metadata['processing'] = {
                    'method': 'ai',
                    'model': 'gpt-3.5-turbo',
                    'timestamp': datetime.now().isoformat(),
                    'confidence': response.choices[0].finish_reason == 'stop'
                }
                logger.info("Successfully processed with AI")
            else:
                # If AI processing failed, keep the original metadata
                metadata['processing'] = {
                    'method': 'traditional',
                    'fallback_reason': {
                        'error_type': 'AIProcessingError',
                        'error_message': ai_result['error'],
                        'resolution_hint': 'AI processing failed to parse the document'
                    },
                    'timestamp': datetime.now().isoformat()
                }
                logger.warning(f"AI processing failed to parse response: {ai_result['error']}")
            
            return metadata
            
        except openai.RateLimitError as e:
            logger.warning(f"AI processing error: Error code: 429 - {str(e)}. Resolution: Please check your OpenAI API quota and billing status at https://platform.openai.com/account/billing")
            metadata['processing'] = {
                'method': 'traditional',
                'fallback_reason': {
                    'error_type': 'RateLimitError',
                    'error_message': str(e)
                },
                'timestamp': datetime.now().isoformat()
            }
            return metadata
        except Exception as e:
            error_info = str(e)
            error_type = type(e).__name__
            quota_exceeded = 'quota' in error_info.lower()
            
            metadata['processing'] = {
                'method': 'traditional',
                'fallback_reason': {
                    'error_type': error_type,
                    'error_message': error_info,
                    'resolution_hint': (
                    'Please check your OpenAI API quota and billing status at '
                    'https://platform.openai.com/account/billing' if quota_exceeded
                    else 'An unexpected error occurred during AI processing'
                )
            },
                'timestamp': datetime.now().isoformat()
            }
            
            logger.warning(
                f"AI processing error: {error_info}. "
                f"Resolution: {metadata['processing']['fallback_reason']['resolution_hint']}"
            )
            
            # Keep the original metadata structure when AI fails
            if 'content' not in metadata:
                metadata['content'] = {
                    'text': text,
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
            
            return metadata

    def _prepare_ai_prompt(self, text: str) -> str:
        """Prepare the system prompt for AI processing."""
        return """You are a document analysis assistant. Extract key information from the document text in the following categories:
        - Document Type: Identify the type of document (e.g., bank statement, invoice, etc.)
        - Purpose: The main purpose or subject of the document
        - Metadata: Key information like dates, reference numbers, account numbers
        - People: Names of individuals mentioned
        - Organizations: Company names, institutions, etc.
        - Amounts: Financial amounts (convert to decimal format)
        - Key-Value Pairs: Important document metadata
        
        Format your response as a JSON object with these fields."""

    def _process_ai_response(self, response: Any) -> Dict[str, Any]:
        """Process the AI response and extract relevant information."""
        try:
            result = json.loads(response.choices[0].message.content)
            
            # Ensure all required fields exist with defaults
            processed_result = {
                "document_type": result.get("document_type", "unknown"),
                "metadata": result.get("metadata", {}),
                "content": {
                    "text": result.get("text", ""),
                    "key_value_pairs": result.get("key_value_pairs", {}),
                    "entities": {
                        "people": result.get("people", []),
                        "organizations": result.get("organizations", []),
                        "dates": result.get("dates", []),
                        "amounts": result.get("amounts", [])
                    }
                }
            }
            
            return processed_result
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response: {str(e)}")
            return {"error": "Failed to parse AI response"}
        except KeyError as e:
            logger.warning(f"Missing required field in AI response: {str(e)}")
            return {"error": f"Invalid AI response format: missing {str(e)}"}
        except Exception as e:
            logger.warning(f"Unexpected error processing AI response: {str(e)}")
            return {"error": f"Failed to process AI response: {str(e)}"}

    def _process_with_template(self, file_path: str) -> Dict[str, Any]:
        """Process document using template-based extraction."""
        try:
            with pdfplumber.open(file_path) as pdf:
                # Get text from first page for identification
                first_page_text = pdf.pages[0].extract_text()
                doc_type = self.identify_document_type(first_page_text)
                
                if not doc_type or doc_type not in self.templates:
                    return {"error": "Unknown document type"}
                
                template = self.templates[doc_type]
                result = {
                    "document_type": doc_type,
                    "metadata": {},
                    "zones": {},
                    "confidence": 0.0,
                    "key_value_pairs": {}
                }
                
                # Process each zone
                total_confidence = 0
                num_required_zones = 0
                
                for zone in template.zones:
                    zone_data = self.extract_from_zone(pdf.pages[0], zone)
                    result["zones"][zone.name] = zone_data
                    
                    if zone.required:
                        num_required_zones += 1
                        patterns_found = len(zone_data.get("matches", []))
                        total_patterns = len(zone.patterns)
                        zone_confidence = patterns_found / total_patterns if total_patterns > 0 else 0
                        total_confidence += zone_confidence
                
                # Calculate overall confidence
                result["confidence"] = total_confidence / num_required_zones if num_required_zones > 0 else 0
                
                # Extract metadata using patterns
                for key, pattern in template.metadata_patterns.items():
                    matches = re.finditer(pattern, first_page_text, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        value = match.group(1)
                        # Clean and standardize values
                        if "amount" in key or "balance" in key or "total" in key:
                            value = self._standardize_amount(value)
                        elif "date" in key or "period" in key:
                            value = self._standardize_date(value)
                        result["metadata"][key] = value
                
                # Extract key-value pairs
                result["key_value_pairs"] = self._extract_key_value_pairs(first_page_text)
                
                # Enhance bank statement template and AI processing
                if doc_type == "bank_statement":
                    result = self._extract_entities(result)
                
                return result
                
        except Exception as e:
            return {"error": str(e)}

    def _standardize_amount(self, amount_str: str) -> float:
        """Standardize amount string to float."""
        try:
            # Remove currency symbols and spaces
            cleaned = amount_str.replace("EUR", "").replace("€", "").strip()
            # Replace German number format
            cleaned = cleaned.replace(".", "").replace(",", ".")
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0

    def _standardize_date(self, date_str: str) -> str:
        """Standardize date string to ISO format."""
        try:
            # Handle German date format
            if "." in date_str:
                parts = date_str.split(".")
                if len(parts) == 3:
                    return f"{parts[2].strip()}-{parts[1].strip():0>2}-{parts[0].strip():0>2}"
            return date_str
        except (ValueError, IndexError):
            return date_str

    def _extract_key_value_pairs(self, text: str) -> Dict[str, str]:
        """Extract key-value pairs from text."""
        pairs = {}
        # Look for patterns like "Key: Value" or "Key Value"
        patterns = [
            r"([A-Za-zäöüÄÖÜß\s]+):\s*([^\n]+)",  # Key: Value
            r"([A-Za-zäöüÄÖÜß\s]+)\s+(\d[\d\s.,]+(?:EUR|€)?(?:\s*p\.a\.)?)"  # Key Amount
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                key = match.group(1).strip()
                value = match.group(2).strip()
                if key and value and len(key) > 2:  # Avoid single-letter keys
                    pairs[key] = value
        
        return pairs

    def identify_document_type(self, text: str) -> Optional[str]:
        """Identify document type based on text content."""
        scores = {}
        for template_name, template in self.templates.items():
            score = 0
            for pattern in template.identifier_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                score += sum(1 for _ in matches)
            scores[template_name] = score

        if not scores:
            return None

        best_match = max(scores.items(), key=lambda x: x[1])
        return best_match[0] if best_match[1] > 0 else None

    def extract_from_zone(self, page: Any, zone: DocumentZone) -> Dict[str, Any]:
        """Extract content from a specific zone in the page."""
        # Convert relative bounds to absolute coordinates
        x1, y1, x2, y2 = zone.bounds
        height = float(page.height)
        width = float(page.width)
        
        crop_box = (
            x1 * width,
            y1 * height,
            x2 * width,
            y2 * height
        )
        
        cropped = page.crop(crop_box)
        extracted = {
            "text": cropped.extract_text() or "",
            "matches": []
        }
        
        # Extract based on content type
        if zone.content_type == "table":
            tables = page.extract_tables()
            if tables:
                extracted["tables"] = tables
        
        # Find pattern matches
        for pattern in zone.patterns:
            matches = re.finditer(pattern, extracted["text"], re.IGNORECASE | re.MULTILINE)
            for match in matches:
                extracted["matches"].append({
                    "pattern": pattern,
                    "groups": match.groups(),
                    "text": match.group(0)
                })
        
        return extracted

    def _extract_entities(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entities from text using OpenAI and traditional methods."""
        text = metadata["content"]["text"]
        if not text:
            return metadata

        # Track processing method
        metadata["filing_cabinet"]["processing_method"] = []
        
        try:
            # Try OpenAI first if it's a bank statement
            if self.openai_client and "bank_statement" in metadata.get("document_info", {}).get("type", "").lower():
                try:
                    metadata["filing_cabinet"]["processing_method"].append("openai")
                    
                    response = self.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": """You are a German bank statement analysis assistant. Extract the following information:
                            1. Account Information:
                               - Account holder name
                               - Account number/IBAN
                               - Bank name and BIC
                            2. Statement Details:
                               - Statement period
                               - Statement number
                               - Opening balance (Alter Saldo)
                               - Closing balance (Neuer Saldo)
                               - Overdraft limit (Eingeräumte Kontoüberziehung)
                            3. Transactions (as a structured list):
                               For each transaction:
                               - Date (YYYY-MM-DD)
                               - Description (full description including reference numbers)
                               - Amount (negative for debits, positive for credits)
                               - Category (e.g., "rent", "insurance", "utilities", etc.)
                               - Reference/mandate information if available
                            
                            Format your response as a JSON object with these exact keys:
                            {
                                "account_info": {
                                    "holder": "",
                                    "account_number": "",
                                    "iban": "",
                                    "bic": "",
                                    "bank": ""
                                },
                                "statement_details": {
                                    "period": "",
                                    "number": "",
                                    "opening_balance": 0.00,
                                    "closing_balance": 0.00,
                                    "overdraft_limit": 0.00
                                },
                                "transactions": [
                                    {
                                        "date": "YYYY-MM-DD",
                                        "description": "",
                                        "amount": 0.00,
                                        "category": "",
                                        "reference": "",
                                        "mandate": ""
                                    }
                                ]
                            }"""},
                            {"role": "user", "content": text}
                        ],
                        temperature=0.3,
                        response_format={"type": "json_object"}
                    )
                    
                    ai_results = json.loads(response.choices[0].message.content)
                    
                    # Update metadata with AI results
                    metadata.setdefault("document_info", {}).update({
                        "type": "bank_statement",
                        "account_info": ai_results.get("account_info", {}),
                        "statement_details": ai_results.get("statement_details", {})
                    })
                    
                    # Add structured transaction data
                    metadata["content"]["transactions"] = ai_results.get("transactions", [])
                    
                except Exception as e:
                    logger.warning(f"AI processing error: {e}")
                    raise  # Re-raise to fall back to traditional methods

        except Exception as e:
            logger.warning(f"OpenAI extraction failed: {e}. Falling back to traditional methods.")
            metadata["filing_cabinet"]["processing_method"].append("traditional")
            
            # Traditional extraction methods as fallback
            transactions = []
            current_transaction = None
            
            for line in text.split("\n"):
                # Look for transaction patterns
                date_match = re.search(r"(\d{2}\.\d{2}\.\d{4})\s+([^-\d].*?)(?:\s+|$)([-\d.,]+)?\s*$", line)
                if date_match:
                    if current_transaction:
                        transactions.append(current_transaction)
                    
                    date_str, desc, amount_str = date_match.groups()
                    try:
                        date = datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
                        amount = float(amount_str.replace(".", "").replace(",", ".")) if amount_str else None
                        
                        current_transaction = {
                            "date": date,
                            "description": desc.strip(),
                            "amount": amount,
                            "category": self._guess_transaction_category(desc),
                            "reference": "",
                            "mandate": ""
                        }
                    except (ValueError, TypeError):
                        continue
                
                # Look for additional transaction information
                elif current_transaction:
                    mandate_match = re.search(r"Mandat:([^\n]+)", line)
                    reference_match = re.search(r"Referenz:([^\n]+)", line)
                    
                    if mandate_match:
                        current_transaction["mandate"] = mandate_match.group(1).strip()
                    if reference_match:
                        current_transaction["reference"] = reference_match.group(1).strip()
                    elif not any(p in line.lower() for p in ["buchung", "valuta"]):
                        # Append additional description lines
                        current_transaction["description"] = current_transaction["description"] + " " + line.strip()
            
            # Don't forget the last transaction
            if current_transaction:
                transactions.append(current_transaction)
            
            if transactions:
                metadata["content"]["transactions"] = transactions

            # Extract balance information
            balance_patterns = {
                "opening_balance": r"Alter\s+Saldo\s+([\d.,]+)\s*Euro",
                "closing_balance": r"Neuer\s+Saldo\s+([\d.,]+)\s*Euro",
                "overdraft_limit": r"Eingeräumte\s+Kontoüberziehung\s+([\d.,]+)\s*Euro"
            }
            
            balances = {}
            for key, pattern in balance_patterns.items():
                match = re.search(pattern, text)
                if match:
                    try:
                        amount = float(match.group(1).replace(".", "").replace(",", "."))
                        balances[key] = amount
                    except (ValueError, TypeError):
                        continue
            
            if balances:
                metadata.setdefault("document_info", {}).setdefault("statement_details", {}).update(balances)

        return metadata

    def _guess_transaction_category(self, description: str) -> str:
        """Guess transaction category based on description."""
        description = description.lower()
        
        categories = {
            "rent": ["miete", "mietvertrag", "wohnung"],
            "insurance": ["versicherung", "allianz", "uniqa", "nurnberger", "huk", "lebensvers"],
            "utilities": ["strom", "gas", "wasser", "stadtwerke", "lekker energie"],
            "salary": ["gehalt", "lohn", "einkommen"],
            "transfer": ["überweisung", "dauerauftrag", "gutschrift"],
            "cash": ["bargeld", "atm", "geldautomat", "bargeldauszahlung"],
            "subscription": ["abo", "netflix", "spotify", "itunes", "google", "medium monthly"],
            "transportation": ["uber", "taxi", "bvg", "deutsche bahn", "mytaxi", "flug", "ratp"],
            "shopping": ["edeka", "rewe", "kaufland", "zara", "esprit", "amazon"],
            "dining": ["restaurant", "café", "coffee", "marche", "bailli"],
            "travel": ["hotel", "booking", "airbnb", "flug", "bahn"],
            "healthcare": ["apotheke", "arzt", "klinik", "medical"],
            "donation": ["spende", "umwelthilfe", "grundeinkommen"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in description for keyword in keywords):
                return category
                
        return "other"
