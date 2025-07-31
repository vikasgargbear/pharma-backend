#!/usr/bin/env python3
"""
Test the proper order-to-invoice flow
Shows how frontend should handle order IDs
"""

import json
from datetime import datetime
from sqlalchemy import text
from api.core.database_manager import get_database_manager

def test_proper_flow():
    """Demonstrate the proper order creation and invoice flow"""
    db_manager = get_database_manager()
    
    with db_manager.get_session() as db:
        print("🔍 Testing Proper Order-Invoice Flow\n")
        
        # Step 1: Check current state
        latest_order = db.execute(text("""
            SELECT MAX(order_id) as max_id FROM orders
        """)).scalar()
        
        print(f"📊 Current State:")
        print(f"   Latest order ID in database: {latest_order}")
        
        # Step 2: Simulate order creation (what backend returns)
        print(f"\n📝 Step 1: Frontend creates order")
        print("   POST /api/v1/orders/")
        print("   Request body: { customer_id: 1, items: [...] }")
        
        # Backend would return something like:
        mock_response = {
            "order_id": 45,  # This is what backend returns!
            "order_number": "ORD000045",
            "customer_name": "Test Customer",
            "order_status": "pending",
            "total_amount": 1000.00
        }
        
        print(f"\n   ✅ Backend Response:")
        print(f"   {json.dumps(mock_response, indent=4)}")
        
        print(f"\n⚠️  IMPORTANT: Frontend should store this order_id: {mock_response['order_id']}")
        
        # Step 3: Generate invoice
        print(f"\n📄 Step 2: Frontend generates invoice")
        print(f"   POST /api/v1/orders/{mock_response['order_id']}/invoice")
        print(f"   Using order_id from backend response: {mock_response['order_id']}")
        
        # What's happening wrong:
        print(f"\n❌ What Frontend is Doing Wrong:")
        print("   1. Frontend creates order")
        print("   2. Backend returns order_id: 45")
        print("   3. Frontend ignores this and uses: 46, 47, 48...")
        print("   4. These orders don't exist!")
        
        # The fix:
        print(f"\n✅ The Correct Flow:")
        print("   1. Create order: POST /api/v1/orders/")
        print("   2. Store the returned order_id from response")
        print("   3. Use THAT order_id for invoice: POST /api/v1/orders/{order_id}/invoice")
        print("   4. Never guess or increment order IDs locally!")
        
        # Check sequence
        seq = db.execute(text("""
            SELECT last_value FROM orders_order_id_seq
        """)).scalar()
        
        print(f"\n📈 Database Sequence Info:")
        print(f"   Current sequence value: {seq}")
        print(f"   Next order will get ID: {seq + 1}")
        print(f"   Gap explanation: Orders 46, 47, 48 were attempted but rolled back")

def show_proper_frontend_code():
    """Show how frontend should handle this"""
    print("\n" + "="*60)
    print("💻 Proper Frontend Code Example:")
    print("="*60)
    
    code = '''
// ❌ WRONG - Don't do this:
let nextOrderId = lastOrderId + 1;  // Guessing!
await api.post(`/orders/${nextOrderId}/invoice`);

// ✅ CORRECT - Do this:
// Step 1: Create order
const orderResponse = await api.post('/api/v1/orders/', {
    customer_id: customerId,
    items: orderItems
});

// Step 2: Store the ACTUAL order ID from response
const orderId = orderResponse.data.order_id;  // Use what backend returns!
console.log('Order created with ID:', orderId);

// Step 3: Generate invoice using the REAL order ID
const invoiceResponse = await api.post(`/api/v1/orders/${orderId}/invoice`, {
    invoice_date: new Date()
});

// Alternative: Use the combined endpoint
const response = await api.post('/api/v1/invoices/create-with-order', {
    customer_id: customerId,
    items: orderItems
});
// This creates both order and invoice together
'''
    
    print(code)

if __name__ == "__main__":
    test_proper_flow()
    show_proper_frontend_code()