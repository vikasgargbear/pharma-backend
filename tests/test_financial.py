"""
Financial Operations Tests
=========================
Tests for financial modules including payments, invoicing, 
tax calculations, and credit management.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List

from base_test import APITestBase
from test_suite_config import TestDataFactory


class TestPayments(APITestBase):
    """Test payment processing functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("accounts")
        
        # Create test customer
        customer_data = TestDataFactory.generate_customer_data()
        customer_data["credit_limit"] = 100000
        self.test_customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", self.test_customer["id"])
        
        # Create test order
        product_data = TestDataFactory.generate_product_data()
        product = self.post("/products", product_data)
        self.register_for_cleanup("product", product["id"])
        
        batch_data = TestDataFactory.generate_batch_data(product["id"])
        batch = self.post("/batches", batch_data)
        self.register_for_cleanup("batch", batch["id"])
        
        order_data = TestDataFactory.generate_order_data(self.test_customer["id"])
        order_data["items"] = [{
            "product_id": product["id"],
            "quantity": 10,
            "price": product["selling_price"],
            "gst_rate": product["gst_rate"]
        }]
        self.test_order = self.post("/orders", order_data)
        self.register_for_cleanup("order", self.test_order["id"])
        
        yield
        self.cleanup_test_data()
    
    def test_payment_recording(self):
        """Test recording various types of payments"""
        payment_methods = ["cash", "cheque", "upi", "bank_transfer", "credit"]
        
        for method in payment_methods:
            payment_data = {
                "order_id": self.test_order["id"],
                "amount": 1000.00,
                "payment_method": method,
                "payment_date": datetime.now().isoformat(),
                "reference_number": f"REF-{method.upper()}-12345"
            }
            
            if method == "cheque":
                payment_data["cheque_number"] = "123456"
                payment_data["cheque_date"] = datetime.now().date().isoformat()
                payment_data["bank_name"] = "Test Bank"
            
            response = self.post("/payments", payment_data)
            
            assert "id" in response
            assert response["payment_method"] == method
            assert response["amount"] == 1000.00
            assert response["status"] in ["completed", "pending"]
            
            self.register_for_cleanup("payment", response["id"])
    
    def test_advance_payment(self):
        """Test advance payment handling"""
        advance_data = {
            "customer_id": self.test_customer["id"],
            "amount": 50000.00,
            "payment_method": "bank_transfer",
            "payment_type": "advance",
            "reference_number": "ADV-12345"
        }
        
        response = self.post("/payments/advance", advance_data)
        
        assert response["payment_type"] == "advance"
        assert response["amount"] == 50000.00
        
        # Check customer advance balance
        balance = self.get(f"/customers/{self.test_customer['id']}/advance-balance")
        assert balance["advance_balance"] >= 50000.00
    
    def test_payment_allocation(self):
        """Test automatic payment allocation to multiple invoices"""
        # Create multiple orders
        orders = []
        total_amount = 0
        
        for i in range(3):
            order_data = TestDataFactory.generate_order_data(self.test_customer["id"])
            order_data["items"] = [{
                "product_id": self.test_order["items"][0]["product_id"],
                "quantity": 5,
                "price": 100.00,
                "gst_rate": 18
            }]
            order = self.post("/orders", order_data)
            orders.append(order)
            self.register_for_cleanup("order", order["id"])
            
            # Calculate total with GST
            total_amount += 500 * 1.18  # 500 + 18% GST
        
        # Make bulk payment
        payment_data = {
            "customer_id": self.test_customer["id"],
            "amount": total_amount,
            "payment_method": "bank_transfer",
            "allocate_to_orders": True
        }
        
        response = self.post("/payments/bulk", payment_data)
        
        # Verify payment is allocated to all orders
        for order in orders:
            order_payments = self.get(f"/orders/{order['id']}/payments")
            assert len(order_payments) > 0
            assert sum(p["amount"] for p in order_payments) == 590.00  # 500 + GST
    
    def test_payment_reconciliation(self):
        """Test payment reconciliation process"""
        # Record payment
        payment_data = {
            "order_id": self.test_order["id"],
            "amount": self.test_order["total_amount"],
            "payment_method": "cheque",
            "cheque_number": "789012",
            "cheque_date": datetime.now().date().isoformat(),
            "bank_name": "Test Bank"
        }
        
        payment = self.post("/payments", payment_data)
        payment_id = payment["id"]
        
        # Reconcile payment
        reconcile_data = {
            "cleared_date": datetime.now().isoformat(),
            "bank_reference": "BANK-REF-12345",
            "cleared_amount": payment["amount"]
        }
        
        self.put(f"/payments/{payment_id}/reconcile", reconcile_data)
        
        # Verify payment is reconciled
        updated_payment = self.get(f"/payments/{payment_id}")
        assert updated_payment["status"] == "completed"
        assert updated_payment["is_reconciled"] == True


class TestInvoicing(APITestBase):
    """Test invoicing and billing functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("accounts")
        yield
        self.cleanup_test_data()
    
    def test_invoice_generation(self):
        """Test invoice generation with proper tax calculations"""
        # Create customer
        customer_data = TestDataFactory.generate_customer_data()
        customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", customer["id"])
        
        # Create products with different GST rates
        gst_rates = [5, 12, 18, 28]
        products = []
        
        for rate in gst_rates:
            product_data = TestDataFactory.generate_product_data()
            product_data["gst_rate"] = rate
            product_data["selling_price"] = 1000.00
            
            product = self.post("/products", product_data)
            products.append(product)
            self.register_for_cleanup("product", product["id"])
            
            # Create batch
            batch_data = TestDataFactory.generate_batch_data(product["id"])
            batch = self.post("/batches", batch_data)
            self.register_for_cleanup("batch", batch["id"])
        
        # Create order with multiple items
        order_data = TestDataFactory.generate_order_data(customer["id"])
        order_data["items"] = [
            {
                "product_id": product["id"],
                "quantity": 2,
                "price": product["selling_price"],
                "gst_rate": product["gst_rate"]
            }
            for product in products
        ]
        
        order = self.post("/orders", order_data)
        self.register_for_cleanup("order", order["id"])
        
        # Generate invoice
        invoice = self.post(f"/orders/{order['id']}/invoice", {})
        
        # Validate invoice
        assert "invoice_number" in invoice
        assert invoice["customer_id"] == customer["id"]
        assert len(invoice["items"]) == 4
        
        # Validate tax calculations
        expected_subtotal = 8000.00  # 4 products × 2 quantity × 1000 price
        expected_gst = {
            5: 100.00,   # 2000 × 5%
            12: 240.00,  # 2000 × 12%
            18: 360.00,  # 2000 × 18%
            28: 560.00   # 2000 × 28%
        }
        
        assert invoice["subtotal"] == expected_subtotal
        
        # Check GST breakup
        gst_details = invoice.get("gst_details", {})
        for rate, expected_tax in expected_gst.items():
            assert abs(gst_details.get(f"gst_{rate}", 0) - expected_tax) < 0.01
        
        total_gst = sum(expected_gst.values())
        assert abs(invoice["total_amount"] - (expected_subtotal + total_gst)) < 0.01
    
    def test_credit_note_generation(self):
        """Test credit note generation for returns"""
        # Create a completed order
        customer_data = TestDataFactory.generate_customer_data()
        customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", customer["id"])
        
        product_data = TestDataFactory.generate_product_data()
        product_data["selling_price"] = 500.00
        product_data["gst_rate"] = 18
        
        product = self.post("/products", product_data)
        self.register_for_cleanup("product", product["id"])
        
        batch_data = TestDataFactory.generate_batch_data(product["id"])
        batch = self.post("/batches", batch_data)
        self.register_for_cleanup("batch", batch["id"])
        
        order_data = TestDataFactory.generate_order_data(customer["id"])
        order_data["items"] = [{
            "product_id": product["id"],
            "quantity": 10,
            "price": product["selling_price"],
            "gst_rate": product["gst_rate"]
        }]
        
        order = self.post("/orders", order_data)
        self.register_for_cleanup("order", order["id"])
        
        # Create return
        return_data = {
            "order_id": order["id"],
            "items": [{
                "product_id": product["id"],
                "quantity": 3,
                "reason": "Damaged goods"
            }]
        }
        
        sales_return = self.post("/sales-returns", return_data)
        
        # Generate credit note
        credit_note = self.post(f"/sales-returns/{sales_return['id']}/credit-note", {})
        
        assert "credit_note_number" in credit_note
        assert credit_note["type"] == "credit_note"
        
        # Validate amounts
        expected_amount = 3 * 500 * 1.18  # 3 items × 500 × (1 + 18% GST)
        assert abs(credit_note["total_amount"] - expected_amount) < 0.01
    
    def test_invoice_pdf_generation(self):
        """Test PDF invoice generation"""
        # Create simple order
        customer_data = TestDataFactory.generate_customer_data()
        customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", customer["id"])
        
        product_data = TestDataFactory.generate_product_data()
        product = self.post("/products", product_data)
        self.register_for_cleanup("product", product["id"])
        
        batch_data = TestDataFactory.generate_batch_data(product["id"])
        batch = self.post("/batches", batch_data)
        self.register_for_cleanup("batch", batch["id"])
        
        order_data = TestDataFactory.generate_order_data(customer["id"])
        order_data["items"] = [{
            "product_id": product["id"],
            "quantity": 5,
            "price": product["selling_price"]
        }]
        
        order = self.post("/orders", order_data)
        self.register_for_cleanup("order", order["id"])
        
        # Generate invoice
        invoice = self.post(f"/orders/{order['id']}/invoice", {})
        
        # Generate PDF
        try:
            pdf_response = self.get(f"/invoices/{invoice['id']}/pdf")
            
            # Basic validation - check if we got binary data
            assert isinstance(pdf_response, bytes) or "pdf_url" in pdf_response
        except Exception as e:
            if "404" in str(e):
                pytest.skip("PDF generation not implemented")
            else:
                raise


class TestTaxCalculations(APITestBase):
    """Test GST and tax calculation scenarios"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("accounts")
        yield
        self.cleanup_test_data()
    
    def test_interstate_gst_calculation(self):
        """Test IGST calculation for interstate transactions"""
        # Create customer from different state
        customer_data = TestDataFactory.generate_customer_data()
        customer_data["state"] = "Maharashtra"
        customer_data["gst_number"] = "27ABCDE1234F1Z5"  # Maharashtra GST
        
        customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", customer["id"])
        
        # Create product
        product_data = TestDataFactory.generate_product_data()
        product_data["gst_rate"] = 18
        product_data["selling_price"] = 1000.00
        
        product = self.post("/products", product_data)
        self.register_for_cleanup("product", product["id"])
        
        batch_data = TestDataFactory.generate_batch_data(product["id"])
        batch = self.post("/batches", batch_data)
        self.register_for_cleanup("batch", batch["id"])
        
        # Create order (assuming company is in different state)
        order_data = TestDataFactory.generate_order_data(customer["id"])
        order_data["items"] = [{
            "product_id": product["id"],
            "quantity": 10,
            "price": product["selling_price"]
        }]
        
        order = self.post("/orders", order_data)
        self.register_for_cleanup("order", order["id"])
        
        # Generate invoice
        invoice = self.post(f"/orders/{order['id']}/invoice", {})
        
        # For interstate, should be IGST only
        assert invoice.get("igst_amount", 0) > 0
        assert invoice.get("cgst_amount", 0) == 0
        assert invoice.get("sgst_amount", 0) == 0
        
        # IGST should be 18% of base amount
        expected_igst = 10000 * 0.18  # 10 × 1000 × 18%
        assert abs(invoice.get("igst_amount", 0) - expected_igst) < 0.01
    
    def test_intrastate_gst_calculation(self):
        """Test CGST/SGST calculation for intrastate transactions"""
        # Create customer from same state
        customer_data = TestDataFactory.generate_customer_data()
        customer_data["state"] = "Karnataka"  # Assuming company is in Karnataka
        customer_data["gst_number"] = "29ABCDE1234F1Z5"  # Karnataka GST
        
        customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", customer["id"])
        
        # Create product
        product_data = TestDataFactory.generate_product_data()
        product_data["gst_rate"] = 18
        product_data["selling_price"] = 1000.00
        
        product = self.post("/products", product_data)
        self.register_for_cleanup("product", product["id"])
        
        batch_data = TestDataFactory.generate_batch_data(product["id"])
        batch = self.post("/batches", batch_data)
        self.register_for_cleanup("batch", batch["id"])
        
        # Create order
        order_data = TestDataFactory.generate_order_data(customer["id"])
        order_data["items"] = [{
            "product_id": product["id"],
            "quantity": 10,
            "price": product["selling_price"]
        }]
        
        order = self.post("/orders", order_data)
        self.register_for_cleanup("order", order["id"])
        
        # Generate invoice
        invoice = self.post(f"/orders/{order['id']}/invoice", {})
        
        # For intrastate, should be CGST + SGST
        assert invoice.get("cgst_amount", 0) > 0
        assert invoice.get("sgst_amount", 0) > 0
        assert invoice.get("igst_amount", 0) == 0
        
        # CGST and SGST should each be 9% (half of 18%)
        expected_cgst = 10000 * 0.09  # 10 × 1000 × 9%
        expected_sgst = 10000 * 0.09  # 10 × 1000 × 9%
        
        assert abs(invoice.get("cgst_amount", 0) - expected_cgst) < 0.01
        assert abs(invoice.get("sgst_amount", 0) - expected_sgst) < 0.01
    
    def test_tax_invoice_with_discounts(self):
        """Test tax calculation with various discount scenarios"""
        customer_data = TestDataFactory.generate_customer_data()
        customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", customer["id"])
        
        product_data = TestDataFactory.generate_product_data()
        product_data["gst_rate"] = 12
        product_data["selling_price"] = 1000.00
        
        product = self.post("/products", product_data)
        self.register_for_cleanup("product", product["id"])
        
        batch_data = TestDataFactory.generate_batch_data(product["id"])
        batch = self.post("/batches", batch_data)
        self.register_for_cleanup("batch", batch["id"])
        
        # Order with item-level discount
        order_data = TestDataFactory.generate_order_data(customer["id"])
        order_data["items"] = [{
            "product_id": product["id"],
            "quantity": 10,
            "price": product["selling_price"],
            "discount_percent": 10  # 10% discount
        }]
        order_data["additional_discount"] = 100  # Additional Rs. 100 discount
        
        order = self.post("/orders", order_data)
        self.register_for_cleanup("order", order["id"])
        
        # Generate invoice
        invoice = self.post(f"/orders/{order['id']}/invoice", {})
        
        # Calculate expected values
        base_amount = 10 * 1000  # 10,000
        after_item_discount = base_amount * 0.9  # 9,000 (10% discount)
        after_additional_discount = after_item_discount - 100  # 8,900
        gst_amount = after_additional_discount * 0.12  # 1,068
        total = after_additional_discount + gst_amount  # 9,968
        
        assert abs(invoice["subtotal"] - after_additional_discount) < 0.01
        assert abs(invoice["total_amount"] - total) < 0.01


class TestCreditManagement(APITestBase):
    """Test customer credit and outstanding management"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("accounts")
        yield
        self.cleanup_test_data()
    
    def test_credit_limit_enforcement(self):
        """Test credit limit enforcement during order creation"""
        # Create customer with specific credit limit
        customer_data = TestDataFactory.generate_customer_data()
        customer_data["credit_limit"] = 10000
        customer_data["payment_terms"] = 30  # 30 days credit
        
        customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", customer["id"])
        
        # Create product
        product_data = TestDataFactory.generate_product_data()
        product_data["selling_price"] = 2000.00
        
        product = self.post("/products", product_data)
        self.register_for_cleanup("product", product["id"])
        
        batch_data = TestDataFactory.generate_batch_data(product["id"])
        batch = self.post("/batches", batch_data)
        self.register_for_cleanup("batch", batch["id"])
        
        # Create order within credit limit
        order_data = TestDataFactory.generate_order_data(customer["id"])
        order_data["items"] = [{
            "product_id": product["id"],
            "quantity": 4,  # Total: 8000
            "price": product["selling_price"]
        }]
        order_data["payment_method"] = "credit"
        
        order1 = self.post("/orders", order_data)
        self.register_for_cleanup("order", order1["id"])
        
        # Try to create order exceeding credit limit
        order_data2 = TestDataFactory.generate_order_data(customer["id"])
        order_data2["items"] = [{
            "product_id": product["id"],
            "quantity": 3,  # Total: 6000, exceeds remaining credit
            "price": product["selling_price"]
        }]
        order_data2["payment_method"] = "credit"
        
        try:
            self.post("/orders", order_data2)
            pytest.fail("Order exceeding credit limit was allowed")
        except Exception as e:
            assert "credit" in str(e).lower() or "limit" in str(e).lower()
    
    def test_outstanding_aging_report(self):
        """Test outstanding amount aging analysis"""
        # Create customer
        customer_data = TestDataFactory.generate_customer_data()
        customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", customer["id"])
        
        # Create product
        product_data = TestDataFactory.generate_product_data()
        product = self.post("/products", product_data)
        self.register_for_cleanup("product", product["id"])
        
        batch_data = TestDataFactory.generate_batch_data(product["id"])
        batch = self.post("/batches", batch_data)
        self.register_for_cleanup("batch", batch["id"])
        
        # Create orders with different dates
        orders_data = [
            {"days_ago": 5, "amount": 1000},
            {"days_ago": 35, "amount": 2000},
            {"days_ago": 65, "amount": 3000},
            {"days_ago": 95, "amount": 4000}
        ]
        
        for order_info in orders_data:
            order_date = datetime.now() - timedelta(days=order_info["days_ago"])
            
            order_data = TestDataFactory.generate_order_data(customer["id"])
            order_data["order_date"] = order_date.isoformat()
            order_data["items"] = [{
                "product_id": product["id"],
                "quantity": 1,
                "price": order_info["amount"]
            }]
            order_data["payment_method"] = "credit"
            
            order = self.post("/orders", order_data)
            self.register_for_cleanup("order", order["id"])
        
        # Get aging report
        aging_report = self.get(f"/customers/{customer['id']}/outstanding-aging")
        
        # Verify aging buckets
        assert "0_30_days" in aging_report
        assert "31_60_days" in aging_report
        assert "61_90_days" in aging_report
        assert "over_90_days" in aging_report
        
        # Verify amounts in correct buckets
        assert aging_report["0_30_days"] >= 1000
        assert aging_report["31_60_days"] >= 2000
        assert aging_report["61_90_days"] >= 3000
        assert aging_report["over_90_days"] >= 4000
    
    def test_payment_reminder_generation(self):
        """Test automatic payment reminder generation"""
        # Create customer
        customer_data = TestDataFactory.generate_customer_data()
        customer_data["payment_terms"] = 15  # 15 days credit
        
        customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", customer["id"])
        
        # Create overdue order
        product_data = TestDataFactory.generate_product_data()
        product = self.post("/products", product_data)
        self.register_for_cleanup("product", product["id"])
        
        batch_data = TestDataFactory.generate_batch_data(product["id"])
        batch = self.post("/batches", batch_data)
        self.register_for_cleanup("batch", batch["id"])
        
        order_date = datetime.now() - timedelta(days=20)  # 5 days overdue
        order_data = TestDataFactory.generate_order_data(customer["id"])
        order_data["order_date"] = order_date.isoformat()
        order_data["items"] = [{
            "product_id": product["id"],
            "quantity": 10,
            "price": 1000
        }]
        order_data["payment_method"] = "credit"
        
        order = self.post("/orders", order_data)
        self.register_for_cleanup("order", order["id"])
        
        # Generate payment reminders
        reminders = self.get("/payment-reminders/pending")
        
        # Verify reminder exists for overdue payment
        customer_reminders = [r for r in reminders if r["customer_id"] == customer["id"]]
        assert len(customer_reminders) > 0
        
        reminder = customer_reminders[0]
        assert reminder["days_overdue"] >= 5
        assert reminder["outstanding_amount"] > 0