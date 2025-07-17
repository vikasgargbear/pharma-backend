"""
Migration endpoints for database updates
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from api.database import engine

router = APIRouter()

@router.post("/run-org-id-migration")
async def run_org_id_migration():
    """Make org_id nullable in all tables"""
    
    tables_with_org_id = [
        'products', 'batches', 'customers', 'orders', 'order_items',
        'payments', 'suppliers', 'purchases', 'purchase_items',
        'inventory_movements', 'org_users', 'org_branches', 'price_lists'
    ]
    
    results = []
    
    try:
        with engine.connect() as conn:
            for table in tables_with_org_id:
                try:
                    # Check if table exists
                    result = conn.execute(text(f"""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    """))
                    
                    if result.scalar() > 0:
                        # Make org_id nullable
                        conn.execute(text(f"""
                            ALTER TABLE {table} 
                            ALTER COLUMN org_id DROP NOT NULL
                        """))
                        results.append(f"✓ Made org_id nullable in {table}")
                    else:
                        results.append(f"⚠ Table {table} not found")
                        
                except Exception as e:
                    results.append(f"✗ Error updating {table}: {str(e)}")
            
            conn.commit()
            
        return {
            "success": True,
            "message": "Migration completed",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))