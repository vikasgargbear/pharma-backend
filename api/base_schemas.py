"""
Clean Pydantic schemas that work with the database
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import uuid

# Default org_id for now (from existing organization)
DEFAULT_ORG_ID = "12de5e22-eee7-4d25-b3a7-d16d01c6170f"

class ProductBase(BaseModel):
    """Base product schema with all fields"""
    product_code: str
    product_name: str
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    manufacturer: Optional[str] = None
    manufacturer_code: Optional[str] = None
    
    # Categories
    category: Optional[str] = None
    subcategory: Optional[str] = None
    category_id: Optional[int] = None
    product_type_id: Optional[int] = None
    
    # UOM
    base_uom_code: Optional[str] = "PIECE"
    purchase_uom_code: Optional[str] = None
    sale_uom_code: Optional[str] = None
    display_uom_code: Optional[str] = None
    allow_loose_units: Optional[bool] = False
    
    # Regulatory
    hsn_code: Optional[str] = None
    drug_schedule: Optional[str] = None
    prescription_required: Optional[bool] = False
    is_controlled_substance: Optional[bool] = False
    
    # Pricing
    purchase_price: Optional[Decimal] = Decimal("0")
    sale_price: Optional[Decimal] = Decimal("0")
    mrp: Optional[Decimal] = Decimal("0")
    trade_discount_percent: Optional[Decimal] = Decimal("0")
    
    # Tax
    gst_percent: Optional[Decimal] = Decimal("12")
    cgst_percent: Optional[Decimal] = Decimal("6")
    sgst_percent: Optional[Decimal] = Decimal("6")
    igst_percent: Optional[Decimal] = Decimal("12")
    tax_category: Optional[str] = "standard"
    
    # Stock
    minimum_stock_level: Optional[int] = 0
    maximum_stock_level: Optional[int] = None
    reorder_level: Optional[int] = None
    reorder_quantity: Optional[int] = None
    
    # Pack info
    pack_size: Optional[str] = None
    pack_details: Optional[dict] = None
    
    # Barcode
    barcode: Optional[str] = None
    barcode_type: Optional[str] = "EAN13"
    alternate_barcodes: Optional[List[str]] = None
    
    # Storage
    storage_location: Optional[str] = None
    shelf_life_days: Optional[int] = None
    
    # Metadata
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    search_keywords: Optional[List[str]] = None
    category_path: Optional[str] = None
    
    # Status
    is_active: Optional[bool] = True
    is_discontinued: Optional[bool] = False
    is_narcotic: Optional[bool] = False
    requires_cold_chain: Optional[bool] = False
    is_habit_forming: Optional[bool] = False
    
    # Additional
    temperature_range: Optional[str] = None
    therapeutic_category: Optional[str] = None
    salt_composition: Optional[str] = None
    strength: Optional[str] = None
    pack_type: Optional[str] = None

class ProductCreate(ProductBase):
    """Schema for creating a product"""
    org_id: Optional[str] = Field(default=DEFAULT_ORG_ID)

class ProductUpdate(BaseModel):
    """Schema for updating a product - all fields optional"""
    product_name: Optional[str] = None
    generic_name: Optional[str] = None
    manufacturer: Optional[str] = None
    hsn_code: Optional[str] = None
    mrp: Optional[Decimal] = None
    gst_percent: Optional[Decimal] = None
    pack_size: Optional[str] = None
    is_active: Optional[bool] = None
    # Add other fields as needed

class ProductResponse(ProductBase):
    """Schema for product responses"""
    product_id: int
    org_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Simplified schemas for common operations
class ProductQuickCreate(BaseModel):
    """Minimal fields to create a product"""
    product_code: str
    product_name: str
    mrp: Optional[Decimal] = Decimal("0")
    hsn_code: Optional[str] = "30049099"
    gst_percent: Optional[Decimal] = Decimal("12")


# Additional schemas to prevent import errors in crud.py
class CustomerCreate(BaseModel):
    customer_name: str
    customer_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class CustomerBase(CustomerCreate):
    customer_id: Optional[int] = None

class Customer(CustomerBase):
    customer_id: int
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    customer_id: int
    order_date: Optional[str] = None
    total_amount: Optional[Decimal] = Decimal("0")

class OrderItemCreate(BaseModel):
    order_id: Optional[int] = None
    product_id: int
    quantity: int
    price: Decimal

class BatchCreate(BaseModel):
    product_id: int
    batch_number: str
    expiry_date: str
    quantity: Optional[int] = 0

class PaymentCreate(BaseModel):
    customer_id: int
    amount: Decimal
    payment_date: Optional[str] = None

class PaymentAllocationCreate(BaseModel):
    payment_id: int
    order_id: int
    amount: Decimal

class CustomerAdvancePaymentCreate(BaseModel):
    customer_id: int
    amount: Decimal

class InventoryMovementCreate(BaseModel):
    product_id: int
    movement_type: str
    quantity: int

class SalesReturnCreate(BaseModel):
    order_id: int
    product_id: int
    quantity: int
    reason: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class SupplierCreate(BaseModel):
    supplier_name: str
    supplier_code: Optional[str] = None

class PurchaseCreate(BaseModel):
    supplier_id: int
    purchase_date: Optional[str] = None

class PurchaseItemCreate(BaseModel):
    purchase_id: Optional[int] = None
    product_id: int
    quantity: int
    price: Decimal

# For batch and payments routers
class BatchBase(BaseModel):
    product_id: int
    batch_number: str
    mfg_date: Optional[str] = None
    expiry_date: str
    purchase_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    quantity_available: int
    location: Optional[str] = None

class Batch(BatchBase):
    batch_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Add any other missing schemas as needed

# Compliance schemas
class ComplianceDashboard(BaseModel):
    total_licenses: int = 0
    expiring_soon: int = 0
    expired: int = 0
    drug_license_status: Optional[str] = "valid"

class TaxEntryCreate(BaseModel):
    entry_type: str
    amount: Decimal
    tax_amount: Optional[Decimal] = None
    description: Optional[str] = None