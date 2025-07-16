"""Enhanced multi-engine pharmaceutical invoice parser.

Uses multiple PDF extraction engines (pdfplumber, PyMuPDF, pdfminer) with
OCR fallback and pharmaceutical-specific pattern recognition.
Targets 85-90% accuracy for Indian pharmaceutical invoices.
"""
from __future__ import annotations

import re
import io
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import logging

try:
    import pdfplumber
    import fitz  # PyMuPDF
    import pytesseract
    from PIL import Image
except ImportError as e:
    logging.warning(f"Missing dependencies for enhanced parser: {e}")

from ..models import Invoice, InvoiceItem
from .base import BaseParser
from ..pharma_patterns import (
    PharmaPatternMatcher, 
    PHARMA_COMPANY_PATTERNS,
    DRUG_NAME_PATTERNS,
    BATCH_PATTERNS,
    EXPIRY_PATTERNS,
    HSN_PHARMA_PATTERNS,
    DRUG_LICENSE_PATTERNS,
    PACK_SIZE_PATTERNS,
    STRENGTH_PATTERNS,
    PRICE_PATTERNS,
    TAX_PATTERNS,
    INVOICE_PATTERNS,
    get_pattern_count
)

# Enhanced pattern definitions for pharmaceutical invoices
_DATE_PATTERNS = [
    r"\b(\d{1,2}[\-/.]?\d{1,2}[\-/.]?\d{4})\b",  # 13/01/2025, 13-01-2025, 13.01.2025
    r"\b(\d{4}[\-/.]?\d{1,2}[\-/.]?\d{1,2})\b",  # 2025-01-13
    r"\b(\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})\b",  # 13 Jan 2025
    r"\b(\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b",
]

_GSTIN_REGEX = r"\b[0-3][0-9][A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b"
_AMOUNT_REGEX = r"(?P<amt>\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"

# Use comprehensive patterns from pharma_patterns module
_PHARMA_KEYWORDS = [
    "tablet", "capsule", "syrup", "injection", "drops", "cream", "ointment",
    "powder", "suspension", "lotion", "gel", "inhaler", "strip", "vial",
    "ampoule", "bottle", "tube", "pack", "box", "mg", "ml", "gm", "mcg"
]


class GenericParser(BaseParser):
    """Enhanced multi-engine parser for pharmaceutical invoices."""

    name = "enhanced_generic"
    supplier_keywords: List[str] = []  # Matches everything
    priority = -100  # Lowest priority so others try first
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pharma_matcher = PharmaPatternMatcher()
        self.confidence_weights = {
            'supplier_match': 0.25,
            'invoice_structure': 0.20,
            'date_extraction': 0.15,
            'amount_validation': 0.20,
            'item_extraction': 0.20
        }
        logging.info(f"Enhanced parser initialized with {get_pattern_count()} pharmaceutical patterns")

    @classmethod
    def _extract_text_multi_engine(cls, pdf_path: str) -> Tuple[str, List[Any]]:
        """Extract text using multiple engines with OCR fallback."""
        text = ""
        tables = []
        
        try:
            # Method 1: pdfplumber (best for tables)
            with pdfplumber.open(pdf_path) as pdf:
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    text_parts.append(page_text)
                    
                    # Extract tables
                    page_tables = page.extract_tables()
                    tables.extend(page_tables or [])
                    
                text = "\n".join(text_parts)
                
            # If text extraction failed, try PyMuPDF
            if len(text.strip()) < 100:
                doc = fitz.open(pdf_path)
                text_parts = []
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text_parts.append(page.get_text())
                text = "\n".join(text_parts)
                doc.close()
                
            # OCR fallback if still poor extraction
            if len(text.strip()) < 50:
                text = cls._ocr_extract(pdf_path)
                
        except Exception as e:
            logging.warning(f"PDF extraction failed: {e}")
            # Final fallback to OCR
            text = cls._ocr_extract(pdf_path)
            
        return text, tables
    
    @classmethod
    def _ocr_extract(cls, pdf_path: str) -> str:
        """Extract text using OCR as fallback."""
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path)
            text_parts = []
            
            for image in images:
                ocr_text = pytesseract.image_to_string(image, lang='eng')
                text_parts.append(ocr_text)
                
            return "\n".join(text_parts)
        except Exception as e:
            logging.error(f"OCR extraction failed: {e}")
            return ""
    
    @classmethod
    def _find_date(cls, text: str) -> Tuple[Optional[datetime], float]:
        """Find invoice date with confidence scoring."""
        confidence = 0.0
        
        for i, pat in enumerate(_DATE_PATTERNS):
            matches = re.findall(pat, text, re.IGNORECASE)
            for match in matches:
                date_str = match if isinstance(match, str) else match[0]
                
                # Try different date formats
                formats = [
                    "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
                    "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
                    "%d %b %Y", "%d %B %Y"
                ]
                
                for fmt in formats:
                    try:
                        date_obj = datetime.strptime(date_str, fmt)
                        # Higher confidence for more specific patterns
                        confidence = 0.9 - (i * 0.1)
                        return date_obj, confidence
                    except ValueError:
                        continue
                        
        return None, 0.0

    @classmethod
    def _find_supplier(cls, text: str) -> Tuple[str, float]:
        """Find supplier name with pharmaceutical company recognition."""
        lines = text.splitlines()
        confidence = 0.0
        supplier_name = "Unknown"
        pharma_matcher = PharmaPatternMatcher()
        
        # Check if text contains pharmaceutical company patterns
        is_pharma, pharma_confidence = pharma_matcher.is_pharma_company(text)
        
        # Look for lines with company patterns
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            line = line.strip()
            if not line or len(line) < 3:
                continue
                
            line_lower = line.lower()
            
            # Use advanced pharmaceutical company pattern matching
            for pattern_str in PHARMA_COMPANY_PATTERNS:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                if pattern.search(line):
                    supplier_name = line[:120]
                    confidence = 0.9 + (0.05 if "pharmaceuticals" in line_lower else 0)
                    return supplier_name, confidence
            
            # Check for common pharma keywords
            pharma_score = sum(1 for keyword in _PHARMA_KEYWORDS 
                             if keyword in line_lower) / len(_PHARMA_KEYWORDS)
            
            if pharma_score > 0.1 and len(line) > 10:
                supplier_name = line[:120]
                confidence = min(0.8, pharma_score * 3) + (pharma_confidence * 0.2)
                return supplier_name, confidence
                
            # Check for traditional company suffixes
            company_suffixes = ["pvt ltd", "private limited", "ltd", "limited", 
                              "pharmaceuticals", "pharma", "healthcare", "labs", "laboratories"]
            for suffix in company_suffixes:
                if suffix in line_lower:
                    supplier_name = line[:120]
                    confidence = 0.75 + (pharma_confidence * 0.2)
                    return supplier_name, confidence
                
            # Fallback: first substantial line
            if len(line) > 15 and confidence < 0.3:
                supplier_name = line[:120]
                confidence = 0.3 + (pharma_confidence * 0.1)
                
        return supplier_name, confidence

    @classmethod
    def _find_gstin(cls, text: str) -> Tuple[Optional[str], float]:
        """Find GSTIN with validation."""
        matches = re.findall(_GSTIN_REGEX, text, re.IGNORECASE)
        
        if not matches:
            return None, 0.0
            
        # Return first valid GSTIN (supplier's)
        gstin = matches[0].upper()
        
        # Validate GSTIN format
        if len(gstin) == 15 and gstin[2:7].isalpha() and gstin[7:11].isdigit():
            return gstin, 0.9
        
        return gstin, 0.6  # Found but format validation failed

    @classmethod
    def _find_invoice_number(cls, text: str) -> Tuple[str, float]:
        """Find invoice number with comprehensive pattern matching."""
        
        # Use pharmaceutical-specific invoice patterns first
        for pattern_str in INVOICE_PATTERNS:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = pattern.findall(text)
            if matches:
                inv_num = matches[0].strip()
                if len(inv_num) >= 3:  # Minimum reasonable length
                    return inv_num, 0.9
        
        # Fallback to basic patterns
        basic_patterns = [
            r"(?:invoice|bill)\s*(?:no|number|#)[\s:]*([A-Za-z0-9\-/]+)",
            r"(?:inv|bill)\s*[\s:]*([A-Za-z0-9\-/]+)",
            r"\b(INV[A-Za-z0-9\-/]+)\b",
            r"\b([A-Z]{2,4}\d{3,8})\b",
        ]
        
        for pattern_str in basic_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = pattern.findall(text)
            if matches:
                inv_num = matches[0].strip()
                if len(inv_num) >= 3:
                    return inv_num, 0.7
                    
        # Last resort: look for standalone alphanumeric patterns
        lines = text.split('\n')[:5]  # Check first 5 lines
        for line in lines:
            if 'invoice' in line.lower():
                tokens = re.findall(r'[A-Z0-9]{3,}', line)
                for token in tokens:
                    if token.upper() != 'INVOICE':
                        return token, 0.5
                        
        return "UNKNOWN", 0.0
    
    @classmethod
    def _find_drug_license(cls, text: str) -> Tuple[Optional[str], float]:
        """Find drug license number using comprehensive patterns."""
        pharma_matcher = PharmaPatternMatcher()
        
        # Use comprehensive drug license patterns
        licenses = pharma_matcher.extract_drug_licenses(text)
        if licenses:
            # Return the one with highest confidence
            best_license = max(licenses, key=lambda x: x[1])
            return best_license[0], best_license[1]
            
        return None, 0.0

    @classmethod
    def _parse_table_items(cls, tables: list, text: str) -> Tuple[List[InvoiceItem], float]:
        """Enhanced table parsing with pharmaceutical-specific logic."""
        items: List[InvoiceItem] = []
        confidence = 0.0
        total_confidence = 0.0
        item_count = 0
        
        # Parse structured tables
        for table in tables:
            if not table or len(table) < 2:
                continue
                
            headers = [str(cell).lower().strip() if cell else "" for cell in table[0]]
            
            # Find column indices
            desc_idx = cls._find_column_index(headers, ['description', 'particulars', 'item', 'product'])
            hsn_idx = cls._find_column_index(headers, ['hsn', 'hsn code', 'code'])
            batch_idx = cls._find_column_index(headers, ['batch', 'batch no', 'lot', 'lot no'])
            exp_idx = cls._find_column_index(headers, ['expiry', 'exp', 'exp date', 'mfg', 'expiry date'])
            qty_idx = cls._find_column_index(headers, ['qty', 'quantity', 'qnty'])
            rate_idx = cls._find_column_index(headers, ['rate', 'price', 'unit price', 'mrp'])
            total_idx = cls._find_column_index(headers, ['total', 'amount', 'total amount'])
            
            # Parse data rows
            for row in table[1:]:
                if not row or len([cell for cell in row if str(cell).strip()]) < 3:
                    continue
                    
                try:
                    item_confidence = 0.0
                    
                    # Extract description
                    description = str(row[desc_idx]).strip() if desc_idx is not None else ""
                    if not description or description.lower() in ['none', 'nan', '']:
                        continue
                        
                    # Check if it's a pharmaceutical item using advanced patterns
                    desc_lower = description.lower()
                    pharma_matcher = PharmaPatternMatcher()
                    
                    # Check for drug name patterns
                    drug_matches = pharma_matcher.extract_drug_names(description)
                    if drug_matches:
                        item_confidence += 0.4
                    
                    # Check for pharmaceutical keywords
                    pharma_score = sum(1 for kw in _PHARMA_KEYWORDS if kw in desc_lower)
                    item_confidence += min(0.3, pharma_score * 0.1)
                    
                    # Check for strength/dosage patterns
                    strength_patterns = STRENGTH_PATTERNS
                    for pattern_str in strength_patterns:
                        if re.search(pattern_str, description, re.IGNORECASE):
                            item_confidence += 0.2
                            break
                    
                    # Extract numeric fields
                    quantity = cls._extract_numeric(row[qty_idx] if qty_idx is not None else "0")
                    unit_price = cls._extract_numeric(row[rate_idx] if rate_idx is not None else "0")
                    total = cls._extract_numeric(row[total_idx] if total_idx is not None else "0")
                    
                    # Validate calculations
                    if quantity and unit_price and total:
                        expected_total = quantity * unit_price
                        if abs(expected_total - total) / total < 0.1:  # 10% tolerance
                            item_confidence += 0.3
                    
                    # Extract other fields with enhanced pattern matching
                    hsn = str(row[hsn_idx]).strip() if hsn_idx is not None else None
                    batch = str(row[batch_idx]).strip() if batch_idx is not None else None
                    expiry = str(row[exp_idx]).strip() if exp_idx is not None else None
                    
                    # Enhanced HSN validation for pharma
                    if hsn:
                        is_pharma_hsn, hsn_confidence = pharma_matcher.validate_hsn_pharma(hsn)
                        if is_pharma_hsn:
                            item_confidence += hsn_confidence * 0.3
                    
                    # Enhanced batch number extraction if not found in table
                    if not batch or batch.lower() in ['none', 'nan', '']:
                        batch_matches = pharma_matcher.extract_batch_numbers(description)
                        if batch_matches:
                            batch = batch_matches[0][0]
                            item_confidence += 0.1
                    
                    # Enhanced expiry date extraction if not found in table
                    if not expiry or expiry.lower() in ['none', 'nan', '']:
                        expiry_matches = pharma_matcher.extract_expiry_dates(description)
                        if expiry_matches:
                            expiry = expiry_matches[0][0]
                            item_confidence += 0.1
                    
                    item = InvoiceItem(
                        description=description,
                        hsn=hsn if hsn and hsn.lower() not in ['none', 'nan', ''] else None,
                        batch=batch if batch and batch.lower() not in ['none', 'nan', ''] else None,
                        expiry=expiry if expiry and expiry.lower() not in ['none', 'nan', ''] else None,
                        quantity=quantity or 0,
                        unit_price=unit_price or 0,
                        total=total or 0,
                    )
                    items.append(item)
                    total_confidence += item_confidence
                    item_count += 1
                    
                except Exception as e:
                    logging.warning(f"Failed to parse table row: {e}")
                    continue
        
        # Calculate overall confidence
        confidence = total_confidence / max(item_count, 1) if item_count > 0 else 0.0
        
        return items, confidence
    
    @classmethod
    def _find_column_index(cls, headers: List[str], keywords: List[str]) -> Optional[int]:
        """Find column index by matching keywords."""
        for i, header in enumerate(headers):
            for keyword in keywords:
                if keyword in header:
                    return i
        return None
    
    @classmethod
    def _extract_numeric(cls, value: Any) -> float:
        """Extract numeric value from string."""
        if value is None:
            return 0.0
            
        str_val = str(value).replace(',', '').strip()
        
        # Find numeric pattern
        match = re.search(r'\d+(?:\.\d+)?', str_val)
        if match:
            try:
                return float(match.group())
            except ValueError:
                pass
        return 0.0

    @classmethod
    def _extract_financial_data(cls, text: str, items: List[InvoiceItem]) -> Dict[str, Any]:
        """Extract financial information with validation."""
        # Extract all amounts
        amounts = []
        for match in re.finditer(_AMOUNT_REGEX, text.replace(',', '')):
            try:
                amount = float(match.group('amt'))
                amounts.append(amount)
            except ValueError:
                continue
        
        # Calculate totals from items
        items_total = sum(item.total for item in items)
        
        # Find the grand total (usually the largest amount)
        grand_total = max(amounts) if amounts else items_total
        
        # Extract tax information
        cgst = cls._extract_tax_amount(text, 'cgst')
        sgst = cls._extract_tax_amount(text, 'sgst')
        igst = cls._extract_tax_amount(text, 'igst')
        
        return {
            'subtotal': items_total,
            'cgst': cgst,
            'sgst': sgst,
            'igst': igst,
            'grand_total': grand_total,
        }
    
    @classmethod
    def _extract_tax_amount(cls, text: str, tax_type: str) -> Optional[float]:
        """Extract specific tax amount using comprehensive patterns."""
        # Use comprehensive tax patterns first
        for pattern_str in TAX_PATTERNS:
            if tax_type.lower() in pattern_str.lower():
                pattern = re.compile(pattern_str, re.IGNORECASE)
                matches = pattern.findall(text)
                if matches:
                    try:
                        # Handle both percentage and amount patterns
                        amount_str = matches[0]
                        if isinstance(amount_str, tuple):
                            amount_str = amount_str[0]
                        return float(amount_str.replace(',', ''))
                    except (ValueError, IndexError):
                        continue
        
        # Fallback to basic pattern
        pattern = rf'{tax_type}[\s:@]*([0-9,]+\.?\d*)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except ValueError:
                pass
        return None
    
    @classmethod
    def _calculate_confidence(cls, 
                            supplier_conf: float,
                            date_conf: float, 
                            invoice_conf: float,
                            items_conf: float,
                            gstin_conf: float) -> float:
        """Calculate overall confidence score."""
        weights = {
            'supplier': 0.25,
            'date': 0.20,
            'invoice_num': 0.15,
            'items': 0.25,
            'gstin': 0.15
        }
        
        total_score = (
            supplier_conf * weights['supplier'] +
            date_conf * weights['date'] +
            invoice_conf * weights['invoice_num'] +
            items_conf * weights['items'] +
            gstin_conf * weights['gstin']
        )
        
        return min(total_score, 1.0)
    
    @classmethod
    def parse(cls, text: str, tables: list) -> Invoice:
        """Enhanced parsing with confidence scoring."""
        
        # Extract all components with confidence
        supplier_name, supplier_conf = cls._find_supplier(text)
        supplier_gstin, gstin_conf = cls._find_gstin(text)
        invoice_date, date_conf = cls._find_date(text)
        invoice_number, invoice_conf = cls._find_invoice_number(text)
        drug_license, _ = cls._find_drug_license(text)
        
        # Parse items
        items, items_conf = cls._parse_table_items(tables, text)
        
        # Extract financial data
        financial_data = cls._extract_financial_data(text, items)
        
        # Calculate overall confidence
        overall_confidence = cls._calculate_confidence(
            supplier_conf, date_conf, invoice_conf, items_conf, gstin_conf
        )
        
        return Invoice(
            supplier_name=supplier_name,
            supplier_gstin=supplier_gstin,
            invoice_number=invoice_number,
            invoice_date=(invoice_date or datetime.today()).date(),
            items=items,
            subtotal=financial_data['subtotal'],
            cgst=financial_data['cgst'],
            sgst=financial_data['sgst'],
            igst=financial_data['igst'],
            grand_total=financial_data['grand_total'],
            raw_text=text,
            confidence=overall_confidence,
        )
    
    @classmethod
    def parse_from_file(cls, pdf_path: str) -> Invoice:
        """Parse invoice directly from PDF file."""
        text, tables = cls._extract_text_multi_engine(pdf_path)
        return cls.parse(text, tables)