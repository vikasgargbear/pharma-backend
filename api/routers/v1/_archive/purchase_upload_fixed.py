"""
Fixed Purchase Upload Router with better error handling
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Dict, Any
import tempfile
import os
import shutil
import logging
from datetime import datetime
from decimal import Decimal

from database.connection import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/parse-invoice-safe")
async def parse_purchase_invoice_safe(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Parse a purchase invoice PDF with better error handling
    Falls back to manual entry structure if parsing fails
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400, 
                detail="Only PDF files are supported"
            )
        
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        try:
            # Try to parse with bill_parser
            try:
                from bill_parser import parse_pdf
                invoice_data = parse_pdf(tmp_path)
                
                # Successfully parsed - return structured data
                response_data = {
                    "success": True,
                    "extracted_data": {
                        "invoice_number": getattr(invoice_data, 'invoice_number', ''),
                        "invoice_date": getattr(invoice_data, 'invoice_date', datetime.now()).isoformat() if hasattr(invoice_data, 'invoice_date') and invoice_data.invoice_date else datetime.now().isoformat()[:10],
                        "supplier_name": getattr(invoice_data, 'supplier_name', ''),
                        "supplier_gstin": getattr(invoice_data, 'supplier_gstin', ''),
                        "supplier_address": getattr(invoice_data, 'supplier_address', ''),
                        "drug_license": getattr(invoice_data, 'drug_license_number', ''),
                        "subtotal": float(getattr(invoice_data, 'subtotal', 0) or 0),
                        "tax_amount": float(getattr(invoice_data, 'tax_amount', 0) or 0),
                        "discount_amount": float(getattr(invoice_data, 'discount_amount', 0) or 0),
                        "grand_total": float(getattr(invoice_data, 'grand_total', 0) or 0),
                        "items": []
                    },
                    "confidence_score": getattr(invoice_data, 'confidence_score', 0.5),
                    "manual_review_required": True
                }
                
                # Process items safely
                if hasattr(invoice_data, 'items') and invoice_data.items:
                    for item in invoice_data.items:
                        try:
                            item_data = {
                                "product_name": getattr(item, 'description', ''),
                                "hsn_code": getattr(item, 'hsn_code', ''),
                                "batch_number": getattr(item, 'batch_number', ''),
                                "expiry_date": getattr(item, 'expiry_date', ''),
                                "quantity": int(getattr(item, 'quantity', 0) or 0),
                                "unit": getattr(item, 'unit', ''),
                                "cost_price": float(getattr(item, 'rate', 0) or 0),
                                "mrp": float(getattr(item, 'mrp', 0) or 0),
                                "discount_percent": float(getattr(item, 'discount_percent', 0) or 0),
                                "tax_percent": float(getattr(item, 'tax_percent', 12) or 12),
                                "amount": float(getattr(item, 'amount', 0) or 0)
                            }
                            response_data["extracted_data"]["items"].append(item_data)
                        except Exception as e:
                            logger.warning(f"Error processing item: {e}")
                            continue
                
                return response_data
                
            except Exception as parse_error:
                logger.warning(f"Bill parser failed: {parse_error}")
                
                # Fallback: Return template for manual entry
                return {
                    "success": False,
                    "message": "Could not extract data automatically. Please fill in manually.",
                    "extracted_data": {
                        "invoice_number": "",
                        "invoice_date": datetime.now().isoformat()[:10],
                        "supplier_name": "",
                        "supplier_gstin": "",
                        "supplier_address": "",
                        "drug_license": "",
                        "subtotal": 0,
                        "tax_amount": 0,
                        "discount_amount": 0,
                        "grand_total": 0,
                        "items": [
                            {
                                "product_name": "",
                                "hsn_code": "",
                                "batch_number": "",  # Will auto-generate if left empty
                                "expiry_date": "",   # Will default to 2 years if left empty
                                "quantity": 0,
                                "unit": "strip",
                                "cost_price": 0,
                                "mrp": 0,
                                "discount_percent": 0,
                                "tax_percent": 12,
                                "amount": 0
                            }
                        ]
                    },
                    "confidence_score": 0,
                    "manual_review_required": True,
                    "parsing_error": str(parse_error)
                }
                
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        logger.error(f"Error in parse_invoice_safe: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process invoice: {str(e)}"
        )

@router.post("/create-from-parsed")
async def create_purchase_from_parsed(
    data: dict,
    db: Session = Depends(get_db)
):
    """Create purchase from parsed or manually entered data"""
    try:
        # Extract data
        extracted = data.get('extracted_data', data)
        
        # Find or create supplier
        supplier_id = extracted.get('supplier_id')
        
        if not supplier_id and extracted.get('supplier_name'):
            # Check if supplier exists
            existing = db.execute(
                text("SELECT supplier_id FROM suppliers WHERE supplier_name = :name"),
                {"name": extracted['supplier_name']}
            ).first()
            
            if existing:
                supplier_id = existing.supplier_id
            else:
                # Create new supplier
                supplier_id = db.execute(
                    text("""
                        INSERT INTO suppliers (
                            org_id, supplier_name, supplier_gstin, 
                            supplier_address, drug_license_number
                        ) VALUES (
                            '12de5e22-eee7-4d25-b3a7-d16d01c6170f',
                            :name, :gstin, :address, :license
                        ) RETURNING supplier_id
                    """),
                    {
                        "name": extracted['supplier_name'],
                        "gstin": extracted.get('supplier_gstin', ''),
                        "address": extracted.get('supplier_address', ''),
                        "license": extracted.get('drug_license', '')
                    }
                ).scalar()
        
        if not supplier_id:
            raise HTTPException(status_code=400, detail="Supplier information required")
        
        # Generate purchase number
        purchase_number = f"PO-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Create purchase with enhanced endpoint
        purchase_data = {
            "supplier_id": supplier_id,
            "purchase_number": purchase_number,
            "purchase_date": datetime.now().isoformat()[:10],
            "supplier_invoice_number": extracted.get('invoice_number', ''),
            "supplier_invoice_date": extracted.get('invoice_date', datetime.now().isoformat()[:10]),
            "subtotal_amount": float(extracted.get('subtotal', 0)),
            "tax_amount": float(extracted.get('tax_amount', 0)),
            "discount_amount": float(extracted.get('discount_amount', 0)),
            "final_amount": float(extracted.get('grand_total', 0)),
            "payment_status": "pending",
            "purchase_status": "draft",
            "items": []
        }
        
        # Process items
        for item in extracted.get('items', []):
            # Find product by name
            product = db.execute(
                text("""
                    SELECT product_id, product_name, hsn_code 
                    FROM products 
                    WHERE LOWER(product_name) LIKE LOWER(:name)
                    LIMIT 1
                """),
                {"name": f"%{item.get('product_name', '')}%"}
            ).first()
            
            if product:
                purchase_data['items'].append({
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "ordered_quantity": int(item.get('quantity', 0)),
                    "received_quantity": 0,
                    "cost_price": float(item.get('cost_price', 0)),
                    "mrp": float(item.get('mrp', 0)),
                    "tax_percent": float(item.get('tax_percent', 12)),
                    "discount_percent": float(item.get('discount_percent', 0)),
                    "batch_number": item.get('batch_number', ''),  # Empty for auto-generation
                    "expiry_date": item.get('expiry_date', ''),    # Empty for default
                    "item_status": "pending"
                })
        
        # Create purchase using enhanced API
        from api.routers.v1.purchase_enhanced import create_purchase_with_items
        result = create_purchase_with_items(purchase_data, db)
        
        return {
            "success": True,
            "purchase_id": result.get("purchase_id"),
            "purchase_number": result.get("purchase_number"),
            "message": "Purchase created successfully from invoice data",
            "items_created": len(purchase_data['items'])
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating purchase: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create purchase: {str(e)}"
        )