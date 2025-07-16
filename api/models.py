from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey, Text, Numeric, CheckConstraint, Boolean
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from datetime import datetime

# Handle both package and direct imports
try:
    from .database import Base
except ImportError:
    from database import Base

# ----------------- FILE UPLOAD MANAGEMENT -----------------
class FileUpload(Base):
    __tablename__ = "file_uploads"
    file_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # File details
    original_filename = Column(Text, nullable=False)
    stored_filename = Column(Text, nullable=False)  # UUID-based filename
    file_path = Column(Text, nullable=False)  # Full path to stored file
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_type = Column(Text, nullable=False)  # MIME type
    file_extension = Column(Text)  # .pdf, .jpg, etc.
    
    # Upload context
    uploaded_by = Column(Integer, ForeignKey("users.user_id"))
    upload_purpose = Column(Text)  # license_document, product_image, challan_photo, etc.
    entity_type = Column(Text)  # license, product, challan, customer, etc.
    entity_id = Column(Integer)  # ID of the related entity
    
    # File verification and processing
    virus_scan_status = Column(Text, default='pending')  # pending, clean, infected, error
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime)
    verified_by = Column(Integer, ForeignKey("users.user_id"))
    
    # File access control
    is_public = Column(Boolean, default=False)
    access_level = Column(Text, default='private')  # public, private, restricted
    allowed_roles = Column(Text)  # JSON array of roles that can access
    
    # File lifecycle
    is_temporary = Column(Boolean, default=False)  # For temporary uploads
    expires_at = Column(DateTime)  # Auto-delete date for temporary files
    is_archived = Column(Boolean, default=False)
    archived_date = Column(DateTime)
    
    # Metadata
    description = Column(Text)
    tags = Column(Text)  # JSON array of tags for searching
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# ----------------- LOYALTY PROGRAM -----------------
class LoyaltyProgram(Base):
    __tablename__ = "loyalty_programs"
    program_id = Column(Integer, primary_key=True, autoincrement=True)
    program_name = Column(Text, nullable=False)
    program_description = Column(Text)
    
    # Program rules
    points_per_rupee = Column(Numeric(10, 4), default=1.0)  # Points earned per ₹1 spent
    points_redemption_value = Column(Numeric(10, 4), default=0.10)  # ₹ value per point
    minimum_redemption_points = Column(Integer, default=100)
    maximum_redemption_points = Column(Integer)  # Cap on single redemption
    
    # Tier system
    has_tiers = Column(Boolean, default=False)
    tier_upgrade_spend_amount = Column(Numeric(10, 2))  # Spend to upgrade tier
    tier_upgrade_points = Column(Integer)  # Points to upgrade tier
    
    # Program validity
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    is_active = Column(Boolean, default=True)
    
    # Special features
    birthday_bonus_points = Column(Integer, default=0)
    referral_bonus_points = Column(Integer, default=0)
    signup_bonus_points = Column(Integer, default=0)
    
    # Program settings
    points_expiry_months = Column(Integer, default=12)  # Points expire after X months
    max_points_per_transaction = Column(Integer)  # Cap on points per order
    min_order_value_for_points = Column(Numeric(10, 2), default=0)  # Minimum order for points
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class CustomerLoyalty(Base):
    __tablename__ = "customer_loyalty"
    loyalty_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    program_id = Column(Integer, ForeignKey("loyalty_programs.program_id"), nullable=False)
    
    # Current status
    current_points = Column(Integer, default=0)
    lifetime_points_earned = Column(Integer, default=0)
    lifetime_points_redeemed = Column(Integer, default=0)
    
    # Tier information
    current_tier = Column(Text, default='Bronze')  # Bronze, Silver, Gold, Platinum
    tier_points = Column(Integer, default=0)  # Points towards next tier
    tier_spend_amount = Column(Numeric(10, 2), default=0)  # Spend towards next tier
    next_tier_threshold = Column(Integer)  # Points/amount needed for next tier
    
    # Membership details
    enrollment_date = Column(Date, default=datetime.utcnow)
    last_activity_date = Column(Date)
    membership_status = Column(Text, default='active')  # active, inactive, suspended
    
    # Special bonuses tracking
    birthday_bonus_claimed = Column(Boolean, default=False)
    last_birthday_bonus_year = Column(Integer)
    referral_count = Column(Integer, default=0)
    referred_by = Column(Integer, ForeignKey("customers.customer_id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class LoyaltyTransaction(Base):
    __tablename__ = "loyalty_transactions"
    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    program_id = Column(Integer, ForeignKey("loyalty_programs.program_id"), nullable=False)
    
    # Transaction details
    transaction_type = Column(Text, nullable=False)  # earned, redeemed, expired, bonus, adjustment
    points = Column(Integer, nullable=False)  # Positive for earned, negative for redeemed
    order_id = Column(Integer, ForeignKey("orders.order_id"))  # If related to an order
    
    # Context
    transaction_reason = Column(Text)  # purchase, birthday_bonus, referral, manual_adjustment
    order_amount = Column(Numeric(10, 2))  # Order amount if earned from purchase
    redemption_amount = Column(Numeric(10, 2))  # Cash value if redeemed
    
    # Balances (snapshot at time of transaction)
    points_before = Column(Integer, nullable=False)
    points_after = Column(Integer, nullable=False)
    
    # Transaction metadata
    transaction_date = Column(DateTime, default=datetime.utcnow)
    processed_by = Column(Integer, ForeignKey("users.user_id"))
    remarks = Column(Text)
    
    # Expiry tracking for earned points
    points_expiry_date = Column(Date)  # When these points will expire
    is_expired = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class LoyaltyRedemption(Base):
    __tablename__ = "loyalty_redemptions"
    redemption_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    loyalty_transaction_id = Column(Integer, ForeignKey("loyalty_transactions.transaction_id"))
    order_id = Column(Integer, ForeignKey("orders.order_id"))  # If redeemed against an order
    
    # Redemption details
    points_redeemed = Column(Integer, nullable=False)
    cash_value = Column(Numeric(10, 2), nullable=False)  # ₹ value of redeemed points
    redemption_type = Column(Text, default='discount')  # discount, cash_back, free_product
    
    # Status
    status = Column(Text, default='completed')  # pending, completed, cancelled, refunded
    redemption_date = Column(DateTime, default=datetime.utcnow)
    processed_by = Column(Integer, ForeignKey("users.user_id"))
    
    # Refund tracking
    refunded_points = Column(Integer, default=0)
    refund_reason = Column(Text)
    refund_date = Column(DateTime)
    refunded_by = Column(Integer, ForeignKey("users.user_id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# ----------------- UPI PAYMENT INTEGRATION -----------------
class UPIPayment(Base):
    __tablename__ = "upi_payments"
    upi_payment_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    
    # UPI details
    upi_transaction_id = Column(Text, unique=True)  # UPI reference number
    upi_id = Column(Text)  # Customer's UPI ID (if provided)
    amount = Column(Numeric(10, 2), nullable=False)
    
    # QR Code details
    qr_code_string = Column(Text, nullable=False)  # Generated UPI QR string
    qr_code_image_path = Column(Text)  # Path to QR code image
    merchant_transaction_id = Column(Text, nullable=False, unique=True)  # Our reference
    
    # Payment tracking
    payment_status = Column(Text, default='pending')  # pending, completed, failed, expired
    initiated_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime, nullable=False)  # QR code expiry (usually 15 mins)
    
    # Bank details
    payer_bank = Column(Text)  # Customer's bank
    payee_bank = Column(Text, default='HDFC Bank')  # Our bank
    bank_reference_number = Column(Text)  # Bank's UTR/reference
    
    # Verification
    amount_received = Column(Numeric(10, 2))  # Actual amount received
    fees_deducted = Column(Numeric(10, 2), default=0)  # Bank fees if any
    settlement_amount = Column(Numeric(10, 2))  # Final settled amount
    
    # Reconciliation
    reconciliation_status = Column(Text, default='pending')  # pending, matched, disputed
    bank_statement_matched = Column(Boolean, default=False)
    reconciled_by = Column(Integer, ForeignKey("users.user_id"))
    reconciliation_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# ----------------- PRODUCTS -----------------
class Product(Base):
    __tablename__ = "products"
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_code = Column(Text, unique=True)  # Frontend uses this field
    product_name = Column(Text, nullable=False)
    category = Column(Text)
    manufacturer = Column(Text)
    product_type = Column(Text)
    hsn_code = Column(Text)
    gst_percent = Column(Numeric(5, 2))
    cgst_percent = Column(Numeric(5, 2))
    sgst_percent = Column(Numeric(5, 2))
    igst_percent = Column(Numeric(5, 2))
    mrp = Column(Numeric(10, 2))
    sale_price = Column(Numeric(10, 2))
    
    # Drug schedule classification fields
    drug_schedule = Column(String(10))  # G, H, H1, X, etc.
    requires_prescription = Column(Boolean, default=False)
    controlled_substance = Column(Boolean, default=False)
    
    # Additional pharmaceutical product details
    generic_name = Column(Text)  # Generic name of the medicine
    composition = Column(Text)  # Full composition details
    dosage_instructions = Column(Text)  # Recommended dosage
    storage_instructions = Column(Text)  # How to store the product
    packer = Column(Text)  # Packing company
    country_of_origin = Column(Text)  # Manufacturing country
# Removed model_number - causes Pydantic warning, replaced with product_code
    dimensions = Column(Text)  # Product dimensions
    weight = Column(Numeric(10, 2))  # Weight in grams
    weight_unit = Column(String(10), default='g')  # Unit of weight
    pack_quantity = Column(Integer)  # Number of units in pack
    pack_form = Column(Text)  # Tablets, Capsules, Syrup, etc.
    is_discontinued = Column(Boolean, default=False)  # Discontinued by manufacturer
    color = Column(Text)  # Color information
    asin = Column(Text)  # Amazon Standard Identification Number or similar
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# ----------------- BATCHES -----------------
class Batch(Base):
    __tablename__ = "batches"
    batch_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    batch_number = Column(Text, nullable=False)
    manufacturing_date = Column('manufacturing_date', Date)  # Map to correct database column
    expiry_date = Column(Date, nullable=False)
    purchase_price = Column(Numeric(10, 2))  # Keep for backward compatibility
    selling_price = Column(Numeric(10, 2))
    quantity_available = Column(Integer, nullable=False)
    location = Column(Text)  # Keep for backward compatibility
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Full database schema columns (optional for now)
    org_id = Column(String)
    lot_number = Column(Text)
    serial_number = Column(Text)
    days_to_expiry = Column(Integer)
    is_near_expiry = Column(Boolean, default=False)
    quantity_received = Column(Integer)
    quantity_sold = Column(Integer, default=0)
    quantity_damaged = Column(Integer, default=0)
    quantity_returned = Column(Integer, default=0)
    received_uom = Column(Text)
    base_quantity = Column(Integer)
    cost_price = Column(Numeric(10, 2))
    mrp = Column(Numeric(10, 2))
    supplier_id = Column(Integer)
    purchase_id = Column(Integer)
    purchase_invoice_number = Column(Text)
    branch_id = Column(Integer)
    location_code = Column(Text)
    rack_number = Column(Text)
    batch_status = Column(Text, default='active')
    is_blocked = Column(Boolean, default=False)
    block_reason = Column(Text)
    current_stock_status = Column(Text)
    notes = Column(Text)
    created_by = Column(Integer)
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_free_sample = Column(Boolean, default=False)
    is_physician_sample = Column(Boolean, default=False)
    temperature_log = Column(Text)
    qa_status = Column(Text, default='pending')
    qa_certificate_url = Column(Text)

# ----------------- CUSTOMERS -----------------
class Customer(Base):
    __tablename__ = "customers"
    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_name = Column(Text, nullable=False)
    contact_person = Column(Text)
    phone = Column(Text)
    email = Column(Text)
    address = Column(Text)
    city = Column(Text)
    state = Column(Text)
    gst_number = Column(Text)
    customer_type = Column(Text)
    credit_limit = Column(Numeric(10, 2))
    payment_terms = Column(Integer)
    # New wholesale business fields
    drug_license_number = Column(Text)  # Customer's drug license
    bank_account_number = Column(Text)
    bank_name = Column(Text)
    bank_ifsc_code = Column(Text)
    bank_branch = Column(Text)
    credit_terms_days = Column(Integer, default=30)  # Payment due days
    credit_used = Column(Numeric(10, 2), default=0)  # Current outstanding
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ----------------- SUPPLIERS -----------------
class Supplier(Base):
    __tablename__ = "suppliers"
    supplier_id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_name = Column(Text, nullable=False)
    contact_person = Column(Text)
    phone = Column(Text)
    email = Column(Text)
    address = Column(Text)
    city = Column(Text)
    state = Column(Text)
    country = Column(Text, default='India')
    gst_number = Column(Text)
    drug_license_number = Column(Text, nullable=False)  # Required for pharma suppliers
    
    # Banking details
    bank_account_number = Column(Text)
    bank_name = Column(Text)
    bank_ifsc_code = Column(Text)
    bank_branch = Column(Text)
    
    # Business terms
    credit_terms_days = Column(Integer, default=30)
    credit_limit = Column(Numeric(10, 2))
    credit_used = Column(Numeric(10, 2), default=0)
    
    # Supplier classification
    supplier_type = Column(Text)  # Manufacturer, Distributor, Wholesaler
    preferred_supplier = Column(Boolean, default=False)
    minimum_order_value = Column(Numeric(10, 2))
    
    # Status and dates
    is_active = Column(Boolean, default=True)
    onboarding_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# ----------------- MEDICAL REPRESENTATIVES -----------------
class MedicalRepresentative(Base):
    __tablename__ = "medical_representatives"
    mr_id = Column(Integer, primary_key=True, autoincrement=True)
    mr_name = Column(Text, nullable=False)
    employee_id = Column(Text)  # Company employee ID
    company = Column(Text)  # Pharmaceutical company they represent
    phone = Column(Text)
    email = Column(Text)
    territory = Column(Text)  # Area they cover
    
    # Commission and incentives
    commission_rate = Column(Numeric(5, 2))  # Percentage
    target_monthly = Column(Numeric(10, 2))  # Monthly sales target
    
    # Professional details
    qualification = Column(Text)
    experience_years = Column(Integer)
    joining_date = Column(Date)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# ----------------- REGULATORY LICENSES -----------------
class RegulatoryLicense(Base):
    __tablename__ = "regulatory_licenses"
    license_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # FIXED: Now properly connected to business entities
    entity_type = Column(Text, nullable=False)  # company, supplier, customer
    entity_id = Column(Integer)  # References supplier_id or customer_id
    company_license = Column(Boolean, default=False)  # True for company's own licenses
    
    license_type = Column(Text, nullable=False)  # Drug License, GST, Shop License, etc.
    license_number = Column(Text, nullable=False)
    license_name = Column(Text)  # Full license name/description
    
    # Issuing authority details
    issuing_authority = Column(Text, nullable=False)
    issuing_state = Column(Text)
    issuing_district = Column(Text)
    
    # Dates
    issue_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    renewal_due_date = Column(Date)  # Calculated field for reminders
    
    # Renewal management
    renewal_reminder_days = Column(Integer, default=60)  # Days before expiry to remind
    auto_renewal_enabled = Column(Boolean, default=False)
    renewal_fee = Column(Numeric(10, 2))
    
    # Document management
    license_document_path = Column(Text)  # File path for license copy
    renewal_application_path = Column(Text)
    
    # Status
    status = Column(Text, default='active')  # active, expired, suspended, renewed
    is_critical = Column(Boolean, default=True)  # Business critical license
    
    # NEW: Indian Regulatory Compliance Fields
    # CDSCO specific fields
    cdsco_license_category = Column(Text)  # Wholesale, Retail, Import, Manufacture
    cdsco_form_type = Column(Text)  # Form 20B, Form 21B, Form 27, etc.
    drug_schedule_covered = Column(Text)  # JSON array: ["G", "H", "H1", "X"]
    narcotic_license = Column(Boolean, default=False)  # For Schedule X
    psychotropic_license = Column(Boolean, default=False)  # For psychotropic substances
    
    # State Drug Controller specific
    state_drug_controller = Column(Text)  # Name of the state drug controller office
    regional_office = Column(Text)  # Regional office under state controller
    
    # License scope and restrictions
    authorized_activities = Column(Text)  # JSON array of authorized activities
    drug_categories_allowed = Column(Text)  # Categories of drugs allowed
    quantity_restrictions = Column(Text)  # Any quantity-based restrictions
    area_of_operation = Column(Text)  # Geographical area covered
    
    # Compliance tracking
    last_inspection_date = Column(Date)
    next_inspection_due = Column(Date)
    compliance_score = Column(Integer)  # Internal compliance rating
    violation_history = Column(Text)  # JSON array of past violations
    
    # Manual document upload tracking
    uploaded_documents = Column(Text)  # JSON array of uploaded document details
    document_verification_status = Column(Text, default='pending')  # pending, verified, rejected
    verified_by = Column(Integer, ForeignKey("users.user_id"))
    verification_date = Column(Date)
    verification_notes = Column(Text)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# NEW: Indian Compliance Tracking Tables
class CDSCOCompliance(Base):
    __tablename__ = "cdsco_compliance"
    compliance_id = Column(Integer, primary_key=True, autoincrement=True)
    license_id = Column(Integer, ForeignKey("regulatory_licenses.license_id"))
    
    # CDSCO specific tracking
    form_type = Column(Text, nullable=False)  # Form 20B, 21B, 27, etc.
    submission_date = Column(Date)
    acknowledgment_number = Column(Text)
    status = Column(Text, default='submitted')  # submitted, approved, rejected, expired
    
    # Drug recall tracking
    recall_notices_received = Column(Integer, default=0)
    recall_actions_completed = Column(Integer, default=0)
    
    # ADR (Adverse Drug Reaction) reporting
    adr_reports_filed = Column(Integer, default=0)
    last_adr_report_date = Column(Date)
    
    # Monthly reporting
    monthly_reports_due = Column(Integer, default=12)
    monthly_reports_filed = Column(Integer, default=0)
    last_monthly_report_date = Column(Date)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class StateDrugControllerCompliance(Base):
    __tablename__ = "state_drug_controller_compliance"
    compliance_id = Column(Integer, primary_key=True, autoincrement=True)
    license_id = Column(Integer, ForeignKey("regulatory_licenses.license_id"))
    state = Column(Text, nullable=False)
    
    # State-specific compliance
    state_license_number = Column(Text)
    regional_office = Column(Text)
    controlling_officer = Column(Text)
    
    # Inspection tracking
    last_inspection_date = Column(Date)
    next_inspection_due = Column(Date)
    inspection_result = Column(Text)  # satisfactory, needs_improvement, violation
    inspector_name = Column(Text)
    
    # State-specific reporting
    quarterly_reports_due = Column(Integer, default=4)
    quarterly_reports_filed = Column(Integer, default=0)
    last_quarterly_report_date = Column(Date)
    
    # Compliance status
    current_status = Column(Text, default='compliant')  # compliant, warning, violation
    penalty_amount = Column(Numeric(10, 2), default=0)
    penalty_paid = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class LicenseDocument(Base):
    __tablename__ = "license_documents"
    document_id = Column(Integer, primary_key=True, autoincrement=True)
    license_id = Column(Integer, ForeignKey("regulatory_licenses.license_id"))
    
    # Document details
    document_type = Column(Text, nullable=False)  # license_copy, renewal_application, compliance_certificate
    document_name = Column(Text, nullable=False)
    file_path = Column(Text, nullable=False)  # Path to uploaded file
    file_size = Column(Integer)  # File size in bytes
    file_format = Column(Text)  # pdf, jpg, png, etc.
    
    # Upload tracking
    uploaded_by = Column(Integer, ForeignKey("users.user_id"))
    upload_date = Column(DateTime, default=datetime.utcnow)
    
    # Verification
    verification_status = Column(Text, default='pending')  # pending, verified, rejected
    verified_by = Column(Integer, ForeignKey("users.user_id"))
    verification_date = Column(DateTime)
    verification_notes = Column(Text)
    
    # Document metadata
    is_current = Column(Boolean, default=True)  # Is this the current version
    version_number = Column(Integer, default=1)
    expires_on = Column(Date)  # If document has expiry
    
    created_at = Column(DateTime, default=datetime.utcnow)

# ----------------- ORDERS -----------------
class Order(Base):
    __tablename__ = "orders"
    order_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    mr_id = Column(Integer, ForeignKey("medical_representatives.mr_id"))  # Link to MR
    order_date = Column(DateTime, default=datetime.utcnow)
    
    # Invoice details
    invoice_no = Column(Text, unique=True)  # Frontend uses this
    invoice_date = Column(Date, default=datetime.utcnow)  # Frontend uses this
    due_date = Column(Date)  # Frontend uses this
    
    # Financial calculations
    gross_amount = Column(Numeric(10, 2))
    discount = Column(Numeric(10, 2))
    tax_amount = Column(Numeric(10, 2))
    final_amount = Column(Numeric(10, 2))
    round_off = Column(Numeric(10, 2), default=0)  # Frontend uses this
    
    # Transport and logistics
    transport_charges = Column(Numeric(10, 2), default=0)  # Frontend uses this
    transport_mode = Column(Text)  # Frontend uses this
    
    # Payment details
    payment_status = Column(Text, default='pending')
    payment_mode = Column(Text, default='CASH')  # Frontend uses this
    
    # Status and metadata
    status = Column(Text, default='placed')
    notes = Column(Text)  # Frontend uses this
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# ----------------- ORDER ITEMS -----------------
class OrderItem(Base):
    __tablename__ = "order_items"
    order_item_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id", ondelete="CASCADE"))
    batch_id = Column(Integer, ForeignKey("batches.batch_id"))
    quantity = Column(Integer)
    unit_price = Column(Numeric(10, 2))
    total_price = Column(Numeric(10, 2))

# ----------------- INVENTORY MOVEMENTS -----------------
class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    movement_id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("batches.batch_id"))
    movement_type = Column(Text)
    quantity = Column(Integer)
    movement_date = Column(DateTime, default=datetime.utcnow)
    reference = Column(Text)

# ----------------- PAYMENTS -----------------
class Payment(Base):
    __tablename__ = "payments"
    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)  # FIXED: Direct customer link
    
    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)
    payment_mode = Column(Text, nullable=False)
    payment_date = Column(DateTime, default=datetime.utcnow)
    reference_number = Column(Text)
    remarks = Column(Text)
    
    # Payment type and status
    payment_type = Column(Text, default='order_payment')  # order_payment, advance, adjustment
    status = Column(Text, default='completed')  # pending, completed, failed, reversed
    
    # Advanced payment tracking
    bank_name = Column(Text)
    transaction_id = Column(Text)
    processed_by = Column(Integer, ForeignKey("users.user_id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# NEW: Payment Allocation Table - Maps payments to orders (many-to-many)
class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"
    allocation_id = Column(Integer, primary_key=True, autoincrement=True)
    payment_id = Column(Integer, ForeignKey("payments.payment_id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    allocated_amount = Column(Numeric(10, 2), nullable=False)
    allocation_date = Column(DateTime, default=datetime.utcnow)
    remarks = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# NEW: Customer Advance Payments
class CustomerAdvancePayment(Base):
    __tablename__ = "customer_advance_payments"
    advance_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.payment_id"), nullable=False)
    
    advance_amount = Column(Numeric(10, 2), nullable=False)
    used_amount = Column(Numeric(10, 2), default=0)
    remaining_amount = Column(Numeric(10, 2), nullable=False)
    
    status = Column(Text, default='active')  # active, fully_used, expired
    expiry_date = Column(Date)  # Optional expiry for advance payments
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# ----------------- SALES RETURNS -----------------
class SalesReturn(Base):
    __tablename__ = "sales_returns"
    return_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    return_date = Column(DateTime, default=datetime.utcnow)
    reason = Column(Text)
    refund_amount = Column(Numeric(10, 2))

# ----------------- USERS -----------------
class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    role = Column(Text)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# ----------------- PURCHASES -----------------
class Purchase(Base):
    __tablename__ = "purchases"
    purchase_id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.supplier_id"))  # Link to supplier
    supplier_name = Column(Text, nullable=False)  # Keep for backward compatibility
    invoice_number = Column(Text)
    invoice_date = Column(Date)
    total_amount = Column(Numeric(10, 2))
    discount = Column(Numeric(10, 2), default=0)
    tax_amount = Column(Numeric(10, 2), default=0)
    final_amount = Column(Numeric(10, 2))
    payment_status = Column(Text, default='pending')
    status = Column(Text, default='received')  # received, partial, returned
    created_at = Column(DateTime, default=datetime.utcnow)

# ----------------- PURCHASE ITEMS -----------------
class PurchaseItem(Base):
    __tablename__ = "purchase_items"
    purchase_item_id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_id = Column(Integer, ForeignKey("purchases.purchase_id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    batch_number = Column(Text)
    expiry_date = Column(Date)
    quantity = Column(Integer)
    purchase_price = Column(Numeric(10, 2))

# ----------------- TAX ENTRIES -----------------
class TaxEntry(Base):
    __tablename__ = "tax_entries"
    tax_entry_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_type = Column(Text, nullable=False)  # sale, purchase, return
    
    # Foreign key connections
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=True)  # For sales
    purchase_id = Column(Integer, ForeignKey("purchases.purchase_id"), nullable=True)  # For purchases
    return_id = Column(Integer, ForeignKey("sales_returns.return_id"), nullable=True)  # For returns
    
    # Tax details
    tax_type = Column(Text, nullable=False)  # CGST, SGST, IGST
    tax_percent = Column(Numeric(5, 2))
    tax_amount = Column(Numeric(10, 2))
    taxable_amount = Column(Numeric(10, 2))  # Base amount on which tax calculated
    
    # GST specific
    gst_type = Column(Text)  # intra-state, inter-state
    hsn_code = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# ----------------- JOURNAL ENTRIES -----------------
class JournalEntry(Base):
    __tablename__ = "journal_entries"
    entry_id = Column(Integer, primary_key=True, autoincrement=True)
    entry_date = Column(Date, default=datetime.utcnow)
    
    # Reference connections
    transaction_type = Column(Text)  # sale, purchase, payment, expense, etc.
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=True)
    purchase_id = Column(Integer, ForeignKey("purchases.purchase_id"), nullable=True)
    payment_id = Column(Integer, ForeignKey("payments.payment_id"), nullable=True)
    vendor_payment_id = Column(Integer, ForeignKey("vendor_payments.vendor_payment_id"), nullable=True)
    
    # Accounting details
    account_name = Column(Text)
    account_type = Column(Text)  # asset, liability, income, expense, equity
    debit_amount = Column(Numeric(10, 2))
    credit_amount = Column(Numeric(10, 2))
    
    # Additional info
    reference = Column(Text)
    remarks = Column(Text)
    voucher_number = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# ----------------- VENDOR PAYMENTS -----------------
class VendorPayment(Base):
    __tablename__ = "vendor_payments"
    vendor_payment_id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_id = Column(Integer, ForeignKey("purchases.purchase_id"))
    supplier_name = Column(Text)
    amount_paid = Column(Numeric(10, 2))
    payment_date = Column(DateTime, default=datetime.utcnow)
    payment_mode = Column(Text)
    remarks = Column(Text)

# ----------------- CART -----------------
class Cart(Base):
    __tablename__ = "carts"
    cart_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255))  # Using String for user_id to support both numeric IDs and auth user IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

# ----------------- CART ITEMS -----------------
class CartItem(Base):
    __tablename__ = "cart_items"
    cart_item_id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey("carts.cart_id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    batch_id = Column(Integer, ForeignKey("batches.batch_id"), nullable=True)
    quantity = Column(Integer, default=1)
    added_at = Column(DateTime, default=datetime.utcnow)
    cart = relationship("Cart", back_populates="items")

# ----------------- PRICE HISTORY -----------------
class PriceHistory(Base):
    __tablename__ = "price_history"
    price_history_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.batch_id"), nullable=True)
    
    # Price changes
    old_mrp = Column(Numeric(10, 2))
    new_mrp = Column(Numeric(10, 2))
    old_sale_price = Column(Numeric(10, 2))
    new_sale_price = Column(Numeric(10, 2))
    old_purchase_price = Column(Numeric(10, 2))
    new_purchase_price = Column(Numeric(10, 2))
    
    # Change details
    change_reason = Column(Text)  # market_rate, supplier_change, promotion, etc.
    effective_date = Column(Date, nullable=False)
    changed_by = Column(Integer, ForeignKey("users.user_id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)

# ----------------- DISCOUNT SCHEMES WITH PROPER RELATIONSHIPS -----------------
class DiscountScheme(Base):
    __tablename__ = "discount_schemes"
    scheme_id = Column(Integer, primary_key=True, autoincrement=True)
    scheme_name = Column(Text, nullable=False)
    scheme_description = Column(Text)
    
    # Discount details
    discount_type = Column(Text, nullable=False)  # percentage, fixed_amount, buy_x_get_y
    discount_value = Column(Numeric(10, 2))  # Amount or percentage
    max_discount_amount = Column(Numeric(10, 2))  # Cap on discount
    
    # FIXED: Proper targeting
    target_type = Column(Text, default='all')  # all, customer_type, specific_customers, product_category, specific_products
    target_customer_types = Column(Text)  # JSON array of customer types
    target_categories = Column(Text)  # JSON array of product categories
    
    # Conditions
    min_quantity = Column(Integer, default=1)
    min_order_value = Column(Numeric(10, 2))
    
    # Validity
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    max_uses_per_customer = Column(Integer)  # Limit uses per customer
    total_usage_limit = Column(Integer)  # Total usage limit
    current_usage_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# NEW: Applied Discounts - Track actual discount usage
class AppliedDiscount(Base):
    __tablename__ = "applied_discounts"
    applied_discount_id = Column(Integer, primary_key=True, autoincrement=True)
    scheme_id = Column(Integer, ForeignKey("discount_schemes.scheme_id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    
    discount_amount = Column(Numeric(10, 2), nullable=False)
    applied_date = Column(DateTime, default=datetime.utcnow)
    
    # Details
    original_amount = Column(Numeric(10, 2))
    final_amount = Column(Numeric(10, 2))
    discount_percentage_used = Column(Numeric(5, 2))
    
    created_at = Column(DateTime, default=datetime.utcnow)

# NEW: Product-Discount Targeting (Many-to-Many)
class DiscountProduct(Base):
    __tablename__ = "discount_products"
    discount_product_id = Column(Integer, primary_key=True, autoincrement=True)
    scheme_id = Column(Integer, ForeignKey("discount_schemes.scheme_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# NEW: Customer-Discount Targeting (Many-to-Many) 
class DiscountCustomer(Base):
    __tablename__ = "discount_customers"
    discount_customer_id = Column(Integer, primary_key=True, autoincrement=True)
    scheme_id = Column(Integer, ForeignKey("discount_schemes.scheme_id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    usage_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# ----------------- CUSTOMER CREDIT MANAGEMENT -----------------
class CustomerCreditNote(Base):
    __tablename__ = "customer_credit_notes"
    credit_note_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=True)
    
    # Credit details
    credit_amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(Text, nullable=False)  # return, damage, pricing_error, goodwill
    credit_type = Column(Text, default='refund')  # refund, adjustment, carry_forward
    
    # Status and dates
    issue_date = Column(Date, default=datetime.utcnow)
    expiry_date = Column(Date)  # If credit expires
    status = Column(Text, default='issued')  # issued, used, expired, cancelled
    used_amount = Column(Numeric(10, 2), default=0)
    remaining_amount = Column(Numeric(10, 2))
    
    # References
    reference_invoice = Column(Text)
    approved_by = Column(Integer, ForeignKey("users.user_id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)

class CustomerOutstanding(Base):
    __tablename__ = "customer_outstanding"
    outstanding_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    
    # Outstanding details
    total_amount = Column(Numeric(10, 2), nullable=False)
    paid_amount = Column(Numeric(10, 2), default=0)
    outstanding_amount = Column(Numeric(10, 2), nullable=False)
    
    # Due date management
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    overdue_days = Column(Integer, default=0)
    
    # Status
    status = Column(Text, default='pending')  # pending, partial, paid, overdue
    payment_reminder_sent = Column(Integer, default=0)  # Count of reminders
    last_reminder_date = Column(Date)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# ----------------- PURCHASE RETURNS -----------------
class PurchaseReturn(Base):
    __tablename__ = "purchase_returns"
    return_id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_id = Column(Integer, ForeignKey("purchases.purchase_id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.supplier_id"), nullable=False)
    
    # Return details
    return_date = Column(Date, default=datetime.utcnow)
    return_invoice_number = Column(Text)
    total_return_amount = Column(Numeric(10, 2))
    
    # Return reason
    reason = Column(Text, nullable=False)  # expired, damaged, wrong_item, quality_issue
    return_type = Column(Text, default='full')  # full, partial
    
    # Status and processing
    status = Column(Text, default='initiated')  # initiated, approved, shipped, refunded
    refund_amount = Column(Numeric(10, 2))
    refund_date = Column(Date)
    refund_mode = Column(Text)  # cash, bank_transfer, credit_note, adjustment
    
    # References
    debit_note_number = Column(Text)
    processed_by = Column(Integer, ForeignKey("users.user_id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class PurchaseReturnItem(Base):
    __tablename__ = "purchase_return_items"
    return_item_id = Column(Integer, primary_key=True, autoincrement=True)
    return_id = Column(Integer, ForeignKey("purchase_returns.return_id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    batch_id = Column(Integer, ForeignKey("batches.batch_id"))
    
    # Return quantities
    original_quantity = Column(Integer)
    return_quantity = Column(Integer)
    unit_price = Column(Numeric(10, 2))
    total_return_value = Column(Numeric(10, 2))
    
    # Item condition
    item_condition = Column(Text)  # expired, damaged, intact
    reason_specific = Column(Text)  # Specific reason for this item
    
    created_at = Column(DateTime, default=datetime.utcnow)

# ----------------- MULTI-LOCATION INVENTORY -----------------
class StorageLocation(Base):
    __tablename__ = "storage_locations"
    location_id = Column(Integer, primary_key=True, autoincrement=True)
    location_name = Column(Text, nullable=False)
    location_code = Column(Text, unique=True)  # Short code like "WH01", "STORE-A"
    location_type = Column(Text)  # warehouse, store, cold_storage, counter
    
    # Physical details
    address = Column(Text)
    capacity = Column(Integer)  # Total capacity in units
    current_occupancy = Column(Integer, default=0)
    
    # Environmental controls
    temperature_controlled = Column(Boolean, default=False)
    temperature_range_min = Column(Numeric(5, 2))
    temperature_range_max = Column(Numeric(5, 2))
    humidity_controlled = Column(Boolean, default=False)
    humidity_range_min = Column(Numeric(5, 2))
    humidity_range_max = Column(Numeric(5, 2))
    
    # Security and access
    security_level = Column(Text, default='standard')  # high, standard, basic
    access_restricted = Column(Boolean, default=False)
    
    # Manager and contact
    location_manager = Column(Integer, ForeignKey("users.user_id"))
    contact_phone = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class BatchLocation(Base):
    __tablename__ = "batch_locations"
    batch_location_id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("batches.batch_id"), nullable=False)
    location_id = Column(Integer, ForeignKey("storage_locations.location_id"), nullable=False)
    
    # Quantity tracking
    quantity_stored = Column(Integer, nullable=False)
    reserved_quantity = Column(Integer, default=0)  # Reserved for orders
    available_quantity = Column(Integer)  # quantity_stored - reserved_quantity
    
    # Location details within storage
    rack_number = Column(Text)
    shelf_number = Column(Text)
    bin_number = Column(Text)
    
    # Tracking
    moved_in_date = Column(DateTime, default=datetime.utcnow)
    last_movement_date = Column(DateTime, default=datetime.utcnow)
    moved_by = Column(Integer, ForeignKey("users.user_id"))
    
    # Status
    status = Column(Text, default='active')  # active, moved_out, quarantined
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# NEW: Inventory Triggers and Real-time Updates
class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("batches.batch_id"), nullable=False)
    
    # Transaction details
    transaction_type = Column(Text, nullable=False)  # sale, purchase, return, adjustment, transfer
    quantity_change = Column(Integer, nullable=False)  # Positive for in, negative for out
    
    # Reference to triggering entity
    reference_type = Column(Text)  # order_item, purchase_item, return_item, manual_adjustment
    reference_id = Column(Integer)  # ID of the triggering record
    
    # Before/After quantities for audit
    quantity_before = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    
    # Transaction metadata
    transaction_date = Column(DateTime, default=datetime.utcnow)
    performed_by = Column(Integer, ForeignKey("users.user_id"))
    remarks = Column(Text)
    
    # Automatic transaction flag
    is_automatic = Column(Boolean, default=True)  # True for system-generated, False for manual
    
    created_at = Column(DateTime, default=datetime.utcnow)

# NEW: Real-time Inventory Status View (Computed)
class BatchInventoryStatus(Base):
    __tablename__ = "batch_inventory_status"
    batch_id = Column(Integer, ForeignKey("batches.batch_id"), primary_key=True)
    
    # Current quantities (updated by triggers)
    current_quantity = Column(Integer, nullable=False, default=0)
    reserved_quantity = Column(Integer, default=0)  # Reserved for pending orders
    available_quantity = Column(Integer, default=0)  # current - reserved
    
    # Thresholds
    minimum_stock_level = Column(Integer, default=10)
    reorder_level = Column(Integer, default=20)
    maximum_stock_level = Column(Integer, default=1000)
    
    # Status flags
    is_out_of_stock = Column(Boolean, default=False)
    is_low_stock = Column(Boolean, default=False)
    needs_reorder = Column(Boolean, default=False)
    
    # Last updated
    last_transaction_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)

# NEW: CHALLAN/DISPATCH ARCHITECTURE - MISSING FROM CURRENT SYSTEM
class Challan(Base):
    __tablename__ = "challans"
    challan_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    
    # Challan details
    challan_number = Column(Text, nullable=False, unique=True)
    challan_date = Column(Date, default=datetime.utcnow)
    dispatch_date = Column(Date)
    expected_delivery_date = Column(Date)
    
    # Transport details
    vehicle_number = Column(Text)
    driver_name = Column(Text)
    driver_phone = Column(Text)
    transport_company = Column(Text)
    lr_number = Column(Text)  # Lorry Receipt Number
    freight_amount = Column(Numeric(10, 2), default=0)
    
    # Delivery address (can be different from customer address)
    delivery_address = Column(Text)
    delivery_city = Column(Text)
    delivery_state = Column(Text)
    delivery_pincode = Column(Text)
    delivery_contact_person = Column(Text)
    delivery_contact_phone = Column(Text)
    
    # Status tracking
    status = Column(Text, default='prepared')  # prepared, dispatched, in_transit, delivered, returned
    dispatch_time = Column(DateTime)
    delivery_time = Column(DateTime)
    
    # Additional details
    remarks = Column(Text)
    special_instructions = Column(Text)
    total_packages = Column(Integer, default=1)
    total_weight = Column(Numeric(10, 2))
    
    # Tracking
    prepared_by = Column(Integer, ForeignKey("users.user_id"))
    dispatched_by = Column(Integer, ForeignKey("users.user_id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class ChallanItem(Base):
    __tablename__ = "challan_items"
    challan_item_id = Column(Integer, primary_key=True, autoincrement=True)
    challan_id = Column(Integer, ForeignKey("challans.challan_id", ondelete="CASCADE"))
    order_item_id = Column(Integer, ForeignKey("order_items.order_item_id"))
    batch_id = Column(Integer, ForeignKey("batches.batch_id"))
    
    # Dispatch quantities
    ordered_quantity = Column(Integer, nullable=False)
    dispatched_quantity = Column(Integer, nullable=False)
    pending_quantity = Column(Integer, default=0)  # If partial dispatch
    
    # Item details for challan
    product_name = Column(Text)  # Copy for challan printing
    batch_number = Column(Text)
    expiry_date = Column(Date)
    unit_price = Column(Numeric(10, 2))
    
    # Package details
    package_type = Column(Text)  # Box, Carton, etc.
    packages_count = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class ChallanTracking(Base):
    __tablename__ = "challan_tracking"
    tracking_id = Column(Integer, primary_key=True, autoincrement=True)
    challan_id = Column(Integer, ForeignKey("challans.challan_id"))
    
    # Tracking details
    location = Column(Text)
    status = Column(Text)  # picked_up, in_transit, out_for_delivery, delivered
    timestamp = Column(DateTime, default=datetime.utcnow)
    remarks = Column(Text)
    
    # Person updating
    updated_by = Column(Integer, ForeignKey("users.user_id"))
    updated_by_name = Column(Text)  # For external updates
    
    created_at = Column(DateTime, default=datetime.utcnow)

# ----------------- NEW MODELS FOR PHASE 2 PRIORITY 3 -----------------

# User Management Models
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    permissions = Column(Text)  # JSON string of permissions
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    resource = Column(String(50))  # e.g., "orders", "customers"
    action = Column(String(50))    # e.g., "create", "read", "update", "delete"
    created_at = Column(DateTime, default=datetime.utcnow)

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    session_token = Column(Text, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Loyalty Program Models
class LoyaltyAccount(Base):
    __tablename__ = "loyalty_accounts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    points_balance = Column(Integer, default=0)
    total_points_earned = Column(Integer, default=0)
    total_points_redeemed = Column(Integer, default=0)
    tier = Column(String(20), default="bronze")  # bronze, silver, gold, platinum
    is_active = Column(Boolean, default=True)
    last_activity_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class PointsTransaction(Base):
    __tablename__ = "points_transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    loyalty_account_id = Column(Integer, ForeignKey("loyalty_accounts.id"), nullable=False)
    points = Column(Integer, nullable=False)  # Positive for earning, negative for redemption
    transaction_type = Column(String(50), nullable=False)  # purchase, redemption, bonus, etc.
    reference_id = Column(Integer)  # Order ID or other reference
    description = Column(Text)
    transaction_date = Column(DateTime, default=datetime.utcnow)

class Reward(Base):
    __tablename__ = "rewards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    points_required = Column(Integer, nullable=False)
    category = Column(String(50))  # discount, gift, service
    required_tier = Column(String(20), default="bronze")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class RewardRedemption(Base):
    __tablename__ = "reward_redemptions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    loyalty_account_id = Column(Integer, ForeignKey("loyalty_accounts.id"), nullable=False)
    reward_id = Column(Integer, ForeignKey("rewards.id"), nullable=False)
    points_used = Column(Integer, nullable=False)
    status = Column(String(20), default="redeemed")  # redeemed, used, expired
    redemption_date = Column(DateTime, default=datetime.utcnow)

# Compliance Models
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    action = Column(String(50), nullable=False)  # CREATE, READ, UPDATE, DELETE
    entity_type = Column(String(50), nullable=False)  # orders, customers, etc.
    entity_id = Column(Integer)
    details = Column(Text)  # JSON string with details
    timestamp = Column(DateTime, default=datetime.utcnow)

class License(Base):
    __tablename__ = "licenses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    license_type = Column(String(100), nullable=False)
    license_number = Column(String(100), unique=True, nullable=False)
    issuing_authority = Column(String(200))
    issue_date = Column(Date)
    expiry_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class RegulatoryReport(Base):
    __tablename__ = "regulatory_reports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_type = Column(String(100), nullable=False)
    title = Column(String(200))
    content = Column(Text)
    status = Column(String(20), default="draft")  # draft, submitted, approved
    created_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow)

class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    check_type = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="pending")  # pending, resolved, failed
    resolution_notes = Column(Text)
    resolved_by = Column(Integer, ForeignKey("users.user_id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

# Note: FileUpload model is already defined at the top of this file

# ----------------- STOCK ADJUSTMENTS -----------------
class StockAdjustment(Base):
    __tablename__ = "stock_adjustments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    adjustment_type = Column(String(50), nullable=False)  # increase, decrease, correction
    adjustment_date = Column(DateTime, default=datetime.utcnow)
    total_items = Column(Integer, nullable=False)
    total_value = Column(Numeric(10, 2), nullable=False)
    reason = Column(Text, nullable=False)
    approved_by = Column(Integer, ForeignKey("users.user_id"))
    reference_number = Column(String(100))
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="pending")  # pending, approved, rejected
    
    # Relationships
    items = relationship("StockAdjustmentItem", back_populates="adjustment", cascade="all, delete-orphan")

class StockAdjustmentItem(Base):
    __tablename__ = "stock_adjustment_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    adjustment_id = Column(Integer, ForeignKey("stock_adjustments.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    batch_id = Column(Integer, ForeignKey("batches.batch_id"), nullable=True)
    quantity_before = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    quantity_adjusted = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(10, 2))
    total_cost = Column(Numeric(10, 2))
    remarks = Column(Text)
    
    # Relationships
    adjustment = relationship("StockAdjustment", back_populates="items")
    product = relationship("Product")
    batch = relationship("Batch")
