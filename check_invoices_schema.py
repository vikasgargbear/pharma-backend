#!/usr/bin/env python3
"""
Check the actual invoices table schema in the database
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from api.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_invoices_schema():
    """Check what columns actually exist in the invoices table"""
    try:
        # Connect to database
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # Check if invoices table exists
            table_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'invoices'
                )
            """)).scalar()
            
            if not table_exists:
                print("❌ invoices table does not exist!")
                return
            
            print("✅ invoices table exists")
            print("\n=== CURRENT INVOICES TABLE SCHEMA ===")
            
            # Get column information
            columns_result = conn.execute(text("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'invoices'
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """))
            
            print("Column Name | Data Type | Nullable | Default | Max Length")
            print("-" * 70)
            
            existing_columns = []
            for row in columns_result:
                col_name, data_type, nullable, default, max_len = row
                existing_columns.append(col_name)
                nullable_str = "YES" if nullable == "YES" else "NO"
                max_len_str = str(max_len) if max_len else "N/A"
                default_str = str(default) if default else "None"
                
                print(f"{col_name:<15} | {data_type:<12} | {nullable_str:<8} | {default_str:<15} | {max_len_str}")
            
            print("\n=== COLUMN ANALYSIS ===")
            
            # Check which columns are missing from the expected set
            expected_columns = [
                'org_id', 'invoice_number', 'order_id', 'customer_id',
                'customer_name', 'customer_gstin',
                'billing_name', 'billing_address', 'billing_city', 'billing_state', 'billing_pincode',
                'invoice_date', 'due_date',
                'gst_type', 'place_of_supply',
                'subtotal_amount', 'discount_amount', 'taxable_amount',
                'cgst_amount', 'sgst_amount', 'igst_amount', 'total_tax_amount',
                'total_amount', 'invoice_status',
                'created_at', 'updated_at'
            ]
            
            missing_columns = [col for col in expected_columns if col not in existing_columns]
            extra_columns = [col for col in existing_columns if col not in expected_columns]
            
            if missing_columns:
                print(f"❌ Missing columns: {', '.join(missing_columns)}")
            else:
                print("✅ All expected columns are present")
            
            if extra_columns:
                print(f"ℹ️  Extra columns: {', '.join(extra_columns)}")
            
            print(f"\nTotal columns in table: {len(existing_columns)}")
            
            # Show the structure needed for billing columns
            if missing_columns:
                print("\n=== SUGGESTED FIX ===")
                print("Run this SQL to add missing columns:")
                print("ALTER TABLE invoices")
                
                column_definitions = {
                    'billing_name': 'VARCHAR(200) NOT NULL DEFAULT \'\'',
                    'billing_address': 'VARCHAR(500) NOT NULL DEFAULT \'\'',
                    'billing_city': 'VARCHAR(100) NOT NULL DEFAULT \'\'',
                    'billing_state': 'VARCHAR(100) NOT NULL DEFAULT \'\'',
                    'billing_pincode': 'VARCHAR(10) NOT NULL DEFAULT \'\'',
                    'gst_type': 'VARCHAR(20) NOT NULL DEFAULT \'cgst_sgst\'',
                    'place_of_supply': 'VARCHAR(2) NOT NULL DEFAULT \'09\'',
                    'due_date': 'DATE',
                    'invoice_status': 'VARCHAR(20) DEFAULT \'generated\'',
                    'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                }
                
                for i, col in enumerate(missing_columns):
                    if col in column_definitions:
                        prefix = "ADD COLUMN" if i == 0 else ", ADD COLUMN"
                        print(f"  {prefix} {col} {column_definitions[col]}")
                
                print(";")
            
    except Exception as e:
        logger.error(f"Failed to check schema: {str(e)}")
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    check_invoices_schema()