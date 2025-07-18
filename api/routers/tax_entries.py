"""
Tax Entries Router - All tax-related endpoints
Migrated from main.py for better modularity and maintainability
Supabase (PostgreSQL) compatible
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from ..database import get_db
from .. import models, schemas
from ..core.crud_base import create_crud
from ..core.security import handle_database_error

# Create router
router = APIRouter(prefix="/tax-entries", tags=["tax_entries"])

# Create CRUD instances using our generic system
tax_entry_crud = create_crud(models.TaxEntry)

# ================= TAX ENTRIES =================

@router.post("/", response_model=schemas.TaxEntry)
@handle_database_error
def create_tax_entry(entry: schemas.TaxEntryCreate, db: Session = Depends(get_db)):
    """Create a new tax entry"""
    return tax_entry_crud.create(db, entry)

@router.get("/", response_model=List[schemas.TaxEntry])
@handle_database_error
def read_tax_entries(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all tax entries with pagination"""
    return tax_entry_crud.get_multi(db, skip=skip, limit=limit)

@router.get("/{tax_entry_id}", response_model=schemas.TaxEntry)
@handle_database_error
def read_tax_entry(tax_entry_id: int, db: Session = Depends(get_db)):
    """Get a specific tax entry by ID"""
    tax_entry = tax_entry_crud.get(db, tax_entry_id)
    if not tax_entry:
        raise HTTPException(status_code=404, detail="Tax entry not found")
    return tax_entry

@router.put("/{tax_entry_id}", response_model=schemas.TaxEntry)
@handle_database_error
def update_tax_entry(tax_entry_id: int, entry: schemas.TaxEntryCreate, db: Session = Depends(get_db)):
    """Update an existing tax entry"""
    db_entry = tax_entry_crud.get(db, tax_entry_id)
    if not db_entry:
        raise HTTPException(status_code=404, detail="Tax entry not found")
    return tax_entry_crud.update(db, db_obj=db_entry, obj_in=entry)

@router.delete("/{tax_entry_id}")
@handle_database_error
def delete_tax_entry(tax_entry_id: int, db: Session = Depends(get_db)):
    """Delete a tax entry"""
    db_entry = tax_entry_crud.get(db, tax_entry_id)
    if not db_entry:
        raise HTTPException(status_code=404, detail="Tax entry not found")
    return tax_entry_crud.remove(db, id=tax_entry_id)

# ================= TAX CALCULATIONS =================

@router.post("/calculate")
@handle_database_error
def calculate_tax(
    base_amount: float,
    tax_rate: float,
    tax_type: str = "GST",
    db: Session = Depends(get_db)
):
    """Calculate tax for a given amount"""
    if tax_rate < 0 or tax_rate > 100:
        raise HTTPException(status_code=400, detail="Tax rate must be between 0 and 100")
    
    tax_amount = (base_amount * tax_rate) / 100
    total_amount = base_amount + tax_amount
    
    return {
        "base_amount": base_amount,
        "tax_rate": tax_rate,
        "tax_type": tax_type,
        "tax_amount": tax_amount,
        "total_amount": total_amount
    }

@router.get("/order/{order_id}/tax-summary")
@handle_database_error
def get_order_tax_summary(order_id: int, db: Session = Depends(get_db)):
    """Get tax summary for a specific order"""
    # Get order
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get tax entries for this order
    tax_entries = db.query(models.TaxEntry).filter(
        models.TaxEntry.order_id == order_id
    ).all()
    
    # Calculate totals
    total_tax = sum(entry.tax_amount for entry in tax_entries)
    
    # Group by tax type
    tax_by_type = {}
    for entry in tax_entries:
        if entry.tax_type not in tax_by_type:
            tax_by_type[entry.tax_type] = 0
        tax_by_type[entry.tax_type] += entry.tax_amount
    
    return {
        "order_id": order_id,
        "base_amount": order.subtotal if hasattr(order, 'subtotal') else order.total_amount,
        "total_tax": total_tax,
        "tax_by_type": tax_by_type,
        "final_amount": order.total_amount,
        "tax_entries": tax_entries
    }

# ================= TAX REPORTING =================

@router.get("/reports/summary")
@handle_database_error
def get_tax_report_summary(
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db)
):
    """Get tax report summary for a date range"""
    query = db.query(models.TaxEntry)
    
    # Apply date filters
    if start_date:
        query = query.filter(models.TaxEntry.created_at >= start_date)
    if end_date:
        query = query.filter(models.TaxEntry.created_at <= end_date)
    
    tax_entries = query.all()
    
    # Calculate totals
    total_tax_collected = sum(entry.tax_amount for entry in tax_entries)
    
    # Group by tax type
    tax_by_type = {}
    for entry in tax_entries:
        if entry.tax_type not in tax_by_type:
            tax_by_type[entry.tax_type] = {
                "count": 0,
                "total_amount": 0
            }
        tax_by_type[entry.tax_type]["count"] += 1
        tax_by_type[entry.tax_type]["total_amount"] += entry.tax_amount
    
    # Group by month
    monthly_tax = {}
    for entry in tax_entries:
        month_key = entry.created_at.strftime("%Y-%m") if entry.created_at else "Unknown"
        if month_key not in monthly_tax:
            monthly_tax[month_key] = 0
        monthly_tax[month_key] += entry.tax_amount
    
    return {
        "period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        },
        "total_tax_collected": total_tax_collected,
        "total_entries": len(tax_entries),
        "tax_by_type": tax_by_type,
        "monthly_breakdown": monthly_tax
    }

@router.get("/reports/gst-summary")
@handle_database_error
def get_gst_summary(
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db)
):
    """Get GST-specific tax summary"""
    query = db.query(models.TaxEntry).filter(
        models.TaxEntry.tax_type.in_(["GST", "CGST", "SGST", "IGST"])
    )
    
    # Apply date filters
    if start_date:
        query = query.filter(models.TaxEntry.created_at >= start_date)
    if end_date:
        query = query.filter(models.TaxEntry.created_at <= end_date)
    
    gst_entries = query.all()
    
    # Calculate GST totals
    gst_breakdown = {
        "CGST": 0,
        "SGST": 0,
        "IGST": 0,
        "GST": 0
    }
    
    for entry in gst_entries:
        if entry.tax_type in gst_breakdown:
            gst_breakdown[entry.tax_type] += entry.tax_amount
    
    total_gst = sum(gst_breakdown.values())
    
    return {
        "period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        },
        "total_gst": total_gst,
        "gst_breakdown": gst_breakdown,
        "total_entries": len(gst_entries)
    }

# ================= TAX COMPLIANCE =================

@router.get("/compliance/pending-returns")
@handle_database_error
def get_pending_tax_returns(db: Session = Depends(get_db)):
    """Get pending tax returns that need to be filed"""
    # This would integrate with tax filing requirements
    # For now, we'll return a summary of recent tax collections
    
    from datetime import datetime, timedelta
    current_month = datetime.now().replace(day=1)
    last_month = current_month - timedelta(days=1)
    last_month_start = last_month.replace(day=1)
    
    # Get tax entries for last month
    last_month_entries = db.query(models.TaxEntry).filter(
        models.TaxEntry.created_at >= last_month_start,
        models.TaxEntry.created_at < current_month
    ).all()
    
    total_tax_last_month = sum(entry.tax_amount for entry in last_month_entries)
    
    return {
        "period": f"{last_month_start.strftime('%Y-%m')}",
        "total_tax_liability": total_tax_last_month,
        "entries_count": len(last_month_entries),
        "due_date": "15th of current month",  # Typical GST filing date
        "status": "pending_filing"
    } 