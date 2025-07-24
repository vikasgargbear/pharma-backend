#!/usr/bin/env python3
"""
Fix missing billing columns in invoices table
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from api.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_invoices_missing_columns():
    """Add missing billing columns to invoices table"""
    try:
        # Connect to database
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            print("🔧 Adding missing columns to invoices table...")
            
            # Add missing columns
            alter_sql = text("""
                ALTER TABLE invoices
                ADD COLUMN IF NOT EXISTS billing_name VARCHAR(200) NOT NULL DEFAULT '',
                ADD COLUMN IF NOT EXISTS billing_city VARCHAR(100) NOT NULL DEFAULT '',
                ADD COLUMN IF NOT EXISTS billing_state VARCHAR(100) NOT NULL DEFAULT '',
                ADD COLUMN IF NOT EXISTS billing_pincode VARCHAR(10) NOT NULL DEFAULT '',
                ADD COLUMN IF NOT EXISTS gst_type VARCHAR(20) NOT NULL DEFAULT 'cgst_sgst',
                ADD COLUMN IF NOT EXISTS place_of_supply VARCHAR(2) NOT NULL DEFAULT '09'
            """)
            
            conn.execute(alter_sql)
            conn.commit()
            print("✅ Successfully added missing columns")
            
            # Verify the fix
            print("\n🔍 Verifying the fix...")
            columns_result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'invoices'
                AND table_schema = 'public'
                AND column_name IN (
                    'billing_name', 'billing_city', 'billing_state', 
                    'billing_pincode', 'gst_type', 'place_of_supply'
                )
                ORDER BY column_name
            """))
            
            found_columns = [row[0] for row in columns_result]
            expected_columns = ['billing_city', 'billing_name', 'billing_pincode', 'billing_state', 'gst_type', 'place_of_supply']
            
            if set(found_columns) == set(expected_columns):
                print("✅ All required columns are now present!")
                print(f"Added columns: {', '.join(sorted(found_columns))}")
            else:
                missing = set(expected_columns) - set(found_columns)
                if missing:
                    print(f"❌ Still missing: {', '.join(missing)}")
                else:
                    print("✅ All columns verified!")
            
            # Update existing records with default billing info from billing_address
            print("\n🔄 Updating existing records with default billing info...")
            update_sql = text("""
                UPDATE invoices 
                SET 
                    billing_name = CASE 
                        WHEN billing_name = '' OR billing_name IS NULL 
                        THEN customer_name 
                        ELSE billing_name 
                    END,
                    billing_city = CASE 
                        WHEN billing_city = '' OR billing_city IS NULL 
                        THEN 'Not Specified' 
                        ELSE billing_city 
                    END,
                    billing_state = CASE 
                        WHEN billing_state = '' OR billing_state IS NULL 
                        THEN 'Not Specified' 
                        ELSE billing_state 
                    END,
                    billing_pincode = CASE 
                        WHEN billing_pincode = '' OR billing_pincode IS NULL 
                        THEN '000000' 
                        ELSE billing_pincode 
                    END
                WHERE billing_name = '' OR billing_name IS NULL
            """)
            
            result = conn.execute(update_sql)
            conn.commit()
            print(f"✅ Updated {result.rowcount} existing records with default billing info")
            
            print("\n🎉 Fix completed successfully!")
            print("\nThe invoices table now has all required columns for INSERT operations:")
            print("- billing_name")
            print("- billing_city") 
            print("- billing_state")
            print("- billing_pincode")
            print("- gst_type")
            print("- place_of_supply")
            
    except Exception as e:
        logger.error(f"Failed to fix invoices table: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = fix_invoices_missing_columns()
    if success:
        print("\n✅ Migration completed successfully!")
        print("You can now run INSERT operations on the invoices table.")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)