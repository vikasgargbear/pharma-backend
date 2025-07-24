#!/usr/bin/env python3
"""
Script to apply pack fields migration to production database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from api.core.config import settings

def apply_pack_migration():
    """Apply the pack fields migration"""
    print("=== APPLYING PACK FIELDS MIGRATION ===\n")
    
    # Create engine
    engine = create_engine(settings.database_url)
    
    # SQL statements to add pack fields
    migration_sql = """
    -- Add new pack configuration columns
    ALTER TABLE products ADD COLUMN IF NOT EXISTS pack_input VARCHAR(50);
    ALTER TABLE products ADD COLUMN IF NOT EXISTS pack_quantity INTEGER;
    ALTER TABLE products ADD COLUMN IF NOT EXISTS pack_multiplier INTEGER;
    ALTER TABLE products ADD COLUMN IF NOT EXISTS pack_unit_type VARCHAR(10);
    ALTER TABLE products ADD COLUMN IF NOT EXISTS unit_count INTEGER;
    ALTER TABLE products ADD COLUMN IF NOT EXISTS unit_measurement VARCHAR(20);
    ALTER TABLE products ADD COLUMN IF NOT EXISTS packages_per_box INTEGER;
    
    -- Add indexes
    CREATE INDEX IF NOT EXISTS idx_products_pack_unit_type ON products(pack_unit_type);
    CREATE INDEX IF NOT EXISTS idx_products_pack_quantity ON products(pack_quantity);
    CREATE INDEX IF NOT EXISTS idx_products_packages_per_box ON products(packages_per_box);
    """
    
    try:
        with engine.connect() as conn:
            # Execute migration
            print("Executing migration...")
            conn.execute(text(migration_sql))
            conn.commit()
            print("✓ Migration executed successfully")
            
            # Verify columns were added
            print("\nVerifying columns...")
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'products' 
                AND column_name IN ('pack_input', 'pack_quantity', 'pack_multiplier', 
                                    'pack_unit_type', 'unit_count', 'unit_measurement', 
                                    'packages_per_box')
                ORDER BY column_name
            """))
            
            columns = [row[0] for row in result]
            print(f"✓ Found {len(columns)} pack columns: {', '.join(columns)}")
            
            if len(columns) == 7:
                print("\n✅ All pack fields successfully added to database!")
            else:
                print(f"\n⚠️  Warning: Expected 7 columns but found {len(columns)}")
                
    except Exception as e:
        print(f"\n❌ Error applying migration: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if 'postgresql' not in settings.database_url:
        print("⚠️  This script is for PostgreSQL databases only")
        sys.exit(1)
        
    print(f"Database: {settings.database_url[:50]}...")
    response = input("\nApply migration? (yes/no): ")
    
    if response.lower() == 'yes':
        if apply_pack_migration():
            print("\n🎉 Migration completed successfully!")
            print("You may need to restart the application for changes to take effect.")
        else:
            print("\n❌ Migration failed!")
    else:
        print("Migration cancelled.")