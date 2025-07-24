#!/usr/bin/env python3
"""
Test script for GST calculation and sales API
Tests both intra-state and inter-state transactions
"""
import requests
import json
from decimal import Decimal
from datetime import date

# Base URL for the API
BASE_URL = "http://localhost:8000"

# Test data for different scenarios
test_scenarios = [
    {
        "name": "Intra-state B2B Sale (Maharashtra to Maharashtra)",
        "data": {
            "sale_date": str(date.today()),
            "party_id": 1,
            "party_name": "ABC Pharmacy",
            "party_gst": "27AABCU9603R1ZP",  # Maharashtra GSTIN
            "party_address": "123 Street, Mumbai",
            "party_phone": "9876543210",
            "payment_mode": "credit",
            "seller_gstin": "27AABCU9603R1ZM",  # Maharashtra GSTIN
            "items": [
                {
                    "product_id": 1,
                    "product_name": "Paracetamol 500mg",
                    "hsn_code": "3004",
                    "batch_number": "B001",
                    "expiry_date": "2025-12-31",
                    "quantity": 10,
                    "unit": "strip",
                    "unit_price": "50.00",
                    "mrp": "60.00",
                    "discount_percent": "10.00",
                    "tax_percent": "12.00"  # 6% CGST + 6% SGST
                }
            ],
            "discount_amount": "0",
            "other_charges": "50.00",
            "notes": "Test intra-state sale"
        },
        "expected_gst_type": "cgst_sgst"
    },
    {
        "name": "Inter-state B2B Sale (Maharashtra to Karnataka)",
        "data": {
            "sale_date": str(date.today()),
            "party_id": 2,
            "party_name": "XYZ Medical Store",
            "party_gst": "29AABCU9603R1ZK",  # Karnataka GSTIN
            "party_address": "456 Avenue, Bangalore",
            "party_phone": "9876543211",
            "payment_mode": "credit",
            "seller_gstin": "27AABCU9603R1ZM",  # Maharashtra GSTIN
            "items": [
                {
                    "product_id": 2,
                    "product_name": "Amoxicillin 500mg",
                    "hsn_code": "3004",
                    "batch_number": "B002",
                    "expiry_date": "2025-06-30",
                    "quantity": 20,
                    "unit": "strip",
                    "unit_price": "75.00",
                    "mrp": "85.00",
                    "discount_percent": "5.00",
                    "tax_percent": "18.00"  # 18% IGST
                }
            ],
            "discount_amount": "0",
            "other_charges": "100.00",
            "notes": "Test inter-state sale"
        },
        "expected_gst_type": "igst"
    },
    {
        "name": "B2C Sale (No buyer GSTIN)",
        "data": {
            "sale_date": str(date.today()),
            "party_id": 3,
            "party_name": "Walk-in Customer",
            "party_gst": None,
            "party_address": "Mumbai",
            "party_phone": "9999999999",
            "party_state_code": "27",  # Maharashtra
            "payment_mode": "cash",
            "seller_gstin": "27AABCU9603R1ZM",
            "items": [
                {
                    "product_id": 3,
                    "product_name": "Cough Syrup",
                    "hsn_code": "3004",
                    "quantity": 1,
                    "unit": "bottle",
                    "unit_price": "120.00",
                    "mrp": "150.00",
                    "discount_percent": "0",
                    "tax_percent": "5.00"  # 2.5% CGST + 2.5% SGST
                }
            ],
            "discount_amount": "0",
            "other_charges": "0",
            "notes": "Test B2C sale"
        },
        "expected_gst_type": "cgst_sgst"
    }
]

def test_sales_api():
    """Test sales API with different GST scenarios"""
    print("Testing Sales API with GST calculations\n")
    print("=" * 80)
    
    for scenario in test_scenarios:
        print(f"\n{scenario['name']}:")
        print("-" * 40)
        
        # Make API call
        response = requests.post(
            f"{BASE_URL}/api/v1/sales/",
            json=scenario['data']
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Success!")
            print(f"Invoice Number: {result['invoice_number']}")
            print(f"GST Type: {result['gst_type']} (Expected: {scenario['expected_gst_type']})")
            print(f"Subtotal: ₹{result['subtotal_amount']}")
            print(f"Discount: ₹{result['discount_amount']}")
            
            if result['gst_type'] == 'cgst_sgst':
                print(f"CGST: ₹{result['cgst_amount']}")
                print(f"SGST: ₹{result['sgst_amount']}")
                print(f"IGST: ₹{result['igst_amount']} (should be 0)")
            else:
                print(f"CGST: ₹{result['cgst_amount']} (should be 0)")
                print(f"SGST: ₹{result['sgst_amount']} (should be 0)")
                print(f"IGST: ₹{result['igst_amount']}")
            
            print(f"Total Tax: ₹{result['tax_amount']}")
            print(f"Grand Total: ₹{result['total_amount']}")
            
            # Validate GST type
            if result['gst_type'] == scenario['expected_gst_type']:
                print("✅ GST type matches expected value")
            else:
                print(f"❌ GST type mismatch! Got {result['gst_type']}, expected {scenario['expected_gst_type']}")
                
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            print(f"Error: {response.text}")

def test_gst_validation():
    """Test GSTIN validation"""
    print("\n\nTesting GSTIN Validation")
    print("=" * 80)
    
    test_gstins = [
        ("27AABCU9603R1ZM", True, "Valid Maharashtra GSTIN"),
        ("29AABCU9603R1ZK", True, "Valid Karnataka GSTIN"),
        ("27AABCU9603R1Z", False, "Too short"),
        ("99AABCU9603R1ZM", False, "Invalid state code"),
        ("27AABCU9603R1AM", False, "Invalid format (should end with Z)"),
        ("", False, "Empty GSTIN"),
        (None, False, "None value")
    ]
    
    # Import the GST service to test validation
    import sys
    sys.path.append('/Users/vikasgarg/Documents/AASO/Infrastructure/pharma-backend')
    from api.services.gst_service import GSTService
    
    for gstin, expected_valid, description in test_gstins:
        is_valid = GSTService.validate_gstin(gstin)
        status = "✅" if is_valid == expected_valid else "❌"
        print(f"{status} {description}: '{gstin}' - Valid: {is_valid}")

if __name__ == "__main__":
    print("GST Sales API Test Script")
    print("========================\n")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is running\n")
        else:
            print("❌ Server health check failed")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please ensure the server is running on port 8000")
        exit(1)
    
    # Run tests
    test_sales_api()
    test_gst_validation()
    
    print("\n\nTest completed!")