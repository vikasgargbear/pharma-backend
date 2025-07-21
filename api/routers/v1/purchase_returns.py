"""
Purchase Return API Router
Handles returns of purchased items back to suppliers
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from datetime import datetime
from decimal import Decimal
import uuid

from ...database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/purchase-returns", tags=["purchase-returns"])

@router.get("/")
async def get_purchase_returns(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    supplier_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of purchase returns with optional filters
    """
    try:
        query = """
            SELECT pr.*, s.supplier_name, p.supplier_invoice_number as original_invoice
            FROM purchase_returns pr
            LEFT JOIN suppliers s ON pr.supplier_id = s.supplier_id
            LEFT JOIN purchases p ON pr.original_purchase_id = p.purchase_id
            WHERE 1=1
        """
        params = {"skip": skip, "limit": limit}
        
        if supplier_id:
            query += " AND pr.supplier_id = :supplier_id"
            params["supplier_id"] = supplier_id
            
        if from_date:
            query += " AND pr.return_date >= :from_date"
            params["from_date"] = from_date
            
        if to_date:
            query += " AND pr.return_date <= :to_date"
            params["to_date"] = to_date
            
        query += " ORDER BY pr.return_date DESC, pr.created_at DESC LIMIT :limit OFFSET :skip"
        
        returns = db.execute(text(query), params).fetchall()
        
        # Get items for each return
        result = []
        for ret in returns:
            items_query = """
                SELECT pri.*, p.product_name, p.hsn_code
                FROM purchase_return_items pri
                LEFT JOIN products p ON pri.product_id = p.product_id
                WHERE pri.return_id = :return_id
            """
            items = db.execute(text(items_query), {"return_id": ret.return_id}).fetchall()
            
            return_dict = dict(ret._mapping)
            return_dict["items"] = [dict(item._mapping) for item in items]
            result.append(return_dict)
            
        # Get total count
        count_query = """
            SELECT COUNT(*) FROM purchase_returns pr WHERE 1=1
        """
        if supplier_id:
            count_query += " AND pr.supplier_id = :supplier_id"
        if from_date:
            count_query += " AND pr.return_date >= :from_date"
        if to_date:
            count_query += " AND pr.return_date <= :to_date"
            
        total = db.execute(text(count_query), params).scalar()
        
        return {
            "total": total,
            "returns": result
        }
        
    except Exception as e:
        logger.error(f"Error fetching purchase returns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/returnable-purchases")
async def get_returnable_purchases(
    supplier_id: Optional[str] = None,
    invoice_number: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get purchase bills that can be returned
    """
    try:
        query = """
            SELECT 
                p.purchase_id,
                p.purchase_number,
                p.supplier_invoice_number,
                p.purchase_date,
                p.supplier_invoice_date,
                p.supplier_id,
                s.supplier_name,
                p.final_amount,
                COUNT(pi.purchase_item_id) as total_items
            FROM purchases p
            LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
            LEFT JOIN purchase_items pi ON p.purchase_id = pi.purchase_id
            WHERE p.purchase_status IN ('received', 'completed')
        """
        params = {}
        
        if supplier_id:
            query += " AND p.supplier_id = :supplier_id"
            params["supplier_id"] = supplier_id
            
        if invoice_number:
            query += " AND (p.supplier_invoice_number LIKE :invoice OR p.purchase_number LIKE :invoice)"
            params["invoice"] = f"%{invoice_number}%"
            
        query += """ 
            GROUP BY p.purchase_id, p.purchase_number, p.supplier_invoice_number,
                     p.purchase_date, p.supplier_invoice_date, p.supplier_id, 
                     s.supplier_name, p.final_amount
            ORDER BY p.purchase_date DESC
            LIMIT 50
        """
        
        purchases = db.execute(text(query), params).fetchall()
        
        result = []
        for purchase in purchases:
            # Check how much has already been returned
            returned_query = """
                SELECT COALESCE(SUM(pri.quantity), 0) as total_returned
                FROM purchase_returns pr
                JOIN purchase_return_items pri ON pr.return_id = pri.return_id
                WHERE pr.original_purchase_id = :purchase_id
            """
            total_returned = db.execute(
                text(returned_query), 
                {"purchase_id": purchase.purchase_id}
            ).scalar()
            
            purchase_dict = dict(purchase._mapping)
            purchase_dict["has_returns"] = total_returned > 0
            purchase_dict["can_return"] = True
            result.append(purchase_dict)
            
        return {"purchases": result}
        
    except Exception as e:
        logger.error(f"Error fetching returnable purchases: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/purchase/{purchase_id}/items")
async def get_purchase_items_for_return(
    purchase_id: str,
    db: Session = Depends(get_db)
):
    """
    Get items from a specific purchase for return
    """
    try:
        # Get purchase details
        purchase = db.execute(
            text("SELECT * FROM purchases WHERE purchase_id = :purchase_id"),
            {"purchase_id": purchase_id}
        ).first()
        
        if not purchase:
            raise HTTPException(status_code=404, detail="Purchase not found")
            
        # Get items with return info
        items_query = """
            SELECT 
                pi.*,
                p.product_name,
                p.hsn_code,
                COALESCE(SUM(pri.quantity), 0) as returned_quantity
            FROM purchase_items pi
            LEFT JOIN products p ON pi.product_id = p.product_id
            LEFT JOIN purchase_return_items pri ON (
                pri.original_purchase_item_id = pi.purchase_item_id
            )
            WHERE pi.purchase_id = :purchase_id
            GROUP BY pi.purchase_item_id, p.product_name, p.hsn_code
        """
        
        items = db.execute(text(items_query), {"purchase_id": purchase_id}).fetchall()
        
        result_items = []
        for item in items:
            item_dict = dict(item._mapping)
            # Use received_quantity if available, otherwise ordered_quantity
            actual_qty = item.received_quantity if item.received_quantity else item.ordered_quantity
            item_dict["returnable_quantity"] = actual_qty - item.returned_quantity
            item_dict["can_return"] = item_dict["returnable_quantity"] > 0
            result_items.append(item_dict)
            
        return {
            "purchase": dict(purchase._mapping),
            "items": result_items
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching purchase items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_purchase_return(
    return_data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a new purchase return (debit note)
    """
    try:
        # Validate required fields
        required_fields = ["original_purchase_id", "supplier_id", "return_date", "items"]
        for field in required_fields:
            if field not in return_data:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing required field: {field}"
                )
                
        if not return_data["items"]:
            raise HTTPException(
                status_code=400,
                detail="At least one item must be returned"
            )
            
        # Generate return/debit note number
        return_number = f"PR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        debit_note_number = return_data.get("debit_note_number", f"DN-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        return_id = str(uuid.uuid4())
        
        # Calculate totals
        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        total_amount = Decimal("0")
        
        for item in return_data["items"]:
            item_total = Decimal(str(item["quantity"])) * Decimal(str(item["rate"]))
            item_tax = item_total * Decimal(str(item.get("tax_percent", 0))) / 100
            
            subtotal += item_total
            tax_amount += item_tax
            total_amount += item_total + item_tax
            
        # Create return record
        db.execute(
            text("""
                INSERT INTO purchase_returns (
                    return_id, org_id, return_number, debit_note_number,
                    return_date, original_purchase_id, supplier_id, 
                    reason, subtotal_amount, tax_amount, total_amount,
                    return_status
                ) VALUES (
                    :return_id, :org_id, :return_number, :debit_note_number,
                    :return_date, :original_purchase_id, :supplier_id,
                    :reason, :subtotal, :tax_amount, :total_amount,
                    'completed'
                )
            """),
            {
                "return_id": return_id,
                "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",  # Default org
                "return_number": return_number,
                "debit_note_number": debit_note_number,
                "return_date": return_data["return_date"],
                "original_purchase_id": return_data["original_purchase_id"],
                "supplier_id": return_data["supplier_id"],
                "reason": return_data.get("reason", ""),
                "subtotal": subtotal,
                "tax_amount": tax_amount,
                "total_amount": total_amount
            }
        )
        
        # Create return items and update inventory
        for item in return_data["items"]:
            # Insert return item
            db.execute(
                text("""
                    INSERT INTO purchase_return_items (
                        return_item_id, return_id, product_id,
                        original_purchase_item_id, quantity, rate,
                        tax_percent, tax_amount, total_amount
                    ) VALUES (
                        :item_id, :return_id, :product_id,
                        :original_item_id, :quantity, :rate,
                        :tax_percent, :tax_amount, :total
                    )
                """),
                {
                    "item_id": str(uuid.uuid4()),
                    "return_id": return_id,
                    "product_id": item["product_id"],
                    "original_item_id": item.get("original_purchase_item_id"),
                    "quantity": item["quantity"],
                    "rate": Decimal(str(item["rate"])),
                    "tax_percent": Decimal(str(item.get("tax_percent", 0))),
                    "tax_amount": Decimal(str(item.get("tax_amount", 0))),
                    "total": Decimal(str(item.get("total_amount", 0)))
                }
            )
            
            # Update inventory (decrease stock)
            if item.get("batch_number"):
                db.execute(
                    text("""
                        UPDATE inventory 
                        SET current_stock = current_stock - :quantity
                        WHERE org_id = :org_id 
                        AND product_id = :product_id 
                        AND batch_number = :batch
                    """),
                    {
                        "quantity": item["quantity"],
                        "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",
                        "product_id": item["product_id"],
                        "batch": item["batch_number"]
                    }
                )
                
        # Update supplier ledger (debit entry)
        db.execute(
            text("""
                INSERT INTO supplier_ledger (
                    ledger_id, org_id, supplier_id, transaction_date,
                    transaction_type, reference_type, reference_id,
                    debit_amount, credit_amount, description
                ) VALUES (
                    :ledger_id, :org_id, :supplier_id, :date,
                    'debit', 'purchase_return', :return_id,
                    :amount, 0, :description
                )
            """),
            {
                "ledger_id": str(uuid.uuid4()),
                "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",
                "supplier_id": return_data["supplier_id"],
                "date": return_data["return_date"],
                "return_id": return_id,
                "amount": total_amount,
                "description": f"Purchase Return - {debit_note_number}"
            }
        )
        
        db.commit()
        
        return {
            "status": "success",
            "return_id": return_id,
            "return_number": return_number,
            "debit_note_number": debit_note_number,
            "message": f"Purchase return {return_number} created successfully"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating purchase return: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{return_id}")
async def get_purchase_return_detail(
    return_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific purchase return
    """
    try:
        # Get return details
        return_query = """
            SELECT pr.*, s.supplier_name, s.gst_number as supplier_gst,
                   p.supplier_invoice_number as original_invoice
            FROM purchase_returns pr
            LEFT JOIN suppliers s ON pr.supplier_id = s.supplier_id
            LEFT JOIN purchases p ON pr.original_purchase_id = p.purchase_id
            WHERE pr.return_id = :return_id
        """
        
        purchase_return = db.execute(
            text(return_query), 
            {"return_id": return_id}
        ).first()
        
        if not purchase_return:
            raise HTTPException(status_code=404, detail="Purchase return not found")
            
        # Get return items
        items_query = """
            SELECT pri.*, p.product_name, p.hsn_code,
                   pi.batch_number, pi.expiry_date
            FROM purchase_return_items pri
            LEFT JOIN products p ON pri.product_id = p.product_id
            LEFT JOIN purchase_items pi ON pri.original_purchase_item_id = pi.purchase_item_id
            WHERE pri.return_id = :return_id
        """
        
        items = db.execute(
            text(items_query), 
            {"return_id": return_id}
        ).fetchall()
        
        result = dict(purchase_return._mapping)
        result["items"] = [dict(item._mapping) for item in items]
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching purchase return detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{return_id}/print")
async def get_purchase_return_print_data(
    return_id: str,
    db: Session = Depends(get_db)
):
    """
    Get purchase return data formatted for printing debit note
    """
    try:
        # Get organization details
        org_query = """
            SELECT * FROM organizations 
            WHERE organization_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f'
        """
        organization = db.execute(text(org_query)).first()
        
        # Get return with all details
        return_data = await get_purchase_return_detail(return_id, db)
        
        # Format for printing
        print_data = {
            "organization": dict(organization._mapping) if organization else {},
            "return": return_data,
            "print_date": datetime.now().isoformat(),
            "document_type": "DEBIT NOTE"
        }
        
        return print_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting print data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{return_id}")
async def cancel_purchase_return(
    return_id: str,
    db: Session = Depends(get_db)
):
    """
    Cancel a purchase return
    """
    try:
        # Check if return exists
        purchase_return = db.execute(
            text("SELECT * FROM purchase_returns WHERE return_id = :return_id"),
            {"return_id": return_id}
        ).first()
        
        if not purchase_return:
            raise HTTPException(status_code=404, detail="Purchase return not found")
            
        if purchase_return.return_status == "cancelled":
            raise HTTPException(status_code=400, detail="Return already cancelled")
            
        # Get return items to reverse inventory
        items = db.execute(
            text("""
                SELECT pri.*, pi.batch_number 
                FROM purchase_return_items pri
                LEFT JOIN purchase_items pi ON pri.original_purchase_item_id = pi.purchase_item_id
                WHERE pri.return_id = :return_id
            """),
            {"return_id": return_id}
        ).fetchall()
        
        # Reverse inventory changes
        for item in items:
            db.execute(
                text("""
                    UPDATE inventory 
                    SET current_stock = current_stock + :quantity
                    WHERE org_id = :org_id 
                    AND product_id = :product_id
                    AND batch_number = :batch
                """),
                {
                    "quantity": item.quantity,
                    "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",
                    "product_id": item.product_id,
                    "batch": item.batch_number or "DEFAULT"
                }
            )
            
        # Reverse ledger entry
        db.execute(
            text("""
                DELETE FROM supplier_ledger 
                WHERE reference_type = 'purchase_return' 
                AND reference_id = :return_id
            """),
            {"return_id": return_id}
        )
        
        # Update return status
        db.execute(
            text("""
                UPDATE purchase_returns 
                SET return_status = 'cancelled',
                    updated_at = CURRENT_TIMESTAMP
                WHERE return_id = :return_id
            """),
            {"return_id": return_id}
        )
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Purchase return {purchase_return.return_number} cancelled successfully"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling purchase return: {e}")
        raise HTTPException(status_code=500, detail=str(e))