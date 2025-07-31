#!/usr/bin/env python3
"""Test script for API endpoints"""

import requests
import json
from datetime import datetime

# Base URL - try both with and without trailing slash
BASE_URLS = [
    "https://pharma-backend-production.up.railway.app",
    "https://aaso-pharma-erp-production.up.railway.app",
    "https://pharma-backend.up.railway.app"
]

def test_endpoint(url, path, method="GET", data=None):
    """Test an API endpoint"""
    full_url = f"{url}{path}"
    print(f"\nTesting {method} {full_url}")
    
    try:
        if method == "GET":
            response = requests.get(full_url, timeout=5)
        elif method == "POST":
            response = requests.post(full_url, json=data, timeout=5)
        
        print(f"Status: {response.status_code}")
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        
        if 'application/json' in content_type:
            try:
                print(f"Response: {json.dumps(response.json(), indent=2)[:200]}...")
            except:
                print(f"Response (text): {response.text[:200]}...")
        else:
            print(f"Response (text): {response.text[:200]}...")
            
        return response.status_code
        
    except requests.exceptions.Timeout:
        print("Request timed out")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        return None
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return None

def main():
    """Run API tests"""
    print("AASO Pharma ERP API Test Script")
    print("=" * 50)
    
    # Find working base URL
    working_url = None
    for base_url in BASE_URLS:
        print(f"\nTrying base URL: {base_url}")
        status = test_endpoint(base_url, "/health")
        if status and status != 404:
            working_url = base_url
            break
            
    if not working_url:
        # Try the main URL with different paths
        working_url = BASE_URLS[0]
        print(f"\nUsing default URL: {working_url}")
    
    # Test endpoints
    endpoints_to_test = [
        ("/", "GET"),
        ("/docs", "GET"),
        ("/openapi.json", "GET"),
        ("/health", "GET"),
        ("/api/health", "GET"),
        ("/api/v1/health", "GET"),
        ("/api/v1/inventory", "GET"),
        ("/api/v1/sales-returns", "GET"),
        ("/api/v1/stock-adjustments", "GET"),
        ("/api/v1/tax-entries", "GET"),
    ]
    
    print(f"\n{'='*50}")
    print(f"Testing endpoints on {working_url}")
    print(f"{'='*50}")
    
    for path, method in endpoints_to_test:
        test_endpoint(working_url, path, method)
        
    # Test a sample sales return POST (will likely fail without auth/data)
    print(f"\n{'='*50}")
    print("Testing POST endpoints")
    print(f"{'='*50}")
    
    # Sample sales return data
    sales_return_data = {
        "order_id": 1,
        "product_id": 1,
        "batch_id": 1,
        "quantity": 2,
        "reason": "Test return",
        "return_date": datetime.now().isoformat(),
        "performed_by": 1
    }
    
    test_endpoint(working_url, "/api/v1/sales-returns", "POST", sales_return_data)

if __name__ == "__main__":
    main()