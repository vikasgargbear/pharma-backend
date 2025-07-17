"""
Public delivery endpoints without authentication
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List

from ..database import get_db

router = APIRouter(prefix="/delivery-public", tags=["delivery-public"])

@router.get("/pending")
async def get_pending_deliveries(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get pending deliveries without authentication"""
    try:
        result = db.execute(text("""
            SELECT o.order_id, o.order_number, o.order_date, 
                   c.customer_name, o.delivery_status,
                   FALSE as has_challan
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.delivery_status != 'delivered'
            ORDER BY o.order_date DESC
            LIMIT :limit OFFSET :skip
        """), {"limit": limit, "skip": skip})
        
        deliveries = []
        for row in result:
            deliveries.append({
                "order_id": row[0],
                "order_number": row[1],
                "order_date": row[2].isoformat() if row[2] else None,
                "customer_name": row[3],
                "delivery_status": row[4],
                "has_challan": row[5]
            })
        
        return {"pending_deliveries": deliveries, "count": len(deliveries)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending deliveries: {str(e)}")

@router.get("/stats")
async def get_delivery_stats(db: Session = Depends(get_db)):
    """Get delivery statistics without authentication"""
    try:
        # Get counts by status
        result = db.execute(text("""
            SELECT 
                COUNT(*) FILTER (WHERE delivery_status = 'pending') as pending,
                COUNT(*) FILTER (WHERE delivery_status = 'in_transit') as in_transit,
                COUNT(*) FILTER (WHERE delivery_status = 'delivered') as delivered,
                COUNT(*) as total
            FROM orders
        """))
        
        row = result.fetchone()
        
        return {
            "stats": {
                "pending": row[0] if row else 0,
                "in_transit": row[1] if row else 0,
                "delivered": row[2] if row else 0,
                "total": row[3] if row else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get delivery stats: {str(e)}")

@router.get("/order/{order_id}/status")
async def get_order_delivery_status(
    order_id: int,
    db: Session = Depends(get_db)
):
    """Get delivery status for a specific order"""
    try:
        result = db.execute(text("""
            SELECT o.order_id, o.order_number, o.delivery_status, 
                   o.delivery_date, c.customer_name,
                   FALSE as has_challan
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_id = :order_id
        """), {"order_id": order_id})
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        return {
            "order_id": row[0],
            "order_number": row[1],
            "delivery_status": row[2],
            "delivery_date": row[3].isoformat() if row[3] else None,
            "customer_name": row[4],
            "has_challan": row[5]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get order status: {str(e)}")

@router.post("/order/{order_id}/mark-delivered")
async def mark_order_delivered(
    order_id: int,
    notes: Dict[str, Any] = {},
    db: Session = Depends(get_db)
):
    """Mark an order as delivered (simplified without authentication)"""
    try:
        # Check if order exists
        check = db.execute(text("SELECT delivery_status FROM orders WHERE order_id = :order_id"), 
                         {"order_id": order_id})
        row = check.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        if row[0] == 'delivered':
            return {"message": "Order already marked as delivered"}
        
        # Update order status
        db.execute(text("""
            UPDATE orders 
            SET delivery_status = 'delivered',
                delivery_date = CURRENT_DATE,
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = :order_id
        """), {"order_id": order_id})
        
        db.commit()
        
        return {
            "message": "Order marked as delivered",
            "order_id": order_id,
            "delivery_notes": notes.get("notes", "")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update order: {str(e)}")