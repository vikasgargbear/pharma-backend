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
    try:
        db_manager = get_database_manager()
        
        # Get SQL file path
        sql_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "database", "supabase", "add_pack_fields.sql"
        )
        
        if not os.path.exists(sql_file):
            print(f"❌ SQL file not found: {sql_file}")
            return False
            
        # Read SQL content
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
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