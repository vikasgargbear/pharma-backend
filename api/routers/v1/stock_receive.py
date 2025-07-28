"""
Stock Receive API - Add inventory to products
Allows adding stock/batches to existing products
"""

from typing import Optional, List
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field

from ...database import get_db
from ...dependencies import get_current_org

# Default org ID for now
DEFAULT_ORG_ID = "12de5e22-eee7-4d25-b3a7-d16d01c6170f"

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

@router.get("/current")
async def get_current_stock(
    include_batches: bool = False,
    include_valuation: bool = False,
    category: Optional[str] = None,
    low_stock_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get current stock levels for all products
    This endpoint provides comprehensive stock information
    """
    org_id = DEFAULT_ORG_ID
    
    try:
        # Build query for stock data
        query = """
            SELECT 
                p.product_id as id,
                p.product_code as code,
                p.product_name as name,
                p.category,
                'Units' as unit,
                p.mrp,
                p.sale_price as price,
                p.minimum_stock_level as reorder_level,
                p.minimum_stock_level as min_stock,
                COALESCE(SUM(b.quantity_available), 0) as current_stock,
                COALESCE(SUM(b.quantity_available), 0) as stock_quantity,
                COALESCE(SUM(b.quantity_available), 0) as available_stock,
                COALESCE(SUM(b.quantity_sold), 0) as reserved_stock,
                COALESCE(SUM(b.quantity_available * b.cost_price), 0) as stock_value
            FROM products p
            LEFT JOIN batches b ON p.product_id = b.product_id 
                AND b.org_id = :org_id 
                AND b.batch_status = 'active'
                AND b.quantity_available > 0
            WHERE p.org_id = :org_id
        """
        
        params = {"org_id": org_id}
        
        if category:
            query += " AND p.category = :category"
            params["category"] = category
            
        query += " GROUP BY p.product_id, p.product_code, p.product_name, p.category, p.mrp, p.sale_price, p.minimum_stock_level"
        
        if low_stock_only:
            query = f"SELECT * FROM ({query}) AS stock_data WHERE current_stock <= reorder_level"
            
        # Add ordering and pagination
        query += " ORDER BY name LIMIT :limit OFFSET :skip"
        params.update({"limit": limit, "skip": skip})
        
        result = db.execute(text(query), params)
        products = []
        
        for row in result:
            product_data = dict(row._mapping)
            
            # Add calculated fields
            product_data["low_stock"] = product_data["current_stock"] <= (product_data["reorder_level"] or 0)
            product_data["expiry_alert"] = False  # Would need batch data to calculate
            
            # Get batch information if requested
            if include_batches:
                batch_result = db.execute(text("""
                    SELECT 
                        batch_number as batch_no,
                        quantity_available as quantity,
                        expiry_date
                    FROM batches
                    WHERE product_id = :product_id 
                        AND org_id = :org_id
                        AND batch_status = 'active'
                        AND quantity_available > 0
                    ORDER BY expiry_date ASC
                """), {
                    "product_id": product_data["id"],
                    "org_id": org_id
                })
                
                batches = []
                for batch in batch_result:
                    batch_data = dict(batch._mapping)
                    # Check if batch is expiring soon (within 90 days)
                    if batch_data["expiry_date"]:
                        days_to_expiry = (batch_data["expiry_date"] - datetime.now().date()).days
                        if days_to_expiry <= 90:
                            product_data["expiry_alert"] = True
                    batches.append(batch_data)
                    
                product_data["batches"] = batches
            else:
                product_data["batches"] = []
                
            products.append(product_data)
            
        return products
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get current stock: {str(e)}"
        )