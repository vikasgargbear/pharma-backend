#!/usr/bin/env python3
"""Check API deployment status"""
import requests
import time

BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

endpoints = [
    "/",
    "/health",
    "/health/detailed",
    "/products/",
    "/api/v1/customers/",
    "/docs"
]

print("Checking API status...")
print("=" * 50)

for endpoint in endpoints:
    try:
        url = BASE_URL + endpoint
        response = requests.get(url, timeout=10)
        print(f"{endpoint:<25} - Status: {response.status_code}")
        if response.status_code == 502:
            print(f"  Error: {response.text[:100]}...")
    except Exception as e:
        print(f"{endpoint:<25} - Error: {str(e)}")

print("\nWaiting 30 seconds and trying again...")
time.sleep(30)

print("\nSecond attempt:")
print("=" * 50)

for endpoint in endpoints:
    try:
        url = BASE_URL + endpoint
        response = requests.get(url, timeout=10)
        print(f"{endpoint:<25} - Status: {response.status_code}")
    except Exception as e:
        print(f"{endpoint:<25} - Error: {str(e)}")