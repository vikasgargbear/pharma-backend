"""
Clean SQLAlchemy models that match the actual database
"""
from sqlalchemy import Column, Integer, Text, Numeric, Boolean, DateTime, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from .database import Base

class Product(Base):
    __tablename__ = "products"
    
    # Primary key
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Organization (UUID in database)
    org_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Core fields
    product_code = Column(Text, nullable=False)
    product_name = Column(Text, nullable=False)
    generic_name = Column(Text)
    brand_name = Column(Text)
    manufacturer = Column(Text)
    manufacturer_code = Column(Text)
    
    # Categories
    category = Column(Text)
    subcategory = Column(Text)
    category_id = Column(Integer)
    product_type_id = Column(Integer)
    
    # UOM fields
    base_uom_code = Column(Text, default="PIECE")
    purchase_uom_code = Column(Text)
    sale_uom_code = Column(Text)
    display_uom_code = Column(Text)
    allow_loose_units = Column(Boolean, default=False)
    
    # Regulatory
    hsn_code = Column(Text)
    drug_schedule = Column(Text)
    prescription_required = Column(Boolean, default=False)
    is_controlled_substance = Column(Boolean, default=False)
    
    # Pricing
    purchase_price = Column(Numeric, default=0)
    sale_price = Column(Numeric, default=0)
    mrp = Column(Numeric, default=0)
    trade_discount_percent = Column(Numeric, default=0)
    
    # Tax
    gst_percent = Column(Numeric, default=12)
    cgst_percent = Column(Numeric, default=6)
    sgst_percent = Column(Numeric, default=6)
    igst_percent = Column(Numeric, default=12)
    tax_category = Column(Text, default="standard")
    
    # Stock levels
    minimum_stock_level = Column(Integer, default=0)
    maximum_stock_level = Column(Integer)
    reorder_level = Column(Integer)
    reorder_quantity = Column(Integer)
    
    # Pack info - original fields
    pack_size = Column(Text)
    pack_details = Column(JSON)  # JSONB in database
    
    # New pack configuration fields
    pack_input = Column(Text)  # Raw user input like '10*10' or '1*100ML'
    pack_quantity = Column(Integer)  # Quantity per unit (first number)
    pack_multiplier = Column(Integer)  # Multiplier or units per box (second number)
    pack_unit_type = Column(Text)  # Unit type like ML, GM, MG
    unit_count = Column(Integer)  # Units per package
    unit_measurement = Column(Text)  # Measurement with unit like '100ML'
    packages_per_box = Column(Integer)  # Packages per box
    
    # Barcode
    barcode = Column(Text)
    barcode_type = Column(Text, default="EAN13")
    alternate_barcodes = Column(ARRAY(Text))  # Array in database
    
    # Storage
    storage_location = Column(Text)
    shelf_life_days = Column(Integer)
    
    # Metadata
    notes = Column(Text)
    tags = Column(ARRAY(Text))  # Array in database
    search_keywords = Column(ARRAY(Text))  # Array in database
    category_path = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_discontinued = Column(Boolean, default=False)
    is_narcotic = Column(Boolean, default=False)
    requires_cold_chain = Column(Boolean, default=False)
    is_habit_forming = Column(Boolean, default=False)
    
    # Additional info
    temperature_range = Column(Text)
    therapeutic_category = Column(Text)
    salt_composition = Column(Text)
    strength = Column(Text)
    pack_type = Column(Text)
    
    # Audit
    created_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


# Minimal models to prevent import errors
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(Text)
    email = Column(Text)

class Customer(Base):
    __tablename__ = "customers"
    customer_id = Column(Integer, primary_key=True)
    customer_name = Column(Text)

class Batch(Base):
    __tablename__ = "batches"
    
    # Primary key
    batch_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    org_id = Column(UUID(as_uuid=True), nullable=False)
    product_id = Column(Integer, nullable=False)
    
    # Batch identification
    batch_number = Column(Text, nullable=False)
    lot_number = Column(Text)
    serial_number = Column(Text)
    
    # Dates
    manufacturing_date = Column(DateTime)
    expiry_date = Column(DateTime, nullable=False)
    days_to_expiry = Column(Integer)
    is_near_expiry = Column(Boolean, default=False)
    
    # Quantities
    quantity_received = Column(Integer, nullable=False)
    quantity_available = Column(Integer, nullable=False)
    quantity_sold = Column(Integer, default=0)
    quantity_damaged = Column(Integer, default=0)
    quantity_returned = Column(Integer, default=0)
    
    # UOM tracking
    received_uom = Column(Text)
    base_quantity = Column(Integer)
    
    # Pricing
    cost_price = Column(Numeric)
    selling_price = Column(Numeric)
    mrp = Column(Numeric)
    
    # Source
    supplier_id = Column(Integer)
    purchase_id = Column(Integer)
    purchase_invoice_number = Column(Text)
    
    # Location
    branch_id = Column(Integer)
    location_code = Column(Text)
    rack_number = Column(Text)
    
    # Status
    batch_status = Column(Text, default='active')
    is_blocked = Column(Boolean, default=False)
    block_reason = Column(Text)
    current_stock_status = Column(Text)
    
    # Metadata
    notes = Column(Text)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"
    order_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer)
    order_date = Column(DateTime)
    total_amount = Column(Numeric)

class OrderItem(Base):
    __tablename__ = "order_items"
    order_item_id = Column(Integer, primary_key=True)
    order_id = Column(Integer)
    product_id = Column(Integer)
    quantity = Column(Integer)
    price = Column(Numeric)

class Payment(Base):
    __tablename__ = "payments"
    payment_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer)
    amount = Column(Numeric)
    payment_date = Column(DateTime)

class Supplier(Base):
    __tablename__ = "suppliers"
    supplier_id = Column(Integer, primary_key=True)
    supplier_name = Column(Text)

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    movement_id = Column(Integer, primary_key=True)
    product_id = Column(Integer)
    movement_type = Column(Text)
    quantity = Column(Integer)

class SalesReturn(Base):
    __tablename__ = "sales_returns"
    return_id = Column(Integer, primary_key=True)
    order_id = Column(Integer)
    product_id = Column(Integer)
    quantity = Column(Integer)
    reason = Column(Text)

class Purchase(Base):
    __tablename__ = "purchases"
    purchase_id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer)
    purchase_date = Column(DateTime)