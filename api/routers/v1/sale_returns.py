"""
Sale Return API Router
Handles returns of sold items with inventory and ledger adjustments
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

router = APIRouter(prefix="/api/v1/sale-returns", tags=["sale-returns"])

@router.get("/")
async def get_sale_returns(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    party_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of sale returns with optional filters
    """
    try:
        query = """
            SELECT sr.*, p.party_name, s.invoice_number as original_invoice_number
            FROM sale_returns sr
            LEFT JOIN parties p ON sr.party_id = p.party_id
            LEFT JOIN sales s ON sr.original_sale_id = s.sale_id
            WHERE 1=1
        """
        params = {"skip": skip, "limit": limit}
        
        if party_id:
            query += " AND sr.party_id = :party_id"
            params["party_id"] = party_id
            
        if from_date:
            query += " AND sr.return_date >= :from_date"
            params["from_date"] = from_date
            
        if to_date:
            query += " AND sr.return_date <= :to_date"
            params["to_date"] = to_date
            
        query += " ORDER BY sr.return_date DESC, sr.created_at DESC LIMIT :limit OFFSET :skip"
        
        returns = db.execute(text(query), params).fetchall()
        
        # Get items for each return
        result = []
        for ret in returns:
            items_query = """
                SELECT sri.*, p.product_name, p.hsn_code
                FROM sale_return_items sri
                LEFT JOIN products p ON sri.product_id = p.product_id
                WHERE sri.return_id = :return_id
            """
            items = db.execute(text(items_query), {"return_id": ret.return_id}).fetchall()
            
            return_dict = dict(ret._mapping)
            return_dict["items"] = [dict(item._mapping) for item in items]
            result.append(return_dict)
            
        # Get total count
        count_query = """
            SELECT COUNT(*) FROM sale_returns sr WHERE 1=1
        """
        if party_id:
            count_query += " AND sr.party_id = :party_id"
        if from_date:
            count_query += " AND sr.return_date >= :from_date"
        if to_date:
            count_query += " AND sr.return_date <= :to_date"
            
        total = db.execute(text(count_query), params).scalar()
        
        return {
            "total": total,
            "returns": result
        }
        
    except Exception as e:
        logger.error(f"Error fetching sale returns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/returnable-invoices")
async def get_returnable_invoices(
    party_id: Optional[str] = None,
    invoice_number: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get sales invoices that can be returned
    """
    try:
        query = """
            SELECT 
                s.sale_id,
                s.invoice_number,
                s.sale_date,
                s.party_id,
                p.party_name,
                s.grand_total,
                COUNT(si.sale_item_id) as total_items
            FROM sales s
            LEFT JOIN parties p ON s.party_id = p.party_id
            LEFT JOIN sale_items si ON s.sale_id = si.sale_id
            WHERE s.sale_status = 'completed'
        """
        params = {}
        
        if party_id:
            query += " AND s.party_id = :party_id"
            params["party_id"] = party_id
            
        if invoice_number:
            query += " AND s.invoice_number LIKE :invoice_number"
            params["invoice_number"] = f"%{invoice_number}%"
            
        query += """ 
            GROUP BY s.sale_id, s.invoice_number, s.sale_date, 
                     s.party_id, p.party_name, s.grand_total
            ORDER BY s.sale_date DESC
            LIMIT 50
        """
        
        invoices = db.execute(text(query), params).fetchall()
        
        result = []
        for inv in invoices:
            # Check how much has already been returned
            returned_query = """
                SELECT COALESCE(SUM(sri.quantity), 0) as total_returned
                FROM sale_returns sr
                JOIN sale_return_items sri ON sr.return_id = sri.return_id
                WHERE sr.original_sale_id = :sale_id
            """
            total_returned = db.execute(
                text(returned_query), 
                {"sale_id": inv.sale_id}
            ).scalar()
            
            invoice_dict = dict(inv._mapping)
            invoice_dict["has_returns"] = total_returned > 0
            invoice_dict["can_return"] = True  # Can be refined based on business rules
            result.append(invoice_dict)
            
        return {"invoices": result}
        
    except Exception as e:
        logger.error(f"Error fetching returnable invoices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/invoice/{sale_id}/items")
async def get_invoice_items_for_return(
    sale_id: str,
    db: Session = Depends(get_db)
):
    """
    Get items from a specific invoice for return
    """
    try:
        # Get sale details
        sale = db.execute(
            text("SELECT * FROM sales WHERE sale_id = :sale_id"),
            {"sale_id": sale_id}
        ).first()
        
        if not sale:
            raise HTTPException(status_code=404, detail="Invoice not found")
            
        # Get items with return info
        items_query = """
            SELECT 
                si.*,
                p.product_name,
                p.hsn_code,
                COALESCE(SUM(sri.quantity), 0) as returned_quantity
            FROM sale_items si
            LEFT JOIN products p ON si.product_id = p.product_id
            LEFT JOIN sale_return_items sri ON (
                sri.original_sale_item_id = si.sale_item_id
            )
            WHERE si.sale_id = :sale_id
            GROUP BY si.sale_item_id, p.product_name, p.hsn_code
        """
        
        items = db.execute(text(items_query), {"sale_id": sale_id}).fetchall()
        
        result_items = []
        for item in items:
            item_dict = dict(item._mapping)
            item_dict["returnable_quantity"] = item.quantity - item.returned_quantity
            item_dict["can_return"] = item_dict["returnable_quantity"] > 0
            result_items.append(item_dict)
            
        return {
            "sale": dict(sale._mapping),
            "items": result_items
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching invoice items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_sale_return(
    return_data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a new sale return
    """
    try:
        # Validate required fields
        required_fields = ["original_sale_id", "party_id", "return_date", "items"]
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
            
        # Generate return number
        return_number = f"SR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
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
                INSERT INTO sale_returns (
                    return_id, org_id, return_number, return_date,
                    original_sale_id, party_id, reason,
                    subtotal_amount, tax_amount, total_amount,
                    payment_mode, return_status
                ) VALUES (
                    :return_id, :org_id, :return_number, :return_date,
                    :original_sale_id, :party_id, :reason,
                    :subtotal, :tax_amount, :total_amount,
                    :payment_mode, 'completed'
                )
            """),
            {
                "return_id": return_id,
                "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",  # Default org
                "return_number": return_number,
                "return_date": return_data["return_date"],
                "original_sale_id": return_data["original_sale_id"],
                "party_id": return_data["party_id"],
                "reason": return_data.get("reason", ""),
                "subtotal": subtotal,
                "tax_amount": tax_amount,
                "total_amount": total_amount,
                "payment_mode": return_data.get("payment_mode", "credit")
            }
        )
        
        # Create return items and update inventory
        for item in return_data["items"]:
            # Insert return item
            db.execute(
                text("""
                    INSERT INTO sale_return_items (
                        return_item_id, return_id, product_id,
                        original_sale_item_id, quantity, rate,
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
                    "original_item_id": item.get("original_sale_item_id"),
                    "quantity": item["quantity"],
                    "rate": Decimal(str(item["rate"])),
                    "tax_percent": Decimal(str(item.get("tax_percent", 0))),
                    "tax_amount": Decimal(str(item.get("tax_amount", 0))),
                    "total": Decimal(str(item.get("total_amount", 0)))
                }
            )
            
            # Update inventory (increase stock)
            if item.get("batch_id"):
                db.execute(
                    text("""
                        UPDATE inventory 
                        SET current_stock = current_stock + :quantity
                        WHERE batch_id = :batch_id
                    """),
                    {
                        "quantity": item["quantity"],
                        "batch_id": item["batch_id"]
                    }
                )
            else:
                # Find or create inventory entry
                db.execute(
                    text("""
                        INSERT INTO inventory (
                            inventory_id, org_id, product_id,
                            batch_number, current_stock
                        ) VALUES (
                            :inv_id, :org_id, :product_id,
                            :batch, :stock
                        )
                        ON CONFLICT (org_id, product_id, batch_number) 
                        DO UPDATE SET current_stock = inventory.current_stock + :stock
                    """),
                    {
                        "inv_id": str(uuid.uuid4()),
                        "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",
                        "product_id": item["product_id"],
                        "batch": item.get("batch_number", "DEFAULT"),
                        "stock": item["quantity"]
                    }
                )
                
        # Update party ledger
        if return_data.get("payment_mode") == "credit":
            # Create credit entry in ledger
            db.execute(
                text("""
                    INSERT INTO party_ledger (
                        ledger_id, org_id, party_id, transaction_date,
                        transaction_type, reference_type, reference_id,
                        debit_amount, credit_amount, description
                    ) VALUES (
                        :ledger_id, :org_id, :party_id, :date,
                        'credit', 'sale_return', :return_id,
                        0, :amount, :description
                    )
                """),
                {
                    "ledger_id": str(uuid.uuid4()),
                    "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",
                    "party_id": return_data["party_id"],
                    "date": return_data["return_date"],
                    "return_id": return_id,
                    "amount": total_amount,
                    "description": f"Sale Return - {return_number}"
                }
            )
            
        db.commit()
        
        return {
            "status": "success",
            "return_id": return_id,
            "return_number": return_number,
            "message": f"Sale return {return_number} created successfully"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating sale return: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{return_id}")
async def get_sale_return_detail(
    return_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific sale return
    """
    try:
        # Get return details
        return_query = """
            SELECT sr.*, p.party_name, p.gst_number as party_gst,
                   s.invoice_number as original_invoice_number
            FROM sale_returns sr
            LEFT JOIN parties p ON sr.party_id = p.party_id
            LEFT JOIN sales s ON sr.original_sale_id = s.sale_id
            WHERE sr.return_id = :return_id
        """
        
        sale_return = db.execute(
            text(return_query), 
            {"return_id": return_id}
        ).first()
        
        if not sale_return:
            raise HTTPException(status_code=404, detail="Sale return not found")
            
        # Get return items
        items_query = """
            SELECT sri.*, p.product_name, p.hsn_code,
                   si.batch_number, si.expiry_date
            FROM sale_return_items sri
            LEFT JOIN products p ON sri.product_id = p.product_id
            LEFT JOIN sale_items si ON sri.original_sale_item_id = si.sale_item_id
            WHERE sri.return_id = :return_id
        """
        
        items = db.execute(
            text(items_query), 
            {"return_id": return_id}
        ).fetchall()
        
        result = dict(sale_return._mapping)
        result["items"] = [dict(item._mapping) for item in items]
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sale return detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{return_id}")
async def cancel_sale_return(
    return_id: str,
    db: Session = Depends(get_db)
):
    """
    Cancel a sale return (if allowed by business rules)
    """
    try:
        # Check if return exists
        sale_return = db.execute(
            text("SELECT * FROM sale_returns WHERE return_id = :return_id"),
            {"return_id": return_id}
        ).first()
        
        if not sale_return:
            raise HTTPException(status_code=404, detail="Sale return not found")
            
        if sale_return.return_status == "cancelled":
            raise HTTPException(status_code=400, detail="Return already cancelled")
            
        # Get return items to reverse inventory
        items = db.execute(
            text("SELECT * FROM sale_return_items WHERE return_id = :return_id"),
            {"return_id": return_id}
        ).fetchall()
        
        # Reverse inventory changes
        for item in items:
            db.execute(
                text("""
                    UPDATE inventory 
                    SET current_stock = current_stock - :quantity
                    WHERE product_id = :product_id
                """),
                {
                    "quantity": item.quantity,
                    "product_id": item.product_id
                }
            )
            
        # Reverse ledger entry if credit return
        if sale_return.payment_mode == "credit":
            db.execute(
                text("""
                    DELETE FROM party_ledger 
                    WHERE reference_type = 'sale_return' 
                    AND reference_id = :return_id
                """),
                {"return_id": return_id}
            )
            
        # Update return status
        db.execute(
            text("""
                UPDATE sale_returns 
                SET return_status = 'cancelled',
                    updated_at = CURRENT_TIMESTAMP
                WHERE return_id = :return_id
            """),
            {"return_id": return_id}
        )
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Sale return {sale_return.return_number} cancelled successfully"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling sale return: {e}")
        raise HTTPException(status_code=500, detail=str(e))