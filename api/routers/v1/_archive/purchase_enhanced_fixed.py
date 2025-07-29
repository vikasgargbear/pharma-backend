"""
Fixed Purchase Enhanced - Works with automatic batch trigger
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

@router.post("/{purchase_id}/receive-fixed")
def receive_purchase_items_fixed(
    purchase_id: int,
    receive_data: dict,
    db: Session = Depends(get_db)
):
    """
    Receive items from a purchase order - Fixed version
    Updates purchase items and status, lets trigger create batches
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
        
        # Update purchase items with received info
        for item in received_items:
            item_id = item.get("purchase_item_id")
            received_qty = item.get("received_quantity", 0)
            
            if received_qty <= 0:
                continue
            
            # Build update query
            update_fields = ["received_quantity = :received_quantity"]
            params = {
                "item_id": item_id,
                "purchase_id": purchase_id,
                "received_quantity": received_qty
            }
            
            # Optional fields
            if item.get("batch_number"):
                update_fields.append("batch_number = :batch_number")
                params["batch_number"] = item["batch_number"]
            
            if item.get("expiry_date"):
                update_fields.append("expiry_date = :expiry_date")
                params["expiry_date"] = item["expiry_date"]
            
            if item.get("manufacturing_date"):
                update_fields.append("manufacturing_date = :manufacturing_date")
                params["manufacturing_date"] = item["manufacturing_date"]
            
            # Update purchase item
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
        
        # Generate GRN number
        grn_number = f"GRN-{purchase.purchase_number}"
        
        # Update purchase status - this will trigger batch creation
        db.execute(
            text("""
                UPDATE purchases 
                SET purchase_status = 'received',
                    grn_number = :grn_number,
                    grn_date = CURRENT_DATE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE purchase_id = :purchase_id
            """),
            {
                "grn_number": grn_number,
                "purchase_id": purchase_id
            }
        )
        
        db.commit()
        
        # Count batches created by the trigger
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
            "note": "Batches auto-created by system trigger with auto-generated numbers if needed"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error receiving items: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to receive items: {str(e)}")