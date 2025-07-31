"""
Test API endpoints to understand the invoice flow
"""
import requests
import json
from datetime import datetime

# Base URL (assuming the API is running on localhost:8000)
BASE_URL = "http://localhost:8000"

def test_order_47_invoice():
    """Test the old endpoint that frontend might be calling"""
    print("Testing POST /api/v1/orders/47/invoice...")
    
    url = f"{BASE_URL}/api/v1/orders/47/invoice"
    data = {
        "invoice_date": datetime.now().date().isoformat()
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

def test_new_invoice_endpoint():
    """Test the new invoice creation endpoint"""
    print("\nTesting POST /api/v1/invoices/create-with-order...")
    
    url = f"{BASE_URL}/api/v1/invoices/create-with-order"
    data = {
        "customer_id": 2,  # Using customer 2 which exists
        "items": [
            {
                "product_id": 1,
                "quantity": 10,
                "unit_price": 100.00,
                "discount_percent": 10,
                "gst_percent": 18
            }
        ],
        "payment_mode": "Credit",
        "notes": "Test invoice created via new endpoint"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def check_recent_orders():
    """Check recent orders via API"""
    print("\nChecking recent orders via API...")
    
    url = f"{BASE_URL}/api/v1/orders"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            orders = response.json()
            print(f"Total orders found: {len(orders)}")
            # Show last 5 orders
            for order in orders[-5:]:
                print(f"  Order ID: {order.get('order_id')}, Number: {order.get('order_number')}, Status: {order.get('order_status')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=== Testing Invoice API Endpoints ===\n")
    
    # First check recent orders
    check_recent_orders()
    
    # Test the problematic endpoint
    test_order_47_invoice()
    
    # Test the new endpoint
    test_new_invoice_endpoint()