"""
SQLAlchemy models generated from actual database schema
Auto-generated to match the existing database exactly
"""

from sqlalchemy import Column, String, Integer, BigInteger, Float, Date, DateTime, ForeignKey, Text, Numeric, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

try:
    from .database import Base
except ImportError:
    from database import Base

class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(String, nullable=True)  # Made nullable to avoid FK issues
    product_code = Column(Text, nullable=False)
    product_name = Column(Text, nullable=False)
    generic_name = Column(Text)
    brand_name = Column(Text)
    manufacturer = Column(Text)
    manufacturer_code = Column(Text)
    category = Column(Text)
    subcategory = Column(Text)
    category_id = Column(Integer)
    product_type_id = Column(Integer)
    base_uom_code = Column(Text, default="PIECE")
    purchase_uom_code = Column(Text)
    sale_uom_code = Column(Text)
    display_uom_code = Column(Text)
    allow_loose_units = Column(Boolean, default=False)
    hsn_code = Column(Text)
    drug_schedule = Column(Text)
    prescription_required = Column(Boolean, default=False)
    is_controlled_substance = Column(Boolean, default=False)
    purchase_price = Column(Numeric)
    sale_price = Column(Numeric)
    mrp = Column(Numeric)
    trade_discount_percent = Column(Numeric)
    gst_percent = Column(Numeric)
    cgst_percent = Column(Numeric)
    sgst_percent = Column(Numeric)
    igst_percent = Column(Numeric)
    tax_category = Column(Text, default="standard")
    minimum_stock_level = Column(Integer)
    maximum_stock_level = Column(Integer)
    reorder_level = Column(Integer)
    reorder_quantity = Column(Integer)
    pack_size = Column(Text)
    pack_details = Column(JSON)
    barcode = Column(Text)
    barcode_type = Column(Text, default="EAN13")
    alternate_barcodes = Column(String)
    storage_location = Column(Text)
    shelf_life_days = Column(Integer)
    notes = Column(Text)
    tags = Column(String)
    search_keywords = Column(String)
    category_path = Column(Text)
    is_active = Column(Boolean, default=True)
    is_discontinued = Column(Boolean, default=False)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_narcotic = Column(Boolean, default=False)
    requires_cold_chain = Column(Boolean, default=False)
    temperature_range = Column(Text)
    is_habit_forming = Column(Boolean, default=False)
    therapeutic_category = Column(Text)
    salt_composition = Column(Text)
    strength = Column(Text)
    pack_type = Column(Text)


class Batch(Base):
    __tablename__ = "batches"

    batch_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(String, nullable=True)  # Made nullable to avoid FK issues
    product_id = Column(Integer, nullable=False)
    batch_number = Column(Text, nullable=False)
    lot_number = Column(Text)
    serial_number = Column(Text)
    manufacturing_date = Column(Date)
    expiry_date = Column(Date, nullable=False)
    days_to_expiry = Column(Integer)
    is_near_expiry = Column(Boolean, default=False)
    quantity_received = Column(Integer, nullable=False)
    quantity_available = Column(Integer, nullable=False)
    quantity_sold = Column(Integer)
    quantity_damaged = Column(Integer)
    quantity_returned = Column(Integer)
    received_uom = Column(Text)
    base_quantity = Column(Integer)
    cost_price = Column(Numeric)
    selling_price = Column(Numeric)
    mrp = Column(Numeric)
    supplier_id = Column(Integer)
    purchase_id = Column(Integer)
    purchase_invoice_number = Column(Text)
    branch_id = Column(Integer)
    location_code = Column(Text)
    rack_number = Column(Text)
    batch_status = Column(Text, default="active")
    is_blocked = Column(Boolean, default=False)
    block_reason = Column(Text)
    current_stock_status = Column(Text)
    notes = Column(Text)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_free_sample = Column(Boolean, default=False)
    is_physician_sample = Column(Boolean, default=False)
    temperature_log = Column(JSON)
    qa_status = Column(Text, default="pending")
    qa_certificate_url = Column(Text)


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(String, nullable=True)  # Made nullable to avoid FK issues
    customer_code = Column(Text, nullable=False)
    customer_name = Column(Text, nullable=False)
    customer_type = Column(Text, default="retail")
    business_type = Column(Text)
    phone = Column(Text)
    alternate_phone = Column(Text)
    email = Column(Text)
    address = Column(Text)
    city = Column(Text)
    state = Column(Text)
    pincode = Column(Text)
    landmark = Column(Text)
    gst_number = Column(Text)
    pan_number = Column(Text)
    drug_license_number = Column(Text)
    food_license_number = Column(Text)
    credit_limit = Column(Numeric)
    credit_period_days = Column(Integer)
    payment_terms = Column(Text)
    price_list_id = Column(Integer)
    discount_percent = Column(Numeric)
    assigned_sales_rep = Column(Integer)
    customer_group = Column(Text)
    loyalty_points = Column(Integer)
    total_business = Column(Numeric)
    outstanding_amount = Column(Numeric)
    last_order_date = Column(Date)
    order_count = Column(Integer)
    is_active = Column(Boolean, default=True)
    blacklisted = Column(Boolean, default=False)
    blacklist_reason = Column(Text)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    customer_category = Column(Text)
    monthly_potential = Column(Numeric)
    preferred_payment_mode = Column(Text)
    collection_route = Column(Text)
    visiting_days = Column(String)


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(String, nullable=True)  # Made nullable to avoid FK issues
    order_number = Column(Text, nullable=False)
    order_date = Column(Date, nullable=False)
    order_time = Column(String)
    customer_id = Column(Integer, nullable=False)
    customer_name = Column(Text)
    customer_phone = Column(Text)
    subtotal_amount = Column(Numeric)
    discount_amount = Column(Numeric)
    tax_amount = Column(Numeric)
    round_off_amount = Column(Numeric)
    final_amount = Column(Numeric)
    payment_mode = Column(Text, default="cash")
    payment_status = Column(Text, default="pending")
    paid_amount = Column(Numeric)
    balance_amount = Column(Numeric)
    invoice_number = Column(Text)
    invoice_date = Column(Date)
    payment_due_date = Column(Date)
    delivery_type = Column(Text, default="pickup")
    delivery_address = Column(Text)
    delivery_status = Column(Text, default="pending")
    delivered_date = Column(Date)
    order_status = Column(Text, default="pending")
    branch_id = Column(Integer)
    created_by = Column(Integer)
    approved_by = Column(Integer)
    notes = Column(Text)
    tags = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    prescription_required = Column(Boolean, default=False)
    prescription_id = Column(Integer)
    doctor_id = Column(Integer)
    is_urgent = Column(Boolean, default=False)
    delivery_slot = Column(Text)
    loyalty_points_earned = Column(Integer)
    loyalty_points_redeemed = Column(Integer)
    applied_scheme_id = Column(Integer)


class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    product_name = Column(Text)
    batch_id = Column(Integer)
    batch_number = Column(Text)
    expiry_date = Column(Date)
    quantity = Column(Integer, nullable=False)
    uom_code = Column(Text)
    base_quantity = Column(Integer)
    mrp = Column(Numeric)
    selling_price = Column(Numeric, nullable=False)
    discount_percent = Column(Numeric)
    discount_amount = Column(Numeric)
    tax_percent = Column(Numeric)
    tax_amount = Column(Numeric)
    total_price = Column(Numeric, nullable=False)
    item_status = Column(Text, default="active")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    role = Column(Text)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime)


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(String, nullable=True)  # Made nullable to avoid FK issues
    payment_number = Column(Text, nullable=False)
    payment_date = Column(Date, nullable=False)
    customer_id = Column(Integer)
    supplier_id = Column(Integer)
    payment_type = Column(Text, nullable=False)
    amount = Column(Numeric, nullable=False)
    payment_mode = Column(Text, nullable=False)
    reference_number = Column(Text)
    bank_name = Column(Text)
    payment_status = Column(Text, default="pending")
    cleared_date = Column(Date)
    branch_id = Column(Integer)
    created_by = Column(Integer)
    approved_by = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(String, nullable=True)  # Made nullable to avoid FK issues
    supplier_code = Column(Text, nullable=False)
    supplier_name = Column(Text, nullable=False)
    company_name = Column(Text)
    supplier_type = Column(Text, default="manufacturer")
    contact_person = Column(Text)
    phone = Column(Text)
    alternate_phone = Column(Text)
    email = Column(Text)
    address = Column(Text)
    city = Column(Text)
    state = Column(Text)
    pincode = Column(Text)
    gst_number = Column(Text)
    pan_number = Column(Text)
    drug_license_number = Column(Text)
    credit_period_days = Column(Integer)
    payment_terms = Column(Text)
    payment_method = Column(Text)
    bank_name = Column(Text)
    account_number = Column(Text)
    ifsc_code = Column(Text)
    total_purchases = Column(Numeric)
    outstanding_amount = Column(Numeric)
    last_purchase_date = Column(Date)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    rating = Column(Integer)
    notes = Column(Text)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Purchase(Base):
    __tablename__ = "purchases"

    purchase_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(String, nullable=True)  # Made nullable to avoid FK issues
    purchase_number = Column(Text, nullable=False)
    purchase_date = Column(Date, nullable=False)
    supplier_id = Column(Integer, nullable=False)
    supplier_name = Column(Text)
    supplier_invoice_number = Column(Text)
    supplier_invoice_date = Column(Date)
    subtotal_amount = Column(Numeric)
    discount_amount = Column(Numeric)
    tax_amount = Column(Numeric)
    other_charges = Column(Numeric)
    final_amount = Column(Numeric)
    payment_status = Column(Text, default="pending")
    paid_amount = Column(Numeric)
    payment_due_date = Column(Date)
    purchase_status = Column(Text, default="draft")
    grn_number = Column(Text)
    grn_date = Column(Date)
    branch_id = Column(Integer)
    created_by = Column(Integer)
    approved_by = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Organization(Base):
    __tablename__ = "organizations"

    org_id = Column(String, primary_key=True)
    org_name = Column(Text, nullable=False)
    business_type = Column(Text, default="pharmaceutical")
    company_registration_number = Column(Text)
    pan_number = Column(Text)
    gst_number = Column(Text)
    drug_license_number = Column(Text)
    primary_contact_name = Column(Text)
    primary_email = Column(Text)
    primary_phone = Column(Text)
    business_address = Column(JSON)
    plan_type = Column(Text, default="starter")
    subscription_status = Column(Text, default="active")
    subscription_start_date = Column(Date)
    subscription_end_date = Column(Date)
    max_users = Column(Integer)
    max_products = Column(Integer)
    max_customers = Column(Integer)
    max_monthly_transactions = Column(Integer)
    business_settings = Column(JSON, default="{}")
    features_enabled = Column(String, default="ARRAY['basic_erp")
    is_active = Column(Boolean, default=True)
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    business_hours = Column(JSON)
    delivery_areas = Column(JSON)
    min_order_value = Column(Numeric)
    delivery_charges = Column(Numeric)
    free_delivery_above = Column(Numeric)
    whatsapp_notifications = Column(Boolean, default=True)
    sms_provider_config = Column(JSON)
    payment_gateway_config = Column(JSON)


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    movement_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(String, nullable=True)  # Made nullable to avoid FK issues
    movement_date = Column(DateTime, default=datetime.utcnow)
    movement_type = Column(Text, nullable=False)
    product_id = Column(Integer, nullable=False)
    batch_id = Column(Integer)
    quantity_in = Column(Integer)
    quantity_out = Column(Integer)
    balance_quantity = Column(Integer)
    movement_uom = Column(Text)
    base_quantity_in = Column(Integer)
    base_quantity_out = Column(Integer)
    reference_type = Column(Text)
    reference_id = Column(Integer)
    reference_number = Column(Text)
    branch_id = Column(Integer)
    from_location = Column(Text)
    to_location = Column(Text)
    performed_by = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(String)
    category_name = Column(Text, nullable=False)
    parent_category_id = Column(Integer)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    is_system_defined = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UnitOfMeasure(Base):
    __tablename__ = "units_of_measure"

    uom_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(String)
    uom_code = Column(Text, nullable=False)
    uom_name = Column(Text, nullable=False)
    uom_category = Column(Text, nullable=False)
    base_unit = Column(Boolean, default=False)
    is_fractional = Column(Boolean, default=False)
    decimal_places = Column(Integer)
    is_system_defined = Column(Boolean, default=True)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class OrgUser(Base):
    __tablename__ = "org_users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(String, nullable=True)  # Made nullable to avoid FK issues
    full_name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    phone = Column(Text)
    employee_id = Column(Text)
    password_hash = Column(Text, nullable=False)
    auth_method = Column(Text, default="password")
    role = Column(Text, nullable=False)
    permissions = Column(JSON, default="{}")
    department = Column(Text)
    branch_access = Column(String)
    can_view_reports = Column(Boolean, default=False)
    can_modify_prices = Column(Boolean, default=False)
    can_approve_discounts = Column(Boolean, default=False)
    discount_limit_percent = Column(Numeric)
    last_login_at = Column(DateTime)
    login_attempts = Column(Integer)
    locked_until = Column(DateTime)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    auth_uid = Column(String)
    last_seen_at = Column(DateTime)
    app_metadata = Column(JSON, default="{}")


class OrgBranch(Base):
    __tablename__ = "org_branches"

    branch_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(String, nullable=True)  # Made nullable to avoid FK issues
    branch_name = Column(Text, nullable=False)
    branch_code = Column(Text, nullable=False)
    branch_type = Column(Text, default="retail")
    address = Column(JSON, nullable=False)
    phone = Column(Text)
    email = Column(Text)
    branch_manager_id = Column(Integer)
    branch_settings = Column(JSON, default="{}")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class PriceList(Base):
    __tablename__ = "price_lists"

    price_list_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(String, nullable=True)  # Made nullable to avoid FK issues
    list_name = Column(Text, nullable=False)
    list_type = Column(Text, nullable=False)
    currency = Column(Text, default="INR")
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date)
    calculation_type = Column(Text, default="fixed")
    base_price_list_id = Column(Integer)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TaxEntry(Base):
    __tablename__ = "tax_entries"

    tax_entry_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_type = Column(Text, nullable=False)
    order_id = Column(Integer)
    purchase_id = Column(Integer)
    return_id = Column(Integer)
    tax_type = Column(Text, nullable=False)
    tax_percent = Column(Numeric)
    tax_amount = Column(Numeric)
    taxable_amount = Column(Numeric)
    gst_type = Column(Text)
    hsn_code = Column(Text)
    created_at = Column(DateTime)


class ChallanItem(Base):
    __tablename__ = "challan_items"

    challan_item_id = Column(Integer, primary_key=True, autoincrement=True)
    challan_id = Column(Integer)
    order_item_id = Column(Integer)
    batch_id = Column(Integer)
    ordered_quantity = Column(Integer, nullable=False)
    dispatched_quantity = Column(Integer, nullable=False)
    pending_quantity = Column(Integer)
    product_name = Column(Text)
    batch_number = Column(Text)
    expiry_date = Column(Date)
    unit_price = Column(Numeric)
    package_type = Column(Text)
    packages_count = Column(Integer)
    created_at = Column(DateTime)


class Challan(Base):
    __tablename__ = "challans"

    challan_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, nullable=False)
    customer_id = Column(Integer, nullable=False)
    challan_number = Column(Text, nullable=False)
    challan_date = Column(Date)
    dispatch_date = Column(Date)
    expected_delivery_date = Column(Date)
    vehicle_number = Column(Text)
    driver_name = Column(Text)
    driver_phone = Column(Text)
    transport_company = Column(Text)
    lr_number = Column(Text)
    freight_amount = Column(Numeric)
    delivery_address = Column(Text)
    delivery_city = Column(Text)
    delivery_state = Column(Text)
    delivery_pincode = Column(Text)
    delivery_contact_person = Column(Text)
    delivery_contact_phone = Column(Text)
    status = Column(Text)
    dispatch_time = Column(DateTime)
    delivery_time = Column(DateTime)
    remarks = Column(Text)
    special_instructions = Column(Text)
    total_packages = Column(Integer)
    total_weight = Column(Numeric)
    prepared_by = Column(Integer)
    dispatched_by = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class SalesReturn(Base):
    __tablename__ = "sales_returns"

    return_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer)
    return_date = Column(DateTime)
    reason = Column(Text)
    refund_amount = Column(Numeric)


