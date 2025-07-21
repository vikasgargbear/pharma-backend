#!/usr/bin/env python3
"""
Quick test for goods receipt functionality
Tests if the purchase trigger has been updated
"""
import requests
import json

BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

def test_goods_receipt():
    """Test receiving items for purchase ID 2"""
    print("Testing Goods Receipt for Purchase ID 2...")
    
    # Prepare receive data for the existing purchase
    receive_data = {
        "items": [
            {
                "purchase_item_id": 1,  # From the test purchase we created
                "received_quantity": 200,
                "batch_number": "DEMO-BATCH-001",
                "expiry_date": "2027-06-30"
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/purchases-enhanced/2/receive",
        json=receive_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESS! Items received successfully!")
        print(f"   - Batches created: {result.get('batches_created', 0)}")
        print(f"   - GRN #: {result.get('grn_number', 'N/A')}")
        print("\nThe purchase trigger has been updated correctly!")
        return True
    else:
        error_detail = response.json().get('detail', 'Unknown error')
        if 'case not found' in error_detail:
            print("❌ FAILED - Trigger not updated yet")
            print("\nPlease run this SQL in Supabase SQL Editor:")
            print("=" * 60)
            print("-- Copy from IMMEDIATE_FIX_purchase_trigger.sql")
            print("=" * 60)
        else:
            print(f"❌ Different error: {error_detail}")
        return False

def check_pending_receipts():
    """Check current pending receipts"""
    print("\nChecking pending receipts...")
    
    response = requests.get(
        f"{BASE_URL}/api/v1/purchases-enhanced/pending-receipts"
    )
    
    if response.status_code == 200:
        pending = response.json()
        print(f"Found {len(pending)} pending purchases")
        
        # Find our test purchase
        for p in pending:
            if p['purchase_id'] == 2:
                print(f"\n✓ Purchase #{p['purchase_number']} is pending receipt")
                print(f"  Supplier: {p['supplier_name']}")
                print(f"  Total: ₹{p['final_amount']}")
                return True
        
        print("\n⚠️  Purchase ID 2 not found in pending receipts")
        print("   It may have already been received.")
    return False

def main():
    print("=" * 60)
    print("Goods Receipt Test")
    print("=" * 60)
    
    # First check if purchase is still pending
    is_pending = check_pending_receipts()
    
    if is_pending:
        # Try to receive it
        success = test_goods_receipt()
        
        if not success:
            print("\n" + "=" * 60)
            print("ACTION REQUIRED:")
            print("1. Go to Supabase SQL Editor")
            print("2. Run the SQL from IMMEDIATE_FIX_purchase_trigger.sql")
            print("3. Run this test again")
            print("=" * 60)
    else:
        print("\nPurchase may have already been received or doesn't exist.")
        print("You can create a new test purchase using test_purchase_upload.py")
    
    print("\nTest completed.")

if __name__ == "__main__":
    main()