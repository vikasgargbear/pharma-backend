#!/usr/bin/env python3
"""
Run database migrations to add enterprise features
This is how companies scale - controlled, incremental updates
"""
import requests
import json
import time

BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

def wait_for_deployment():
    """Wait for deployment to be ready"""
    print("⏳ Waiting for deployment to be ready...")
    for i in range(10):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API is ready!")
                return True
        except:
            pass
        print(f"   Attempt {i+1}/10...")
        time.sleep(10)
    return False

def run_migrations():
    """Run the migration steps"""
    print("\n🚀 Running Database Migrations")
    print("=" * 50)
    
    # Step 1: Check current columns
    print("\n1️⃣ Checking current database schema...")
    response = requests.get(f"{BASE_URL}/migrations/v2/check-customer-columns")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Existing columns: {len(data['existing_columns'])}")
        print(f"   Missing columns: {len(data['missing_columns'])}")
        
        if data['missing_columns']:
            print(f"   Need to add: {', '.join(data['missing_columns'][:5])}...")
        
        if data['ready_for_enterprise']:
            print("   ✅ Database already has all enterprise columns!")
            return
    else:
        print(f"   ❌ Error: {response.status_code}")
        return
    
    # Step 2: Add missing columns
    print("\n2️⃣ Adding enterprise columns...")
    response = requests.post(f"{BASE_URL}/migrations/v2/add-customer-columns")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"   ✅ {data['message']}")
            print(f"   Added columns: {len(data.get('new_columns', []))}")
            if data.get('new_columns'):
                print(f"   New: {', '.join(data['new_columns'][:5])}...")
        else:
            print(f"   ❌ Migration failed: {data.get('message')}")
            return
    else:
        print(f"   ❌ Error: {response.status_code}")
        return
    
    # Step 3: Create sample data
    print("\n3️⃣ Creating sample customer data...")
    response = requests.post(f"{BASE_URL}/migrations/v2/create-sample-customers")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ {data['message']}")
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    # Step 4: Test the enterprise endpoints
    print("\n4️⃣ Testing enterprise customer endpoints...")
    response = requests.get(f"{BASE_URL}/api/v1/customers/")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Customer API working!")
        print(f"   Total customers: {data.get('total', 0)}")
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("✅ Migration complete! Your pharma backend now has:")
    print("   • GST compliance (GSTIN validation)")
    print("   • Credit limit management")
    print("   • Multi-type customers")
    print("   • Address management")
    print("   • Contact tracking")
    print("   • And much more!")
    
    print("\n🎯 Next: Run test_customer_endpoints.py to test all features")

if __name__ == "__main__":
    if wait_for_deployment():
        run_migrations()
    else:
        print("❌ Deployment not ready. Please wait and try again.")