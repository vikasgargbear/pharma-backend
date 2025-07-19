#!/usr/bin/env python3
"""Check Railway deployment status"""

import requests
import time
import json

BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

def check_deployment():
    """Check if deployment is working"""
    endpoints = [
        ("/health", "Health Check"),
        ("/docs", "API Documentation"),
        ("/api/v1/inventory", "Inventory API"),
        ("/api/v1/sales-returns", "Sales Returns API"),
    ]
    
    print("Checking Railway Deployment Status")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    all_good = True
    
    for path, name in endpoints:
        url = f"{BASE_URL}{path}"
        try:
            response = requests.get(url, timeout=5)
            
            # Check if it's an Express error
            if "Cannot GET" in response.text:
                print(f"❌ {name}: Express.js error (Not FastAPI)")
                all_good = False
            elif response.status_code == 200:
                print(f"✅ {name}: OK")
            elif response.status_code == 307:
                print(f"↗️  {name}: Redirect (probably OK)")
            elif response.status_code == 404:
                # Check if it's FastAPI 404 or Express 404
                if "detail" in response.text:
                    print(f"⚠️  {name}: FastAPI 404 (API running)")
                else:
                    print(f"❌ {name}: Express 404")
                    all_good = False
            else:
                print(f"⚠️  {name}: Status {response.status_code}")
                
        except Exception as e:
            print(f"❌ {name}: {type(e).__name__}")
            all_good = False
    
    print("=" * 50)
    
    if all_good:
        print("✅ Deployment looks good!")
    else:
        print("❌ Deployment issues detected")
        print("\nPossible causes:")
        print("1. Railway is still deploying")
        print("2. Configuration mismatch") 
        print("3. Different service is running")
        
    return all_good

if __name__ == "__main__":
    # Check multiple times
    for i in range(3):
        if i > 0:
            print(f"\nWaiting 30 seconds before retry {i+1}/3...")
            time.sleep(30)
        
        if check_deployment():
            break