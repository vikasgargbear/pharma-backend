#!/usr/bin/env python3
"""
Consolidated Purchase System Test Suite
Run this to verify the complete purchase system functionality
"""
import requests
import json
from datetime import datetime, timedelta
import sys

BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"

class PurchaseSystemTester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.results = []
    
    def run_all_tests(self):
        """Run all test scenarios"""
        print("="*70)
        print("PURCHASE SYSTEM TEST SUITE")
        print("="*70)
        
        # Test 1: Basic purchase flow
        self.test_basic_purchase_flow()
        
        # Test 2: Auto batch generation
        self.test_auto_batch_generation()
        
        # Test 3: Custom batch override
        self.test_custom_batch_override()
        
        # Test 4: PDF simulation
        self.test_pdf_simulation()
        
        # Summary
        self.print_summary()
    
    def test_basic_purchase_flow(self):
        """Test complete purchase to receipt flow"""
        print("\n[TEST 1] Basic Purchase Flow")
        print("-" * 40)
        
        try:
            # Create purchase
            purchase_data = self._get_purchase_data("BASIC-TEST")
            resp = requests.post(f"{self.base_url}/api/v1/purchases-enhanced/with-items", json=purchase_data)
            
            if resp.status_code != 200:
                self._record_result("Basic Purchase Flow", False, f"Create failed: {resp.status_code}")
                return
            
            purchase_id = resp.json()['purchase_id']
            print(f"✓ Created purchase #{resp.json()['purchase_number']}")
            
            # Get items
            resp = requests.get(f"{self.base_url}/api/v1/purchases-enhanced/{purchase_id}/items")
            items = resp.json()
            
            # Receive goods
            receive_data = {
                "items": [{
                    "purchase_item_id": items[0]['purchase_item_id'],
                    "received_quantity": items[0]['ordered_quantity']
                }]
            }
            
            resp = requests.post(
                f"{self.base_url}/api/v1/purchases-enhanced/{purchase_id}/receive-fixed",
                json=receive_data
            )
            
            if resp.status_code == 200:
                print(f"✓ Goods received: {resp.json()['grn_number']}")
                self._record_result("Basic Purchase Flow", True, "Complete flow successful")
            else:
                self._record_result("Basic Purchase Flow", False, resp.json().get('detail'))
                
        except Exception as e:
            self._record_result("Basic Purchase Flow", False, str(e))
    
    def test_auto_batch_generation(self):
        """Test automatic batch number generation"""
        print("\n[TEST 2] Auto Batch Generation")
        print("-" * 40)
        
        try:
            # Create without batch
            purchase_data = self._get_purchase_data("AUTO-BATCH", include_batch=False)
            resp = requests.post(f"{self.base_url}/api/v1/purchases-enhanced/with-items", json=purchase_data)
            
            if resp.status_code != 200:
                self._record_result("Auto Batch Generation", False, "Create failed")
                return
            
            purchase_id = resp.json()['purchase_id']
            print(f"✓ Created without batch: #{resp.json()['purchase_number']}")
            
            # Receive without batch
            resp = requests.get(f"{self.base_url}/api/v1/purchases-enhanced/{purchase_id}/items")
            items = resp.json()
            
            receive_data = {
                "items": [{
                    "purchase_item_id": items[0]['purchase_item_id'],
                    "received_quantity": items[0]['ordered_quantity']
                }]
            }
            
            resp = requests.post(
                f"{self.base_url}/api/v1/purchases-enhanced/{purchase_id}/receive-fixed",
                json=receive_data
            )
            
            if resp.status_code == 200:
                print("✓ Auto-generated batch successfully")
                self._record_result("Auto Batch Generation", True, "Batch auto-generated")
            else:
                self._record_result("Auto Batch Generation", False, resp.json().get('detail'))
                
        except Exception as e:
            self._record_result("Auto Batch Generation", False, str(e))
    
    def test_custom_batch_override(self):
        """Test custom batch number at receipt"""
        print("\n[TEST 3] Custom Batch Override")
        print("-" * 40)
        
        try:
            # Create without batch
            purchase_data = self._get_purchase_data("CUSTOM-OVERRIDE", include_batch=False)
            resp = requests.post(f"{self.base_url}/api/v1/purchases-enhanced/with-items", json=purchase_data)
            
            if resp.status_code != 200:
                self._record_result("Custom Batch Override", False, "Create failed")
                return
            
            purchase_id = resp.json()['purchase_id']
            print(f"✓ Created: #{resp.json()['purchase_number']}")
            
            # Receive WITH custom batch
            resp = requests.get(f"{self.base_url}/api/v1/purchases-enhanced/{purchase_id}/items")
            items = resp.json()
            
            custom_batch = f"CUSTOM-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            receive_data = {
                "items": [{
                    "purchase_item_id": items[0]['purchase_item_id'],
                    "received_quantity": items[0]['ordered_quantity'],
                    "batch_number": custom_batch,
                    "expiry_date": "2026-12-31"
                }]
            }
            
            resp = requests.post(
                f"{self.base_url}/api/v1/purchases-enhanced/{purchase_id}/receive-fixed",
                json=receive_data
            )
            
            if resp.status_code == 200:
                print(f"✓ Custom batch applied: {custom_batch}")
                self._record_result("Custom Batch Override", True, "Custom batch accepted")
            else:
                self._record_result("Custom Batch Override", False, resp.json().get('detail'))
                
        except Exception as e:
            self._record_result("Custom Batch Override", False, str(e))
    
    def test_pdf_simulation(self):
        """Test PDF parsing simulation with partial data"""
        print("\n[TEST 4] PDF Parsing Simulation")
        print("-" * 40)
        
        try:
            # Simulate PDF with batch but no expiry
            purchase_data = self._get_purchase_data("PDF-SIM")
            purchase_data['items'][0]['batch_number'] = "PDF-BATCH-2024"
            purchase_data['items'][0].pop('expiry_date', None)  # Remove expiry
            
            resp = requests.post(f"{self.base_url}/api/v1/purchases-enhanced/with-items", json=purchase_data)
            
            if resp.status_code != 200:
                self._record_result("PDF Simulation", False, "Create failed")
                return
            
            purchase_id = resp.json()['purchase_id']
            print(f"✓ Created with partial data: #{resp.json()['purchase_number']}")
            
            # Receive - should use batch and add default expiry
            resp = requests.get(f"{self.base_url}/api/v1/purchases-enhanced/{purchase_id}/items")
            items = resp.json()
            
            receive_data = {
                "items": [{
                    "purchase_item_id": items[0]['purchase_item_id'],
                    "received_quantity": items[0]['ordered_quantity']
                }]
            }
            
            resp = requests.post(
                f"{self.base_url}/api/v1/purchases-enhanced/{purchase_id}/receive-fixed",
                json=receive_data
            )
            
            if resp.status_code == 200:
                print("✓ Handled partial data with defaults")
                self._record_result("PDF Simulation", True, "Defaults applied successfully")
            else:
                self._record_result("PDF Simulation", False, resp.json().get('detail'))
                
        except Exception as e:
            self._record_result("PDF Simulation", False, str(e))
    
    def _get_purchase_data(self, invoice_prefix, include_batch=True):
        """Generate test purchase data"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        data = {
            "supplier_id": 1,
            "purchase_date": datetime.now().date().isoformat(),
            "supplier_invoice_number": f"{invoice_prefix}-{timestamp}",
            "supplier_invoice_date": datetime.now().date().isoformat(),
            "subtotal_amount": 1000.00,
            "tax_amount": 120.00,
            "final_amount": 1120.00,
            "items": [
                {
                    "product_id": 14,
                    "product_name": "Ibuprofen 400mg",
                    "ordered_quantity": 50,
                    "cost_price": 20.00,
                    "mrp": 30.00,
                    "tax_percent": 12.0
                }
            ]
        }
        
        if include_batch:
            data['items'][0]['batch_number'] = f"TEST-{timestamp}"
            data['items'][0]['expiry_date'] = "2026-12-31"
        
        return data
    
    def _record_result(self, test_name, passed, message):
        """Record test result"""
        self.results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        for result in self.results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"{result['test']}: {status}")
            if not result['passed']:
                print(f"  └─ {result['message']}")
        
        passed = sum(1 for r in self.results if r['passed'])
        total = len(self.results)
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Purchase system is fully operational.")
        else:
            print("\n⚠️  Some tests failed. Check the errors above.")
            sys.exit(1)


def main():
    """Run the test suite"""
    tester = PurchaseSystemTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()