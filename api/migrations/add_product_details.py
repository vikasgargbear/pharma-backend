"""
Migration script to add additional pharmaceutical product details to the Product table.
"""
import os
import sys

# Add parent directory to path to import from api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import engine

def run_migration():
    """
    Run the migration to add additional pharmaceutical product details to the Product table.
    """
    print("Starting migration: Add additional pharmaceutical product details to Product table")
    
    # Connect to the database
    conn = engine.connect()
    
    try:
        # Add pharmaceutical product detail fields to Product table
        # SQLite doesn't support adding multiple columns in one statement, so we add them one by one
        print("Adding pharmaceutical product detail fields to Product table...")
        
        conn.execute("ALTER TABLE products ADD COLUMN generic_name TEXT")
        conn.execute("ALTER TABLE products ADD COLUMN composition TEXT")
        conn.execute("ALTER TABLE products ADD COLUMN dosage_instructions TEXT")
        conn.execute("ALTER TABLE products ADD COLUMN storage_instructions TEXT")
        conn.execute("ALTER TABLE products ADD COLUMN packer TEXT")
        conn.execute("ALTER TABLE products ADD COLUMN country_of_origin TEXT")
        conn.execute("ALTER TABLE products ADD COLUMN model_number TEXT")
        conn.execute("ALTER TABLE products ADD COLUMN dimensions TEXT")
        conn.execute("ALTER TABLE products ADD COLUMN weight NUMERIC(10, 2)")
        conn.execute("ALTER TABLE products ADD COLUMN weight_unit VARCHAR(10) DEFAULT 'g'")
        conn.execute("ALTER TABLE products ADD COLUMN pack_quantity INTEGER")
        conn.execute("ALTER TABLE products ADD COLUMN pack_form TEXT")
        conn.execute("ALTER TABLE products ADD COLUMN is_discontinued BOOLEAN DEFAULT FALSE")
        conn.execute("ALTER TABLE products ADD COLUMN color TEXT")
        conn.execute("ALTER TABLE products ADD COLUMN asin TEXT")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.close()
        return False
    
    conn.close()
    return True

if __name__ == "__main__":
    run_migration()
