#!/usr/bin/env python3
"""
Test product creation with batch
"""
import requests
import json
from datetime import datetime, timedelta

API_BASE = "https://pharma-backend-production-0c09.up.railway.app"

def test_product_creation_with_batch():
    """Test creating a product with initial batch"""
    
    # Product data with quantity_received to trigger batch creation
    product_data = {
        "product_code": f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "product_name": "Test Product with Batch",
        "manufacturer": "Test Manufacturer",
        "hsn_code": "30049099",
        "gst_percent": 12,
        "mrp": 150.0,
        "sale_price": 140.0,
        "cost_price": 100.0,
        "category": "Tablet",
        "salt_composition": "Test Salt",
        "quantity_received": 100,  # This should trigger batch creation
        "expiry_date": (datetime.now() + timedelta(days=730)).strftime("%Y-%m-%d"),
        "base_unit": "Tablet",
        "sale_unit": "Strip",
        "pack_input": "10 x 10",
        "pack_quantity": 10,
        "pack_multiplier": 10,
        "pack_unit_type": "strip"
    }
    
    print("Creating product with data:")
    print(json.dumps(product_data, indent=2))
    
    # Create product
    response = requests.post(f"{API_BASE}/products/", json=product_data)
    print(f"\nResponse status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        product_id = response.json().get("product_id")
        print(f"\nProduct created with ID: {product_id}")
        
        # Check if batch was created
        print("\nChecking batches for this product...")
        batch_response = requests.get(f"{API_BASE}/api/v1/inventory/batches?product_id={product_id}")
        print(f"Batch response status: {batch_response.status_code}")
        
        if batch_response.status_code == 200:
            batches_data = batch_response.json()
            print(f"Batches found: {json.dumps(batches_data, indent=2)}")
            
            if batches_data.get("total", 0) > 0:
                print("✅ Batch was created successfully!")
            else:
                print("❌ No batch was created!")
        else:
            print(f"Error fetching batches: {batch_response.text}")
    else:
        print(f"Error creating product: {response.text}")

if __name__ == "__main__":
    test_product_creation_with_batch()