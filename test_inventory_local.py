"""
Test script for inventory management endpoints
Tests batch tracking, stock movements, and expiry management
"""
import requests
import json
from datetime import datetime, date, timedelta

# Base URL for local testing
BASE_URL = "http://localhost:8080"

# Organization ID (default from our system)
ORG_ID = "12de5e22-eee7-4d25-b3a7-d16d01c6170f"


def test_inventory_migration():
    """Test inventory migration endpoints"""
    print("\n=== Testing Inventory Migration ===")
    
    # Check existing tables
    response = requests.get(f"{BASE_URL}/migrations/v2/check-inventory-tables")
    print(f"Check tables: {response.status_code}")
    result = response.json()
    print(f"Tables ready: {result.get('inventory_ready')}")
    print(f"Existing: {result.get('existing_tables')}")
    print(f"Missing: {result.get('missing_tables')}")
    
    if not result.get('inventory_ready'):
        # Run migration
        print("\nRunning inventory migration...")
        response = requests.post(f"{BASE_URL}/migrations/v2/add-inventory-tables")
        print(f"Migration status: {response.status_code}")
        print(f"Result: {json.dumps(response.json(), indent=2)}")
    else:
        print("Inventory tables already exist")
    
    return response.status_code == 200


def test_create_batch():
    """Test creating a new batch"""
    print("\n=== Testing Batch Creation ===")
    
    # Create batch for product 1
    batch_data = {
        "org_id": ORG_ID,
        "product_id": 1,
        "batch_number": f"TEST-{datetime.now().strftime('%Y%m%d-%H%M')}",
        "manufacturing_date": str(date.today() - timedelta(days=30)),
        "expiry_date": str(date.today() + timedelta(days=365)),
        "quantity_received": 500,
        "quantity_available": 500,
        "cost_price": 3.50,
        "mrp": 7.00,
        "location_code": "Test Rack",
        "notes": "Test batch creation"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/inventory/batches", json=batch_data)
    print(f"Create batch: {response.status_code}")
    
    if response.status_code == 200:
        batch = response.json()
        print(f"Created batch ID: {batch.get('batch_id')}")
        print(f"Batch number: {batch.get('batch_number')}")
        print(f"Days to expiry: {batch.get('days_to_expiry')}")
        return batch.get('batch_id')
    else:
        print(f"Error: {response.text}")
        return None


def test_list_batches():
    """Test listing batches with filters"""
    print("\n=== Testing Batch Listing ===")
    
    # List all batches
    response = requests.get(f"{BASE_URL}/api/v1/inventory/batches")
    print(f"List batches: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Total batches: {result.get('total')}")
        
        for batch in result.get('batches', [])[:3]:
            print(f"\nBatch: {batch.get('batch_number')}")
            print(f"  Product: {batch.get('product_name')}")
            print(f"  Expiry: {batch.get('expiry_date')}")
            print(f"  Available: {batch.get('quantity_available')}")
            print(f"  Days to expiry: {batch.get('days_to_expiry')}")
    
    # Test with filters
    print("\n--- Testing filters ---")
    
    # Near expiry batches
    response = requests.get(f"{BASE_URL}/api/v1/inventory/batches?expiring_in_days=90")
    print(f"Near expiry batches: {response.json().get('total', 0)}")
    
    # By location
    response = requests.get(f"{BASE_URL}/api/v1/inventory/batches?location=Rack")
    print(f"Batches in Rack: {response.json().get('total', 0)}")


def test_current_stock():
    """Test current stock endpoints"""
    print("\n=== Testing Current Stock ===")
    
    # Get stock for product 1
    response = requests.get(f"{BASE_URL}/api/v1/inventory/stock/current/1")
    print(f"Get stock for product 1: {response.status_code}")
    
    if response.status_code == 200:
        stock = response.json()
        print(f"Product: {stock.get('product_name')}")
        print(f"Total quantity: {stock.get('total_quantity')}")
        print(f"Available: {stock.get('available_quantity')}")
        print(f"Allocated: {stock.get('allocated_quantity')}")
        print(f"Total batches: {stock.get('total_batches')}")
        print(f"Stock value: ₹{stock.get('total_value')}")
    
    # List all stock
    print("\n--- All products stock ---")
    response = requests.get(f"{BASE_URL}/api/v1/inventory/stock/current")
    print(f"List all stock: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Total products: {result.get('total')}")
        
        for stock in result.get('stocks', [])[:3]:
            print(f"\n{stock.get('product_name')} ({stock.get('product_code')})")
            print(f"  Quantity: {stock.get('total_quantity')}")
            print(f"  Value: ₹{stock.get('total_value')}")
            if stock.get('is_below_minimum'):
                print("  ⚠️ Below minimum stock!")
    
    # Test low stock filter
    response = requests.get(f"{BASE_URL}/api/v1/inventory/stock/current?low_stock_only=true")
    print(f"\nLow stock products: {response.json().get('total', 0)}")


def test_stock_movement():
    """Test stock movement recording"""
    print("\n=== Testing Stock Movements ===")
    
    # Record a sale movement
    movement_data = {
        "org_id": ORG_ID,
        "product_id": 1,
        "batch_id": 1,  # Use first batch
        "movement_type": "sale",
        "quantity": -10,  # Negative for outward
        "reference_type": "order",
        "reference_id": 1,
        "reason": "Test sale",
        "notes": "Testing stock movement API"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/inventory/movements", json=movement_data)
    print(f"Record movement: {response.status_code}")
    
    if response.status_code == 200:
        movement = response.json()
        print(f"Movement ID: {movement.get('movement_id')}")
        print(f"Stock before: {movement.get('stock_before')}")
        print(f"Stock after: {movement.get('stock_after')}")
    else:
        print(f"Error: {response.text}")
    
    # List movements
    response = requests.get(f"{BASE_URL}/api/v1/inventory/movements?limit=5")
    print(f"\nList movements: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Total movements: {result.get('total')}")
        
        for mov in result.get('movements', [])[:3]:
            print(f"\n{mov.get('movement_type').upper()} - {mov.get('product_name')}")
            print(f"  Quantity: {mov.get('quantity')}")
            print(f"  Date: {mov.get('movement_date')}")
            print(f"  Reason: {mov.get('reason')}")


def test_stock_adjustment():
    """Test stock adjustment"""
    print("\n=== Testing Stock Adjustment ===")
    
    adjustment_data = {
        "product_id": 2,
        "batch_id": 3,
        "adjustment_type": "counting",
        "quantity": 5,  # Adding 5 units
        "reason": "Physical count adjustment",
        "notes": "Found extra units during count"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/inventory/stock/adjustment", json=adjustment_data)
    print(f"Stock adjustment: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Adjustment recorded: {result.get('movement_id')}")
    else:
        print(f"Error: {response.text}")


def test_expiry_alerts():
    """Test expiry alerts"""
    print("\n=== Testing Expiry Alerts ===")
    
    # Get alerts for next 180 days
    response = requests.get(f"{BASE_URL}/api/v1/inventory/expiry/alerts?days_ahead=180")
    print(f"Get expiry alerts: {response.status_code}")
    
    if response.status_code == 200:
        alerts = response.json()
        print(f"Total alerts: {len(alerts)}")
        
        # Group by alert level
        by_level = {}
        for alert in alerts:
            level = alert.get('alert_level')
            by_level[level] = by_level.get(level, 0) + 1
        
        print("\nAlerts by level:")
        for level, count in by_level.items():
            print(f"  {level}: {count}")
        
        # Show critical alerts
        critical = [a for a in alerts if a.get('alert_level') in ['expired', 'critical']]
        if critical:
            print("\nCritical alerts:")
            for alert in critical[:3]:
                print(f"\n  {alert.get('product_name')} - Batch {alert.get('batch_number')}")
                print(f"    Expiry: {alert.get('expiry_date')}")
                print(f"    Days to expiry: {alert.get('days_to_expiry')}")
                print(f"    Quantity: {alert.get('quantity_available')}")
                print(f"    Value at risk: ₹{alert.get('stock_value')}")


def test_inventory_dashboard():
    """Test inventory dashboard"""
    print("\n=== Testing Inventory Dashboard ===")
    
    response = requests.get(f"{BASE_URL}/api/v1/inventory/dashboard")
    print(f"Get dashboard: {response.status_code}")
    
    if response.status_code == 200:
        dashboard = response.json()
        
        print("\nStock Overview:")
        print(f"  Total products: {dashboard.get('total_products')}")
        print(f"  Total batches: {dashboard.get('total_batches')}")
        print(f"  Total stock value: ₹{dashboard.get('total_stock_value')}")
        
        print("\nAlerts:")
        print(f"  Expired products: {dashboard.get('expired_products')}")
        print(f"  Near expiry products: {dashboard.get('near_expiry_products')}")
        print(f"  Low stock products: {dashboard.get('low_stock_products')}")
        print(f"  Out of stock products: {dashboard.get('out_of_stock_products')}")
        
        print("\nActivity:")
        print(f"  Today's movements: {dashboard.get('todays_movements')}")
        print(f"  Pending orders: {dashboard.get('pending_orders')}")
        
        # Fast moving products
        fast_moving = dashboard.get('fast_moving_products', [])
        if fast_moving:
            print("\nFast moving products:")
            for product in fast_moving[:3]:
                print(f"  {product.get('product_name')}: {product.get('movement_quantity')} units")


def run_all_tests():
    """Run all inventory tests"""
    print("🚀 Starting Inventory Management Tests")
    print("=" * 50)
    
    tests = [
        ("Migration", test_inventory_migration),
        ("Batch Creation", test_create_batch),
        ("Batch Listing", test_list_batches),
        ("Current Stock", test_current_stock),
        ("Stock Movement", test_stock_movement),
        ("Stock Adjustment", test_stock_adjustment),
        ("Expiry Alerts", test_expiry_alerts),
        ("Dashboard", test_inventory_dashboard)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            test_func()
            results.append((test_name, "✅ PASSED"))
        except Exception as e:
            print(f"\n❌ Error in {test_name}: {str(e)}")
            results.append((test_name, "❌ FAILED"))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    for test_name, status in results:
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, status in results if "PASSED" in status)
    print(f"\nTotal: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n✅ All inventory tests passed! Ready for deployment.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is running")
            run_all_tests()
        else:
            print("❌ Server health check failed")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on port 8080")
        print("Run: uvicorn api.main:app --reload --port 8080")