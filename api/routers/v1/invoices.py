"""
Invoice endpoints for detailed invoice data retrieval
Optimized for frontend PDF generation
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from decimal import Decimal
from datetime import date
import logging

from ...database import get_db
from ...services.invoice_service import InvoiceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])

# Default organization ID (should come from auth in production)
DEFAULT_ORG_ID = "12de5e22-eee7-4d25-b3a7-d16d01c6170f"


class InvoiceDetailResponse(BaseModel):
    """Comprehensive invoice details for PDF generation"""
    # Invoice details
    invoice_id: int
    invoice_number: str
    invoice_date: date
    due_date: Optional[date]
    
    # Order details
    order_id: int
    order_number: str
    order_date: date
    
    # Organization details
    org_name: str = "AASO Pharma"
    org_address: str = "123 Business Park, Mumbai, Maharashtra - 400001"
    org_gstin: str = "27AABCU9603R1ZM"
    org_phone: str = "+91 98765 43210"
    org_email: str = "info@aasopharma.com"
    
    # Customer details
    customer_id: int
    customer_name: str
    customer_code: str
    customer_gstin: Optional[str]
    billing_address: str
    shipping_address: Optional[str]
    customer_phone: Optional[str]
    customer_email: Optional[str]
    
    # Financial details
    subtotal_amount: Decimal
    discount_amount: Decimal
    taxable_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    total_tax_amount: Decimal
    round_off_amount: Decimal
    total_amount: Decimal
    
    # Payment details
    payment_status: str
    paid_amount: Decimal
    balance_amount: Decimal
    
    # Items
    items: list
    
    # Additional info
    notes: Optional[str]
    terms_and_conditions: str = "1. Goods once sold will not be taken back\n2. Interest @ 18% p.a. will be charged on overdue payments\n3. Subject to Mumbai Jurisdiction"
    
    # Bank details for payment
    bank_details: dict = {
        "bank_name": "HDFC Bank",
        "account_name": "AASO Pharma Pvt Ltd",
        "account_number": "50200012345678",
        "ifsc_code": "HDFC0001234",
        "branch": "Andheri West, Mumbai"
    }


@router.get("/{invoice_id}/details", response_model=InvoiceDetailResponse)
async def get_invoice_details(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive invoice details for PDF generation
    
    Returns all data needed by frontend to generate invoice PDF including:
    - Complete invoice information
    - Customer details with formatted addresses
    - Itemized list with HSN codes
    - Tax breakup (CGST/SGST/IGST)
    - Payment status and history
    - Organization details
    """
    try:
        # Check if area column exists
        area_exists = db.execute(text("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'customers' 
                AND column_name = 'area'
            )
        """)).scalar()
        
        # Get invoice with all related data
        if area_exists:
            invoice_query = text("""
                SELECT 
                    i.*,
                    o.order_number, o.order_date, o.org_id,
                    c.customer_code, c.phone as customer_phone, c.email as customer_email,
                    c.address_line1, c.address_line2, c.area, c.city, c.state, c.pincode
                FROM invoices i
                JOIN orders o ON i.order_id = o.order_id
                JOIN customers c ON i.customer_id = c.customer_id
                WHERE i.invoice_id = :invoice_id
            """)
        else:
            invoice_query = text("""
                SELECT 
                    i.*,
                    o.order_number, o.order_date, o.org_id,
                    c.customer_code, c.phone as customer_phone, c.email as customer_email,
                    c.address_line1, c.address_line2, NULL as area, c.city, c.state, c.pincode
                FROM invoices i
                JOIN orders o ON i.order_id = o.order_id
                JOIN customers c ON i.customer_id = c.customer_id
                WHERE i.invoice_id = :invoice_id
            """)
        
        invoice = db.execute(invoice_query, {"invoice_id": invoice_id}).fetchone()
        
        if not invoice:
            raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} not found")
        
        # Get invoice items with product details
        items_query = text("""
            SELECT 
                ii.*,
                p.product_name, p.product_code, p.hsn_code,
                p.manufacturer, p.composition,
                b.batch_number, b.expiry_date
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.product_id
            LEFT JOIN order_items oi ON oi.product_id = ii.product_id 
                AND oi.order_id = :order_id
            LEFT JOIN batches b ON oi.batch_id = b.batch_id
            WHERE ii.invoice_id = :invoice_id
            ORDER BY ii.invoice_item_id
        """)
        
        items = db.execute(items_query, {
            "invoice_id": invoice_id,
            "order_id": invoice.order_id
        }).fetchall()
        
        # Format items for response
        formatted_items = []
        for idx, item in enumerate(items, 1):
            formatted_items.append({
                "sr_no": idx,
                "product_name": item.product_name,
                "product_code": item.product_code,
                "hsn_code": item.hsn_code or "3004",  # Default pharma HSN
                "batch_number": item.batch_number,
                "expiry_date": item.expiry_date,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "discount_percent": float(item.discount_percent or 0),
                "discount_amount": float(item.discount_amount or 0),
                "tax_percent": float(item.tax_percent or 0),
                "cgst_percent": float(item.tax_percent or 0) / 2 if invoice.cgst_amount > 0 else 0,
                "sgst_percent": float(item.tax_percent or 0) / 2 if invoice.sgst_amount > 0 else 0,
                "igst_percent": float(item.tax_percent or 0) if invoice.igst_amount > 0 else 0,
                "cgst_amount": float(item.cgst_amount or 0),
                "sgst_amount": float(item.sgst_amount or 0),
                "igst_amount": float(item.igst_amount or 0),
                "line_total": float(item.line_total),
                "manufacturer": item.manufacturer,
                "composition": item.composition
            })
        
        # Calculate balance
        balance_amount = invoice.total_amount - invoice.paid_amount
        
        # Format addresses
        billing_address = InvoiceService.format_address(invoice)
        shipping_address = invoice.shipping_address or billing_address
        
        # Prepare response
        response_data = {
            # Invoice details
            "invoice_id": invoice.invoice_id,
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date,
            "due_date": invoice.due_date,
            
            # Order details
            "order_id": invoice.order_id,
            "order_number": invoice.order_number,
            "order_date": invoice.order_date,
            
            # Customer details
            "customer_id": invoice.customer_id,
            "customer_name": invoice.customer_name,
            "customer_code": invoice.customer_code,
            "customer_gstin": invoice.customer_gstin,
            "billing_address": billing_address,
            "shipping_address": shipping_address,
            "customer_phone": invoice.customer_phone,
            "customer_email": invoice.customer_email,
            
            # Financial details
            "subtotal_amount": invoice.subtotal_amount,
            "discount_amount": invoice.discount_amount,
            "taxable_amount": invoice.taxable_amount,
            "cgst_amount": invoice.cgst_amount,
            "sgst_amount": invoice.sgst_amount,
            "igst_amount": invoice.igst_amount,
            "total_tax_amount": invoice.total_tax_amount,
            "round_off_amount": invoice.round_off_amount,
            "total_amount": invoice.total_amount,
            
            # Payment details
            "payment_status": invoice.payment_status,
            "paid_amount": invoice.paid_amount,
            "balance_amount": balance_amount,
            
            # Items
            "items": formatted_items,
            
            # Additional info
            "notes": invoice.notes
        }
        
        return InvoiceDetailResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting invoice details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get invoice details: {str(e)}")


@router.get("/list")
async def list_invoices(
    customer_id: Optional[int] = None,
    payment_status: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List invoices with filters
    
    - Filter by customer, payment status, date range
    - Includes customer name and order details
    - Pagination support
    """
    try:
        # Build query
        query = """
            SELECT 
                i.invoice_id, i.invoice_number, i.invoice_date, i.due_date,
                i.total_amount, i.paid_amount, i.payment_status,
                c.customer_id, c.customer_name, c.customer_code,
                o.order_number, o.order_date,
                (i.total_amount - i.paid_amount) as balance_amount
            FROM invoices i
            JOIN orders o ON i.order_id = o.order_id
            JOIN customers c ON i.customer_id = c.customer_id
            WHERE o.org_id = :org_id
        """
        
        params = {"org_id": DEFAULT_ORG_ID}
        
        # Add filters
        if customer_id:
            query += " AND i.customer_id = :customer_id"
            params["customer_id"] = customer_id
        
        if payment_status:
            query += " AND i.payment_status = :payment_status"
            params["payment_status"] = payment_status
        
        if from_date:
            query += " AND i.invoice_date >= :from_date"
            params["from_date"] = from_date
        
        if to_date:
            query += " AND i.invoice_date <= :to_date"
            params["to_date"] = to_date
        
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query}) as cnt"
        total = db.execute(text(count_query), params).scalar()
        
        # Add ordering and pagination
        query += " ORDER BY i.invoice_date DESC, i.invoice_id DESC"
        query += " LIMIT :limit OFFSET :skip"
        params.update({"limit": limit, "skip": skip})
        
        # Execute query
        result = db.execute(text(query), params)
        invoices = [dict(row._mapping) for row in result]
        
        return {
            "total": total,
            "page": skip // limit + 1,
            "per_page": limit,
            "invoices": invoices
        }
        
    except Exception as e:
        logger.error(f"Error listing invoices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list invoices")


@router.put("/{invoice_id}/update-pdf")
async def update_invoice_pdf_status(
    invoice_id: int,
    pdf_url: str,
    db: Session = Depends(get_db)
):
    """
    Update invoice with PDF URL after frontend generates it
    
    Call this after successfully generating PDF in frontend
    """
    try:
        db.execute(text("""
            UPDATE invoices
            SET pdf_url = :pdf_url,
                pdf_generated_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE invoice_id = :invoice_id
        """), {"invoice_id": invoice_id, "pdf_url": pdf_url})
        
        db.commit()
        
        return {"message": "PDF URL updated successfully", "invoice_id": invoice_id}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating PDF URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update PDF URL")