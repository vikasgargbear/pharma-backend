"""
Debug script to test org-users API endpoint
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"  # Change if your backend is running elsewhere
ENDPOINTS = [
    "/api/v1/org-users",
    "/api/v1/users",
    "/api/v1/org-users/roles",
    "/health/detailed"
]

print("🔍 Testing User Management API Endpoints\n")
print("=" * 50)

# Test each endpoint
for endpoint in ENDPOINTS:
    url = f"{BASE_URL}{endpoint}"
    print(f"\n📍 Testing: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response type: {type(data)}")
            
            # Pretty print the response
            if isinstance(data, dict):
                print(f"   Keys: {list(data.keys())}")
                if 'data' in data:
                    print(f"   Data length: {len(data['data']) if isinstance(data['data'], list) else 'Not a list'}")
                    if isinstance(data['data'], list) and len(data['data']) > 0:
                        print(f"   First user: {json.dumps(data['data'][0], indent=2)}")
            elif isinstance(data, list):
                print(f"   List length: {len(data)}")
                if len(data) > 0:
                    print(f"   First item: {json.dumps(data[0], indent=2)}")
        else:
            print(f"   Error: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection failed - Is the backend running?")
    except requests.exceptions.Timeout:
        print(f"   ❌ Request timed out")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

print("\n" + "=" * 50)
print("\n💡 Quick fixes:")
print("1. Make sure backend is running: cd pharma-backend && uvicorn api.main:app --reload")
print("2. Check if DATABASE_URL is set correctly in .env")
print("3. Verify org_users table exists in Supabase")
print("4. Check browser console for CORS errors")