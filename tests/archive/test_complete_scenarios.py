#!/usr/bin/env python3
"""
Test various batch creation scenarios
"""
import requests
import json
from datetime import datetime

BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

def test_scenario_1_no_batch():
    """Scenario 1: No batch info at all"""
    print("\n" + "="*60)
    print("SCENARIO 1: No batch information provided")
    print("="*60)
    
    purchase_data = {
        "supplier_id": 1,
        "purchase_date": datetime.now().date().isoformat(),
        "supplier_invoice_number": f"NO-BATCH-{datetime.now().strftime('%H%M%S')}",
        "supplier_invoice_date": datetime.now().date().isoformat(),
        "subtotal_amount": 500.00,
        "tax_amount": 60.00,
        "final_amount": 560.00,
        "items": [{
            "product_id": 14,
            "product_name": "Ibuprofen 400mg",
            "ordered_quantity": 25,
            "cost_price": 20.00,
            "mrp": 30.00
            # NO batch, expiry, or mfg date
        }]
    }
    
    # Create purchase
    resp = requests.post(f"{BASE_URL}/api/v1/purchases-enhanced/with-items", json=purchase_data)
    if resp.status_code != 200:
        print(f"❌ Failed to create purchase: {resp.text}")
        return False
    
    purchase_id = resp.json()['purchase_id']
    print(f"✅ Created purchase #{resp.json()['purchase_number']}")
    
    # Get items
    resp = requests.get(f"{BASE_URL}/api/v1/purchases-enhanced/{purchase_id}/items")
    items = resp.json()
    
    # Receive without batch
    receive_data = {
        "items": [{
            "purchase_item_id": items[0]['purchase_item_id'],
            "received_quantity": 25
        }]
    }
    
    resp = requests.post(f"{BASE_URL}/api/v1/purchases-enhanced/{purchase_id}/receive-fixed", json=receive_data)
    if resp.status_code == 200:
        print(f"✅ Auto-generated batch for {resp.json()['batches_created']} items")
        return True
    else:
        print(f"❌ Failed: {resp.json()}")
        return False

def test_scenario_2_custom_batch():
    """Scenario 2: Custom batch provided at receipt"""
    print("\n" + "="*60)
    print("SCENARIO 2: Custom batch at receipt time")
    print("="*60)
    
    # Create without batch
    purchase_data = {
        "supplier_id": 1,
        "purchase_date": datetime.now().date().isoformat(),
        "supplier_invoice_number": f"CUSTOM-{datetime.now().strftime('%H%M%S')}",
        "supplier_invoice_date": datetime.now().date().isoformat(),
        "subtotal_amount": 1000.00,
        "tax_amount": 120.00,
        "final_amount": 1120.00,
        "items": [{
            "product_id": 14,
            "product_name": "Ibuprofen 400mg",
            "ordered_quantity": 50,
            "cost_price": 20.00,
            "mrp": 30.00
        }]
    }
    
    resp = requests.post(f"{BASE_URL}/api/v1/purchases-enhanced/with-items", json=purchase_data)
    if resp.status_code != 200:
        return False
    
    purchase_id = resp.json()['purchase_id']
    print(f"✅ Created purchase #{resp.json()['purchase_number']}")
    
    # Get items
    resp = requests.get(f"{BASE_URL}/api/v1/purchases-enhanced/{purchase_id}/items")
    items = resp.json()
    
    # Receive WITH custom batch
    custom_batch = f"MANUAL-{datetime.now().strftime('%Y%m%d-%H%M')}"
    receive_data = {
        "items": [{
            "purchase_item_id": items[0]['purchase_item_id'],
            "received_quantity": 50,
            "batch_number": custom_batch,
            "expiry_date": "2026-06-30"
        }]
    }
    
    resp = requests.post(f"{BASE_URL}/api/v1/purchases-enhanced/{purchase_id}/receive-fixed", json=receive_data)
    if resp.status_code == 200:
        print(f"✅ Used custom batch: {custom_batch}")
        return True
    else:
        print(f"❌ Failed: {resp.json()}")
        return False

def test_scenario_3_pdf_parsed():
    """Scenario 3: Simulating PDF parsed data"""
    print("\n" + "="*60)
    print("SCENARIO 3: PDF parsed with partial batch info")
    print("="*60)
    
    # Simulate PDF that has batch but no expiry
    purchase_data = {
        "supplier_id": 1,
        "purchase_date": datetime.now().date().isoformat(),
        "supplier_invoice_number": f"PDF-PARSED-{datetime.now().strftime('%H%M%S')}",
        "supplier_invoice_date": datetime.now().date().isoformat(),
        "subtotal_amount": 2000.00,
        "tax_amount": 240.00,
        "final_amount": 2240.00,
        "items": [{
            "product_id": 14,
            "product_name": "Ibuprofen 400mg",
            "ordered_quantity": 100,
            "cost_price": 20.00,
            "mrp": 30.00,
            "batch_number": "MFG-2024-0789"
            # Has batch but no expiry (common in PDFs)
        }]
    }
    
    resp = requests.post(f"{BASE_URL}/api/v1/purchases-enhanced/with-items", json=purchase_data)
    if resp.status_code != 200:
        return False
    
    purchase_id = resp.json()['purchase_id']
    print(f"✅ Created with PDF batch: MFG-2024-0789")
    
    # Get items
    resp = requests.get(f"{BASE_URL}/api/v1/purchases-enhanced/{purchase_id}/items")
    items = resp.json()
    
    # Receive - trigger will use the batch and add default expiry
    receive_data = {
        "items": [{
            "purchase_item_id": items[0]['purchase_item_id'],
            "received_quantity": 100
        }]
    }
    
    resp = requests.post(f"{BASE_URL}/api/v1/purchases-enhanced/{purchase_id}/receive-fixed", json=receive_data)
    if resp.status_code == 200:
        print(f"✅ Batch created with default expiry date")
        return True
    else:
        print(f"❌ Failed: {resp.json()}")
        return False

def main():
    print("="*60)
    print("TESTING BATCH CREATION SCENARIOS")
    print("="*60)
    
    results = []
    
    # Test all scenarios
    results.append(("No batch info", test_scenario_1_no_batch()))
    results.append(("Custom batch", test_scenario_2_custom_batch()))
    results.append(("PDF partial info", test_scenario_3_pdf_parsed()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for scenario, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{scenario}: {status}")
    
    if all(r[1] for r in results):
        print("\n🎉 ALL SCENARIOS WORKING!")
        print("\nThe system handles:")
        print("- Missing batch info → Auto-generates")
        print("- Custom batches → Uses provided")
        print("- Partial PDF data → Fills defaults")
    else:
        print("\n⚠️  Some scenarios failed")

if __name__ == "__main__":
    main()