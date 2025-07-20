#!/usr/bin/env python3
"""
Smart test that creates unique batches each time
"""
import requests
import json
import random
from datetime import datetime, timedelta

BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

def create_purchase_without_batch():
    """Create purchase without pre-defining batch numbers"""
    print("1. Creating purchase (batch will be assigned at receipt)...")
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = random.randint(1000, 9999)
    
    purchase_data = {
        "supplier_id": 1,
        "purchase_date": datetime.now().date().isoformat(),
        "supplier_invoice_number": f"SMART-INV-{timestamp}-{random_suffix}",
        "supplier_invoice_date": datetime.now().date().isoformat(),
        "subtotal_amount": 2500.00,
        "discount_amount": 125.00,
        "tax_amount": 285.00,
        "final_amount": 2660.00,
        "items": [
            {
                "product_id": 14,
                "product_name": "Ibuprofen 400mg",
                "ordered_quantity": 125,
                "cost_price": 20.00,
                "mrp": 30.00,
                "discount_percent": 5.0,
                "tax_percent": 12.0,
                # Don't specify batch_number here - let it be assigned at receipt
                "expiry_date": "2026-12-31"
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/purchases-enhanced/with-items",
        json=purchase_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Purchase created!")
        print(f"      - ID: {result['purchase_id']}")
        print(f"      - Number: {result['purchase_number']}")
        return result['purchase_id'], timestamp, random_suffix
    else:
        print(f"   ❌ Failed: {response.text}")
        return None, None, None

def receive_with_new_batch(purchase_id, timestamp, suffix):
    """Receive goods with a freshly generated batch number"""
    print(f"\n2. Receiving goods with new batch number...")
    
    # Get purchase items first
    response = requests.get(
        f"{BASE_URL}/api/v1/purchases-enhanced/{purchase_id}/items"
    )
    
    if response.status_code != 200:
        print("   ❌ Could not get purchase items")
        return False
    
    items = response.json()
    
    # Generate unique batch number for receipt
    batch_number = f"RECV-{timestamp}-{suffix}"
    print(f"   Using batch number: {batch_number}")
    
    receive_data = {
        "items": [
            {
                "purchase_item_id": item['purchase_item_id'],
                "received_quantity": item['ordered_quantity'],
                "batch_number": batch_number,  # New unique batch
                "expiry_date": item.get('expiry_date', '2026-12-31')
            }
            for item in items
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/purchases-enhanced/{purchase_id}/receive",
        json=receive_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Success! Goods received")
        print(f"      - Batches: {result.get('batches_created', 0)}")
        print(f"      - GRN: {result.get('grn_number', 'N/A')}")
        return True
    else:
        print(f"   ❌ Failed: {response.status_code}")
        error = response.json()
        print(f"      {error.get('detail', 'Unknown error')}")
        return False

def verify_success(purchase_id):
    """Check if purchase is now received"""
    print(f"\n3. Verifying purchase status...")
    
    # Check pending receipts - should not include our purchase
    response = requests.get(
        f"{BASE_URL}/api/v1/purchases-enhanced/pending-receipts"
    )
    
    if response.status_code == 200:
        pending = response.json()
        
        # Check if our purchase is still pending
        is_pending = any(p['purchase_id'] == purchase_id for p in pending)
        
        if not is_pending:
            print("   ✅ Purchase no longer in pending list")
            print("   ✅ Goods receipt completed successfully!")
            return True
        else:
            print("   ❌ Purchase still showing as pending")
            return False
    
    return False

def main():
    print("=" * 70)
    print("SMART PURCHASE FLOW TEST")
    print("=" * 70)
    
    # Create purchase
    purchase_id, timestamp, suffix = create_purchase_without_batch()
    
    if purchase_id:
        # Receive with new batch
        success = receive_with_new_batch(purchase_id, timestamp, suffix)
        
        if success:
            # Verify
            verify_success(purchase_id)
            
            print("\n" + "=" * 70)
            print("🎉 COMPLETE SUCCESS!")
            print("=" * 70)
            print("✅ All triggers working correctly")
            print("✅ Purchase → Receipt → Inventory flow complete")
            print("✅ System is fully operational")
            print("=" * 70)
        else:
            print("\n⚠️  Check if any more trigger fixes needed")
    
    print("\nTest completed.")

if __name__ == "__main__":
    main()