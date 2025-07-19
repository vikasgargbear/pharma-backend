#!/usr/bin/env python3
"""
Demo script to test the AASO Pharma ERP system end-to-end
This demonstrates the complete workflow from customer creation to invoice generation
"""
import requests
import json
from datetime import datetime, date
import sys
import time

# Configuration
BASE_URL = "https://pharma-backend-production-0c09.up.railway.app"
# BASE_URL = "http://localhost:8000"  # Uncomment for local testing

# Default org_id used in the system
ORG_ID = "12de5e22-eee7-4d25-b3a7-d16d01c6170f"

# ANSI color codes for better output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_step(step_num, title):
    """Print a formatted step header"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Step {step_num}: {title}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")


def print_success(message):
    """Print success message in green"""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message):
    """Print error message in red"""
    print(f"{RED}✗ {message}{RESET}")


def print_info(key, value):
    """Print info in yellow"""
    print(f"{YELLOW}{key}:{RESET} {value}")


def check_health():
    """Check if the API is healthy"""
    print_step(1, "Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print_success("API is healthy")
            return True
        else:
            print_error(f"API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot connect to API: {str(e)}")
        return False


def create_customer():
    """Create a demo customer"""
    print_step(2, "Create Customer")
    
    customer_data = {
        "org_id": ORG_ID,
        "customer_name": "Demo Pharmacy " + datetime.now().strftime("%Y%m%d%H%M%S"),
        "customer_code": "DEMO" + datetime.now().strftime("%H%M%S"),
        "customer_type": "pharmacy",
        "contact_person": "John Doe",
        "phone": "9876543210",
        "email": "demo@pharmacy.com",
        "address_line1": "123 Main Street",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400001",
        "gstin": "27AABCU9603R1ZM",  # Maharashtra GSTIN
        "credit_limit": 50000,
        "credit_days": 30,
        "discount_percent": 5
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/customers/",
            json=customer_data
        )
        
        if response.status_code == 200:
            customer = response.json()
            print_success(f"Customer created successfully")
            print_info("Customer ID", customer['customer_id'])
            print_info("Customer Name", customer['customer_name'])
            print_info("GSTIN", customer['gstin'])
            return customer
        else:
            print_error(f"Failed to create customer: {response.status_code}")
            print(response.json())
            return None
    except Exception as e:
        print_error(f"Error creating customer: {str(e)}")
        return None


def check_products():
    """Check available products"""
    print_step(3, "Check Available Products")
    
    try:
        response = requests.get(f"{BASE_URL}/products/")
        
        if response.status_code == 200:
            products = response.json()
            if products:
                print_success(f"Found {len(products)} products")
                # Display first 3 products
                for i, product in enumerate(products[:3]):
                    print(f"\n  Product {i+1}:")
                    print_info("    ID", product['product_id'])
                    print_info("    Name", product['product_name'])
                    print_info("    MRP", f"₹{product['mrp']}")
                    print_info("    GST Rate", f"{product.get('gst_percent', 0)}%")
                return products
            else:
                print_error("No products found. Please add products first.")
                return None
        else:
            print_error(f"Failed to fetch products: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Error fetching products: {str(e)}")
        return None


def check_inventory(product_id):
    """Check inventory for a product"""
    print_step(4, "Check Inventory")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/inventory/stock/current")
        
        if response.status_code == 200:
            data = response.json()
            stock_items = data.get('stocks', []) if isinstance(data, dict) else data
            # Find our product
            product_stock = [s for s in stock_items if s['product_id'] == product_id]
            
            if product_stock:
                stock = product_stock[0]
                print_success(f"Product has inventory")
                print_info("Available Quantity", stock.get('available_quantity', 0))
                print_info("Total Quantity", stock.get('total_quantity', 0))
                # Check if product has available stock
                if stock.get('available_quantity', 0) > 0:
                    return True
                else:
                    print_error("Product has no available quantity")
                    return False
            else:
                print_error("Product has no inventory. Please add stock first.")
                return False
        else:
            print_error(f"Failed to check inventory: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error checking inventory: {str(e)}")
        return False


def create_order(customer, products):
    """Create a demo order"""
    print_step(5, "Create Order")
    
    if not products:
        print_error("No products available")
        return None
    
    # Select first product with inventory
    selected_product = None
    for product in products[:5]:  # Check first 5 products
        if check_inventory(product['product_id']):
            selected_product = product
            break
    
    if not selected_product:
        print_error("No products with available inventory found")
        return None
    
    # Calculate tax for the item
    unit_price = float(selected_product['mrp']) * 0.8  # 20% discount
    quantity = 10
    discount_percent = 5
    tax_percent = selected_product.get('gst_percent', 12)
    
    # Calculate line total and tax
    line_total = unit_price * quantity
    discount_amount = line_total * discount_percent / 100
    taxable_amount = line_total - discount_amount
    tax_amount = taxable_amount * tax_percent / 100
    
    order_data = {
        "org_id": ORG_ID,
        "customer_id": customer['customer_id'],
        "order_date": date.today().isoformat(),
        "delivery_date": date.today().isoformat(),
        "order_type": "sales",  # Changed from "regular" to "sales"
        "payment_mode": "credit",
        "order_source": "direct",
        "billing_name": customer['customer_name'],
        "billing_address": customer['address_line1'],
        "shipping_name": customer['customer_name'],
        "shipping_address": customer['address_line1'],
        "notes": "Demo order for testing",
        "items": [
            {
                "product_id": selected_product['product_id'],
                "quantity": quantity,
                "unit_price": unit_price,
                "selling_price": unit_price,  # Add selling_price field
                "discount_percent": discount_percent,
                "tax_percent": tax_percent,
                "tax_amount": tax_amount
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/orders/",
            json=order_data
        )
        
        if response.status_code == 200:
            order = response.json()
            print_success(f"Order created successfully")
            print_info("Order ID", order['order_id'])
            print_info("Order Number", order['order_number'])
            print_info("Total Amount", f"₹{order['total_amount']}")
            print_info("Status", order['order_status'])
            return order
        else:
            print_error(f"Failed to create order: {response.status_code}")
            print(response.json())
            return None
    except Exception as e:
        print_error(f"Error creating order: {str(e)}")
        return None


def generate_invoice(order):
    """Generate invoice for the order"""
    print_step(6, "Generate Invoice")
    
    invoice_data = {
        "order_id": order['order_id'],
        "invoice_date": date.today().isoformat(),
        "payment_terms_days": 30,
        "notes": "Thank you for your business!"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/billing/invoices",
            json=invoice_data
        )
        
        if response.status_code == 200:
            invoice = response.json()
            print_success(f"Invoice generated successfully")
            print_info("Invoice ID", invoice['invoice_id'])
            print_info("Invoice Number", invoice['invoice_number'])
            print_info("Total Amount", f"₹{invoice['total_amount']}")
            print_info("Due Date", invoice['due_date'])
            print_info("GST Type", invoice['gst_type'])
            return invoice
        else:
            print_error(f"Failed to generate invoice: {response.status_code}")
            print(response.json())
            return None
    except Exception as e:
        print_error(f"Error generating invoice: {str(e)}")
        return None


def check_dashboards():
    """Check various dashboard endpoints"""
    print_step(7, "Check Dashboards")
    
    dashboards = [
        ("Order Dashboard", f"{BASE_URL}/api/v1/orders/dashboard/stats"),
        ("Inventory Dashboard", f"{BASE_URL}/api/v1/inventory/dashboard"),
        ("Billing Summary", f"{BASE_URL}/billing/summary")
    ]
    
    for name, url in dashboards:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print_success(f"{name} is working")
                data = response.json()
                # Print first few keys
                for key in list(data.keys())[:3]:
                    if isinstance(data[key], (int, float, str)):
                        print(f"  - {key}: {data[key]}")
            else:
                print_error(f"{name} failed: {response.status_code}")
        except Exception as e:
            print_error(f"{name} error: {str(e)}")


def main():
    """Run the complete demo"""
    print(f"\n{GREEN}AASO Pharma ERP Demo Script{RESET}")
    print(f"Testing against: {YELLOW}{BASE_URL}{RESET}")
    print(f"Organization ID: {YELLOW}{ORG_ID}{RESET}")
    
    # Step 1: Health check
    if not check_health():
        print_error("API is not accessible. Please check the URL and try again.")
        sys.exit(1)
    
    # Step 2: Create customer
    customer = create_customer()
    if not customer:
        print_error("Cannot proceed without a customer")
        sys.exit(1)
    
    time.sleep(1)  # Small delay
    
    # Step 3: Check products
    products = check_products()
    
    time.sleep(1)
    
    # Step 4 & 5: Create order (includes inventory check)
    order = create_order(customer, products)
    if not order:
        print_error("Cannot proceed without an order")
        print_info("Tip", "Make sure you have products with available inventory")
        sys.exit(1)
    
    time.sleep(1)
    
    # Step 6: Generate invoice
    invoice = generate_invoice(order)
    
    time.sleep(1)
    
    # Step 7: Check dashboards
    check_dashboards()
    
    # Summary
    print(f"\n{GREEN}{'='*60}{RESET}")
    print(f"{GREEN}Demo Completed Successfully!{RESET}")
    print(f"{GREEN}{'='*60}{RESET}")
    
    if invoice:
        print(f"\nYou have successfully:")
        print(f"1. Created a customer: {customer['customer_name']}")
        print(f"2. Created order: {order['order_number']}")
        print(f"3. Generated invoice: {invoice['invoice_number']}")
        print(f"\nNext steps:")
        print(f"- Record a payment: POST /billing/payments")
        print(f"- Check GSTR-1: GET /billing/gst/gstr1")
        print(f"- View invoice: GET /billing/invoices/{invoice['invoice_id']}")


if __name__ == "__main__":
    main()