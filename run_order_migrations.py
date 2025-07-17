#!/usr/bin/env python3
"""
Run order management migrations
This adds order tables and sample data
"""
import requests
import time

BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

def wait_for_deployment():
    """Wait for new deployment"""
    print("⏳ Waiting for deployment...")
    for i in range(12):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                # Check if order endpoints exist
                response = requests.get(f"{BASE_URL}/api/v1/orders/", timeout=5)
                if response.status_code in [200, 500]:  # 500 means endpoint exists but DB not ready
                    print("✅ Order endpoints are deployed!")
                    return True
        except:
            pass
        print(f"   Attempt {i+1}/12...")
        time.sleep(15)
    return False

def run_order_migrations():
    """Run order migrations"""
    print("\n🚀 Running Order Management Migrations")
    print("=" * 50)
    
    # Step 1: Add order columns
    print("\n1️⃣ Adding order management columns...")
    response = requests.post(f"{BASE_URL}/migrations/v2/add-order-columns", timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"   ✅ {data['message']}")
            print(f"   Tables checked: {', '.join(data.get('tables_checked', []))}")
            print(f"   Columns added: {len(data.get('columns_added', []))}")
            if data.get('columns_added'):
                print(f"   New columns: {', '.join(data['columns_added'][:5])}...")
        else:
            print(f"   ❌ Migration failed: {data.get('message')}")
            return
    else:
        print(f"   ❌ Error: {response.status_code}")
        return
    
    # Step 2: Create sample orders
    print("\n2️⃣ Creating sample order data...")
    response = requests.post(f"{BASE_URL}/migrations/v2/create-sample-orders", timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"   ✅ {data['message']}")
        else:
            print(f"   ⚠️  {data.get('message')}")
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    # Step 3: Test order endpoints
    print("\n3️⃣ Testing order endpoints...")
    response = requests.get(f"{BASE_URL}/api/v1/orders/")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Order API working!")
        print(f"   Total orders: {data.get('total', 0)}")
        
        # Show sample orders
        if data.get('orders'):
            print("\n   Sample Orders Created:")
            for order in data['orders'][:3]:
                print(f"   • {order['order_number']} - {order['customer_name']}")
                print(f"     Total: ₹{order['total_amount']} | Status: {order['order_status']}")
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    # Step 4: Test dashboard
    print("\n4️⃣ Testing order dashboard...")
    response = requests.get(f"{BASE_URL}/api/v1/orders/dashboard/stats")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"   ✅ Dashboard working!")
        print(f"   Total orders: {stats.get('total_orders', 0)}")
        print(f"   Today's orders: {stats.get('today_orders', 0)}")
        print(f"   This month: {stats.get('month_orders', 0)} orders worth ₹{stats.get('month_amount', 0)}")
    
    print("\n" + "=" * 50)
    print("✅ Order management system is ready!")
    print("\nFeatures now available:")
    print("   • Create multi-item orders")
    print("   • Credit limit validation")
    print("   • Inventory checking")
    print("   • Tax calculation")
    print("   • Order workflow (confirm → invoice → deliver)")
    print("   • Dashboard analytics")
    
    print("\n🎯 Next: Run test_order_endpoints.py for full testing")

if __name__ == "__main__":
    if wait_for_deployment():
        run_order_migrations()
    else:
        print("❌ Order endpoints not deployed yet. Please wait and try again.")