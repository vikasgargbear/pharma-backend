#!/usr/bin/env python3
"""
Test script for customer management endpoints
Tests all CRUD operations and business logic
"""
import requests
import json
from datetime import date, datetime
from decimal import Decimal

# Base URL
BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

# Test data
test_customer = {
    "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",
    "customer_name": "Apollo Pharmacy - MG Road",
    "contact_person": "Rajesh Kumar",
    "phone": "9876543210",
    "alternate_phone": "9876543211",
    "email": "apollo.mgroad@example.com",
    "address_line1": "Shop No. 123, MG Road",
    "address_line2": "Near Metro Station",
    "city": "Bangalore",
    "state": "Karnataka",
    "pincode": "560001",
    "gstin": "29ABCDE1234F1Z5",
    "pan_number": "ABCDE1234F",
    "drug_license_number": "KA-B-123456",
    "customer_type": "pharmacy",
    "credit_limit": 50000.00,
    "credit_days": 30,
    "discount_percent": 5.0,
    "is_active": True,
    "notes": "Premium customer, prompt payment"
}

def test_create_customer():
    """Test customer creation"""
    print("\n1. Testing customer creation...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/customers/",
        json=test_customer
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        customer = response.json()
        print(f"✅ Customer created: {customer['customer_name']} (Code: {customer['customer_code']})")
        return customer['customer_id']
    else:
        print(f"❌ Error: {response.text}")
        return None

def test_list_customers():
    """Test customer listing with filters"""
    print("\n2. Testing customer listing...")
    
    # Test basic listing
    response = requests.get(f"{BASE_URL}/api/v1/customers/")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} customers")
        
        # Test with search
        response = requests.get(f"{BASE_URL}/api/v1/customers/?search=Apollo")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search 'Apollo': {len(data['customers'])} results")
        
        # Test with filters
        response = requests.get(f"{BASE_URL}/api/v1/customers/?customer_type=pharmacy&city=Bangalore")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Filter pharmacy in Bangalore: {len(data['customers'])} results")
    else:
        print(f"❌ Error: {response.text}")

def test_get_customer(customer_id):
    """Test getting single customer"""
    print(f"\n3. Testing get customer {customer_id}...")
    
    response = requests.get(f"{BASE_URL}/api/v1/customers/{customer_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        customer = response.json()
        print(f"✅ Customer details:")
        print(f"   Name: {customer['customer_name']}")
        print(f"   Outstanding: ₹{customer['outstanding_amount']}")
        print(f"   Total Business: ₹{customer['total_business']}")
    else:
        print(f"❌ Error: {response.text}")

def test_update_customer(customer_id):
    """Test customer update"""
    print(f"\n4. Testing update customer {customer_id}...")
    
    update_data = {
        "credit_limit": 75000.00,
        "discount_percent": 7.5,
        "notes": "Premium customer, increased credit limit"
    }
    
    response = requests.put(
        f"{BASE_URL}/api/v1/customers/{customer_id}",
        json=update_data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        customer = response.json()
        print(f"✅ Customer updated:")
        print(f"   Credit Limit: ₹{customer['credit_limit']}")
        print(f"   Discount: {customer['discount_percent']}%")
    else:
        print(f"❌ Error: {response.text}")

def test_customer_ledger(customer_id):
    """Test customer ledger"""
    print(f"\n5. Testing customer ledger for {customer_id}...")
    
    response = requests.get(f"{BASE_URL}/api/v1/customers/{customer_id}/ledger")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        ledger = response.json()
        print(f"✅ Ledger summary:")
        print(f"   Opening Balance: ₹{ledger['opening_balance']}")
        print(f"   Total Debit: ₹{ledger['total_debit']}")
        print(f"   Total Credit: ₹{ledger['total_credit']}")
        print(f"   Closing Balance: ₹{ledger['closing_balance']}")
        print(f"   Entries: {len(ledger['entries'])}")
    else:
        print(f"❌ Error: {response.text}")

def test_customer_outstanding(customer_id):
    """Test customer outstanding"""
    print(f"\n6. Testing customer outstanding for {customer_id}...")
    
    response = requests.get(f"{BASE_URL}/api/v1/customers/{customer_id}/outstanding")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        outstanding = response.json()
        print(f"✅ Outstanding summary:")
        print(f"   Total Outstanding: ₹{outstanding['total_outstanding']}")
        print(f"   Available Credit: ₹{outstanding['available_credit']}")
        print(f"   Overdue Amount: ₹{outstanding['overdue_amount']}")
        print(f"   Outstanding Invoices: {len(outstanding['invoices'])}")
    else:
        print(f"❌ Error: {response.text}")

def test_check_credit_limit(customer_id):
    """Test credit limit check"""
    print(f"\n7. Testing credit limit check for {customer_id}...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/customers/{customer_id}/check-credit",
        params={"order_amount": 10000}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        if result['valid']:
            print(f"✅ Credit check passed:")
            print(f"   Credit Limit: ₹{result['credit_limit']}")
            print(f"   Outstanding: ₹{result['outstanding']}")
            print(f"   Available: ₹{result['available']}")
        else:
            print(f"❌ Credit check failed: {result['message']}")
    else:
        print(f"❌ Error: {response.text}")

def test_record_payment(customer_id):
    """Test payment recording"""
    print(f"\n8. Testing payment recording for {customer_id}...")
    
    payment_data = {
        "customer_id": customer_id,
        "payment_date": str(date.today()),
        "amount": 5000.00,
        "payment_mode": "upi",
        "reference_number": "UPI123456789",
        "notes": "Payment via PhonePe"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/customers/{customer_id}/payment",
        json=payment_data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        payment = response.json()
        print(f"✅ Payment recorded:")
        print(f"   Payment ID: {payment['payment_id']}")
        print(f"   Amount: ₹{payment['amount']}")
        print(f"   Allocated: ₹{payment['allocated_amount']}")
        print(f"   Unallocated: ₹{payment['unallocated_amount']}")
    else:
        print(f"❌ Error: {response.text}")

def main():
    """Run all tests"""
    print("🧪 Testing Customer Management Endpoints")
    print("=" * 50)
    
    # Create customer
    customer_id = test_create_customer()
    
    if customer_id:
        # Test other endpoints
        test_list_customers()
        test_get_customer(customer_id)
        test_update_customer(customer_id)
        test_customer_ledger(customer_id)
        test_customer_outstanding(customer_id)
        test_check_credit_limit(customer_id)
        test_record_payment(customer_id)
    
    print("\n✅ Customer endpoint tests completed!")

if __name__ == "__main__":
    main()