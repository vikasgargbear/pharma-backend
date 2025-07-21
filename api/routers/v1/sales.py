"""
Sales API Router
Handles direct sales/cash sales and invoice generation
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from datetime import datetime, date
from decimal import Decimal
import uuid
from pydantic import BaseModel, Field

from ...database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sales", tags=["sales"])

# Pydantic models for request/response
class SaleItemCreate(BaseModel):
    """Sale item for direct invoice creation"""
    product_id: int
    product_name: str
    hsn_code: Optional[str] = None
    batch_id: Optional[int] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[str] = None
    quantity: int = Field(..., gt=0)
    unit: str = "strip"
    unit_price: Decimal = Field(..., ge=0)  # This is what frontend is missing
    mrp: Decimal = Field(..., ge=0)
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    tax_percent: Decimal = Field(..., ge=0, le=28)  # This is what frontend is missing
    

class SaleCreate(BaseModel):
    """Create a direct sale/invoice"""
    sale_date: Optional[date] = None
    party_id: int
    party_name: str
    party_gst: Optional[str] = None
    party_address: Optional[str] = None
    party_phone: Optional[str] = None
    payment_mode: str = "cash"  # cash, credit, card, upi
    items: List[SaleItemCreate]
    discount_amount: Optional[Decimal] = Decimal("0")
    other_charges: Optional[Decimal] = Decimal("0")
    notes: Optional[str] = None
    

class SaleResponse(BaseModel):
    """Sale response with all details"""
    sale_id: str
    invoice_number: str
    sale_date: date
    party_id: int
    party_name: str
    subtotal_amount: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    payment_mode: str
    sale_status: str
    created_at: datetime


@router.post("/", response_model=SaleResponse)
async def create_direct_sale(
    sale_data: SaleCreate,
    db: Session = Depends(get_db)
):
    """
    Create a direct sale/cash sale with invoice
    """
    try:
        # Generate sale ID and invoice number
        sale_id = str(uuid.uuid4())
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Use provided date or current date
        sale_date = sale_data.sale_date or date.today()
        
        # Calculate totals
        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        
        for item in sale_data.items:
            item_total = item.quantity * item.unit_price
            item_discount = item_total * item.discount_percent / 100
            taxable_amount = item_total - item_discount
            item_tax = taxable_amount * item.tax_percent / 100
            
            subtotal += item_total
            tax_amount += item_tax
            
        # Apply overall discount
        total_after_tax = subtotal + tax_amount - sale_data.discount_amount
        final_total = total_after_tax + sale_data.other_charges
        
        # Create sale record
        db.execute(
            text("""
                INSERT INTO sales (
                    sale_id, org_id, invoice_number, sale_date,
                    party_id, party_name, party_gst, party_address,
                    party_phone, subtotal_amount, discount_amount,
                    tax_amount, other_charges, grand_total,
                    payment_mode, sale_status, notes
                ) VALUES (
                    :sale_id, :org_id, :invoice_number, :sale_date,
                    :party_id, :party_name, :party_gst, :party_address,
                    :party_phone, :subtotal, :discount, :tax,
                    :other_charges, :total, :payment_mode, :status, :notes
                )
            """),
            {
                "sale_id": sale_id,
                "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",
                "invoice_number": invoice_number,
                "sale_date": sale_date,
                "party_id": sale_data.party_id,
                "party_name": sale_data.party_name,
                "party_gst": sale_data.party_gst,
                "party_address": sale_data.party_address,
                "party_phone": sale_data.party_phone,
                "subtotal": subtotal,
                "discount": sale_data.discount_amount,
                "tax": tax_amount,
                "other_charges": sale_data.other_charges,
                "total": final_total,
                "payment_mode": sale_data.payment_mode,
                "status": "completed",
                "notes": sale_data.notes
            }
        )
        
        # Create sale items
        for item in sale_data.items:
            item_total = item.quantity * item.unit_price
            item_discount_amount = item_total * item.discount_percent / 100
            taxable_amount = item_total - item_discount_amount
            item_tax_amount = taxable_amount * item.tax_percent / 100
            total_amount = taxable_amount + item_tax_amount
            
            db.execute(
                text("""
                    INSERT INTO sale_items (
                        sale_item_id, sale_id, product_id, product_name,
                        hsn_code, batch_id, batch_number, expiry_date,
                        quantity, unit, unit_price, mrp,
                        discount_percent, discount_amount,
                        tax_percent, tax_amount, total_amount
                    ) VALUES (
                        :item_id, :sale_id, :product_id, :product_name,
                        :hsn, :batch_id, :batch_number, :expiry,
                        :quantity, :unit, :unit_price, :mrp,
                        :disc_percent, :disc_amount,
                        :tax_percent, :tax_amount, :total
                    )
                """),
                {
                    "item_id": str(uuid.uuid4()),
                    "sale_id": sale_id,
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "hsn": item.hsn_code,
                    "batch_id": item.batch_id,
                    "batch_number": item.batch_number,
                    "expiry": item.expiry_date,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "unit_price": item.unit_price,
                    "mrp": item.mrp,
                    "disc_percent": item.discount_percent,
                    "disc_amount": item_discount_amount,
                    "tax_percent": item.tax_percent,
                    "tax_amount": item_tax_amount,
                    "total": total_amount
                }
            )
            
            # Update inventory
            if item.batch_id:
                db.execute(
                    text("""
                        UPDATE inventory 
                        SET current_stock = current_stock - :quantity
                        WHERE batch_id = :batch_id
                    """),
                    {"quantity": item.quantity, "batch_id": item.batch_id}
                )
            else:
                # Deduct from any available batch
                db.execute(
                    text("""
                        UPDATE inventory 
                        SET current_stock = current_stock - :quantity
                        WHERE product_id = :product_id 
                        AND current_stock >= :quantity
                        AND org_id = :org_id
                        ORDER BY expiry_date ASC
                        LIMIT 1
                    """),
                    {
                        "quantity": item.quantity,
                        "product_id": item.product_id,
                        "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f"
                    }
                )
                
        # Create ledger entry if credit sale
        if sale_data.payment_mode == "credit":
            db.execute(
                text("""
                    INSERT INTO party_ledger (
                        ledger_id, org_id, party_id, transaction_date,
                        transaction_type, reference_type, reference_id,
                        debit_amount, credit_amount, description
                    ) VALUES (
                        :ledger_id, :org_id, :party_id, :date,
                        'debit', 'sale', :sale_id,
                        :amount, 0, :description
                    )
                """),
                {
                    "ledger_id": str(uuid.uuid4()),
                    "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",
                    "party_id": sale_data.party_id,
                    "date": sale_date,
                    "sale_id": sale_id,
                    "amount": final_total,
                    "description": f"Sale Invoice - {invoice_number}"
                }
            )
            
        db.commit()
        
        return SaleResponse(
            sale_id=sale_id,
            invoice_number=invoice_number,
            sale_date=sale_date,
            party_id=sale_data.party_id,
            party_name=sale_data.party_name,
            subtotal_amount=subtotal,
            discount_amount=sale_data.discount_amount,
            tax_amount=tax_amount,
            total_amount=final_total,
            payment_mode=sale_data.payment_mode,
            sale_status="completed",
            created_at=datetime.now()
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating sale: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    party_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    payment_mode: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of sales with optional filters
    """
    try:
        query = """
            SELECT s.*, p.party_name, p.gst_number as party_gst
            FROM sales s
            LEFT JOIN parties p ON s.party_id = p.party_id
            WHERE s.org_id = :org_id
        """
        params = {
            "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",
            "skip": skip,
            "limit": limit
        }
        
        if party_id:
            query += " AND s.party_id = :party_id"
            params["party_id"] = party_id
            
        if from_date:
            query += " AND s.sale_date >= :from_date"
            params["from_date"] = from_date
            
        if to_date:
            query += " AND s.sale_date <= :to_date"
            params["to_date"] = to_date
            
        if payment_mode:
            query += " AND s.payment_mode = :payment_mode"
            params["payment_mode"] = payment_mode
            
        query += " ORDER BY s.sale_date DESC, s.created_at DESC LIMIT :limit OFFSET :skip"
        
        sales = db.execute(text(query), params).fetchall()
        
        # Get count
        count_query = query.replace("SELECT s.*, p.party_name, p.gst_number as party_gst", "SELECT COUNT(*)")
        count_query = count_query.split("ORDER BY")[0]
        total = db.execute(text(count_query), params).scalar()
        
        return {
            "total": total,
            "sales": [dict(sale._mapping) for sale in sales]
        }
        
    except Exception as e:
        logger.error(f"Error fetching sales: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{sale_id}")
async def get_sale_detail(
    sale_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed sale information including items
    """
    try:
        # Get sale
        sale = db.execute(
            text("""
                SELECT s.*, p.party_name, p.gst_number as party_gst,
                       p.address as party_address, p.phone as party_phone
                FROM sales s
                LEFT JOIN parties p ON s.party_id = p.party_id
                WHERE s.sale_id = :sale_id
            """),
            {"sale_id": sale_id}
        ).first()
        
        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")
            
        # Get items
        items = db.execute(
            text("""
                SELECT si.*, p.product_name, p.hsn_code
                FROM sale_items si
                LEFT JOIN products p ON si.product_id = p.product_id
                WHERE si.sale_id = :sale_id
            """),
            {"sale_id": sale_id}
        ).fetchall()
        
        result = dict(sale._mapping)
        result["items"] = [dict(item._mapping) for item in items]
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sale detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoice/{invoice_number}")
async def get_sale_by_invoice(
    invoice_number: str,
    db: Session = Depends(get_db)
):
    """
    Get sale by invoice number
    """
    try:
        sale = db.execute(
            text("""
                SELECT s.*, p.party_name, p.gst_number as party_gst
                FROM sales s
                LEFT JOIN parties p ON s.party_id = p.party_id
                WHERE s.invoice_number = :invoice_number
            """),
            {"invoice_number": invoice_number}
        ).first()
        
        if not sale:
            raise HTTPException(status_code=404, detail="Invoice not found")
            
        return dict(sale._mapping)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{sale_id}/print")
async def get_sale_print_data(
    sale_id: str,
    db: Session = Depends(get_db)
):
    """
    Get sale data formatted for printing
    """
    try:
        # Get organization details
        org = db.execute(
            text("SELECT * FROM organizations WHERE organization_id = :org_id"),
            {"org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f"}
        ).first()
        
        # Get sale with all details
        sale_data = await get_sale_detail(sale_id, db)
        
        # Format for printing
        print_data = {
            "organization": dict(org._mapping) if org else {
                "organization_name": "AASO Pharma",
                "address": "123 Business Park",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400001",
                "gst_number": "27AABCU9603R1ZM",
                "drug_license": "MH-123456",
                "phone": "9876543210",
                "email": "info@aasopharma.com"
            },
            "invoice": sale_data,
            "print_date": datetime.now().isoformat()
        }
        
        return print_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting print data: {e}")
        raise HTTPException(status_code=500, detail=str(e))