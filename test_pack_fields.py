#!/usr/bin/env python3
"""Test script to debug pack field issue"""
import requests
import json
import time

# Test product data matching what frontend sends
test_product = {
    "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",
    "product_name": "Test Paracetamol Pack Fields",
    "product_code": f"TEST{str(int(time.time()))[-6:]}",
    "manufacturer": "Test Pharma",
    "hsn_code": "3004",
    "gst_percent": 12,
    "mrp": 100.0,
    "sale_price": 90.0,
    "category": "Tablet",
    "salt_composition": "Paracetamol 500mg",
    "quantity_received": 100,
    "cost_price": 70.0,
    "expiry_date": "2026-12-01",
    "base_unit": "Tablet",
    "sale_unit": "Strip",
    
    # Pack configuration - these are the fields getting lost
    "pack_input": "10*10",
    "pack_quantity": 10,
    "pack_multiplier": 10,
    "pack_unit_type": None,
    "unit_count": 10,
    "unit_measurement": None,
    "packages_per_box": 10,
    
    # Legacy fields
    "pack_type": "10*10",
    "pack_size": "10*10"
}

print("Testing product creation with pack fields...")
print(f"pack_input: {test_product['pack_input']}")
print(f"pack_quantity: {test_product['pack_quantity']}")
print(f"pack_multiplier: {test_product['pack_multiplier']}")

# Call the API
response = requests.post(
    "http://localhost:8000/api/v1/products/",
    json=test_product,
    headers={"Content-Type": "application/json"}
)

print(f"\nResponse status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"\nProduct created with ID: {result.get('product_id')}")
    print(f"\nPack config returned:")
    pack_config = result.get('pack_config', {})
    for field, value in pack_config.items():
        print(f"  {field}: {value}")
else:
    print(f"Error: {response.text}")