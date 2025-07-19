"""
Stock Adjustments API Router
Manages inventory adjustments for damage, expiry, physical counts, etc.
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

router = APIRouter(prefix="/api/v1/stock-adjustments", tags=["stock-adjustments"])

@router.get("/")
def get_stock_adjustments(
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[int] = Query(None, description="Filter by product"),
    batch_id: Optional[int] = Query(None, description="Filter by batch"),
    adjustment_type: Optional[str] = Query(None, description="Filter by type: damage, expiry, count, theft, other"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    db: Session = Depends(get_db)
):
    """Get stock adjustments with optional filtering"""
    try:
        query = """
            SELECT 
                sa.*,
                p.product_name,
                p.brand_name,
                b.batch_number,
                b.expiry_date,
                u.username as adjusted_by_name
            FROM stock_adjustments sa
            LEFT JOIN products p ON sa.product_id = p.product_id
            LEFT JOIN batches b ON sa.batch_id = b.batch_id
            LEFT JOIN users u ON sa.adjusted_by = u.id
            WHERE 1=1
        """
        params = {}
        
        if product_id:
            query += " AND sa.product_id = :product_id"
            params["product_id"] = product_id
            
        if batch_id:
            query += " AND sa.batch_id = :batch_id"
            params["batch_id"] = batch_id
            
        if adjustment_type:
            query += " AND sa.adjustment_type = :adjustment_type"
            params["adjustment_type"] = adjustment_type
            
        if start_date:
            query += " AND sa.adjustment_date >= :start_date"
            params["start_date"] = start_date
            
        if end_date:
            query += " AND sa.adjustment_date <= :end_date"
            params["end_date"] = end_date
            
        query += " ORDER BY sa.adjustment_date DESC LIMIT :limit OFFSET :skip"
        params.update({"limit": limit, "skip": skip})
        
        result = db.execute(text(query), params)
        adjustments = [dict(row._mapping) for row in result]
        
        return adjustments
        
    except Exception as e:
        logger.error(f"Error fetching stock adjustments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stock adjustments: {str(e)}")

@router.get("/{adjustment_id}")
def get_stock_adjustment(adjustment_id: int, db: Session = Depends(get_db)):
    """Get a single stock adjustment by ID"""
    try:
        result = db.execute(
            text("""
                SELECT 
                    sa.*,
                    p.product_name,
                    p.brand_name,
                    p.mrp,
                    b.batch_number,
                    b.expiry_date,
                    b.purchase_price,
                    u.username as adjusted_by_name,
                    (sa.quantity_adjusted * b.purchase_price) as adjustment_value
                FROM stock_adjustments sa
                LEFT JOIN products p ON sa.product_id = p.product_id
                LEFT JOIN batches b ON sa.batch_id = b.batch_id
                LEFT JOIN users u ON sa.adjusted_by = u.id
                WHERE sa.adjustment_id = :adjustment_id
            """),
            {"adjustment_id": adjustment_id}
        )
        adjustment = result.first()
        if not adjustment:
            raise HTTPException(status_code=404, detail="Stock adjustment not found")
        return dict(adjustment._mapping)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock adjustment {adjustment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stock adjustment: {str(e)}")

@router.post("/")
def create_stock_adjustment(adjustment_data: dict, db: Session = Depends(get_db)):
    """
    Create a new stock adjustment
    This will:
    1. Create the adjustment record
    2. Update batch quantities
    3. Create inventory movement record
    4. Log the adjustment for audit
    """
    try:
        # Validate batch exists and has enough stock for negative adjustments
        batch = db.execute(
            text("""
                SELECT b.*, p.product_name 
                FROM batches b
                JOIN products p ON b.product_id = p.product_id
                WHERE b.batch_id = :batch_id
            """),
            {"batch_id": adjustment_data.get("batch_id")}
        ).first()
        
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
            
        quantity_adjusted = adjustment_data.get("quantity_adjusted", 0)
        
        # For negative adjustments, check available quantity
        if quantity_adjusted < 0 and abs(quantity_adjusted) > batch.quantity_available:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock. Available: {batch.quantity_available}"
            )
        
        # Create adjustment record
        adjustment_id = db.execute(
            text("""
                INSERT INTO stock_adjustments (
                    product_id, batch_id, adjustment_type, 
                    quantity_adjusted, old_quantity, new_quantity,
                    reason, adjustment_date, adjusted_by,
                    reference_number, notes
                ) VALUES (
                    :product_id, :batch_id, :adjustment_type,
                    :quantity_adjusted, :old_quantity, :new_quantity,
                    :reason, :adjustment_date, :adjusted_by,
                    :reference_number, :notes
                ) RETURNING adjustment_id
            """),
            {
                "product_id": batch.product_id,
                "batch_id": adjustment_data.get("batch_id"),
                "adjustment_type": adjustment_data.get("adjustment_type"),
                "quantity_adjusted": quantity_adjusted,
                "old_quantity": batch.quantity_available,
                "new_quantity": batch.quantity_available + quantity_adjusted,
                "reason": adjustment_data.get("reason"),
                "adjustment_date": adjustment_data.get("adjustment_date", datetime.utcnow()),
                "adjusted_by": adjustment_data.get("adjusted_by"),
                "reference_number": adjustment_data.get("reference_number"),
                "notes": adjustment_data.get("notes")
            }
        ).scalar()
        
        # Update batch quantity
        db.execute(
            text("""
                UPDATE batches 
                SET quantity_available = quantity_available + :quantity_adjusted
                WHERE batch_id = :batch_id
            """),
            {
                "quantity_adjusted": quantity_adjusted,
                "batch_id": adjustment_data.get("batch_id")
            }
        )
        
        # Create inventory movement record
        movement_type = "adjustment_in" if quantity_adjusted > 0 else "adjustment_out"
        db.execute(
            text("""
                INSERT INTO inventory_movements (
                    product_id, batch_id, movement_type,
                    quantity, movement_date, reference_type,
                    reference_id, notes
                ) VALUES (
                    :product_id, :batch_id, :movement_type,
                    :quantity, :movement_date, :reference_type,
                    :reference_id, :notes
                )
            """),
            {
                "product_id": batch.product_id,
                "batch_id": adjustment_data.get("batch_id"),
                "movement_type": movement_type,
                "quantity": abs(quantity_adjusted),
                "movement_date": datetime.utcnow(),
                "reference_type": "stock_adjustment",
                "reference_id": adjustment_id,
                "notes": f"{adjustment_data.get('adjustment_type')}: {adjustment_data.get('reason')}"
            }
        )
        
        db.commit()
        
        return {
            "adjustment_id": adjustment_id,
            "message": "Stock adjustment created successfully",
            "new_quantity": batch.quantity_available + quantity_adjusted
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating stock adjustment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create stock adjustment: {str(e)}")

@router.post("/physical-count")
def create_physical_count_adjustment(count_data: dict, db: Session = Depends(get_db)):
    """
    Create stock adjustments based on physical count
    Compares counted quantity with system quantity and creates adjustments
    """
    try:
        adjustments_created = []
        
        for item in count_data.get("count_items", []):
            batch_id = item.get("batch_id")
            counted_quantity = item.get("counted_quantity")
            
            # Get current system quantity
            batch = db.execute(
                text("SELECT * FROM batches WHERE batch_id = :batch_id"),
                {"batch_id": batch_id}
            ).first()
            
            if not batch:
                continue
                
            system_quantity = batch.quantity_available
            difference = counted_quantity - system_quantity
            
            # Only create adjustment if there's a difference
            if difference != 0:
                adjustment_type = "count_gain" if difference > 0 else "count_loss"
                
                adjustment_id = db.execute(
                    text("""
                        INSERT INTO stock_adjustments (
                            product_id, batch_id, adjustment_type,
                            quantity_adjusted, old_quantity, new_quantity,
                            reason, adjustment_date, adjusted_by,
                            reference_number
                        ) VALUES (
                            :product_id, :batch_id, :adjustment_type,
                            :quantity_adjusted, :old_quantity, :new_quantity,
                            :reason, :adjustment_date, :adjusted_by,
                            :reference_number
                        ) RETURNING adjustment_id
                    """),
                    {
                        "product_id": batch.product_id,
                        "batch_id": batch_id,
                        "adjustment_type": adjustment_type,
                        "quantity_adjusted": difference,
                        "old_quantity": system_quantity,
                        "new_quantity": counted_quantity,
                        "reason": "Physical inventory count",
                        "adjustment_date": count_data.get("count_date", datetime.utcnow()),
                        "adjusted_by": count_data.get("counted_by"),
                        "reference_number": count_data.get("count_reference")
                    }
                ).scalar()
                
                # Update batch quantity
                db.execute(
                    text("""
                        UPDATE batches 
                        SET quantity_available = :new_quantity
                        WHERE batch_id = :batch_id
                    """),
                    {
                        "new_quantity": counted_quantity,
                        "batch_id": batch_id
                    }
                )
                
                adjustments_created.append({
                    "adjustment_id": adjustment_id,
                    "batch_id": batch_id,
                    "difference": difference
                })
        
        db.commit()
        
        return {
            "message": "Physical count adjustments created",
            "adjustments_created": len(adjustments_created),
            "details": adjustments_created
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating physical count adjustments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create adjustments: {str(e)}")

@router.post("/expire-batches")
def expire_batches(expiry_data: dict = None, db: Session = Depends(get_db)):
    """
    Mark expired batches and create stock adjustments
    Can be run manually or scheduled
    """
    try:
        # Find expired batches
        expired_batches = db.execute(
            text("""
                SELECT b.*, p.product_name
                FROM batches b
                JOIN products p ON b.product_id = p.product_id
                WHERE b.expiry_date <= CURRENT_DATE
                AND b.quantity_available > 0
                AND b.batch_status != 'expired'
            """)
        ).fetchall()
        
        adjustments_created = []
        
        for batch in expired_batches:
            # Create expiry adjustment
            adjustment_id = db.execute(
                text("""
                    INSERT INTO stock_adjustments (
                        product_id, batch_id, adjustment_type,
                        quantity_adjusted, old_quantity, new_quantity,
                        reason, adjustment_date, adjusted_by
                    ) VALUES (
                        :product_id, :batch_id, 'expiry',
                        :quantity_adjusted, :old_quantity, 0,
                        'Product expired', CURRENT_DATE, :adjusted_by
                    ) RETURNING adjustment_id
                """),
                {
                    "product_id": batch.product_id,
                    "batch_id": batch.batch_id,
                    "quantity_adjusted": -batch.quantity_available,
                    "old_quantity": batch.quantity_available,
                    "adjusted_by": expiry_data.get("adjusted_by") if expiry_data else None
                }
            ).scalar()
            
            # Update batch
            db.execute(
                text("""
                    UPDATE batches 
                    SET quantity_available = 0,
                        batch_status = 'expired'
                    WHERE batch_id = :batch_id
                """),
                {"batch_id": batch.batch_id}
            )
            
            adjustments_created.append({
                "adjustment_id": adjustment_id,
                "batch_id": batch.batch_id,
                "product_name": batch.product_name,
                "quantity_expired": batch.quantity_available
            })
        
        db.commit()
        
        return {
            "message": "Expired batches processed",
            "batches_expired": len(adjustments_created),
            "details": adjustments_created
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing expired batches: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process expired batches: {str(e)}")

@router.get("/analytics/summary")
def get_adjustment_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get stock adjustment analytics"""
    try:
        query = """
            SELECT 
                COUNT(*) as total_adjustments,
                SUM(CASE WHEN quantity_adjusted > 0 THEN quantity_adjusted ELSE 0 END) as total_quantity_added,
                SUM(CASE WHEN quantity_adjusted < 0 THEN ABS(quantity_adjusted) ELSE 0 END) as total_quantity_removed,
                COUNT(DISTINCT product_id) as products_affected,
                COUNT(DISTINCT batch_id) as batches_affected
            FROM stock_adjustments
            WHERE 1=1
        """
        params = {}
        
        if start_date:
            query += " AND adjustment_date >= :start_date"
            params["start_date"] = start_date
            
        if end_date:
            query += " AND adjustment_date <= :end_date"
            params["end_date"] = end_date
        
        result = db.execute(text(query), params)
        analytics = dict(result.first()._mapping)
        
        # Get breakdown by adjustment type
        type_query = """
            SELECT 
                adjustment_type,
                COUNT(*) as count,
                SUM(ABS(quantity_adjusted)) as total_quantity,
                SUM(ABS(quantity_adjusted * COALESCE(b.purchase_price, 0))) as total_value
            FROM stock_adjustments sa
            LEFT JOIN batches b ON sa.batch_id = b.batch_id
            WHERE 1=1
        """
        
        if start_date:
            type_query += " AND sa.adjustment_date >= :start_date"
        if end_date:
            type_query += " AND sa.adjustment_date <= :end_date"
            
        type_query += " GROUP BY adjustment_type ORDER BY total_quantity DESC"
        
        type_result = db.execute(text(type_query), params)
        adjustment_types = [dict(row._mapping) for row in type_result]
        
        analytics["by_adjustment_type"] = adjustment_types
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error fetching adjustment analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get adjustment analytics: {str(e)}")