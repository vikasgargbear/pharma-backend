"""
Quick Sale API - The simplest way to create a sale
One endpoint, no complexity, just works
"""

from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
import uuid

from ...database import get_db
from ...core.auth import get_current_org

router = APIRouter(
    prefix="/api/v1/quick-sale",
    tags=["quick-sale"]
)

class QuickSaleItem(BaseModel):
    """Minimal item info for quick sale"""
    product_id: int
    quantity: int = Field(gt=0)
    # Optional - will use product's MRP if not provided
    unit_price: Optional[Decimal] = None
    discount_percent: Optional[Decimal] = 0

class QuickSaleRequest(BaseModel):
    """Minimal info needed for a complete sale"""
    customer_id: int
    items: List[QuickSaleItem]
    # Optional fields with smart defaults
    payment_mode: Optional[str] = "Cash"
    payment_amount: Optional[Decimal] = None  # If None, assumes full payment
    discount_amount: Optional[Decimal] = 0
    notes: Optional[str] = None

class QuickSaleResponse(BaseModel):
    """Everything you need after a sale"""
    success: bool
    invoice_number: str
    total_amount: Decimal
    # IDs are included but frontend doesn't need to use them
    order_id: int
    invoice_id: int
    # Ready-to-print invoice URL (if implemented)
    invoice_url: Optional[str] = None
    message: str

@router.post("/", response_model=QuickSaleResponse)
async def create_quick_sale(
    sale: QuickSaleRequest,
    db: Session = Depends(get_db),
    current_org = Depends(get_current_org)
):
    """
    The simplest way to create a sale - just send customer and items!
    
    This endpoint:
    1. Creates order (automatically)
    2. Validates inventory
    3. Calculates prices and taxes
    4. Creates invoice
    5. Records payment
    6. Updates inventory
    
    All in one atomic transaction!
    """
    org_id = current_org["org_id"]
    
    try:
        # Start transaction
        print(f"🚀 Quick sale for customer {sale.customer_id}")
        
        # Step 1: Validate customer
        customer = db.execute(text("""
            SELECT customer_id, customer_name, gstin, state_code, credit_days
            FROM customers
            WHERE customer_id = :customer_id AND org_id = :org_id
        """), {
            "customer_id": sale.customer_id,
            "org_id": org_id
        }).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Step 2: Create order (behind the scenes)
        order_result = db.execute(text("""
            INSERT INTO orders (
                org_id, customer_id, order_type, order_status,
                order_date, delivery_date,
                subtotal, discount_amount, final_amount,
                paid_amount, payment_mode,
                notes, created_at, updated_at
            ) VALUES (
                :org_id, :customer_id, 'sales_order', 'confirmed',
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                0, :discount_amount, 0,
                0, :payment_mode,
                :notes, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            ) RETURNING order_id
        """), {
            "org_id": org_id,
            "customer_id": sale.customer_id,
            "discount_amount": float(sale.discount_amount or 0),
            "payment_mode": sale.payment_mode,
            "notes": sale.notes
        })
        
        order_id = order_result.scalar()
        print(f"✅ Created order {order_id}")
        
        # Step 3: Process items and calculate totals
        subtotal = Decimal("0")
        total_tax = Decimal("0")
        
        for item in sale.items:
            # Get product details
            product = db.execute(text("""
                SELECT product_id, product_name, mrp, sale_price, 
                       gst_percent, hsn_code
                FROM products
                WHERE product_id = :product_id
            """), {"product_id": item.product_id}).first()
            
            if not product:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Product {item.product_id} not found"
                )
            
            # Use provided price or product's price
            unit_price = item.unit_price or product.sale_price or product.mrp
            
            # Check inventory
            available_stock = db.execute(text("""
                SELECT COALESCE(SUM(quantity_available), 0) as stock
                FROM batches
                WHERE product_id = :product_id 
                    AND org_id = :org_id
                    AND (expiry_date IS NULL OR expiry_date > CURRENT_DATE)
            """), {
                "product_id": item.product_id,
                "org_id": org_id
            }).scalar() or 0
            
            if available_stock < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for {product.product_name}. Available: {available_stock}"
                )
            
            # Calculate item totals
            line_total = item.quantity * unit_price
            discount_amount = line_total * (item.discount_percent or 0) / 100
            taxable_amount = line_total - discount_amount
            gst_percent = product.gst_percent or Decimal("12")
            tax_amount = taxable_amount * gst_percent / 100
            item_total = taxable_amount + tax_amount
            
            subtotal += line_total
            total_tax += tax_amount
            
            # Insert order item
            db.execute(text("""
                INSERT INTO order_items (
                    order_id, product_id, quantity, unit_price,
                    discount_percent, discount_amount,
                    taxable_amount, tax_percent, tax_amount,
                    total_amount
                ) VALUES (
                    :order_id, :product_id, :quantity, :unit_price,
                    :discount_percent, :discount_amount,
                    :taxable_amount, :tax_percent, :tax_amount,
                    :total_amount
                )
            """), {
                "order_id": order_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": float(unit_price),
                "discount_percent": float(item.discount_percent or 0),
                "discount_amount": float(discount_amount),
                "taxable_amount": float(taxable_amount),
                "tax_percent": float(gst_percent),
                "tax_amount": float(tax_amount),
                "total_amount": float(item_total)
            })
            
            # Update inventory (FIFO)
            remaining_qty = item.quantity
            batches = db.execute(text("""
                SELECT batch_id, quantity_available
                FROM batches
                WHERE product_id = :product_id 
                    AND org_id = :org_id
                    AND quantity_available > 0
                    AND (expiry_date IS NULL OR expiry_date > CURRENT_DATE)
                ORDER BY expiry_date ASC, batch_id ASC
                FOR UPDATE
            """), {
                "product_id": item.product_id,
                "org_id": org_id
            }).fetchall()
            
            for batch in batches:
                if remaining_qty <= 0:
                    break
                    
                qty_from_batch = min(remaining_qty, batch.quantity_available)
                
                db.execute(text("""
                    UPDATE batches
                    SET quantity_available = quantity_available - :qty,
                        quantity_sold = quantity_sold + :qty,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE batch_id = :batch_id
                """), {
                    "qty": qty_from_batch,
                    "batch_id": batch.batch_id
                })
                
                remaining_qty -= qty_from_batch
        
        # Step 4: Update order totals
        final_amount = subtotal - (sale.discount_amount or 0)
        
        db.execute(text("""
            UPDATE orders 
            SET subtotal = :subtotal,
                final_amount = :final_amount,
                tax_amount = :tax_amount
            WHERE order_id = :order_id
        """), {
            "subtotal": float(subtotal),
            "final_amount": float(final_amount),
            "tax_amount": float(total_tax),
            "order_id": order_id
        })
        
        # Step 5: Generate invoice
        invoice_number = f"INV{datetime.now().strftime('%Y%m%d')}{order_id:04d}"
        
        # Calculate GST split (assuming intra-state for simplicity)
        cgst_amount = total_tax / 2
        sgst_amount = total_tax / 2
        igst_amount = Decimal("0")
        
        invoice_result = db.execute(text("""
            INSERT INTO invoices (
                org_id, invoice_number, order_id, customer_id,
                invoice_date, due_date,
                subtotal, discount_amount, taxable_amount,
                cgst_amount, sgst_amount, igst_amount,
                total_amount, payment_status,
                created_at, updated_at
            ) VALUES (
                :org_id, :invoice_number, :order_id, :customer_id,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                :subtotal, :discount_amount, :taxable_amount,
                :cgst_amount, :sgst_amount, :igst_amount,
                :total_amount, :payment_status,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            ) RETURNING invoice_id
        """), {
            "org_id": org_id,
            "invoice_number": invoice_number,
            "order_id": order_id,
            "customer_id": sale.customer_id,
            "subtotal": float(subtotal),
            "discount_amount": float(sale.discount_amount or 0),
            "taxable_amount": float(subtotal - (sale.discount_amount or 0)),
            "cgst_amount": float(cgst_amount),
            "sgst_amount": float(sgst_amount),
            "igst_amount": float(igst_amount),
            "total_amount": float(final_amount),
            "payment_status": "paid" if sale.payment_mode == "Cash" else "pending"
        })
        
        invoice_id = invoice_result.scalar()
        print(f"✅ Created invoice {invoice_number}")
        
        # Step 6: Record payment if provided
        payment_amount = sale.payment_amount or final_amount
        
        if payment_amount > 0:
            db.execute(text("""
                INSERT INTO billing_payments (
                    org_id, order_id, invoice_id, customer_id,
                    payment_date, payment_mode, amount,
                    reference_number, notes,
                    created_at
                ) VALUES (
                    :org_id, :order_id, :invoice_id, :customer_id,
                    CURRENT_TIMESTAMP, :payment_mode, :amount,
                    :reference_number, 'Quick sale payment',
                    CURRENT_TIMESTAMP
                )
            """), {
                "org_id": org_id,
                "order_id": order_id,
                "invoice_id": invoice_id,
                "customer_id": sale.customer_id,
                "payment_mode": sale.payment_mode,
                "amount": float(payment_amount),
                "reference_number": f"PAY-{invoice_number}"
            })
            
            # Update order paid amount
            db.execute(text("""
                UPDATE orders 
                SET paid_amount = :amount
                WHERE order_id = :order_id
            """), {
                "amount": float(payment_amount),
                "order_id": order_id
            })
            
            # Update invoice payment status
            if payment_amount >= final_amount:
                db.execute(text("""
                    UPDATE invoices 
                    SET payment_status = 'paid',
                        paid_amount = :amount
                    WHERE invoice_id = :invoice_id
                """), {
                    "amount": float(payment_amount),
                    "invoice_id": invoice_id
                })
        
        # Commit everything
        db.commit()
        print(f"✅ Quick sale completed successfully!")
        
        return QuickSaleResponse(
            success=True,
            invoice_number=invoice_number,
            total_amount=final_amount,
            order_id=order_id,
            invoice_id=invoice_id,
            invoice_url=f"/api/v1/invoices/{invoice_id}/print",  # If implemented
            message=f"Sale completed! Invoice {invoice_number} generated."
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Quick sale failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Sale failed: {str(e)}"
        )