"""Test endpoint to diagnose pack fields issue"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db

router = APIRouter(prefix="/test", tags=["test"])

@router.post("/pack-fields")
def test_pack_fields(data: dict, db: Session = Depends(get_db)):
    """Test if pack fields can be saved directly"""
    
    # Log what we received
    print("\n=== TEST PACK FIELDS ===")
    print("Received data:", data)
    
    # Try direct SQL insert
    try:
        result = db.execute(text("""
            INSERT INTO products (
                org_id, product_code, product_name, manufacturer, hsn_code,
                mrp, sale_price, gst_percent, pack_type, pack_size,
                pack_input, pack_quantity, pack_multiplier, pack_unit_type
            ) VALUES (
                :org_id, :product_code, :product_name, :manufacturer, :hsn_code,
                :mrp, :sale_price, :gst_percent, :pack_type, :pack_size,
                :pack_input, :pack_quantity, :pack_multiplier, :pack_unit_type
            ) RETURNING product_id, pack_input, pack_quantity
        """), {
            "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",
            "product_code": f"TEST_{data.get('test_id', '001')}",
            "product_name": "Test Product",
            "manufacturer": "Test Mfg",
            "hsn_code": "3004",
            "mrp": 100,
            "sale_price": 90,
            "gst_percent": 12,
            "pack_type": "10*10",
            "pack_size": "10*10",
            "pack_input": data.get("pack_input", "10*10"),
            "pack_quantity": data.get("pack_quantity", 10),
            "pack_multiplier": data.get("pack_multiplier", 10),
            "pack_unit_type": data.get("pack_unit_type", None)
        })
        
        row = result.fetchone()
        db.commit()
        
        return {
            "success": True,
            "product_id": row[0],
            "saved_pack_input": row[1],
            "saved_pack_quantity": row[2],
            "message": "Direct SQL insert successful"
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

@router.get("/check-columns")
def check_columns(db: Session = Depends(get_db)):
    """Check if pack columns exist in database"""
    
    result = db.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'products' 
        AND column_name LIKE 'pack_%' OR column_name LIKE 'unit_%'
        ORDER BY column_name
    """))
    
    columns = [{"name": row[0], "type": row[1]} for row in result]
    
    return {
        "pack_columns": columns,
        "count": len(columns)
    }