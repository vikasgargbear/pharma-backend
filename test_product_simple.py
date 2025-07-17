"""
Simple test to verify product creation works
"""
import requests
import json
from datetime import datetime

BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"
ORG_ID = "12de5e22-eee7-4d25-b3a7-d16d01c6170f"

def test_create_product():
    """Test creating a product with minimal fields"""
    
    # Generate unique product code
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    product_code = f"TEST{timestamp}"
    
    product_data = {
        "org_id": ORG_ID,
        "product_code": product_code,
        "product_name": f"Test Product {timestamp}",
        "hsn_code": "30049099",
        "mrp": 100.50,
        "gst_percent": 12.0
    }
    
    print(f"Creating product with code: {product_code}")
    print(f"Request data: {json.dumps(product_data, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/products/",
        json=product_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nResponse status: {response.status_code}")
    
    try:
        result = response.json()
        print(f"Response data: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print("\n✅ Product created successfully!")
            return result
        else:
            print(f"\n❌ Error: {result.get('detail', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Failed to parse response: {e}")
        print(f"Raw response: {response.text}")
    
    return None

def test_list_products():
    """Test listing products"""
    print("\n--- Testing Product List ---")
    
    response = requests.get(f"{BASE_URL}/products/")
    
    print(f"Response status: {response.status_code}")
    
    try:
        result = response.json()
        if isinstance(result, list):
            print(f"Found {len(result)} products")
            if result:
                print(f"First product: {json.dumps(result[0], indent=2)}")
        else:
            print(f"Response: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
        print(f"Raw response: {response.text}")

if __name__ == "__main__":
    # Test product creation
    created_product = test_create_product()
    
    # Test product listing
    test_list_products()