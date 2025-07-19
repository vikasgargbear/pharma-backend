"""
Migration endpoints for database updates
"""
from fastapi import APIRouter
from sqlalchemy import text, create_engine
from ..core.config import settings

router = APIRouter()

@router.post("/run-org-id-migration")
async def run_org_id_migration():
    """Make org_id nullable in all tables"""
    
    tables_with_org_id = [
        'products', 'batches', 'customers', 'orders',
        'payments', 'suppliers', 'purchases',
        'inventory_movements', 'org_users', 'org_branches', 'price_lists'
    ]
    
    results = []
    
    # Create a new engine for isolated transaction
    engine = create_engine(settings.DATABASE_URL)
    
    for table in tables_with_org_id:
        try:
            with engine.connect() as conn:
                trans = conn.begin()
                try:
                    # Check if table exists and has org_id column
                    result = conn.execute(text(f"""
                        SELECT COUNT(*) 
                        FROM information_schema.columns 
                        WHERE table_name = '{table}' 
                        AND column_name = 'org_id'
                    """))
                    
                    if result.scalar() > 0:
                        # Make org_id nullable
                        conn.execute(text(f"""
                            ALTER TABLE {table} 
                            ALTER COLUMN org_id DROP NOT NULL
                        """))
                        trans.commit()
                        results.append(f"✓ Made org_id nullable in {table}")
                    else:
                        trans.rollback()
                        results.append(f"⚠ Table {table} doesn't have org_id column")
                        
                except Exception as e:
                    trans.rollback()
                    results.append(f"✗ Error updating {table}: {str(e)}")
                    
        except Exception as e:
            results.append(f"✗ Connection error for {table}: {str(e)}")
            
    engine.dispose()
    
    return {
        "success": True,
        "message": "Migration completed",
        "results": results
    }