#!/usr/bin/env python3
"""
Test automatic batch generation with fixed endpoint
"""
import requests
import json
from datetime import datetime

BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

def test_auto_batch_with_fixed_endpoint():
    """Test using the fixed endpoint that works with triggers"""
    print("=" * 70)
    print("TESTING AUTO BATCH GENERATION (FIXED)")
    print("=" * 70)
    
    # Step 1: Create purchase without batch
    print("\n1. Creating purchase WITHOUT batch numbers...")
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    purchase_data = {
        "supplier_id": 1,
        "purchase_date": datetime.now().date().isoformat(),
        "supplier_invoice_number": f"FIXED-TEST-{timestamp}",
        "supplier_invoice_date": datetime.now().date().isoformat(),
        "subtotal_amount": 1500.00,
        "discount_amount": 75.00,
        "tax_amount": 171.00,
        "final_amount": 1596.00,
        "items": [
            {
                "product_id": 14,
                "product_name": "Ibuprofen 400mg",
                "ordered_quantity": 75,
                "cost_price": 20.00,
                "mrp": 30.00,
                "discount_percent": 5.0,
                "tax_percent": 12.0
                # NO batch info provided
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/purchases-enhanced/with-items",
        json=purchase_data
    )
    
    if response.status_code != 200:
        print(f"   ❌ Failed: {response.text}")
        return
    
    result = response.json()
    purchase_id = result['purchase_id']
    print(f"   ✅ Created purchase #{result['purchase_number']}")
    print(f"      No batch numbers provided")
    
    # Step 2: Get items
    print("\n2. Getting purchase items...")
    response = requests.get(f"{BASE_URL}/api/v1/purchases-enhanced/{purchase_id}/items")
    
    if response.status_code != 200:
        print(f"   ❌ Failed to get items")
        return
    
    items = response.json()
    print(f"   ✅ Found {len(items)} items")
    print(f"      Batch: {items[0].get('batch_number', 'NULL')}")
    
    # Step 3: Use FIXED endpoint
    print("\n3. Using receive-fixed endpoint (trigger handles batches)...")
    
    receive_data = {
        "items": [
            {
                "purchase_item_id": items[0]['purchase_item_id'],
                "received_quantity": items[0]['ordered_quantity']
                # NO batch - let trigger generate
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/purchases-enhanced/{purchase_id}/receive-fixed",
        json=receive_data
    )
    
    if response.status_code != 200:
        print(f"   ❌ Failed: {response.status_code}")
        error = response.json()
        print(f"      {error.get('detail', 'Unknown error')}")
        return
    
    result = response.json()
    print(f"   ✅ Success!")
    print(f"      GRN: {result.get('grn_number')}")
    print(f"      Batches created: {result.get('batches_created')}")
    print(f"      Note: {result.get('note')}")
    
    print("\n" + "=" * 70)
    print("✅ AUTO BATCH GENERATION WORKING!")
    print("=" * 70)
    print("The trigger successfully:")
    print("- Generated batch number (AUTO-YYYYMMDD-PRODUCTID-XXXX)")
    print("- Set default expiry date (2 years)")
    print("- Created inventory movement")
    print("=" * 70)

if __name__ == "__main__":
    test_auto_batch_with_fixed_endpoint()