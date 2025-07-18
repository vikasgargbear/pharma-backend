#!/usr/bin/env python3
"""Test critical endpoints to ensure nothing breaks during cleanup"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Define critical endpoints to test
CRITICAL_ENDPOINTS = [
    # Health checks
    ("GET", "/health", None, "Health Check"),
    ("GET", "/health/detailed", None, "Detailed Health"),
    ("GET", "/", None, "Root"),
    
    # Customer endpoints
    ("GET", "/api/v1/customers/", None, "List Customers"),
    ("GET", "/api/v1/customers/2", None, "Get Customer"),
    
    # Order endpoints
    ("GET", "/api/v1/orders/", None, "List Orders"),
    ("GET", "/api/v1/orders/dashboard/stats", None, "Order Stats"),
    
    # Inventory endpoints  
    ("GET", "/api/v1/inventory/stock/current", None, "Stock Status"),
    ("GET", "/api/v1/inventory/dashboard", None, "Inventory Dashboard"),
    
    # Billing endpoints
    ("GET", "/billing/invoices", None, "List Invoices"),
    ("GET", "/billing/summary", None, "Invoice Summary"),
    
    # Other endpoints
    ("GET", "/products/", None, "Products"),
    ("GET", "/organizations/list", None, "Organizations"),
    ("GET", "/db-inspect/tables", None, "DB Inspect"),
]

def test_endpoint(method, path, data, name):
    """Test a single endpoint"""
    url = f"{BASE_URL}{path}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            return False, f"Unsupported method: {method}"
        
        # Check if request was successful (2xx status code)
        if 200 <= response.status_code < 300:
            return True, response.json() if response.text else "Empty response"
        else:
            return False, f"Status {response.status_code}: {response.text[:200]}"
            
    except requests.exceptions.Timeout:
        return False, "Request timed out"
    except requests.exceptions.ConnectionError:
        return False, "Connection error - is the server running?"
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    print(f"Starting endpoint tests at {datetime.now()}")
    print()
    
    results = []
    for method, path, data, name in CRITICAL_ENDPOINTS:
        print("=" * 60)
        print(f"Testing: {method} {path}")
        
        success, result = test_endpoint(method, path, data, name)
        results.append((name, success))
        
        if success:
            print(f"Status: {200}")
            print(f"Response: {json.dumps(result, indent=2)[:200]}...")
            print("✅ Success")
        else:
            print(f"❌ Failed")
            print(f"Error: {result}")
        print()
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:.<40} {status}")
    
    print(f"\nTotal: {passed}/{total} passed ({passed/total*100:.1f}%)")
    
    if passed < total:
        print("\n⚠️  Some tests failed. Review before proceeding.")
    else:
        print("\n✅ All tests passed!")

if __name__ == "__main__":
    main()