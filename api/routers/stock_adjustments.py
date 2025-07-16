"""
Stock Adjustments Router - All stock adjustment endpoints
NEW: Complete stock adjustment system with real-time updates
Supabase (PostgreSQL) compatible
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta

from ..database import get_db
from .. import models, schemas
from ..core.crud_base import create_crud
from ..core.security import handle_database_error
from ..business_logic import StockAdjustmentManager
from ..dependencies import get_current_user

# Create router
router = APIRouter(prefix="/stock-adjustments", tags=["stock_adjustments"])

# Create CRUD instances using our generic system
stock_adjustment_crud = create_crud(models.StockAdjustment)

# ================= STOCK ADJUSTMENTS =================

@router.post("/")
@handle_database_error
def create_stock_adjustment(
    adjustment_data: schemas.StockAdjustmentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create stock adjustment with complete real-time updates"""
    try:
        # Use business logic manager for complete automation
        result = StockAdjustmentManager.process_stock_adjustment(
            db=db,
            batch_id=adjustment_data.batch_id,
            adjustment_quantity=adjustment_data.adjustment_quantity,
            adjustment_type=adjustment_data.adjustment_type,
            reason=adjustment_data.reason,
            user_id=current_user.user_id
        )
        
        return {
            "message": "Stock adjustment processed successfully with real-time updates",
            "stock_adjustment": result["stock_adjustment"],
            "inventory_transaction": result["inventory_transaction"],
            "status": "success"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[schemas.StockAdjustment])
@handle_database_error
def read_stock_adjustments(
    skip: int = 0,
    limit: int = 100,
    batch_id: Optional[int] = None,
    adjustment_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get all stock adjustments with optional filtering"""
    query = db.query(models.StockAdjustment)
    
    # Apply filters
    if batch_id:
        query = query.filter(models.StockAdjustment.batch_id == batch_id)
    if adjustment_type:
        query = query.filter(models.StockAdjustment.adjustment_type == adjustment_type)
    if start_date:
        query = query.filter(models.StockAdjustment.created_at >= start_date)
    if end_date:
        query = query.filter(models.StockAdjustment.created_at <= end_date)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{adjustment_id}", response_model=schemas.StockAdjustment)
@handle_database_error
def read_stock_adjustment(adjustment_id: int, db: Session = Depends(get_db)):
    """Get a specific stock adjustment by ID"""
    adjustment = stock_adjustment_crud.get(db, adjustment_id)
    if not adjustment:
        raise HTTPException(status_code=404, detail="Stock adjustment not found")
    return adjustment

@router.get("/batch/{batch_id}/adjustments", response_model=List[schemas.StockAdjustment])
@handle_database_error
def get_batch_adjustments(
    batch_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all stock adjustments for a specific batch"""
    return db.query(models.StockAdjustment).filter(
        models.StockAdjustment.batch_id == batch_id
    ).limit(limit).all()

# ================= STOCK ADJUSTMENT ANALYTICS =================

@router.get("/analytics/summary")
@handle_database_error
def get_stock_adjustment_analytics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get stock adjustment analytics summary"""
    query = db.query(models.StockAdjustment)
    
    # Apply date filters
    if start_date:
        query = query.filter(models.StockAdjustment.created_at >= start_date)
    if end_date:
        query = query.filter(models.StockAdjustment.created_at <= end_date)
    
    adjustments = query.all()
    
    # Calculate statistics
    total_adjustments = len(adjustments)
    
    # Group by adjustment type
    adjustment_types = {}
    total_positive = 0
    total_negative = 0
    
    for adj in adjustments:
        adj_type = adj.adjustment_type
        if adj_type not in adjustment_types:
            adjustment_types[adj_type] = {"count": 0, "total_quantity": 0}
        
        adjustment_types[adj_type]["count"] += 1
        adjustment_types[adj_type]["total_quantity"] += adj.adjustment_quantity
        
        if adj.adjustment_quantity > 0:
            total_positive += adj.adjustment_quantity
        else:
            total_negative += abs(adj.adjustment_quantity)
    
    # Calculate net adjustment
    net_adjustment = total_positive - total_negative
    
    return {
        "period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        },
        "total_adjustments": total_adjustments,
        "adjustment_types": adjustment_types,
        "quantity_summary": {
            "total_positive": total_positive,
            "total_negative": total_negative,
            "net_adjustment": net_adjustment
        },
        "most_common_reason": max(
            [adj.reason for adj in adjustments],
            key=[adj.reason for adj in adjustments].count
        ) if adjustments else None
    }

@router.get("/analytics/by-reason")
@handle_database_error
def get_adjustments_by_reason(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get stock adjustments grouped by reason"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    adjustments = db.query(models.StockAdjustment).filter(
        models.StockAdjustment.created_at >= start_date
    ).all()
    
    # Group by reason
    reason_stats = {}
    for adj in adjustments:
        reason = adj.reason
        if reason not in reason_stats:
            reason_stats[reason] = {
                "count": 0,
                "total_quantity": 0,
                "positive_adjustments": 0,
                "negative_adjustments": 0
            }
        
        reason_stats[reason]["count"] += 1
        reason_stats[reason]["total_quantity"] += adj.adjustment_quantity
        
        if adj.adjustment_quantity > 0:
            reason_stats[reason]["positive_adjustments"] += adj.adjustment_quantity
        else:
            reason_stats[reason]["negative_adjustments"] += abs(adj.adjustment_quantity)
    
    return {
        "period_days": days,
        "total_adjustments": len(adjustments),
        "reason_breakdown": reason_stats
    }

# ================= BATCH ADJUSTMENT OPERATIONS =================

@router.post("/batch/{batch_id}/adjust")
@handle_database_error
def adjust_batch_stock(
    batch_id: int,
    adjustment_quantity: int,
    adjustment_type: str,
    reason: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Quick stock adjustment for a specific batch"""
    try:
        # Verify batch exists
        batch = db.query(models.Batch).filter(models.Batch.batch_id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Use business logic manager
        result = StockAdjustmentManager.process_stock_adjustment(
            db=db,
            batch_id=batch_id,
            adjustment_quantity=adjustment_quantity,
            adjustment_type=adjustment_type,
            reason=reason,
            user_id=current_user.user_id
        )
        
        return {
            "message": f"Stock adjusted successfully for batch {batch.batch_number}",
            "batch_id": batch_id,
            "adjustment_quantity": adjustment_quantity,
            "stock_adjustment": result["stock_adjustment"],
            "status": "success"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 