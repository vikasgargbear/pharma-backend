"""
Stock Receive API - Add inventory to products
Allows adding stock/batches to existing products
"""

from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field

from ...database import get_db
from ...dependencies import get_current_org

router = APIRouter(
    prefix="/api/v1/stock",
    tags=["stock"]
)

class StockReceiveRequest(BaseModel):
    """Request model for receiving stock"""
    product_id: int
    batch_number: Optional[str] = None
    quantity: int = Field(gt=0, description="Quantity to receive")
    cost_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    mrp: Optional[Decimal] = None
    expiry_date: Optional[datetime] = None
    supplier_id: Optional[int] = None
    purchase_invoice_number: Optional[str] = None
    notes: Optional[str] = None

class StockReceiveResponse(BaseModel):
    """Response after receiving stock"""
    batch_id: int
    batch_number: str
    product_id: int
    product_name: str
    quantity_received: int
    quantity_available: int
    expiry_date: datetime
    message: str

@router.post("/receive", response_model=StockReceiveResponse)
async def receive_stock(
    stock_data: StockReceiveRequest,
    db: Session = Depends(get_db),
    current_org = Depends(get_current_org)
):
    """
    Receive stock for a product by creating a new batch
    """
    org_id = current_org["org_id"]
    
    try:
        # Get product details
        product = db.execute(text("""
            SELECT product_id, product_name, mrp, sale_price, purchase_price
            FROM products
            WHERE product_id = :product_id AND org_id = :org_id
        """), {
            "product_id": stock_data.product_id,
            "org_id": org_id
        }).first()
        
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product with ID {stock_data.product_id} not found"
            )
        
        # Generate batch number if not provided
        if not stock_data.batch_number:
            batch_number = f"RCV-{datetime.now().strftime('%Y%m%d')}-{stock_data.product_id}-{int(datetime.now().timestamp()) % 10000}"
        else:
            batch_number = stock_data.batch_number
            
        # Check if batch number already exists
        existing = db.execute(text("""
            SELECT batch_id FROM batches
            WHERE batch_number = :batch_number AND org_id = :org_id
        """), {
            "batch_number": batch_number,
            "org_id": org_id
        }).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Batch number {batch_number} already exists"
            )
        
        # Set defaults
        expiry_date = stock_data.expiry_date or (datetime.now() + timedelta(days=730))  # 2 years default
        cost_price = stock_data.cost_price or product.purchase_price or (product.mrp * Decimal("0.7"))
        selling_price = stock_data.selling_price or product.sale_price or (product.mrp * Decimal("0.9"))
        mrp = stock_data.mrp or product.mrp
        
        # Create batch
        result = db.execute(text("""
            INSERT INTO batches (
                org_id, product_id, batch_number, expiry_date,
                quantity_received, quantity_available, quantity_sold,
                quantity_damaged, quantity_returned,
                cost_price, selling_price, mrp,
                supplier_id, purchase_invoice_number,
                batch_status, notes,
                created_at, updated_at
            ) VALUES (
                :org_id, :product_id, :batch_number, :expiry_date,
                :quantity, :quantity, 0, 0, 0,
                :cost_price, :selling_price, :mrp,
                :supplier_id, :purchase_invoice_number,
                'active', :notes,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            ) RETURNING batch_id
        """), {
            "org_id": org_id,
            "product_id": stock_data.product_id,
            "batch_number": batch_number,
            "expiry_date": expiry_date,
            "quantity": stock_data.quantity,
            "cost_price": cost_price,
            "selling_price": selling_price,
            "mrp": mrp,
            "supplier_id": stock_data.supplier_id,
            "purchase_invoice_number": stock_data.purchase_invoice_number,
            "notes": stock_data.notes
        })
        
        batch_id = result.scalar()
        db.commit()
        
        return StockReceiveResponse(
            batch_id=batch_id,
            batch_number=batch_number,
            product_id=product.product_id,
            product_name=product.product_name,
            quantity_received=stock_data.quantity,
            quantity_available=stock_data.quantity,
            expiry_date=expiry_date,
            message=f"Successfully received {stock_data.quantity} units of {product.product_name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to receive stock: {str(e)}"
        )

@router.get("/check/{product_id}")
async def check_stock(
    product_id: int,
    db: Session = Depends(get_db),
    current_org = Depends(get_current_org)
):
    """
    Check available stock for a product
    """
    org_id = current_org["org_id"]
    
    # Get product details
    product = db.execute(text("""
        SELECT product_id, product_name
        FROM products
        WHERE product_id = :product_id AND org_id = :org_id
    """), {
        "product_id": product_id,
        "org_id": org_id
    }).first()
    
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Get stock details
    batches = db.execute(text("""
        SELECT 
            batch_id,
            batch_number,
            quantity_available,
            expiry_date,
            batch_status
        FROM batches
        WHERE product_id = :product_id 
            AND org_id = :org_id
            AND quantity_available > 0
        ORDER BY expiry_date ASC
    """), {
        "product_id": product_id,
        "org_id": org_id
    }).fetchall()
    
    # Calculate total
    total_available = sum(batch.quantity_available for batch in batches)
    
    return {
        "product_id": product.product_id,
        "product_name": product.product_name,
        "total_available": total_available,
        "batches": [
            {
                "batch_id": batch.batch_id,
                "batch_number": batch.batch_number,
                "quantity_available": batch.quantity_available,
                "expiry_date": batch.expiry_date,
                "status": batch.batch_status
            }
            for batch in batches
        ]
    }