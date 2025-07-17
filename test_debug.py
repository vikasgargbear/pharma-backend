"""
Debug test to see actual errors
"""
import requests

# Test the root endpoint first
print("Testing root endpoint...")
response = requests.get("https://pharma-backend-production-0c09.up.railway.app/")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Test health endpoint
print("\nTesting health endpoint...")
response = requests.get("https://pharma-backend-production-0c09.up.railway.app/health")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Test creating a minimal product
print("\nTesting product creation...")
product_data = {
    "product_code": "DEBUG001",
    "product_name": "Debug Product"
}

response = requests.post(
    "https://pharma-backend-production-0c09.up.railway.app/products/",
    json=product_data
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")  # First 500 chars