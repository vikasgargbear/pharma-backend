"""
Products API Router - Demonstrates the new modular architecture
Reduces from 200+ lines to ~80 lines using generic CRUD
"""
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.crud_base import create_crud
from ..core.security import ResourceNotFoundError
from ..database import get_db
from ..models import Product
from ..schemas import Product as ProductSchema, ProductCreate

# Create router
router = APIRouter(prefix="/products", tags=["products"])

# Create CRUD instance - replaces 200+ lines of repetitive code!
product_crud = create_crud(Product)

@router.post("/", response_model=ProductSchema)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product"""
    return product_crud.create(db=db, obj_in=product)

@router.get("/", response_model=List[ProductSchema])
def get_products(
    skip: int = 0, limit: int = 100, category: Optional[str] = None,
    manufacturer: Optional[str] = None, db: Session = Depends(get_db)
):
    """Get products with optional filtering"""
    filters = {}
    if category:
        filters["category"] = category
    if manufacturer:
        filters["manufacturer"] = manufacturer
    
    return product_crud.get_multi(db=db, skip=skip, limit=limit, filters=filters)

@router.get("/{product_id}", response_model=ProductSchema)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID"""
    product = product_crud.get(db=db, id=product_id)
    if not product:
        raise ResourceNotFoundError("Product", product_id)
    return product

@router.put("/{product_id}", response_model=ProductSchema) 
def update_product(product_id: int, product_update: ProductCreate, db: Session = Depends(get_db)):
    """Update a product"""
    db_product = product_crud.get(db=db, id=product_id)
    if not db_product:
        raise ResourceNotFoundError("Product", product_id)
    return product_crud.update(db=db, db_obj=db_product, obj_in=product_update)

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product"""
    if not product_crud.exists(db=db, id=product_id):
        raise ResourceNotFoundError("Product", product_id)
    product_crud.remove(db=db, id=product_id)
    return {"message": f"Product {product_id} deleted successfully"} 