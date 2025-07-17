"""
Final comprehensive API test
"""
import requests
import json
from datetime import datetime

BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

def test_endpoint(method, path, data=None):
    """Test an endpoint and return status"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            r = requests.get(url)
        elif method == "POST":
            r = requests.post(url, json=data)
        
        status = "✅" if r.status_code < 400 else "❌"
        print(f"{status} {method} {path} - {r.status_code}")
        return r.status_code < 400
    except Exception as e:
        print(f"❌ {method} {path} - Error: {e}")
        return False

print("FINAL API TEST - Working Endpoints")
print("="*50)

# Basic endpoints
test_endpoint("GET", "/")
test_endpoint("GET", "/health")
test_endpoint("GET", "/health/detailed")
test_endpoint("GET", "/info")

# Database inspection
test_endpoint("GET", "/db-inspect/tables")
test_endpoint("GET", "/db-inspect/table/products/columns")

# Organizations
test_endpoint("GET", "/organizations/list")

# Test endpoints
test_endpoint("GET", "/test/")
test_endpoint("POST", "/test/echo", {"test": "data"})

# Products Simple
test_endpoint("GET", "/products-simple/")
test_endpoint("GET", "/products-simple/5")
test_endpoint("POST", "/products-simple/", {
    "product_code": f"API_TEST_{datetime.now().strftime('%H%M%S')}",
    "product_name": "API Test Product",
    "mrp": 99.99
})

# Delivery (will fail - needs auth)
test_endpoint("GET", "/delivery/pending")

# Original products (will fail)
test_endpoint("GET", "/products/")

print("\n" + "="*50)
print("Testing complete!")