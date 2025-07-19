"""
Sales Returns API Router
Manages product returns, refunds, and inventory adjustments
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from datetime import date, datetime
from decimal import Decimal

from ...database import get_db
from ...models import SalesReturn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sales-returns", tags=["sales-returns"])

@router.get("/")
def get_sales_returns(
    skip: int = 0,
    limit: int = 100,
    customer_id: Optional[int] = Query(None, description="Filter by customer"),
    product_id: Optional[int] = Query(None, description="Filter by product"),
    status: Optional[str] = Query(None, description="Filter by return status"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    db: Session = Depends(get_db)
):
    """Get sales returns with optional filtering"""
    try:
        query = """
            SELECT 
                sr.*,
                o.customer_id,
                c.customer_name,
                p.product_name,
                p.brand_name,
                oi.price as unit_price,
                (sr.quantity * oi.price) as return_amount
            FROM sales_returns sr
            LEFT JOIN orders o ON sr.order_id = o.order_id
            LEFT JOIN customers c ON o.customer_id = c.customer_id
            LEFT JOIN products p ON sr.product_id = p.product_id
            LEFT JOIN order_items oi ON sr.order_id = oi.order_id AND sr.product_id = oi.product_id
            WHERE 1=1
        """
        params = {}
        
        if customer_id:
            query += " AND o.customer_id = :customer_id"
            params["customer_id"] = customer_id
            
        if product_id:
            query += " AND sr.product_id = :product_id"
            params["product_id"] = product_id
            
        if status:
            query += " AND sr.return_status = :status"
            params["status"] = status
            
        if start_date:
            query += " AND sr.return_date >= :start_date"
            params["start_date"] = start_date
            
        if end_date:
            query += " AND sr.return_date <= :end_date"
            params["end_date"] = end_date
            
        query += " ORDER BY sr.return_date DESC LIMIT :limit OFFSET :skip"
        params.update({"limit": limit, "skip": skip})
        
        result = db.execute(text(query), params)
        returns = [dict(row._mapping) for row in result]
        
        return returns
        
    except Exception as e:
        logger.error(f"Error fetching sales returns: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sales returns: {str(e)}")

@router.get("/{return_id}")
def get_sales_return(return_id: int, db: Session = Depends(get_db)):
    """Get a single sales return by ID"""
    try:
        result = db.execute(
            text("""
                SELECT 
                    sr.*,
                    o.customer_id,
                    c.customer_name,
                    c.customer_phone,
                    p.product_name,
                    p.brand_name,
                    b.batch_number,
                    oi.price as unit_price,
                    (sr.quantity * oi.price) as return_amount
                FROM sales_returns sr
                LEFT JOIN orders o ON sr.order_id = o.order_id
                LEFT JOIN customers c ON o.customer_id = c.customer_id
                LEFT JOIN products p ON sr.product_id = p.product_id
                LEFT JOIN batches b ON sr.batch_id = b.batch_id
                LEFT JOIN order_items oi ON sr.order_id = oi.order_id AND sr.product_id = oi.product_id
                WHERE sr.return_id = :return_id
            """),
            {"return_id": return_id}
        )
        sales_return = result.first()
        if not sales_return:
            raise HTTPException(status_code=404, detail="Sales return not found")
        return dict(sales_return._mapping)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sales return {return_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sales return: {str(e)}")

@router.post("/")
def create_sales_return(return_data: dict, db: Session = Depends(get_db)):
    """
    Create a new sales return
    This will:
    1. Create the return record
    2. Update inventory (add stock back)
    3. Create credit note/refund entry
    4. Update order status if fully returned
    """
    try:
        # Validate order and product exist
        order_check = db.execute(
            text("SELECT order_id, order_status FROM orders WHERE order_id = :order_id"),
            {"order_id": return_data.get("order_id")}
        ).first()
        
        if not order_check:
            raise HTTPException(status_code=404, detail="Order not found")
            
        # Check if product was in the order
        order_item = db.execute(
            text("""
                SELECT oi.*, p.product_name 
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                WHERE oi.order_id = :order_id AND oi.product_id = :product_id
            """),
            {
                "order_id": return_data.get("order_id"),
                "product_id": return_data.get("product_id")
            }
        ).first()
        
        if not order_item:
            raise HTTPException(status_code=400, detail="Product not found in order")
            
        # Validate return quantity
        if return_data.get("quantity", 0) > order_item.quantity:
            raise HTTPException(status_code=400, detail="Return quantity exceeds ordered quantity")
        
        # Create return record
        return_id = db.execute(
            text("""
                INSERT INTO sales_returns (
                    order_id, product_id, batch_id, quantity, 
                    reason, return_date, return_status, 
                    refund_amount, credit_note_number
                ) VALUES (
                    :order_id, :product_id, :batch_id, :quantity,
                    :reason, :return_date, :return_status,
                    :refund_amount, :credit_note_number
                ) RETURNING return_id
            """),
            {
                "order_id": return_data.get("order_id"),
                "product_id": return_data.get("product_id"),
                "batch_id": return_data.get("batch_id"),
                "quantity": return_data.get("quantity"),
                "reason": return_data.get("reason"),
                "return_date": return_data.get("return_date", datetime.utcnow()),
                "return_status": return_data.get("return_status", "pending"),
                "refund_amount": return_data.get("quantity", 0) * order_item.price,
                "credit_note_number": return_data.get("credit_note_number")
            }
        ).scalar()
        
        # Update inventory - add stock back
        if return_data.get("batch_id"):
            db.execute(
                text("""
                    UPDATE batches 
                    SET quantity_available = quantity_available + :quantity,
                        quantity_sold = quantity_sold - :quantity
                    WHERE batch_id = :batch_id
                """),
                {
                    "quantity": return_data.get("quantity"),
                    "batch_id": return_data.get("batch_id")
                }
            )
        
        db.commit()
        
        return {
            "return_id": return_id,
            "message": "Sales return created successfully",
            "refund_amount": float(return_data.get("quantity", 0) * order_item.price)
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating sales return: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create sales return: {str(e)}")

@router.put("/{return_id}/approve")
def approve_sales_return(return_id: int, approval_data: dict = None, db: Session = Depends(get_db)):
    """Approve a sales return and process refund"""
    try:
        # Get return details
        sales_return = db.execute(
            text("SELECT * FROM sales_returns WHERE return_id = :return_id"),
            {"return_id": return_id}
        ).first()
        
        if not sales_return:
            raise HTTPException(status_code=404, detail="Sales return not found")
            
        if sales_return.return_status == "approved":
            raise HTTPException(status_code=400, detail="Return already approved")
        
        # Update return status
        db.execute(
            text("""
                UPDATE sales_returns 
                SET return_status = 'approved',
                    approved_by = :approved_by,
                    approved_date = :approved_date,
                    notes = :notes
                WHERE return_id = :return_id
            """),
            {
                "return_id": return_id,
                "approved_by": approval_data.get("approved_by") if approval_data else None,
                "approved_date": datetime.utcnow(),
                "notes": approval_data.get("notes") if approval_data else None
            }
        )
        
        # Create refund/credit note entry
        # This would integrate with your payment/accounting system
        
        db.commit()
        
        return {"message": "Sales return approved successfully"}
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving sales return {return_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to approve sales return: {str(e)}")

@router.put("/{return_id}/reject")
def reject_sales_return(return_id: int, rejection_data: dict = None, db: Session = Depends(get_db)):
    """Reject a sales return"""
    try:
        # Update return status
        result = db.execute(
            text("""
                UPDATE sales_returns 
                SET return_status = 'rejected',
                    rejected_reason = :reason,
                    notes = :notes
                WHERE return_id = :return_id
                RETURNING return_id
            """),
            {
                "return_id": return_id,
                "reason": rejection_data.get("reason") if rejection_data else None,
                "notes": rejection_data.get("notes") if rejection_data else None
            }
        )
        
        if not result.scalar():
            raise HTTPException(status_code=404, detail="Sales return not found")
        
        db.commit()
        
        return {"message": "Sales return rejected"}
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error rejecting sales return {return_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reject sales return: {str(e)}")

@router.get("/analytics/summary")
def get_return_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get sales return analytics"""
    try:
        query = """
            SELECT 
                COUNT(*) as total_returns,
                COUNT(CASE WHEN return_status = 'approved' THEN 1 END) as approved_returns,
                COUNT(CASE WHEN return_status = 'pending' THEN 1 END) as pending_returns,
                COUNT(CASE WHEN return_status = 'rejected' THEN 1 END) as rejected_returns,
                SUM(CASE WHEN return_status = 'approved' THEN refund_amount ELSE 0 END) as total_refund_amount,
                COUNT(DISTINCT order_id) as unique_orders_with_returns,
                COUNT(DISTINCT product_id) as unique_products_returned
            FROM sales_returns
            WHERE 1=1
        """
        params = {}
        
        if start_date:
            query += " AND return_date >= :start_date"
            params["start_date"] = start_date
            
        if end_date:
            query += " AND return_date <= :end_date"
            params["end_date"] = end_date
        
        result = db.execute(text(query), params)
        analytics = dict(result.first()._mapping)
        
        # Get top reasons for returns
        reason_query = """
            SELECT 
                reason,
                COUNT(*) as count,
                SUM(refund_amount) as total_amount
            FROM sales_returns
            WHERE return_status = 'approved'
        """
        
        if start_date:
            reason_query += " AND return_date >= :start_date"
        if end_date:
            reason_query += " AND return_date <= :end_date"
            
        reason_query += " GROUP BY reason ORDER BY count DESC LIMIT 10"
        
        reason_result = db.execute(text(reason_query), params)
        top_reasons = [dict(row._mapping) for row in reason_result]
        
        analytics["top_return_reasons"] = top_reasons
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error fetching return analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get return analytics: {str(e)}")