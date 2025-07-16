"""
Batches Router - All batch-related endpoints
Migrated from main.py for better modularity and maintainability
Supabase (PostgreSQL) compatible
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime, timedelta
from sqlalchemy import and_, or_

from ..database import get_db
from .. import models, schemas, crud
from ..core.crud_base import create_crud
from ..core.security import handle_database_error

# Create router
router = APIRouter(prefix="/batches", tags=["batches"])

# Create CRUD instances using our generic system
batch_crud = create_crud(models.Batch)

# ================= BATCHES =================

@router.post("/", response_model=schemas.Batch)
@handle_database_error
def create_batch(batch: schemas.BatchCreate, db: Session = Depends(get_db)):
    """Create a new batch"""
    return batch_crud.create(db, batch)

@router.get("/", response_model=List[schemas.Batch])
@handle_database_error
def read_batches(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all batches with pagination"""
    return batch_crud.get_multi(db, skip=skip, limit=limit)

@router.get("/{batch_id}", response_model=schemas.Batch)
@handle_database_error
def read_batch(batch_id: int, db: Session = Depends(get_db)):
    """Get a specific batch by ID"""
    batch = batch_crud.get(db, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch

@router.put("/{batch_id}", response_model=schemas.Batch)
@handle_database_error
def update_batch(batch_id: int, batch: schemas.BatchCreate, db: Session = Depends(get_db)):
    """Update an existing batch"""
    db_batch = batch_crud.get(db, batch_id)
    if not db_batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch_crud.update(db, db_obj=db_batch, obj_in=batch)

@router.delete("/{batch_id}")
@handle_database_error
def delete_batch(batch_id: int, db: Session = Depends(get_db)):
    """Delete a batch"""
    db_batch = batch_crud.get(db, batch_id)
    if not db_batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch_crud.remove(db, id=batch_id)

# ================= BATCH FILTERING =================

@router.get("/product/{product_id}/batches", response_model=List[schemas.Batch])
@handle_database_error
def get_product_batches(product_id: int, db: Session = Depends(get_db)):
    """Get all batches for a specific product"""
    return db.query(models.Batch).filter(
        models.Batch.product_id == product_id
    ).all()

@router.get("/supplier/{supplier_id}/batches", response_model=List[schemas.Batch])
@handle_database_error
def get_supplier_batches(supplier_id: int, db: Session = Depends(get_db)):
    """Get all batches from a specific supplier"""
    return db.query(models.Batch).filter(
        models.Batch.supplier_id == supplier_id
    ).all()

@router.get("/search/batch-number/{batch_number}", response_model=List[schemas.Batch])
@handle_database_error
def search_batches_by_number(batch_number: str, db: Session = Depends(get_db)):
    """Search batches by batch number (partial match)"""
    return db.query(models.Batch).filter(
        models.Batch.batch_number.ilike(f"%{batch_number}%")
    ).all()

# ================= EXPIRY MANAGEMENT =================

@router.get("/expiry/expired", response_model=List[schemas.Batch])
@handle_database_error
def get_expired_batches(db: Session = Depends(get_db)):
    """Get all expired batches"""
    today = date.today()
    return db.query(models.Batch).filter(
        models.Batch.expiry_date < today
    ).all()

@router.get("/expiry/expiring-soon", response_model=List[schemas.Batch])
@handle_database_error
def get_expiring_batches(days_ahead: int = 30, db: Session = Depends(get_db)):
    """Get batches expiring within specified days"""
    today = date.today()
    future_date = today + timedelta(days=days_ahead)
    
    return db.query(models.Batch).filter(
        and_(
            models.Batch.expiry_date >= today,
            models.Batch.expiry_date <= future_date
        )
    ).all()

@router.get("/expiry/by-month/{year}/{month}", response_model=List[schemas.Batch])
@handle_database_error
def get_batches_expiring_by_month(year: int, month: int, db: Session = Depends(get_db)):
    """Get batches expiring in a specific month"""
    try:
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        return db.query(models.Batch).filter(
            and_(
                models.Batch.expiry_date >= start_date,
                models.Batch.expiry_date <= end_date
            )
        ).all()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid year or month")

# ================= BATCH ANALYTICS =================

@router.get("/analytics/summary")
@handle_database_error
def get_batch_analytics(db: Session = Depends(get_db)):
    """Get batch analytics summary"""
    # Total batches
    total_batches = db.query(models.Batch).count()
    
    # Expired batches
    today = date.today()
    expired_batches = db.query(models.Batch).filter(
        models.Batch.expiry_date < today
    ).count()
    
    # Expiring soon (30 days)
    thirty_days_future = today + timedelta(days=30)
    expiring_soon = db.query(models.Batch).filter(
        and_(
            models.Batch.expiry_date >= today,
            models.Batch.expiry_date <= thirty_days_future
        )
    ).count()
    
    # Active batches (not expired)
    active_batches = db.query(models.Batch).filter(
        models.Batch.expiry_date >= today
    ).count()
    
    # Calculate total quantities
    total_quantity = db.query(models.Batch).with_entities(
        models.Batch.quantity_received
    ).all()
    total_received = sum(batch.quantity_received for batch in total_quantity if batch.quantity_received)
    
    return {
        "total_batches": total_batches,
        "active_batches": active_batches,
        "expired_batches": expired_batches,
        "expiring_soon_30d": expiring_soon,
        "total_quantity_received": total_received,
        "expired_percentage": (expired_batches / total_batches * 100) if total_batches > 0 else 0
    }

@router.get("/analytics/expiry-timeline")
@handle_database_error
def get_expiry_timeline(db: Session = Depends(get_db)):
    """Get batch expiry timeline for the next 12 months"""
    today = date.today()
    timeline = {}
    
    for month_offset in range(12):
        # Calculate month start and end
        if today.month + month_offset <= 12:
            month = today.month + month_offset
            year = today.year
        else:
            month = (today.month + month_offset) % 12
            year = today.year + 1
        
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)
        
        # Count batches expiring in this month
        expiring_count = db.query(models.Batch).filter(
            and_(
                models.Batch.expiry_date >= month_start,
                models.Batch.expiry_date <= month_end
            )
        ).count()
        
        timeline[f"{year}-{month:02d}"] = expiring_count
    
    return {
        "timeline": timeline,
        "period": "next_12_months"
    }

# ================= BATCH OPERATIONS =================

@router.post("/{batch_id}/mark-expired")
@handle_database_error
def mark_batch_expired(batch_id: int, db: Session = Depends(get_db)):
    """Mark a batch as expired (for manual expiry management)"""
    batch = batch_crud.get(db, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Update expiry date to today if not already expired
    if batch.expiry_date >= date.today():
        batch.expiry_date = date.today()
        db.commit()
        db.refresh(batch)
    
    return {
        "message": "Batch marked as expired",
        "batch_id": batch_id,
        "expiry_date": batch.expiry_date
    }

@router.get("/{batch_id}/current-stock")
@handle_database_error
def get_batch_current_stock(batch_id: int, db: Session = Depends(get_db)):
    """Get current stock level for a specific batch"""
    batch = batch_crud.get(db, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Calculate current stock from inventory transactions
    transactions = db.query(models.InventoryTransaction).filter(
        models.InventoryTransaction.batch_id == batch_id
    ).all()
    
    current_stock = batch.quantity_received
    for transaction in transactions:
        if transaction.transaction_type in ["sale", "return_to_supplier", "damage", "expired"]:
            current_stock -= transaction.quantity
        elif transaction.transaction_type in ["purchase", "return_from_customer"]:
            current_stock += transaction.quantity
    
    return {
        "batch_id": batch_id,
        "batch_number": batch.batch_number,
        "initial_quantity": batch.quantity_received,
        "current_stock": current_stock,
        "transactions_count": len(transactions),
        "expiry_date": batch.expiry_date,
        "status": "expired" if batch.expiry_date < date.today() else "active"
    }

@router.get("/reports/wastage-analysis")
@handle_database_error
def get_wastage_analysis(db: Session = Depends(get_db)):
    """Get analysis of expired/wasted batches"""
    today = date.today()
    
    # Get expired batches
    expired_batches = db.query(models.Batch).filter(
        models.Batch.expiry_date < today
    ).all()
    
    # Calculate wastage
    total_wastage_quantity = 0
    total_wastage_value = 0
    
    for batch in expired_batches:
        # Get remaining stock for this batch
        transactions = db.query(models.InventoryTransaction).filter(
            models.InventoryTransaction.batch_id == batch.id
        ).all()
        
        remaining_stock = batch.quantity_received
        for transaction in transactions:
            if transaction.transaction_type in ["sale", "return_to_supplier", "damage", "expired"]:
                remaining_stock -= transaction.quantity
            elif transaction.transaction_type in ["purchase", "return_from_customer"]:
                remaining_stock += transaction.quantity
        
        if remaining_stock > 0:
            total_wastage_quantity += remaining_stock
            total_wastage_value += remaining_stock * (batch.unit_cost if hasattr(batch, 'unit_cost') else 0)
    
    return {
        "expired_batches_count": len(expired_batches),
        "total_wastage_quantity": total_wastage_quantity,
        "total_wastage_value": total_wastage_value,
        "average_wastage_per_batch": total_wastage_quantity / len(expired_batches) if expired_batches else 0
    } 