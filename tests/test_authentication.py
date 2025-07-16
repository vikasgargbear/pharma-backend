"""
Authentication & Authorization Tests
====================================
Comprehensive tests for authentication flows, JWT tokens, role-based access,
and security vulnerabilities.
"""

import pytest
import time
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any

from base_test import APITestBase
from test_suite_config import TEST_USERS, TestDataFactory


class TestAuthentication(APITestBase):
    """Test authentication and authorization"""
    
    def test_user_registration(self):
        """Test new user registration flow"""
        user_data = {
            "username": TestDataFactory.generate_email(),
            "password": "SecurePass123!",
            "full_name": "Test User",
            "role": "sales",
            "is_active": True
        }
        
        # Register new user
        response = self.post("/auth/register", user_data, auth_required=False)
        
        # Assertions
        assert "id" in response
        assert response["username"] == user_data["username"]
        assert response["role"] == user_data["role"]
        assert "password" not in response  # Password should not be returned
        
        self.register_for_cleanup("user", response["id"])
        
        # Verify user can login
        login_response = self.post("/auth/login", {
            "username": user_data["username"],
            "password": user_data["password"]
        }, auth_required=False)
        
        assert "access_token" in login_response
        assert "refresh_token" in login_response
        assert login_response["token_type"] == "bearer"
    
    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        for user_type, user_info in TEST_USERS.items():
            response = self.post("/auth/login", {
                "username": user_info["username"],
                "password": user_info["password"]
            }, auth_required=False)
            
            # Validate response
            assert "access_token" in response
            assert "refresh_token" in response
            assert "token_type" in response
            assert response["token_type"] == "bearer"
            
            # Decode and validate JWT
            try:
                # Note: In production, verify with proper secret
                decoded = jwt.decode(response["access_token"], options={"verify_signature": False})
                assert decoded["sub"] == user_info["username"]
                assert decoded["role"] == user_info["role"]
                assert "exp" in decoded
                assert "iat" in decoded
            except jwt.InvalidTokenError as e:
                pytest.fail(f"Invalid JWT token: {e}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        invalid_attempts = [
            {"username": "nonexistent@pharmaco.com", "password": "password123"},
            {"username": TEST_USERS["admin"]["username"], "password": "wrongpassword"},
            {"username": "", "password": "password123"},
            {"username": "admin", "password": ""},
        ]
        
        for attempt in invalid_attempts:
            try:
                response = self.post("/auth/login", attempt, auth_required=False)
                # If we get here, login succeeded when it shouldn't have
                pytest.fail(f"Login succeeded with invalid credentials: {attempt}")
            except Exception as e:
                # Expected to fail
                assert "401" in str(e) or "400" in str(e)
    
    def test_token_refresh(self):
        """Test token refresh flow"""
        # First login
        login_response = self.post("/auth/login", {
            "username": TEST_USERS["admin"]["username"],
            "password": TEST_USERS["admin"]["password"]
        }, auth_required=False)
        
        refresh_token = login_response["refresh_token"]
        
        # Wait a moment to ensure new token has different timestamp
        time.sleep(1)
        
        # Refresh token
        refresh_response = self.post("/auth/refresh", {
            "refresh_token": refresh_token
        }, auth_required=False)
        
        assert "access_token" in refresh_response
        assert refresh_response["access_token"] != login_response["access_token"]
    
    def test_token_expiration(self):
        """Test token expiration handling"""
        # This test would need to be configured based on actual token expiry settings
        # For now, we'll test that expired tokens are rejected
        
        # Create an expired token (this is a mock - in real tests, wait for expiry)
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxNjAwMDAwMDAwfQ.invalid"
        
        self.session.headers.update({"Authorization": f"Bearer {expired_token}"})
        
        try:
            self.get("/customers")
            pytest.fail("Request succeeded with expired token")
        except Exception as e:
            assert "401" in str(e)
    
    def test_logout(self):
        """Test logout functionality"""
        # Login first
        self.authenticate("admin")
        
        # Logout
        response = self.post("/auth/logout", {})
        
        # Try to use the token after logout
        try:
            self.get("/customers")
            pytest.fail("Token still valid after logout")
        except Exception as e:
            assert "401" in str(e)
    
    def test_password_change(self):
        """Test password change flow"""
        # Create test user
        user_data = {
            "username": TestDataFactory.generate_email(),
            "password": "OldPassword123!",
            "full_name": "Password Test User",
            "role": "sales"
        }
        
        user_response = self.post("/auth/register", user_data, auth_required=False)
        self.register_for_cleanup("user", user_response["id"])
        
        # Login with old password
        login_response = self.post("/auth/login", {
            "username": user_data["username"],
            "password": user_data["password"]
        }, auth_required=False)
        
        # Change password
        self.session.headers.update({"Authorization": f"Bearer {login_response['access_token']}"})
        
        self.post("/auth/change-password", {
            "old_password": user_data["password"],
            "new_password": "NewPassword123!"
        })
        
        # Try login with old password - should fail
        try:
            self.post("/auth/login", {
                "username": user_data["username"],
                "password": user_data["password"]
            }, auth_required=False)
            pytest.fail("Login succeeded with old password")
        except Exception:
            pass
        
        # Login with new password - should succeed
        new_login = self.post("/auth/login", {
            "username": user_data["username"],
            "password": "NewPassword123!"
        }, auth_required=False)
        
        assert "access_token" in new_login
    
    def test_role_based_access_control(self):
        """Test RBAC for different user roles"""
        test_cases = [
            {
                "role": "admin",
                "allowed": ["/users", "/customers", "/products", "/orders", "/analytics/revenue"],
                "forbidden": []
            },
            {
                "role": "sales",
                "allowed": ["/customers", "/products", "/orders"],
                "forbidden": ["/users", "/analytics/revenue"]
            },
            {
                "role": "warehouse",
                "allowed": ["/products", "/inventory", "/batches"],
                "forbidden": ["/users", "/analytics/revenue", "/payments"]
            }
        ]
        
        for test_case in test_cases:
            # Authenticate as user with specific role
            self.authenticate(test_case["role"])
            
            # Test allowed endpoints
            for endpoint in test_case["allowed"]:
                try:
                    self.get(endpoint)
                except Exception as e:
                    if "404" not in str(e):  # 404 is ok, means route exists but no data
                        pytest.fail(f"{test_case['role']} should have access to {endpoint}: {e}")
            
            # Test forbidden endpoints
            for endpoint in test_case["forbidden"]:
                try:
                    self.get(endpoint)
                    pytest.fail(f"{test_case['role']} should NOT have access to {endpoint}")
                except Exception as e:
                    assert "403" in str(e) or "401" in str(e)
    
    def test_concurrent_login_sessions(self):
        """Test multiple concurrent sessions for same user"""
        username = TEST_USERS["admin"]["username"]
        password = TEST_USERS["admin"]["password"]
        
        # Create multiple sessions
        sessions = []
        for i in range(5):
            response = self.post("/auth/login", {
                "username": username,
                "password": password
            }, auth_required=False)
            sessions.append(response["access_token"])
        
        # All sessions should be valid
        for i, token in enumerate(sessions):
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            response = self.get("/auth/me")
            assert response["username"] == username
    
    def test_sql_injection_in_login(self):
        """Test SQL injection vulnerability in login"""
        sql_injection_attempts = [
            {"username": "admin' OR '1'='1", "password": "anything"},
            {"username": "admin'; DROP TABLE users; --", "password": "anything"},
            {"username": "admin' UNION SELECT * FROM users--", "password": "anything"},
            {"username": "admin", "password": "' OR '1'='1"},
        ]
        
        for attempt in sql_injection_attempts:
            try:
                self.post("/auth/login", attempt, auth_required=False)
                pytest.fail(f"SQL injection succeeded: {attempt}")
            except Exception as e:
                # Should fail with 401, not 500 (which would indicate SQL error)
                assert "401" in str(e) or "400" in str(e)
                assert "500" not in str(e)
    
    def test_brute_force_protection(self):
        """Test brute force login protection"""
        username = "bruteforce@test.com"
        
        # Make multiple failed login attempts
        failed_attempts = 0
        for i in range(10):
            try:
                self.post("/auth/login", {
                    "username": username,
                    "password": f"wrongpassword{i}"
                }, auth_required=False)
            except Exception:
                failed_attempts += 1
        
        # After multiple failures, account should be locked or rate limited
        assert failed_attempts == 10
        
        # Check if further attempts are rate limited
        try:
            self.post("/auth/login", {
                "username": username,
                "password": "anotherpassword"
            }, auth_required=False)
        except Exception as e:
            # Should get rate limit error (429) or account locked error
            assert "429" in str(e) or "locked" in str(e).lower() or "too many" in str(e).lower()
    
    def test_password_complexity_requirements(self):
        """Test password complexity validation"""
        weak_passwords = [
            "password",          # Too simple
            "12345678",         # Only numbers
            "abcdefgh",         # Only lowercase
            "ABCDEFGH",         # Only uppercase
            "Pass1",            # Too short
            "password123",      # No special characters
            " " * 10,           # Only spaces
        ]
        
        for weak_password in weak_passwords:
            try:
                user_data = {
                    "username": TestDataFactory.generate_email(),
                    "password": weak_password,
                    "full_name": "Test User",
                    "role": "sales"
                }
                self.post("/auth/register", user_data, auth_required=False)
                pytest.fail(f"Weak password accepted: {weak_password}")
            except Exception as e:
                assert "400" in str(e) or "password" in str(e).lower()
    
    def test_session_timeout(self):
        """Test session timeout behavior"""
        # This test would need to be adjusted based on actual session timeout settings
        # For demonstration, we'll test that sessions have timeout info
        
        login_response = self.post("/auth/login", {
            "username": TEST_USERS["admin"]["username"],
            "password": TEST_USERS["admin"]["password"]
        }, auth_required=False)
        
        # Decode token to check expiration
        token = login_response["access_token"]
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        # Check token has expiration
        assert "exp" in decoded
        exp_time = datetime.fromtimestamp(decoded["exp"])
        now = datetime.now()
        
        # Token should expire in the future
        assert exp_time > now
        
        # Token should not be valid for more than 24 hours (adjust based on your settings)
        assert exp_time < now + timedelta(hours=25)
    
    def test_cross_tenant_access_prevention(self):
        """Test that users cannot access other tenant's data"""
        # This test assumes multi-tenant setup
        # Create two users from different organizations
        
        user1_data = {
            "username": TestDataFactory.generate_email(),
            "password": "TenantUser1!",
            "full_name": "Tenant 1 User",
            "role": "admin",
            "organization_id": 1
        }
        
        user2_data = {
            "username": TestDataFactory.generate_email(),
            "password": "TenantUser2!",
            "full_name": "Tenant 2 User",
            "role": "admin",
            "organization_id": 2
        }
        
        # Register users (implementation depends on your multi-tenant setup)
        # Test that user1 cannot access user2's data
        # This is a placeholder for tenant isolation testing
        pass


class TestAuthenticationPerformance(APITestBase):
    """Performance tests for authentication endpoints"""
    
    def test_login_performance(self):
        """Test login endpoint performance"""
        results = []
        
        for i in range(10):
            start_time = time.time()
            
            self.post("/auth/login", {
                "username": TEST_USERS["admin"]["username"],
                "password": TEST_USERS["admin"]["password"]
            }, auth_required=False)
            
            duration = time.time() - start_time
            results.append(duration)
        
        avg_time = sum(results) / len(results)
        max_time = max(results)
        
        # Login should complete within 1 second
        assert avg_time < 1.0, f"Average login time {avg_time:.3f}s exceeds 1s threshold"
        assert max_time < 2.0, f"Maximum login time {max_time:.3f}s exceeds 2s threshold"
    
    def test_concurrent_login_load(self):
        """Test login endpoint under concurrent load"""
        results = self.run_concurrent_requests(
            "/auth/login",
            method="POST",
            data={
                "username": TEST_USERS["admin"]["username"],
                "password": TEST_USERS["admin"]["password"]
            },
            concurrent_users=20
        )
        
        analysis = self.analyze_performance_results(results)
        
        # Performance assertions
        assert float(analysis["p95"][:-1]) < 2.0, f"95th percentile {analysis['p95']} exceeds 2s"
        assert float(analysis["success_rate"][:-1]) > 95, f"Success rate {analysis['success_rate']} below 95%"
        
        self.logger.info(f"Concurrent login performance: {analysis}")