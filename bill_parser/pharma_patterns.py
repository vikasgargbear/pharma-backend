"""
Comprehensive pharmaceutical industry patterns for invoice parsing.
Contains 50+ specialized regex patterns for Indian pharmaceutical companies.
"""
import re
from typing import Dict, List, Tuple

# Pharmaceutical Company Name Patterns
PHARMA_COMPANY_PATTERNS = [
    # Major Indian Pharmaceutical Companies
    r"sun\s+pharma(?:ceuticals)?",
    r"dr\.?\s*reddy[\'s]*\s*(?:lab|laboratories)?",
    r"cipla\s*(?:ltd|limited)?",
    r"lupin\s*(?:ltd|limited)?",
    r"aurobindo\s+pharma",
    r"divi[\'s]*\s*(?:lab|laboratories)",
    r"biocon\s*(?:ltd|limited)?",
    r"cadila\s+(?:healthcare|pharma)",
    r"torrent\s+(?:pharma|pharmaceuticals)",
    r"glenmark\s+(?:pharma|pharmaceuticals)",
    r"alkem\s+(?:lab|laboratories)",
    r"abbott\s+(?:india|healthcare)",
    r"pfizer\s*(?:ltd|limited)?",
    r"novartis\s*(?:india)?",
    r"gsk\s*(?:pharma|pharmaceuticals)?",
    r"sanofi\s*(?:india|aventis)?",
    r"mankind\s+pharma",
    r"emcure\s+(?:pharma|pharmaceuticals)",
    r"intas\s+(?:pharma|pharmaceuticals)",
    r"zydus\s+(?:cadila|healthcare)",
    
    # Generic pharmaceutical company patterns
    r"\w+\s+(?:pharma|pharmaceuticals|healthcare|labs?|laboratories)",
    r"\w+\s+(?:life\s+sciences|biotech|medicines)",
    r"(?:pharma|bio|medi)\w*\s+(?:ltd|limited|pvt|private)",
]

# Product/Drug Name Patterns
DRUG_NAME_PATTERNS = [
    # Common drug formulations
    r"(?:paracetamol|acetaminophen)\s*(?:\d+\s*mg)?",
    r"(?:ibuprofen|brufen)\s*(?:\d+\s*mg)?",
    r"(?:amoxicillin|augmentin)\s*(?:\d+\s*mg)?",
    r"(?:azithromycin|zithromax)\s*(?:\d+\s*mg)?",
    r"(?:metformin|glucophage)\s*(?:\d+\s*mg)?",
    r"(?:omeprazole|pantoprazole)\s*(?:\d+\s*mg)?",
    r"(?:amlodipine|norvasc)\s*(?:\d+\s*mg)?",
    r"(?:atorvastatin|lipitor)\s*(?:\d+\s*mg)?",
    r"(?:clopidogrel|plavix)\s*(?:\d+\s*mg)?",
    r"(?:losartan|cozaar)\s*(?:\d+\s*mg)?",
    
    # Antibiotic patterns
    r"(?:ampi|amoxy|cefi|cipro|levo)\w*\s*(?:\d+\s*mg)?",
    r"\w*cillin\s*(?:\d+\s*mg)?",
    r"\w*mycin\s*(?:\d+\s*mg)?",
    r"\w*floxacin\s*(?:\d+\s*mg)?",
    
    # Vitamin and supplement patterns
    r"(?:vitamin|vit)\s*[a-z]\d*\s*(?:\d+\s*(?:mg|iu))?",
    r"(?:calcium|iron|zinc|magnesium)\s*(?:\d+\s*mg)?",
    r"(?:omega|fish\s+oil)\s*(?:\d+\s*mg)?",
    r"(?:multivitamin|multi\s+vitamin)",
    
    # Generic drug patterns
    r"\w+\s*(?:tablet|tab|capsule|cap|syrup|injection|inj)",
    r"\w+\s*(?:\d+\s*(?:mg|ml|gm|mcg))",
]

# Batch Number Patterns
BATCH_PATTERNS = [
    r"(?:batch|lot)\s*(?:no\.?|number)?\s*:?\s*([A-Z0-9]{3,15})",
    r"\b(B\d{6,10})\b",
    r"\b(LOT\d{3,8})\b",
    r"\b([A-Z]{2}\d{4,8})\b",
    r"\b(\d{6}[A-Z]{2,4})\b",
    r"(?:mfg|manufacturing)\s*(?:no\.?|number)?\s*:?\s*([A-Z0-9]{3,15})",
]

# Expiry Date Patterns
EXPIRY_PATTERNS = [
    r"(?:exp|expiry|expires?)\s*(?:date)?\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    r"(?:exp|expiry)\s*:?\s*(\d{1,2}\s+\w{3}\s+\d{2,4})",
    r"(?:valid\s+(?:up\s+)?to|until)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    r"\b(exp\s*\d{1,2}[/-]\d{2,4})\b",
    r"(?:shelf\s+life|use\s+before)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
]

# Manufacturing Date Patterns
MFG_DATE_PATTERNS = [
    r"(?:mfg|manufactured|made)\s*(?:date|on)?\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    r"(?:production|prod)\s*(?:date)?\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    r"(?:dom|date\s+of\s+(?:manufacture|production))\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
]

# HSN Code Patterns (Pharmaceutical specific)
HSN_PHARMA_PATTERNS = [
    r"\b(3003\d{4})\b",  # Medicaments for therapeutic/prophylactic uses
    r"\b(3004\d{4})\b",  # Medicaments for therapeutic/prophylactic uses
    r"\b(2936\d{4})\b",  # Vitamins and their derivatives
    r"\b(2937\d{4})\b",  # Hormones and derivatives
    r"\b(2939\d{4})\b",  # Alkaloids and their derivatives
    r"\b(2941\d{4})\b",  # Antibiotics
    r"\b(1302\d{4})\b",  # Vegetable saps and extracts
    r"\b(2106\d{4})\b",  # Food preparations
]

# Drug License Patterns (State-wise)
DRUG_LICENSE_PATTERNS = [
    # Format: State Code + Number + Alpha
    r"\b(DL\s*[A-Z]{2}\s*\d{2,6}[A-Z]?)\b",
    r"\b([A-Z]{2}[/-]?\d{2}[/-]?\d{4,6}[A-Z]?)\b",
    r"(?:drug\s+lic(?:ence|ense)?|dl)\s*(?:no\.?|number)?\s*:?\s*([A-Z0-9/-]{5,15})",
    r"(?:retail|wholesale)\s+drug\s+lic(?:ence|ense)?\s*:?\s*([A-Z0-9/-]{5,15})",
    
    # Specific state patterns
    r"\b(MH[/-]?\d{2}[/-]?\d{6}[A-Z]?)\b",  # Maharashtra
    r"\b(DL[/-]?\d{2}[/-]?\d{6}[A-Z]?)\b",  # Delhi
    r"\b(KA[/-]?\d{2}[/-]?\d{6}[A-Z]?)\b",  # Karnataka
    r"\b(GJ[/-]?\d{2}[/-]?\d{6}[A-Z]?)\b",  # Gujarat
    r"\b(TN[/-]?\d{2}[/-]?\d{6}[A-Z]?)\b",  # Tamil Nadu
    r"\b(UP[/-]?\d{2}[/-]?\d{6}[A-Z]?)\b",  # Uttar Pradesh
]

# Pack Size Patterns
PACK_SIZE_PATTERNS = [
    r"(\d+)\s*x\s*(\d+)",  # 10x10, 5x14, etc.
    r"(\d+)\s*(?:strips?|blisters?)",
    r"(\d+)\s*(?:tablets?|caps?|capsules?)",
    r"(\d+)\s*ml\s*(?:bottle|vial)",
    r"(\d+)\s*gm?\s*(?:tube|jar)",
    r"pack\s+of\s+(\d+)",
    r"box\s+of\s+(\d+)",
]

# Strength/Dosage Patterns
STRENGTH_PATTERNS = [
    r"(\d+(?:\.\d+)?)\s*(mg|mcg|gm?|ml|iu|units?)",
    r"(\d+(?:\.\d+)?)\s*milligrams?",
    r"(\d+(?:\.\d+)?)\s*micrograms?",
    r"(\d+(?:\.\d+)?)\s*(?:milli)?liters?",
    r"(\d+(?:\.\d+)?)\s*(?:international\s+)?units?",
]

# Price/Amount Patterns (India specific)
PRICE_PATTERNS = [
    r"(?:rs\.?|rupees?|₹)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
    r"(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:rs\.?|rupees?|₹)",
    r"(?:mrp|max\.?\s*retail\s*price)\s*:?\s*(?:rs\.?|₹)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
    r"(?:rate|price|amount)\s*:?\s*(?:rs\.?|₹)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
]

# Tax Patterns (GST specific)
TAX_PATTERNS = [
    r"(?:cgst|central\s+gst)\s*@?\s*(\d+(?:\.\d+)?)\s*%",
    r"(?:sgst|state\s+gst)\s*@?\s*(\d+(?:\.\d+)?)\s*%",
    r"(?:igst|integrated\s+gst)\s*@?\s*(\d+(?:\.\d+)?)\s*%",
    r"(?:gst|tax)\s*@?\s*(\d+(?:\.\d+)?)\s*%",
    r"(?:cgst|sgst|igst)\s*(?:amount)?\s*:?\s*(?:rs\.?|₹)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
]

# Discount Patterns
DISCOUNT_PATTERNS = [
    r"(?:discount|disc\.?)\s*@?\s*(\d+(?:\.\d+)?)\s*%",
    r"(?:trade\s+)?discount\s*:?\s*(?:rs\.?|₹)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
    r"(?:less|minus)\s*:?\s*(?:rs\.?|₹)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
]

# Address Patterns (for supplier identification)
ADDRESS_PATTERNS = [
    r"(?:plot|survey)\s+(?:no\.?)?\s*(\d+[a-z]?)",
    r"(?:building|bldg\.?)\s+(?:no\.?)?\s*(\w+)",
    r"(?:floor|flr\.?)\s+(\d+(?:st|nd|rd|th)?)",
    r"pin\s*(?:code)?\s*:?\s*(\d{6})",
    r"\b(\d{6})\b",  # PIN code
    r"(?:phone|ph\.?|tel\.?|mobile|mob\.?)\s*:?\s*([\d\s\-\+\(\)]{10,15})",
]

# Supplier Contact Patterns
CONTACT_PATTERNS = [
    r"(?:phone|ph\.?|tel\.?)\s*:?\s*([\d\s\-\+\(\)]{10,15})",
    r"(?:mobile|mob\.?|cell)\s*:?\s*([\d\s\-\+\(\)]{10,15})",
    r"(?:email|e-mail)\s*:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
    r"(?:website|web|www)\s*:?\s*((?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
    r"(?:fax)\s*:?\s*([\d\s\-\+\(\)]{10,15})",
]

# Invoice Number Patterns (Pharmaceutical specific)
INVOICE_PATTERNS = [
    r"(?:invoice|bill)\s*(?:no\.?|number|#)\s*:?\s*([A-Z]{2,4}\d{4,8})",
    r"(?:invoice|bill)\s*(?:no\.?|number|#)\s*:?\s*(INV[A-Z0-9/-]{3,12})",
    r"(?:invoice|bill)\s*(?:no\.?|number|#)\s*:?\s*([A-Z0-9/-]{5,15})",
    r"\b(SI\d{6,10})\b",  # Sales Invoice
    r"\b(PI\d{6,10})\b",  # Purchase Invoice
    r"\b(TI\d{6,10})\b",  # Tax Invoice
]


class PharmaPatternMatcher:
    """Advanced pattern matcher for pharmaceutical invoices."""
    
    def __init__(self):
        self.company_patterns = [re.compile(p, re.IGNORECASE) for p in PHARMA_COMPANY_PATTERNS]
        self.drug_patterns = [re.compile(p, re.IGNORECASE) for p in DRUG_NAME_PATTERNS]
        self.batch_patterns = [re.compile(p, re.IGNORECASE) for p in BATCH_PATTERNS]
        self.expiry_patterns = [re.compile(p, re.IGNORECASE) for p in EXPIRY_PATTERNS]
        self.hsn_patterns = [re.compile(p) for p in HSN_PHARMA_PATTERNS]
        self.license_patterns = [re.compile(p, re.IGNORECASE) for p in DRUG_LICENSE_PATTERNS]
        
    def is_pharma_company(self, text: str) -> Tuple[bool, float]:
        """Check if text contains pharmaceutical company indicators."""
        matches = 0
        total_patterns = len(self.company_patterns)
        
        for pattern in self.company_patterns:
            if pattern.search(text):
                matches += 1
                
        confidence = matches / total_patterns if total_patterns > 0 else 0.0
        return matches > 0, confidence
    
    def extract_drug_names(self, text: str) -> List[Tuple[str, float]]:
        """Extract potential drug names with confidence scores."""
        results = []
        
        for pattern in self.drug_patterns:
            matches = pattern.findall(text)
            for match in matches:
                confidence = 0.7 if any(keyword in match.lower() 
                                      for keyword in ['tablet', 'capsule', 'mg', 'ml']) else 0.5
                results.append((match, confidence))
                
        return results
    
    def extract_batch_numbers(self, text: str) -> List[Tuple[str, float]]:
        """Extract batch numbers with confidence."""
        results = []
        
        for pattern in self.batch_patterns:
            matches = pattern.findall(text)
            for match in matches:
                confidence = 0.8 if 'batch' in text.lower() or 'lot' in text.lower() else 0.6
                results.append((match, confidence))
                
        return results
    
    def extract_expiry_dates(self, text: str) -> List[Tuple[str, float]]:
        """Extract expiry dates with confidence."""
        results = []
        
        for pattern in self.expiry_patterns:
            matches = pattern.findall(text)
            for match in matches:
                confidence = 0.9 if 'exp' in text.lower() else 0.7
                results.append((match, confidence))
                
        return results
    
    def validate_hsn_pharma(self, hsn: str) -> Tuple[bool, float]:
        """Validate if HSN code is pharmaceutical."""
        if not hsn:
            return False, 0.0
            
        for pattern in self.hsn_patterns:
            if pattern.match(hsn):
                return True, 0.9
                
        # Check if starts with pharmaceutical HSN prefixes
        pharma_prefixes = ['3003', '3004', '2936', '2937', '2939', '2941']
        if any(hsn.startswith(prefix) for prefix in pharma_prefixes):
            return True, 0.8
            
        return False, 0.0
    
    def extract_drug_licenses(self, text: str) -> List[Tuple[str, float]]:
        """Extract drug license numbers."""
        results = []
        
        for pattern in self.license_patterns:
            matches = pattern.findall(text)
            for match in matches:
                confidence = 0.9 if 'drug' in text.lower() and 'lic' in text.lower() else 0.7
                results.append((match, confidence))
                
        return results


# Quick access functions
def get_all_patterns() -> Dict[str, List[str]]:
    """Return all patterns organized by category."""
    return {
        'companies': PHARMA_COMPANY_PATTERNS,
        'drugs': DRUG_NAME_PATTERNS,
        'batches': BATCH_PATTERNS,
        'expiry': EXPIRY_PATTERNS,
        'hsn': HSN_PHARMA_PATTERNS,
        'licenses': DRUG_LICENSE_PATTERNS,
        'pack_sizes': PACK_SIZE_PATTERNS,
        'strengths': STRENGTH_PATTERNS,
        'prices': PRICE_PATTERNS,
        'taxes': TAX_PATTERNS,
        'discounts': DISCOUNT_PATTERNS,
        'addresses': ADDRESS_PATTERNS,
        'contacts': CONTACT_PATTERNS,
        'invoices': INVOICE_PATTERNS,
    }

def get_pattern_count() -> int:
    """Return total number of patterns."""
    all_patterns = get_all_patterns()
    return sum(len(patterns) for patterns in all_patterns.values())