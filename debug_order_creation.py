"""Debug script to check order creation issue"""
import requests
import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres.kfhlcqracxvxkqllwywd:lkiSF948fj2jf8ejfkKJ@aws-0-ap-south-1.pooler.supabase.com:6543/postgres')

def check_latest_orders():
    """Check latest orders in database"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("\n=== LATEST ORDERS ===")
    cur.execute("""
        SELECT order_id, order_number, customer_id, order_status, 
               created_at, final_amount
        FROM orders 
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    
    orders = cur.fetchall()
    for order in orders:
        print(f"Order ID: {order[0]}, Number: {order[1]}, Customer: {order[2]}, Status: {order[3]}, Created: {order[4]}, Amount: {order[5]}")
    
    print("\n=== LATEST INVOICES ===")
    cur.execute("""
        SELECT invoice_id, invoice_number, order_id, customer_id, 
               created_at, total_amount
        FROM invoices 
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    
    invoices = cur.fetchall()
    for inv in invoices:
        print(f"Invoice ID: {inv[0]}, Number: {inv[1]}, Order ID: {inv[2]}, Customer: {inv[3]}, Created: {inv[4]}, Amount: {inv[5]}")
    
    print("\n=== CHECKING ORDER-INVOICE LINKAGE ===")
    cur.execute("""
        SELECT i.invoice_number, i.order_id, o.order_number, o.order_id as actual_order_id
        FROM invoices i
        LEFT JOIN orders o ON i.order_id = o.order_id
        ORDER BY i.created_at DESC
        LIMIT 5
    """)
    
    links = cur.fetchall()
    for link in links:
        if link[3] is None:
            print(f"❌ Invoice {link[0]} has order_id {link[1]} but NO matching order found!")
        else:
            print(f"✅ Invoice {link[0]} correctly linked to Order {link[2]}")
    
    print("\n=== ORDER ITEMS DETAILS ===")
    cur.execute("""
        SELECT oi.order_id, o.order_number, p.product_name, 
               oi.quantity, oi.selling_price, oi.discount_percent, oi.total_price
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE o.order_id IN (SELECT order_id FROM orders ORDER BY created_at DESC LIMIT 3)
        ORDER BY oi.order_id DESC
    """)
    
    items = cur.fetchall()
    for item in items:
        print(f"Order {item[1]}: {item[2]} - Qty: {item[3]}, Price: {item[4]}, Discount: {item[5]}%, Total: {item[6]}")
    
    conn.close()

def test_quick_sale():
    """Test the quick-sale endpoint"""
    print("\n=== TESTING QUICK-SALE ENDPOINT ===")
    
    # Get auth token
    auth_response = requests.post(
        'https://pharma-backend-production-0c09.up.railway.app/api/v1/users/login',
        json={"email": "admin@pharma.com", "password": "admin123"}
    )
    
    if auth_response.status_code != 200:
        print(f"❌ Login failed: {auth_response.text}")
        return
        
    token = auth_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test quick-sale
    test_data = {
        "customer_id": 33,
        "items": [{
            "product_id": 1,
            "quantity": 2,
            "unit_price": 100,
            "discount_percent": 10
        }],
        "payment_mode": "cash",
        "payment_amount": 180
    }
    
    response = requests.post(
        'https://pharma-backend-production-0c09.up.railway.app/api/v1/quick-sale/',
        json=test_data,
        headers=headers
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    check_latest_orders()
    # test_quick_sale()  # Uncomment to test endpoint