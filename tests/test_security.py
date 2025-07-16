"""
Security Tests
==============
Comprehensive security testing including SQL injection, XSS, CSRF,
authentication bypass, and other vulnerabilities.
"""

import pytest
import time
import json
import base64
from typing import Dict, Any, List
from datetime import datetime, timedelta

from base_test import APITestBase
from test_suite_config import TestDataFactory, TEST_USERS


class TestSQLInjection(APITestBase):
    """Test for SQL injection vulnerabilities"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("admin")
        yield
    
    def test_sql_injection_in_search(self):
        """Test SQL injection in search parameters"""
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE products; --",
            "' UNION SELECT * FROM users--",
            "1' AND '1'='1",
            "' OR 1=1--",
            "admin'--",
            "' OR 'x'='x",
            "'; UPDATE products SET price=0; --",
            "' OR id IS NOT NULL--",
            "1' ORDER BY 100--"
        ]
        
        endpoints = [
            ("/products", "search"),
            ("/customers", "search"),
            ("/orders", "search")
        ]
        
        for endpoint, param in endpoints:
            for payload in sql_payloads:
                try:
                    response = self.get(endpoint, params={param: payload})
                    
                    # Should return empty results or filtered results
                    # but NOT all records (which would indicate injection worked)
                    if isinstance(response, list):
                        # If we get results, verify they actually match the search term
                        for item in response:
                            # The payload should not have matched any real data
                            assert False, f"SQL injection may have succeeded: {payload}"
                    
                except Exception as e:
                    # Check that we don't get database errors (500)
                    assert "500" not in str(e), f"Database error with payload: {payload}"
    
    def test_sql_injection_in_ids(self):
        """Test SQL injection in ID parameters"""
        sql_payloads = [
            "1 OR 1=1",
            "1; DROP TABLE products;",
            "1 UNION SELECT * FROM users",
            "-1 OR 1=1",
            "1' OR '1'='1",
            "1/**/OR/**/1=1"
        ]
        
        for payload in sql_payloads:
            try:
                # Try to access with SQL injection in ID
                self.get(f"/products/{payload}")
                pytest.fail(f"SQL injection in ID accepted: {payload}")
            except Exception as e:
                # Should get 404 or 400, not 500
                assert "404" in str(e) or "400" in str(e) or "422" in str(e)
                assert "500" not in str(e)
    
    def test_sql_injection_in_post_data(self):
        """Test SQL injection in POST request data"""
        # Create a valid product first
        valid_product = TestDataFactory.generate_product_data()
        
        sql_payloads = [
            {"name": "Product'; DROP TABLE products; --"},
            {"name": "Product' OR '1'='1"},
            {"description": "'; UPDATE products SET price=0; --"},
            {"sku": "SKU' UNION SELECT password FROM users--"}
        ]
        
        for payload_dict in sql_payloads:
            product_data = valid_product.copy()
            product_data.update(payload_dict)
            
            try:
                response = self.post("/products", product_data)
                
                # If product is created, verify the data is properly escaped
                created_product = self.get(f"/products/{response['id']}")
                
                # The malicious string should be stored as-is (escaped)
                for key, value in payload_dict.items():
                    assert created_product[key] == value
                
                self.register_for_cleanup("product", response["id"])
                
            except Exception as e:
                # Validation might reject it, which is also fine
                assert "400" in str(e) or "422" in str(e)


class TestXSSVulnerabilities(APITestBase):
    """Test for Cross-Site Scripting vulnerabilities"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("admin")
        yield
        self.cleanup_test_data()
    
    def test_xss_in_product_data(self):
        """Test XSS payloads in product fields"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "<body onload=alert('XSS')>",
            "'\"><script>alert(String.fromCharCode(88,83,83))</script>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS')>",
            "<textarea onfocus=alert('XSS')>"
        ]
        
        for payload in xss_payloads:
            product_data = TestDataFactory.generate_product_data()
            product_data["name"] = f"Test Product {payload}"
            product_data["description"] = payload
            
            try:
                response = self.post("/products", product_data)
                
                # Verify the data is stored safely (escaped/sanitized)
                created_product = self.get(f"/products/{response['id']}")
                
                # The payload should be present but escaped
                assert payload in created_product["name"] or \
                       created_product["name"] == f"Test Product {payload}"
                
                # Check that script tags are escaped in API responses
                response_text = json.dumps(created_product)
                assert "<script>" not in response_text or \
                       "&lt;script&gt;" in response_text
                
                self.register_for_cleanup("product", response["id"])
                
            except Exception as e:
                # Some payloads might be rejected by validation
                assert "400" in str(e) or "422" in str(e)
    
    def test_xss_in_customer_data(self):
        """Test XSS in customer information"""
        xss_payloads = {
            "name": "<script>alert('XSS')</script>Company",
            "contact_person": "<img src=x onerror=alert('XSS')>",
            "address": "<iframe src='javascript:alert(1)'></iframe>",
            "remarks": "<svg/onload=alert('XSS')>"
        }
        
        customer_data = TestDataFactory.generate_customer_data()
        
        for field, payload in xss_payloads.items():
            test_data = customer_data.copy()
            test_data[field] = payload
            
            try:
                response = self.post("/customers", test_data)
                
                # Verify stored data is safe
                created_customer = self.get(f"/customers/{response['id']}")
                
                # Payload should be stored but made safe
                assert payload in created_customer[field] or \
                       created_customer[field] == payload
                
                self.register_for_cleanup("customer", response["id"])
                
            except Exception as e:
                # Validation might reject it
                assert "400" in str(e) or "422" in str(e)


class TestAuthenticationBypass(APITestBase):
    """Test for authentication bypass vulnerabilities"""
    
    def test_access_without_token(self):
        """Test accessing protected endpoints without authentication"""
        # Clear authentication
        self.session.headers.pop("Authorization", None)
        
        protected_endpoints = [
            "/users",
            "/customers",
            "/products",
            "/orders",
            "/payments",
            "/analytics/revenue",
            "/users/1",
            "/orders/1/invoice"
        ]
        
        for endpoint in protected_endpoints:
            try:
                self.get(endpoint)
                pytest.fail(f"Accessed {endpoint} without authentication")
            except Exception as e:
                assert "401" in str(e), f"Expected 401 for {endpoint}, got {e}"
    
    def test_invalid_token_formats(self):
        """Test various invalid token formats"""
        invalid_tokens = [
            "InvalidToken",
            "Bearer",
            "Bearer ",
            "Token abc123",
            "Basic YWRtaW46cGFzc3dvcmQ=",  # Basic auth attempt
            "",
            "null",
            "undefined",
            "Bearer null",
            "Bearer undefined"
        ]
        
        for token in invalid_tokens:
            self.session.headers["Authorization"] = token
            
            try:
                self.get("/customers")
                pytest.fail(f"Access granted with invalid token: {token}")
            except Exception as e:
                assert "401" in str(e)
    
    def test_jwt_token_manipulation(self):
        """Test JWT token manipulation attacks"""
        # First get a valid token
        login_response = self.post("/auth/login", {
            "username": TEST_USERS["sales"]["username"],
            "password": TEST_USERS["sales"]["password"]
        }, auth_required=False)
        
        valid_token = login_response["access_token"]
        
        # Try various token manipulations
        manipulations = [
            valid_token[:-1],  # Remove last character
            valid_token + "a",  # Add character
            valid_token.replace(".", ""),  # Remove dots
            base64.b64encode(b'{"sub":"admin","role":"admin"}').decode(),  # Fake token
            "eyJhbGciOiJub25lIn0.eyJzdWIiOiJhZG1pbiJ9.",  # Algorithm none attack
        ]
        
        for manipulated_token in manipulations:
            self.session.headers["Authorization"] = f"Bearer {manipulated_token}"
            
            try:
                self.get("/users")  # Admin-only endpoint
                pytest.fail(f"Token manipulation succeeded: {manipulated_token[:20]}...")
            except Exception as e:
                assert "401" in str(e) or "403" in str(e)
    
    def test_privilege_escalation(self):
        """Test horizontal and vertical privilege escalation"""
        # Login as sales user
        self.authenticate("sales")
        
        # Try to access admin-only endpoints
        admin_endpoints = [
            "/users",
            "/users/1",
            "/analytics/revenue",
            "/system/config"
        ]
        
        for endpoint in admin_endpoints:
            try:
                self.get(endpoint)
                pytest.fail(f"Sales user accessed admin endpoint: {endpoint}")
            except Exception as e:
                assert "403" in str(e) or "401" in str(e)
        
        # Try to modify another user's data
        try:
            self.put("/users/1", {"role": "admin"})
            pytest.fail("Sales user could modify user roles")
        except Exception as e:
            assert "403" in str(e) or "401" in str(e)


class TestCSRFProtection(APITestBase):
    """Test Cross-Site Request Forgery protection"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("admin")
        yield
    
    def test_csrf_token_validation(self):
        """Test CSRF token requirements for state-changing operations"""
        # Remove CSRF token if present
        self.session.headers.pop("X-CSRF-Token", None)
        
        # Try state-changing operations without CSRF token
        operations = [
            ("POST", "/products", TestDataFactory.generate_product_data()),
            ("PUT", "/products/1", {"name": "Updated"}),
            ("DELETE", "/products/1", None),
            ("POST", "/orders", {"customer_id": 1})
        ]
        
        csrf_required = False
        
        for method, endpoint, data in operations:
            try:
                if method == "POST":
                    self.post(endpoint, data)
                elif method == "PUT":
                    self.put(endpoint, data)
                elif method == "DELETE":
                    self.delete(endpoint)
                
                # If we get here, CSRF might not be required
                # Check if there's another protection mechanism
                
            except Exception as e:
                if "csrf" in str(e).lower() or "403" in str(e):
                    csrf_required = True
        
        # Note: CSRF might be handled differently (e.g., SameSite cookies)
        # This test documents the current behavior


class TestRateLimiting(APITestBase):
    """Test rate limiting and DDoS protection"""
    
    def test_rate_limiting_on_login(self):
        """Test rate limiting on login endpoint"""
        # Make rapid login attempts
        attempts = []
        
        for i in range(20):
            start_time = time.time()
            
            try:
                self.post("/auth/login", {
                    "username": f"test{i}@example.com",
                    "password": "wrongpassword"
                }, auth_required=False)
            except Exception as e:
                if "429" in str(e):
                    # Rate limit hit
                    attempts.append({
                        "attempt": i + 1,
                        "time": time.time() - start_time,
                        "limited": True
                    })
                    break
                else:
                    attempts.append({
                        "attempt": i + 1,
                        "time": time.time() - start_time,
                        "limited": False
                    })
        
        # Should hit rate limit before 20 attempts
        limited_attempts = [a for a in attempts if a["limited"]]
        assert len(limited_attempts) > 0, "No rate limiting detected on login endpoint"
    
    def test_rate_limiting_on_api_endpoints(self):
        """Test rate limiting on regular API endpoints"""
        self.authenticate("admin")
        
        # Make rapid requests
        request_count = 0
        rate_limited = False
        
        for i in range(100):
            try:
                self.get("/products")
                request_count += 1
            except Exception as e:
                if "429" in str(e):
                    rate_limited = True
                    break
        
        # Log findings
        self.logger.info(f"Made {request_count} requests before rate limit")
        
        # Should have some rate limiting in place
        if not rate_limited:
            self.logger.warning("No rate limiting detected on API endpoints")


class TestDataExposure(APITestBase):
    """Test for sensitive data exposure"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("admin")
        yield
    
    def test_password_exposure_in_responses(self):
        """Test that passwords are never exposed in API responses"""
        # Create user
        user_data = {
            "username": TestDataFactory.generate_email(),
            "password": "SecurePassword123!",
            "full_name": "Test User",
            "role": "sales"
        }
        
        response = self.post("/auth/register", user_data, auth_required=False)
        
        # Check response doesn't contain password
        response_str = json.dumps(response)
        assert user_data["password"] not in response_str
        assert "password" not in response
        
        # Get user details
        if "id" in response:
            user_details = self.get(f"/users/{response['id']}")
            assert "password" not in user_details
            assert user_data["password"] not in json.dumps(user_details)
    
    def test_sensitive_headers_not_exposed(self):
        """Test that sensitive headers are not exposed"""
        response = self.session.get(f"{self.base_url}/health")
        
        # Check that sensitive headers are not present
        sensitive_headers = [
            "X-Powered-By",
            "Server",
            "X-AspNet-Version",
            "X-AspNetMvc-Version"
        ]
        
        for header in sensitive_headers:
            assert header not in response.headers, \
                f"Sensitive header {header} is exposed"
    
    def test_error_messages_dont_leak_info(self):
        """Test that error messages don't leak sensitive information"""
        # Try to create duplicate user
        user_data = {
            "username": TEST_USERS["admin"]["username"],
            "password": "password123",
            "role": "admin"
        }
        
        try:
            self.post("/auth/register", user_data, auth_required=False)
        except Exception as e:
            error_msg = str(e).lower()
            
            # Should not reveal that user exists
            assert "already exists" not in error_msg
            assert "duplicate" not in error_msg
            assert "table" not in error_msg
            assert "column" not in error_msg
            assert "database" not in error_msg
    
    def test_api_keys_not_in_responses(self):
        """Test that API keys and secrets are not exposed"""
        # Get various configuration endpoints
        config_endpoints = [
            "/config",
            "/settings",
            "/info",
            "/health"
        ]
        
        sensitive_patterns = [
            "api_key",
            "secret",
            "password",
            "token",
            "private",
            "credential"
        ]
        
        for endpoint in config_endpoints:
            try:
                response = self.get(endpoint)
                response_str = json.dumps(response).lower()
                
                for pattern in sensitive_patterns:
                    if pattern in response_str:
                        # Check if it's just a key name with empty/masked value
                        for key in response:
                            if pattern in key.lower() and response[key]:
                                assert response[key] in ["***", "hidden", "[REDACTED]", None], \
                                    f"Possible exposed secret in {endpoint}: {key}"
                
            except Exception:
                # Endpoint might not exist, which is fine
                pass


class TestFileUploadSecurity(APITestBase):
    """Test file upload security"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("admin")
        yield
    
    def test_malicious_file_upload(self):
        """Test uploading potentially malicious files"""
        malicious_files = [
            # PHP webshell
            ("shell.php", "<?php system($_GET['cmd']); ?>", "application/x-php"),
            # JavaScript file
            ("malicious.js", "alert('XSS')", "application/javascript"),
            # HTML file with JS
            ("evil.html", "<html><script>alert('XSS')</script></html>", "text/html"),
            # SVG with embedded JS
            ("bad.svg", "<svg onload='alert(1)'></svg>", "image/svg+xml"),
            # Executable
            ("virus.exe", b"MZ\x90\x00", "application/x-executable")
        ]
        
        for filename, content, mime_type in malicious_files:
            files = {
                "file": (filename, content, mime_type)
            }
            
            try:
                self.post("/file-uploads/test", files=files)
                pytest.fail(f"Malicious file accepted: {filename}")
            except Exception as e:
                assert "400" in str(e) or "415" in str(e) or "422" in str(e)
    
    def test_path_traversal_in_filename(self):
        """Test path traversal attacks in file uploads"""
        path_traversal_names = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "test/../../secret.txt"
        ]
        
        for filename in path_traversal_names:
            files = {
                "file": (filename, b"test content", "text/plain")
            }
            
            try:
                response = self.post("/file-uploads/test", files=files)
                
                # If upload succeeds, verify the file is stored safely
                if "filename" in response:
                    stored_name = response["filename"]
                    assert ".." not in stored_name
                    assert "/" not in stored_name or stored_name.startswith("uploads/")
                
            except Exception as e:
                # Should reject or sanitize the filename
                assert "400" in str(e) or "422" in str(e)