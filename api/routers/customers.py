"""
Customers Router - All customer-related endpoints
Migrated from main.py for better modularity and maintainability
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models, schemas
from ..core.crud_base import create_crud
from ..core.security import handle_database_error

# Create router
router = APIRouter(prefix="/customers", tags=["customers"])

# Create CRUD instances using our generic system
customer_crud = create_crud(models.Customer)
credit_note_crud = create_crud(models.CustomerCreditNote)
outstanding_crud = create_crud(models.CustomerOutstanding)
advance_payment_crud = create_crud(models.CustomerAdvancePayment)

# ================= CUSTOMERS =================

@router.post("/", response_model=schemas.Customer)
@handle_database_error
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer"""
    return customer_crud.create(db, customer)

@router.get("/", response_model=List[schemas.Customer])
@handle_database_error
def read_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all customers with pagination"""
    return customer_crud.get_multi(db, skip=skip, limit=limit)

@router.get("/{customer_id}", response_model=schemas.Customer)
@handle_database_error
def read_customer(customer_id: int, db: Session = Depends(get_db)):
    """Get a specific customer by ID"""
    customer = customer_crud.get(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.put("/{customer_id}", response_model=schemas.Customer)
@handle_database_error
def update_customer(customer_id: int, customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    """Update an existing customer"""
    db_customer = customer_crud.get(db, customer_id)
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer_crud.update(db, db_obj=db_customer, obj_in=customer)

@router.delete("/{customer_id}")
@handle_database_error
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    """Delete a customer"""
    db_customer = customer_crud.get(db, customer_id)
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer_crud.remove(db, id=customer_id)

# ================= CUSTOMER CREDIT NOTES =================

@router.post("/credit-notes/", response_model=schemas.CustomerCreditNote)
@handle_database_error
def create_customer_credit_note(credit_note: schemas.CustomerCreditNoteCreate, db: Session = Depends(get_db)):
    """Create a customer credit note"""
    return credit_note_crud.create(db, credit_note)

@router.get("/credit-notes/", response_model=List[schemas.CustomerCreditNote])
@handle_database_error
def read_customer_credit_notes(customer_id: int = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get customer credit notes with optional filtering by customer"""
    if customer_id:
        return db.query(models.CustomerCreditNote).filter(
            models.CustomerCreditNote.customer_id == customer_id
        ).offset(skip).limit(limit).all()
    return credit_note_crud.get_multi(db, skip=skip, limit=limit)

@router.get("/credit-notes/{credit_note_id}", response_model=schemas.CustomerCreditNote)
@handle_database_error
def read_customer_credit_note(credit_note_id: int, db: Session = Depends(get_db)):
    """Get a specific customer credit note"""
    credit_note = credit_note_crud.get(db, credit_note_id)
    if not credit_note:
        raise HTTPException(status_code=404, detail="Credit note not found")
    return credit_note

@router.put("/credit-notes/{credit_note_id}", response_model=schemas.CustomerCreditNote)
@handle_database_error
def update_customer_credit_note(credit_note_id: int, credit_note: schemas.CustomerCreditNoteCreate, db: Session = Depends(get_db)):
    """Update a customer credit note"""
    db_credit_note = credit_note_crud.get(db, credit_note_id)
    if not db_credit_note:
        raise HTTPException(status_code=404, detail="Credit note not found")
    return credit_note_crud.update(db, db_obj=db_credit_note, obj_in=credit_note)

# ================= CUSTOMER OUTSTANDING =================

@router.post("/outstanding/", response_model=schemas.CustomerOutstanding)
@handle_database_error
def create_customer_outstanding(outstanding: schemas.CustomerOutstandingCreate, db: Session = Depends(get_db)):
    """Create customer outstanding record"""
    return outstanding_crud.create(db, outstanding)

@router.get("/outstanding/", response_model=List[schemas.CustomerOutstanding])
@handle_database_error
def read_customer_outstanding(customer_id: int = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get customer outstanding records with optional filtering by customer"""
    if customer_id:
        return db.query(models.CustomerOutstanding).filter(
            models.CustomerOutstanding.customer_id == customer_id
        ).offset(skip).limit(limit).all()
    return outstanding_crud.get_multi(db, skip=skip, limit=limit)

@router.get("/outstanding/{outstanding_id}", response_model=schemas.CustomerOutstanding)
@handle_database_error
def read_customer_outstanding_record(outstanding_id: int, db: Session = Depends(get_db)):
    """Get a specific customer outstanding record"""
    outstanding = outstanding_crud.get(db, outstanding_id)
    if not outstanding:
        raise HTTPException(status_code=404, detail="Outstanding record not found")
    return outstanding

@router.put("/outstanding/{outstanding_id}", response_model=schemas.CustomerOutstanding)
@handle_database_error
def update_customer_outstanding(outstanding_id: int, outstanding: schemas.CustomerOutstandingCreate, db: Session = Depends(get_db)):
    """Update customer outstanding record"""
    db_outstanding = outstanding_crud.get(db, outstanding_id)
    if not db_outstanding:
        raise HTTPException(status_code=404, detail="Outstanding record not found")
    return outstanding_crud.update(db, db_obj=db_outstanding, obj_in=outstanding)

# ================= CUSTOMER ADVANCE PAYMENTS =================

@router.get("/{customer_id}/advance-balance")
@handle_database_error
def get_customer_advance_balance(customer_id: int, db: Session = Depends(get_db)):
    """Get customer's advance payment balance"""
    # Verify customer exists
    customer = customer_crud.get(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Calculate advance balance
    total_balance = db.query(models.CustomerAdvancePayment).filter(
        models.CustomerAdvancePayment.customer_id == customer_id
    ).with_entities(
        models.CustomerAdvancePayment.remaining_balance
    ).scalar() or 0
    
    return {"customer_id": customer_id, "advance_balance": total_balance}

@router.get("/{customer_id}/advance-payments", response_model=List[schemas.CustomerAdvancePayment])
@handle_database_error
def get_customer_advance_payments(customer_id: int, db: Session = Depends(get_db)):
    """Get all advance payments for a customer"""
    # Verify customer exists
    customer = customer_crud.get(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return db.query(models.CustomerAdvancePayment).filter(
        models.CustomerAdvancePayment.customer_id == customer_id
    ).all()

@router.get("/{customer_id}/active-challans", response_model=List[schemas.Challan])
@handle_database_error
def get_customer_active_challans(customer_id: int, db: Session = Depends(get_db)):
    """Get active challans for a customer"""
    # Verify customer exists
    customer = customer_crud.get(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return db.query(models.Challan).filter(
        models.Challan.customer_id == customer_id,
        models.Challan.status.in_(["pending", "packed", "shipped"])
    ).all()

# ================= CUSTOMER PAYMENT OPERATIONS =================

@router.get("/{customer_id}/payment-summary")
@handle_database_error
def get_customer_payment_summary(customer_id: int, db: Session = Depends(get_db)):
    """Get comprehensive payment summary for customer"""
    # Verify customer exists
    customer = customer_crud.get(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get payment allocations
    payment_allocations = db.query(models.PaymentAllocation).join(
        models.Payment, models.PaymentAllocation.payment_id == models.Payment.id
    ).filter(
        models.Payment.customer_id == customer_id
    ).all()
    
    total_payments = sum(allocation.allocated_amount for allocation in payment_allocations)
    
    # Get outstanding orders
    orders = db.query(models.Order).filter(models.Order.customer_id == customer_id).all()
    total_orders_value = sum(order.total_amount for order in orders)
    
    # Get advance balance
    advance_balance = db.query(models.CustomerAdvancePayment).filter(
        models.CustomerAdvancePayment.customer_id == customer_id
    ).with_entities(
        models.CustomerAdvancePayment.remaining_balance
    ).scalar() or 0
    
    outstanding_amount = total_orders_value - total_payments
    
    return {
        "customer_id": customer_id,
        "total_orders_value": total_orders_value,
        "total_payments": total_payments,
        "outstanding_amount": outstanding_amount,
        "advance_balance": advance_balance,
        "payment_allocations_count": len(payment_allocations),
        "orders_count": len(orders)
    } 