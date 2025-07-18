"""
Comprehensive validation utilities for the Pharma ERP system
Includes input sanitization, format validation, and security checks
"""
import re
import bleach
from email_validator import validate_email, EmailNotValidError


class SecurityValidator:
    """Security-focused validation utilities"""
    
    @staticmethod
    def sanitize_html(value: str) -> str:
        """Remove potentially dangerous HTML tags and attributes"""
        if not value:
            return value
        
        # Allow only safe HTML tags
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
        allowed_attributes = {}
        
        return bleach.clean(value, tags=allowed_tags, attributes=allowed_attributes, strip=True)
    
    @staticmethod
    def sanitize_sql_input(value: str) -> str:
        """Basic SQL injection prevention"""
        if not value:
            return value
        
        # Remove common SQL injection patterns
        dangerous_patterns = [
            r"(\b(union|select|insert|delete|update|drop|create|alter|exec|execute)\b)",
            r"(--|#|/\*|\*/)",
            r"(\b(or|and)\s+\d+\s*=\s*\d+)",
            r"(\bxp_\w+)",
            r"(\bsp_\w+)"
        ]
        
        cleaned_value = value
        for pattern in dangerous_patterns:
            cleaned_value = re.sub(pattern, '', cleaned_value, flags=re.IGNORECASE)
        
        return cleaned_value.strip()
    
    @staticmethod
    def validate_no_script_tags(value: str) -> str:
        """Ensure no script tags are present"""
        if not value:
            return value
        
        # Remove script tags and their content
        script_pattern = r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>'
        cleaned_value = re.sub(script_pattern, '', value, flags=re.IGNORECASE)
        
        # Remove javascript: protocols
        js_pattern = r'javascript:'
        cleaned_value = re.sub(js_pattern, '', cleaned_value, flags=re.IGNORECASE)
        
        return cleaned_value


class PharmaceuticalValidator:
    """Pharmaceutical industry specific validators"""
    
    @staticmethod
    def validate_drug_schedule(schedule: str) -> bool:
        """Validate Indian pharmaceutical drug schedule"""
        valid_schedules = ['G', 'H', 'H1', 'X']
        return schedule.upper() in valid_schedules
    
    @staticmethod
    def validate_hsn_code(hsn_code: str) -> bool:
        """Validate HSN (Harmonized System of Nomenclature) code format"""
        # HSN codes are typically 6-8 digits
        pattern = r'^\d{6,8}$'
        return bool(re.match(pattern, hsn_code))
    
    @staticmethod
    def validate_gst_number(gst_number: str) -> bool:
        """Validate Indian GST number format"""
        # GST format: 22AAAAA0000A1Z5 (15 characters)
        pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$'
        return bool(re.match(pattern, gst_number))
    
    @staticmethod
    def validate_batch_number(batch_number: str) -> bool:
        """Validate pharmaceutical batch number format"""
        # Alphanumeric, 3-20 characters, no special chars except hyphen/underscore
        pattern = r'^[A-Za-z0-9_-]{3,20}$'
        return bool(re.match(pattern, batch_number))
    
    @staticmethod
    def validate_expiry_date(expiry_date: str) -> bool:
        """Validate expiry date format and ensure it's in future"""
        from datetime import datetime, date
        
        try:
            # Support multiple date formats
            date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(expiry_date, fmt).date()
                    return parsed_date > date.today()
                except ValueError:
                    continue
            
            return False
        except Exception:
            return False


class BusinessValidator:
    """Business logic validators"""
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Validate Indian phone number format"""
        # Indian mobile numbers: 10 digits starting with 6-9
        pattern = r'^[6-9]\d{9}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_positive_amount(amount: float) -> bool:
        """Validate that amount is positive and reasonable"""
        return amount > 0 and amount <= 999999.99
    
    @staticmethod
    def validate_percentage(percentage: float) -> bool:
        """Validate percentage is between 0 and 100"""
        return 0 <= percentage <= 100
    
    @staticmethod
    def validate_quantity(quantity: int) -> bool:
        """Validate quantity is positive integer"""
        return isinstance(quantity, int) and quantity > 0


# Pydantic validators that can be used in schemas
def validate_email_format(email: str) -> str:
    """Enhanced email validation"""
    try:
        # Use email-validator library for comprehensive validation
        validated_email = validate_email(email)
        return validated_email.email
    except EmailNotValidError:
        raise ValueError("Invalid email format")


def validate_and_sanitize_text(text: str) -> str:
    """Validate and sanitize text input"""
    if not text:
        return text
    
    # Sanitize HTML and SQL
    sanitized = SecurityValidator.sanitize_html(text)
    sanitized = SecurityValidator.sanitize_sql_input(sanitized)
    sanitized = SecurityValidator.validate_no_script_tags(sanitized)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    return sanitized


def validate_drug_schedule_field(schedule: str) -> str:
    """Validator for drug schedule field"""
    if not PharmaceuticalValidator.validate_drug_schedule(schedule):
        raise ValueError("Invalid drug schedule. Must be one of: G, H, H1, X")
    return schedule.upper()


def validate_gst_number_field(gst_number: str) -> str:
    """Validator for GST number field"""
    if gst_number and not PharmaceuticalValidator.validate_gst_number(gst_number):
        raise ValueError("Invalid GST number format")
    return gst_number


def validate_phone_field(phone: str) -> str:
    """Validator for phone number field"""
    if not BusinessValidator.validate_phone_number(phone):
        raise ValueError("Invalid phone number. Must be 10 digits starting with 6-9")
    return phone


def validate_positive_price(price: float) -> float:
    """Validator for price fields"""
    if not BusinessValidator.validate_positive_amount(price):
        raise ValueError("Price must be positive and less than 999999.99")
    return price