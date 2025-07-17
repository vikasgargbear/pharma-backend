"""
Test ALL working endpoints after fixes
"""
import requests
import json
from datetime import datetime

BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

def test(method, path, data=None, expected=200):
    """Test endpoint"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            r = requests.get(url)
        else:
            r = requests.post(url, json=data)
        
        status = "✅" if r.status_code == expected else "❌"
        print(f"{status} {method} {path} - {r.status_code}")
        
        if r.status_code != expected and r.status_code < 500:
            print(f"   Response: {r.text[:100]}")
            
        return r.status_code == expected
    except Exception as e:
        print(f"❌ {method} {path} - Error: {e}")
        return False

print("COMPLETE API TEST - All Endpoints")
print("="*60)

success = 0
total = 0

# Basic API
tests = [
    ("GET", "/", None, 200),
    ("GET", "/health", None, 200),
    ("GET", "/health/detailed", None, 200),
    ("GET", "/info", None, 200),
]

# DB Inspection
tests.extend([
    ("GET", "/db-inspect/tables", None, 200),
    ("GET", "/db-inspect/table/products/columns", None, 200),
    ("GET", "/db-inspect/full-schema", None, 200),
    ("GET", "/db-inspect/query?sql=SELECT COUNT(*) FROM products", None, 200),
])

# Organizations
tests.extend([
    ("GET", "/organizations/list", None, 200),
])

# Test endpoints
tests.extend([
    ("GET", "/test/", None, 200),
    ("POST", "/test/echo", {"hello": "world"}, 200),
])

# Products Simple
tests.extend([
    ("GET", "/products-simple/", None, 200),
    ("GET", "/products-simple/5", None, 200),
    ("POST", "/products-simple/", {
        "product_code": f"TEST_{datetime.now().strftime('%H%M%S')}",
        "product_name": "Test Product",
        "mrp": 50.0
    }, 200),
])

# Original Products (should work now)
tests.extend([
    ("GET", "/products/", None, 200),
    ("GET", "/products/5", None, 200),
])

# Public Delivery (NEW)
tests.extend([
    ("GET", "/delivery-public/pending", None, 200),
    ("GET", "/delivery-public/stats", None, 200),
    ("GET", "/delivery-public/order/1/status", None, 404),  # Order might not exist
])

# Migrations
tests.extend([
    ("POST", "/migrations/run-org-id-migration", None, 200),
])

# Run all tests
for method, path, data, expected in tests:
    total += 1
    if test(method, path, data, expected):
        success += 1

print("\n" + "="*60)
print(f"RESULTS: {success}/{total} tests passed ({success/total*100:.1f}%)")
print("="*60)