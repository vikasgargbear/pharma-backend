"""
Test all API endpoints systematically
"""
import requests
import json
from datetime import datetime

BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"
ORG_ID = "12de5e22-eee7-4d25-b3a7-d16d01c6170f"

def test_endpoint(method, path, data=None, description=""):
    """Test a single endpoint"""
    url = f"{BASE_URL}{path}"
    print(f"\n{'='*60}")
    print(f"Testing: {method} {path}")
    if description:
        print(f"Description: {description}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        elif method == "PUT":
            response = requests.put(url, json=data, headers={"Content-Type": "application/json"})
        elif method == "DELETE":
            response = requests.delete(url)
        
        print(f"Status: {response.status_code}")
        
        try:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)[:200]}...")
        except:
            print(f"Response: {response.text[:200]}...")
            
        return response.status_code < 400
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    """Test all endpoints"""
    results = {"working": [], "failing": []}
    
    # Basic endpoints
    endpoints = [
        ("GET", "/", None, "Root endpoint"),
        ("GET", "/health", None, "Health check"),
        ("GET", "/docs", None, "API documentation"),
        
        # Products endpoints
        ("GET", "/products/", None, "List products"),
        ("POST", "/products/", {
            "org_id": ORG_ID,
            "product_code": f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "product_name": "Test Product",
            "hsn_code": "30049099",
            "mrp": 100.0
        }, "Create product"),
        
        # Delivery endpoints
        ("GET", "/delivery/status", None, "Delivery status"),
        
        # DB inspection endpoints
        ("GET", "/db-inspect/tables", None, "List database tables"),
        
        # Organizations endpoints
        ("GET", "/organizations/list", None, "List organizations"),
        
        # Test endpoints
        ("GET", "/test/", None, "Test endpoint"),
        
        # Migration endpoints
        ("GET", "/migrations/run-org-id-migration", None, "Migration status"),
    ]
    
    print("Testing Full API Endpoints")
    print("="*60)
    
    for method, path, data, desc in endpoints:
        success = test_endpoint(method, path, data, desc)
        if success:
            results["working"].append(f"{method} {path}")
        else:
            results["failing"].append(f"{method} {path}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"\n✅ Working Endpoints ({len(results['working'])}):")
    for endpoint in results["working"]:
        print(f"  - {endpoint}")
    
    print(f"\n❌ Failing Endpoints ({len(results['failing'])}):")
    for endpoint in results["failing"]:
        print(f"  - {endpoint}")

if __name__ == "__main__":
    main()