#!/usr/bin/env python3
"""
Debug why Order 47 is being referenced
"""

from sqlalchemy import text
from api.core.database_manager import get_database_manager

def debug_order_issue():
    """Debug the order 47 issue"""
    db_manager = get_database_manager()
    
    with db_manager.get_session() as db:
        print("🔍 Debugging Order System...\n")
        
        # Check current order sequence
        sequence_value = db.execute(text("""
            SELECT last_value, is_called 
            FROM orders_order_id_seq
        """)).first()
        
        print(f"📊 Database Sequence Status:")
        print(f"   Last value: {sequence_value.last_value}")
        print(f"   Is called: {sequence_value.is_called}")
        print(f"   Next order ID will be: {sequence_value.last_value + 1 if sequence_value.is_called else sequence_value.last_value}")
        
        # Check actual orders
        print(f"\n📋 Actual Orders in Database:")
        orders = db.execute(text("""
            SELECT order_id, order_status, created_at, customer_id, final_amount
            FROM orders
            WHERE order_id >= 40
            ORDER BY order_id DESC
            LIMIT 10
        """)).fetchall()
        
        for order in orders:
            print(f"   Order #{order.order_id} - Status: {order.order_status} - Amount: {order.final_amount} - Created: {order.created_at}")
        
        # Check for gaps
        print(f"\n⚠️  Missing Order IDs:")
        all_ids = [o.order_id for o in orders]
        if all_ids:
            for i in range(min(all_ids), max(all_ids) + 1):
                if i not in all_ids:
                    print(f"   Order #{i} is missing")
        
        # Check latest invoices
        print(f"\n📄 Latest Invoices:")
        invoices = db.execute(text("""
            SELECT invoice_id, invoice_number, order_id, created_at
            FROM invoices
            ORDER BY invoice_id DESC
            LIMIT 5
        """)).fetchall()
        
        for inv in invoices:
            print(f"   Invoice {inv.invoice_number} - Order ID: {inv.order_id} - Created: {inv.created_at}")
        
        # The real issue
        print(f"\n❗ THE ISSUE:")
        print("   1. Frontend is trying to create invoice for Order #47")
        print("   2. Order #47 doesn't exist (was never created)")
        print("   3. Database sequence is at 47, so next order will be #48")
        print("   4. Orders #46 and #47 likely failed during creation")
        print("\n💡 SOLUTION:")
        print("   Frontend should use: POST /api/v1/invoices/create-with-order")
        print("   This creates both order AND invoice in one transaction")

if __name__ == "__main__":
    debug_order_issue()