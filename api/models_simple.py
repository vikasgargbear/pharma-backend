"""
Simplified models that should match a basic pharmaceutical database
Based on common patterns found in pharma systems
"""

from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey, Text, Numeric, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

try:
    from .database import Base
except ImportError:
    from database import Base

# Core models that most pharma databases have

class Product(Base):
    __tablename__ = "products"
    
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_code = Column(String(50), unique=True)
    product_name = Column(String(200), nullable=False)
    category = Column(String(100))
    manufacturer = Column(String(200))
    hsn_code = Column(String(20))
    gst_percent = Column(Numeric(5, 2))
    mrp = Column(Numeric(10, 2))
    sale_price = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Batch(Base):
    __tablename__ = "batches"
    
    batch_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.product_id"))
    batch_number = Column(String(100), nullable=False)
    manufacture_date = Column(Date)  # Common variations: mfg_date, manufacturing_date
    expiry_date = Column(Date, nullable=False)
    quantity_available = Column(Integer, default=0)
    purchase_price = Column(Numeric(10, 2))
    selling_price = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)

class Customer(Base):
    __tablename__ = "customers"
    
    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_name = Column(String(200), nullable=False)
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    gst_number = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"
    
    order_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    order_date = Column(DateTime, default=datetime.utcnow)
    invoice_no = Column(String(50), unique=True)
    gross_amount = Column(Numeric(10, 2))
    discount = Column(Numeric(10, 2), default=0)
    tax_amount = Column(Numeric(10, 2))
    final_amount = Column(Numeric(10, 2))
    payment_status = Column(String(20), default='pending')
    status = Column(String(20), default='placed')
    created_at = Column(DateTime, default=datetime.utcnow)

class OrderItem(Base):
    __tablename__ = "order_items"
    
    order_item_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    batch_id = Column(Integer, ForeignKey("batches.batch_id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2))
    total_price = Column(Numeric(10, 2))

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    
    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    amount = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(DateTime, default=datetime.utcnow)
    payment_mode = Column(String(50))
    status = Column(String(20), default='completed')
    created_at = Column(DateTime, default=datetime.utcnow)

# Add more models as we discover them from the actual database