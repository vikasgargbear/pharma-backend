"""
Payments Router - All payment-related endpoints
Migrated from main.py for better modularity and maintainability
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ..database import get_db
from .. import models, schemas, crud
from ..core.crud_base import create_crud
from ..core.security import handle_database_error
from ..business_logic import PaymentManager
from ..dependencies import get_current_user

# Create router
router = APIRouter(prefix="/payments", tags=["payments"])

# Create CRUD instances using our generic system
payment_crud = create_crud(models.Payment)
payment_allocation_crud = create_crud(models.PaymentAllocation)
advance_payment_crud = create_crud(models.CustomerAdvancePayment)
upi_payment_crud = create_crud(models.UPIPayment)

# ================= BASIC PAYMENTS =================

@router.post("/", response_model=schemas.Payment)
@handle_database_error
def create_payment(
    payment: schemas.PaymentCreate, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a payment with automatic processing"""
    try:
        # Create payment
        created_payment = payment_crud.create(db, payment)
        
        # FIXED: Automatically process payment with real-time updates
        PaymentManager.process_payment_received(db, created_payment.payment_id)
        
        return created_payment
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[schemas.Payment])
@handle_database_error
def read_payments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all payments with pagination"""
    return payment_crud.get_multi(db, skip=skip, limit=limit)

@router.get("/{payment_id}", response_model=schemas.Payment)
@handle_database_error
def read_payment(payment_id: int, db: Session = Depends(get_db)):
    """Get a specific payment by ID"""
    payment = payment_crud.get(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@router.put("/{payment_id}", response_model=schemas.Payment)
@handle_database_error
def update_payment(
    payment_id: int, 
    payment: schemas.PaymentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a payment with automatic processing"""
    db_payment = payment_crud.get(db, payment_id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    try:
        # Update payment
        updated_payment = payment_crud.update(db, db_obj=db_payment, obj_in=payment)
        
        # FIXED: Automatically process payment with real-time updates
        PaymentManager.process_payment_received(db, payment_id)
        
        return updated_payment
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{payment_id}")
@handle_database_error
def delete_payment(payment_id: int, db: Session = Depends(get_db)):
    """Delete a payment"""
    db_payment = payment_crud.get(db, payment_id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment_crud.remove(db, id=payment_id)

# ================= PAYMENT ALLOCATIONS =================

@router.post("/with-allocation/", response_model=schemas.Payment)
@handle_database_error
def create_payment_with_allocation(
    payment_data: schemas.PaymentWithAllocationCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """FIXED: Create payment with automatic allocation and real-time updates"""
    try:
        # Use business logic manager for complete automation
        payment = PaymentManager.create_payment_with_allocation(
            db=db,
            customer_id=payment_data.customer_id,
            amount=payment_data.amount,
            payment_mode=payment_data.payment_mode,
            order_ids=payment_data.order_ids,
            payment_type=payment_data.payment_type,
            processed_by=current_user.user_id,
            reference_number=payment_data.reference_number if hasattr(payment_data, 'reference_number') else None,
            bank_name=payment_data.bank_name if hasattr(payment_data, 'bank_name') else None,
            transaction_id=payment_data.transaction_id if hasattr(payment_data, 'transaction_id') else None
        )
        
        # FIXED: Automatically process payment with real-time updates
        PaymentManager.process_payment_received(db, payment.payment_id)
        
        return payment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/allocations/", response_model=List[schemas.PaymentAllocation])
@handle_database_error
def read_payment_allocations(
    payment_id: int = None,
    order_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get payment allocations with optional filtering"""
    query = db.query(models.PaymentAllocation)
    
    if payment_id:
        query = query.filter(models.PaymentAllocation.payment_id == payment_id)
    if order_id:
        query = query.filter(models.PaymentAllocation.order_id == order_id)
    
    return query.offset(skip).limit(limit).all()

@router.post("/apply-advance/")
@handle_database_error
def apply_advance_to_order(
    advance_data: schemas.AdvancePaymentApplication,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """FIXED: Apply advance payment with real-time updates"""
    try:
        # Use business logic manager for complete automation
        result = PaymentManager.apply_advance_payment(
            db=db,
            customer_id=advance_data.customer_id,
            order_id=advance_data.order_id,
            amount=advance_data.amount
        )
        
        return {
            "message": "Advance payment applied successfully with real-time updates",
            "amount_applied": result,
            "status": "success"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ================= ADVANCE PAYMENTS =================

@router.post("/advance/", response_model=schemas.CustomerAdvancePayment)
@handle_database_error
def create_advance_payment(advance: schemas.CustomerAdvancePaymentCreate, db: Session = Depends(get_db)):
    """Create a customer advance payment"""
    return advance_payment_crud.create(db, advance)

@router.put("/advance/{advance_payment_id}", response_model=schemas.CustomerAdvancePayment)
@handle_database_error
def update_advance_payment(advance_payment_id: int, updates: schemas.CustomerAdvancePaymentCreate, db: Session = Depends(get_db)):
    """Update an advance payment"""
    db_advance = advance_payment_crud.get(db, advance_payment_id)
    if not db_advance:
        raise HTTPException(status_code=404, detail="Advance payment not found")
    return advance_payment_crud.update(db, db_obj=db_advance, obj_in=updates)

# ================= UPI PAYMENTS =================

@router.post("/upi/generate-qr/", response_model=schemas.UPIPaymentResponse)
@handle_database_error
async def generate_upi_qr_code(
    payment: schemas.UPIPaymentCreate,
    db: Session = Depends(get_db)
):
    """Generate UPI QR code for payment"""
    return await crud.generate_upi_qr_code(db=db, payment=payment)

@router.get("/upi/{merchant_tx_id}", response_model=schemas.UPIPaymentResponse)
@handle_database_error
async def get_upi_payment(merchant_tx_id: str, db: Session = Depends(get_db)):
    """Get UPI payment details by merchant transaction ID"""
    upi_payment = db.query(models.UPIPayment).filter(
        models.UPIPayment.merchant_transaction_id == merchant_tx_id
    ).first()
    
    if not upi_payment:
        raise HTTPException(status_code=404, detail="UPI payment not found")
    
    return upi_payment

@router.put("/upi/update-status/{merchant_tx_id}")
@handle_database_error
async def update_upi_payment_status(
    merchant_tx_id: str,
    status_update: schemas.UPIPaymentStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update UPI payment status (webhook endpoint)"""
    upi_payment = db.query(models.UPIPayment).filter(
        models.UPIPayment.merchant_transaction_id == merchant_tx_id
    ).first()
    
    if not upi_payment:
        raise HTTPException(status_code=404, detail="UPI payment not found")
    
    upi_payment.status = status_update.status
    upi_payment.gateway_transaction_id = status_update.gateway_transaction_id
    upi_payment.gateway_response = status_update.gateway_response
    
    db.commit()
    db.refresh(upi_payment)
    
    return {
        "message": "UPI payment status updated successfully",
        "merchant_tx_id": merchant_tx_id,
        "status": upi_payment.status
    }

@router.get("/upi/customer/{customer_id}/payments")
@handle_database_error
async def get_customer_upi_payments(
    customer_id: int,
    status: str = None,
    db: Session = Depends(get_db)
):
    """Get all UPI payments for a customer"""
    query = db.query(models.UPIPayment).filter(
        models.UPIPayment.customer_id == customer_id
    )
    
    if status:
        query = query.filter(models.UPIPayment.status == status)
    
    return query.all()

@router.put("/upi/reconcile/{upi_payment_id}")
@handle_database_error
async def reconcile_upi_payment(
    upi_payment_id: int,
    bank_matched: bool = True,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """Reconcile UPI payment with bank statement"""
    upi_payment = upi_payment_crud.get(db, upi_payment_id)
    if not upi_payment:
        raise HTTPException(status_code=404, detail="UPI payment not found")
    
    upi_payment.is_reconciled = bank_matched
    upi_payment.reconciled_by = user_id
    upi_payment.reconciled_at = db.query(models.func.now()).scalar()
    
    db.commit()
    db.refresh(upi_payment)
    
    return {
        "message": "UPI payment reconciliation updated",
        "upi_payment_id": upi_payment_id,
        "is_reconciled": bank_matched
    }

@router.get("/upi/qr-image/{merchant_tx_id}")
@handle_database_error
async def get_qr_code_image(merchant_tx_id: str, db: Session = Depends(get_db)):
    """Get QR code image for UPI payment"""
    upi_payment = db.query(models.UPIPayment).filter(
        models.UPIPayment.merchant_transaction_id == merchant_tx_id
    ).first()
    
    if not upi_payment:
        raise HTTPException(status_code=404, detail="UPI payment not found")
    
    if not upi_payment.qr_code_url:
        raise HTTPException(status_code=404, detail="QR code not generated")
    
    return {
        "merchant_tx_id": merchant_tx_id,
        "qr_code_url": upi_payment.qr_code_url,
        "upi_id": upi_payment.upi_id,
        "amount": upi_payment.amount
    }

# ================= VENDOR PAYMENTS =================

@router.post("/vendor/", response_model=schemas.VendorPayment)
@handle_database_error
def create_vendor_payment(payment: schemas.VendorPaymentCreate, db: Session = Depends(get_db)):
    """Create a vendor payment"""
    vendor_payment_crud = create_crud(models.VendorPayment)
    return vendor_payment_crud.create(db, payment)

@router.get("/vendor/", response_model=List[schemas.VendorPayment])
@handle_database_error
def read_vendor_payments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all vendor payments with pagination"""
    vendor_payment_crud = create_crud(models.VendorPayment)
    return vendor_payment_crud.get_multi(db, skip=skip, limit=limit)

@router.get("/vendor/{vendor_payment_id}", response_model=schemas.VendorPayment)
@handle_database_error
def read_vendor_payment(vendor_payment_id: int, db: Session = Depends(get_db)):
    """Get a specific vendor payment"""
    vendor_payment_crud = create_crud(models.VendorPayment)
    payment = vendor_payment_crud.get(db, vendor_payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Vendor payment not found")
    return payment

@router.put("/vendor/{vendor_payment_id}", response_model=schemas.VendorPayment)
@handle_database_error
def update_vendor_payment(vendor_payment_id: int, payment: schemas.VendorPaymentCreate, db: Session = Depends(get_db)):
    """Update a vendor payment"""
    vendor_payment_crud = create_crud(models.VendorPayment)
    db_payment = vendor_payment_crud.get(db, vendor_payment_id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Vendor payment not found")
    return vendor_payment_crud.update(db, db_obj=db_payment, obj_in=payment)

@router.delete("/vendor/{vendor_payment_id}")
@handle_database_error
def delete_vendor_payment(vendor_payment_id: int, db: Session = Depends(get_db)):
    """Delete a vendor payment"""
    vendor_payment_crud = create_crud(models.VendorPayment)
    db_payment = vendor_payment_crud.get(db, vendor_payment_id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Vendor payment not found")
    return vendor_payment_crud.remove(db, id=vendor_payment_id) 