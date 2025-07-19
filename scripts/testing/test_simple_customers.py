#!/usr/bin/env python3
"""Test simple customer endpoints"""
import requests
import json

BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

print("Testing Simple Customer Endpoints")
print("=" * 50)

# 1. List customers
print("\n1. List customers:")
response = requests.get(f"{BASE_URL}/customers-simple/")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Total customers: {data['total']}")
    print(f"Retrieved: {len(data['customers'])}")

# 2. Create customer
print("\n2. Create customer:")
response = requests.post(
    f"{BASE_URL}/customers-simple/",
    params={
        "customer_name": "Test Pharmacy",
        "phone": "9999999999",
        "email": "test@pharmacy.com"
    }
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    customer = response.json()
    print(f"Created customer ID: {customer.get('customer_id')}")
    customer_id = customer.get('customer_id')
    
    # 3. Get customer
    if customer_id:
        print(f"\n3. Get customer {customer_id}:")
        response = requests.get(f"{BASE_URL}/customers-simple/{customer_id}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Name: {data.get('customer_name')}")
            print(f"Total orders: {data.get('total_orders', 0)}")
            print(f"Total business: {data.get('total_business', 0)}")
        
        # 4. Get customer orders
        print(f"\n4. Get customer {customer_id} orders:")
        response = requests.get(f"{BASE_URL}/customers-simple/{customer_id}/orders")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total orders: {data['total_orders']}")

print("\n✅ Simple customer endpoints test completed!")