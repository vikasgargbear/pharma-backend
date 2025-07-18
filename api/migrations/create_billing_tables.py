"""
Migration to create billing tables for invoice generation and payments
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


def create_billing_tables(db: Session) -> dict:
    """Create invoices, invoice_items, and invoice_payments tables"""
    
    results = {
        "success": False,
        "message": "",
        "tables_created": []
    }
    
    try:
        # Drop existing simple invoices table if it exists
        logger.info("Dropping existing invoices table if exists...")
        db.execute(text("DROP TABLE IF EXISTS invoices CASCADE"))
        db.commit()
        
        # Create invoices table
        logger.info("Creating invoices table...")
        db.execute(text("""
            CREATE TABLE invoices (
                invoice_id SERIAL PRIMARY KEY,
                org_id UUID NOT NULL,
                invoice_number VARCHAR(50) NOT NULL,
                order_id INTEGER NOT NULL,
                invoice_date DATE NOT NULL,
                due_date DATE,
                
                -- Customer details (captured at invoice time)
                customer_id INTEGER NOT NULL,
                customer_name VARCHAR(200) NOT NULL,
                customer_gstin VARCHAR(20),
                
                -- Billing address
                billing_name VARCHAR(200) NOT NULL,
                billing_address VARCHAR(500) NOT NULL,
                billing_city VARCHAR(100) NOT NULL,
                billing_state VARCHAR(100) NOT NULL,
                billing_pincode VARCHAR(10) NOT NULL,
                billing_phone VARCHAR(15),
                
                -- Shipping address
                shipping_name VARCHAR(200),
                shipping_address VARCHAR(500),
                shipping_city VARCHAR(100),
                shipping_state VARCHAR(100),
                shipping_pincode VARCHAR(10),
                
                -- GST details
                gst_type VARCHAR(20) NOT NULL, -- cgst_sgst or igst
                place_of_supply VARCHAR(2) NOT NULL, -- State code
                is_reverse_charge BOOLEAN DEFAULT FALSE,
                
                -- Amounts
                subtotal_amount DECIMAL(12,2) NOT NULL,
                discount_amount DECIMAL(12,2) DEFAULT 0,
                taxable_amount DECIMAL(12,2) NOT NULL,
                cgst_amount DECIMAL(12,2) DEFAULT 0,
                sgst_amount DECIMAL(12,2) DEFAULT 0,
                igst_amount DECIMAL(12,2) DEFAULT 0,
                total_tax_amount DECIMAL(12,2) NOT NULL,
                round_off_amount DECIMAL(5,2) DEFAULT 0,
                total_amount DECIMAL(12,2) NOT NULL,
                
                -- Payment tracking
                invoice_status VARCHAR(20) NOT NULL DEFAULT 'draft',
                paid_amount DECIMAL(12,2) DEFAULT 0,
                
                -- E-Invoice details (for future use)
                irn VARCHAR(100),
                ack_number VARCHAR(50),
                ack_date TIMESTAMP,
                qr_code TEXT,
                
                -- Additional info
                payment_terms VARCHAR(100),
                notes TEXT,
                terms_conditions TEXT,
                
                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Constraints
                UNIQUE(org_id, invoice_number),
                FOREIGN KEY (org_id) REFERENCES organizations(org_id),
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        """))
        results["tables_created"].append("invoices")
        
        # Create invoice_items table
        logger.info("Creating invoice_items table...")
        db.execute(text("""
            CREATE TABLE invoice_items (
                item_id SERIAL PRIMARY KEY,
                invoice_id INTEGER NOT NULL,
                
                -- Product details
                product_id INTEGER NOT NULL,
                product_name VARCHAR(200) NOT NULL,
                hsn_code VARCHAR(10),
                
                -- Batch details
                batch_id INTEGER,
                batch_number VARCHAR(50),
                
                -- Quantities and pricing
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                mrp DECIMAL(10,2),
                
                -- Discounts
                discount_percent DECIMAL(5,2) DEFAULT 0,
                discount_amount DECIMAL(10,2) DEFAULT 0,
                
                -- Tax
                gst_percent DECIMAL(5,2) DEFAULT 0,
                cgst_amount DECIMAL(10,2) DEFAULT 0,
                sgst_amount DECIMAL(10,2) DEFAULT 0,
                igst_amount DECIMAL(10,2) DEFAULT 0,
                
                -- Totals
                taxable_amount DECIMAL(12,2) NOT NULL,
                total_amount DECIMAL(12,2) NOT NULL,
                
                -- Constraints
                FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(product_id),
                FOREIGN KEY (batch_id) REFERENCES batches(batch_id)
            )
        """))
        results["tables_created"].append("invoice_items")
        
        # Create invoice_payments table
        logger.info("Creating invoice_payments table...")
        db.execute(text("""
            CREATE TABLE invoice_payments (
                payment_id SERIAL PRIMARY KEY,
                invoice_id INTEGER NOT NULL,
                
                -- Payment details
                payment_date DATE NOT NULL,
                amount DECIMAL(12,2) NOT NULL,
                payment_mode VARCHAR(20) NOT NULL, -- cash, card, bank_transfer, upi, cheque
                
                -- Payment reference details
                transaction_reference VARCHAR(100),
                bank_name VARCHAR(100),
                cheque_number VARCHAR(50),
                cheque_date DATE,
                
                -- Additional info
                notes TEXT,
                
                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Constraints
                FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
            )
        """))
        results["tables_created"].append("invoice_payments")
        
        # Create indexes for better performance
        logger.info("Creating indexes...")
        indexes = [
            ("idx_invoices_org_id", "invoices(org_id)"),
            ("idx_invoices_invoice_number", "invoices(invoice_number)"),
            ("idx_invoices_order_id", "invoices(order_id)"),
            ("idx_invoices_customer_id", "invoices(customer_id)"),
            ("idx_invoices_invoice_date", "invoices(invoice_date)"),
            ("idx_invoices_due_date", "invoices(due_date)"),
            ("idx_invoices_invoice_status", "invoices(invoice_status)"),
            ("idx_invoice_items_invoice_id", "invoice_items(invoice_id)"),
            ("idx_invoice_items_product_id", "invoice_items(product_id)"),
            ("idx_invoice_payments_invoice_id", "invoice_payments(invoice_id)"),
            ("idx_invoice_payments_payment_date", "invoice_payments(payment_date)")
        ]
        
        for index_name, index_def in indexes:
            try:
                db.execute(text(f"CREATE INDEX {index_name} ON {index_def}"))
                logger.info(f"Created index: {index_name}")
            except Exception as e:
                logger.warning(f"Could not create index {index_name}: {str(e)}")
        
        # Create triggers for updated_at
        logger.info("Creating triggers...")
        db.execute(text("""
            DROP TRIGGER IF EXISTS update_invoices_updated_at ON invoices;
            CREATE TRIGGER update_invoices_updated_at
            BEFORE UPDATE ON invoices
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """))
        
        # Add missing columns to orders table if needed
        logger.info("Checking orders table for missing columns...")
        try:
            # Check if paid_amount exists in orders
            result = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'orders' AND column_name = 'paid_amount'
            """)).scalar()
            
            if not result:
                logger.info("Adding paid_amount column to orders table...")
                db.execute(text("""
                    ALTER TABLE orders 
                    ADD COLUMN paid_amount DECIMAL(12,2) DEFAULT 0
                """))
                logger.info("Added paid_amount column to orders table")
        except Exception as e:
            logger.warning(f"Could not check/add paid_amount column: {str(e)}")
        
        # Commit all changes
        db.commit()
        
        results["success"] = True
        results["message"] = f"Successfully created billing tables: {', '.join(results['tables_created'])}"
        logger.info(results["message"])
        
    except Exception as e:
        db.rollback()
        results["success"] = False
        results["message"] = f"Failed to create billing tables: {str(e)}"
        logger.error(results["message"])
    
    return results


def drop_billing_tables(db: Session) -> dict:
    """Drop billing tables (for rollback)"""
    
    results = {
        "success": False,
        "message": "",
        "tables_dropped": []
    }
    
    try:
        tables = ["invoice_payments", "invoice_items", "invoices"]
        
        for table in tables:
            try:
                db.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                results["tables_dropped"].append(table)
                logger.info(f"Dropped table: {table}")
            except Exception as e:
                logger.warning(f"Could not drop table {table}: {str(e)}")
        
        # Remove paid_amount from orders if it exists
        try:
            db.execute(text("""
                ALTER TABLE orders 
                DROP COLUMN IF EXISTS paid_amount
            """))
            logger.info("Removed paid_amount column from orders table")
        except Exception as e:
            logger.warning(f"Could not remove paid_amount column: {str(e)}")
        
        db.commit()
        
        results["success"] = True
        results["message"] = f"Successfully dropped tables: {', '.join(results['tables_dropped'])}"
        
    except Exception as e:
        db.rollback()
        results["success"] = False
        results["message"] = f"Failed to drop billing tables: {str(e)}"
        logger.error(results["message"])
    
    return results