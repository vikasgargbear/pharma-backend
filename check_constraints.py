#!/usr/bin/env python3
"""
Check what values are allowed in the invoice_status check constraint
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.database import get_db
from sqlalchemy import text

def check_invoice_status_constraint():
    """Check the invoice_status check constraint"""
    
    # Get database connection
    db = next(get_db())
    
    try:
        print("🔍 Checking invoice_status constraint...")
        
        # Get constraint definition
        constraint_sql = """
        SELECT 
            conname as constraint_name,
            pg_get_constraintdef(oid) as constraint_definition
        FROM pg_constraint 
        WHERE conname LIKE '%invoice_status%' OR conname LIKE '%check_invoice_status%'
        """
        
        constraints = db.execute(text(constraint_sql)).fetchall()
        
        print(f"\n📋 Found {len(constraints)} constraints:")
        for constraint in constraints:
            print(f"   ✓ {constraint.constraint_name}: {constraint.constraint_definition}")
        
        # Also check the table definition
        print("\n🔍 Checking invoices table structure...")
        table_sql = """
        SELECT 
            column_name,
            data_type,
            column_default,
            is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'invoices' 
        AND column_name IN ('invoice_status', 'payment_status')
        ORDER BY column_name;
        """
        
        columns = db.execute(text(table_sql)).fetchall()
        
        print(f"\n📋 Status columns in invoices table:")
        for col in columns:
            print(f"   ✓ {col.column_name} ({col.data_type}) - Default: {col.column_default}")
        
    except Exception as e:
        print(f"❌ Error checking constraints: {str(e)}")
    
    finally:
        db.close()

if __name__ == "__main__":
    check_invoice_status_constraint()