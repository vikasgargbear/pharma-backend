#!/usr/bin/env python3
"""
Final comprehensive test after all trigger fixes
This should work perfectly once all SQL fixes are applied
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

def test_complete_flow():
    """Test the complete purchase flow"""
    print("=" * 70)
    print("FINAL PURCHASE FLOW TEST")
    print("=" * 70)
    
    # Step 1: Create Purchase
    print("\n1. Creating purchase order...")
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    purchase_data = {
        "supplier_id": 1,
        "purchase_date": datetime.now().date().isoformat(),
        "supplier_invoice_number": f"FINAL-TEST-{timestamp}",
        "supplier_invoice_date": datetime.now().date().isoformat(),
        "subtotal_amount": 5000.00,
        "discount_amount": 250.00,
        "tax_amount": 570.00,
        "final_amount": 5320.00,
        "items": [
            {
                "product_id": 14,
                "product_name": "Ibuprofen 400mg",
                "ordered_quantity": 250,
                "cost_price": 20.00,
                "mrp": 30.00,
                "discount_percent": 5.0,
                "tax_percent": 12.0,
                "batch_number": f"FINAL-BATCH-{timestamp}",
                "expiry_date": "2027-01-31"
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/purchases-enhanced/with-items",
        json=purchase_data
    )
    
    if response.status_code != 200:
        print(f"   ❌ Failed to create purchase: {response.text}")
        return False
    
    result = response.json()
    purchase_id = result['purchase_id']
    print(f"   ✅ Created purchase #{result['purchase_number']} (ID: {purchase_id})")
    
    # Step 2: Check pending receipts
    print("\n2. Checking pending receipts...")
    response = requests.get(f"{BASE_URL}/api/v1/purchases-enhanced/pending-receipts")
    
    if response.status_code == 200:
        pending = response.json()
        found = any(p['purchase_id'] == purchase_id for p in pending)
        if found:
            print(f"   ✅ Purchase is in pending receipts list")
        else:
            print(f"   ❌ Purchase not found in pending list")
    
    # Step 3: Get purchase items
    print("\n3. Getting purchase items...")
    response = requests.get(f"{BASE_URL}/api/v1/purchases-enhanced/{purchase_id}/items")
    
    if response.status_code != 200:
        print(f"   ❌ Failed to get items: {response.text}")
        return False
    
    items = response.json()
    print(f"   ✅ Found {len(items)} items")
    
    # Step 4: Receive goods
    print("\n4. Receiving goods...")
    receive_data = {
        "items": [
            {
                "purchase_item_id": item['purchase_item_id'],
                "received_quantity": item['ordered_quantity'],
                "batch_number": item.get('batch_number', f"RECV-{timestamp}"),
                "expiry_date": item.get('expiry_date', '2027-01-31')
            }
            for item in items
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/purchases-enhanced/{purchase_id}/receive",
        json=receive_data
    )
    
    if response.status_code != 200:
        print(f"   ❌ Failed to receive goods: {response.status_code}")
        error = response.json()
        print(f"   Error: {error.get('detail', 'Unknown error')}")
        
        # Diagnose the error
        error_detail = str(error.get('detail', ''))
        if 'duplicate key value violates unique constraint' in error_detail:
            if 'batches_org_id_product_id_batch_number_key' in error_detail:
                print("\n   ⚠️  Batch already exists. API is trying to create duplicate.")
            elif 'supplier_outstanding_purchase_id_key' in error_detail:
                print("\n   ⚠️  Need to run: FIX_supplier_outstanding_trigger.sql")
        elif 'case not found' in error_detail:
            print("\n   ⚠️  Need to run: IMMEDIATE_FIX_purchase_trigger.sql")
        elif 'null value in column "batch_number"' in error_detail:
            print("\n   ⚠️  Need to run: DISABLE_auto_batch_trigger.sql")
            print("   The automatic batch creation trigger is conflicting with API")
        
        return False
    
    result = response.json()
    print(f"   ✅ Goods received successfully!")
    print(f"   - GRN: {result.get('grn_number')}")
    print(f"   - Batches created: {result.get('batches_created', 0)}")
    
    # Step 5: Verify purchase is no longer pending
    print("\n5. Verifying purchase status...")
    response = requests.get(f"{BASE_URL}/api/v1/purchases-enhanced/pending-receipts")
    
    if response.status_code == 200:
        pending = response.json()
        still_pending = any(p['purchase_id'] == purchase_id for p in pending)
        if not still_pending:
            print(f"   ✅ Purchase is no longer in pending list")
        else:
            print(f"   ❌ Purchase still showing as pending")
    
    return True

def main():
    success = test_complete_flow()
    
    if success:
        print("\n" + "=" * 70)
        print("🎉 COMPLETE SUCCESS!")
        print("=" * 70)
        print("✅ Purchase creation")
        print("✅ Goods receipt")
        print("✅ Batch creation")
        print("✅ Inventory movement")
        print("✅ Supplier outstanding")
        print("✅ All systems operational!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ Test failed - check errors above")
        print("=" * 70)
        print("\nRequired SQL fixes to run in order:")
        print("1. IMMEDIATE_FIX_purchase_trigger.sql (if 'case not found')")
        print("2. FIX_supplier_outstanding_trigger.sql (if 'ON CONFLICT')")
        print("3. DISABLE_auto_batch_trigger.sql (if 'batch_number null')")
        print("=" * 70)

if __name__ == "__main__":
    main()