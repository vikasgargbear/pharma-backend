#!/usr/bin/env python3
"""Check customer table columns"""
import requests

BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

# First check if db-inspect is working
print("Checking if db-inspect endpoint is available...")
response = requests.get(f"{BASE_URL}/db-inspect/table/customers/columns")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    columns = response.json()
    print("\nCustomers table columns:")
    for col in columns:
        print(f"  - {col['name']} ({col['type']})")
else:
    print(f"Error: {response.text}")