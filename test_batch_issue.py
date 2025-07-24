#!/usr/bin/env python3
"""
Test script to investigate batch creation issue
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from api.core.config import settings
import json

def check_batch_creation():
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        print("=== Checking Chai Products ===")
        result = conn.execute(text("""
            SELECT product_id, product_name, product_code, created_at
            FROM products
            WHERE product_name ILIKE '%chai%'
            ORDER BY created_at DESC
            LIMIT 5
        """))
        
        products = []
        for row in result:
            products.append({
                'id': row.product_id,
                'name': row.product_name,
                'code': row.product_code,
                'created': str(row.created_at)
            })
            print(f"Product: {row.product_name} (ID: {row.product_id}, Code: {row.product_code})")
        
        if not products:
            print("No Chai products found!")
            return
            
        print("\n=== Checking Batches for These Products ===")
        product_ids = [p['id'] for p in products]
        
        result = conn.execute(text("""
            SELECT b.batch_id, b.batch_number, b.product_id, b.quantity_available, 
                   b.quantity_received, b.org_id, b.created_at, p.product_name
            FROM batches b
            JOIN products p ON b.product_id = p.product_id
            WHERE b.product_id = ANY(:product_ids)
            ORDER BY b.created_at DESC
        """), {"product_ids": product_ids})
        
        batch_count = 0
        for row in result:
            batch_count += 1
            print(f"\nBatch found:")
            print(f"  - Batch Number: {row.batch_number}")
            print(f"  - Product: {row.product_name}")
            print(f"  - Quantity Available: {row.quantity_available}")
            print(f"  - Quantity Received: {row.quantity_received}")
            print(f"  - Org ID: {row.org_id}")
            print(f"  - Created: {row.created_at}")
        
        if batch_count == 0:
            print("❌ No batches found for any Chai products!")
            
            # Check if there are ANY batches in the system
            print("\n=== Checking Total Batches in System ===")
            result = conn.execute(text("SELECT COUNT(*) as count FROM batches"))
            total_batches = result.scalar()
            print(f"Total batches in system: {total_batches}")
            
            if total_batches > 0:
                # Show some sample batches
                print("\n=== Sample Batches ===")
                result = conn.execute(text("""
                    SELECT b.batch_number, p.product_name, b.quantity_available, b.created_at
                    FROM batches b
                    JOIN products p ON b.product_id = p.product_id
                    ORDER BY b.created_at DESC
                    LIMIT 5
                """))
                for row in result:
                    print(f"Batch: {row.batch_number} - {row.product_name} (Qty: {row.quantity_available})")
        
        # Check if the inventory table has any entries for Chai products
        print("\n=== Checking Inventory Table ===")
        result = conn.execute(text("""
            SELECT i.batch_number, i.current_stock, p.product_name
            FROM inventory i
            JOIN products p ON i.product_id = p.product_id
            WHERE p.product_name ILIKE '%chai%'
        """))
        
        inv_count = 0
        for row in result:
            inv_count += 1
            print(f"Inventory: Batch {row.batch_number} - {row.product_name} (Stock: {row.current_stock})")
            
        if inv_count == 0:
            print("No inventory entries found for Chai products")

if __name__ == "__main__":
    check_batch_creation()