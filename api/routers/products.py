"""
Products API Router - Demonstrates the new modular architecture
Reduces from 200+ lines to ~80 lines using generic CRUD
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.crud_base import create_crud
from ..core.security import ResourceNotFoundError
from ..database import get_db
from ..models import Product
from ..schemas import ProductResponse, ProductCreate

# Create router
router = APIRouter(prefix="/products", tags=["products"])

# Create CRUD instance - replaces 200+ lines of repetitive code!
product_crud = create_crud(Product)

@router.post("/", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product"""
    # Ensure org_id is set
    product_dict = product.dict()
    if not product_dict.get('org_id'):
        product_dict['org_id'] = "12de5e22-eee7-4d25-b3a7-d16d01c6170f"
    
    # Create product with the dict
    db_product = Product(**product_dict)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/")
def get_products(
    skip: int = 0, limit: int = 100, category: Optional[str] = None,
    manufacturer: Optional[str] = None, db: Session = Depends(get_db)
):
    """Get products with optional filtering"""
    try:
        # Simple query without complex ORM
        query = "SELECT * FROM products WHERE 1=1"
        params = {"skip": skip, "limit": limit}
        
        if category:
            query += " AND category = :category"
            params["category"] = category
        if manufacturer:
            query += " AND manufacturer = :manufacturer"
            params["manufacturer"] = manufacturer
            
        query += " ORDER BY product_id DESC LIMIT :limit OFFSET :skip"
        
        result = db.execute(text(query), params)
        products = []
        
        for row in result:
            product_dict = dict(row._mapping)
            # Convert UUID to string if needed
            if product_dict.get('org_id'):
                product_dict['org_id'] = str(product_dict['org_id'])
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

@router.put("/{product_id}", response_model=ProductResponse) 
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