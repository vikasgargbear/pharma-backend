"""
Enhanced Purchase Management v2 - Works with automatic batch creation
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database.connection import get_db
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/{purchase_id}/receive-v2")
def receive_purchase_items_v2(
    purchase_id: int,
    receive_data: dict,
    db: Session = Depends(get_db)
):
    """
    Receive items from a purchase order - Version 2
    Works with the automatic batch creation trigger
    """
    try:
        # Get purchase details
        purchase = db.execute(
            text("SELECT * FROM purchases WHERE purchase_id = :id"),
            {"id": purchase_id}
        ).first()
        
        if not purchase:
            raise HTTPException(status_code=404, detail="Purchase not found")
        
        if purchase.purchase_status == "received":
            raise HTTPException(status_code=400, detail="Purchase already received")
        
        received_items = receive_data.get("items", [])
        
        # Update purchase items with received quantities
        for item in received_items:
            item_id = item.get("purchase_item_id")
            received_qty = item.get("received_quantity", 0)
            
            if received_qty <= 0:
                continue
            
            # Update the purchase item with batch info if provided
            update_fields = ["received_quantity = :received_quantity"]
            params = {
                "item_id": item_id,
                "purchase_id": purchase_id,
                "received_quantity": received_qty
            }
            
            # Only update batch number if provided
            if item.get("batch_number"):
                update_fields.append("batch_number = :batch_number")
                params["batch_number"] = item["batch_number"]
            
            if item.get("expiry_date"):
                update_fields.append("expiry_date = :expiry_date")
                params["expiry_date"] = item["expiry_date"]
            
            if item.get("manufacturing_date"):
                update_fields.append("manufacturing_date = :manufacturing_date")
                params["manufacturing_date"] = item["manufacturing_date"]
            
            db.execute(
                text(f"""
                    UPDATE purchase_items 
                    SET {', '.join(update_fields)},
                        item_status = 'received',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE purchase_item_id = :item_id 
                    AND purchase_id = :purchase_id
                """),
                params
            )
        
        # Update purchase status to received
        # This will trigger the automatic batch creation
        grn_number = f"GRN-{purchase.purchase_number}"
        
        db.execute(
            text("""
                UPDATE purchases 
                SET purchase_status = 'received',
                    grn_number = :grn_number,
                    grn_date = CURRENT_DATE
                WHERE purchase_id = :purchase_id
            """),
            {
                "grn_number": grn_number,
                "purchase_id": purchase_id
            }
        )
        
        db.commit()
        
        # Count batches created (by the trigger)
        batch_count = db.execute(
            text("""
                SELECT COUNT(*) as count 
                FROM batches 
                WHERE purchase_id = :purchase_id
            """),
            {"purchase_id": purchase_id}
        ).scalar()
        
        return {
            "message": "Purchase received successfully",
            "purchase_id": purchase_id,
            "grn_number": grn_number,
            "batches_created": batch_count,
            "note": "Batches auto-created by system trigger"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error receiving items: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to receive items: {str(e)}")

@router.get("/{purchase_id}/batches")
def get_purchase_batches(
    purchase_id: int,
    db: Session = Depends(get_db)
):
    """Get all batches created from a purchase"""
    try:
        batches = db.execute(
            text("""
                SELECT 
                    b.batch_id,
                    b.batch_number,
                    b.product_id,
                    p.product_name,
                    b.quantity_received,
                    b.quantity_available,
                    b.expiry_date,
                    b.manufacturing_date,
                    b.cost_price,
                    b.mrp,
                    b.batch_status
                FROM batches b
                JOIN products p ON b.product_id = p.product_id
                WHERE b.purchase_id = :purchase_id
                ORDER BY b.created_at DESC
            """),
            {"purchase_id": purchase_id}
        ).fetchall()
        
        return [
            {
                "batch_id": b.batch_id,
                "batch_number": b.batch_number,
                "product_id": b.product_id,
                "product_name": b.product_name,
                "quantity_received": b.quantity_received,
                "quantity_available": b.quantity_available,
                "expiry_date": b.expiry_date.isoformat() if b.expiry_date else None,
                "manufacturing_date": b.manufacturing_date.isoformat() if b.manufacturing_date else None,
                "cost_price": float(b.cost_price),
                "mrp": float(b.mrp),
                "status": b.batch_status
            }
            for b in batches
        ]
        
    except Exception as e:
        logger.error(f"Error getting purchase batches: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get batches: {str(e)}")