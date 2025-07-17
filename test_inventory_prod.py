"""
Test script for inventory management endpoints on production
"""
import requests
import json
from datetime import datetime, date, timedelta

# Production URL
BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

# Organization ID
ORG_ID = "12de5e22-eee7-4d25-b3a7-d16d01c6170f"


def test_inventory_migration():
    """Test inventory migration endpoints"""
    print("\n=== Testing Inventory Migration ===")
    
    # Check if tables exist
    response = requests.get(f"{BASE_URL}/migrations/v2/check-inventory-tables")
    print(f"Check tables: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Inventory ready: {result.get('inventory_ready')}")
        print(f"Batch count: {result.get('batch_count')}")
        print(f"Movement count: {result.get('movement_count')}")
        
        if not result.get('inventory_ready'):
            # Run migration
            print("\nRunning inventory migration...")
            response = requests.post(f"{BASE_URL}/migrations/v2/add-inventory-tables")
            print(f"Migration: {response.status_code}")
            if response.status_code == 200:
                print(json.dumps(response.json(), indent=2))


def test_inventory_endpoints():
    """Test main inventory endpoints"""
    print("\n=== Testing Inventory Endpoints ===")
    
    # Test batches endpoint
    response = requests.get(f"{BASE_URL}/api/v1/inventory/batches")
    print(f"GET /batches: {response.status_code}")
    
    # Test stock endpoint
    response = requests.get(f"{BASE_URL}/api/v1/inventory/stock/current")
    print(f"GET /stock/current: {response.status_code}")
    
    # Test movements endpoint
    response = requests.get(f"{BASE_URL}/api/v1/inventory/movements?limit=5")
    print(f"GET /movements: {response.status_code}")
    
    # Test expiry alerts
    response = requests.get(f"{BASE_URL}/api/v1/inventory/expiry/alerts")
    print(f"GET /expiry/alerts: {response.status_code}")
    
    # Test dashboard
    response = requests.get(f"{BASE_URL}/api/v1/inventory/dashboard")
    print(f"GET /dashboard: {response.status_code}")
    
    if response.status_code == 200:
        dashboard = response.json()
        print("\nDashboard Summary:")
        print(f"- Total products: {dashboard.get('total_products')}")
        print(f"- Total batches: {dashboard.get('total_batches')}")
        print(f"- Stock value: ₹{dashboard.get('total_stock_value')}")
        print(f"- Expired products: {dashboard.get('expired_products')}")
        print(f"- Low stock products: {dashboard.get('low_stock_products')}")


def test_create_sample_batch():
    """Create a sample batch if we have products"""
    print("\n=== Testing Sample Batch Creation ===")
    
    # First check if we have products
    response = requests.get(f"{BASE_URL}/products/")
    if response.status_code != 200 or not response.json():
        print("No products found. Skipping batch creation.")
        return
    
    products = response.json()[:3]  # Get first 3 products
    
    for i, product in enumerate(products):
        batch_data = {
            "org_id": ORG_ID,
            "product_id": product["product_id"],
            "batch_number": f"PROD-{datetime.now().strftime('%Y%m%d')}-{i+1}",
            "manufacturing_date": str(date.today() - timedelta(days=30)),
            "expiry_date": str(date.today() + timedelta(days=365)),
            "quantity_received": 100 * (i + 1),
            "quantity_available": 100 * (i + 1),
            "cost_price": float(product.get("purchase_price", 10.00)),
            "mrp": float(product.get("price", 20.00)),
            "location_code": f"Rack-{chr(65 + i)}",
            "notes": f"Production batch for {product.get('product_name')}"
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/inventory/batches", json=batch_data)
        if response.status_code == 200:
            print(f"✅ Created batch for {product.get('product_name')}")
        else:
            print(f"❌ Failed to create batch for {product.get('product_name')}: {response.status_code}")
            if response.status_code == 422:
                print(f"   Error: {response.json()}")


def main():
    """Run all production tests"""
    print("🚀 Testing Inventory Management on Production")
    print(f"URL: {BASE_URL}")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Run tests
    test_inventory_migration()
    test_inventory_endpoints()
    test_create_sample_batch()
    
    print("\n" + "=" * 60)
    print("✅ Inventory management tests completed!")
    print("\nNext steps:")
    print("1. Create sample products if needed")
    print("2. Test batch creation with actual product IDs")
    print("3. Record stock movements and adjustments")
    print("4. Monitor expiry alerts and dashboard")


if __name__ == "__main__":
    main()