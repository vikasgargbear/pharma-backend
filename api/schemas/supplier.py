"""
Supplier schemas for request/response validation
"""
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from uuid import UUID


class SupplierBase(BaseModel):
    """Base supplier schema with common fields"""
    supplier_name: str = Field(..., min_length=1, max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    company_name: Optional[str] = Field(None, max_length=255)
    supplier_type: str = Field(default="pharmaceutical")
    
    # Contact information
    contact_person: Optional[str] = Field(None, max_length=100)
    phone: str = Field(..., pattern=r'^[6-9]\d{9}$')
    alternate_phone: Optional[str] = Field(None, pattern=r'^[6-9]\d{9}$')
    email: Optional[str] = Field(None, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255, alias="address")
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    pincode: Optional[str] = Field(None, pattern=r'^\d{6}$')
    
    # Regulatory
    gstin: Optional[str] = Field(None, alias="gst_number", pattern=r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$')
    pan_number: Optional[str] = Field(None, pattern=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')
    drug_license_no: Optional[str] = Field(None, alias="drug_license_number", max_length=100)
    
    # Commercial terms
    payment_terms: int = Field(default=30, alias="credit_period_days", ge=0, le=365)
    payment_method: Optional[str] = Field(None, max_length=50)
    
    # Banking
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_no: Optional[str] = Field(None, alias="account_number", max_length=50)
    bank_ifsc_code: Optional[str] = Field(None, alias="ifsc_code", pattern=r'^[A-Z]{4}0[A-Z0-9]{6}$')
    
    # Additional
    notes: Optional[str] = None
    is_active: bool = Field(default=True)
    
    class Config:
        allow_population_by_field_name = True
        
    @validator('phone', 'alternate_phone')
    def clean_phone(cls, v):
        if v:
            # Remove any non-digit characters
            return ''.join(filter(str.isdigit, v))
        return v
    
    @validator('gstin', 'pan_number', 'bank_ifsc_code')
    def uppercase_fields(cls, v):
        if v:
            return v.upper()
        return v


class SupplierCreate(SupplierBase):
    """Schema for creating a new supplier"""
    # org_id will be added by the API based on authentication
    pass


class SupplierUpdate(BaseModel):
    """Schema for updating a supplier"""
    supplier_name: Optional[str] = Field(None, min_length=1, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    supplier_type: Optional[str] = None
    
    # Contact information
    contact_person: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, pattern=r'^[6-9]\d{9}$')
    alternate_phone: Optional[str] = Field(None, pattern=r'^[6-9]\d{9}$')
    email: Optional[str] = Field(None, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    
    # Address
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=1, max_length=100)
    pincode: Optional[str] = Field(None, pattern=r'^\d{6}$')
    
    # Regulatory
    gst_number: Optional[str] = Field(None, pattern=r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$')
    pan_number: Optional[str] = Field(None, pattern=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')
    drug_license_number: Optional[str] = Field(None, max_length=100)
    
    # Commercial terms
    credit_period_days: Optional[int] = Field(None, ge=0, le=365)
    payment_method: Optional[str] = Field(None, max_length=50)
    
    # Banking
    bank_name: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=50)
    ifsc_code: Optional[str] = Field(None, pattern=r'^[A-Z]{4}0[A-Z0-9]{6}$')
    
    # Additional
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    
    class Config:
        allow_population_by_field_name = True


class SupplierResponse(BaseModel):
    """Schema for supplier response"""
    supplier_id: int
    org_id: UUID
    supplier_code: str
    supplier_name: str
    company_name: Optional[str]
    supplier_type: str
    
    # Contact information
    contact_person: Optional[str]
    phone: str
    alternate_phone: Optional[str]
    email: Optional[str]
    
    # Address
    address: Optional[str]
    city: str
    state: str
    pincode: Optional[str]
    
    # Regulatory
    gst_number: Optional[str]
    pan_number: Optional[str]
    drug_license_number: Optional[str]
    
    # Commercial terms
    credit_period_days: int
    payment_terms: Optional[str]
    payment_method: Optional[str]
    
    # Banking
    bank_name: Optional[str]
    account_number: Optional[str]
    ifsc_code: Optional[str]
    
    # Business metrics
    total_purchases: Decimal
    outstanding_amount: Decimal
    last_purchase_date: Optional[date]
    
    # Metadata
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class SupplierListResponse(BaseModel):
    """Response for supplier list with pagination"""
    suppliers: list[SupplierResponse]
    total: int
    page: int
    per_page: int
    
    
class SupplierProductResponse(BaseModel):
    """Products supplied by a supplier"""
    product_id: int
    product_name: str
    product_code: str
    last_purchase_rate: Decimal
    last_purchase_date: Optional[date]
    total_quantity_purchased: Decimal