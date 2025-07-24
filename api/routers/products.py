"""
Products API Router - Demonstrates the new modular architecture
Reduces from 200+ lines to ~80 lines using generic CRUD
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import time

from ..core.crud_base import create_crud
from ..core.security import ResourceNotFoundError
from ..database import get_db
from ..models import Product
from ..base_schemas import ProductCreate as BaseProductCreate
from ..schemas_v2.product_schema import ProductCreate, ProductUpdate, ProductResponse

# Create router
router = APIRouter(prefix="/products", tags=["products"])

# Create CRUD instance - replaces 200+ lines of repetitive code!
product_crud = create_crud(Product)

@router.post("/")
def create_product(product: dict, db: Session = Depends(get_db)):
    """Create a new product with new pack configuration"""
    try:
        # Use raw dict to avoid Pydantic validation stripping fields
        product_dict = product
        # Set default org_id
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
        
        # Debug: Check if new pack fields are present
        pack_fields = ['pack_input', 'pack_quantity', 'pack_multiplier', 'pack_unit_type', 'unit_count', 'unit_measurement', 'packages_per_box']
        print("Pack fields in request:")
        for field in pack_fields:
            print(f"  {field}: {product_dict.get(field, 'NOT PRESENT')}")
        
        # Remove fields not in database model
        db_fields = product_dict.copy()
        quantity_received = db_fields.pop('quantity_received', None)  # Will be handled in batch creation
        expiry_date = db_fields.pop('expiry_date', None)  # Will be handled in batch creation
        db_fields.pop('qty_per_strip', None)  # Legacy field
        db_fields.pop('strips_per_box', None)  # Legacy field
        
        # Set additional required fields
        # Always use cost_price for purchase_price if provided
        if 'cost_price' in db_fields:
            db_fields['purchase_price'] = db_fields.pop('cost_price')
        elif 'purchase_price' not in db_fields:
            db_fields['purchase_price'] = 0
        
        # Set UOM codes based on base_unit and sale_unit
        if 'base_unit' in db_fields:
            db_fields['base_uom_code'] = db_fields.pop('base_unit')
        if 'sale_unit' in db_fields:
            db_fields['sale_uom_code'] = db_fields.pop('sale_unit')
            
        # Log the exact fields being sent to database
        print(f"\nFinal fields being saved to DB:")
        for field in ['pack_input', 'pack_quantity', 'pack_multiplier', 'pack_unit_type']:
            print(f"  {field}: {db_fields.get(field, 'NOT IN DICT')}")
        
        # Create product with the dict
        print(f"Fields being sent to DB: {list(db_fields.keys())}")
        db_product = Product(**db_fields)
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        
        # Debug: Check what was saved
        print(f"\nProduct saved - checking pack fields:")
        print(f"  pack_input: {db_product.pack_input}")
        print(f"  pack_quantity: {db_product.pack_quantity}")
        print(f"  pack_multiplier: {db_product.pack_multiplier}")
        print(f"  pack_unit_type: {db_product.pack_unit_type}")
        
        # Debug logging for batch creation
        print(f"\nBatch creation check:")
        print(f"  quantity_received: {quantity_received} (type: {type(quantity_received)})")
        print(f"  expiry_date: {expiry_date} (type: {type(expiry_date)})")
        
        # Create initial batch if quantity provided
        if quantity_received:
            from ..models import Batch
            from datetime import datetime, timedelta
            
            print(f"Creating batch - quantity_received is truthy: {quantity_received}")
            
            # If no expiry date provided, set a default (2 years from now)
            if not expiry_date:
                expiry_date = (datetime.now() + timedelta(days=730)).date()
                print(f"No expiry date provided, using default: {expiry_date}")
            else:
                print(f"Using provided expiry date: {expiry_date}")
                
            batch = Batch(
                org_id=db_product.org_id,
                product_id=db_product.product_id,
                batch_number=f"BATCH{int(time.time()) % 1000000}",
                expiry_date=expiry_date,
                quantity_received=quantity_received,
                quantity_available=quantity_received,
                cost_price=db_product.purchase_price,
                selling_price=db_product.sale_price,
                mrp=db_product.mrp,
                batch_status='active'
            )
            db.add(batch)
            db.commit()
        
        # Return the created product with all fields
        result = {
            "product_id": db_product.product_id,
            "product_code": db_product.product_code,
            "product_name": db_product.product_name,
            "manufacturer": db_product.manufacturer,
            "hsn_code": db_product.hsn_code,
            "category": db_product.category,
            "salt_composition": db_product.salt_composition,
            "mrp": float(db_product.mrp or 0),
            "sale_price": float(db_product.sale_price or 0),
            "cost_price": float(db_product.purchase_price or 0),
            "gst_percent": float(db_product.gst_percent or 12),
            "base_unit": db_product.base_uom_code or 'Unit',
            "sale_unit": db_product.sale_uom_code or 'Unit',
            "org_id": str(db_product.org_id),
            "is_active": db_product.is_active,
            "created_at": db_product.created_at.isoformat() if db_product.created_at else None,
            "updated_at": db_product.updated_at.isoformat() if db_product.updated_at else None,
            "pack_config": {
                "pack_input": db_product.pack_input,
                "pack_quantity": db_product.pack_quantity,
                "pack_multiplier": db_product.pack_multiplier,
                "pack_unit_type": db_product.pack_unit_type,
                "unit_count": db_product.unit_count,
                "unit_measurement": db_product.unit_measurement,
                "packages_per_box": db_product.packages_per_box
            },
            "message": "Product created successfully"
        }
        
        print(f"Returning product with pack fields: pack_input={result['pack_config']['pack_input']}, pack_quantity={result['pack_config']['pack_quantity']}")
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
            
            # Add pack configuration
            product_dict['pack_config'] = {
                "pack_input": product_dict.get('pack_input'),
                "pack_quantity": product_dict.get('pack_quantity'),
                "pack_multiplier": product_dict.get('pack_multiplier'),
                "pack_unit_type": product_dict.get('pack_unit_type'),
                "unit_count": product_dict.get('unit_count'),
                "unit_measurement": product_dict.get('unit_measurement'),
                "packages_per_box": product_dict.get('packages_per_box')
            }
            
            # Add computed fields
            product_dict['base_unit'] = product_dict.get('base_uom_code', 'Unit')
            product_dict['sale_unit'] = product_dict.get('sale_uom_code', 'Unit')
            product_dict['cost_price'] = float(product_dict.get('purchase_price', 0))
                
            products.append(product_dict)
        
        return products
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get products: {str(e)}")

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID"""
    try:
        db_product = db.query(Product).filter(Product.product_id == product_id).first()
        if not db_product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        # Return using ProductResponse model
        return ProductResponse(
            product_id=db_product.product_id,
            product_code=db_product.product_code,
            product_name=db_product.product_name,
            manufacturer=db_product.manufacturer,
            hsn_code=db_product.hsn_code,
            category=db_product.category,
            salt_composition=db_product.salt_composition,
            mrp=db_product.mrp,
            sale_price=db_product.sale_price,
            cost_price=db_product.purchase_price,
            gst_percent=db_product.gst_percent,
            base_unit=db_product.base_uom_code or 'Unit',
            sale_unit=db_product.sale_uom_code or 'Unit',
            org_id=str(db_product.org_id),
            is_active=db_product.is_active,
            created_at=db_product.created_at,
            updated_at=db_product.updated_at,
            pack_config={
                "pack_input": db_product.pack_input,
                "pack_quantity": db_product.pack_quantity,
                "pack_multiplier": db_product.pack_multiplier,
                "pack_unit_type": db_product.pack_unit_type,
                "unit_count": db_product.unit_count,
                "unit_measurement": db_product.unit_measurement,
                "packages_per_box": db_product.packages_per_box
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get product: {str(e)}")

@router.put("/{product_id}", response_model=ProductResponse) 
def update_product(product_id: int, product_update: ProductUpdate, db: Session = Depends(get_db)):
    """Update a product with new pack configuration"""
    try:
        # Get existing product
        db_product = db.query(Product).filter(Product.product_id == product_id).first()
        if not db_product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        # Update fields
        update_data = product_update.model_dump(exclude_unset=True) if hasattr(product_update, 'model_dump') else product_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_product, field):
                setattr(db_product, field, value)
        
        db_product.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_product)
        
        # Return using ProductResponse model
        return ProductResponse(
            product_id=db_product.product_id,
            product_code=db_product.product_code,
            product_name=db_product.product_name,
            manufacturer=db_product.manufacturer,
            hsn_code=db_product.hsn_code,
            category=db_product.category,
            salt_composition=db_product.salt_composition,
            mrp=db_product.mrp,
            sale_price=db_product.sale_price,
            cost_price=db_product.purchase_price,
            gst_percent=db_product.gst_percent,
            base_unit=db_product.base_uom_code or 'Unit',
            sale_unit=db_product.sale_uom_code or 'Unit',
            org_id=str(db_product.org_id),
            is_active=db_product.is_active,
            created_at=db_product.created_at,
            updated_at=db_product.updated_at,
            pack_config={
                "pack_input": db_product.pack_input,
                "pack_quantity": db_product.pack_quantity,
                "pack_multiplier": db_product.pack_multiplier,
                "pack_unit_type": db_product.pack_unit_type,
                "unit_count": db_product.unit_count,
                "unit_measurement": db_product.unit_measurement,
                "packages_per_box": db_product.packages_per_box
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product"""
    if not product_crud.exists(db=db, id=product_id):
        raise ResourceNotFoundError(404, f"Product {product_id} not found")
    product_crud.remove(db=db, id=product_id)
    return {"message": f"Product {product_id} deleted successfully"} 