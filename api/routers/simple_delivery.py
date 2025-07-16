from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel

from ..database import get_db
from ..models import User
from ..dependencies import get_current_user

router = APIRouter(prefix="/delivery", tags=["Simple Delivery"])

# =============================================
# SIMPLE PYDANTIC MODELS
# =============================================

class DeliveryConfirmRequest(BaseModel):
    delivery_notes: Optional[str] = None
    delivery_issues: Optional[str] = None
    customer_satisfied: Optional[bool] = None
    customer_feedback: Optional[str] = None

class DeliveryStatusResponse(BaseModel):
    order_id: int
    delivery_status: str
    delivery_date: Optional[date]
    has_challan: bool
    is_delivered: bool
    confirmed_by_name: Optional[str]
    delivery_notes: Optional[str]

class PendingDeliveryResponse(BaseModel):
    order_id: int
    customer_name: str
    order_date: datetime
    has_challan: bool
    challan_id: Optional[int]
    delivery_status: str

# =============================================
# SIMPLE DELIVERY ENDPOINTS
# =============================================

@router.post("/order/{order_id}/delivered")
async def mark_order_delivered(
    order_id: int,
    request: DeliveryConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark an order as delivered (no challan required)
    Simple ERP endpoint - just mark as delivered with notes
    """
    try:
        # Call the database function
        result = db.execute(
            "SELECT mark_order_delivered(:order_id, :user_id, :notes)",
            {
                "order_id": order_id,
                "user_id": current_user.user_id,
                "notes": request.delivery_notes
            }
        ).fetchone()
        
        if result and result[0]:
            # Update additional fields if provided
            if request.delivery_issues or request.customer_satisfied is not None or request.customer_feedback:
                db.execute(
                    """
                    UPDATE delivery_confirmations 
                    SET delivery_issues = :issues,
                        customer_satisfied = :satisfied,
                        customer_feedback = :feedback
                    WHERE order_id = :order_id
                    """,
                    {
                        "issues": request.delivery_issues,
                        "satisfied": request.customer_satisfied,
                        "feedback": request.customer_feedback,
                        "order_id": order_id
                    }
                )
            
            db.commit()
            return {"success": True, "message": "Order marked as delivered"}
        else:
            raise HTTPException(status_code=400, detail="Failed to mark order as delivered")
            
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/challan/{challan_id}/delivered")
async def mark_challan_delivered(
    challan_id: int,
    request: DeliveryConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a challan as delivered
    Simple ERP endpoint - just mark as delivered with notes
    """
    try:
        # Call the database function
        result = db.execute(
            "SELECT mark_challan_delivered(:challan_id, :user_id, :notes)",
            {
                "challan_id": challan_id,
                "user_id": current_user.user_id,
                "notes": request.delivery_notes
            }
        ).fetchone()
        
        if result and result[0]:
            # Update additional fields if provided
            if request.delivery_issues or request.customer_satisfied is not None or request.customer_feedback:
                db.execute(
                    """
                    UPDATE delivery_confirmations 
                    SET delivery_issues = :issues,
                        customer_satisfied = :satisfied,
                        customer_feedback = :feedback
                    WHERE challan_id = :challan_id
                    """,
                    {
                        "issues": request.delivery_issues,
                        "satisfied": request.customer_satisfied,
                        "feedback": request.customer_feedback,
                        "challan_id": challan_id
                    }
                )
            
            db.commit()
            return {"success": True, "message": "Challan marked as delivered"}
        else:
            raise HTTPException(status_code=400, detail="Failed to mark challan as delivered")
            
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/order/{order_id}/status", response_model=DeliveryStatusResponse)
async def get_order_delivery_status(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get delivery status for an order
    Simple ERP endpoint - check if order is delivered
    """
    try:
        result = db.execute(
            "SELECT * FROM get_delivery_status(:order_id)",
            {"order_id": order_id}
        ).fetchone()
        
        if result:
            return DeliveryStatusResponse(
                order_id=result[0],
                delivery_status=result[1] or "pending",
                delivery_date=result[2],
                has_challan=result[3] or False,
                is_delivered=result[4] or False,
                confirmed_by_name=result[5],
                delivery_notes=result[6]
            )
        else:
            raise HTTPException(status_code=404, detail="Order not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pending", response_model=List[PendingDeliveryResponse])
async def get_pending_deliveries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all pending deliveries
    Simple ERP endpoint - list orders that need delivery confirmation
    """
    try:
        results = db.execute("SELECT * FROM get_pending_deliveries()").fetchall()
        
        return [
            PendingDeliveryResponse(
                order_id=row[0],
                customer_name=row[1],
                order_date=row[2],
                has_challan=row[3] or False,
                challan_id=row[4],
                delivery_status=row[5] or "pending"
            )
            for row in results
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/order/{order_id}/status")
async def update_order_delivery_status(
    order_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update order delivery status
    Simple ERP endpoint - change status to pending/dispatched/delivered/cancelled/pickup
    """
    valid_statuses = ["pending", "dispatched", "delivered", "cancelled", "pickup"]
    
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    try:
        # Simple update - no complex logic
        result = db.execute(
            "UPDATE orders SET delivery_status = :status WHERE order_id = :order_id",
            {"status": status, "order_id": order_id}
        )
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Order not found")
        
        db.commit()
        return {"success": True, "message": f"Order status updated to {status}"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_delivery_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get simple delivery statistics
    Simple ERP endpoint - basic counts and stats
    """
    try:
        # Get delivery status counts
        status_counts = db.execute("""
            SELECT 
                delivery_status,
                COUNT(*) as count
            FROM orders
            WHERE delivery_status IS NOT NULL
            GROUP BY delivery_status
        """).fetchall()
        
        # Get today's deliveries
        today_deliveries = db.execute("""
            SELECT COUNT(*) as count
            FROM orders
            WHERE delivery_date = CURRENT_DATE
        """).fetchone()
        
        # Get pending deliveries count
        pending_count = db.execute("""
            SELECT COUNT(*) as count
            FROM orders
            WHERE delivery_status IN ('pending', 'dispatched')
        """).fetchone()
        
        return {
            "status_counts": {row[0]: row[1] for row in status_counts},
            "today_deliveries": today_deliveries[0] if today_deliveries else 0,
            "pending_deliveries": pending_count[0] if pending_count else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# SIMPLE BULK OPERATIONS
# =============================================

@router.post("/bulk/mark-delivered")
async def bulk_mark_delivered(
    order_ids: List[int],
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark multiple orders as delivered at once
    Simple ERP endpoint - bulk operations for efficiency
    """
    try:
        success_count = 0
        failed_orders = []
        
        for order_id in order_ids:
            try:
                result = db.execute(
                    "SELECT mark_order_delivered(:order_id, :user_id, :notes)",
                    {
                        "order_id": order_id,
                        "user_id": current_user.user_id,
                        "notes": notes
                    }
                ).fetchone()
                
                if result and result[0]:
                    success_count += 1
                else:
                    failed_orders.append(order_id)
            except:
                failed_orders.append(order_id)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Marked {success_count} orders as delivered",
            "success_count": success_count,
            "failed_orders": failed_orders
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 