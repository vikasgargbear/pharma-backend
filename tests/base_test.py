"""
Base Test Class
===============
Foundation for all API tests with common functionality including
authentication, request helpers, and assertion methods.
"""

import time
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import pytest
from functools import wraps

from .test_suite_config import (
    Environment, ENVIRONMENTS, TestConfig, TestMetrics,
    TEST_USERS
)


class APITestBase:
    """Base class for all API tests"""
    
    def __init__(self, environment: Environment = Environment.LOCAL):
        self.env = environment
        self.config = ENVIRONMENTS[environment]
        self.base_url = self.config.base_url
        self.session = self._create_session()
        self.metrics = TestMetrics()
        self.logger = self._setup_logger()
        self.auth_tokens = {}
        self.test_data_cleanup = []
        
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry logic"""
        session = requests.Session()
        
        # Configure retries
        retry_strategy = Retry(
            total=self.config.retry_count,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "PharmaAPI-TestSuite/1.0"
        })
        
        return session
    
    def _setup_logger(self) -> logging.Logger:
        """Setup test logger"""
        logger = logging.getLogger(f"api_test_{self.env.value}")
        logger.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(
            f"test_results/api_test_{self.env.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def authenticate(self, user_type: str = "admin") -> str:
        """Authenticate and get token"""
        if user_type in self.auth_tokens:
            return self.auth_tokens[user_type]
        
        user = TEST_USERS.get(user_type)
        if not user:
            raise ValueError(f"Unknown user type: {user_type}")
        
        response = self.post("/auth/login", {
            "username": user["username"],
            "password": user["password"]
        }, auth_required=False)
        
        token = response["access_token"]
        self.auth_tokens[user_type] = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        return token
    
    def measure_time(func):
        """Decorator to measure execution time"""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            try:
                result = func(self, *args, **kwargs)
                duration = time.time() - start_time
                self.logger.info(f"{func.__name__} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                self.logger.error(f"{func.__name__} failed after {duration:.3f}s: {str(e)}")
                raise
        return wrapper
    
    @measure_time
    def get(self, endpoint: str, params: Dict[str, Any] = None, 
            auth_required: bool = True) -> Dict[str, Any]:
        """Make GET request"""
        url = f"{self.base_url}{endpoint}"
        
        headers = self.session.headers.copy()
        if not auth_required:
            headers.pop("Authorization", None)
        
        response = self.session.get(
            url, 
            params=params, 
            headers=headers,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl
        )
        
        self._log_request_response("GET", url, params, response)
        response.raise_for_status()
        
        return response.json() if response.text else {}
    
    @measure_time
    def post(self, endpoint: str, data: Dict[str, Any] = None, 
             files: Dict[str, Any] = None, auth_required: bool = True) -> Dict[str, Any]:
        """Make POST request"""
        url = f"{self.base_url}{endpoint}"
        
        headers = self.session.headers.copy()
        if not auth_required:
            headers.pop("Authorization", None)
        
        if files:
            headers.pop("Content-Type", None)  # Let requests set it for multipart
        
        response = self.session.post(
            url,
            json=data if not files else None,
            data=data if files else None,
            files=files,
            headers=headers,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl
        )
        
        self._log_request_response("POST", url, data, response)
        response.raise_for_status()
        
        return response.json() if response.text else {}
    
    @measure_time
    def put(self, endpoint: str, data: Dict[str, Any], 
            auth_required: bool = True) -> Dict[str, Any]:
        """Make PUT request"""
        url = f"{self.base_url}{endpoint}"
        
        headers = self.session.headers.copy()
        if not auth_required:
            headers.pop("Authorization", None)
        
        response = self.session.put(
            url,
            json=data,
            headers=headers,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl
        )
        
        self._log_request_response("PUT", url, data, response)
        response.raise_for_status()
        
        return response.json() if response.text else {}
    
    @measure_time
    def delete(self, endpoint: str, auth_required: bool = True) -> bool:
        """Make DELETE request"""
        url = f"{self.base_url}{endpoint}"
        
        headers = self.session.headers.copy()
        if not auth_required:
            headers.pop("Authorization", None)
        
        response = self.session.delete(
            url,
            headers=headers,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl
        )
        
        self._log_request_response("DELETE", url, None, response)
        response.raise_for_status()
        
        return response.status_code == 204
    
    def _log_request_response(self, method: str, url: str, 
                              data: Any, response: requests.Response):
        """Log request and response details"""
        self.logger.debug(f"""
        Request:
        {method} {url}
        Headers: {json.dumps(dict(self.session.headers), indent=2)}
        Body: {json.dumps(data, indent=2) if data else 'None'}
        
        Response:
        Status: {response.status_code}
        Headers: {json.dumps(dict(response.headers), indent=2)}
        Body: {response.text[:1000] if response.text else 'None'}
        """)
    
    # Assertion helpers
    def assert_status_code(self, response: requests.Response, expected: int):
        """Assert response status code"""
        assert response.status_code == expected, \
            f"Expected status {expected}, got {response.status_code}. Response: {response.text}"
    
    def assert_response_time(self, duration: float, threshold: float):
        """Assert response time is within threshold"""
        assert duration <= threshold, \
            f"Response time {duration:.3f}s exceeded threshold {threshold}s"
    
    def assert_response_schema(self, data: Dict[str, Any], schema: Dict[str, type]):
        """Assert response matches expected schema"""
        for field, expected_type in schema.items():
            assert field in data, f"Missing required field: {field}"
            assert isinstance(data[field], expected_type), \
                f"Field {field} expected {expected_type}, got {type(data[field])}"
    
    def assert_list_response(self, data: List[Dict[str, Any]], 
                             min_items: int = 0, max_items: int = None):
        """Assert list response is valid"""
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) >= min_items, f"Expected at least {min_items} items, got {len(data)}"
        if max_items:
            assert len(data) <= max_items, f"Expected at most {max_items} items, got {len(data)}"
    
    def assert_error_response(self, response: Dict[str, Any], 
                              expected_error: str = None):
        """Assert error response format"""
        assert "error" in response or "detail" in response, \
            "Error response missing error/detail field"
        
        if expected_error:
            error_msg = response.get("error") or response.get("detail")
            assert expected_error.lower() in error_msg.lower(), \
                f"Expected error containing '{expected_error}', got '{error_msg}'"
    
    def assert_pagination_response(self, response: Dict[str, Any]):
        """Assert pagination response format"""
        required_fields = ["items", "total", "page", "size", "pages"]
        for field in required_fields:
            assert field in response, f"Missing pagination field: {field}"
        
        assert isinstance(response["items"], list), "Items should be a list"
        assert response["total"] >= 0, "Total should be non-negative"
        assert response["page"] > 0, "Page should be positive"
        assert response["size"] > 0, "Size should be positive"
        assert response["pages"] >= 0, "Pages should be non-negative"
    
    # Test data management
    def register_for_cleanup(self, resource_type: str, resource_id: Any):
        """Register resource for cleanup after test"""
        self.test_data_cleanup.append({
            "type": resource_type,
            "id": resource_id,
            "timestamp": datetime.now()
        })
    
    def cleanup_test_data(self):
        """Cleanup all registered test data"""
        self.logger.info(f"Cleaning up {len(self.test_data_cleanup)} test resources")
        
        cleanup_order = ["order", "batch", "payment", "customer", "product", "user"]
        
        for resource_type in cleanup_order:
            resources = [r for r in self.test_data_cleanup if r["type"] == resource_type]
            
            for resource in resources:
                try:
                    endpoint = f"/{resource_type}s/{resource['id']}"
                    self.delete(endpoint)
                    self.logger.debug(f"Cleaned up {resource_type} {resource['id']}")
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup {resource_type} {resource['id']}: {e}")
        
        self.test_data_cleanup.clear()
    
    # Performance testing helpers
    def run_concurrent_requests(self, endpoint: str, method: str = "GET", 
                                data: Dict[str, Any] = None, 
                                concurrent_users: int = 10) -> List[Tuple[float, bool]]:
        """Run concurrent requests and return response times"""
        import concurrent.futures
        
        def make_request():
            start_time = time.time()
            try:
                if method == "GET":
                    self.get(endpoint)
                elif method == "POST":
                    self.post(endpoint, data)
                duration = time.time() - start_time
                return (duration, True)
            except Exception:
                duration = time.time() - start_time
                return (duration, False)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_request) for _ in range(concurrent_users)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        return results
    
    def analyze_performance_results(self, results: List[Tuple[float, bool]]) -> Dict[str, Any]:
        """Analyze performance test results"""
        response_times = [r[0] for r in results]
        success_count = sum(1 for r in results if r[1])
        
        response_times.sort()
        
        return {
            "total_requests": len(results),
            "successful_requests": success_count,
            "failed_requests": len(results) - success_count,
            "success_rate": f"{(success_count / len(results) * 100):.2f}%",
            "min_response_time": f"{min(response_times):.3f}s",
            "max_response_time": f"{max(response_times):.3f}s",
            "avg_response_time": f"{sum(response_times) / len(response_times):.3f}s",
            "p50": f"{response_times[int(len(response_times) * 0.5)]:.3f}s",
            "p90": f"{response_times[int(len(response_times) * 0.9)]:.3f}s",
            "p95": f"{response_times[int(len(response_times) * 0.95)]:.3f}s",
            "p99": f"{response_times[int(len(response_times) * 0.99)]:.3f}s"
        }