"""
Fix missing invoices table - Run this if invoice_items and invoice_payments exist but invoices doesn't
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

def create_invoices_table_only(db: Session):
    """Create only the invoices table (when other billing tables already exist)"""
    try:
        # Create invoices table
        create_invoices_sql = text("""
            CREATE TABLE IF NOT EXISTS invoices (
                invoice_id SERIAL PRIMARY KEY,
                
                -- Reference to order
                order_id INTEGER NOT NULL,
                invoice_number VARCHAR(50) UNIQUE NOT NULL,
                invoice_date DATE NOT NULL,
                
                -- Customer details (denormalized for invoice)
                customer_id INTEGER NOT NULL,
                customer_name VARCHAR(200) NOT NULL,
                customer_gstin VARCHAR(15),
                billing_address TEXT NOT NULL,
                shipping_address TEXT,
                
                -- Financial details
                subtotal_amount DECIMAL(12,2) NOT NULL,
                discount_amount DECIMAL(10,2) DEFAULT 0,
                taxable_amount DECIMAL(12,2) NOT NULL,
                cgst_amount DECIMAL(10,2) DEFAULT 0,
                sgst_amount DECIMAL(10,2) DEFAULT 0,
                igst_amount DECIMAL(10,2) DEFAULT 0,
                total_tax_amount DECIMAL(10,2) NOT NULL,
                round_off_amount DECIMAL(5,2) DEFAULT 0,
                total_amount DECIMAL(12,2) NOT NULL,
                
                -- Payment details
                payment_status VARCHAR(20) DEFAULT 'unpaid',
                paid_amount DECIMAL(12,2) DEFAULT 0,
                payment_date TIMESTAMP,
                payment_method VARCHAR(50),
                
                -- Metadata
                invoice_type VARCHAR(20) DEFAULT 'tax_invoice',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                org_id UUID NOT NULL,
                
                -- Constraints
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                CHECK (payment_status IN ('unpaid', 'partially_paid', 'paid', 'overdue'))
            )
        """)
        
        db.execute(create_invoices_sql)
        db.commit()
        logger.info("✅ Created invoices table")
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_invoices_order_id ON invoices(order_id)",
            "CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_invoices_invoice_date ON invoices(invoice_date)",
            "CREATE INDEX IF NOT EXISTS idx_invoices_payment_status ON invoices(payment_status)",
            "CREATE INDEX IF NOT EXISTS idx_invoices_org_id ON invoices(org_id)"
        ]
        
        for index_sql in indexes:
            db.execute(text(index_sql))
            db.commit()
        
        logger.info("✅ Created indexes for invoices table")
        
        return {
            "success": True,
            "message": "Successfully created invoices table",
            "tables_created": ["invoices"]
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create invoices table: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to create invoices table: {str(e)}",
            "tables_created": []
        }

# SQL for manual execution in Supabase
MANUAL_SQL = """
-- Create the missing invoices table
CREATE TABLE invoices (
    invoice_id SERIAL PRIMARY KEY,
    
    -- Reference to order
    order_id INTEGER NOT NULL,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    invoice_date DATE NOT NULL,
    
    -- Customer details (denormalized for invoice)
    customer_id INTEGER NOT NULL,
    customer_name VARCHAR(200) NOT NULL,
    customer_gstin VARCHAR(15),
    billing_address TEXT NOT NULL,
    shipping_address TEXT,
    
    -- Financial details
    subtotal_amount DECIMAL(12,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    taxable_amount DECIMAL(12,2) NOT NULL,
    cgst_amount DECIMAL(10,2) DEFAULT 0,
    sgst_amount DECIMAL(10,2) DEFAULT 0,
    igst_amount DECIMAL(10,2) DEFAULT 0,
    total_tax_amount DECIMAL(10,2) NOT NULL,
    round_off_amount DECIMAL(5,2) DEFAULT 0,
    total_amount DECIMAL(12,2) NOT NULL,
    
    -- Payment details
    payment_status VARCHAR(20) DEFAULT 'unpaid',
    paid_amount DECIMAL(12,2) DEFAULT 0,
    payment_date TIMESTAMP,
    payment_method VARCHAR(50),
    
    -- Metadata
    invoice_type VARCHAR(20) DEFAULT 'tax_invoice',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    org_id UUID NOT NULL,
    
    -- Constraints
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    CHECK (payment_status IN ('unpaid', 'partially_paid', 'paid', 'overdue'))
);

-- Create indexes
CREATE INDEX idx_invoices_order_id ON invoices(order_id);
CREATE INDEX idx_invoices_customer_id ON invoices(customer_id);
CREATE INDEX idx_invoices_invoice_date ON invoices(invoice_date);
CREATE INDEX idx_invoices_payment_status ON invoices(payment_status);
CREATE INDEX idx_invoices_org_id ON invoices(org_id);

-- Grant permissions (adjust as needed for your setup)
GRANT ALL ON invoices TO authenticated;
GRANT USAGE ON SEQUENCE invoices_invoice_id_seq TO authenticated;
"""