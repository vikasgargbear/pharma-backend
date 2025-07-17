from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Union, List, Dict
from datetime import datetime, date

# ---------------- Products ----------------
class ProductBase(BaseModel):
    org_id: Optional[str] = Field("550e8400-e29b-41d4-a716-446655440000", example="550e8400-e29b-41d4-a716-446655440000")
    product_code: str = Field(..., example="PARA500")
    product_name: str = Field(..., example="Paracetamol 500mg")
    generic_name: Optional[str] = Field(None, example="Paracetamol")
    brand_name: Optional[str] = Field(None, example="Crocin")
    manufacturer: Optional[str] = Field(None, example="GSK")
    manufacturer_code: Optional[str] = Field(None, example="GSK001")
    category: Optional[str] = Field(None, example="medication")
    subcategory: Optional[str] = Field(None, example="fever")
    category_id: Optional[int] = Field(None, example=1)
    product_type_id: Optional[int] = Field(None, example=1)
    base_uom_code: Optional[str] = Field("PIECE", example="PIECE")
    purchase_uom_code: Optional[str] = Field(None, example="BOX")
    sale_uom_code: Optional[str] = Field(None, example="STRIP")
    display_uom_code: Optional[str] = Field(None, example="STRIP")
    allow_loose_units: Optional[bool] = Field(False, example=False)
    hsn_code: Optional[str] = Field(None, example="3004")
    drug_schedule: Optional[str] = Field(None, example="H")
    prescription_required: Optional[bool] = Field(False, example=True)
    is_controlled_substance: Optional[bool] = Field(False, example=False)
    purchase_price: Optional[float] = Field(None, example=10.0)
    sale_price: Optional[float] = Field(None, example=18.0)
    mrp: Optional[float] = Field(None, example=20.0)
    trade_discount_percent: Optional[float] = Field(None, example=10.0)
    gst_percent: Optional[float] = Field(None, example=12.0)
    cgst_percent: Optional[float] = Field(None, example=6.0)
    sgst_percent: Optional[float] = Field(None, example=6.0)
    igst_percent: Optional[float] = Field(None, example=0.0)
    tax_category: Optional[str] = Field("standard", example="standard")
    minimum_stock_level: Optional[int] = Field(None, example=100)
    maximum_stock_level: Optional[int] = Field(None, example=1000)
    reorder_level: Optional[int] = Field(None, example=200)
    reorder_quantity: Optional[int] = Field(None, example=500)
    pack_size: Optional[str] = Field(None, example="10 tablets")
    pack_details: Optional[dict] = Field(None, example={"strips": 10, "tablets_per_strip": 10})
    barcode: Optional[str] = Field(None, example="8901030865278")
    barcode_type: Optional[str] = Field("EAN13", example="EAN13")
    alternate_barcodes: Optional[List[str]] = Field(None, example=["1234567890123"])
    storage_location: Optional[str] = Field(None, example="A1-B2")
    shelf_life_days: Optional[int] = Field(None, example=730)
    notes: Optional[str] = Field(None, example="Store in cool dry place")
    tags: Optional[List[str]] = Field(None, example=["fever", "pain-relief"])
    search_keywords: Optional[List[str]] = Field(None, example=["paracetamol", "fever", "headache"])
    category_path: Optional[str] = Field(None, example="medication/fever")
    is_active: Optional[bool] = Field(True, example=True)
    is_discontinued: Optional[bool] = Field(False, example=False)
    created_by: Optional[int] = Field(None, example=1)
    is_narcotic: Optional[bool] = Field(False, example=False)
    requires_cold_chain: Optional[bool] = Field(False, example=False)
    temperature_range: Optional[str] = Field(None, example="2-8°C")
    is_habit_forming: Optional[bool] = Field(False, example=False)
    therapeutic_category: Optional[str] = Field(None, example="Analgesic")
    salt_composition: Optional[str] = Field(None, example="Paracetamol 500mg")
    strength: Optional[str] = Field(None, example="500mg")
    pack_type: Optional[str] = Field(None, example="Strip")

class ProductCreate(ProductBase):
    org_id: Optional[str] = Field(None, example="org-123")  # Make org_id optional for creation

class Product(ProductBase):
    product_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ---------------- Batches ----------------
class BatchBase(BaseModel):
    product_id: int
    batch_number: str
    mfg_date: Optional[date]  # Match database column name
    expiry_date: date
    purchase_price: Optional[float] = None
    selling_price: Optional[float] = None
    quantity_available: int
    location: Optional[str] = None

class BatchCreate(BatchBase):
    pass

class Batch(BatchBase):
    batch_id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ---------------- Customers ----------------
class CustomerBase(BaseModel):
    customer_name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    gst_number: Optional[str] = None
    customer_type: Optional[str] = None
    credit_limit: Optional[float] = None
    payment_terms: Optional[int] = None
    # New wholesale business fields
    drug_license_number: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    bank_branch: Optional[str] = None
    credit_terms_days: Optional[int] = Field(30, example=30)
    credit_used: Optional[float] = Field(0.0, example=0.0)
    is_active: Optional[bool] = Field(True, example=True)

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    customer_id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ---------------- Orders ----------------
class OrderBase(BaseModel):
    customer_id: int
    mr_id: Optional[int] = None  # Medical Representative
    order_date: Optional[datetime]
    
    # Invoice details
    invoice_no: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    
    # Financial calculations
    gross_amount: float
    discount: float
    tax_amount: float
    final_amount: float
    round_off: Optional[float] = Field(0.0, example=0.0)
    
    # Transport and logistics
    transport_charges: Optional[float] = Field(0.0, example=0.0)
    transport_mode: Optional[str] = None
    
    # Payment details
    payment_status: Optional[str] = Field("pending")
    payment_mode: Optional[str] = Field("CASH")
    
    # Status and metadata
    status: Optional[str] = Field("placed")
    notes: Optional[str] = None

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    order_id: int
    class Config:
        from_attributes = True


# ---------------- Order Items ----------------
class OrderItemBase(BaseModel):
    order_id: int
    batch_id: int
    quantity: int
    unit_price: float
    total_price: float

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    order_item_id: int
    class Config:
        from_attributes = True


# ---------------- Inventory Movements ----------------
class InventoryMovementBase(BaseModel):
    batch_id: int
    movement_type: str
    quantity: int
    movement_date: Optional[datetime]
    reference: Optional[str]

class InventoryMovementCreate(InventoryMovementBase):
    pass

class InventoryMovement(InventoryMovementBase):
    movement_id: int
    class Config:
        from_attributes = True


# ---------------- Payments ----------------
class PaymentBase(BaseModel):
    order_id: int
    amount: float
    payment_mode: str
    payment_date: Optional[datetime]
    reference_number: Optional[str]
    remarks: Optional[str]

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    payment_id: int
    class Config:
        from_attributes = True


# ---------------- Sales Returns ----------------
class SalesReturnBase(BaseModel):
    order_id: int
    return_date: Optional[datetime]
    reason: Optional[str]
    refund_amount: float

class SalesReturnCreate(SalesReturnBase):
    pass

class SalesReturn(SalesReturnBase):
    return_id: int
    class Config:
        from_attributes = True


# ---------------- Users ----------------
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: Optional[str]
    password_hash: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ---------------- Purchases ----------------
class PurchaseBase(BaseModel):
    supplier_id: Optional[int] = None  # Link to supplier
    supplier_name: str  # Keep for backward compatibility
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    total_amount: float
    discount: Optional[float] = Field(0.0, example=0.0)
    tax_amount: Optional[float] = Field(0.0, example=0.0)
    final_amount: Optional[float] = None
    payment_status: Optional[str] = Field("pending")
    status: Optional[str] = Field("received")

class PurchaseCreate(PurchaseBase):
    pass

class Purchase(PurchaseBase):
    purchase_id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ---------------- Purchase Items ----------------
class PurchaseItemBase(BaseModel):
    purchase_id: int
    product_id: int
    batch_number: str
    expiry_date: date
    quantity: int
    purchase_price: float

class PurchaseItemCreate(PurchaseItemBase):
    pass

class PurchaseItem(PurchaseItemBase):
    purchase_item_id: int
    class Config:
        from_attributes = True


# ---------------- Tax Entries ----------------
class TaxEntryBase(BaseModel):
    transaction_type: str
    # Foreign key connections
    order_id: Optional[int] = None  # For sales
    purchase_id: Optional[int] = None  # For purchases
    return_id: Optional[int] = None  # For returns
    
    # Tax details
    tax_type: str  # CGST, SGST, IGST
    tax_percent: float
    tax_amount: float
    taxable_amount: Optional[float] = None  # Base amount
    
    # GST specific
    gst_type: Optional[str] = None  # intra-state, inter-state
    hsn_code: Optional[str] = None

class TaxEntryCreate(TaxEntryBase):
    pass

class TaxEntry(TaxEntryBase):
    tax_entry_id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ---------------- Vendor Payments ----------------
class VendorPaymentBase(BaseModel):
    purchase_id: int
    supplier_name: str
    amount_paid: float
    payment_date: Optional[datetime]
    payment_mode: Optional[str]
    remarks: Optional[str]

class VendorPaymentCreate(VendorPaymentBase):
    pass

class VendorPayment(VendorPaymentBase):
    vendor_payment_id: int
    class Config:
        from_attributes = True


# ---------------- Journal Entries ----------------
class JournalEntryBase(BaseModel):
    entry_date: Optional[date] = None
    
    # Reference connections
    transaction_type: Optional[str] = None  # sale, purchase, payment, expense
    order_id: Optional[int] = None
    purchase_id: Optional[int] = None
    payment_id: Optional[int] = None
    vendor_payment_id: Optional[int] = None
    
    # Accounting details
    account_name: str
    account_type: Optional[str] = None  # asset, liability, income, expense, equity
    debit_amount: float
    credit_amount: float
    
    # Additional info
    reference: Optional[str] = None
    remarks: Optional[str] = None
    voucher_number: Optional[str] = None

class JournalEntryCreate(JournalEntryBase):
    pass

class JournalEntry(JournalEntryBase):
    entry_id: int
    class Config:
        from_attributes = True


# ---------------- Cart ----------------
class CartBase(BaseModel):
    user_id: str  # Using string for user_id to support both numeric IDs and auth user IDs

class CartCreate(CartBase):
    pass

class Cart(CartBase):
    cart_id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


# ---------------- Cart Items ----------------
class CartItemBase(BaseModel):
    cart_id: int
    product_id: int
    batch_id: Optional[int] = None
    quantity: int = 1

class CartItemCreate(CartItemBase):
    pass

class CartItem(CartItemBase):
    cart_item_id: int
    added_at: datetime

    class Config:
        from_attributes = True

# ---------------- Suppliers ----------------
class SupplierBase(BaseModel):
    supplier_name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = Field("India", example="India")
    gst_number: Optional[str] = None
    drug_license_number: str  # Required for pharma suppliers
    
    # Banking details
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    bank_branch: Optional[str] = None
    
    # Business terms
    credit_terms_days: Optional[int] = Field(30, example=30)
    credit_limit: Optional[float] = None
    credit_used: Optional[float] = Field(0.0, example=0.0)
    
    # Supplier classification
    supplier_type: Optional[str] = None  # Manufacturer, Distributor, Wholesaler
    preferred_supplier: Optional[bool] = Field(False, example=False)
    minimum_order_value: Optional[float] = None
    
    # Status and dates
    is_active: Optional[bool] = Field(True, example=True)
    onboarding_date: Optional[date] = None

class SupplierCreate(SupplierBase):
    pass

class Supplier(SupplierBase):
    supplier_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Medical Representatives ----------------
class MedicalRepresentativeBase(BaseModel):
    mr_name: str
    employee_id: Optional[str] = None
    company: Optional[str] = None  # Pharmaceutical company they represent
    phone: Optional[str] = None
    email: Optional[str] = None
    territory: Optional[str] = None  # Area they cover
    
    # Commission and incentives
    commission_rate: Optional[float] = None  # Percentage
    target_monthly: Optional[float] = None  # Monthly sales target
    
    # Professional details
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    joining_date: Optional[date] = None
    
    # Status
    is_active: Optional[bool] = Field(True, example=True)

class MedicalRepresentativeCreate(MedicalRepresentativeBase):
    pass

class MedicalRepresentative(MedicalRepresentativeBase):
    mr_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Enhanced Regulatory Licenses ----------------
class RegulatoryLicenseBase(BaseModel):
    # FIXED: Now properly connected to business entities
    entity_type: str  # company, supplier, customer
    entity_id: Optional[int] = None  # References supplier_id or customer_id
    company_license: Optional[bool] = Field(False, example=False)  # True for company's own licenses
    
    license_type: str  # Drug License, GST, Shop License, etc.
    license_number: str
    license_name: Optional[str] = None  # Full license name/description
    
    # Issuing authority details
    issuing_authority: str
    issuing_state: Optional[str] = None
    issuing_district: Optional[str] = None
    
    # Dates
    issue_date: date
    expiry_date: date
    renewal_due_date: Optional[date] = None  # Calculated field for reminders
    
    # Renewal management
    renewal_reminder_days: Optional[int] = Field(60, example=60)  # Days before expiry to remind
    auto_renewal_enabled: Optional[bool] = Field(False, example=False)
    renewal_fee: Optional[float] = None
    
    # Document management
    license_document_path: Optional[str] = None  # File path for license copy
    renewal_application_path: Optional[str] = None
    
    # Status
    status: Optional[str] = Field("active", example="active")  # active, expired, suspended, renewed
    is_critical: Optional[bool] = Field(True, example=True)  # Business critical license

class RegulatoryLicenseCreate(RegulatoryLicenseBase):
    pass

class RegulatoryLicense(RegulatoryLicenseBase):
    license_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Price History ----------------
class PriceHistoryBase(BaseModel):
    product_id: int
    batch_id: Optional[int] = None
    
    # Price changes
    old_mrp: Optional[float] = None
    new_mrp: Optional[float] = None
    old_sale_price: Optional[float] = None
    new_sale_price: Optional[float] = None
    old_purchase_price: Optional[float] = None
    new_purchase_price: Optional[float] = None
    
    # Change details
    change_reason: Optional[str] = None  # market_rate, supplier_change, promotion, etc.
    effective_date: date
    changed_by: Optional[int] = None

class PriceHistoryCreate(PriceHistoryBase):
    pass

class PriceHistory(PriceHistoryBase):
    price_history_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Enhanced Discount Schemes ----------------
class DiscountSchemeBase(BaseModel):
    scheme_name: str
    scheme_description: Optional[str] = None
    
    # Discount details
    discount_type: str  # percentage, fixed_amount, buy_x_get_y
    discount_value: float  # Amount or percentage
    max_discount_amount: Optional[float] = None  # Cap on discount
    
    # FIXED: Proper targeting
    target_type: Optional[str] = Field("all", example="all")  # all, customer_type, specific_customers, product_category, specific_products
    target_customer_types: Optional[str] = None  # JSON array of customer types
    target_categories: Optional[str] = None  # JSON array of product categories
    
    # Conditions
    min_quantity: Optional[int] = Field(1, example=1)
    min_order_value: Optional[float] = None
    
    # Validity
    valid_from: datetime
    valid_until: datetime
    is_active: Optional[bool] = Field(True, example=True)
    
    # Usage tracking
    max_uses_per_customer: Optional[int] = None  # Limit uses per customer
    total_usage_limit: Optional[int] = None  # Total usage limit
    current_usage_count: Optional[int] = Field(0, example=0)

class DiscountSchemeCreate(DiscountSchemeBase):
    pass

class DiscountScheme(DiscountSchemeBase):
    scheme_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Applied Discounts ----------------
class AppliedDiscountBase(BaseModel):
    scheme_id: int
    order_id: int
    customer_id: int
    
    discount_amount: float
    applied_date: Optional[datetime] = None
    
    # Details
    original_amount: Optional[float] = None
    final_amount: Optional[float] = None
    discount_percentage_used: Optional[float] = None

class AppliedDiscountCreate(AppliedDiscountBase):
    pass

class AppliedDiscount(AppliedDiscountBase):
    applied_discount_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Discount Product Targeting ----------------
class DiscountProductBase(BaseModel):
    scheme_id: int
    product_id: int

class DiscountProductCreate(DiscountProductBase):
    pass

class DiscountProduct(DiscountProductBase):
    discount_product_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Discount Customer Targeting ----------------
class DiscountCustomerBase(BaseModel):
    scheme_id: int
    customer_id: int
    usage_count: Optional[int] = Field(0, example=0)

class DiscountCustomerCreate(DiscountCustomerBase):
    pass

class DiscountCustomer(DiscountCustomerBase):
    discount_customer_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Inventory Transactions ----------------
class InventoryTransactionBase(BaseModel):
    batch_id: int
    
    # Transaction details
    transaction_type: str  # sale, purchase, return, adjustment, transfer
    quantity_change: int  # Positive for in, negative for out
    
    # Reference to triggering entity
    reference_type: Optional[str] = None  # order_item, purchase_item, return_item, manual_adjustment
    reference_id: Optional[int] = None  # ID of the triggering record
    
    # Before/After quantities for audit
    quantity_before: int
    quantity_after: int
    
    # Transaction metadata
    transaction_date: Optional[datetime] = None
    performed_by: Optional[int] = None
    remarks: Optional[str] = None
    
    # Automatic transaction flag
    is_automatic: Optional[bool] = Field(True, example=True)  # True for system-generated, False for manual

class InventoryTransactionCreate(InventoryTransactionBase):
    pass

class InventoryTransaction(InventoryTransactionBase):
    transaction_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Batch Inventory Status ----------------
class BatchInventoryStatusBase(BaseModel):
    batch_id: int
    
    # Current quantities (updated by triggers)
    current_quantity: int
    reserved_quantity: Optional[int] = Field(0, example=0)  # Reserved for pending orders
    available_quantity: Optional[int] = Field(0, example=0)  # current - reserved
    
    # Thresholds
    minimum_stock_level: Optional[int] = Field(10, example=10)
    reorder_level: Optional[int] = Field(20, example=20)
    maximum_stock_level: Optional[int] = Field(1000, example=1000)
    
    # Status flags
    is_out_of_stock: Optional[bool] = Field(False, example=False)
    is_low_stock: Optional[bool] = Field(False, example=False)
    needs_reorder: Optional[bool] = Field(False, example=False)
    
    # Last updated
    last_transaction_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

class BatchInventoryStatusCreate(BatchInventoryStatusBase):
    pass

class BatchInventoryStatus(BatchInventoryStatusBase):
    
    class Config:
        from_attributes = True

# ---------------- Customer Credit Notes ----------------
class CustomerCreditNoteBase(BaseModel):
    customer_id: int
    order_id: Optional[int] = None
    
    # Credit details
    credit_amount: float
    reason: str  # return, damage, pricing_error, goodwill
    credit_type: Optional[str] = Field("refund", example="refund")  # refund, adjustment, carry_forward
    
    # Status and dates
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None  # If credit expires
    status: Optional[str] = Field("issued", example="issued")  # issued, used, expired, cancelled
    used_amount: Optional[float] = Field(0.0, example=0.0)
    remaining_amount: Optional[float] = None
    
    # References
    reference_invoice: Optional[str] = None
    approved_by: Optional[int] = None

class CustomerCreditNoteCreate(CustomerCreditNoteBase):
    pass

class CustomerCreditNote(CustomerCreditNoteBase):
    credit_note_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Customer Outstanding ----------------
class CustomerOutstandingBase(BaseModel):
    customer_id: int
    order_id: int
    
    # Outstanding details
    total_amount: float
    paid_amount: Optional[float] = Field(0.0, example=0.0)
    outstanding_amount: float
    
    # Due date management
    invoice_date: date
    due_date: date
    overdue_days: Optional[int] = Field(0, example=0)
    
    # Status
    status: Optional[str] = Field("pending", example="pending")  # pending, partial, paid, overdue
    payment_reminder_sent: Optional[int] = Field(0, example=0)  # Count of reminders
    last_reminder_date: Optional[date] = None

class CustomerOutstandingCreate(CustomerOutstandingBase):
    pass

class CustomerOutstanding(CustomerOutstandingBase):
    outstanding_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Purchase Returns ----------------
class PurchaseReturnBase(BaseModel):
    purchase_id: int
    supplier_id: int
    
    # Return details
    return_date: Optional[date] = None
    return_invoice_number: Optional[str] = None
    total_return_amount: Optional[float] = None
    
    # Return reason
    reason: str  # expired, damaged, wrong_item, quality_issue
    return_type: Optional[str] = Field("full", example="full")  # full, partial
    
    # Status and processing
    status: Optional[str] = Field("initiated", example="initiated")  # initiated, approved, shipped, refunded
    refund_amount: Optional[float] = None
    refund_date: Optional[date] = None
    refund_mode: Optional[str] = None  # cash, bank_transfer, credit_note, adjustment
    
    # References
    debit_note_number: Optional[str] = None
    processed_by: Optional[int] = None

class PurchaseReturnCreate(PurchaseReturnBase):
    pass

class PurchaseReturn(PurchaseReturnBase):
    return_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Purchase Return Items ----------------
class PurchaseReturnItemBase(BaseModel):
    return_id: int
    product_id: int
    batch_id: int
    
    # Return quantities
    original_quantity: Optional[int] = None
    return_quantity: int
    unit_price: Optional[float] = None
    total_return_value: Optional[float] = None
    
    # Item condition
    item_condition: Optional[str] = None  # expired, damaged, intact
    reason_specific: Optional[str] = None  # Specific reason for this item

class PurchaseReturnItemCreate(PurchaseReturnItemBase):
    pass

class PurchaseReturnItem(PurchaseReturnItemBase):
    return_item_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Storage Locations ----------------
class StorageLocationBase(BaseModel):
    location_name: str
    location_code: Optional[str] = None  # Short code like "WH01", "STORE-A"
    location_type: Optional[str] = None  # warehouse, store, cold_storage, counter
    
    # Physical details
    address: Optional[str] = None
    capacity: Optional[int] = None  # Total capacity in units
    current_occupancy: Optional[int] = Field(0, example=0)
    
    # Environmental controls
    temperature_controlled: Optional[bool] = Field(False, example=False)
    temperature_range_min: Optional[float] = None
    temperature_range_max: Optional[float] = None
    humidity_controlled: Optional[bool] = Field(False, example=False)
    humidity_range_min: Optional[float] = None
    humidity_range_max: Optional[float] = None
    
    # Security and access
    security_level: Optional[str] = Field("standard", example="standard")  # high, standard, basic
    access_restricted: Optional[bool] = Field(False, example=False)
    
    # Manager and contact
    location_manager: Optional[int] = None
    contact_phone: Optional[str] = None
    
    # Status
    is_active: Optional[bool] = Field(True, example=True)

class StorageLocationCreate(StorageLocationBase):
    pass

class StorageLocation(StorageLocationBase):
    location_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Batch Locations ----------------
class BatchLocationBase(BaseModel):
    batch_id: int
    location_id: int
    
    # Quantity tracking
    quantity_stored: int
    reserved_quantity: Optional[int] = Field(0, example=0)  # Reserved for orders
    available_quantity: Optional[int] = None  # quantity_stored - reserved_quantity
    
    # Location details within storage
    rack_number: Optional[str] = None
    shelf_number: Optional[str] = None
    bin_number: Optional[str] = None
    
    # Tracking
    moved_in_date: Optional[datetime] = None
    last_movement_date: Optional[datetime] = None
    moved_by: Optional[int] = None
    
    # Status
    status: Optional[str] = Field("active", example="active")  # active, moved_out, quarantined

class BatchLocationCreate(BatchLocationBase):
    pass

class BatchLocation(BatchLocationBase):
    batch_location_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Enhanced Payments ----------------
class PaymentBase(BaseModel):
    customer_id: int  # FIXED: Direct customer link
    
    # Payment details
    amount: float
    payment_mode: str
    payment_date: Optional[datetime] = None
    reference_number: Optional[str] = None
    remarks: Optional[str] = None
    
    # Payment type and status
    payment_type: Optional[str] = Field("order_payment", example="order_payment")  # order_payment, advance, adjustment
    status: Optional[str] = Field("completed", example="completed")  # pending, completed, failed, reversed
    
    # Advanced payment tracking
    bank_name: Optional[str] = None
    transaction_id: Optional[str] = None
    processed_by: Optional[int] = None

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    payment_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Payment Allocations ----------------
class PaymentAllocationBase(BaseModel):
    payment_id: int
    order_id: int
    allocated_amount: float
    allocation_date: Optional[datetime] = None
    remarks: Optional[str] = None

class PaymentAllocationCreate(PaymentAllocationBase):
    pass

class PaymentAllocation(PaymentAllocationBase):
    allocation_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Customer Advance Payments ----------------
class CustomerAdvancePaymentBase(BaseModel):
    customer_id: int
    payment_id: int
    
    advance_amount: float
    used_amount: Optional[float] = Field(0.0, example=0.0)
    remaining_amount: float
    
    status: Optional[str] = Field("active", example="active")  # active, fully_used, expired
    expiry_date: Optional[date] = None  # Optional expiry for advance payments

class CustomerAdvancePaymentCreate(CustomerAdvancePaymentBase):
    pass

class CustomerAdvancePayment(CustomerAdvancePaymentBase):
    advance_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- Complex Order Creation ----------------
class CompleteOrderCreate(BaseModel):
    """Schema for creating an order with all business logic applied"""
    # Order details
    customer_id: int
    mr_id: Optional[int] = None
    order_date: Optional[datetime] = None
    gross_amount: float
    tax_amount: float
    
    # Order items
    order_items: List[OrderItemCreate]
    
    # Payment information (optional for advance payments)
    payment_info: Optional[PaymentCreate] = None
    apply_advance_payment: Optional[bool] = Field(False, example=False)
    
    # User performing the action
    user_id: Optional[int] = None

class CompleteOrderResponse(BaseModel):
    """Response schema for complete order creation"""
    order_id: int
    final_amount: float
    discount_applied: float
    inventory_transactions: int
    payment_id: Optional[int] = None
    advance_applied: Optional[float] = None
    status: str

# ---------------- CHALLAN/DISPATCH ARCHITECTURE ----------------
class ChallanBase(BaseModel):
    order_id: int
    customer_id: int
    
    # Challan details
    challan_number: str
    challan_date: Optional[date] = None
    dispatch_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    
    # Transport details
    vehicle_number: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    transport_company: Optional[str] = None
    lr_number: Optional[str] = None
    freight_amount: Optional[float] = Field(0.0, example=0.0)
    
    # Delivery address
    delivery_address: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_state: Optional[str] = None
    delivery_pincode: Optional[str] = None
    delivery_contact_person: Optional[str] = None
    delivery_contact_phone: Optional[str] = None
    
    # Status and details
    status: Optional[str] = Field("prepared", example="prepared")
    remarks: Optional[str] = None
    special_instructions: Optional[str] = None
    total_packages: Optional[int] = Field(1, example=1)
    total_weight: Optional[float] = None

class ChallanCreate(ChallanBase):
    pass

class Challan(ChallanBase):
    challan_id: int
    dispatch_time: Optional[datetime] = None
    delivery_time: Optional[datetime] = None
    prepared_by: Optional[int] = None
    dispatched_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ChallanItemBase(BaseModel):
    challan_id: int
    order_item_id: int
    batch_id: int
    
    # Dispatch quantities
    ordered_quantity: int
    dispatched_quantity: int
    pending_quantity: Optional[int] = Field(0, example=0)
    
    # Item details
    product_name: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    unit_price: Optional[float] = None
    
    # Package details
    package_type: Optional[str] = None
    packages_count: Optional[int] = Field(1, example=1)

class ChallanItemCreate(ChallanItemBase):
    pass

class ChallanItem(ChallanItemBase):
    challan_item_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChallanTrackingBase(BaseModel):
    challan_id: int
    location: str
    status: str
    timestamp: Optional[datetime] = None
    remarks: Optional[str] = None
    updated_by: Optional[int] = None
    updated_by_name: Optional[str] = None

class ChallanTrackingCreate(ChallanTrackingBase):
    pass

class ChallanTracking(ChallanTrackingBase):
    tracking_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ---------------- MISSING BUSINESS OPERATIONS ----------------
class StockAdjustmentItem(BaseModel):
    batch_id: int
    adjustment_quantity: int  # Can be positive or negative
    reason: str

class StockAdjustmentRequest(BaseModel):
    adjustments: List[StockAdjustmentItem]
    overall_reason: str
    user_id: Optional[int] = None

class SalesReturnProcessRequest(BaseModel):
    return_items: List[Dict]  # List of return items with batch_id, return_quantity
    user_id: Optional[int] = None

class BatchRecommendationRequest(BaseModel):
    product_id: int
    required_quantity: int

class BatchRecommendationResponse(BaseModel):
    product_id: int
    requested_quantity: int
    total_available: int
    can_fulfill: bool
    shortage: int
    recommendations: List[Dict]

class ExpiryAlert(BaseModel):
    batch_id: int
    batch_number: str
    product_id: int
    expiry_date: date
    days_to_expiry: int
    current_quantity: int
    alert_type: str  # EXPIRED, CRITICAL_EXPIRY, WARNING_EXPIRY

class ChallanDispatchRequest(BaseModel):
    vehicle_number: str
    driver_name: str
    driver_phone: Optional[str] = None
    transport_company: str
    lr_number: Optional[str] = None
    freight_amount: Optional[float] = 0.0
    expected_delivery_date: Optional[date] = None
    special_instructions: Optional[str] = None

# ---------------- Enhanced Indian Regulatory Compliance ----------------
class EnhancedRegulatoryLicenseBase(BaseModel):
    # Basic license info
    entity_type: str  # company, supplier, customer
    entity_id: Optional[int] = None
    company_license: Optional[bool] = Field(False, example=False)
    
    license_type: str  # Drug License, GST, Shop License, etc.
    license_number: str
    license_name: Optional[str] = None
    
    # Issuing authority details
    issuing_authority: str
    issuing_state: Optional[str] = None
    issuing_district: Optional[str] = None
    
    # Dates
    issue_date: date
    expiry_date: date
    renewal_due_date: Optional[date] = None
    
    # NEW: Indian Regulatory Compliance Fields
    # CDSCO specific fields
    cdsco_license_category: Optional[str] = Field(None, example="Wholesale")  # Wholesale, Retail, Import, Manufacture
    cdsco_form_type: Optional[str] = Field(None, example="Form 20B")  # Form 20B, Form 21B, Form 27, etc.
    drug_schedule_covered: Optional[str] = Field(None, example='["G", "H", "H1"]')  # JSON array: ["G", "H", "H1", "X"]
    narcotic_license: Optional[bool] = Field(False, example=False)  # For Schedule X
    psychotropic_license: Optional[bool] = Field(False, example=False)  # For psychotropic substances
    
    # State Drug Controller specific
    state_drug_controller: Optional[str] = Field(None, example="Karnataka State Drug Controller")
    regional_office: Optional[str] = Field(None, example="Bangalore Regional Office")
    
    # License scope and restrictions
    authorized_activities: Optional[str] = Field(None, example='["wholesale", "retail", "storage"]')  # JSON array
    drug_categories_allowed: Optional[str] = Field(None, example="All allopathic medicines except narcotics")
    quantity_restrictions: Optional[str] = Field(None, example="No quantity restrictions")
    area_of_operation: Optional[str] = Field(None, example="Karnataka State")
    
    # Compliance tracking
    last_inspection_date: Optional[date] = None
    next_inspection_due: Optional[date] = None
    compliance_score: Optional[int] = Field(None, example=95)  # Internal compliance rating
    violation_history: Optional[str] = Field(None, example='[]')  # JSON array of past violations
    
    # Document upload tracking
    document_verification_status: Optional[str] = Field("pending", example="pending")  # pending, verified, rejected
    verification_notes: Optional[str] = None
    
    # Basic fields
    renewal_reminder_days: Optional[int] = Field(60, example=60)
    renewal_fee: Optional[float] = None
    status: Optional[str] = Field("active", example="active")
    is_critical: Optional[bool] = Field(True, example=True)

class EnhancedRegulatoryLicenseCreate(EnhancedRegulatoryLicenseBase):
    pass

class EnhancedRegulatoryLicense(EnhancedRegulatoryLicenseBase):
    license_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ---------------- CDSCO Compliance ----------------
class CDSCOComplianceBase(BaseModel):
    license_id: int
    form_type: str = Field(..., example="Form 20B")  # Form 20B, 21B, 27, etc.
    submission_date: Optional[date] = None
    acknowledgment_number: Optional[str] = None
    status: Optional[str] = Field("submitted", example="submitted")  # submitted, approved, rejected, expired
    
    # Drug recall tracking
    recall_notices_received: Optional[int] = Field(0, example=0)
    recall_actions_completed: Optional[int] = Field(0, example=0)
    
    # ADR (Adverse Drug Reaction) reporting
    adr_reports_filed: Optional[int] = Field(0, example=0)
    last_adr_report_date: Optional[date] = None
    
    # Monthly reporting
    monthly_reports_due: Optional[int] = Field(12, example=12)
    monthly_reports_filed: Optional[int] = Field(0, example=0)
    last_monthly_report_date: Optional[date] = None

class CDSCOComplianceCreate(CDSCOComplianceBase):
    pass

class CDSCOCompliance(CDSCOComplianceBase):
    compliance_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ---------------- State Drug Controller Compliance ----------------
class StateDrugControllerComplianceBase(BaseModel):
    license_id: int
    state: str = Field(..., example="Karnataka")
    
    # State-specific compliance
    state_license_number: Optional[str] = None
    regional_office: Optional[str] = Field(None, example="Bangalore Regional Office")
    controlling_officer: Optional[str] = Field(None, example="Dr. Raj Kumar")
    
    # Inspection tracking
    last_inspection_date: Optional[date] = None
    next_inspection_due: Optional[date] = None
    inspection_result: Optional[str] = Field(None, example="satisfactory")  # satisfactory, needs_improvement, violation
    inspector_name: Optional[str] = None
    
    # State-specific reporting
    quarterly_reports_due: Optional[int] = Field(4, example=4)
    quarterly_reports_filed: Optional[int] = Field(0, example=0)
    last_quarterly_report_date: Optional[date] = None
    
    # Compliance status
    current_status: Optional[str] = Field("compliant", example="compliant")  # compliant, warning, violation
    penalty_amount: Optional[float] = Field(0.0, example=0.0)
    penalty_paid: Optional[bool] = Field(True, example=True)

class StateDrugControllerComplianceCreate(StateDrugControllerComplianceBase):
    pass

class StateDrugControllerCompliance(StateDrugControllerComplianceBase):
    compliance_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ---------------- License Document Management ----------------
class LicenseDocumentBase(BaseModel):
    license_id: int
    document_type: str = Field(..., example="license_copy")  # license_copy, renewal_application, compliance_certificate
    document_name: str = Field(..., example="Drug_License_Copy.pdf")
    file_path: str = Field(..., example="/uploads/licenses/drug_license_123.pdf")
    file_size: Optional[int] = Field(None, example=1048576)  # File size in bytes
    file_format: Optional[str] = Field(None, example="pdf")  # pdf, jpg, png, etc.
    
    # Document metadata
    is_current: Optional[bool] = Field(True, example=True)
    version_number: Optional[int] = Field(1, example=1)
    expires_on: Optional[date] = None

class LicenseDocumentCreate(LicenseDocumentBase):
    uploaded_by: int

class LicenseDocument(LicenseDocumentBase):
    document_id: int
    uploaded_by: int
    upload_date: Optional[datetime] = None
    
    # Verification
    verification_status: Optional[str] = Field("pending", example="pending")  # pending, verified, rejected
    verified_by: Optional[int] = None
    verification_date: Optional[datetime] = None
    verification_notes: Optional[str] = None
    
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ----------------- FILE UPLOAD SCHEMAS -----------------
class FileUploadCreate(BaseModel):
    upload_purpose: str
    entity_type: str
    entity_id: int
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_temporary: Optional[bool] = False
    access_level: Optional[str] = "private"

class FileUploadResponse(BaseModel):
    file_id: int
    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int
    file_type: str
    file_extension: str
    upload_purpose: str
    entity_type: str
    entity_id: int
    is_verified: bool
    virus_scan_status: str
    access_level: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ----------------- LOYALTY PROGRAM SCHEMAS -----------------
class LoyaltyProgramCreate(BaseModel):
    program_name: str
    program_description: Optional[str] = None
    points_per_rupee: float = 1.0
    points_redemption_value: float = 0.10
    minimum_redemption_points: int = 100
    maximum_redemption_points: Optional[int] = None
    has_tiers: bool = False
    tier_upgrade_spend_amount: Optional[float] = None
    tier_upgrade_points: Optional[int] = None
    start_date: date
    end_date: Optional[date] = None
    birthday_bonus_points: int = 0
    referral_bonus_points: int = 0
    signup_bonus_points: int = 0
    points_expiry_months: int = 12
    max_points_per_transaction: Optional[int] = None
    min_order_value_for_points: float = 0

class LoyaltyProgramResponse(BaseModel):
    program_id: int
    program_name: str
    program_description: Optional[str]
    points_per_rupee: float
    points_redemption_value: float
    minimum_redemption_points: int
    maximum_redemption_points: Optional[int]
    has_tiers: bool
    start_date: date
    end_date: Optional[date]
    is_active: bool
    birthday_bonus_points: int
    referral_bonus_points: int
    signup_bonus_points: int
    points_expiry_months: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class CustomerLoyaltyResponse(BaseModel):
    loyalty_id: int
    customer_id: int
    program_id: int
    current_points: int
    lifetime_points_earned: int
    lifetime_points_redeemed: int
    current_tier: str
    tier_points: int
    tier_spend_amount: float
    next_tier_threshold: Optional[int]
    enrollment_date: date
    last_activity_date: Optional[date]
    membership_status: str
    birthday_bonus_claimed: bool
    referral_count: int
    
    class Config:
        from_attributes = True

class LoyaltyTransactionCreate(BaseModel):
    customer_id: int
    program_id: int
    transaction_type: str  # earned, redeemed, expired, bonus, adjustment
    points: int
    order_id: Optional[int] = None
    transaction_reason: Optional[str] = None
    order_amount: Optional[float] = None
    redemption_amount: Optional[float] = None
    points_expiry_date: Optional[date] = None
    remarks: Optional[str] = None

class LoyaltyTransactionResponse(BaseModel):
    transaction_id: int
    customer_id: int
    program_id: int
    transaction_type: str
    points: int
    order_id: Optional[int]
    transaction_reason: Optional[str]
    order_amount: Optional[float]
    redemption_amount: Optional[float]
    points_before: int
    points_after: int
    transaction_date: datetime
    points_expiry_date: Optional[date]
    is_expired: bool
    
    class Config:
        from_attributes = True

class LoyaltyRedemptionCreate(BaseModel):
    customer_id: int
    points_redeemed: int
    order_id: Optional[int] = None
    redemption_type: str = "discount"  # discount, cash_back, free_product

class LoyaltyRedemptionResponse(BaseModel):
    redemption_id: int
    customer_id: int
    order_id: Optional[int]
    points_redeemed: int
    cash_value: float
    redemption_type: str
    status: str
    redemption_date: datetime
    refunded_points: int
    
    class Config:
        from_attributes = True

# ----------------- UPI PAYMENT SCHEMAS -----------------
class UPIPaymentCreate(BaseModel):
    order_id: Optional[int] = None
    customer_id: int
    amount: float
    upi_id: Optional[str] = None
    expires_in_minutes: int = 15  # QR code validity

class UPIPaymentResponse(BaseModel):
    upi_payment_id: int
    order_id: Optional[int]
    customer_id: int
    amount: float
    qr_code_string: str
    qr_code_image_path: Optional[str]
    merchant_transaction_id: str
    payment_status: str
    initiated_at: datetime
    expires_at: datetime
    upi_transaction_id: Optional[str]
    amount_received: Optional[float]
    settlement_amount: Optional[float]
    reconciliation_status: str
    
    class Config:
        from_attributes = True

class UPIPaymentStatusUpdate(BaseModel):
    upi_transaction_id: str
    payment_status: str  # completed, failed
    amount_received: Optional[float] = None
    payer_bank: Optional[str] = None
    bank_reference_number: Optional[str] = None
    fees_deducted: Optional[float] = 0

# ---------------- Missing Schemas ----------------
class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    document_id: Optional[int] = None
    file_path: Optional[str] = None

class ComplianceDashboard(BaseModel):
    total_licenses: int
    active_licenses: int
    expiring_soon: int  # Licenses expiring in next 60 days
    expired_licenses: int
    pending_renewals: int
    
    # CDSCO specific
    cdsco_forms_pending: int
    adr_reports_pending: int
    monthly_reports_pending: int
    
    # State compliance
    states_covered: int
    inspection_due_count: int
    compliance_violations: int
    
    # Document status
    documents_pending_verification: int
    documents_verified: int
    documents_rejected: int

# ================= NEW SCHEMAS FOR PHASE 2 PRIORITY 3 =================

# User Management Schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Optional[str] = None
    is_active: bool = True

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[str] = None
    is_active: Optional[bool] = None

class Role(RoleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserSessionBase(BaseModel):
    session_token: str
    expires_at: datetime
    is_active: bool = True

class UserSessionCreate(UserSessionBase):
    user_id: int

class UserSession(UserSessionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# User Auth Schemas
class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

# Loyalty Program Schemas
class LoyaltyAccountBase(BaseModel):
    customer_id: int
    points_balance: int = 0
    total_points_earned: int = 0
    total_points_redeemed: int = 0
    tier: str = "bronze"
    is_active: bool = True

class LoyaltyAccountCreate(BaseModel):
    customer_id: int

class LoyaltyAccountUpdate(BaseModel):
    points_balance: Optional[int] = None
    tier: Optional[str] = None
    is_active: Optional[bool] = None

class LoyaltyAccount(LoyaltyAccountBase):
    id: int
    last_activity_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PointsTransactionBase(BaseModel):
    loyalty_account_id: int
    points: int
    transaction_type: str
    reference_id: Optional[int] = None
    description: Optional[str] = None

class PointsTransactionCreate(PointsTransactionBase):
    pass

class PointsTransaction(PointsTransactionBase):
    id: int
    transaction_date: datetime
    
    class Config:
        from_attributes = True

class RewardBase(BaseModel):
    title: str
    description: Optional[str] = None
    points_required: int
    category: Optional[str] = None
    required_tier: str = "bronze"
    is_active: bool = True

class RewardCreate(RewardBase):
    pass

class Reward(RewardBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RewardRedemptionBase(BaseModel):
    loyalty_account_id: int
    reward_id: int
    points_used: int
    status: str = "redeemed"

class RewardRedemptionCreate(RewardRedemptionBase):
    pass

class RewardRedemption(RewardRedemptionBase):
    id: int
    redemption_date: datetime
    
    class Config:
        from_attributes = True

# Compliance Schemas
class AuditLogBase(BaseModel):
    user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLog(AuditLogBase):
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class LicenseBase(BaseModel):
    license_type: str
    license_number: str
    issuing_authority: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_active: bool = True

class LicenseCreate(LicenseBase):
    pass

class LicenseUpdate(BaseModel):
    license_type: Optional[str] = None
    license_number: Optional[str] = None
    issuing_authority: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_active: Optional[bool] = None

class License(LicenseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RegulatoryReportBase(BaseModel):
    report_type: str
    title: Optional[str] = None
    content: Optional[str] = None
    status: str = "draft"

class RegulatoryReportCreate(RegulatoryReportBase):
    pass

class RegulatoryReport(RegulatoryReportBase):
    id: int
    created_at: datetime
    submitted_at: Optional[datetime] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ComplianceCheckBase(BaseModel):
    check_type: str
    description: Optional[str] = None
    status: str = "pending"

class ComplianceCheckCreate(ComplianceCheckBase):
    pass

class ComplianceCheck(ComplianceCheckBase):
    id: int
    resolution_notes: Optional[str] = None
    resolved_by: Optional[int] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ComplianceResolution(BaseModel):
    notes: str
    resolved_by: int

# File Upload Schemas
class FileUploadBase(BaseModel):
    filename: str
    unique_filename: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    storage_type: str = "local"
    is_active: bool = True

class FileUploadCreate(FileUploadBase):
    pass

class FileUpload(FileUploadBase):
    id: int
    uploaded_at: datetime
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Challan Schemas
class ChallanDeliveryInfo(BaseModel):
    delivered_by: str
    delivery_notes: Optional[str] = None
    customer_signature: Optional[str] = None

class ChallanItemBase(BaseModel):
    product_id: int
    quantity: int
    rate: float
    amount: float

class ChallanItemCreate(ChallanItemBase):
    pass

class ChallanItemUpdate(BaseModel):
    quantity: Optional[int] = None
    rate: Optional[float] = None
    amount: Optional[float] = None

class ChallanItem(ChallanItemBase):
    id: int
    challan_id: int
    
    class Config:
        from_attributes = True

class ChallanBase(BaseModel):
    order_id: int
    customer_id: int
    challan_number: str
    challan_date: Optional[date] = None
    
class ChallanCreate(ChallanBase):
    pass

class ChallanUpdate(BaseModel):
    status: Optional[str] = None
    delivery_date: Optional[date] = None
    
class Challan(ChallanBase):
    id: int
    status: str = "pending"
    dispatch_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None
    total_amount: Optional[float] = None
    
    class Config:
        from_attributes = True

# Audit Export Schema
class AuditExportRequest(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    user_id: Optional[int] = None


# ============= MISSING SCHEMAS - Added for Router Compatibility =============

# Payment with Allocation Schema
class PaymentWithAllocationCreate(PaymentCreate):
    """Payment creation with automatic allocation to orders"""
    allocate_to_orders: bool = True
    order_ids: Optional[List[int]] = None
    allocation_strategy: Optional[str] = "oldest_first"  # oldest_first, proportional, manual


# Advance Payment Application Schema  
class AdvancePaymentApplication(BaseModel):
    """Apply advance payment to specific orders"""
    advance_payment_id: int
    order_ids: List[int]
    amounts: Optional[Dict[int, float]] = None  # order_id -> amount mapping
    apply_full_amount: bool = False


# Challan from Order Creation Schema
class ChallanFromOrderCreate(BaseModel):
    """Create challan from existing order"""
    order_id: int
    delivery_date: Optional[date] = None
    transport_details: Optional[str] = None
    remarks: Optional[str] = None
    include_partial: bool = False
    selected_items: Optional[List[int]] = None  # order_item_ids


# Stock Adjustment Schemas
class StockAdjustmentBase(BaseModel):
    """Base schema for stock adjustments"""
    adjustment_type: str  # damage, theft, counting_error, return_to_vendor, etc.
    adjustment_date: datetime
    total_items: int
    total_value: float
    reason: str
    approved_by: Optional[int] = None
    reference_number: Optional[str] = None


class StockAdjustmentCreate(StockAdjustmentBase):
    """Create new stock adjustment"""
    items: List[StockAdjustmentItem]
    auto_approve: bool = False


class StockAdjustment(StockAdjustmentBase):
    """Stock adjustment with ID"""
    id: int
    created_by: int
    created_at: datetime
    status: str  # pending, approved, rejected
    items: Optional[List[StockAdjustmentItem]] = None
    
    class Config:
        from_attributes = True