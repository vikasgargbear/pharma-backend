#!/usr/bin/env python3
"""Test script to verify batch creation works after fixing the Batch model"""

import requests
import json
from datetime import datetime, date, timedelta

BASE_URL = "http://localhost:8000"

def test_product_creation_with_batch():
    """Test creating a product with quantity and expiry date to trigger batch creation"""
    print("Testing product creation with batch...")
    
    # Sample product data with quantity and expiry to trigger batch creation
    product_data = {
        "product_name": "Test Batch Medicine",
        "product_code": f"BATCH_TEST_{int(datetime.now().timestamp())}",
        "manufacturer": "Test Pharma Batch",
        "hsn_code": "30049099",
        "category": "Tablet",
        "salt_composition": "Paracetamol 500mg",
        "mrp": 100.00,
        "sale_price": 90.00,
        "cost_price": 70.00,
        "gst_percent": 12,
        "base_unit": "Tablet",
        "sale_unit": "Strip",
        # These fields should trigger batch creation
        "quantity_received": 100,
        "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
        
        # Pack fields
        "pack_input": "10*10",
        "pack_quantity": 10,
        "pack_multiplier": 10,
        "pack_unit_type": None,
        "unit_count": 10,
        "unit_measurement": None,
        "packages_per_box": 10
    }
    
    try:
        # Create the product
        url = f"{BASE_URL}/products/"
        response = requests.post(url, json=product_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Product created successfully!")
            print(f"   Product ID: {result.get('product_id')}")
            print(f"   Product Name: {result.get('product_name')}")
            print(f"   Message: {result.get('message', 'No message')}")
            
            # Check if batch was created by querying products with batch info
            product_id = result.get('product_id')
            if product_id:
                return test_batch_info(product_id, result.get('product_name'))
            
            return True
        else:
            print(f"❌ Product creation failed!")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating product: {str(e)}")
        return False

def test_batch_info(product_id, product_name):
    """Check if batch information is available for the created product"""
    print(f"\nChecking batch info for product {product_id}...")
    
    try:
        # Get products with batch info
        url = f"{BASE_URL}/products/?include_batch_info=true"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            products = response.json()
            
            # Find our product
            our_product = None
            for product in products:
                if product.get('product_id') == product_id:
                    our_product = product
                    break
            
            if our_product:
                batch_count = our_product.get('batch_count', 0)
                total_stock = our_product.get('total_stock', 0)
                
                print(f"✅ Product found in batch query!")
                print(f"   Batch Count: {batch_count}")
                print(f"   Total Stock: {total_stock}")
                
                if batch_count > 0 and total_stock > 0:
                    print("✅ Batch creation appears successful!")
                    return True
                else:
                    print("⚠️  Product found but no batch information available")
                    return False
            else:
                print("❌ Product not found in batch query")
                return False
        else:
            print(f"❌ Failed to query products with batch info")
            print(f"   Status Code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking batch info: {str(e)}")
        return False

def main():
    """Run the batch creation test"""
    print("Batch Creation Test")
    print("=" * 50)
    
    success = test_product_creation_with_batch()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Batch creation test PASSED!")
        print("The updated Batch model works correctly.")
    else:
        print("❌ Batch creation test FAILED!")
        print("Check the server logs for more details.")

if __name__ == "__main__":
    main()