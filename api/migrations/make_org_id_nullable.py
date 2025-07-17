"""
Migration to make org_id nullable across all tables
"""
from sqlalchemy import text
from api.database import engine

def run_migration():
    """Make org_id nullable in all tables that have it"""
    
    tables_with_org_id = [
        'products', 'batches', 'customers', 'orders', 'order_items',
        'payments', 'suppliers', 'purchases', 'purchase_items',
        'inventory_movements', 'org_users', 'org_branches', 'price_lists'
    ]
    
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
                    print(f"✓ Made org_id nullable in {table}")
                else:
                    print(f"⚠ Table {table} not found")
                    
            except Exception as e:
                print(f"✗ Error updating {table}: {str(e)}")
        
        conn.commit()
        print("\n✓ Migration completed successfully")

if __name__ == "__main__":
    run_migration()