#!/usr/bin/env python3
"""
Debug script to check why Order 46 is not found
"""

from sqlalchemy import text
from api.core.database_manager import get_database_manager

def check_order_46():
    """Check the status of order 46"""
    db_manager = get_database_manager()
    
    with db_manager.get_session() as db:
        print("🔍 Checking Order 46...\n")
        
        # Check if order exists at all
        order = db.execute(text("""
            SELECT order_id, org_id, customer_id, order_status, 
                   created_at, final_amount
            FROM orders
            WHERE order_id = 46
        """)).first()
        
        if not order:
            print("❌ Order 46 does not exist in the database!")
            
            # Check latest orders to see what IDs exist
            latest = db.execute(text("""
                SELECT order_id, created_at, order_status
                FROM orders
                ORDER BY order_id DESC
                LIMIT 5
            """)).fetchall()
            
            print("\n📋 Latest orders in the system:")
            for o in latest:
                print(f"   Order #{o.order_id} - {o.order_status} - Created: {o.created_at}")
                
        else:
            print(f"✅ Order 46 exists!")
            print(f"   Org ID: {order.org_id}")
            print(f"   Customer ID: {order.customer_id}")
            print(f"   Status: {order.order_status}")
            print(f"   Amount: {order.final_amount}")
            print(f"   Created: {order.created_at}")
            
            # Check if it's an org_id mismatch
            if str(order.org_id) != "12de5e22-eee7-4d25-b3a7-d16d01c6170f":
                print(f"\n⚠️  Order has different org_id: {order.org_id}")
                print("   Default org_id: 12de5e22-eee7-4d25-b3a7-d16d01c6170f")
                
            # Check if invoice already exists for this order
            invoice = db.execute(text("""
                SELECT invoice_number, created_at, total_amount
                FROM invoices
                WHERE order_id = :order_id
            """), {"order_id": 46}).first()
            
            if invoice:
                print(f"\n📄 Invoice already exists for this order!")
                print(f"   Invoice Number: {invoice.invoice_number}")
                print(f"   Total: {invoice.total_amount}")
                print(f"   Created: {invoice.created_at}")

if __name__ == "__main__":
    check_order_46()