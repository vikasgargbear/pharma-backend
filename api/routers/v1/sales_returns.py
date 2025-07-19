"""
Sales Returns API Router (Simplified)
Uses existing inventory_movements table for returns
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from datetime import date, datetime
from decimal import Decimal

from ...database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sales-returns", tags=["sales-returns"])

@router.get("/")
def get_sales_returns(
    skip: int = 0,
    limit: int = 100,
    customer_id: Optional[int] = Query(None, description="Filter by customer"),
    product_id: Optional[int] = Query(None, description="Filter by product"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    db: Session = Depends(get_db)
):
    """Get sales returns from inventory movements"""
    try:
        query = """
            SELECT 
                im.movement_id as return_id,
                im.movement_date as return_date,
                im.product_id,
                p.product_name,
                p.brand_name,
                im.batch_id,
                b.batch_number,
                im.quantity_in as quantity_returned,
                im.reference_id as order_id,
                im.reference_number,
                im.notes as reason,
                o.customer_id,
                c.customer_name,
                (im.quantity_in * COALESCE(b.selling_price, p.sale_price)) as refund_amount
            FROM inventory_movements im
            JOIN products p ON im.product_id = p.product_id
            LEFT JOIN batches b ON im.batch_id = b.batch_id
            LEFT JOIN orders o ON im.reference_id = o.order_id AND im.reference_type = 'sales_return'
            LEFT JOIN customers c ON o.customer_id = c.customer_id
            WHERE im.movement_type = 'sales_return'
        """
        params = {}
        
        if customer_id:
            query += " AND o.customer_id = :customer_id"
            params["customer_id"] = customer_id
            
        if product_id:
            query += " AND im.product_id = :product_id"
            params["product_id"] = product_id
            
        if start_date:
            query += " AND im.movement_date >= :start_date"
            params["start_date"] = start_date
            
        if end_date:
            query += " AND im.movement_date <= :end_date"
            params["end_date"] = end_date
            
        query += " ORDER BY im.movement_date DESC LIMIT :limit OFFSET :skip"
        params.update({"limit": limit, "skip": skip})
        
        result = db.execute(text(query), params)
        returns = [dict(row._mapping) for row in result]
        
        return returns
        
    except Exception as e:
        logger.error(f"Error fetching sales returns: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sales returns: {str(e)}")

@router.post("/")
def create_sales_return(return_data: dict, db: Session = Depends(get_db)):
    """
    Create a sales return using inventory movements
    This will:
    1. Create inventory movement record (quantity IN)
    2. Update batch quantity (add stock back)
    3. Update order status if needed
    """
    try:
        # Validate order exists
        order_check = db.execute(
            text("SELECT order_id, customer_id FROM orders WHERE order_id = :order_id"),
            {"order_id": return_data.get("order_id")}
        ).first()
        
        if not order_check:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get product and batch info
        product_info = db.execute(
            text("""
                SELECT p.product_id, p.product_name, p.sale_price, b.batch_id, b.selling_price
                FROM products p
                LEFT JOIN batches b ON p.product_id = b.product_id
                WHERE p.product_id = :product_id
                AND (b.batch_id = :batch_id OR :batch_id IS NULL)
                LIMIT 1
            """),
            {
                "product_id": return_data.get("product_id"),
                "batch_id": return_data.get("batch_id")
            }
        ).first()
        
        if not product_info:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Create inventory movement for return
        movement_id = db.execute(
            text("""
                INSERT INTO inventory_movements (
                    org_id, movement_date, movement_type,
                    product_id, batch_id, quantity_in, quantity_out,
                    reference_type, reference_id, reference_number,
                    notes, performed_by
                ) VALUES (
                    '12de5e22-eee7-4d25-b3a7-d16d01c6170f', -- Default org
                    :movement_date, 'sales_return',
                    :product_id, :batch_id, :quantity, 0,
                    'sales_return', :order_id, :reference_number,
                    :notes, :performed_by
                ) RETURNING movement_id
            """),
            {
                "movement_date": return_data.get("return_date", datetime.utcnow()),
                "product_id": return_data.get("product_id"),
                "batch_id": return_data.get("batch_id"),
                "quantity": return_data.get("quantity"),
                "order_id": return_data.get("order_id"),
                "reference_number": f"SR-{return_data.get('order_id')}-{datetime.now().strftime('%Y%m%d%H%M')}",
                "notes": return_data.get("reason"),
                "performed_by": return_data.get("performed_by")
            }
        ).scalar()
        
        # Update batch quantity if batch_id provided
        if return_data.get("batch_id"):
            db.execute(
                text("""
                    UPDATE batches 
                    SET quantity_available = quantity_available + :quantity,
                        quantity_sold = GREATEST(0, quantity_sold - :quantity)
                    WHERE batch_id = :batch_id
                """),
                {
                    "quantity": return_data.get("quantity"),
                    "batch_id": return_data.get("batch_id")
                }
            )
        
        db.commit()
        
        # Calculate refund amount
        unit_price = product_info.selling_price or product_info.sale_price or 0
        refund_amount = float(return_data.get("quantity", 0) * unit_price)
        
        return {
            "movement_id": movement_id,
            "message": "Sales return created successfully",
            "refund_amount": refund_amount,
            "reference_number": f"SR-{return_data.get('order_id')}-{datetime.now().strftime('%Y%m%d%H%M')}"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating sales return: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create sales return: {str(e)}")

@router.get("/analytics/summary")
def get_return_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get sales return analytics from inventory movements"""
    try:
        query = """
            SELECT 
                COUNT(*) as total_returns,
                SUM(im.quantity_in) as total_quantity_returned,
                COUNT(DISTINCT im.product_id) as unique_products_returned,
                COUNT(DISTINCT o.customer_id) as unique_customers,
                SUM(im.quantity_in * COALESCE(b.selling_price, p.sale_price)) as total_refund_value
            FROM inventory_movements im
            JOIN products p ON im.product_id = p.product_id
            LEFT JOIN batches b ON im.batch_id = b.batch_id
            LEFT JOIN orders o ON im.reference_id = o.order_id AND im.reference_type = 'sales_return'
            WHERE im.movement_type = 'sales_return'
        """
        params = {}
        
        if start_date:
            query += " AND im.movement_date >= :start_date"
            params["start_date"] = start_date
            
        if end_date:
            query += " AND im.movement_date <= :end_date"
            params["end_date"] = end_date
        
        result = db.execute(text(query), params)
        analytics = dict(result.first()._mapping)
        
        # Get top returned products
        products_query = """
            SELECT 
                p.product_id,
                p.product_name,
                p.brand_name,
                COUNT(*) as return_count,
                SUM(im.quantity_in) as total_quantity,
                SUM(im.quantity_in * COALESCE(b.selling_price, p.sale_price)) as total_value
            FROM inventory_movements im
            JOIN products p ON im.product_id = p.product_id
            LEFT JOIN batches b ON im.batch_id = b.batch_id
            WHERE im.movement_type = 'sales_return'
        """
        
        if start_date:
            products_query += " AND im.movement_date >= :start_date"
        if end_date:
            products_query += " AND im.movement_date <= :end_date"
            
        products_query += " GROUP BY p.product_id, p.product_name, p.brand_name ORDER BY total_quantity DESC LIMIT 10"
        
        products_result = db.execute(text(products_query), params)
        top_returned_products = [dict(row._mapping) for row in products_result]
        
        analytics["top_returned_products"] = top_returned_products
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error fetching return analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get return analytics: {str(e)}")