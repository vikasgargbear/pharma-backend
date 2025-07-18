"""
Consolidated Pydantic schemas for AASO Pharma ERP
All request/response models in one organized file
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class CustomerType(str, Enum):
    RETAIL = "retail"
    WHOLESALE = "wholesale"
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    PHARMACY = "pharmacy"


class OrderStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    SENT = "sent"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    CANCELLED = "cancelled"


class PaymentMode(str, Enum):
    CASH = "cash"
    CARD = "card"
    UPI = "upi"
    BANK_TRANSFER = "bank_transfer"
    CHEQUE = "cheque"
    CREDIT = "credit"


class GSTType(str, Enum):
    CGST_SGST = "cgst_sgst"  # Same state
    IGST = "igst"            # Inter-state


# ============================================================================
# ORGANIZATION SCHEMAS
# ============================================================================

class OrganizationBase(BaseModel):
    org_name: str
    gstin: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationResponse(OrganizationBase):
    org_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CUSTOMER SCHEMAS
# ============================================================================

class CustomerBase(BaseModel):
    customer_name: str
    contact_person: Optional[str] = None
    phone: str
    alternate_phone: Optional[str] = None
    email: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gstin: Optional[str] = None
    pan_number: Optional[str] = None
    drug_license_number: Optional[str] = None
    customer_type: CustomerType = CustomerType.RETAIL
    credit_limit: Decimal = Field(default=Decimal("0"), ge=0)
    credit_days: int = Field(default=0, ge=0)
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    is_active: bool = True
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    org_id: UUID = Field(default=UUID("12de5e22-eee7-4d25-b3a7-d16d01c6170f"))


class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    gstin: Optional[str] = None
    customer_type: Optional[CustomerType] = None
    credit_limit: Optional[Decimal] = None
    credit_days: Optional[int] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    customer_id: int
    org_id: UUID
    customer_code: str
    total_orders: int = 0
    total_sales: Decimal = Decimal("0")
    outstanding_amount: Decimal = Decimal("0")
    last_order_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PRODUCT SCHEMAS
# ============================================================================

class ProductBase(BaseModel):
    product_name: str
    product_code: Optional[str] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    composition: Optional[str] = None
    strength: Optional[str] = None
    unit_of_measure: str = "pieces"
    hsn_code: Optional[str] = None
    gst_percent: Decimal = Field(default=Decimal("12"), ge=0, le=100)
    drug_schedule: Optional[str] = None
    requires_prescription: bool = False
    is_active: bool = True
    description: Optional[str] = None


class ProductCreate(ProductBase):
    org_id: UUID = Field(default=UUID("12de5e22-eee7-4d25-b3a7-d16d01c6170f"))


class ProductResponse(ProductBase):
    product_id: int
    org_id: UUID
    total_stock: int = 0
    total_batches: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# BATCH SCHEMAS
# ============================================================================

class BatchBase(BaseModel):
    batch_number: str
    manufacturing_date: Optional[date] = None
    expiry_date: date
    mrp: Decimal = Field(ge=0)
    purchase_price: Decimal = Field(ge=0)
    selling_price: Decimal = Field(ge=0)
    quantity_received: int = Field(ge=0)
    supplier_name: Optional[str] = None


class BatchCreate(BatchBase):
    product_id: int
    org_id: UUID = Field(default=UUID("12de5e22-eee7-4d25-b3a7-d16d01c6170f"))


class BatchResponse(BatchBase):
    batch_id: int
    product_id: int
    org_id: UUID
    quantity_available: int
    quantity_sold: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ORDER SCHEMAS
# ============================================================================

class OrderItemBase(BaseModel):
    product_id: int
    batch_id: Optional[int] = None
    quantity: int = Field(gt=0)
    unit_price: Optional[Decimal] = None
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    order_item_id: int
    order_id: int
    product_name: str
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    selling_price: Decimal
    discount_amount: Decimal
    tax_percent: Decimal
    tax_amount: Decimal
    line_total: Decimal

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    customer_id: int
    order_date: date = Field(default_factory=date.today)
    delivery_date: Optional[date] = None
    billing_name: Optional[str] = None
    billing_address: Optional[str] = None
    billing_gstin: Optional[str] = None
    shipping_name: Optional[str] = None
    shipping_address: Optional[str] = None
    shipping_phone: Optional[str] = None
    order_type: str = "sales"
    payment_terms: str = "credit"
    notes: Optional[str] = None
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    delivery_charges: Decimal = Field(default=Decimal("0"), ge=0)
    other_charges: Decimal = Field(default=Decimal("0"))


class OrderCreate(OrderBase):
    org_id: UUID = Field(default=UUID("12de5e22-eee7-4d25-b3a7-d16d01c6170f"))
    items: List[OrderItemCreate]


class OrderResponse(OrderBase):
    order_id: int
    org_id: UUID
    order_number: str
    order_status: OrderStatus
    customer_name: str
    customer_code: str
    customer_phone: str
    subtotal_amount: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal  # Maps to final_amount in DB
    paid_amount: Decimal
    balance_amount: Decimal
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# BILLING SCHEMAS
# ============================================================================

class InvoiceItemBase(BaseModel):
    product_name: str
    hsn_code: Optional[str] = None
    batch_number: Optional[str] = None
    quantity: int
    unit_of_measure: str = "pieces"
    unit_price: Decimal
    discount_amount: Decimal = Decimal("0")
    taxable_amount: Decimal
    gst_percent: Decimal
    cgst_amount: Decimal = Decimal("0")
    sgst_amount: Decimal = Decimal("0")
    igst_amount: Decimal = Decimal("0")
    line_total: Decimal


class InvoiceCreate(BaseModel):
    order_id: int
    invoice_date: date = Field(default_factory=date.today)
    payment_terms_days: int = 30
    notes: Optional[str] = None


class InvoiceResponse(BaseModel):
    invoice_id: int
    order_id: int
    customer_id: int
    invoice_number: str
    invoice_date: date
    due_date: date
    invoice_status: InvoiceStatus
    subtotal_amount: Decimal
    discount_amount: Decimal
    taxable_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    total_tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    balance_amount: Decimal
    gst_type: GSTType
    payment_terms_days: int
    notes: Optional[str] = None
    items: List[InvoiceItemBase]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    invoice_id: int
    amount: Decimal = Field(gt=0)
    payment_date: date = Field(default_factory=date.today)
    payment_mode: PaymentMode
    reference_number: Optional[str] = None
    bank_name: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    payment_id: int
    invoice_id: int
    invoice_number: str
    amount: Decimal
    payment_date: date
    payment_mode: PaymentMode
    reference_number: Optional[str] = None
    bank_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# INVENTORY SCHEMAS
# ============================================================================

class StockLevel(BaseModel):
    product_id: int
    product_name: str
    product_code: str
    total_quantity: int
    available_quantity: int
    allocated_quantity: int
    reorder_level: int
    total_value: Decimal
    batches_count: int
    near_expiry_count: int
    expired_count: int


class InventoryMovement(BaseModel):
    movement_id: int
    batch_id: int
    product_name: str
    batch_number: str
    movement_type: str
    quantity_in: int
    quantity_out: int
    reference_type: str
    reference_id: int
    reason: Optional[str] = None
    movement_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# REPORT SCHEMAS
# ============================================================================

class SalesReport(BaseModel):
    period: str
    total_orders: int
    total_sales: Decimal
    total_tax: Decimal
    top_products: List[Dict[str, Any]]
    top_customers: List[Dict[str, Any]]


class GSTR1Summary(BaseModel):
    period_from: date
    period_to: date
    b2b_supplies: List[Dict[str, Any]]
    b2c_supplies: List[Dict[str, Any]]
    total_taxable_value: Decimal
    total_cgst: Decimal
    total_sgst: Decimal
    total_igst: Decimal
    total_tax: Decimal


class InvoiceSummary(BaseModel):
    total_invoices: int
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    overdue_amount: Decimal
    status_breakdown: Dict[str, int]


# ============================================================================
# GENERIC SCHEMAS
# ============================================================================

class ListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: List[Any]


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# CUSTOMER LEDGER & OUTSTANDING SCHEMAS
# ============================================================================

class CustomerLedgerEntry(BaseModel):
    date: date
    description: str
    reference_type: str
    reference_number: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    balance: Decimal = Decimal("0")

    class Config:
        from_attributes = True


class CustomerLedgerResponse(BaseModel):
    customer_id: int
    customer_name: str
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    opening_balance: Decimal = Decimal("0")
    closing_balance: Decimal = Decimal("0")
    total_debit: Decimal = Decimal("0")
    total_credit: Decimal = Decimal("0")
    entries: List[CustomerLedgerEntry] = []

    class Config:
        from_attributes = True


class OutstandingInvoice(BaseModel):
    invoice_id: int
    invoice_number: str
    invoice_date: date
    due_date: date
    total_amount: Decimal
    paid_amount: Decimal
    balance_amount: Decimal
    days_overdue: int

    class Config:
        from_attributes = True


class CustomerOutstandingResponse(BaseModel):
    customer_id: int
    customer_name: str
    total_outstanding: Decimal = Decimal("0")
    overdue_amount: Decimal = Decimal("0")
    invoices: List[OutstandingInvoice] = []

    class Config:
        from_attributes = True


class PaymentRecord(BaseModel):
    customer_id: int
    payment_date: date = Field(default_factory=date.today)
    amount: Decimal = Field(gt=0)
    payment_mode: PaymentMode
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    allocate_to_invoices: Optional[List[int]] = None

    class Config:
        from_attributes = True


# ============================================================================
# ADDITIONAL SCHEMAS
# ============================================================================

class GSTReportRequest(BaseModel):
    from_date: date
    to_date: date
    report_type: str = "GSTR1"


class GSTR3BSummary(BaseModel):
    period: str
    outward_taxable_supplies: Decimal
    outward_tax: Decimal
    inward_taxable_supplies: Decimal
    input_tax_credit: Decimal
    tax_payable: Decimal


class OrderConfirmation(BaseModel):
    notes: Optional[str] = None


class OrderDelivery(BaseModel):
    delivery_date: date = Field(default_factory=date.today)
    notes: Optional[str] = None


# ============================================================================
# LEGACY COMPATIBILITY (to be removed)
# ============================================================================

# Keep list response name for backward compatibility
CustomerListResponse = ListResponse
ProductListResponse = ListResponse
OrderListResponse = ListResponse