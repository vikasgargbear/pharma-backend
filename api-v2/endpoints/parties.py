"""
Parties API Endpoints - Customers and Suppliers
Direct mapping to parties schema with proper field names
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
import re

router = APIRouter()

# Pydantic Models matching our schema exactly

class CustomerBase(BaseModel):
    """Base customer model matching parties.customers table"""
    customer_code: str = Field(..., description="Unique customer code")
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_type: str = Field(..., pattern="^(pharmacy|hospital|clinic|distributor|other)$")
    primary_phone: str = Field(..., min_length=10, max_length=15)
    alternate_phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    
    # Flatten address fields (no more JSONB)
    billing_address: str
    billing_city: str
    billing_state: str
    billing_pincode: str
    billing_country: str = "India"
    
    shipping_address: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_pincode: Optional[str] = None
    shipping_country: Optional[str] = None
    
    # GST and compliance
    gst_number: Optional[str] = Field(None, pattern="^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
    gst_state_code: Optional[str] = Field(None, pattern="^[0-9]{2}$")
    pan_number: Optional[str] = Field(None, pattern="^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
    
    # License information
    drug_license_number: Optional[str] = None
    drug_license_expiry: Optional[datetime] = None
    fssai_number: Optional[str] = None
    
    # Credit management - NEW FIELD NAMES
    credit_limit: float = Field(default=0, ge=0)
    current_outstanding: float = Field(default=0)  # This was the issue!
    credit_days: int = Field(default=0, ge=0)
    payment_terms: Optional[str] = None
    
    # Categorization
    customer_group: Optional[str] = None
    customer_category: Optional[str] = None
    discount_percentage: float = Field(default=0, ge=0, le=100)
    
    # Preferences
    preferred_payment_mode: Optional[str] = None
    preferred_delivery_time: Optional[str] = None
    
    # Status
    status: str = Field(default="active", pattern="^(active|inactive|blocked)$")
    notes: Optional[str] = None
    
    @validator('email')
    def validate_email(cls, v):
        if v and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('shipping_address', always=True)
    def set_shipping_address(cls, v, values):
        if not v and 'billing_address' in values:
            return values['billing_address']
        return v

class CustomerCreate(CustomerBase):
    """Customer creation model"""
    pass

class CustomerUpdate(BaseModel):
    """Customer update model - all fields optional"""
    customer_name: Optional[str] = None
    customer_type: Optional[str] = None
    primary_phone: Optional[str] = None
    credit_limit: Optional[float] = None
    current_outstanding: Optional[float] = None
    status: Optional[str] = None
    # Add other fields as needed

class CustomerResponse(CustomerBase):
    """Customer response model with computed fields"""
    customer_id: int
    org_id: str
    available_credit: float = Field(description="credit_limit - current_outstanding")
    total_business: float = Field(default=0)
    last_transaction_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    @validator('available_credit', always=True)
    def calculate_available_credit(cls, v, values):
        return values.get('credit_limit', 0) - values.get('current_outstanding', 0)
    
    class Config:
        orm_mode = True

class CustomerListResponse(BaseModel):
    """Paginated customer list response"""
    success: bool = True
    data: List[CustomerResponse]
    meta: Dict[str, Any] = Field(default_factory=dict)

# API Endpoints

@router.get("/customers", response_model=CustomerListResponse)
async def list_customers(
    search: Optional[str] = Query(None, description="Search by name, code, phone, GST"),
    customer_type: Optional[str] = Query(None, pattern="^(pharmacy|hospital|clinic|distributor|other)$"),
    status: Optional[str] = Query(None, pattern="^(active|inactive|blocked)$"),
    has_outstanding: Optional[bool] = Query(None, description="Filter by outstanding balance"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("customer_name", description="Sort field"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$")
):
    """
    List customers with advanced filtering and pagination
    
    Features:
    - Search across multiple fields
    - Filter by type, status, outstanding
    - Pagination with metadata
    - Flexible sorting
    """
    # Mock data for now - will connect to database
    customers = [
        CustomerResponse(
            customer_id=1,
            org_id="123e4567-e89b-12d3-a456-426614174000",
            customer_code="CUST001",
            customer_name="ABC Pharmacy",
            customer_type="pharmacy",
            primary_phone="9876543210",
            email="abc@pharmacy.com",
            billing_address="123 Main Street",
            billing_city="Mumbai",
            billing_state="Maharashtra",
            billing_pincode="400001",
            gst_number="27ABCDE1234F1Z5",
            gst_state_code="27",
            credit_limit=100000,
            current_outstanding=25000,
            credit_days=30,
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]
    
    return CustomerListResponse(
        success=True,
        data=customers,
        meta={
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": 1,
                "total_pages": 1
            },
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0"
        }
    )

@router.get("/customers/search", response_model=CustomerListResponse)
async def search_customers(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Quick customer search for autocomplete
    
    Searches across:
    - Customer name
    - Customer code
    - Phone numbers
    - GST number
    """
    # Implementation here
    return CustomerListResponse(
        success=True,
        data=[],
        meta={"query": q, "limit": limit}
    )

@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int):
    """Get customer details by ID"""
    # Implementation here
    raise HTTPException(status_code=404, detail="Customer not found")

@router.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(customer: CustomerCreate):
    """
    Create new customer
    
    Features:
    - Auto-generate customer code if not provided
    - Validate GST/PAN format
    - Set default credit terms
    - Initialize outstanding to 0
    """
    # Implementation here
    pass

@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: int, customer: CustomerUpdate):
    """Update customer details"""
    # Implementation here
    pass

@router.post("/customers/{customer_id}/update-outstanding")
async def update_customer_outstanding(
    customer_id: int,
    amount: float = Query(..., description="Amount to add (positive) or subtract (negative)"),
    transaction_type: str = Query(..., pattern="^(invoice|payment|credit_note|debit_note)$"),
    reference_id: Optional[int] = Query(None, description="Reference document ID")
):
    """
    Update customer outstanding balance
    
    Used by:
    - Invoice creation (+)
    - Payment receipt (-)
    - Credit notes (-)
    - Debit notes (+)
    """
    # Implementation here
    return {
        "success": True,
        "data": {
            "customer_id": customer_id,
            "previous_outstanding": 25000,
            "adjustment": amount,
            "new_outstanding": 25000 + amount,
            "transaction_type": transaction_type,
            "reference_id": reference_id
        }
    }

@router.get("/customers/{customer_id}/credit-check")
async def check_customer_credit(
    customer_id: int,
    order_amount: float = Query(..., description="Proposed order amount")
):
    """
    Check if customer has sufficient credit for new order
    
    Returns:
    - available_credit
    - credit_status (ok, warning, blocked)
    - can_proceed (boolean)
    """
    # Mock implementation
    return {
        "success": True,
        "data": {
            "customer_id": customer_id,
            "credit_limit": 100000,
            "current_outstanding": 25000,
            "available_credit": 75000,
            "order_amount": order_amount,
            "after_order_outstanding": 25000 + order_amount,
            "credit_status": "ok" if order_amount <= 75000 else "blocked",
            "can_proceed": order_amount <= 75000,
            "message": "Credit available" if order_amount <= 75000 else "Credit limit exceeded"
        }
    }

@router.get("/customers/{customer_id}/transactions")
async def get_customer_transactions(
    customer_id: int,
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    transaction_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Get customer transaction history"""
    # Implementation here
    return {
        "success": True,
        "data": [],
        "meta": {
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": 0,
                "total_pages": 0
            }
        }
    }

# Backward compatibility endpoints for v1
@router.get("/customers/outstanding/{customer_id}")
async def get_customer_outstanding_v1(customer_id: int):
    """
    Legacy endpoint for v1 compatibility
    Maps outstanding_balance -> current_outstanding
    """
    return {
        "customer_id": customer_id,
        "outstanding_balance": 25000,  # Frontend expects this field
        "credit_limit": 100000,
        "available_credit": 75000
    }