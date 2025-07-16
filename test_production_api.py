#!/usr/bin/env python3
"""
Production API Testing Script
Tests all API endpoints after deployment to Supabase/Railway/Render
"""
import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://your-backend-url.railway.app"  # Update with your deployed URL
API_KEY = "your-api-key"  # Update if using API key authentication

# Test user credentials
TEST_USER = {
    "email": "testuser@pharma.com",
    "password": "TestPassword123!",
    "full_name": "Test User",
    "role": "employee"
}

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test_header(test_name):
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}Testing: {test_name}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

def print_result(endpoint, method, status_code, expected_status, response_time=None):
    if status_code == expected_status:
        print(f"{GREEN}✓ {method} {endpoint} - Status: {status_code}{RESET}", end="")
    else:
        print(f"{RED}✗ {method} {endpoint} - Status: {status_code} (Expected: {expected_status}){RESET}", end="")
    
    if response_time:
        print(f" - Response time: {response_time:.2f}ms")
    else:
        print()

class APITester:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.token = None
        self.test_data = {}

    def test_health_check(self):
        """Test if the API is running"""
        print_test_header("Health Check")
        try:
            start_time = datetime.now()
            response = self.session.get(f"{self.base_url}/health")
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            print_result("/health", "GET", response.status_code, 200, response_time)
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Database: {data.get('database', 'Unknown')}")
                print(f"  Status: {data.get('status', 'Unknown')}")
                return True
            return False
        except Exception as e:
            print(f"{RED}✗ Health check failed: {str(e)}{RESET}")
            return False

    def test_user_registration(self):
        """Test user registration"""
        print_test_header("User Registration")
        try:
            response = self.session.post(
                f"{self.base_url}/api/users",
                json=TEST_USER
            )
            print_result("/api/users", "POST", response.status_code, 201)
            
            if response.status_code == 201:
                self.test_data['user'] = response.json()
                print(f"  User ID: {self.test_data['user'].get('user_id')}")
                return True
            else:
                print(f"  Error: {response.text}")
            return False
        except Exception as e:
            print(f"{RED}✗ Registration failed: {str(e)}{RESET}")
            return False

    def test_user_login(self):
        """Test user login"""
        print_test_header("User Login")
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"]
                }
            )
            print_result("/api/auth/login", "POST", response.status_code, 200)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                print(f"  Token obtained: {'Yes' if self.token else 'No'}")
                return True
            else:
                print(f"  Error: {response.text}")
            return False
        except Exception as e:
            print(f"{RED}✗ Login failed: {str(e)}{RESET}")
            return False

    def test_products_crud(self):
        """Test Products CRUD operations"""
        print_test_header("Products CRUD")
        
        # Create product
        product_data = {
            "name": "Test Medicine",
            "brand": "Test Brand",
            "category": "Tablets",
            "mrp": 100.00,
            "sale_price": 90.00,
            "current_stock": 100,
            "unit": "Strip"
        }
        
        try:
            # CREATE
            response = self.session.post(f"{self.base_url}/api/products", json=product_data)
            print_result("/api/products", "POST", response.status_code, 201)
            
            if response.status_code == 201:
                self.test_data['product'] = response.json()
                product_id = self.test_data['product'].get('product_id')
                
                # READ
                response = self.session.get(f"{self.base_url}/api/products/{product_id}")
                print_result(f"/api/products/{product_id}", "GET", response.status_code, 200)
                
                # LIST
                response = self.session.get(f"{self.base_url}/api/products")
                print_result("/api/products", "GET", response.status_code, 200)
                
                # UPDATE
                update_data = {"sale_price": 85.00}
                response = self.session.put(f"{self.base_url}/api/products/{product_id}", json=update_data)
                print_result(f"/api/products/{product_id}", "PUT", response.status_code, 200)
                
                # DELETE
                response = self.session.delete(f"{self.base_url}/api/products/{product_id}")
                print_result(f"/api/products/{product_id}", "DELETE", response.status_code, 200)
                
                return True
            return False
        except Exception as e:
            print(f"{RED}✗ Products test failed: {str(e)}{RESET}")
            return False

    def test_customers_crud(self):
        """Test Customers CRUD operations"""
        print_test_header("Customers CRUD")
        
        customer_data = {
            "customer_name": "Test Pharmacy",
            "contact_person": "John Doe",
            "contact_phone": "9876543210",
            "email": "test@pharmacy.com",
            "address": "123 Test Street",
            "city": "Test City",
            "state": "Test State",
            "license_number": "TEST123"
        }
        
        try:
            # CREATE
            response = self.session.post(f"{self.base_url}/api/customers", json=customer_data)
            print_result("/api/customers", "POST", response.status_code, 201)
            
            if response.status_code == 201:
                self.test_data['customer'] = response.json()
                customer_id = self.test_data['customer'].get('customer_id')
                
                # READ
                response = self.session.get(f"{self.base_url}/api/customers/{customer_id}")
                print_result(f"/api/customers/{customer_id}", "GET", response.status_code, 200)
                
                # LIST
                response = self.session.get(f"{self.base_url}/api/customers")
                print_result("/api/customers", "GET", response.status_code, 200)
                
                return True
            return False
        except Exception as e:
            print(f"{RED}✗ Customers test failed: {str(e)}{RESET}")
            return False

    def test_orders_workflow(self):
        """Test complete order workflow"""
        print_test_header("Orders Workflow")
        
        # First create necessary data
        # Create product
        product_data = {
            "name": "Order Test Medicine",
            "brand": "Test Brand",
            "category": "Tablets",
            "mrp": 100.00,
            "sale_price": 90.00,
            "current_stock": 100,
            "unit": "Strip"
        }
        
        try:
            # Create product
            response = self.session.post(f"{self.base_url}/api/products", json=product_data)
            if response.status_code != 201:
                print(f"{RED}Failed to create test product{RESET}")
                return False
            
            product_id = response.json().get('product_id')
            
            # Create order
            order_data = {
                "customer_id": self.test_data.get('customer', {}).get('customer_id', 1),
                "status": "placed",
                "payment_status": "pending",
                "total_amount": 900.00,
                "discount_amount": 0,
                "tax_amount": 0,
                "notes": "Test order"
            }
            
            response = self.session.post(f"{self.base_url}/api/orders", json=order_data)
            print_result("/api/orders", "POST", response.status_code, 201)
            
            if response.status_code == 201:
                order_id = response.json().get('order_id')
                
                # Add order items
                order_item_data = {
                    "order_id": order_id,
                    "product_id": product_id,
                    "batch_id": 1,  # Assuming batch exists
                    "quantity": 10,
                    "unit_price": 90.00,
                    "subtotal": 900.00
                }
                
                response = self.session.post(f"{self.base_url}/api/order-items", json=order_item_data)
                print_result("/api/order-items", "POST", response.status_code, 201)
                
                # Get order details
                response = self.session.get(f"{self.base_url}/api/orders/{order_id}")
                print_result(f"/api/orders/{order_id}", "GET", response.status_code, 200)
                
                return True
            return False
        except Exception as e:
            print(f"{RED}✗ Orders workflow test failed: {str(e)}{RESET}")
            return False

    def test_file_upload(self):
        """Test file upload functionality"""
        print_test_header("File Upload")
        
        # Create a test file
        test_file_content = b"Test PDF content"
        files = {'file': ('test.pdf', test_file_content, 'application/pdf')}
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/files/upload",
                files=files,
                data={'category': 'test'}
            )
            print_result("/api/files/upload", "POST", response.status_code, 201)
            
            if response.status_code == 201:
                file_data = response.json()
                print(f"  File ID: {file_data.get('file_id')}")
                print(f"  File URL: {file_data.get('file_url')}")
                return True
            return False
        except Exception as e:
            print(f"{RED}✗ File upload test failed: {str(e)}{RESET}")
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print(f"\n{YELLOW}🚀 Starting Production API Tests{RESET}")
        print(f"{YELLOW}Base URL: {self.base_url}{RESET}")
        print(f"{YELLOW}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
        
        results = {
            "Health Check": self.test_health_check(),
            "User Registration": self.test_user_registration(),
            "User Login": self.test_user_login(),
            "Products CRUD": self.test_products_crud(),
            "Customers CRUD": self.test_customers_crud(),
            "Orders Workflow": self.test_orders_workflow(),
            "File Upload": self.test_file_upload()
        }
        
        # Summary
        print(f"\n{BLUE}{'=' * 60}{RESET}")
        print(f"{BLUE}TEST SUMMARY{RESET}")
        print(f"{BLUE}{'=' * 60}{RESET}")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = f"{GREEN}PASSED{RESET}" if result else f"{RED}FAILED{RESET}"
            print(f"{test_name}: {status}")
        
        print(f"\n{YELLOW}Total: {passed}/{total} tests passed{RESET}")
        
        if passed == total:
            print(f"{GREEN}✅ All tests passed! Your API is ready for production.{RESET}")
        else:
            print(f"{RED}❌ Some tests failed. Please check the logs above.{RESET}")
        
        return passed == total

def main():
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
    
    print(f"{YELLOW}Make sure to update BASE_URL with your deployed backend URL!{RESET}")
    print(f"{YELLOW}Current URL: {BASE_URL}{RESET}")
    
    tester = APITester(BASE_URL)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()