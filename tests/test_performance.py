"""
Performance Tests
================
Load testing, stress testing, and performance benchmarking
for all API endpoints.
"""

import pytest
import time
import statistics
import concurrent.futures
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta

from base_test import APITestBase
from test_suite_config import TestDataFactory, PERFORMANCE_BENCHMARKS


class TestEndpointPerformance(APITestBase):
    """Test individual endpoint performance"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("admin")
        
        # Create test data for performance testing
        self.test_products = []
        self.test_customers = []
        
        # Create 50 products
        for i in range(50):
            product_data = TestDataFactory.generate_product_data()
            product = self.post("/products", product_data)
            self.test_products.append(product)
            self.register_for_cleanup("product", product["id"])
        
        # Create 20 customers
        for i in range(20):
            customer_data = TestDataFactory.generate_customer_data()
            customer = self.post("/customers", customer_data)
            self.test_customers.append(customer)
            self.register_for_cleanup("customer", customer["id"])
        
        yield
        self.cleanup_test_data()
    
    def test_product_list_performance(self):
        """Test product listing endpoint performance"""
        response_times = []
        
        # Test different page sizes
        page_sizes = [10, 25, 50, 100]
        
        for size in page_sizes:
            for i in range(10):  # 10 requests per page size
                start_time = time.time()
                
                response = self.get("/products", params={
                    "page": 1,
                    "size": size
                })
                
                duration = time.time() - start_time
                response_times.append(duration)
                
                # Verify response
                if isinstance(response, dict) and "items" in response:
                    assert len(response["items"]) <= size
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        
        # Assert performance requirements
        assert avg_time < 0.5, f"Average response time {avg_time:.3f}s exceeds 500ms"
        assert p95_time < 1.0, f"95th percentile {p95_time:.3f}s exceeds 1s"
        
        self.logger.info(f"Product list performance - Avg: {avg_time:.3f}s, P95: {p95_time:.3f}s")
    
    def test_product_search_performance(self):
        """Test product search performance with various queries"""
        search_queries = [
            "Para",  # Common prefix
            "Vitamin D3",  # Specific product
            "Tablet",  # Category search
            "XYZ123",  # Non-existent
            "Test Medicine",  # Generic term
        ]
        
        response_times = []
        
        for query in search_queries:
            for i in range(5):  # 5 requests per query
                start_time = time.time()
                
                self.get("/products", params={"search": query})
                
                duration = time.time() - start_time
                response_times.append(duration)
        
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        
        assert avg_time < 0.3, f"Average search time {avg_time:.3f}s exceeds 300ms"
        assert max_time < 1.0, f"Maximum search time {max_time:.3f}s exceeds 1s"
    
    def test_order_creation_performance(self):
        """Test order creation performance with varying complexity"""
        response_times = []
        
        # Test orders with different numbers of items
        item_counts = [1, 5, 10, 20]
        
        for item_count in item_counts:
            for i in range(5):  # 5 orders per item count
                # Prepare order data
                order_data = TestDataFactory.generate_order_data(
                    self.test_customers[i % len(self.test_customers)]["id"]
                )
                
                # Add items
                order_data["items"] = []
                for j in range(item_count):
                    product = self.test_products[j % len(self.test_products)]
                    order_data["items"].append({
                        "product_id": product["id"],
                        "quantity": 10,
                        "price": product["selling_price"]
                    })
                
                start_time = time.time()
                
                order = self.post("/orders", order_data)
                
                duration = time.time() - start_time
                response_times.append({
                    "duration": duration,
                    "item_count": item_count
                })
                
                self.register_for_cleanup("order", order["id"])
        
        # Analyze by item count
        for count in item_counts:
            times = [r["duration"] for r in response_times if r["item_count"] == count]
            avg_time = statistics.mean(times)
            
            # Performance should scale reasonably with item count
            expected_time = 0.5 + (count * 0.05)  # Base + per-item overhead
            
            assert avg_time < expected_time, \
                f"Order creation with {count} items: {avg_time:.3f}s exceeds expected {expected_time:.3f}s"
    
    def test_invoice_generation_performance(self):
        """Test invoice generation performance"""
        # Create orders for invoice generation
        orders = []
        
        for i in range(10):
            order_data = TestDataFactory.generate_order_data(
                self.test_customers[i % len(self.test_customers)]["id"]
            )
            
            # Add 5-10 items per order
            order_data["items"] = []
            item_count = 5 + (i % 6)
            
            for j in range(item_count):
                product = self.test_products[j % len(self.test_products)]
                order_data["items"].append({
                    "product_id": product["id"],
                    "quantity": 10 + j,
                    "price": product["selling_price"],
                    "gst_rate": product["gst_rate"]
                })
            
            order = self.post("/orders", order_data)
            orders.append(order)
            self.register_for_cleanup("order", order["id"])
        
        # Test invoice generation
        response_times = []
        
        for order in orders:
            start_time = time.time()
            
            invoice = self.post(f"/orders/{order['id']}/invoice", {})
            
            duration = time.time() - start_time
            response_times.append(duration)
            
            # Verify invoice has all required fields
            assert "invoice_number" in invoice
            assert "items" in invoice
            assert len(invoice["items"]) == len(order["items"])
        
        avg_time = statistics.mean(response_times)
        p90_time = statistics.quantiles(response_times, n=10)[8]  # 90th percentile
        
        assert avg_time < 1.0, f"Average invoice generation time {avg_time:.3f}s exceeds 1s"
        assert p90_time < 2.0, f"90th percentile {p90_time:.3f}s exceeds 2s"


class TestConcurrentLoad(APITestBase):
    """Test system behavior under concurrent load"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("admin")
        yield
    
    def test_concurrent_read_operations(self):
        """Test concurrent read operations"""
        endpoints = [
            "/products",
            "/customers",
            "/orders",
            "/batches"
        ]
        
        def make_request(endpoint):
            start_time = time.time()
            try:
                self.get(endpoint)
                return (time.time() - start_time, True)
            except Exception:
                return (time.time() - start_time, False)
        
        # Run concurrent requests
        concurrent_users = 50
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            # Submit requests
            for i in range(200):  # 200 total requests
                endpoint = endpoints[i % len(endpoints)]
                futures.append(executor.submit(make_request, endpoint))
            
            # Collect results
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analyze results
        successful = [r for r in results if r[1]]
        failed = [r for r in results if not r[1]]
        
        success_rate = len(successful) / len(results) * 100
        avg_response_time = statistics.mean([r[0] for r in successful])
        
        assert success_rate > 95, f"Success rate {success_rate:.1f}% below 95%"
        assert avg_response_time < 2.0, f"Average response time {avg_response_time:.3f}s exceeds 2s"
        
        self.logger.info(f"Concurrent read test - Success: {success_rate:.1f}%, Avg time: {avg_response_time:.3f}s")
    
    def test_concurrent_write_operations(self):
        """Test concurrent write operations"""
        def create_product():
            start_time = time.time()
            try:
                product_data = TestDataFactory.generate_product_data()
                product = self.post("/products", product_data)
                self.register_for_cleanup("product", product["id"])
                return (time.time() - start_time, True)
            except Exception:
                return (time.time() - start_time, False)
        
        # Run concurrent product creations
        concurrent_users = 20
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(create_product) for _ in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analyze results
        successful = [r for r in results if r[1]]
        success_rate = len(successful) / len(results) * 100
        avg_time = statistics.mean([r[0] for r in successful]) if successful else 0
        
        assert success_rate > 90, f"Write success rate {success_rate:.1f}% below 90%"
        assert avg_time < 3.0, f"Average write time {avg_time:.3f}s exceeds 3s"
    
    def test_mixed_workload_performance(self):
        """Test performance under mixed read/write workload"""
        # Create initial data
        product_data = TestDataFactory.generate_product_data()
        product = self.post("/products", product_data)
        self.register_for_cleanup("product", product["id"])
        
        customer_data = TestDataFactory.generate_customer_data()
        customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", customer["id"])
        
        def mixed_operations(operation_type):
            start_time = time.time()
            try:
                if operation_type == "read_products":
                    self.get("/products")
                elif operation_type == "read_single":
                    self.get(f"/products/{product['id']}")
                elif operation_type == "create_order":
                    order_data = TestDataFactory.generate_order_data(customer["id"])
                    order_data["items"] = [{
                        "product_id": product["id"],
                        "quantity": 5,
                        "price": 100
                    }]
                    order = self.post("/orders", order_data)
                    self.register_for_cleanup("order", order["id"])
                elif operation_type == "update_product":
                    self.put(f"/products/{product['id']}", {"reorder_level": 100})
                
                return (time.time() - start_time, True, operation_type)
            except Exception:
                return (time.time() - start_time, False, operation_type)
        
        # Define workload mix
        operations = (
            ["read_products"] * 40 +  # 40% read list
            ["read_single"] * 30 +    # 30% read single
            ["create_order"] * 20 +   # 20% create
            ["update_product"] * 10   # 10% update
        )
        
        # Run mixed workload
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(mixed_operations, op) for op in operations]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analyze by operation type
        for op_type in set(operations):
            op_results = [r for r in results if r[2] == op_type]
            successful = [r for r in op_results if r[1]]
            
            if successful:
                avg_time = statistics.mean([r[0] for r in successful])
                success_rate = len(successful) / len(op_results) * 100
                
                self.logger.info(f"{op_type} - Success: {success_rate:.1f}%, Avg time: {avg_time:.3f}s")
                
                # Assert reasonable performance for each operation type
                if "read" in op_type:
                    assert avg_time < 1.0, f"{op_type} average time {avg_time:.3f}s exceeds 1s"
                else:
                    assert avg_time < 2.0, f"{op_type} average time {avg_time:.3f}s exceeds 2s"


class TestStressAndLimits(APITestBase):
    """Test system limits and stress scenarios"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("admin")
        yield
        self.cleanup_test_data()
    
    def test_large_payload_handling(self):
        """Test handling of large request payloads"""
        # Create customer for orders
        customer_data = TestDataFactory.generate_customer_data()
        customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", customer["id"])
        
        # Create products
        products = []
        for i in range(10):
            product_data = TestDataFactory.generate_product_data()
            product = self.post("/products", product_data)
            products.append(product)
            self.register_for_cleanup("product", product["id"])
        
        # Test order with many items
        large_order_data = TestDataFactory.generate_order_data(customer["id"])
        large_order_data["items"] = []
        
        # Add 100 items
        for i in range(100):
            product = products[i % len(products)]
            large_order_data["items"].append({
                "product_id": product["id"],
                "quantity": 10 + i,
                "price": product["selling_price"],
                "discount_percent": i % 10
            })
        
        start_time = time.time()
        
        try:
            order = self.post("/orders", large_order_data)
            duration = time.time() - start_time
            
            assert len(order["items"]) == 100
            assert duration < 5.0, f"Large order creation took {duration:.3f}s, exceeds 5s"
            
            self.register_for_cleanup("order", order["id"])
            
        except Exception as e:
            # System might have limits on order size
            if "413" in str(e) or "too large" in str(e).lower():
                self.logger.info("System enforces payload size limits")
            else:
                raise
    
    def test_pagination_performance(self):
        """Test pagination performance with large datasets"""
        # Assuming products already exist in the system
        
        page_sizes = [10, 25, 50, 100]
        response_times = []
        
        for size in page_sizes:
            for page in range(1, 6):  # Test first 5 pages
                start_time = time.time()
                
                response = self.get("/products", params={
                    "page": page,
                    "size": size
                })
                
                duration = time.time() - start_time
                response_times.append({
                    "page": page,
                    "size": size,
                    "duration": duration
                })
                
                # Verify pagination metadata
                if isinstance(response, dict):
                    assert "page" in response
                    assert "size" in response
                    assert "total" in response
        
        # Analyze performance
        for size in page_sizes:
            size_times = [r["duration"] for r in response_times if r["size"] == size]
            avg_time = statistics.mean(size_times)
            
            # Pagination should be efficient regardless of page size
            assert avg_time < 1.0, f"Pagination with size {size}: avg {avg_time:.3f}s exceeds 1s"
    
    def test_sustained_load_performance(self):
        """Test system performance under sustained load"""
        test_duration_seconds = 30
        request_delay = 0.1  # 10 requests per second
        
        results = []
        start_test = time.time()
        
        while time.time() - start_test < test_duration_seconds:
            request_start = time.time()
            
            try:
                # Rotate through different endpoints
                endpoints = ["/products", "/customers", "/orders"]
                endpoint = endpoints[len(results) % len(endpoints)]
                
                self.get(endpoint)
                success = True
            except Exception:
                success = False
            
            duration = time.time() - request_start
            results.append({
                "time": time.time() - start_test,
                "duration": duration,
                "success": success
            })
            
            # Wait before next request
            time.sleep(request_delay)
        
        # Analyze results
        successful = [r for r in results if r["success"]]
        success_rate = len(successful) / len(results) * 100
        
        # Check performance degradation over time
        first_half = [r["duration"] for r in successful[:len(successful)//2]]
        second_half = [r["duration"] for r in successful[len(successful)//2:]]
        
        avg_first = statistics.mean(first_half) if first_half else 0
        avg_second = statistics.mean(second_half) if second_half else 0
        
        # Performance shouldn't degrade significantly
        degradation = ((avg_second - avg_first) / avg_first * 100) if avg_first > 0 else 0
        
        assert success_rate > 95, f"Success rate {success_rate:.1f}% under sustained load"
        assert degradation < 50, f"Performance degraded by {degradation:.1f}% over time"
        
        self.logger.info(f"Sustained load test - Requests: {len(results)}, "
                        f"Success: {success_rate:.1f}%, "
                        f"Degradation: {degradation:.1f}%")


class TestDatabasePerformance(APITestBase):
    """Test database-intensive operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("admin")
        yield
        self.cleanup_test_data()
    
    def test_complex_query_performance(self):
        """Test performance of complex queries"""
        # Create test data
        customers = []
        for i in range(5):
            customer_data = TestDataFactory.generate_customer_data()
            customer = self.post("/customers", customer_data)
            customers.append(customer)
            self.register_for_cleanup("customer", customer["id"])
        
        products = []
        for i in range(20):
            product_data = TestDataFactory.generate_product_data()
            product = self.post("/products", product_data)
            products.append(product)
            self.register_for_cleanup("product", product["id"])
        
        # Create orders with multiple items
        for customer in customers:
            for i in range(10):
                order_data = TestDataFactory.generate_order_data(customer["id"])
                order_data["items"] = [
                    {
                        "product_id": products[j]["id"],
                        "quantity": 5 + j,
                        "price": products[j]["selling_price"]
                    }
                    for j in range(5)
                ]
                
                order = self.post("/orders", order_data)
                self.register_for_cleanup("order", order["id"])
        
        # Test complex queries
        complex_queries = [
            # Customer with orders summary
            f"/customers/{customers[0]['id']}/order-summary",
            
            # Product sales analytics
            f"/products/{products[0]['id']}/sales-analytics",
            
            # Dashboard stats
            "/analytics/dashboard",
            
            # Revenue by period
            "/analytics/revenue?period=month",
            
            # Top selling products
            "/analytics/top-products?limit=10"
        ]
        
        response_times = []
        
        for endpoint in complex_queries:
            for i in range(5):  # 5 requests per query
                start_time = time.time()
                
                try:
                    self.get(endpoint)
                    duration = time.time() - start_time
                    response_times.append({
                        "endpoint": endpoint,
                        "duration": duration
                    })
                except Exception as e:
                    if "404" not in str(e):
                        raise
        
        # Analyze performance
        if response_times:
            avg_time = statistics.mean([r["duration"] for r in response_times])
            max_time = max([r["duration"] for r in response_times])
            
            assert avg_time < 2.0, f"Average complex query time {avg_time:.3f}s exceeds 2s"
            assert max_time < 5.0, f"Maximum complex query time {max_time:.3f}s exceeds 5s"
    
    def test_bulk_operations_performance(self):
        """Test performance of bulk operations"""
        # Test bulk product creation
        products_data = [TestDataFactory.generate_product_data() for _ in range(50)]
        
        start_time = time.time()
        
        try:
            response = self.post("/products/bulk", {"products": products_data})
            duration = time.time() - start_time
            
            assert response["created"] == 50
            assert duration < 5.0, f"Bulk creation of 50 products took {duration:.3f}s"
            
            # Register for cleanup
            if "product_ids" in response:
                for pid in response["product_ids"]:
                    self.register_for_cleanup("product", pid)
                    
        except Exception as e:
            if "404" not in str(e):
                # Bulk operations might not be implemented
                self.logger.info("Bulk operations not available, testing individual creates")
                
                start_time = time.time()
                for product_data in products_data[:10]:  # Test with 10 products
                    product = self.post("/products", product_data)
                    self.register_for_cleanup("product", product["id"])
                
                duration = time.time() - start_time
                assert duration < 10.0, f"Creating 10 products individually took {duration:.3f}s"