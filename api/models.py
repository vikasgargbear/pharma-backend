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
    
    # Pack info
    pack_size = Column(Text)
    pack_details = Column(JSON)  # JSONB in database
    
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