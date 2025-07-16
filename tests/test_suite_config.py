"""
Enterprise Test Suite Configuration
==================================
Centralized configuration for all API tests including environments,
test data factories, and performance benchmarks.
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import random
import string


class Environment(Enum):
    """Test environment configurations"""
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class TestConfig:
    """Test configuration for different environments"""
    base_url: str
    api_key: Optional[str] = None
    timeout: int = 30
    retry_count: int = 3
    verify_ssl: bool = True
    performance_thresholds: Dict[str, float] = None

    def __post_init__(self):
        if self.performance_thresholds is None:
            self.performance_thresholds = {
                "auth": 1.0,  # 1 second for auth endpoints
                "read": 0.5,  # 500ms for read operations
                "write": 1.0,  # 1 second for write operations
                "complex": 2.0,  # 2 seconds for complex queries
                "file_upload": 5.0  # 5 seconds for file uploads
            }


# Environment configurations
ENVIRONMENTS = {
    Environment.LOCAL: TestConfig(
        base_url="http://localhost:8000",
        verify_ssl=False
    ),
    Environment.STAGING: TestConfig(
        base_url=os.getenv("STAGING_API_URL", "https://staging-api.pharmaco.com"),
        api_key=os.getenv("STAGING_API_KEY")
    ),
    Environment.PRODUCTION: TestConfig(
        base_url=os.getenv("PROD_API_URL", "https://api.pharmaco.com"),
        api_key=os.getenv("PROD_API_KEY"),
        timeout=60
    )
}


class TestDataFactory:
    """Factory for generating test data"""
    
    @staticmethod
    def generate_gst_number() -> str:
        """Generate valid GST number format"""
        state_code = random.randint(10, 37)
        pan = ''.join(random.choices(string.ascii_uppercase, k=5)) + \
              ''.join(random.choices(string.digits, k=4)) + \
              random.choice(string.ascii_uppercase)
        return f"{state_code}{pan}1Z5"
    
    @staticmethod
    def generate_phone_number() -> str:
        """Generate valid Indian phone number"""
        return f"+91{random.randint(7000000000, 9999999999)}"
    
    @staticmethod
    def generate_email() -> str:
        """Generate unique test email"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"test_{timestamp}_{random.randint(1000, 9999)}@pharmtest.com"
    
    @staticmethod
    def generate_product_data() -> Dict[str, Any]:
        """Generate test product data"""
        categories = ["Tablet", "Capsule", "Syrup", "Injection", "Cream", "Drops"]
        schedules = ["H", "H1", "X", "G", "J", "C", "C1"]
        
        return {
            "name": f"Test Medicine {random.randint(1000, 9999)}",
            "sku": f"SKU{random.randint(100000, 999999)}",
            "category": random.choice(categories),
            "manufacturer": f"Test Pharma Ltd",
            "hsn_code": f"{random.randint(3000, 3999)}",
            "gst_rate": random.choice([5, 12, 18]),
            "base_price": round(random.uniform(10, 1000), 2),
            "selling_price": round(random.uniform(15, 1500), 2),
            "mrp": round(random.uniform(20, 2000), 2),
            "unit": "Strip",
            "pack_size": random.choice([10, 15, 30]),
            "reorder_level": random.randint(10, 100),
            "drug_schedule": random.choice(schedules),
            "requires_prescription": random.choice([True, False]),
            "is_active": True
        }
    
    @staticmethod
    def generate_customer_data() -> Dict[str, Any]:
        """Generate test customer data"""
        customer_types = ["Pharmacy", "Hospital", "Clinic", "Nursing Home"]
        
        return {
            "name": f"Test {random.choice(customer_types)} {random.randint(100, 999)}",
            "customer_type": random.choice(["retail", "wholesale", "hospital"]),
            "contact_person": f"Test Person {random.randint(1, 100)}",
            "phone": TestDataFactory.generate_phone_number(),
            "email": TestDataFactory.generate_email(),
            "address": f"{random.randint(1, 999)} Test Street",
            "city": random.choice(["Mumbai", "Delhi", "Bangalore", "Chennai"]),
            "state": random.choice(["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu"]),
            "pincode": f"{random.randint(100000, 999999)}",
            "gst_number": TestDataFactory.generate_gst_number(),
            "drug_license_number": f"DL-{random.randint(1000, 9999)}",
            "credit_limit": random.randint(10000, 100000),
            "payment_terms": random.choice([0, 15, 30, 45]),
            "is_active": True
        }
    
    @staticmethod
    def generate_order_data(customer_id: int) -> Dict[str, Any]:
        """Generate test order data"""
        return {
            "customer_id": customer_id,
            "order_date": datetime.now().isoformat(),
            "delivery_date": (datetime.now() + timedelta(days=random.randint(1, 7))).isoformat(),
            "payment_method": random.choice(["cash", "credit", "upi", "cheque"]),
            "payment_status": random.choice(["pending", "partial", "paid"]),
            "delivery_status": "pending",
            "remarks": "Test order generated by API test suite"
        }
    
    @staticmethod
    def generate_batch_data(product_id: int) -> Dict[str, Any]:
        """Generate test batch data"""
        manufacture_date = datetime.now() - timedelta(days=random.randint(30, 180))
        expiry_date = manufacture_date + timedelta(days=random.randint(365, 730))
        
        return {
            "product_id": product_id,
            "batch_number": f"BATCH{datetime.now().strftime('%Y%m')}{random.randint(1000, 9999)}",
            "manufacture_date": manufacture_date.date().isoformat(),
            "expiry_date": expiry_date.date().isoformat(),
            "quantity": random.randint(100, 1000),
            "purchase_price": round(random.uniform(10, 900), 2),
            "selling_price": round(random.uniform(15, 1350), 2),
            "mrp": round(random.uniform(20, 1800), 2),
            "supplier": f"Test Supplier {random.randint(1, 50)}",
            "location": random.choice(["Rack A1", "Rack B2", "Rack C3", "Store Room"])
        }


class TestMetrics:
    """Track and report test metrics"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0
        self.performance_data = []
        self.error_logs = []
    
    def start_suite(self):
        """Mark test suite start"""
        self.start_time = datetime.now()
    
    def end_suite(self):
        """Mark test suite end"""
        self.end_time = datetime.now()
    
    def record_test(self, test_name: str, status: str, duration: float, error: str = None):
        """Record individual test result"""
        self.total_tests += 1
        
        if status == "passed":
            self.passed_tests += 1
        elif status == "failed":
            self.failed_tests += 1
            if error:
                self.error_logs.append({
                    "test": test_name,
                    "error": error,
                    "timestamp": datetime.now().isoformat()
                })
        elif status == "skipped":
            self.skipped_tests += 1
        
        self.performance_data.append({
            "test": test_name,
            "duration": duration,
            "status": status
        })
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate test execution report"""
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        
        return {
            "summary": {
                "total": self.total_tests,
                "passed": self.passed_tests,
                "failed": self.failed_tests,
                "skipped": self.skipped_tests,
                "pass_rate": f"{(self.passed_tests / self.total_tests * 100):.2f}%" if self.total_tests > 0 else "0%",
                "duration": f"{duration:.2f} seconds"
            },
            "performance": {
                "average_duration": f"{sum(p['duration'] for p in self.performance_data) / len(self.performance_data):.3f}s" if self.performance_data else "0s",
                "slowest_tests": sorted(self.performance_data, key=lambda x: x['duration'], reverse=True)[:5]
            },
            "errors": self.error_logs[:10],  # Top 10 errors
            "timestamp": datetime.now().isoformat()
        }


# Test categories for organization
TEST_CATEGORIES = {
    "smoke": ["health", "auth_login", "basic_crud"],
    "authentication": ["auth_*", "token_*", "permission_*"],
    "core_business": ["customer_*", "product_*", "order_*", "inventory_*"],
    "financial": ["payment_*", "invoice_*", "tax_*", "credit_*"],
    "integration": ["whatsapp_*", "sms_*", "email_*", "pdf_*"],
    "performance": ["perf_*", "load_*", "stress_*"],
    "security": ["sec_*", "injection_*", "xss_*", "auth_bypass_*"],
    "edge_cases": ["edge_*", "boundary_*", "negative_*"]
}


# Performance benchmarks
PERFORMANCE_BENCHMARKS = {
    "p50": 0.5,  # 50th percentile should be under 500ms
    "p90": 1.0,  # 90th percentile should be under 1s
    "p95": 1.5,  # 95th percentile should be under 1.5s
    "p99": 2.0,  # 99th percentile should be under 2s
}


# Test user personas
TEST_USERS = {
    "admin": {
        "username": "admin@pharmaco.com",
        "password": "AdminTest123!",
        "role": "admin",
        "permissions": ["*"]
    },
    "manager": {
        "username": "manager@pharmaco.com",
        "password": "ManagerTest123!",
        "role": "manager",
        "permissions": ["read:*", "write:*", "delete:own"]
    },
    "sales": {
        "username": "sales@pharmaco.com",
        "password": "SalesTest123!",
        "role": "sales",
        "permissions": ["read:products", "write:orders", "read:customers"]
    },
    "warehouse": {
        "username": "warehouse@pharmaco.com",
        "password": "WarehouseTest123!",
        "role": "warehouse",
        "permissions": ["read:inventory", "write:inventory", "read:orders"]
    },
    "accounts": {
        "username": "accounts@pharmaco.com",
        "password": "AccountsTest123!",
        "role": "accounts",
        "permissions": ["read:*", "write:payments", "write:invoices"]
    }
}