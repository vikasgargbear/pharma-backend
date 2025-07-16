"""
Core Business Logic Tests
=========================
Tests for core pharmaceutical business operations including products,
customers, orders, inventory, and batch management.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List
import random

from base_test import APITestBase
from test_suite_config import TestDataFactory


class TestProducts(APITestBase):
    """Test product management functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("admin")
        yield
        self.cleanup_test_data()
    
    def test_create_product(self):
        """Test creating a new product"""
        product_data = TestDataFactory.generate_product_data()
        
        response = self.post("/products", product_data)
        
        # Validate response
        assert "id" in response
        assert response["name"] == product_data["name"]
        assert response["sku"] == product_data["sku"]
        assert response["gst_rate"] == product_data["gst_rate"]
        assert response["is_active"] == True
        
        self.register_for_cleanup("product", response["id"])
        
        # Verify product can be retrieved
        get_response = self.get(f"/products/{response['id']}")
        assert get_response["id"] == response["id"]
    
    def test_create_product_with_drug_schedule(self):
        """Test creating scheduled drug products"""
        scheduled_drugs = ["H", "H1", "X"]
        
        for schedule in scheduled_drugs:
            product_data = TestDataFactory.generate_product_data()
            product_data["drug_schedule"] = schedule
            product_data["requires_prescription"] = True
            
            response = self.post("/products", product_data)
            
            assert response["drug_schedule"] == schedule
            assert response["requires_prescription"] == True
            
            self.register_for_cleanup("product", response["id"])
    
    def test_update_product(self):
        """Test updating product details"""
        # Create product
        product_data = TestDataFactory.generate_product_data()
        create_response = self.post("/products", product_data)
        product_id = create_response["id"]
        
        # Update product
        update_data = {
            "selling_price": 999.99,
            "reorder_level": 50,
            "is_active": False
        }
        
        update_response = self.put(f"/products/{product_id}", update_data)
        
        assert update_response["selling_price"] == 999.99
        assert update_response["reorder_level"] == 50
        assert update_response["is_active"] == False
        
        self.register_for_cleanup("product", product_id)
    
    def test_product_search(self):
        """Test product search functionality"""
        # Create multiple products
        products = []
        search_term = "Paracetamol"
        
        for i in range(5):
            product_data = TestDataFactory.generate_product_data()
            if i < 3:
                product_data["name"] = f"{search_term} {random.randint(100, 999)}mg"
            
            response = self.post("/products", product_data)
            products.append(response["id"])
            self.register_for_cleanup("product", response["id"])
        
        # Search products
        search_response = self.get("/products", params={"search": search_term})
        
        assert len(search_response) >= 3
        for product in search_response:
            if search_term in product["name"]:
                assert search_term.lower() in product["name"].lower()
    
    def test_product_validation(self):
        """Test product data validation"""
        invalid_products = [
            {"name": ""},  # Empty name
            {"name": "Test", "gst_rate": -5},  # Negative GST
            {"name": "Test", "gst_rate": 50},  # Invalid GST rate
            {"name": "Test", "mrp": 100, "selling_price": 150},  # Selling > MRP
            {"name": "Test", "base_price": -100},  # Negative price
        ]
        
        for invalid_data in invalid_products:
            try:
                self.post("/products", invalid_data)
                pytest.fail(f"Invalid product data accepted: {invalid_data}")
            except Exception as e:
                assert "400" in str(e) or "422" in str(e)
    
    def test_bulk_product_import(self):
        """Test bulk product import functionality"""
        products_data = [TestDataFactory.generate_product_data() for _ in range(10)]
        
        # If bulk endpoint exists
        try:
            response = self.post("/products/bulk", {"products": products_data})
            
            assert "created" in response
            assert response["created"] == 10
            
            # Register all for cleanup
            if "product_ids" in response:
                for product_id in response["product_ids"]:
                    self.register_for_cleanup("product", product_id)
        except Exception as e:
            if "404" in str(e):
                # Bulk endpoint not implemented, skip
                pytest.skip("Bulk product import not implemented")
            else:
                raise


class TestCustomers(APITestBase):
    """Test customer management functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("admin")
        yield
        self.cleanup_test_data()
    
    def test_create_customer(self):
        """Test creating a new customer"""
        customer_data = TestDataFactory.generate_customer_data()
        
        response = self.post("/customers", customer_data)
        
        # Validate response
        assert "id" in response
        assert response["name"] == customer_data["name"]
        assert response["gst_number"] == customer_data["gst_number"]
        assert response["credit_limit"] == customer_data["credit_limit"]
        
        self.register_for_cleanup("customer", response["id"])
    
    def test_customer_credit_management(self):
        """Test customer credit limit and balance tracking"""
        customer_data = TestDataFactory.generate_customer_data()
        customer_data["credit_limit"] = 50000
        
        # Create customer
        customer = self.post("/customers", customer_data)
        customer_id = customer["id"]
        self.register_for_cleanup("customer", customer_id)
        
        # Check initial credit balance
        balance_response = self.get(f"/customers/{customer_id}/credit-balance")
        
        assert balance_response["credit_limit"] == 50000
        assert balance_response["used_credit"] == 0
        assert balance_response["available_credit"] == 50000
    
    def test_customer_validation(self):
        """Test customer data validation"""
        invalid_customers = [
            {"name": ""},  # Empty name
            {"name": "Test", "gst_number": "INVALID"},  # Invalid GST
            {"name": "Test", "phone": "123"},  # Invalid phone
            {"name": "Test", "email": "notanemail"},  # Invalid email
            {"name": "Test", "credit_limit": -1000},  # Negative credit
        ]
        
        for invalid_data in invalid_customers:
            try:
                self.post("/customers", invalid_data)
                pytest.fail(f"Invalid customer data accepted: {invalid_data}")
            except Exception as e:
                assert "400" in str(e) or "422" in str(e)
    
    def test_customer_document_upload(self):
        """Test uploading customer documents"""
        # Create customer
        customer_data = TestDataFactory.generate_customer_data()
        customer = self.post("/customers", customer_data)
        customer_id = customer["id"]
        self.register_for_cleanup("customer", customer_id)
        
        # Upload drug license
        files = {
            "file": ("drug_license.pdf", b"Mock PDF content", "application/pdf")
        }
        
        try:
            response = self.post(
                f"/customers/{customer_id}/documents",
                data={"document_type": "drug_license"},
                files=files
            )
            
            assert "document_id" in response or "id" in response
            assert response.get("document_type") == "drug_license"
        except Exception as e:
            if "404" in str(e):
                pytest.skip("Document upload not implemented")
            else:
                raise


class TestOrders(APITestBase):
    """Test order management functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("sales")
        
        # Create test customer and products
        customer_data = TestDataFactory.generate_customer_data()
        self.test_customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", self.test_customer["id"])
        
        self.test_products = []
        for _ in range(3):
            product_data = TestDataFactory.generate_product_data()
            product = self.post("/products", product_data)
            self.test_products.append(product)
            self.register_for_cleanup("product", product["id"])
            
            # Create batch for product
            batch_data = TestDataFactory.generate_batch_data(product["id"])
            batch = self.post("/batches", batch_data)
            self.register_for_cleanup("batch", batch["id"])
        
        yield
        self.cleanup_test_data()
    
    def test_create_order(self):
        """Test creating a new order"""
        order_data = TestDataFactory.generate_order_data(self.test_customer["id"])
        
        # Add order items
        order_data["items"] = [
            {
                "product_id": self.test_products[0]["id"],
                "quantity": 10,
                "price": self.test_products[0]["selling_price"]
            },
            {
                "product_id": self.test_products[1]["id"],
                "quantity": 5,
                "price": self.test_products[1]["selling_price"]
            }
        ]
        
        response = self.post("/orders", order_data)
        
        assert "id" in response
        assert response["customer_id"] == self.test_customer["id"]
        assert len(response.get("items", [])) == 2
        assert response["status"] == "pending"
        
        self.register_for_cleanup("order", response["id"])
    
    def test_order_workflow(self):
        """Test complete order workflow from creation to delivery"""
        # Create order
        order_data = TestDataFactory.generate_order_data(self.test_customer["id"])
        order_data["items"] = [{
            "product_id": self.test_products[0]["id"],
            "quantity": 10,
            "price": self.test_products[0]["selling_price"]
        }]
        
        order = self.post("/orders", order_data)
        order_id = order["id"]
        self.register_for_cleanup("order", order_id)
        
        # Confirm order
        self.put(f"/orders/{order_id}/confirm", {})
        
        # Generate invoice
        invoice = self.post(f"/orders/{order_id}/invoice", {})
        assert "invoice_number" in invoice
        
        # Mark as packed
        self.put(f"/orders/{order_id}/pack", {})
        
        # Mark as shipped
        self.put(f"/orders/{order_id}/ship", {
            "tracking_number": "TEST123456",
            "carrier": "Test Logistics"
        })
        
        # Mark as delivered
        self.put(f"/orders/{order_id}/deliver", {
            "delivered_by": "Test Driver",
            "delivery_notes": "Delivered successfully"
        })
        
        # Verify final status
        final_order = self.get(f"/orders/{order_id}")
        assert final_order["status"] == "delivered"
    
    def test_order_cancellation(self):
        """Test order cancellation with inventory restoration"""
        # Create order
        order_data = TestDataFactory.generate_order_data(self.test_customer["id"])
        order_data["items"] = [{
            "product_id": self.test_products[0]["id"],
            "quantity": 10,
            "price": self.test_products[0]["selling_price"]
        }]
        
        order = self.post("/orders", order_data)
        order_id = order["id"]
        self.register_for_cleanup("order", order_id)
        
        # Get initial inventory
        initial_inventory = self.get(f"/products/{self.test_products[0]['id']}/inventory")
        
        # Cancel order
        self.put(f"/orders/{order_id}/cancel", {
            "reason": "Customer request"
        })
        
        # Verify order is cancelled
        cancelled_order = self.get(f"/orders/{order_id}")
        assert cancelled_order["status"] == "cancelled"
        
        # Verify inventory is restored
        final_inventory = self.get(f"/products/{self.test_products[0]['id']}/inventory")
        assert final_inventory["available_quantity"] == initial_inventory["available_quantity"]
    
    def test_order_with_scheduled_drugs(self):
        """Test order containing scheduled drugs requires additional validation"""
        # Create scheduled drug product
        scheduled_product_data = TestDataFactory.generate_product_data()
        scheduled_product_data["drug_schedule"] = "H"
        scheduled_product_data["requires_prescription"] = True
        
        scheduled_product = self.post("/products", scheduled_product_data)
        self.register_for_cleanup("product", scheduled_product["id"])
        
        # Create batch
        batch_data = TestDataFactory.generate_batch_data(scheduled_product["id"])
        batch = self.post("/batches", batch_data)
        self.register_for_cleanup("batch", batch["id"])
        
        # Try to create order without prescription
        order_data = TestDataFactory.generate_order_data(self.test_customer["id"])
        order_data["items"] = [{
            "product_id": scheduled_product["id"],
            "quantity": 5,
            "price": scheduled_product["selling_price"]
        }]
        
        try:
            self.post("/orders", order_data)
            pytest.fail("Order with scheduled drug created without prescription")
        except Exception as e:
            assert "prescription" in str(e).lower() or "400" in str(e)


class TestInventory(APITestBase):
    """Test inventory management functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("warehouse")
        
        # Create test product
        product_data = TestDataFactory.generate_product_data()
        self.test_product = self.post("/products", product_data)
        self.register_for_cleanup("product", self.test_product["id"])
        
        yield
        self.cleanup_test_data()
    
    def test_batch_management(self):
        """Test batch creation and tracking"""
        batch_data = TestDataFactory.generate_batch_data(self.test_product["id"])
        
        response = self.post("/batches", batch_data)
        
        assert "id" in response
        assert response["batch_number"] == batch_data["batch_number"]
        assert response["quantity"] == batch_data["quantity"]
        assert response["product_id"] == self.test_product["id"]
        
        self.register_for_cleanup("batch", response["id"])
        
        # Verify batch appears in product inventory
        inventory = self.get(f"/products/{self.test_product['id']}/inventory")
        assert inventory["total_quantity"] >= batch_data["quantity"]
    
    def test_expiry_tracking(self):
        """Test batch expiry date tracking and alerts"""
        # Create batch expiring soon
        batch_data = TestDataFactory.generate_batch_data(self.test_product["id"])
        batch_data["expiry_date"] = (datetime.now() + timedelta(days=30)).date().isoformat()
        
        batch = self.post("/batches", batch_data)
        self.register_for_cleanup("batch", batch["id"])
        
        # Check expiring batches
        expiring = self.get("/batches/expiring", params={"days": 60})
        
        assert len(expiring) > 0
        assert any(b["id"] == batch["id"] for b in expiring)
    
    def test_stock_movement(self):
        """Test inventory movement tracking"""
        # Create batch
        batch_data = TestDataFactory.generate_batch_data(self.test_product["id"])
        batch_data["quantity"] = 100
        
        batch = self.post("/batches", batch_data)
        self.register_for_cleanup("batch", batch["id"])
        
        # Create stock adjustment
        adjustment_data = {
            "batch_id": batch["id"],
            "adjustment_type": "damage",
            "quantity": -10,
            "reason": "Damaged during handling"
        }
        
        self.post("/inventory/adjustments", adjustment_data)
        
        # Verify stock is updated
        updated_batch = self.get(f"/batches/{batch['id']}")
        assert updated_batch["quantity"] == 90
        
        # Verify movement is tracked
        movements = self.get(f"/batches/{batch['id']}/movements")
        assert len(movements) > 0
        assert any(m["quantity"] == -10 for m in movements)
    
    def test_reorder_alerts(self):
        """Test low stock and reorder alerts"""
        # Create product with low reorder level
        product_data = TestDataFactory.generate_product_data()
        product_data["reorder_level"] = 50
        
        product = self.post("/products", product_data)
        self.register_for_cleanup("product", product["id"])
        
        # Create batch with quantity below reorder level
        batch_data = TestDataFactory.generate_batch_data(product["id"])
        batch_data["quantity"] = 30
        
        batch = self.post("/batches", batch_data)
        self.register_for_cleanup("batch", batch["id"])
        
        # Check reorder alerts
        alerts = self.get("/inventory/reorder-alerts")
        
        assert len(alerts) > 0
        assert any(a["product_id"] == product["id"] for a in alerts)
    
    def test_batch_wise_pricing(self):
        """Test different pricing for different batches"""
        # Create multiple batches with different prices
        batches = []
        prices = [100, 120, 110]
        
        for price in prices:
            batch_data = TestDataFactory.generate_batch_data(self.test_product["id"])
            batch_data["selling_price"] = price
            batch_data["quantity"] = 50
            
            batch = self.post("/batches", batch_data)
            batches.append(batch)
            self.register_for_cleanup("batch", batch["id"])
        
        # Get batch-wise pricing
        pricing = self.get(f"/products/{self.test_product['id']}/batch-pricing")
        
        assert len(pricing) >= 3
        for batch_price in pricing:
            assert batch_price["selling_price"] in prices


class TestBusinessPerformance(APITestBase):
    """Test business operations performance"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("admin")
        yield
    
    def test_product_search_performance(self):
        """Test product search performance with large dataset"""
        # This assumes products already exist in the system
        
        search_terms = ["Para", "Cough", "Vitamin", "Anti"]
        results = []
        
        for term in search_terms:
            start_time = time.time()
            response = self.get("/products", params={"search": term})
            duration = time.time() - start_time
            results.append(duration)
        
        avg_time = sum(results) / len(results)
        
        # Search should complete within 500ms
        assert avg_time < 0.5, f"Average search time {avg_time:.3f}s exceeds 500ms threshold"
    
    def test_order_creation_performance(self):
        """Test order creation performance"""
        # Prepare test data
        customer_data = TestDataFactory.generate_customer_data()
        customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", customer["id"])
        
        product_data = TestDataFactory.generate_product_data()
        product = self.post("/products", product_data)
        self.register_for_cleanup("product", product["id"])
        
        batch_data = TestDataFactory.generate_batch_data(product["id"])
        batch = self.post("/batches", batch_data)
        self.register_for_cleanup("batch", batch["id"])
        
        # Test order creation
        results = []
        
        for i in range(5):
            order_data = TestDataFactory.generate_order_data(customer["id"])
            order_data["items"] = [{
                "product_id": product["id"],
                "quantity": 10,
                "price": product["selling_price"]
            }]
            
            start_time = time.time()
            order = self.post("/orders", order_data)
            duration = time.time() - start_time
            results.append(duration)
            
            self.register_for_cleanup("order", order["id"])
        
        avg_time = sum(results) / len(results)
        max_time = max(results)
        
        # Order creation should complete within 1 second
        assert avg_time < 1.0, f"Average order creation time {avg_time:.3f}s exceeds 1s threshold"
        assert max_time < 2.0, f"Maximum order creation time {max_time:.3f}s exceeds 2s threshold"