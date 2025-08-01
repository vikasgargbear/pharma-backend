"""
Add pack configuration fields to products table
Migration to add pack_input and related fields for enhanced product packaging support
"""

import os
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..core.database_manager import get_database_manager

def run_migration():
    """Run the pack fields migration"""
    # DISABLED: Products are in inventory.products, not master.products
    # This migration is no longer needed with the new schema
    print("⚠️  Skipping add_pack_fields migration - using new schema")
    return True
    
    try:
        db_manager = get_database_manager()
        
        # SQL content embedded directly to avoid file path issues
        sql_content = """
-- Add pack configuration columns to master.products table
ALTER TABLE master.products ADD COLUMN IF NOT EXISTS pack_input VARCHAR(50);
ALTER TABLE master.products ADD COLUMN IF NOT EXISTS pack_quantity INTEGER;
ALTER TABLE master.products ADD COLUMN IF NOT EXISTS pack_multiplier INTEGER;
ALTER TABLE master.products ADD COLUMN IF NOT EXISTS pack_unit_type VARCHAR(10);
ALTER TABLE master.products ADD COLUMN IF NOT EXISTS unit_count INTEGER;
ALTER TABLE master.products ADD COLUMN IF NOT EXISTS unit_measurement VARCHAR(20);
ALTER TABLE master.products ADD COLUMN IF NOT EXISTS packages_per_box INTEGER;

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_products_pack_unit_type ON master.products(pack_unit_type);
CREATE INDEX IF NOT EXISTS idx_products_pack_quantity ON master.products(pack_quantity);
CREATE INDEX IF NOT EXISTS idx_products_packages_per_box ON master.products(packages_per_box);
"""
        
        # Execute migration
        with db_manager.get_session() as db:
            print("🔄 Adding pack configuration fields to products table...")
            
            # Split SQL into individual statements and execute
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for stmt in statements:
                if stmt and not stmt.startswith('--'):  # Skip comments and empty statements
                    try:
                        db.execute(text(stmt))
                        print(f"✅ Executed: {stmt[:50]}...")
                    except Exception as e:
                        # Handle "column already exists" errors gracefully
                        if "already exists" in str(e).lower():
                            print(f"⚠️  Column already exists: {stmt[:50]}...")
                        else:
                            print(f"❌ Error executing: {stmt[:50]}...")
                            print(f"   Error: {e}")
                            raise
            
            db.commit()
            print("✅ Pack fields migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("✅ Migration completed successfully")
    else:
        print("❌ Migration failed")