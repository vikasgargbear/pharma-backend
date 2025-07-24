#!/usr/bin/env python3
"""
Quick fix to add inventory for Monaco product (ID: 49)
This creates a batch with available stock
"""

from datetime import datetime, timedelta
from sqlalchemy import text
from api.core.database_manager import get_database_manager
import uuid

def add_inventory_for_monaco():
    """Add inventory batch for Monaco product"""
    db_manager = get_database_manager()
    
    with db_manager.get_session() as db:
        try:
            # First, verify product exists and get its details
            product = db.execute(text("""
                SELECT product_id, product_name, mrp, org_id
                FROM products
                WHERE product_id = 49
            """)).first()
            
            if not product:
                print("❌ Product with ID 49 not found!")
                return False
                
            print(f"✅ Found product: {product.product_name} (ID: {product.product_id})")
            
            # Check existing batches
            existing = db.execute(text("""
                SELECT COUNT(*) as count, 
                       COALESCE(SUM(quantity_available), 0) as total_available
                FROM batches
                WHERE product_id = 49
            """)).first()
            
            print(f"📊 Existing batches: {existing.count}, Total available: {existing.total_available}")
            
            # Create a new batch with stock
            batch_data = {
                'org_id': product.org_id,
                'product_id': 49,
                'batch_number': f'STOCK-FIX-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
                'expiry_date': datetime.now() + timedelta(days=365),  # 1 year expiry
                'quantity_received': 100,  # Add 100 units
                'quantity_available': 100,
                'quantity_sold': 0,
                'quantity_damaged': 0,
                'quantity_returned': 0,
                'cost_price': float(product.mrp) * 0.7,  # 70% of MRP as cost
                'selling_price': float(product.mrp) * 0.9,  # 90% of MRP as selling
                'mrp': product.mrp,
                'batch_status': 'active',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Insert the batch
            db.execute(text("""
                INSERT INTO batches (
                    org_id, product_id, batch_number, expiry_date,
                    quantity_received, quantity_available, quantity_sold,
                    quantity_damaged, quantity_returned,
                    cost_price, selling_price, mrp,
                    batch_status, created_at, updated_at
                ) VALUES (
                    :org_id, :product_id, :batch_number, :expiry_date,
                    :quantity_received, :quantity_available, :quantity_sold,
                    :quantity_damaged, :quantity_returned,
                    :cost_price, :selling_price, :mrp,
                    :batch_status, :created_at, :updated_at
                )
            """), batch_data)
            
            db.commit()
            
            print(f"✅ Successfully added batch with 100 units for Monaco!")
            print(f"   Batch number: {batch_data['batch_number']}")
            print(f"   Expiry date: {batch_data['expiry_date'].strftime('%Y-%m-%d')}")
            
            # Verify the stock is now available
            new_stock = db.execute(text("""
                SELECT COALESCE(SUM(quantity_available), 0) as total_stock
                FROM batches
                WHERE product_id = 49
                    AND (expiry_date IS NULL OR expiry_date > CURRENT_DATE)
            """)).scalar()
            
            print(f"📦 Total available stock for Monaco: {new_stock} units")
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding inventory: {e}")
            db.rollback()
            return False

if __name__ == "__main__":
    print("🔧 Fixing inventory for Monaco product...")
    success = add_inventory_for_monaco()
    
    if success:
        print("\n✅ Inventory fix completed successfully!")
        print("You should now be able to create invoices for Monaco.")
    else:
        print("\n❌ Inventory fix failed. Please check the error messages above.")