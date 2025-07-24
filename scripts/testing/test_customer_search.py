#!/usr/bin/env python3
"""
Test script to diagnose customer search issues
"""
import requests
import json
import time
from datetime import datetime

# Base URL
BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

def test_customer_search():
    """Test customer search with different parameters"""
    
    print("🔍 Testing Customer Search Endpoint")
    print("=" * 50)
    
    # Test 1: Basic list without search
    print("\n1. Testing basic customer list (no search)...")
    start_time = time.time()
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/customers/",
            params={"limit": 10},
            timeout=30
        )
        elapsed = time.time() - start_time
        print(f"Status: {response.status_code}")
        print(f"Response time: {elapsed:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: Found {data.get('total', 0)} customers")
            print(f"   Returned: {len(data.get('customers', []))} customers")
        else:
            print(f"❌ Error: {response.text}")
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT after 30 seconds!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test 2: Search with a simple term
    print("\n2. Testing search with term 'Apollo'...")
    start_time = time.time()
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/customers/",
            params={"search": "Apollo", "limit": 10},
            timeout=30
        )
        elapsed = time.time() - start_time
        print(f"Status: {response.status_code}")
        print(f"Response time: {elapsed:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: Found {len(data.get('customers', []))} matching customers")
        else:
            print(f"❌ Error: {response.text}")
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT after 30 seconds!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test 3: Search with phone number
    print("\n3. Testing search with phone number...")
    start_time = time.time()
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/customers/",
            params={"search": "987654", "limit": 10},
            timeout=30
        )
        elapsed = time.time() - start_time
        print(f"Status: {response.status_code}")
        print(f"Response time: {elapsed:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: Found {len(data.get('customers', []))} matching customers")
        else:
            print(f"❌ Error: {response.text}")
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT after 30 seconds!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test 4: Check database schema
    print("\n4. Checking database schema for customers table...")
    try:
        response = requests.get(
            f"{BASE_URL}/db/inspect",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            for table in data.get('tables', []):
                if table['name'] == 'customers':
                    print("✅ Found customers table")
                    print(f"   Columns: {len(table['columns'])}")
                    # Check if area column exists
                    area_exists = any(col['name'] == 'area' for col in table['columns'])
                    print(f"   Area column exists: {'Yes' if area_exists else 'No'}")
                    break
        else:
            print(f"❌ Could not inspect database: {response.status_code}")
    except Exception as e:
        print(f"❌ Error inspecting database: {str(e)}")
    
    # Test 5: Direct SQL query test (if possible)
    print("\n5. Testing with minimal parameters...")
    start_time = time.time()
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/customers/",
            params={"limit": 1},
            timeout=10
        )
        elapsed = time.time() - start_time
        print(f"Status: {response.status_code}")
        print(f"Response time: {elapsed:.2f} seconds")
        
        if response.status_code == 200:
            print(f"✅ Minimal query successful")
        else:
            print(f"❌ Error: {response.text}")
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT after 10 seconds!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_customer_search()