#!/usr/bin/env python3
"""
Test script for order management endpoints
"""
import requests
import json
from datetime import date, datetime
from decimal import Decimal

# Base URL - change to local for local testing
# BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"
BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

def test_order_endpoints():
    """Test all order endpoints"""
    print("🧪 Testing Order Management Endpoints")
    print("=" * 50)
    
    # 1. List orders
    print("\n1. List orders:")
    response = requests.get(f"{BASE_URL}/api/v1/orders/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total orders: {data.get('total', 0)}")
        if data.get('orders'):
            print(f"First order: {data['orders'][0]['order_number']}")
    else:
        print(f"Error: {response.text[:200]}...")
    
    # 2. Get order dashboard
    print("\n2. Order dashboard:")
    response = requests.get(f"{BASE_URL}/api/v1/orders/dashboard/stats")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print(f"Total orders: {stats.get('total_orders', 0)}")
        print(f"Pending: {stats.get('pending_orders', 0)}")
        print(f"Today's orders: {stats.get('today_orders', 0)}")
    
    # 3. Create an order
    print("\n3. Create new order:")
    
    # First get a customer ID
    cust_response = requests.get(f"{BASE_URL}/customers-simple/")
    if cust_response.status_code == 200 and cust_response.json().get('customers'):
        customer_id = cust_response.json()['customers'][0]['customer_id']
        print(f"Using customer ID: {customer_id}")
        
        # Get some products
        prod_response = requests.get(f"{BASE_URL}/products/")
        if prod_response.status_code == 200:
            products = prod_response.json()
            if products and len(products) > 0:
                # Create order with 2 products
                order_data = {
                    "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",
                    "customer_id": customer_id,
                    "order_date": str(date.today()),
                    "delivery_date": str(date.today()),
                    "order_type": "sales",
                    "payment_terms": "credit",
                    "items": [
                        {
                            "product_id": products[0]['product_id'],
                            "quantity": 10,
                            "unit_price": float(products[0].get('mrp', 100)),
                            "discount_percent": 5.0,
                            "discount_amount": 0,
                            "tax_percent": float(products[0].get('gst_percent', 12)),
                            "tax_amount": 0
                        }
                    ]
                }
                
                if len(products) > 1:
                    order_data["items"].append({
                        "product_id": products[1]['product_id'],
                        "quantity": 5,
                        "unit_price": float(products[1].get('mrp', 200)),
                        "discount_percent": 0,
                        "discount_amount": 0,
                        "tax_percent": float(products[1].get('gst_percent', 12)),
                        "tax_amount": 0
                    })
                
                response = requests.post(
                    f"{BASE_URL}/api/v1/orders/",
                    json=order_data
                )
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    order = response.json()
                    print(f"✅ Created order: {order['order_number']}")
                    print(f"   Total: ₹{order['total_amount']}")
                    return order['order_id']
                else:
                    print(f"❌ Error: {response.text[:200]}...")
    
    # 4. Get specific order
    if 'order' in locals() and response.status_code == 200:
        order_id = order['order_id']
        print(f"\n4. Get order {order_id}:")
        response = requests.get(f"{BASE_URL}/api/v1/orders/{order_id}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            order_details = response.json()
            print(f"Order: {order_details['order_number']}")
            print(f"Customer: {order_details['customer_name']}")
            print(f"Items: {len(order_details['items'])}")
            print(f"Status: {order_details['order_status']}")
        
        # 5. Confirm order
        print(f"\n5. Confirm order {order_id}:")
        response = requests.put(f"{BASE_URL}/api/v1/orders/{order_id}/confirm")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Order confirmed")
        
        # 6. Generate invoice
        print(f"\n6. Generate invoice for order {order_id}:")
        invoice_data = {
            "invoice_date": str(date.today()),
            "print_copy": False,
            "send_email": False
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/orders/{order_id}/invoice",
            json=invoice_data
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            invoice = response.json()
            print(f"✅ Invoice created: {invoice.get('invoice_number')}")
    
    print("\n✅ Order endpoint tests completed!")

def test_order_migrations():
    """Run order migrations first"""
    print("\n🔧 Running Order Migrations")
    print("=" * 50)
    
    # 1. Add order columns
    print("\n1. Adding order columns...")
    response = requests.post(f"{BASE_URL}/migrations/v2/add-order-columns")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"✅ {result.get('message')}")
            print(f"   Columns added: {len(result.get('columns_added', []))}")
    
    # 2. Create sample orders
    print("\n2. Creating sample orders...")
    response = requests.post(f"{BASE_URL}/migrations/v2/create-sample-orders")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result.get('message')}")

if __name__ == "__main__":
    # Run migrations first if needed
    # test_order_migrations()
    
    # Test endpoints
    test_order_endpoints()