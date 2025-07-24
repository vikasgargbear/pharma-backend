#!/usr/bin/env python3
"""
Fix missing invoice columns in production database
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.database import get_db
from sqlalchemy import text

def fix_invoice_columns():
    """Add missing columns to invoices table"""
    
    # Read the SQL file
    sql_file = project_root / "database" / "supabase" / "15_add_missing_invoice_columns.sql"
    
    if not sql_file.exists():
        print(f"❌ SQL file not found: {sql_file}")
        return False
    
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    # Get database connection
    db = next(get_db())
    
    try:
        print("🔧 Adding missing columns to invoices table...")
        
        # Execute the SQL
        result = db.execute(text(sql_content))
        db.commit()
        
        print("✅ Successfully added missing invoice columns")
        
        # Verify the columns exist
        check_sql = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'invoices' 
        AND column_name IN ('billing_name', 'billing_address', 'billing_city', 
                           'billing_state', 'billing_pincode', 'gst_type', 
                           'place_of_supply', 'customer_gstin', 'taxable_amount', 'total_tax_amount')
        ORDER BY column_name;
        """
        
        columns = db.execute(text(check_sql)).fetchall()
        
        print(f"\n📋 Verified {len(columns)} columns exist:")
        for col in columns:
            print(f"   ✓ {col.column_name} ({col.data_type})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding columns: {str(e)}")
        db.rollback()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    success = fix_invoice_columns()
    sys.exit(0 if success else 1)