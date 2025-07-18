"""
Orders Router - All order-related endpoints
Migrated from main.py for better modularity and maintainability
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
from fastapi.responses import FileResponse

from ..database import get_db
from .. import models, schemas  # crud import removed - not used
from ..core.crud_base import create_crud
from ..core.security import handle_database_error
from ..dependencies import get_current_user

# Create router
router = APIRouter(prefix="/orders", tags=["orders"])

# Create CRUD instances using our generic system
order_crud = create_crud(models.Order)
order_item_crud = create_crud(models.OrderItem)

# ================= ORDERS =================

@router.post("/", response_model=schemas.Order)
@handle_database_error
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    """Create a new order"""
    return order_crud.create(db, order)

@router.get("/", response_model=List[schemas.Order])
@handle_database_error
def read_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all orders with pagination"""
    return order_crud.get_multi(db, skip=skip, limit=limit)

@router.get("/{order_id}", response_model=schemas.Order)
@handle_database_error
def read_order(order_id: int, db: Session = Depends(get_db)):
    """Get a specific order by ID"""
    order = order_crud.get(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.put("/{order_id}", response_model=schemas.Order)
@handle_database_error
def update_order(order_id: int, order: schemas.OrderCreate, db: Session = Depends(get_db)):
    """Update an existing order"""
    db_order = order_crud.get(db, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_crud.update(db, db_obj=db_order, obj_in=order)

@router.delete("/{order_id}")
@handle_database_error
def delete_order(order_id: int, db: Session = Depends(get_db)):
    """Delete an order"""
    db_order = order_crud.get(db, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_crud.remove(db, id=order_id)

# ================= ORDER ITEMS =================

@router.post("/items/", response_model=schemas.OrderItem)
@handle_database_error
def create_order_item(item: schemas.OrderItemCreate, db: Session = Depends(get_db)):
    """Create a new order item"""
    return order_item_crud.create(db, item)

@router.get("/items/", response_model=List[schemas.OrderItem])
@handle_database_error
def read_order_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all order items with pagination"""
    return order_item_crud.get_multi(db, skip=skip, limit=limit)

@router.get("/items/{order_item_id}", response_model=schemas.OrderItem)
@handle_database_error
def read_order_item(order_item_id: int, db: Session = Depends(get_db)):
    """Get a specific order item by ID"""
    item = order_item_crud.get(db, order_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Order item not found")
    return item

@router.put("/items/{order_item_id}", response_model=schemas.OrderItem)
@handle_database_error
def update_order_item(order_item_id: int, item: schemas.OrderItemCreate, db: Session = Depends(get_db)):
    """Update an existing order item"""
    db_item = order_item_crud.get(db, order_item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Order item not found")
    return order_item_crud.update(db, db_obj=db_item, obj_in=item)

@router.delete("/items/{order_item_id}")
@handle_database_error
def delete_order_item(order_item_id: int, db: Session = Depends(get_db)):
    """Delete an order item"""
    db_item = order_item_crud.get(db, order_item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Order item not found")
    return order_item_crud.remove(db, id=order_item_id)

# ================= ADVANCED ORDER OPERATIONS =================

@router.post("/complete/", response_model=schemas.CompleteOrderResponse)
@handle_database_error
def create_complete_order(order: schemas.CompleteOrderCreate, db: Session = Depends(get_db)):
    """Create a complete order with items and payment processing"""
    # TODO: Implement create_complete_order logic here or in service layer
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/{order_id}/payment-status")
@handle_database_error
def get_order_payment_status(order_id: int, db: Session = Depends(get_db)):
    """Get payment status for a specific order"""
    # Check if order exists
    db_order = order_crud.get(db, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get payment allocations for this order
    payment_allocations = db.query(models.PaymentAllocation).filter(
        models.PaymentAllocation.order_id == order_id
    ).all()
    
    total_paid = sum(allocation.allocated_amount for allocation in payment_allocations)
    
    return {
        "order_id": order_id,
        "order_total": db_order.total_amount,
        "total_paid": total_paid,
        "outstanding": db_order.total_amount - total_paid,
        "status": "paid" if total_paid >= db_order.total_amount else "pending",
        "payment_allocations": [
            {
                "payment_id": allocation.payment_id,
                "allocated_amount": allocation.allocated_amount,
                "allocation_date": allocation.created_at
            }
            for allocation in payment_allocations
        ]
    } 

@router.post("/{order_id}/upload-bill")
async def upload_customer_bill(
    order_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload customer bill PDF for a specific order.
    Links the uploaded file to the order record.
    """
    try:
        # Verify order exists
        order = db.query(models.Order).filter(models.Order.order_id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Validate file type
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are allowed for bills")
        
        # Generate unique filename
        import uuid
        file_extension = ".pdf"
        unique_filename = f"customer_bill_{order_id}_{uuid.uuid4().hex}{file_extension}"
        
        # Create upload directory if it doesn't exist
        upload_dir = "uploads/customer_bills"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create file upload record
        file_data = {
            "original_filename": file.filename,
            "stored_filename": unique_filename,
            "file_path": file_path,
            "file_size": len(content),
            "file_type": file.content_type,
            "file_extension": file_extension,
            "uploaded_by": current_user["user_id"],
            "upload_purpose": "customer_bill",
            "entity_type": "order",
            "entity_id": order_id,
            "access_level": "private",
            "description": f"Customer bill for order #{order_id}",
            "is_verified": False,
            "virus_scan_status": "pending"
        }
        
        file_upload_crud = create_crud(models.FileUpload)
        uploaded_file = file_upload_crud.create(db, schemas.FileUploadCreate(**file_data))
        
        return {
            "message": "Customer bill uploaded successfully",
            "file_id": uploaded_file.file_id,
            "filename": uploaded_file.original_filename,
            "order_id": order_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/{order_id}/bills")
async def get_customer_bills(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all bill files for a specific order.
    """
    # Verify order exists
    order = db.query(models.Order).filter(models.Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get all bill files for this order
    bills = db.query(models.FileUpload).filter(
        models.FileUpload.entity_type == "order",
        models.FileUpload.entity_id == order_id,
        models.FileUpload.upload_purpose == "customer_bill",
        models.FileUpload.is_active == True
    ).order_by(models.FileUpload.uploaded_at.desc()).all()
    
    return [
        {
            "file_id": bill.file_id,
            "filename": bill.original_filename,
            "upload_date": bill.uploaded_at,
            "file_size": bill.file_size,
            "verification_status": bill.virus_scan_status,
            "download_url": f"/files/download/{bill.stored_filename}"
        }
        for bill in bills
    ]

@router.get("/{order_id}/download-bill/{file_id}")
async def download_customer_bill(
    order_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Download a specific customer bill.
    """
    # Verify file belongs to this order
    file_record = db.query(models.FileUpload).filter(
        models.FileUpload.file_id == file_id,
        models.FileUpload.entity_type == "order",
        models.FileUpload.entity_id == order_id,
        models.FileUpload.upload_purpose == "customer_bill",
        models.FileUpload.is_active == True
    ).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="Bill file not found")
    
    # Check if file exists on disk
    if not os.path.exists(file_record.file_path):
        raise HTTPException(status_code=404, detail="Physical file not found")
    
    return FileResponse(
        path=file_record.file_path,
        filename=file_record.original_filename,
        media_type="application/pdf"
    )

@router.post("/{order_id}/generate-bill")
async def generate_customer_bill(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a PDF bill for the order and save it to the file system.
    This endpoint automatically creates a bill PDF from order data.
    """
    try:
        # Get order with related data
        order = db.query(models.Order).filter(models.Order.order_id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get customer details
        customer = db.query(models.Customer).filter(models.Customer.customer_id == order.customer_id).first()
        
        # Get order items
        order_items = db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).all()
        
        # TODO: Implement PDF generation logic here
        # For now, we'll create a placeholder response
        
        return {
            "message": "Bill generation feature will be implemented next",
            "order_id": order_id,
            "customer_name": customer.customer_name if customer else "Unknown",
            "total_amount": order.final_amount,
            "items_count": len(order_items)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bill generation failed: {str(e)}")

@router.get("/customer/{customer_id}/bills")
async def get_customer_all_bills(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all bills for a specific customer across all orders.
    """
    # Verify customer exists
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get all order IDs for this customer
    order_ids = db.query(models.Order.order_id).filter(models.Order.customer_id == customer_id).subquery()
    
    # Get all bill files for all orders of this customer
    bills = db.query(models.FileUpload).filter(
        models.FileUpload.entity_type == "order",
        models.FileUpload.entity_id.in_(order_ids),
        models.FileUpload.upload_purpose == "customer_bill",
        models.FileUpload.is_active == True
    ).order_by(models.FileUpload.uploaded_at.desc()).all()
    
    return [
        {
            "file_id": bill.file_id,
            "filename": bill.original_filename,
            "order_id": bill.entity_id,
            "upload_date": bill.uploaded_at,
            "file_size": bill.file_size,
            "verification_status": bill.virus_scan_status,
            "download_url": f"/files/download/{bill.stored_filename}"
        }
        for bill in bills
    ] 