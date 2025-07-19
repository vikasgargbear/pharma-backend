"""
Products API Router - Demonstrates the new modular architecture
Reduces from 200+ lines to ~80 lines using generic CRUD
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.crud_base import create_crud
from ..core.security import ResourceNotFoundError
from ..database import get_db
from ..models import Product
from ..base_schemas import ProductCreate

# Create router
router = APIRouter(prefix="/products", tags=["products"])

# Create CRUD instance - replaces 200+ lines of repetitive code!
product_crud = create_crud(Product)

@router.post("/")
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product"""
    try:
        # Ensure org_id is set
        product_dict = product.dict()
        if not product_dict.get('org_id'):
            product_dict['org_id'] = "12de5e22-eee7-4d25-b3a7-d16d01c6170f"
        
        # Check if product already exists
        existing = db.execute(text("""
            SELECT product_id, product_code, product_name, mrp, sale_price, gst_percent
            FROM products 
            WHERE org_id = :org_id AND product_code = :product_code
        """), {
            "org_id": product_dict['org_id'],
            "product_code": product_dict['product_code']
        }).fetchone()
        
        if existing:
            # Return existing product
            result = {
                "product_id": existing.product_id,
                "product_code": existing.product_code,
                "product_name": existing.product_name,
                "org_id": product_dict['org_id'],
                "mrp": float(existing.mrp or 0),
                "sale_price": float(existing.sale_price or 0),
                "gst_percent": float(existing.gst_percent or 12),
                "message": "Product already exists"
            }
            print(f"Product already exists: {result}")
            return result
        
        # Log the data being created
        import json
        print(f"Creating product with data: {json.dumps({k: str(v) for k, v in product_dict.items()}, indent=2)}")
        
        # Create product with the dict
        db_product = Product(**product_dict)
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        
        # Convert to dict for response - ensure all fields are JSON serializable
        result = {
            "product_id": db_product.product_id,
            "product_code": db_product.product_code,
            "product_name": db_product.product_name,
            "org_id": str(db_product.org_id),
            "mrp": float(db_product.mrp or 0),
            "sale_price": float(db_product.sale_price or 0),
            "gst_percent": float(db_product.gst_percent or 12),
            "cgst_percent": float(db_product.cgst_percent or 6),
            "sgst_percent": float(db_product.sgst_percent or 6),
            "igst_percent": float(db_product.igst_percent or 12),
            "hsn_code": db_product.hsn_code,
            "manufacturer": db_product.manufacturer,
            "category": db_product.category,
            "is_active": db_product.is_active
        }
        print(f"Product created successfully: {result}")
        return result
    except Exception as e:
        db.rollback()
        print(f"Error creating product: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

@router.get("/")
def get_products(
    skip: int = 0, limit: int = 100, category: Optional[str] = None,
    manufacturer: Optional[str] = None, search: Optional[str] = None,
    include_batch_info: bool = True, db: Session = Depends(get_db)
):
    """Get products with optional filtering, search, and batch information"""
    try:
        # Query with batch count and availability
        if include_batch_info:
            query = """
                SELECT p.*, 
                       COUNT(DISTINCT b.batch_id) as batch_count,
                       COALESCE(SUM(b.quantity_available), 0) as total_stock,
                       COUNT(DISTINCT CASE WHEN b.quantity_available > 0 AND (b.expiry_date IS NULL OR b.expiry_date > CURRENT_DATE) THEN b.batch_id END) as available_batches
                FROM products p
                LEFT JOIN batches b ON p.product_id = b.product_id AND b.org_id = p.org_id
                WHERE p.org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f'
            """
            group_by = " GROUP BY p.product_id"
        else:
            query = "SELECT * FROM products WHERE org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f'"
            group_by = ""
        
        params = {"skip": skip, "limit": limit}
        
        if search:
            # Case-insensitive search in product name, code, and generic name
            query += """ AND (
                LOWER(p.product_name) LIKE LOWER(:search) OR 
                LOWER(p.product_code) LIKE LOWER(:search) OR
                LOWER(p.generic_name) LIKE LOWER(:search) OR
                LOWER(p.brand_name) LIKE LOWER(:search)
            )"""
            params["search"] = f"%{search}%"
            
        if category:
            query += " AND p.category = :category"
            params["category"] = category
        if manufacturer:
            query += " AND p.manufacturer = :manufacturer"
            params["manufacturer"] = manufacturer
        
        # Add GROUP BY for aggregated queries
        query += group_by
            
        # Order by product name for better UX when searching
        query += " ORDER BY p.product_name LIMIT :limit OFFSET :skip"
        
        result = db.execute(text(query), params)
        products = []
        
        for row in result:
            product_dict = dict(row._mapping)
            # Convert UUID to string if needed
            if product_dict.get('org_id'):
                product_dict['org_id'] = str(product_dict['org_id'])
            
            # Ensure numeric fields are properly typed
            if include_batch_info:
                product_dict['batch_count'] = int(product_dict.get('batch_count', 0))
                product_dict['total_stock'] = int(product_dict.get('total_stock', 0))
                product_dict['available_batches'] = int(product_dict.get('available_batches', 0))
                
            products.append(product_dict)
        
        return products
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get products: {str(e)}")

@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID"""
    try:
        result = db.execute(text("""
            SELECT * FROM products WHERE product_id = :product_id
        """), {"product_id": product_id})
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        product_dict = dict(row._mapping)
        # Convert UUID to string if needed
        if product_dict.get('org_id'):
            product_dict['org_id'] = str(product_dict['org_id'])
            
        return product_dict
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get product: {str(e)}")

@router.put("/{product_id}") 
def update_product(product_id: int, product_update: ProductCreate, db: Session = Depends(get_db)):
    """Update a product"""
    db_product = product_crud.get(db=db, id=product_id)
    if not db_product:
        raise ResourceNotFoundError(404, f"Product {product_id} not found")
    return product_crud.update(db=db, db_obj=db_product, obj_in=product_update)

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product"""
    if not product_crud.exists(db=db, id=product_id):
        raise ResourceNotFoundError(404, f"Product {product_id} not found")
    product_crud.remove(db=db, id=product_id)
    return {"message": f"Product {product_id} deleted successfully"} 