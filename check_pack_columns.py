#!/usr/bin/env python3
"""
Script to check if pack configuration columns exist in the database
and provide guidance on how to add them if missing.
"""

from sqlalchemy import inspect, text
from api.database import engine
from api.models import Product

def check_pack_columns():
    """Check if pack configuration columns exist in the database"""
    
    print("🔍 Checking database schema for pack configuration columns...\n")
    
    # Define expected pack columns
    pack_columns = [
        'pack_input',
        'pack_quantity', 
        'pack_multiplier',
        'pack_unit_type',
        'unit_count',
        'unit_measurement',
        'packages_per_box'
    ]
    
    # Get actual database columns
    inspector = inspect(engine)
    db_columns = [col['name'] for col in inspector.get_columns('products')]
    
    # Check model columns
    model_columns = [c.name for c in Product.__table__.columns]
    
    print("📋 Pack columns defined in SQLAlchemy model:")
    for col in pack_columns:
        if col in model_columns:
            print(f"   ✅ {col}")
        else:
            print(f"   ❌ {col} (missing from model)")
    
    print("\n📊 Pack columns in actual database:")
    missing_columns = []
    for col in pack_columns:
        if col in db_columns:
            print(f"   ✅ {col}")
        else:
            print(f"   ❌ {col} (missing from database)")
            missing_columns.append(col)
    
    if missing_columns:
        print("\n⚠️  MISSING COLUMNS DETECTED!")
        print(f"   The following columns are defined in the model but missing from the database:")
        for col in missing_columns:
            print(f"   - {col}")
        
        print("\n🔧 TO FIX THIS ISSUE:")
        print("   1. Run the migration script: add_pack_columns_migration.sql")
        print("   2. Or run this SQL in your database:")
        print("   ```sql")
        for col in missing_columns:
            col_type = "TEXT" if col in ['pack_input', 'pack_unit_type', 'unit_measurement'] else "INTEGER"
            print(f"   ALTER TABLE products ADD COLUMN IF NOT EXISTS {col} {col_type};")
        print("   ```")
    else:
        print("\n✅ All pack configuration columns exist in the database!")
    
    # Test creating a product with pack fields
    print("\n🧪 Testing product creation with pack fields...")
    try:
        with engine.connect() as conn:
            # Try to insert a test product with pack fields
            result = conn.execute(text("""
                INSERT INTO products (
                    org_id, product_code, product_name, 
                    pack_input, pack_quantity, pack_multiplier
                ) VALUES (
                    '00000000-0000-0000-0000-000000000000'::uuid,
                    'TEST_PACK_' || extract(epoch from now())::text,
                    'Test Pack Product',
                    '10*10', 10, 10
                ) RETURNING product_id;
            """))
            
            # If successful, delete the test product
            test_id = result.scalar()
            conn.execute(text("DELETE FROM products WHERE product_id = :id"), {"id": test_id})
            conn.commit()
            
            print("   ✅ Successfully created and deleted test product with pack fields")
    except Exception as e:
            print(f"   ❌ Failed to create product with pack fields: {str(e)}")
            print("      This confirms the columns are missing from the database")

if __name__ == "__main__":
    check_pack_columns()