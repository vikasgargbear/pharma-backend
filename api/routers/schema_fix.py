"""
Schema Fix Router - Temporary endpoint to fix database schema issues
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db

router = APIRouter(prefix="/schema-fix", tags=["schema-fix"])

@router.get("/debug-model")
def debug_batch_model():
    """Debug what columns the Batch model thinks it has"""
    try:
        from ..models import Batch
        
        columns = []
        for col in Batch.__table__.columns:
            columns.append({
                "name": col.name,
                "type": str(col.type),
                "key": col.key,
                "python_attr": col.key
            })
        
        # Check for specific attributes
        has_mfg_date = hasattr(Batch, 'mfg_date')
        has_manufacturing_date = hasattr(Batch, 'manufacturing_date')
        
        return {
            "table_name": Batch.__tablename__,
            "columns": columns,
            "has_mfg_date_attr": has_mfg_date,
            "has_manufacturing_date_attr": has_manufacturing_date,
            "python_attrs": [attr for attr in dir(Batch) if not attr.startswith('_') and not callable(getattr(Batch, attr))]
        }
    except Exception as e:
        return {"error": str(e), "traceback": str(e)}

@router.post("/rename-mfg-date")
def rename_mfg_date_column(db: Session = Depends(get_db)):
    """Rename mfg_date column to manufacturing_date in batches table"""
    try:
        # Check if mfg_date column exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'batches' 
            AND column_name = 'mfg_date'
        """))
        
        if result.fetchone():
            # Rename the column
            db.execute(text("ALTER TABLE batches RENAME COLUMN mfg_date TO manufacturing_date"))
            db.commit()
            return {"status": "success", "message": "Column renamed from mfg_date to manufacturing_date"}
        else:
            # Check if manufacturing_date already exists
            result = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'batches' 
                AND column_name = 'manufacturing_date'
            """))
            
            if result.fetchone():
                return {"status": "info", "message": "manufacturing_date column already exists"}
            else:
                return {"status": "error", "message": "Neither mfg_date nor manufacturing_date found"}
                
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Schema fix failed: {str(e)}")

@router.get("/check-batch-schema")
def check_batch_schema(db: Session = Depends(get_db)):
    """Check the current schema of the batches table"""
    try:
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'batches' 
            ORDER BY ordinal_position
        """))
        
        columns = []
        for row in result:
            columns.append({
                "column_name": row[0],
                "data_type": row[1], 
                "is_nullable": row[2]
            })
            
        return {"table": "batches", "columns": columns}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema check failed: {str(e)}")