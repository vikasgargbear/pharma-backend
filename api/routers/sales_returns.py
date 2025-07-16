"""
Sales Returns Router - All sales return endpoints
Migrated from main.py for better modularity and maintainability
Supabase (PostgreSQL) compatible
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from ..database import get_db
from .. import models, schemas, crud
from ..core.crud_base import create_crud
from ..core.security import handle_database_error
from ..business_logic import InventoryManager
from ..dependencies import get_current_user

# Create router
router = APIRouter(prefix="/sales-returns", tags=["sales_returns"])

# Create CRUD instances using our generic system
sales_return_crud = create_crud(models.SalesReturn)

# ================= SALES RETURNS =================

@router.post("/", response_model=schemas.SalesReturn)
@handle_database_error
def create_sales_return(
    return_: schemas.SalesReturnCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """FIXED: Create a new sales return with automatic inventory processing"""
    try:
        # Create the sales return
        sales_return = sales_return_crud.create(db, return_)
        
        # FIXED: Automatically process inventory updates for the return
        if hasattr(return_, 'return_items') and return_.return_items:
            return_items = [
                {
                    'batch_id': item.batch_id,
                    'return_quantity': item.return_quantity,
                    'return_item_id': item.return_item_id if hasattr(item, 'return_item_id') else None
                }
                for item in return_.return_items
            ]
            
            # Process inventory updates using business logic manager
            InventoryManager.process_sales_return(db, return_items, current_user.user_id)
        
        return sales_return
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[schemas.SalesReturn])
@handle_database_error
def read_sales_returns(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all sales returns with pagination"""
    return sales_return_crud.get_multi(db, skip=skip, limit=limit)

@router.get("/{return_id}", response_model=schemas.SalesReturn)
@handle_database_error
def read_sales_return(return_id: int, db: Session = Depends(get_db)):
    """Get a specific sales return by ID"""
    sales_return = sales_return_crud.get(db, return_id)
    if not sales_return:
        raise HTTPException(status_code=404, detail="Sales return not found")
    return sales_return

@router.put("/{return_id}", response_model=schemas.SalesReturn)
@handle_database_error
def update_sales_return(return_id: int, return_: schemas.SalesReturnCreate, db: Session = Depends(get_db)):
    """Update an existing sales return"""
    db_return = sales_return_crud.get(db, return_id)
    if not db_return:
        raise HTTPException(status_code=404, detail="Sales return not found")
    return sales_return_crud.update(db, db_obj=db_return, obj_in=return_)

@router.delete("/{return_id}")
@handle_database_error
def delete_sales_return(return_id: int, db: Session = Depends(get_db)):
    """Delete a sales return"""
    db_return = sales_return_crud.get(db, return_id)
    if not db_return:
        raise HTTPException(status_code=404, detail="Sales return not found")
    return sales_return_crud.remove(db, id=return_id)

# ================= SALES RETURN ANALYTICS =================

@router.get("/analytics/summary")
@handle_database_error
def get_sales_return_analytics(db: Session = Depends(get_db)):
    """Get sales return analytics summary"""
    # Total returns
    total_returns = db.query(models.SalesReturn).count()
    
    # Total return value
    total_value = db.query(models.SalesReturn).with_entities(
        models.SalesReturn.total_amount
    ).all()
    total_return_value = sum(return_.total_amount for return_ in total_value if return_.total_amount)
    
    # Recent returns (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_returns = db.query(models.SalesReturn).filter(
        models.SalesReturn.created_at >= thirty_days_ago
    ).count()
    
    # Calculate return rate compared to total sales
    total_orders = db.query(models.Order).count()
    total_order_value = db.query(models.Order).with_entities(
        models.Order.total_amount
    ).all()
    total_sales_value = sum(order.total_amount for order in total_order_value if order.total_amount)
    
    return_rate = (total_return_value / total_sales_value * 100) if total_sales_value > 0 else 0
    
    return {
        "total_returns": total_returns,
        "total_return_value": total_return_value,
        "recent_returns_30d": recent_returns,
        "return_rate_percentage": return_rate,
        "average_return_value": total_return_value / total_returns if total_returns > 0 else 0
    }

@router.get("/customer/{customer_id}/returns", response_model=List[schemas.SalesReturn])
@handle_database_error
def get_customer_sales_returns(customer_id: int, db: Session = Depends(get_db)):
    """Get all sales returns for a specific customer"""
    return db.query(models.SalesReturn).filter(
        models.SalesReturn.customer_id == customer_id
    ).all()

@router.get("/order/{order_id}/returns", response_model=List[schemas.SalesReturn])
@handle_database_error
def get_order_sales_returns(order_id: int, db: Session = Depends(get_db)):
    """Get all sales returns for a specific order"""
    return db.query(models.SalesReturn).filter(
        models.SalesReturn.order_id == order_id
    ).all()

@router.post("/{return_id}/process")
@handle_database_error
def process_sales_return(
    return_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """FIXED: Process a sales return with complete real-time updates"""
    sales_return = sales_return_crud.get(db, return_id)
    if not sales_return:
        raise HTTPException(status_code=404, detail="Sales return not found")
    
    if sales_return.status == "processed":
        raise HTTPException(status_code=400, detail="Sales return already processed")
    
    try:
        # Update return status
        sales_return.status = "processed"
        sales_return.processed_at = db.query(models.func.now()).scalar()
        
        # FIXED: Get return items and process inventory using business logic
        return_items = db.query(models.SalesReturnItem).filter(
            models.SalesReturnItem.return_id == return_id
        ).all()
        
        if return_items:
            return_items_data = [
                {
                    'batch_id': item.batch_id,
                    'return_quantity': item.return_quantity,
                    'return_item_id': item.return_item_id
                }
                for item in return_items
            ]
            
            # Process inventory updates using business logic manager
            InventoryManager.process_sales_return(db, return_items_data, current_user.user_id)
        
        db.commit()
        
        return {
            "message": "Sales return processed successfully with real-time inventory updates",
            "return_id": return_id,
            "status": "processed",
            "inventory_updated": True
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) 