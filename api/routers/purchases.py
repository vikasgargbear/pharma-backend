"""
Purchases Router - All purchase-related endpoints
Migrated from main.py for better modularity and maintainability
Supabase (PostgreSQL) compatible
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import os
import tempfile
import logging
from fastapi.responses import FileResponse
from datetime import datetime

from ..database import get_db
from .. import models, schemas
from ..core.crud_base import create_crud
from ..core.security import handle_database_error
from ..dependencies import get_current_user

# Import enhanced bill parser
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from bill_parser.parsers.generic import GenericParser

# Create router
router = APIRouter(prefix="/purchases", tags=["purchases"])

# Create CRUD instances using our generic system
purchase_crud = create_crud(models.Purchase)
purchase_item_crud = create_crud(models.PurchaseItem)
purchase_return_crud = create_crud(models.PurchaseReturn)
purchase_return_item_crud = create_crud(models.PurchaseReturnItem)
supplier_crud = create_crud(models.Supplier)

# ================= PURCHASES =================

@router.post("/", response_model=schemas.Purchase)
@handle_database_error
def create_purchase(purchase: schemas.PurchaseCreate, db: Session = Depends(get_db)):
    """Create a new purchase order"""
    return purchase_crud.create(db, purchase)

@router.get("/", response_model=List[schemas.Purchase])
@handle_database_error
def read_purchases(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all purchases with pagination"""
    return purchase_crud.get_multi(db, skip=skip, limit=limit)

@router.get("/{purchase_id}", response_model=schemas.Purchase)
@handle_database_error
def read_purchase(purchase_id: int, db: Session = Depends(get_db)):
    """Get a specific purchase by ID"""
    purchase = purchase_crud.get(db, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase

@router.put("/{purchase_id}", response_model=schemas.Purchase)
@handle_database_error
def update_purchase(purchase_id: int, purchase: schemas.PurchaseCreate, db: Session = Depends(get_db)):
    """Update an existing purchase"""
    db_purchase = purchase_crud.get(db, purchase_id)
    if not db_purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase_crud.update(db, db_obj=db_purchase, obj_in=purchase)

@router.delete("/{purchase_id}")
@handle_database_error
def delete_purchase(purchase_id: int, db: Session = Depends(get_db)):
    """Delete a purchase"""
    db_purchase = purchase_crud.get(db, purchase_id)
    if not db_purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase_crud.remove(db, id=purchase_id)

# ================= PURCHASE ITEMS =================

@router.post("/items/", response_model=schemas.PurchaseItem)
@handle_database_error
def create_purchase_item(item: schemas.PurchaseItemCreate, db: Session = Depends(get_db)):
    """Create a new purchase item"""
    return purchase_item_crud.create(db, item)

@router.get("/items/", response_model=List[schemas.PurchaseItem])
@handle_database_error
def read_purchase_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all purchase items with pagination"""
    return purchase_item_crud.get_multi(db, skip=skip, limit=limit)

@router.get("/items/{purchase_item_id}", response_model=schemas.PurchaseItem)
@handle_database_error
def read_purchase_item(purchase_item_id: int, db: Session = Depends(get_db)):
    """Get a specific purchase item by ID"""
    item = purchase_item_crud.get(db, purchase_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Purchase item not found")
    return item

@router.put("/items/{purchase_item_id}", response_model=schemas.PurchaseItem)
@handle_database_error
def update_purchase_item(purchase_item_id: int, item: schemas.PurchaseItemCreate, db: Session = Depends(get_db)):
    """Update an existing purchase item"""
    db_item = purchase_item_crud.get(db, purchase_item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Purchase item not found")
    return purchase_item_crud.update(db, db_obj=db_item, obj_in=item)

@router.delete("/items/{purchase_item_id}")
@handle_database_error
def delete_purchase_item(purchase_item_id: int, db: Session = Depends(get_db)):
    """Delete a purchase item"""
    db_item = purchase_item_crud.get(db, purchase_item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Purchase item not found")
    return purchase_item_crud.remove(db, id=purchase_item_id)

# ================= PURCHASE RETURNS =================

@router.post("/returns/", response_model=schemas.PurchaseReturn)
@handle_database_error
def create_purchase_return(purchase_return: schemas.PurchaseReturnCreate, db: Session = Depends(get_db)):
    """Create a purchase return"""
    return purchase_return_crud.create(db, purchase_return)

@router.get("/returns/", response_model=List[schemas.PurchaseReturn])
@handle_database_error
def read_purchase_returns(supplier_id: int = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get purchase returns with optional supplier filtering"""
    query = db.query(models.PurchaseReturn)
    
    if supplier_id:
        query = query.filter(models.PurchaseReturn.supplier_id == supplier_id)
    
    return query.offset(skip).limit(limit).all()

@router.get("/returns/{return_id}", response_model=schemas.PurchaseReturn)
@handle_database_error
def read_purchase_return(return_id: int, db: Session = Depends(get_db)):
    """Get a specific purchase return"""
    purchase_return = purchase_return_crud.get(db, return_id)
    if not purchase_return:
        raise HTTPException(status_code=404, detail="Purchase return not found")
    return purchase_return

@router.put("/returns/{return_id}", response_model=schemas.PurchaseReturn)
@handle_database_error
def update_purchase_return(return_id: int, purchase_return: schemas.PurchaseReturnCreate, db: Session = Depends(get_db)):
    """Update a purchase return"""
    db_return = purchase_return_crud.get(db, return_id)
    if not db_return:
        raise HTTPException(status_code=404, detail="Purchase return not found")
    return purchase_return_crud.update(db, db_obj=db_return, obj_in=purchase_return)

# ================= PURCHASE RETURN ITEMS =================

@router.post("/return-items/", response_model=schemas.PurchaseReturnItem)
@handle_database_error
def create_purchase_return_item(return_item: schemas.PurchaseReturnItemCreate, db: Session = Depends(get_db)):
    """Create a purchase return item"""
    return purchase_return_item_crud.create(db, return_item)

@router.get("/return-items/return/{return_id}", response_model=List[schemas.PurchaseReturnItem])
@handle_database_error
def read_purchase_return_items(return_id: int, db: Session = Depends(get_db)):
    """Get all return items for a specific purchase return"""
    return db.query(models.PurchaseReturnItem).filter(
        models.PurchaseReturnItem.return_id == return_id
    ).all()

@router.get("/return-items/{return_item_id}", response_model=schemas.PurchaseReturnItem)
@handle_database_error
def read_purchase_return_item(return_item_id: int, db: Session = Depends(get_db)):
    """Get a specific purchase return item"""
    return_item = purchase_return_item_crud.get(db, return_item_id)
    if not return_item:
        raise HTTPException(status_code=404, detail="Purchase return item not found")
    return return_item

# ================= SUPPLIERS =================

@router.post("/suppliers/", response_model=schemas.Supplier)
@handle_database_error
def create_supplier(supplier: schemas.SupplierCreate, db: Session = Depends(get_db)):
    """Create a new supplier"""
    return supplier_crud.create(db, supplier)

@router.get("/suppliers/", response_model=List[schemas.Supplier])
@handle_database_error
def read_suppliers(skip: int = 0, limit: int = 100, is_active: bool = None, db: Session = Depends(get_db)):
    """Get suppliers with optional active status filtering"""
    query = db.query(models.Supplier)
    
    if is_active is not None:
        query = query.filter(models.Supplier.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()

@router.get("/suppliers/{supplier_id}", response_model=schemas.Supplier)
@handle_database_error
def read_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """Get a specific supplier by ID"""
    supplier = supplier_crud.get(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier

@router.put("/suppliers/{supplier_id}", response_model=schemas.Supplier)
@handle_database_error
def update_supplier(supplier_id: int, supplier: schemas.SupplierCreate, db: Session = Depends(get_db)):
    """Update an existing supplier"""
    db_supplier = supplier_crud.get(db, supplier_id)
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier_crud.update(db, db_obj=db_supplier, obj_in=supplier)

@router.delete("/suppliers/{supplier_id}")
@handle_database_error
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """Delete a supplier (soft delete by setting is_active=False)"""
    db_supplier = supplier_crud.get(db, supplier_id)
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Soft delete by setting is_active to False
    db_supplier.is_active = False
    db.commit()
    db.refresh(db_supplier)
    
    return {"message": "Supplier deactivated successfully", "supplier_id": supplier_id}

# ================= PURCHASE ANALYTICS =================

@router.get("/analytics/summary")
@handle_database_error
def get_purchase_analytics(db: Session = Depends(get_db)):
    """Get purchase analytics summary"""
    # Total purchases
    total_purchases = db.query(models.Purchase).count()
    
    # Total purchase value
    total_value = db.query(models.Purchase).with_entities(
        models.Purchase.total_amount
    ).all()
    total_purchase_value = sum(purchase.total_amount for purchase in total_value if purchase.total_amount)
    
    # Active suppliers
    active_suppliers = db.query(models.Supplier).filter(
        models.Supplier.is_active == True
    ).count()
    
    # Recent purchases (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_purchases = db.query(models.Purchase).filter(
        models.Purchase.created_at >= thirty_days_ago
    ).count()
    
    return {
        "total_purchases": total_purchases,
        "total_purchase_value": total_purchase_value,
        "active_suppliers": active_suppliers,
        "recent_purchases_30d": recent_purchases,
        "average_purchase_value": total_purchase_value / total_purchases if total_purchases > 0 else 0
    }

@router.get("/suppliers/{supplier_id}/analytics")
@handle_database_error
def get_supplier_analytics(supplier_id: int, db: Session = Depends(get_db)):
    """Get analytics for a specific supplier"""
    # Verify supplier exists
    supplier = supplier_crud.get(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Get supplier's purchases
    purchases = db.query(models.Purchase).filter(
        models.Purchase.supplier_id == supplier_id
    ).all()
    
    # Calculate metrics
    total_purchases = len(purchases)
    total_value = sum(purchase.total_amount for purchase in purchases if purchase.total_amount)
    
    # Get purchase returns
    returns = db.query(models.PurchaseReturn).filter(
        models.PurchaseReturn.supplier_id == supplier_id
    ).all()
    
    total_returns = len(returns)
    total_return_value = sum(return_.total_amount for return_ in returns if return_.total_amount)
    
    return {
        "supplier_id": supplier_id,
        "supplier_name": supplier.name,
        "total_purchases": total_purchases,
        "total_purchase_value": total_value,
        "total_returns": total_returns,
        "total_return_value": total_return_value,
        "net_purchase_value": total_value - total_return_value,
        "return_rate": (total_return_value / total_value * 100) if total_value > 0 else 0
    } 

@router.post("/{purchase_id}/upload-invoice")
async def upload_purchase_invoice(
    purchase_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload purchase invoice PDF for a specific purchase.
    Links the uploaded file to the purchase record.
    """
    try:
        # Verify purchase exists
        purchase = db.query(models.Purchase).filter(models.Purchase.purchase_id == purchase_id).first()
        if not purchase:
            raise HTTPException(status_code=404, detail="Purchase not found")
        
        # Validate file type
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are allowed for invoices")
        
        # Generate unique filename
        import uuid
        file_extension = ".pdf"
        unique_filename = f"purchase_invoice_{purchase_id}_{uuid.uuid4().hex}{file_extension}"
        
        # Create upload directory if it doesn't exist
        upload_dir = "uploads/purchase_invoices"
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
            "upload_purpose": "purchase_invoice",
            "entity_type": "purchase",
            "entity_id": purchase_id,
            "access_level": "private",
            "description": f"Purchase invoice for purchase #{purchase_id}",
            "is_verified": False,
            "virus_scan_status": "pending"
        }
        
        file_upload_crud = create_crud(models.FileUpload)
        uploaded_file = file_upload_crud.create(db, schemas.FileUploadCreate(**file_data))
        
        return {
            "message": "Purchase invoice uploaded successfully",
            "file_id": uploaded_file.file_id,
            "filename": uploaded_file.original_filename,
            "purchase_id": purchase_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/{purchase_id}/invoices")
async def get_purchase_invoices(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all invoice files for a specific purchase.
    """
    # Verify purchase exists
    purchase = db.query(models.Purchase).filter(models.Purchase.purchase_id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    # Get all invoice files for this purchase
    invoices = db.query(models.FileUpload).filter(
        models.FileUpload.entity_type == "purchase",
        models.FileUpload.entity_id == purchase_id,
        models.FileUpload.upload_purpose == "purchase_invoice",
        models.FileUpload.is_active == True
    ).order_by(models.FileUpload.uploaded_at.desc()).all()
    
    return [
        {
            "file_id": invoice.file_id,
            "filename": invoice.original_filename,
            "upload_date": invoice.uploaded_at,
            "file_size": invoice.file_size,
            "verification_status": invoice.virus_scan_status,
            "download_url": f"/files/download/{invoice.stored_filename}"
        }
        for invoice in invoices
    ]

@router.get("/{purchase_id}/download-invoice/{file_id}")
async def download_purchase_invoice(
    purchase_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Download a specific purchase invoice.
    """
    # Verify file belongs to this purchase
    file_record = db.query(models.FileUpload).filter(
        models.FileUpload.file_id == file_id,
        models.FileUpload.entity_type == "purchase",
        models.FileUpload.entity_id == purchase_id,
        models.FileUpload.upload_purpose == "purchase_invoice",
        models.FileUpload.is_active == True
    ).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="Invoice file not found")
    
    # Check if file exists on disk
    if not os.path.exists(file_record.file_path):
        raise HTTPException(status_code=404, detail="Physical file not found")
    
    return FileResponse(
        path=file_record.file_path,
        filename=file_record.original_filename,
        media_type="application/pdf"
    )


# ================= ENHANCED BILL PARSING =================

@router.post("/parse-invoice", response_model=Dict[str, Any])
@handle_database_error
async def parse_invoice_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Parse uploaded pharmaceutical invoice PDF using enhanced AI parser.
    Returns structured data with confidence scores.
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Create temporary file
    temp_file = None
    try:
        # Save uploaded file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        # Parse invoice using enhanced parser
        parser = GenericParser()
        parsed_invoice = parser.parse_from_file(temp_file.name)
        
        # Convert to API response format
        response_data = {
            "success": True,
            "confidence": parsed_invoice.confidence,
            "supplier": {
                "name": parsed_invoice.supplier_name,
                "gstin": parsed_invoice.supplier_gstin,
            },
            "invoice": {
                "number": parsed_invoice.invoice_number,
                "date": parsed_invoice.invoice_date.isoformat() if parsed_invoice.invoice_date else None,
            },
            "financial": {
                "subtotal": parsed_invoice.subtotal,
                "cgst": parsed_invoice.cgst,
                "sgst": parsed_invoice.sgst,
                "igst": parsed_invoice.igst,
                "grand_total": parsed_invoice.grand_total,
            },
            "items": [
                {
                    "description": item.description,
                    "hsn": item.hsn,
                    "batch": item.batch,
                    "expiry": item.expiry,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total": item.total,
                }
                for item in parsed_invoice.items
            ],
            "parsing_metadata": {
                "filename": file.filename,
                "parsed_at": datetime.now().isoformat(),
                "parser_version": "enhanced_generic_v2.0",
                "pattern_count": 113,
            }
        }
        
        logging.info(f"Successfully parsed invoice {file.filename} with confidence {parsed_invoice.confidence:.2f}")
        return response_data
        
    except Exception as e:
        logging.error(f"Failed to parse invoice {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to parse invoice: {str(e)}")
        
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


@router.post("/create-from-invoice", response_model=schemas.Purchase)
@handle_database_error
async def create_purchase_from_parsed_invoice(
    file: UploadFile = File(...),
    auto_create_supplier: bool = True,
    auto_match_products: bool = True,
    min_confidence: float = 0.7,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Parse invoice PDF and automatically create purchase record with items.
    Optionally auto-create suppliers and match products.
    """
    # Parse the invoice first
    temp_file = None
    try:
        # Save uploaded file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        # Parse invoice
        parser = GenericParser()
        parsed_invoice = parser.parse_from_file(temp_file.name)
        
        if parsed_invoice.confidence < min_confidence:
            raise HTTPException(
                status_code=400, 
                detail=f"Parsing confidence {parsed_invoice.confidence:.2f} below minimum {min_confidence}"
            )
        
        # Find or create supplier
        supplier = None
        if parsed_invoice.supplier_gstin:
            supplier = db.query(models.Supplier).filter(
                models.Supplier.gstin == parsed_invoice.supplier_gstin
            ).first()
        
        if not supplier and auto_create_supplier:
            supplier_data = {
                "name": parsed_invoice.supplier_name,
                "gstin": parsed_invoice.supplier_gstin,
                "contact_person": "",
                "phone": "",
                "email": "",
                "address": "",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
            supplier = models.Supplier(**supplier_data)
            db.add(supplier)
            db.commit()
            db.refresh(supplier)
            logging.info(f"Auto-created supplier: {supplier.name}")
        
        if not supplier:
            raise HTTPException(status_code=400, detail="Supplier not found and auto-creation disabled")
        
        # Create purchase record
        purchase_data = {
            "supplier_id": supplier.supplier_id,
            "invoice_number": parsed_invoice.invoice_number,
            "invoice_date": parsed_invoice.invoice_date,
            "subtotal": parsed_invoice.subtotal or 0,
            "cgst_amount": parsed_invoice.cgst or 0,
            "sgst_amount": parsed_invoice.sgst or 0,
            "igst_amount": parsed_invoice.igst or 0,
            "total_amount": parsed_invoice.grand_total or 0,
            "status": "pending_review",  # Require manual review
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        
        purchase = models.Purchase(**purchase_data)
        db.add(purchase)
        db.commit()
        db.refresh(purchase)
        
        # Create purchase items
        created_items = []
        for item in parsed_invoice.items:
            # Try to match existing product if enabled
            product = None
            if auto_match_products and item.description:
                # Simple name matching - can be enhanced with fuzzy matching
                product = db.query(models.Product).filter(
                    models.Product.name.ilike(f"%{item.description.split()[0]}%")
                ).first()
            
            item_data = {
                "purchase_id": purchase.purchase_id,
                "product_id": product.product_id if product else None,
                "description": item.description,
                "hsn_code": item.hsn,
                "batch_number": item.batch,
                "expiry_date": item.expiry,
                "quantity": item.quantity,
                "purchase_price": item.unit_price,
                "total_amount": item.total,
                "created_at": datetime.now(),
            }
            
            purchase_item = models.PurchaseItem(**item_data)
            db.add(purchase_item)
            created_items.append(purchase_item)
        
        db.commit()
        
        # Refresh purchase to get all relationships
        db.refresh(purchase)
        
        logging.info(f"Successfully created purchase {purchase.purchase_id} from invoice {file.filename}")
        return purchase
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to create purchase from invoice {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create purchase: {str(e)}")
        
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


@router.get("/{purchase_id}/parse-confidence", response_model=Dict[str, Any])
@handle_database_error
def get_parsing_confidence_metrics(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get parsing confidence metrics for a purchase created from parsed invoice.
    Useful for quality assurance and manual review prioritization.
    """
    purchase = purchase_crud.get(db, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    # Calculate confidence metrics based on data completeness
    metrics = {
        "purchase_id": purchase_id,
        "supplier_confidence": 0.8 if purchase.supplier_id else 0.0,
        "invoice_data_confidence": 0.9 if purchase.invoice_number and purchase.invoice_date else 0.5,
        "financial_confidence": 0.8 if purchase.total_amount and purchase.total_amount > 0 else 0.3,
        "items_confidence": 0.0,
        "overall_confidence": 0.0,
        "recommendations": [],
    }
    
    # Analyze items
    items = db.query(models.PurchaseItem).filter(
        models.PurchaseItem.purchase_id == purchase_id
    ).all()
    
    if items:
        item_scores = []
        for item in items:
            item_score = 0.0
            if item.description:
                item_score += 0.3
            if item.hsn_code:
                item_score += 0.2
            if item.batch_number:
                item_score += 0.2
            if item.quantity and item.quantity > 0:
                item_score += 0.15
            if item.purchase_price and item.purchase_price > 0:
                item_score += 0.15
            
            item_scores.append(item_score)
        
        metrics["items_confidence"] = sum(item_scores) / len(item_scores)
    
    # Calculate overall confidence
    weights = {
        "supplier": 0.2,
        "invoice_data": 0.2,
        "financial": 0.3,
        "items": 0.3,
    }
    
    metrics["overall_confidence"] = (
        metrics["supplier_confidence"] * weights["supplier"] +
        metrics["invoice_data_confidence"] * weights["invoice_data"] +
        metrics["financial_confidence"] * weights["financial"] +
        metrics["items_confidence"] * weights["items"]
    )
    
    # Generate recommendations
    if metrics["overall_confidence"] < 0.7:
        metrics["recommendations"].append("Manual review recommended")
    if metrics["supplier_confidence"] < 0.5:
        metrics["recommendations"].append("Verify supplier information")
    if metrics["financial_confidence"] < 0.6:
        metrics["recommendations"].append("Check financial amounts")
    if metrics["items_confidence"] < 0.6:
        metrics["recommendations"].append("Review item details and matching")
    
    return metrics


# ================= PARSER HEALTH CHECK =================

@router.get("/parser/health", response_model=Dict[str, Any])
def get_parser_health():
    """
    Check the health status of the enhanced bill parser.
    """
    try:
        parser = GenericParser()
        from bill_parser.pharma_patterns import get_pattern_count
        
        return {
            "status": "healthy",
            "parser_version": "enhanced_generic_v2.0",
            "pattern_count": get_pattern_count(),
            "features": [
                "Multi-engine PDF extraction",
                "113+ pharmaceutical patterns",
                "Confidence scoring",
                "HSN validation",
                "Drug license extraction",
                "Advanced table parsing"
            ]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "parser_version": "unknown"
        } 