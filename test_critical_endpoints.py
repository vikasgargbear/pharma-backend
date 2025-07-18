#!/usr/bin/env python3
"""
Test all critical endpoints to ensure nothing breaks during cleanup
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_endpoint(method, path, data=None, expected_status=None):
    """Test a single endpoint"""
    url = f"{BASE_URL}{path}"
    print(f"\n{'='*60}")
    print(f"Testing: {method} {path}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        else:
            print(f"Unsupported method: {method}")
            return False
        
        print(f"Status: {response.status_code}")
        
        # Check expected status if provided
        if expected_status and response.status_code != expected_status:
            print(f"❌ Expected {expected_status}, got {response.status_code}")
            return False
        
        # Try to parse JSON response
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)[:200]}...")
        except:
            print(f"Response: {response.text[:200]}...")
        
        # Consider 2xx and 3xx as success
        if 200 <= response.status_code < 400:
            print("✅ Success")
            return True
        else:
            print("❌ Failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def run_all_tests():
    """Run all critical endpoint tests"""
    print(f"Starting endpoint tests at {datetime.now()}")
    
    results = []
    
    # Core endpoints
    results.append(("Health Check", test_endpoint("GET", "/health")))
    results.append(("Detailed Health", test_endpoint("GET", "/health/detailed")))
    results.append(("Root", test_endpoint("GET", "/")))
    
    # V1 Customer endpoints
    results.append(("List Customers", test_endpoint("GET", "/api/v1/customers/")))
    results.append(("Get Customer", test_endpoint("GET", "/api/v1/customers/2")))
    
    # V1 Order endpoints
    results.append(("List Orders", test_endpoint("GET", "/api/v1/orders/")))
    results.append(("Order Stats", test_endpoint("GET", "/api/v1/orders/dashboard/stats")))
    
    # V1 Inventory endpoints
    results.append(("Stock Status", test_endpoint("GET", "/api/v1/inventory/stock/current")))
    results.append(("Inventory Dashboard", test_endpoint("GET", "/api/v1/inventory/dashboard")))
    
    # V1 Billing endpoints
    results.append(("List Invoices", test_endpoint("GET", "/billing/invoices")))
    results.append(("Invoice Summary", test_endpoint("GET", "/billing/summary")))
    
    # Legacy endpoints that might be used
    results.append(("Products", test_endpoint("GET", "/products/")))
    results.append(("Organizations", test_endpoint("GET", "/organizations/list")))
    results.append(("DB Inspect", test_endpoint("GET", "/db-inspect/tables")))
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:.<40} {status}")
    
    print(f"\nTotal: {passed}/{total} passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Safe to proceed with cleanup.")
        return True
    else:
        print("\n⚠️  Some tests failed. Review before proceeding.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)