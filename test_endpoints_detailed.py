"""
Detailed endpoint testing with more coverage
"""
import requests
import json

BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

def test_get(path, description=""):
    """Test GET endpoint"""
    print(f"\n{'='*50}")
    print(f"GET {path} - {description}")
    try:
        response = requests.get(f"{BASE_URL}{path}")
        print(f"Status: {response.status_code}")
        if response.status_code < 500:
            print(f"Response: {json.dumps(response.json(), indent=2)[:100]}...")
        return response.status_code < 400
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_post(path, data, description=""):
    """Test POST endpoint"""
    print(f"\n{'='*50}")
    print(f"POST {path} - {description}")
    print(f"Data: {json.dumps(data, indent=2)[:100]}...")
    try:
        response = requests.post(f"{BASE_URL}{path}", json=data)
        print(f"Status: {response.status_code}")
        if response.status_code < 500:
            print(f"Response: {json.dumps(response.json(), indent=2)[:100]}...")
        return response.status_code < 400
    except Exception as e:
        print(f"Error: {e}")
        return False

# Test all endpoints
print("DETAILED ENDPOINT TEST")
print("="*50)

# Basic endpoints
test_get("/", "Root")
test_get("/health", "Health")
test_get("/health/detailed", "Detailed health")
test_get("/info", "API info")

# DB inspection
test_get("/db-inspect/tables", "List tables")
test_get("/db-inspect/table/products/columns", "Product columns")

# Organizations
test_get("/organizations/list", "List orgs")

# Test
test_get("/test/", "Test endpoint")
test_post("/test/echo", {"message": "hello"}, "Echo test")

# Products - try different approaches
test_get("/products/", "List products")
test_get("/products/1", "Get single product")

# Delivery
test_get("/delivery/pending", "Pending deliveries")
test_get("/delivery/stats", "Delivery stats")

# Try to find what's in db-inspect query
test_get("/db-inspect/query?sql=SELECT COUNT(*) FROM products", "Count products")