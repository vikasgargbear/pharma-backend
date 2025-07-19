#!/usr/bin/env python3
"""
Test script for Purchase Order Upload functionality
"""
import requests
import json
import os
from datetime import datetime, timedelta

# Base URL - update for production
BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"  # Production URL

def test_parse_invoice():
    """Test uploading and parsing a purchase invoice"""
    print("\n1. Testing Invoice Parse...")
    
    # Create a test PDF file path (you'll need an actual PDF)
    test_file = "test_invoice.pdf"  # Replace with actual invoice file
    
    if not os.path.exists(test_file):
        print("   ⚠️  No test file found. Please provide a PDF invoice.")
        return None
    
    with open(test_file, 'rb') as f:
        files = {'file': (test_file, f, 'application/pdf')}
        response = requests.post(
            f"{BASE_URL}/api/v1/purchase-upload/parse-invoice",
            files=files
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Invoice parsed successfully!")
        print(f"   - Supplier: {data['extracted_data']['supplier_name']}")
        print(f"   - Invoice #: {data['extracted_data']['invoice_number']}")
        print(f"   - Total: ₹{data['extracted_data']['grand_total']}")
        print(f"   - Items: {len(data['extracted_data']['items'])}")
        return data
    else:
        print(f"   ❌ Failed: {response.status_code} - {response.text}")
        return None

def test_validate_invoice(invoice_data):
    """Test invoice validation"""
    print("\n2. Testing Invoice Validation...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/purchase-upload/validate-invoice",
        json=invoice_data
    )
    
    if response.status_code == 200:
        validation = response.json()
        print(f"   ✅ Validation complete")
        print(f"   - Valid: {validation['is_valid']}")
        print(f"   - Errors: {len(validation['errors'])}")
        print(f"   - Warnings: {len(validation['warnings'])}")
        
        for error in validation['errors']:
            print(f"     ❌ {error}")
        for warning in validation['warnings']:
            print(f"     ⚠️  {warning}")
            
        return validation
    else:
        print(f"   ❌ Failed: {response.status_code}")
        return None

def test_create_from_parsed(parsed_data):
    """Test creating purchase from parsed data"""
    print("\n3. Testing Purchase Creation from Parsed Data...")
    
    # Prepare the data (simulate user edits/confirmations)
    purchase_data = {
        "supplier_id": parsed_data['extracted_data'].get('supplier_id'),
        "invoice_number": parsed_data['extracted_data']['invoice_number'],
        "invoice_date": parsed_data['extracted_data']['invoice_date'],
        "subtotal": parsed_data['extracted_data']['subtotal'],
        "tax_amount": parsed_data['extracted_data']['tax_amount'],
        "discount_amount": parsed_data['extracted_data']['discount_amount'],
        "grand_total": parsed_data['extracted_data']['grand_total'],
        "items": parsed_data['extracted_data']['items']
    }
    
    # If supplier not matched, create new
    if not purchase_data['supplier_id']:
        purchase_data['supplier'] = {
            "supplier_name": parsed_data['extracted_data']['supplier_name'],
            "supplier_gstin": parsed_data['extracted_data']['supplier_gstin'],
            "supplier_address": parsed_data['extracted_data']['supplier_address']
        }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/purchase-upload/create-from-parsed",
        json=purchase_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Purchase created successfully!")
        print(f"   - Purchase ID: {result['purchase_id']}")
        print(f"   - Purchase #: {result['purchase_number']}")
        print(f"   - Items: {result['items_created']}")
        return result
    else:
        print(f"   ❌ Failed: {response.status_code} - {response.text}")
        return None

def test_manual_purchase_with_items():
    """Test manual purchase creation with items"""
    print("\n4. Testing Manual Purchase Creation with Items...")
    
    # Sample manual entry data
    purchase_data = {
        "supplier_id": 1,  # Assuming supplier exists
        "purchase_date": datetime.now().date().isoformat(),
        "supplier_invoice_number": f"INV-TEST-{datetime.now().strftime('%Y%m%d')}",
        "supplier_invoice_date": datetime.now().date().isoformat(),
        "subtotal_amount": 1000.00,
        "discount_amount": 50.00,
        "tax_amount": 114.00,
        "other_charges": 20.00,
        "final_amount": 1084.00,
        "items": [
            {
                "product_id": 14,  # Ibuprofen from our tests
                "product_name": "Ibuprofen 400mg",
                "ordered_quantity": 100,
                "cost_price": 10.00,
                "mrp": 15.00,
                "discount_percent": 5.0,
                "tax_percent": 12.0,
                "batch_number": f"TEST-{datetime.now().strftime('%Y%m')}",
                "expiry_date": (datetime.now() + timedelta(days=730)).date().isoformat()
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/purchases-enhanced/with-items",
        json=purchase_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Manual purchase created!")
        print(f"   - Purchase ID: {result['purchase_id']}")
        print(f"   - Purchase #: {result['purchase_number']}")
        return result
    else:
        print(f"   ❌ Failed: {response.status_code} - {response.text}")
        return None

def test_get_purchase_items(purchase_id):
    """Test getting purchase items"""
    print(f"\n5. Testing Get Purchase Items for ID: {purchase_id}...")
    
    response = requests.get(
        f"{BASE_URL}/api/v1/purchases-enhanced/{purchase_id}/items"
    )
    
    if response.status_code == 200:
        items = response.json()
        print(f"   ✅ Found {len(items)} items")
        for item in items:
            print(f"   - {item['product_name']}: {item['ordered_quantity']} @ ₹{item['cost_price']}")
        return items
    else:
        print(f"   ❌ Failed: {response.status_code}")
        return None

def test_receive_items(purchase_id):
    """Test receiving purchase items"""
    print(f"\n6. Testing Receive Items for Purchase: {purchase_id}...")
    
    # First get the items
    items_response = requests.get(
        f"{BASE_URL}/api/v1/purchases-enhanced/{purchase_id}/items"
    )
    
    if items_response.status_code != 200:
        print("   ❌ Could not get purchase items")
        return None
    
    items = items_response.json()
    
    # Prepare receive data
    receive_data = {
        "items": [
            {
                "purchase_item_id": item['purchase_item_id'],
                "received_quantity": item['ordered_quantity'],
                "batch_number": item.get('batch_number', f"RCV-{datetime.now().strftime('%Y%m%d')}"),
                "expiry_date": item.get('expiry_date')
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
        print(f"   ✅ Items received successfully!")
        print(f"   - Batches created: {result['batches_created']}")
        print(f"   - GRN #: {result['grn_number']}")
        return result
    else:
        print(f"   ❌ Failed: {response.status_code} - {response.text}")
        return None

def test_pending_receipts():
    """Test getting pending receipts"""
    print("\n7. Testing Get Pending Receipts...")
    
    response = requests.get(
        f"{BASE_URL}/api/v1/purchases-enhanced/pending-receipts"
    )
    
    if response.status_code == 200:
        pending = response.json()
        print(f"   ✅ Found {len(pending)} pending purchases")
        for p in pending[:3]:  # Show first 3
            print(f"   - {p['purchase_number']} from {p['supplier_name']}")
        return pending
    else:
        print(f"   ❌ Failed: {response.status_code}")
        return None

def main():
    """Run all tests"""
    print("=" * 60)
    print("Purchase Order Upload & Management Test Suite")
    print("=" * 60)
    
    # Test 1: Parse invoice (if PDF available)
    parsed_data = test_parse_invoice()
    
    if parsed_data:
        # Test 2: Validate
        validation = test_validate_invoice(parsed_data['extracted_data'])
        
        # Test 3: Create from parsed
        if validation and validation['is_valid']:
            purchase_result = test_create_from_parsed(parsed_data)
    
    # Test 4: Manual creation
    manual_result = test_manual_purchase_with_items()
    
    if manual_result:
        # Test 5: Get items
        items = test_get_purchase_items(manual_result['purchase_id'])
        
        # Test 6: Receive items
        if items:
            receive_result = test_receive_items(manual_result['purchase_id'])
    
    # Test 7: Pending receipts
    pending = test_pending_receipts()
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()