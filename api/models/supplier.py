"""
Supplier model definition
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class Supplier(Base):
    """Supplier/Vendor model"""
    __tablename__ = "suppliers"
    
    supplier_id = Column(Integer, primary_key=True, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.org_id"), nullable=False)
    
    # Identification
    supplier_code = Column(String(50), nullable=False, unique=True)
    supplier_name = Column(String(255), nullable=False)
    company_name = Column(String(255))
    supplier_type = Column(String(50), default="pharmaceutical")
    
    # Contact information
    contact_person = Column(String(100))
    phone = Column(String(15), nullable=False)
    alternate_phone = Column(String(15))
    email = Column(String(100))
    
    # Address
    address = Column(Text)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(10))
    
    # Regulatory
    gst_number = Column(String(15))
    pan_number = Column(String(10))
    drug_license_number = Column(String(100))
    
    # Payment terms
    credit_period_days = Column(Integer, default=30)
    credit_limit = Column(Numeric(12, 2))
    payment_terms = Column(Text)
    payment_method = Column(String(50))
    
    # Banking
    bank_name = Column(String(100))
    account_number = Column(String(50))
    ifsc_code = Column(String(11))
    
    # Business metrics
    total_purchases = Column(Numeric(15, 2), default=0)
    outstanding_amount = Column(Numeric(12, 2), default=0)
    last_purchase_date = Column(Date)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="suppliers")
    purchases = relationship("Purchase", back_populates="supplier")
    
    def __repr__(self):
        return f"<Supplier(id={self.supplier_id}, name={self.supplier_name}, code={self.supplier_code})>"