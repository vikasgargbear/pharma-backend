"""
Simple products router without complex dependencies
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
import uuid

from ..database import get_db

router = APIRouter(prefix="/products-simple", tags=["products-simple"])

@router.get("/")
async def list_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all products"""
    try:
        result = db.execute(text("""
            SELECT product_id, org_id, product_code, product_name, 
                   generic_name, manufacturer, hsn_code, mrp, 
                   gst_percent, is_active
            FROM products 
            ORDER BY product_id DESC
            LIMIT :limit OFFSET :skip
        """), {"limit": limit, "skip": skip})
        
        products = []
        for row in result:
            products.append({
                "product_id": row[0],
                "org_id": str(row[1]) if row[1] else None,
                "product_code": row[2],
                "product_name": row[3],
                "generic_name": row[4],
                "manufacturer": row[5],
                "hsn_code": row[6],
                "mrp": float(row[7]) if row[7] else 0,
                "gst_percent": float(row[8]) if row[8] else 0,
                "is_active": row[9]
            })
        
        return {"products": products, "count": len(products)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list products: {str(e)}")

@router.post("/")
async def create_product(
    product_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a new product"""
    try:
        # Ensure org_id is set
        if not product_data.get('org_id'):
            product_data['org_id'] = "12de5e22-eee7-4d25-b3a7-d16d01c6170f"
        
        # Required fields
        if not product_data.get('product_code') or not product_data.get('product_name'):
            raise HTTPException(status_code=400, detail="product_code and product_name are required")
        
        # Insert product
        result = db.execute(text("""
            INSERT INTO products (
                org_id, product_code, product_name, generic_name,
                manufacturer, hsn_code, mrp, gst_percent, is_active
            ) VALUES (
                :org_id, :product_code, :product_name, :generic_name,
                :manufacturer, :hsn_code, :mrp, :gst_percent, :is_active
            ) RETURNING product_id
        """), {
            "org_id": product_data['org_id'],
            "product_code": product_data['product_code'],
            "product_name": product_data['product_name'],
            "generic_name": product_data.get('generic_name'),
            "manufacturer": product_data.get('manufacturer'),
            "hsn_code": product_data.get('hsn_code', '30049099'),
            "mrp": product_data.get('mrp', 0),
            "gst_percent": product_data.get('gst_percent', 12),
            "is_active": product_data.get('is_active', True)
        })
        
        product_id = result.scalar()
        db.commit()
        
        return {
            "message": "Product created successfully",
            "product_id": product_id,
            "product_code": product_data['product_code']
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

@router.get("/{product_id}")
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product"""
    try:
        result = db.execute(text("""
            SELECT product_id, org_id, product_code, product_name, 
                   generic_name, manufacturer, hsn_code, mrp, 
                   gst_percent, is_active
            FROM products 
            WHERE product_id = :product_id
        """), {"product_id": product_id})
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        return {
            "product_id": row[0],
            "org_id": str(row[1]) if row[1] else None,
            "product_code": row[2],
            "product_name": row[3],
            "generic_name": row[4],
            "manufacturer": row[5],
            "hsn_code": row[6],
            "mrp": float(row[7]) if row[7] else 0,
            "gst_percent": float(row[8]) if row[8] else 0,
            "is_active": row[9]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get product: {str(e)}")