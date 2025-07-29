#!/usr/bin/env python3
"""
Receivables Data Seeding Script
Seeds the database with sample financial data to demonstrate the collection center functionality
"""

import os
import sys
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database.connection import get_db_session

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ORG_ID = '12de5e22-eee7-4d25-b3a7-d16d01c6170f'

def seed_customers_and_ledgers():
    """Seed customers and their corresponding ledgers"""
    db = next(get_db_session())
    
    customers_data = [
        {
            'name': 'Apollo Pharmacy',
            'phone': '+91 9876543210',
            'email': 'accounts@apollo.com',
            'address': 'Shop 15, Andheri West, Mumbai',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'credit_limit': 200000,
            'credit_days': 30
        },
        {
            'name': 'MedPlus Health Services',
            'phone': '+91 9876543211', 
            'email': 'finance@medplusmart.com',
            'address': 'Plot 42, Banjara Hills, Hyderabad',
            'city': 'Hyderabad',
            'state': 'Telangana',
            'credit_limit': 150000,
            'credit_days': 45
        },
        {
            'name': 'Wellness Forever',
            'phone': '+91 9876543212',
            'email': 'accounts@wellnessforever.com', 
            'address': 'FC Road, Pune',
            'city': 'Pune',
            'state': 'Maharashtra',
            'credit_limit': 250000,
            'credit_days': 30
        },
        {
            'name': '1mg Healthcare',
            'phone': '+91 9876543213',
            'email': 'collections@1mg.com',
            'address': 'Sector 44, Gurgaon',
            'city': 'Gurgaon', 
            'state': 'Haryana',
            'credit_limit': 300000,
            'credit_days': 60
        },
        {
            'name': 'PharmEasy Retail',
            'phone': '+91 9876543214',
            'email': 'accounts@pharmeasy.in',
            'address': 'Lower Parel, Mumbai',
            'city': 'Mumbai',
            'state': 'Maharashtra', 
            'credit_limit': 500000,
            'credit_days': 45
        }
    ]
    
    try:
        for customer_data in customers_data:
            # Insert customer
            customer_query = text("""
                INSERT INTO customers (
                    org_id, customer_name, phone, email, address_line1, 
                    city, state, credit_limit, credit_days, is_active
                ) VALUES (
                    :org_id, :name, :phone, :email, :address,
                    :city, :state, :credit_limit, :credit_days, true
                )
                ON CONFLICT (org_id, customer_name) DO UPDATE SET
                    phone = EXCLUDED.phone,
                    email = EXCLUDED.email
                RETURNING customer_id
            """)
            
            result = db.execute(customer_query, {
                'org_id': ORG_ID,
                'name': customer_data['name'],
                'phone': customer_data['phone'],
                'email': customer_data['email'],
                'address': customer_data['address'],
                'city': customer_data['city'],
                'state': customer_data['state'],
                'credit_limit': customer_data['credit_limit'],
                'credit_days': customer_data['credit_days']
            })
            
            customer_id = result.fetchone()[0]
            logger.info(f"Created/updated customer: {customer_data['name']} (ID: {customer_id})")
            
        db.commit()
        logger.info("✅ Customers seeded successfully")
        
    except Exception as e:
        logger.error(f"❌ Error seeding customers: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def seed_bill_details():
    """Seed bill_details table with outstanding amounts"""
    db = next(get_db_session())
    
    try:
        # Get customer IDs
        customers_query = text("""
            SELECT customer_id, customer_name, credit_days 
            FROM customers 
            WHERE org_id = :org_id AND is_active = true
        """)
        customers = db.execute(customers_query, {'org_id': ORG_ID}).fetchall()
        
        if not customers:
            logger.error("No customers found. Please run seed_customers_and_ledgers first.")
            return
            
        bill_templates = [
            {'amount': 125000, 'days_overdue': 35},
            {'amount': 85000, 'days_overdue': 22}, 
            {'amount': 195000, 'days_overdue': 78},
            {'amount': 67000, 'days_overdue': 12},
            {'amount': 156000, 'days_overdue': 45},
            {'amount': 89000, 'days_overdue': 5},
            {'amount': 234000, 'days_overdue': 92},
            {'amount': 45000, 'days_overdue': 0}
        ]
        
        for customer in customers:
            customer_id = customer.customer_id
            customer_name = customer.customer_name
            credit_days = customer.credit_days or 30
            
            # Create 1-3 bills per customer
            num_bills = random.randint(1, 3)
            
            for i in range(num_bills):
                bill_template = random.choice(bill_templates)
                bill_amount = bill_template['amount'] + random.randint(-20000, 50000)
                days_overdue = bill_template['days_overdue'] + random.randint(-5, 15)
                days_overdue = max(0, days_overdue)  # Don't allow negative overdue
                
                # Calculate dates
                bill_date = date.today() - timedelta(days=days_overdue + credit_days + random.randint(0, 10))
                due_date = bill_date + timedelta(days=credit_days)
                
                bill_number = f"INV-{customer_id}-{i+1:03d}"
                
                # Random payment (0-80% of bill amount)
                paid_amount = random.randint(0, int(bill_amount * 0.8)) if random.random() > 0.3 else 0
                outstanding_amount = bill_amount - paid_amount
                
                # Skip if no outstanding amount
                if outstanding_amount <= 0:
                    continue
                    
                status = 'Outstanding' if paid_amount == 0 else 'Partial'
                
                bill_query = text("""
                    INSERT INTO bill_details (
                        org_id, ledger_id, bill_number, bill_date, bill_amount,
                        paid_amount, outstanding_amount, due_date, status
                    ) VALUES (
                        :org_id, :ledger_id, :bill_number, :bill_date, :bill_amount,
                        :paid_amount, :outstanding_amount, :due_date, :status
                    )
                    ON CONFLICT (org_id, bill_number) DO UPDATE SET
                        outstanding_amount = EXCLUDED.outstanding_amount,
                        status = EXCLUDED.status
                """)
                
                db.execute(bill_query, {
                    'org_id': ORG_ID,
                    'ledger_id': customer_id,  # Using customer_id as ledger_id for simplicity
                    'bill_number': bill_number,
                    'bill_date': bill_date,
                    'bill_amount': bill_amount,
                    'paid_amount': paid_amount, 
                    'outstanding_amount': outstanding_amount,
                    'due_date': due_date,
                    'status': status
                })
                
                logger.info(f"Created bill {bill_number} for {customer_name}: ₹{outstanding_amount:,.0f} outstanding")
        
        db.commit()
        logger.info("✅ Bill details seeded successfully")
        
    except Exception as e:
        logger.error(f"❌ Error seeding bill details: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def seed_payments():
    """Seed payments table with recent payment history"""
    db = next(get_db_session())
    
    try:
        # Get customers
        customers_query = text("""
            SELECT customer_id, customer_name 
            FROM customers 
            WHERE org_id = :org_id AND is_active = true
        """)
        customers = db.execute(customers_query, {'org_id': ORG_ID}).fetchall()
        
        payment_methods = ['cash', 'cheque', 'neft', 'upi']
        
        for customer in customers:
            customer_id = customer.customer_id
            customer_name = customer.customer_name
            
            # Create 2-5 historical payments
            num_payments = random.randint(2, 5)
            
            for i in range(num_payments):
                payment_date = date.today() - timedelta(days=random.randint(1, 90))
                amount = random.randint(25000, 150000)
                method = random.choice(payment_methods)
                
                # Generate reference based on method
                reference = ""
                if method == 'cheque':
                    reference = f"CHQ{random.randint(100000, 999999)}"
                elif method == 'neft':
                    reference = f"NEFT{random.randint(1000000000, 9999999999)}"
                elif method == 'upi':
                    reference = f"UPI{random.randint(100000000000, 999999999999)}"
                
                payment_query = text("""
                    INSERT INTO payments (
                        org_id, customer_id, amount, payment_method, payment_date,
                        reference_number, status, created_at
                    ) VALUES (
                        :org_id, :customer_id, :amount, :method, :payment_date,
                        :reference, 'confirmed', :created_at
                    )
                """)
                
                db.execute(payment_query, {
                    'org_id': ORG_ID,
                    'customer_id': customer_id,
                    'amount': amount,
                    'method': method,
                    'payment_date': payment_date,
                    'reference': reference,
                    'created_at': datetime.combine(payment_date, datetime.min.time())
                })
                
                logger.info(f"Created payment for {customer_name}: ₹{amount:,.0f} via {method}")
        
        db.commit()
        logger.info("✅ Payments seeded successfully")
        
    except Exception as e:
        logger.error(f"❌ Error seeding payments: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_data():
    """Verify the seeded data"""
    db = next(get_db_session())
    
    try:
        # Check customers
        customers_count = db.execute(text("""
            SELECT COUNT(*) FROM customers WHERE org_id = :org_id
        """), {'org_id': ORG_ID}).scalar()
        
        # Check bills
        bills_count = db.execute(text("""
            SELECT COUNT(*) FROM bill_details WHERE org_id = :org_id
        """), {'org_id': ORG_ID}).scalar()
        
        # Check total outstanding
        total_outstanding = db.execute(text("""
            SELECT COALESCE(SUM(outstanding_amount), 0) 
            FROM bill_details WHERE org_id = :org_id
        """), {'org_id': ORG_ID}).scalar()
        
        # Check payments
        payments_count = db.execute(text("""
            SELECT COUNT(*) FROM payments WHERE org_id = :org_id
        """), {'org_id': ORG_ID}).scalar()
        
        total_payments = db.execute(text("""
            SELECT COALESCE(SUM(amount), 0) 
            FROM payments WHERE org_id = :org_id
        """), {'org_id': ORG_ID}).scalar()
        
        logger.info("📊 DATA VERIFICATION SUMMARY:")
        logger.info(f"   • Customers: {customers_count}")
        logger.info(f"   • Outstanding Bills: {bills_count}")
        logger.info(f"   • Total Outstanding: ₹{total_outstanding:,.0f}")
        logger.info(f"   • Payment Records: {payments_count}")
        logger.info(f"   • Total Payments: ₹{total_payments:,.0f}")
        
    except Exception as e:
        logger.error(f"❌ Error verifying data: {e}")
    finally:
        db.close()


def main():
    """Main seeding function"""
    logger.info("🌱 Starting Receivables Data Seeding...")
    logger.info(f"   Organization ID: {ORG_ID}")
    
    try:
        # Step 1: Seed customers and ledgers
        logger.info("\n1️⃣ Seeding customers and ledgers...")
        seed_customers_and_ledgers()
        
        # Step 2: Seed bill details (outstanding amounts)
        logger.info("\n2️⃣ Seeding bill details...")
        seed_bill_details()
        
        # Step 3: Seed payment history
        logger.info("\n3️⃣ Seeding payment history...")
        seed_payments()
        
        # Step 4: Verify data
        logger.info("\n4️⃣ Verifying seeded data...")
        verify_data()
        
        logger.info("\n🎉 Data seeding completed successfully!")
        logger.info("\n🔗 You can now test the Receivables Hub with real data:")
        logger.info("   • Navigate to /receivables/hub")
        logger.info("   • Click on 'Smart Dashboard' to see aging analysis")
        logger.info("   • Try the WhatsApp reminder functionality")
        logger.info("   • Check the analytics and field agent features")
        
    except Exception as e:
        logger.error(f"💥 Data seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()