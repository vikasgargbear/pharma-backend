"""
Challans Router - All challan (delivery receipt) endpoints
Critical for pharmaceutical regulatory compliance and delivery tracking
Supabase (PostgreSQL) compatible
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy import and_, or_, func

from ..database import get_db
from .. import models, schemas, crud
from ..core.crud_base import create_crud
from ..core.security import handle_database_error
from ..business_logic import ChallanManager
from ..dependencies import get_current_user

# Create router
router = APIRouter(prefix="/challans", tags=["challans"])

# Create CRUD instances using our generic system
challan_crud = create_crud(models.Challan)
challan_item_crud = create_crud(models.ChallanItem)
customer_crud = create_crud(models.Customer)

# ================= CHALLANS =================

@router.post("/", response_model=schemas.Challan)
@handle_database_error
def create_challan(challan: schemas.ChallanCreate, db: Session = Depends(get_db)):
    """Create a new challan"""
    return challan_crud.create(db, challan)

@router.get("/", response_model=List[schemas.Challan])
@handle_database_error
def read_challans(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get all challans with optional filtering"""
    query = db.query(models.Challan)
    
    # Apply filters
    if status:
        query = query.filter(models.Challan.status == status)
    if customer_id:
        query = query.filter(models.Challan.customer_id == customer_id)
    if start_date:
        query = query.filter(models.Challan.challan_date >= start_date)
    if end_date:
        query = query.filter(models.Challan.challan_date <= end_date)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{challan_id}", response_model=schemas.Challan)
@handle_database_error
def read_challan(challan_id: int, db: Session = Depends(get_db)):
    """Get a specific challan by ID"""
    challan = challan_crud.get(db, challan_id)
    if not challan:
        raise HTTPException(status_code=404, detail="Challan not found")
    return challan

@router.put("/{challan_id}", response_model=schemas.Challan)
@handle_database_error
def update_challan(
    challan_id: int,
    challan_update: schemas.ChallanUpdate,
    db: Session = Depends(get_db)
):
    """Update a challan"""
    challan = challan_crud.get(db, challan_id)
    if not challan:
        raise HTTPException(status_code=404, detail="Challan not found")
    
    return challan_crud.update(db, db_obj=challan, obj_in=challan_update)

@router.delete("/{challan_id}")
@handle_database_error
def delete_challan(challan_id: int, db: Session = Depends(get_db)):
    """Delete a challan"""
    challan = challan_crud.get(db, challan_id)
    if not challan:
        raise HTTPException(status_code=404, detail="Challan not found")
    
    challan_crud.remove(db, id=challan_id)
    return {"message": "Challan deleted successfully"}

# ================= CHALLAN ITEMS =================

@router.post("/{challan_id}/items/", response_model=schemas.ChallanItem)
@handle_database_error
def create_challan_item(
    challan_id: int,
    item: schemas.ChallanItemCreate,
    db: Session = Depends(get_db)
):
    """Add an item to a challan"""
    # Verify challan exists
    challan = challan_crud.get(db, challan_id)
    if not challan:
        raise HTTPException(status_code=404, detail="Challan not found")
    
    # Set challan_id
    item_dict = item.dict()
    item_dict["challan_id"] = challan_id
    
    return challan_item_crud.create(db, schemas.ChallanItemCreate(**item_dict))

@router.get("/{challan_id}/items/", response_model=List[schemas.ChallanItem])
@handle_database_error
def read_challan_items(challan_id: int, db: Session = Depends(get_db)):
    """Get all items for a specific challan"""
    challan = challan_crud.get(db, challan_id)
    if not challan:
        raise HTTPException(status_code=404, detail="Challan not found")
    
    return db.query(models.ChallanItem).filter(models.ChallanItem.challan_id == challan_id).all()

@router.put("/{challan_id}/items/{item_id}", response_model=schemas.ChallanItem)
@handle_database_error
def update_challan_item(
    challan_id: int,
    item_id: int,
    item_update: schemas.ChallanItemUpdate,
    db: Session = Depends(get_db)
):
    """Update a challan item"""
    item = db.query(models.ChallanItem).filter(
        models.ChallanItem.id == item_id,
        models.ChallanItem.challan_id == challan_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Challan item not found")
    
    return challan_item_crud.update(db, db_obj=item, obj_in=item_update)

@router.delete("/{challan_id}/items/{item_id}")
@handle_database_error
def delete_challan_item(challan_id: int, item_id: int, db: Session = Depends(get_db)):
    """Delete a challan item"""
    item = db.query(models.ChallanItem).filter(
        models.ChallanItem.id == item_id,
        models.ChallanItem.challan_id == challan_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Challan item not found")
    
    challan_item_crud.remove(db, id=item_id)
    return {"message": "Challan item deleted successfully"}

# ================= CHALLAN STATUS MANAGEMENT =================

@router.post("/{challan_id}/dispatch")
@handle_database_error
def dispatch_challan(
    challan_id: int,
    dispatch_details: schemas.ChallanDispatchRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """FIXED: Dispatch challan with complete real-time updates"""
    try:
        # Use business logic manager for complete automation
        challan = ChallanManager.dispatch_challan(
            db=db,
            challan_id=challan_id,
            dispatch_details=dispatch_details.dict(),
            user_id=current_user.user_id
        )
        
        return {
            "message": "Challan dispatched successfully with real-time updates",
            "challan": challan,
            "status": "success"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{challan_id}/deliver")
@handle_database_error
def deliver_challan(
    challan_id: int,
    delivery_info: schemas.ChallanDeliveryInfo,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """FIXED: Deliver challan with complete real-time updates"""
    try:
        # Use business logic for complete delivery processing
        result = ChallanManager.deliver_challan(
            db=db,
            challan_id=challan_id,
            delivery_info=delivery_info.dict(),
            user_id=current_user.user_id
        )
        
        return {
            "message": "Challan delivered successfully with real-time updates",
            "challan": result["challan"],
            "delivery_confirmation": result["delivery_confirmation"],
            "status": "success"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/from-order/{order_id}")
@handle_database_error
def create_challan_from_order(
    order_id: int,
    challan_data: schemas.ChallanFromOrderCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create challan from order with complete automation"""
    try:
        challan = ChallanManager.create_challan_from_order(
            db=db,
            order_id=order_id,
            user_id=current_user.user_id,
            partial_items=challan_data.partial_items if hasattr(challan_data, 'partial_items') else None
        )
        
        return {
            "message": "Challan created successfully",
            "challan": challan,
            "status": "success"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{challan_id}/cancel")
@handle_database_error
def cancel_challan(
    challan_id: int,
    cancellation_reason: str,
    db: Session = Depends(get_db)
):
    """Cancel a challan"""
    challan = challan_crud.get(db, challan_id)
    if not challan:
        raise HTTPException(status_code=404, detail="Challan not found")
    
    if challan.status in ["delivered", "cancelled"]:
        raise HTTPException(status_code=400, detail="Cannot cancel delivered or already cancelled challan")
    
    # Update challan status
    challan.status = "cancelled"
    challan.cancellation_reason = cancellation_reason
    challan.cancelled_date = datetime.utcnow()
    db.commit()
    
    return {"message": "Challan cancelled successfully", "challan": challan}

# ================= CHALLAN ANALYTICS =================

@router.get("/analytics/summary")
@handle_database_error
def get_challan_analytics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get challan analytics summary"""
    query = db.query(models.Challan)
    
    # Apply date filters
    if start_date:
        query = query.filter(models.Challan.challan_date >= start_date)
    if end_date:
        query = query.filter(models.Challan.challan_date <= end_date)
    
    challans = query.all()
    
    # Calculate statistics
    total_challans = len(challans)
    status_counts = {}
    total_value = 0
    
    for challan in challans:
        # Count by status
        status = challan.status
        if status not in status_counts:
            status_counts[status] = 0
        status_counts[status] += 1
        
        # Calculate total value
        if challan.total_amount:
            total_value += challan.total_amount
    
    # Calculate delivery performance
    delivered_challans = status_counts.get("delivered", 0)
    delivery_rate = (delivered_challans / total_challans * 100) if total_challans > 0 else 0
    
    # Calculate average delivery time
    delivered_with_dates = db.query(models.Challan).filter(
        models.Challan.status == "delivered",
        models.Challan.dispatch_date.isnot(None),
        models.Challan.delivery_date.isnot(None)
    ).all()
    
    if delivered_with_dates:
        total_delivery_time = sum(
            (challan.delivery_date - challan.dispatch_date).total_seconds() / 3600  # Convert to hours
            for challan in delivered_with_dates
        )
        avg_delivery_time_hours = total_delivery_time / len(delivered_with_dates)
    else:
        avg_delivery_time_hours = 0
    
    return {
        "period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        },
        "total_challans": total_challans,
        "total_value": total_value,
        "status_distribution": status_counts,
        "delivery_performance": {
            "delivery_rate": delivery_rate,
            "avg_delivery_time_hours": avg_delivery_time_hours
        },
        "cancelled_challans": status_counts.get("cancelled", 0),
        "pending_challans": status_counts.get("pending", 0)
    }

@router.get("/analytics/delivery-performance")
@handle_database_error
def get_delivery_performance(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get delivery performance metrics"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get challans from the specified period
    challans = db.query(models.Challan).filter(
        models.Challan.challan_date >= start_date
    ).all()
    
    # Calculate metrics
    total_challans = len(challans)
    on_time_deliveries = 0
    late_deliveries = 0
    total_delivery_time = 0
    delivered_count = 0
    
    for challan in challans:
        if challan.status == "delivered" and challan.dispatch_date and challan.delivery_date:
            delivered_count += 1
            delivery_time = (challan.delivery_date - challan.dispatch_date).total_seconds() / 3600
            total_delivery_time += delivery_time
            
            # Assume expected delivery time is 24 hours
            if delivery_time <= 24:
                on_time_deliveries += 1
            else:
                late_deliveries += 1
    
    # Calculate percentages
    on_time_percentage = (on_time_deliveries / delivered_count * 100) if delivered_count > 0 else 0
    avg_delivery_time = total_delivery_time / delivered_count if delivered_count > 0 else 0
    
    return {
        "period_days": days,
        "total_challans": total_challans,
        "delivered_challans": delivered_count,
        "on_time_deliveries": on_time_deliveries,
        "late_deliveries": late_deliveries,
        "on_time_percentage": on_time_percentage,
        "avg_delivery_time_hours": avg_delivery_time,
        "delivery_rate": (delivered_count / total_challans * 100) if total_challans > 0 else 0
    }

# ================= CUSTOMER SPECIFIC CHALLANS =================

@router.get("/customer/{customer_id}", response_model=List[schemas.Challan])
@handle_database_error
def get_customer_challans(
    customer_id: int,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all challans for a specific customer"""
    query = db.query(models.Challan).filter(models.Challan.customer_id == customer_id)
    
    if status:
        query = query.filter(models.Challan.status == status)
    
    return query.limit(limit).all()

@router.get("/customer/{customer_id}/pending", response_model=List[schemas.Challan])
@handle_database_error
def get_customer_pending_challans(customer_id: int, db: Session = Depends(get_db)):
    """Get pending challans for a specific customer"""
    return db.query(models.Challan).filter(
        models.Challan.customer_id == customer_id,
        models.Challan.status == "pending"
    ).all()

# ================= CHALLAN PRINTING & EXPORT =================

@router.get("/{challan_id}/print-data")
@handle_database_error
def get_challan_print_data(challan_id: int, db: Session = Depends(get_db)):
    """Get formatted data for challan printing"""
    challan = challan_crud.get(db, challan_id)
    if not challan:
        raise HTTPException(status_code=404, detail="Challan not found")
    
    # Get challan items
    items = db.query(models.ChallanItem).filter(models.ChallanItem.challan_id == challan_id).all()
    
    # Get customer details
    customer = db.query(models.Customer).filter(models.Customer.id == challan.customer_id).first()
    
    return {
        "challan": challan,
        "items": items,
        "customer": customer,
        "print_date": datetime.utcnow().isoformat(),
        "total_items": len(items),
        "total_quantity": sum(item.quantity for item in items),
        "total_amount": challan.total_amount
    }

@router.get("/reports/daily")
@handle_database_error
def get_daily_challan_report(
    report_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db)
):
    """Get daily challan report"""
    challans = db.query(models.Challan).filter(
        func.date(models.Challan.challan_date) == report_date
    ).all()
    
    # Calculate summary
    total_challans = len(challans)
    total_value = sum(challan.total_amount for challan in challans if challan.total_amount)
    
    status_summary = {}
    for challan in challans:
        status = challan.status
        if status not in status_summary:
            status_summary[status] = {"count": 0, "value": 0}
        status_summary[status]["count"] += 1
        if challan.total_amount:
            status_summary[status]["value"] += challan.total_amount
    
    return {
        "report_date": report_date.isoformat(),
        "total_challans": total_challans,
        "total_value": total_value,
        "status_summary": status_summary,
        "challans": challans
    } 