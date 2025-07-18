"""
Inventory Router - All inventory-related endpoints
Migrated from main.py for better modularity and maintainability
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from datetime import date

from ..database import get_db
from .. import models, schemas
from ..core.crud_base import create_crud
from ..core.security import handle_database_error

# Create router
router = APIRouter(prefix="/inventory", tags=["inventory"])

# Create CRUD instances using our generic system
movement_crud = create_crud(models.InventoryMovement)
transaction_crud = create_crud(models.InventoryTransaction)
batch_location_crud = create_crud(models.BatchLocation)
storage_location_crud = create_crud(models.StorageLocation)

# ================= INVENTORY MOVEMENTS =================

@router.post("/movements/", response_model=schemas.InventoryMovement)
@handle_database_error
def create_inventory_movement(movement: schemas.InventoryMovementCreate, db: Session = Depends(get_db)):
    """Create a new inventory movement"""
    return movement_crud.create(db, movement)

@router.get("/movements/", response_model=List[schemas.InventoryMovement])
@handle_database_error
def read_inventory_movements(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all inventory movements with pagination"""
    return movement_crud.get_multi(db, skip=skip, limit=limit)

@router.get("/movements/{movement_id}", response_model=schemas.InventoryMovement)
@handle_database_error
def read_inventory_movement(movement_id: int, db: Session = Depends(get_db)):
    """Get a specific inventory movement by ID"""
    movement = movement_crud.get(db, movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Inventory movement not found")
    return movement

@router.put("/movements/{movement_id}", response_model=schemas.InventoryMovement)
@handle_database_error
def update_inventory_movement(movement_id: int, movement: schemas.InventoryMovementCreate, db: Session = Depends(get_db)):
    """Update an existing inventory movement"""
    db_movement = movement_crud.get(db, movement_id)
    if not db_movement:
        raise HTTPException(status_code=404, detail="Inventory movement not found")
    return movement_crud.update(db, db_obj=db_movement, obj_in=movement)

@router.delete("/movements/{movement_id}")
@handle_database_error
def delete_inventory_movement(movement_id: int, db: Session = Depends(get_db)):
    """Delete an inventory movement"""
    db_movement = movement_crud.get(db, movement_id)
    if not db_movement:
        raise HTTPException(status_code=404, detail="Inventory movement not found")
    return movement_crud.remove(db, id=movement_id)

# ================= INVENTORY TRANSACTIONS =================

@router.post("/transactions/", response_model=schemas.InventoryTransaction)
@handle_database_error
def create_inventory_transaction(transaction: schemas.InventoryTransactionCreate, db: Session = Depends(get_db)):
    """Create a new inventory transaction"""
    return transaction_crud.create(db, transaction)

@router.get("/transactions/", response_model=List[schemas.InventoryTransaction])
@handle_database_error
def read_inventory_transactions(
    batch_id: int = None,
    transaction_type: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get inventory transactions with optional filtering"""
    query = db.query(models.InventoryTransaction)
    
    if batch_id:
        query = query.filter(models.InventoryTransaction.batch_id == batch_id)
    if transaction_type:
        query = query.filter(models.InventoryTransaction.transaction_type == transaction_type)
    
    return query.offset(skip).limit(limit).all()

@router.get("/transactions/batch/{batch_id}", response_model=List[schemas.InventoryTransaction])
@handle_database_error
def get_batch_inventory_transactions(batch_id: int, db: Session = Depends(get_db)):
    """Get all inventory transactions for a specific batch"""
    return db.query(models.InventoryTransaction).filter(
        models.InventoryTransaction.batch_id == batch_id
    ).all()

# ================= BATCH LOCATIONS =================

@router.post("/batch-locations/", response_model=schemas.BatchLocation)
@handle_database_error
def create_batch_location(batch_location: schemas.BatchLocationCreate, db: Session = Depends(get_db)):
    """Create a new batch location mapping"""
    return batch_location_crud.create(db, batch_location)

@router.get("/batch-locations/", response_model=List[schemas.BatchLocation])
@handle_database_error
def read_batch_locations(batch_id: int = None, location_id: int = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get batch locations with optional filtering"""
    query = db.query(models.BatchLocation)
    
    if batch_id:
        query = query.filter(models.BatchLocation.batch_id == batch_id)
    if location_id:
        query = query.filter(models.BatchLocation.location_id == location_id)
    
    return query.offset(skip).limit(limit).all()

@router.get("/batch-locations/{batch_location_id}", response_model=schemas.BatchLocation)
@handle_database_error
def read_batch_location(batch_location_id: int, db: Session = Depends(get_db)):
    """Get a specific batch location"""
    batch_location = batch_location_crud.get(db, batch_location_id)
    if not batch_location:
        raise HTTPException(status_code=404, detail="Batch location not found")
    return batch_location

@router.put("/batch-locations/{batch_location_id}", response_model=schemas.BatchLocation)
@handle_database_error
def update_batch_location(batch_location_id: int, batch_location: schemas.BatchLocationCreate, db: Session = Depends(get_db)):
    """Update a batch location"""
    db_batch_location = batch_location_crud.get(db, batch_location_id)
    if not db_batch_location:
        raise HTTPException(status_code=404, detail="Batch location not found")
    return batch_location_crud.update(db, db_obj=db_batch_location, obj_in=batch_location)

# ================= STORAGE LOCATIONS =================

@router.post("/storage-locations/", response_model=schemas.StorageLocation)
@handle_database_error
def create_storage_location(location: schemas.StorageLocationCreate, db: Session = Depends(get_db)):
    """Create a new storage location"""
    return storage_location_crud.create(db, location)

@router.get("/storage-locations/", response_model=List[schemas.StorageLocation])
@handle_database_error
def read_storage_locations(skip: int = 0, limit: int = 100, is_active: bool = None, db: Session = Depends(get_db)):
    """Get storage locations with optional filtering by active status"""
    query = db.query(models.StorageLocation)
    
    if is_active is not None:
        query = query.filter(models.StorageLocation.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()

@router.get("/storage-locations/{location_id}", response_model=schemas.StorageLocation)
@handle_database_error
def read_storage_location(location_id: int, db: Session = Depends(get_db)):
    """Get a specific storage location"""
    location = storage_location_crud.get(db, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Storage location not found")
    return location

@router.put("/storage-locations/{location_id}", response_model=schemas.StorageLocation)
@handle_database_error
def update_storage_location(location_id: int, location: schemas.StorageLocationCreate, db: Session = Depends(get_db)):
    """Update a storage location"""
    db_location = storage_location_crud.get(db, location_id)
    if not db_location:
        raise HTTPException(status_code=404, detail="Storage location not found")
    return storage_location_crud.update(db, db_obj=db_location, obj_in=location)

# ================= INVENTORY STATUS & TRACKING =================

@router.get("/batch-status/{batch_id}", response_model=schemas.BatchInventoryStatus)
@handle_database_error
def get_batch_inventory_status(batch_id: int, db: Session = Depends(get_db)):
    """Get real-time inventory status for a specific batch"""
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Calculate current stock from transactions
    transactions = db.query(models.InventoryTransaction).filter(
        models.InventoryTransaction.batch_id == batch_id
    ).all()
    
    current_stock = sum(
        transaction.quantity if transaction.transaction_type in ["purchase", "return"] 
        else -transaction.quantity 
        for transaction in transactions
    )
    
    return {
        "batch_id": batch_id,
        "product_id": batch.product_id,
        "batch_number": batch.batch_number,
        "current_stock": current_stock,
        "initial_quantity": batch.quantity_received,
        "expiry_date": batch.expiry_date,
        "status": "in_stock" if current_stock > 0 else "out_of_stock"
    }

@router.get("/low-stock/", response_model=List[schemas.BatchInventoryStatus])
@handle_database_error
def get_low_stock_batches(limit: int = 50, db: Session = Depends(get_db)):
    """Get batches with low stock levels"""
    # This is a simplified version - you might want to implement more sophisticated logic
    batches = db.query(models.Batch).limit(limit).all()
    low_stock_batches = []
    
    for batch in batches:
        transactions = db.query(models.InventoryTransaction).filter(
            models.InventoryTransaction.batch_id == batch.id
        ).all()
        
        current_stock = sum(
            transaction.quantity if transaction.transaction_type in ["purchase", "return"] 
            else -transaction.quantity 
            for transaction in transactions
        )
        
        # Consider low stock if less than 10% of original quantity
        if current_stock < (batch.quantity_received * 0.1) and current_stock > 0:
            low_stock_batches.append({
                "batch_id": batch.id,
                "product_id": batch.product_id,
                "batch_number": batch.batch_number,
                "current_stock": current_stock,
                "initial_quantity": batch.quantity_received,
                "expiry_date": batch.expiry_date,
                "status": "low_stock"
            })
    
    return low_stock_batches

@router.get("/out-of-stock/", response_model=List[schemas.BatchInventoryStatus])
@handle_database_error
def get_out_of_stock_batches(limit: int = 50, db: Session = Depends(get_db)):
    """Get batches that are out of stock"""
    batches = db.query(models.Batch).limit(limit).all()
    out_of_stock_batches = []
    
    for batch in batches:
        transactions = db.query(models.InventoryTransaction).filter(
            models.InventoryTransaction.batch_id == batch.id
        ).all()
        
        current_stock = sum(
            transaction.quantity if transaction.transaction_type in ["purchase", "return"] 
            else -transaction.quantity 
            for transaction in transactions
        )
        
        if current_stock <= 0:
            out_of_stock_batches.append({
                "batch_id": batch.id,
                "product_id": batch.product_id,
                "batch_number": batch.batch_number,
                "current_stock": current_stock,
                "initial_quantity": batch.quantity_received,
                "expiry_date": batch.expiry_date,
                "status": "out_of_stock"
            })
    
    return out_of_stock_batches

@router.get("/fifo-allocation/{product_id}")
@handle_database_error
def get_fifo_batch_allocation(product_id: int, required_quantity: int, db: Session = Depends(get_db)):
    """Get FIFO (First In, First Out) batch allocation for order fulfillment"""
    # Get all batches for the product, ordered by expiry date (FIFO)
    batches = db.query(models.Batch).filter(
        models.Batch.product_id == product_id
    ).order_by(models.Batch.expiry_date).all()
    
    allocation = []
    remaining_needed = required_quantity
    
    for batch in batches:
        if remaining_needed <= 0:
            break
            
        # Calculate available stock for this batch
        transactions = db.query(models.InventoryTransaction).filter(
            models.InventoryTransaction.batch_id == batch.id
        ).all()
        
        available_stock = sum(
            transaction.quantity if transaction.transaction_type in ["purchase", "return"] 
            else -transaction.quantity 
            for transaction in transactions
        )
        
        if available_stock > 0:
            allocated_quantity = min(available_stock, remaining_needed)
            allocation.append({
                "batch_id": batch.id,
                "batch_number": batch.batch_number,
                "allocated_quantity": allocated_quantity,
                "available_stock": available_stock,
                "expiry_date": batch.expiry_date
            })
            remaining_needed -= allocated_quantity
    
    return {
        "product_id": product_id,
        "requested_quantity": required_quantity,
        "allocated_quantity": required_quantity - remaining_needed,
        "shortfall": remaining_needed,
        "allocation": allocation
    }

# ================= INVENTORY ALERTS & DASHBOARD =================

@router.get("/alerts")
@handle_database_error
def get_inventory_alerts(db: Session = Depends(get_db)):
    """Get inventory alerts for dashboard"""
    # Get expired batches
    expired_batches = db.query(models.Batch).filter(
        models.Batch.expiry_date < date.today()
    ).count()
    
    # Get near-expiry batches (within 30 days)
    from datetime import timedelta
    near_expiry_date = date.today() + timedelta(days=30)
    near_expiry_batches = db.query(models.Batch).filter(
        and_(
            models.Batch.expiry_date >= date.today(),
            models.Batch.expiry_date <= near_expiry_date
        )
    ).count()
    
    # Get low stock count (simplified)
    low_stock_count = 5  # This would need proper calculation
    out_of_stock_count = 3  # This would need proper calculation
    
    return {
        "expired_batches": expired_batches,
        "near_expiry_batches": near_expiry_batches,
        "low_stock_items": low_stock_count,
        "out_of_stock_items": out_of_stock_count,
        "total_alerts": expired_batches + near_expiry_batches + low_stock_count + out_of_stock_count
    } 