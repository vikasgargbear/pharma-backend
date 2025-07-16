#!/usr/bin/env python3
"""
Standalone Test Runner with Mock Server
======================================
Runs the actual test suite with a mock server to demonstrate
real test execution without backend dependencies.
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add tests directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock responses for different endpoints
MOCK_RESPONSES = {
    "/health": {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    },
    "/auth/login": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh",
        "token_type": "bearer"
    },
    "/auth/register": {
        "id": 1,
        "username": "test@example.com",
        "role": "sales",
        "is_active": True
    },
    "/products": [
        {
            "id": 1,
            "name": "Paracetamol 500mg",
            "sku": "PAR500",
            "category": "Tablet",
            "gst_rate": 12,
            "selling_price": 10.50,
            "is_active": True
        },
        {
            "id": 2,
            "name": "Amoxicillin 250mg",
            "sku": "AMX250",
            "category": "Capsule",
            "gst_rate": 12,
            "selling_price": 25.00,
            "is_active": True
        }
    ],
    "/customers": [
        {
            "id": 1,
            "name": "Test Pharmacy",
            "phone": "+919876543210",
            "email": "test@pharmacy.com",
            "gst_number": "27ABCDE1234F1Z5",
            "credit_limit": 50000,
            "is_active": True
        }
    ],
    "/orders": {
        "id": 1,
        "customer_id": 1,
        "order_date": datetime.now().isoformat(),
        "total_amount": 1180.00,
        "status": "pending",
        "items": []
    }
}


class MockAPIHandler(BaseHTTPRequestHandler):
    """Mock API request handler"""
    
    def do_GET(self):
        """Handle GET requests"""
        path = urlparse(self.path).path
        
        # Add artificial delay to simulate network
        time.sleep(0.05)
        
        if path in MOCK_RESPONSES:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = MOCK_RESPONSES[path]
            self.wfile.write(json.dumps(response).encode())
        elif path.startswith("/products/") or path.startswith("/customers/"):
            # Mock individual resource
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            resource_id = path.split("/")[-1]
            response = {"id": int(resource_id), "name": f"Mock Resource {resource_id}"}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        path = urlparse(self.path).path
        
        # Add artificial delay
        time.sleep(0.1)
        
        if path in MOCK_RESPONSES:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = MOCK_RESPONSES[path]
            self.wfile.write(json.dumps(response).encode())
        else:
            # Mock successful creation
            self.send_response(201)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {"id": 1, "status": "created"}
            self.wfile.write(json.dumps(response).encode())
    
    def do_PUT(self):
        """Handle PUT requests"""
        self.do_POST()  # Similar handling
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        self.send_response(204)
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress request logging"""
        pass


def start_mock_server(port=8000):
    """Start mock API server in background"""
    server = HTTPServer(('localhost', port), MockAPIHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server


def run_actual_tests():
    """Run actual test suite against mock server"""
    print("\n" + "="*80)
    print("RUNNING ACTUAL TEST SUITE WITH MOCK SERVER")
    print("="*80 + "\n")
    
    # Start mock server
    print("Starting mock API server on http://localhost:8000...")
    server = start_mock_server()
    time.sleep(1)  # Give server time to start
    
    # Import and run actual tests
    try:
        # Run pytest with our test modules
        import subprocess
        
        test_modules = [
            "tests/test_authentication.py::TestAuthentication::test_login_valid_credentials",
            "tests/test_authentication.py::TestAuthentication::test_login_invalid_credentials",
            "tests/test_authentication.py::TestAuthentication::test_token_refresh",
            "tests/test_core_business.py::TestProducts::test_create_product",
            "tests/test_core_business.py::TestCustomers::test_create_customer",
            "tests/test_security.py::TestSQLInjection::test_sql_injection_in_search",
        ]
        
        results_dir = Path("test_results")
        results_dir.mkdir(exist_ok=True)
        
        # Run selected tests
        cmd = [
            "python", "-m", "pytest",
            "-v",
            "--tb=short",
            "--json-report",
            f"--json-report-file={results_dir}/actual_test_results.json",
            "--maxfail=10"  # Stop after 10 failures
        ] + test_modules
        
        print("Running selected test cases...\n")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        # Parse and display results
        json_report_path = results_dir / "actual_test_results.json"
        if json_report_path.exists():
            with open(json_report_path, "r") as f:
                test_results = json.load(f)
            
            print("\n" + "="*80)
            print("TEST RESULTS SUMMARY")
            print("="*80)
            
            summary = test_results.get("summary", {})
            print(f"\nTotal Tests: {summary.get('total', 0)}")
            print(f"Passed: {summary.get('passed', 0)}")
            print(f"Failed: {summary.get('failed', 0)}")
            print(f"Skipped: {summary.get('skipped', 0)}")
            print(f"Duration: {test_results.get('duration', 0):.2f}s")
        
    except ImportError:
        print("\nPytest not found. Running simplified test demonstration...")
        
        # Run simplified test demonstration
        from test_suite_config import TestDataFactory
        
        print("\nDemonstrating test data generation:")
        print("-" * 40)
        
        # Show product data generation
        product = TestDataFactory.generate_product_data()
        print("\nGenerated Product Data:")
        print(json.dumps(product, indent=2))
        
        # Show customer data generation
        customer = TestDataFactory.generate_customer_data()
        print("\nGenerated Customer Data:")
        print(json.dumps(customer, indent=2))
        
        # Show GST number validation
        print("\nGenerated GST Numbers:")
        for i in range(3):
            print(f"  {TestDataFactory.generate_gst_number()}")
        
        print("\nGenerated Phone Numbers:")
        for i in range(3):
            print(f"  {TestDataFactory.generate_phone_number()}")
    
    finally:
        print("\n" + "="*80)
        print("Test execution complete!")
        print("="*80)
        
        print("\nNext Steps:")
        print("1. Fix backend import issues")
        print("2. Install test dependencies: pip install -r tests/requirements-test.txt")
        print("3. Run full test suite: python tests/run_enterprise_tests.py")


if __name__ == "__main__":
    run_actual_tests()