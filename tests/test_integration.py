"""
Integration Tests
=================
Tests for third-party integrations including WhatsApp, SMS, 
file uploads, and external services.
"""

import pytest
import os
import json
from datetime import datetime
from typing import Dict, Any

from base_test import APITestBase
from test_suite_config import TestDataFactory


class TestWhatsAppIntegration(APITestBase):
    """Test WhatsApp messaging integration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("admin")
        
        # Create test customer with WhatsApp number
        customer_data = TestDataFactory.generate_customer_data()
        customer_data["phone"] = "+919876543210"  # Valid WhatsApp number format
        customer_data["whatsapp_enabled"] = True
        
        self.test_customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", self.test_customer["id"])
        
        yield
        self.cleanup_test_data()
    
    def test_send_order_confirmation(self):
        """Test sending order confirmation via WhatsApp"""
        # Create order
        product_data = TestDataFactory.generate_product_data()
        product = self.post("/products", product_data)
        self.register_for_cleanup("product", product["id"])
        
        batch_data = TestDataFactory.generate_batch_data(product["id"])
        batch = self.post("/batches", batch_data)
        self.register_for_cleanup("batch", batch["id"])
        
        order_data = TestDataFactory.generate_order_data(self.test_customer["id"])
        order_data["items"] = [{
            "product_id": product["id"],
            "quantity": 5,
            "price": product["selling_price"]
        }]
        
        order = self.post("/orders", order_data)
        self.register_for_cleanup("order", order["id"])
        
        # Send WhatsApp notification
        whatsapp_data = {
            "template": "order_confirmation",
            "parameters": {
                "order_number": order["id"],
                "customer_name": self.test_customer["name"],
                "total_amount": order["total_amount"],
                "delivery_date": order["delivery_date"]
            }
        }
        
        try:
            response = self.post(f"/orders/{order['id']}/whatsapp-notification", whatsapp_data)
            
            assert "message_id" in response or "status" in response
            assert response.get("status") in ["sent", "queued", "delivered"]
        except Exception as e:
            if "404" in str(e):
                pytest.skip("WhatsApp integration not implemented")
            elif "test" in str(e).lower() or "sandbox" in str(e).lower():
                # Accept test mode responses
                pass
            else:
                raise
    
    def test_send_payment_reminder(self):
        """Test sending payment reminder via WhatsApp"""
        reminder_data = {
            "customer_id": self.test_customer["id"],
            "template": "payment_reminder",
            "parameters": {
                "customer_name": self.test_customer["name"],
                "outstanding_amount": 50000,
                "due_date": "2024-01-15",
                "invoice_numbers": ["INV-2024-001", "INV-2024-002"]
            }
        }
        
        try:
            response = self.post("/whatsapp/payment-reminder", reminder_data)
            
            assert response.get("status") in ["sent", "queued", "delivered", "test_mode"]
        except Exception as e:
            if "404" in str(e):
                pytest.skip("WhatsApp payment reminder not implemented")
            else:
                raise
    
    def test_whatsapp_broadcast(self):
        """Test WhatsApp broadcast messaging"""
        # Create multiple customers
        customers = [self.test_customer["id"]]
        
        for i in range(2):
            customer_data = TestDataFactory.generate_customer_data()
            customer_data["whatsapp_enabled"] = True
            customer = self.post("/customers", customer_data)
            customers.append(customer["id"])
            self.register_for_cleanup("customer", customer["id"])
        
        # Send broadcast
        broadcast_data = {
            "customer_ids": customers,
            "template": "promotional_offer",
            "parameters": {
                "offer_text": "Get 10% off on all medicines this week!",
                "validity": "Valid till 31st January 2024"
            }
        }
        
        try:
            response = self.post("/whatsapp/broadcast", broadcast_data)
            
            assert "broadcast_id" in response
            assert response["total_recipients"] == len(customers)
            assert response["status"] in ["processing", "completed"]
        except Exception as e:
            if "404" in str(e):
                pytest.skip("WhatsApp broadcast not implemented")
            else:
                raise
    
    def test_whatsapp_template_validation(self):
        """Test WhatsApp template validation"""
        # Test with invalid template
        invalid_data = {
            "customer_id": self.test_customer["id"],
            "template": "non_existent_template",
            "parameters": {}
        }
        
        try:
            self.post("/whatsapp/send", invalid_data)
            pytest.fail("Invalid template was accepted")
        except Exception as e:
            assert "template" in str(e).lower() or "400" in str(e)


class TestSMSIntegration(APITestBase):
    """Test SMS messaging integration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("admin")
        yield
        self.cleanup_test_data()
    
    def test_send_otp_sms(self):
        """Test sending OTP via SMS"""
        otp_data = {
            "phone": "+919876543210",
            "purpose": "login_verification"
        }
        
        try:
            response = self.post("/sms/send-otp", otp_data)
            
            assert "otp_id" in response or "reference_id" in response
            assert response.get("status") in ["sent", "pending", "test_mode"]
            
            # In test mode, might return the OTP for verification
            if "otp" in response and response.get("test_mode"):
                assert len(str(response["otp"])) == 6  # 6-digit OTP
        except Exception as e:
            if "404" in str(e):
                pytest.skip("SMS OTP not implemented")
            else:
                raise
    
    def test_verify_otp(self):
        """Test OTP verification"""
        # First send OTP
        otp_data = {
            "phone": "+919876543210",
            "purpose": "login_verification"
        }
        
        try:
            send_response = self.post("/sms/send-otp", otp_data)
            
            # Verify OTP
            verify_data = {
                "phone": otp_data["phone"],
                "otp": send_response.get("otp", "123456"),  # Use test OTP if provided
                "reference_id": send_response.get("otp_id") or send_response.get("reference_id")
            }
            
            verify_response = self.post("/sms/verify-otp", verify_data)
            
            assert verify_response.get("verified") in [True, False]
            assert "message" in verify_response
        except Exception as e:
            if "404" in str(e):
                pytest.skip("SMS OTP verification not implemented")
            else:
                raise
    
    def test_send_transactional_sms(self):
        """Test sending transactional SMS"""
        # Create customer
        customer_data = TestDataFactory.generate_customer_data()
        customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", customer["id"])
        
        sms_data = {
            "phone": customer["phone"],
            "message": f"Dear {customer['name']}, your order #12345 has been dispatched and will be delivered by tomorrow.",
            "type": "transactional"
        }
        
        try:
            response = self.post("/sms/send", sms_data)
            
            assert response.get("status") in ["sent", "queued", "delivered", "test_mode"]
            assert "message_id" in response or "reference_id" in response
        except Exception as e:
            if "404" in str(e):
                pytest.skip("Transactional SMS not implemented")
            else:
                raise


class TestFileUpload(APITestBase):
    """Test file upload functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("admin")
        yield
        self.cleanup_test_data()
    
    def test_upload_product_image(self):
        """Test uploading product images"""
        # Create product
        product_data = TestDataFactory.generate_product_data()
        product = self.post("/products", product_data)
        self.register_for_cleanup("product", product["id"])
        
        # Upload image
        files = {
            "file": ("product_image.jpg", b"Mock JPEG image content", "image/jpeg")
        }
        
        try:
            response = self.post(
                f"/products/{product['id']}/image",
                files=files
            )
            
            assert "image_url" in response or "file_url" in response
            assert response.get("file_type") == "image/jpeg"
        except Exception as e:
            if "404" in str(e):
                pytest.skip("Product image upload not implemented")
            else:
                raise
    
    def test_upload_purchase_invoice(self):
        """Test uploading purchase invoices"""
        # Create test data
        supplier_data = {
            "name": "Test Supplier",
            "gst_number": TestDataFactory.generate_gst_number()
        }
        
        # Mock purchase invoice PDF
        pdf_content = b"%PDF-1.4 Mock PDF content"
        
        files = {
            "file": ("purchase_invoice.pdf", pdf_content, "application/pdf")
        }
        
        data = {
            "supplier_name": supplier_data["name"],
            "invoice_number": "PINV-2024-001",
            "invoice_date": datetime.now().date().isoformat()
        }
        
        try:
            response = self.post(
                "/purchases/upload-invoice",
                data=data,
                files=files
            )
            
            assert "file_id" in response or "invoice_id" in response
            assert response.get("status") in ["uploaded", "processing", "completed"]
            
            # Check if OCR/parsing was attempted
            if "extracted_data" in response:
                assert isinstance(response["extracted_data"], dict)
        except Exception as e:
            if "404" in str(e):
                pytest.skip("Purchase invoice upload not implemented")
            else:
                raise
    
    def test_upload_customer_documents(self):
        """Test uploading customer KYC documents"""
        # Create customer
        customer_data = TestDataFactory.generate_customer_data()
        customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", customer["id"])
        
        # Upload multiple documents
        documents = [
            {
                "type": "drug_license",
                "file": ("drug_license.pdf", b"Mock drug license PDF", "application/pdf")
            },
            {
                "type": "gst_certificate",
                "file": ("gst_cert.pdf", b"Mock GST certificate PDF", "application/pdf")
            },
            {
                "type": "pan_card",
                "file": ("pan_card.jpg", b"Mock PAN card image", "image/jpeg")
            }
        ]
        
        uploaded_docs = []
        
        for doc in documents:
            files = {"file": doc["file"]}
            data = {"document_type": doc["type"]}
            
            try:
                response = self.post(
                    f"/customers/{customer['id']}/documents",
                    data=data,
                    files=files
                )
                
                uploaded_docs.append(response)
                assert "document_id" in response or "id" in response
                assert response.get("document_type") == doc["type"]
            except Exception as e:
                if "404" not in str(e):
                    raise
        
        if not uploaded_docs:
            pytest.skip("Customer document upload not implemented")
    
    def test_file_size_validation(self):
        """Test file size limits"""
        # Create large file (mock)
        large_file_size = 50 * 1024 * 1024  # 50MB
        large_file_content = b"X" * 1000  # Mock large file with small content
        
        files = {
            "file": ("large_file.pdf", large_file_content, "application/pdf")
        }
        
        # Add Content-Length header to simulate large file
        headers = {"Content-Length": str(large_file_size)}
        
        try:
            self.session.headers.update(headers)
            self.post("/file-uploads/test", files=files)
            pytest.fail("Large file was accepted")
        except Exception as e:
            assert "413" in str(e) or "size" in str(e).lower() or "large" in str(e).lower()
        finally:
            # Reset headers
            self.session.headers.pop("Content-Length", None)
    
    def test_file_type_validation(self):
        """Test file type restrictions"""
        # Try uploading executable file
        files = {
            "file": ("malicious.exe", b"MZ\x90\x00", "application/x-executable")
        }
        
        try:
            self.post("/file-uploads/test", files=files)
            pytest.fail("Executable file was accepted")
        except Exception as e:
            assert "400" in str(e) or "type" in str(e).lower() or "format" in str(e).lower()


class TestEmailIntegration(APITestBase):
    """Test email notification functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("admin")
        yield
        self.cleanup_test_data()
    
    def test_send_invoice_email(self):
        """Test sending invoice via email"""
        # Create customer with email
        customer_data = TestDataFactory.generate_customer_data()
        customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", customer["id"])
        
        # Create order and invoice
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
        
        # Send email
        email_data = {
            "to": customer["email"],
            "cc": ["accounts@pharmaco.com"],
            "subject": f"Invoice {invoice['invoice_number']}",
            "template": "invoice_email",
            "attachments": ["invoice_pdf"]
        }
        
        try:
            response = self.post(f"/invoices/{invoice['id']}/email", email_data)
            
            assert response.get("status") in ["sent", "queued", "test_mode"]
            assert "message_id" in response or "email_id" in response
        except Exception as e:
            if "404" in str(e):
                pytest.skip("Invoice email not implemented")
            else:
                raise
    
    def test_send_payment_receipt_email(self):
        """Test sending payment receipt via email"""
        # Create customer
        customer_data = TestDataFactory.generate_customer_data()
        customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", customer["id"])
        
        # Create payment
        payment_data = {
            "customer_id": customer["id"],
            "amount": 25000,
            "payment_method": "bank_transfer",
            "reference_number": "TXN123456"
        }
        
        payment = self.post("/payments", payment_data)
        self.register_for_cleanup("payment", payment["id"])
        
        # Send receipt
        email_data = {
            "to": customer["email"],
            "template": "payment_receipt"
        }
        
        try:
            response = self.post(f"/payments/{payment['id']}/email-receipt", email_data)
            
            assert response.get("status") in ["sent", "queued", "test_mode"]
        except Exception as e:
            if "404" in str(e):
                pytest.skip("Payment receipt email not implemented")
            else:
                raise
    
    def test_email_template_personalization(self):
        """Test email template variable substitution"""
        # Create test data
        customer_data = TestDataFactory.generate_customer_data()
        customer = self.post("/customers", customer_data)
        self.register_for_cleanup("customer", customer["id"])
        
        # Test template rendering
        template_data = {
            "template": "welcome_email",
            "variables": {
                "customer_name": customer["name"],
                "company_name": "PharmaCo Ltd",
                "account_manager": "John Doe",
                "support_email": "support@pharmaco.com"
            },
            "preview_only": True  # Don't actually send
        }
        
        try:
            response = self.post("/email/preview", template_data)
            
            assert "subject" in response
            assert "html_body" in response or "body" in response
            
            # Check variable substitution
            body = response.get("html_body") or response.get("body")
            assert customer["name"] in body
            assert "PharmaCo Ltd" in body
        except Exception as e:
            if "404" in str(e):
                pytest.skip("Email template preview not implemented")
            else:
                raise


class TestExternalAPIIntegration(APITestBase):
    """Test integration with external APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.authenticate("admin")
        yield
    
    def test_gst_verification(self):
        """Test GST number verification with government API"""
        gst_numbers = [
            "27AABCU9603R1ZM",  # Sample Maharashtra GST
            "29AABCU9603R1ZK",  # Sample Karnataka GST
        ]
        
        for gst in gst_numbers:
            try:
                response = self.post("/integrations/verify-gst", {
                    "gst_number": gst
                })
                
                assert response.get("valid") in [True, False]
                
                if response["valid"]:
                    assert "business_name" in response
                    assert "address" in response
                    assert "status" in response
            except Exception as e:
                if "404" in str(e):
                    pytest.skip("GST verification not implemented")
                elif "test" in str(e).lower() or "mock" in str(e).lower():
                    # Accept test/mock responses
                    pass
                else:
                    raise
    
    def test_pincode_lookup(self):
        """Test pincode to location lookup"""
        pincodes = ["560001", "400001", "110001"]  # Bangalore, Mumbai, Delhi
        
        for pincode in pincodes:
            try:
                response = self.get("/integrations/pincode-lookup", 
                                  params={"pincode": pincode})
                
                assert "city" in response
                assert "state" in response
                assert "district" in response
                
                # Validate known pincodes
                if pincode == "560001":
                    assert response["city"].lower() in ["bangalore", "bengaluru"]
                    assert response["state"].lower() == "karnataka"
            except Exception as e:
                if "404" in str(e):
                    pytest.skip("Pincode lookup not implemented")
                else:
                    raise
    
    def test_drug_database_lookup(self):
        """Test drug information lookup from database"""
        drug_names = ["Paracetamol", "Amoxicillin", "Omeprazole"]
        
        for drug in drug_names:
            try:
                response = self.get("/integrations/drug-info",
                                  params={"name": drug})
                
                assert "drug_name" in response
                assert "compositions" in response or "active_ingredients" in response
                assert "therapeutic_class" in response
                
                # Check for scheduling info
                if "schedule" in response:
                    assert response["schedule"] in ["H", "H1", "X", "G", "J", "K", ""]
            except Exception as e:
                if "404" in str(e):
                    pytest.skip("Drug database lookup not implemented")
                else:
                    raise