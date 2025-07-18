-- ============================================
-- 12. Complete Invoice Module Migrations
-- ============================================
-- This file consolidates all invoice-related migrations including fixes
-- for existing tables and missing columns
-- Created: 2025-07-18

-- ============================================
-- 12.1 Fix invoices table columns
-- ============================================
DO $$ 
BEGIN
    -- Only proceed if invoices table exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'invoices') THEN
        -- Add updated_at if missing (CRITICAL for API)
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoices' AND column_name='updated_at') THEN
            ALTER TABLE invoices ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
            RAISE NOTICE 'Added updated_at to invoices table';
        END IF;
        
        -- Add cancellation tracking columns
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoices' AND column_name='cancelled_at') THEN
            ALTER TABLE invoices ADD COLUMN cancelled_at TIMESTAMP;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoices' AND column_name='cancellation_reason') THEN
            ALTER TABLE invoices ADD COLUMN cancellation_reason TEXT;
        END IF;
        
        -- Add due date for payment tracking
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoices' AND column_name='due_date') THEN
            ALTER TABLE invoices ADD COLUMN due_date DATE;
        END IF;
        
        -- Add PDF storage fields
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoices' AND column_name='pdf_url') THEN
            ALTER TABLE invoices ADD COLUMN pdf_url TEXT;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoices' AND column_name='pdf_generated_at') THEN
            ALTER TABLE invoices ADD COLUMN pdf_generated_at TIMESTAMP;
        END IF;
    END IF;
END $$;

-- ============================================
-- 12.2 Create/Update invoice_items table
-- ============================================
CREATE TABLE IF NOT EXISTS invoice_items (
    invoice_item_id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    product_code VARCHAR(50),
    hsn_code VARCHAR(20),
    batch_number VARCHAR(50),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    tax_percent DECIMAL(5,2) DEFAULT 0,
    cgst_amount DECIMAL(10,2) DEFAULT 0,
    sgst_amount DECIMAL(10,2) DEFAULT 0,
    igst_amount DECIMAL(10,2) DEFAULT 0,
    line_total DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 12.3 Fix invoice_payments table
-- ============================================
DO $$
BEGIN
    -- Check if table exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'invoice_payments') THEN
        
        -- Add all missing columns with proper defaults
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoice_payments' AND column_name='payment_amount') THEN
            ALTER TABLE invoice_payments ADD COLUMN payment_amount DECIMAL(12,2) NOT NULL DEFAULT 0;
            RAISE NOTICE 'Added payment_amount column';
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoice_payments' AND column_name='payment_mode') THEN
            ALTER TABLE invoice_payments ADD COLUMN payment_mode VARCHAR(20) NOT NULL DEFAULT 'cash';
            RAISE NOTICE 'Added payment_mode column';
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoice_payments' AND column_name='payment_date') THEN
            ALTER TABLE invoice_payments ADD COLUMN payment_date DATE NOT NULL DEFAULT CURRENT_DATE;
            RAISE NOTICE 'Added payment_date column';
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoice_payments' AND column_name='payment_reference') THEN
            ALTER TABLE invoice_payments ADD COLUMN payment_reference VARCHAR(50);
            -- Make it unique after adding
            UPDATE invoice_payments SET payment_reference = 'PAY-' || payment_id::text WHERE payment_reference IS NULL;
            ALTER TABLE invoice_payments ALTER COLUMN payment_reference SET NOT NULL;
            -- Add unique constraint if not exists
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'invoice_payments_payment_reference_key') THEN
                ALTER TABLE invoice_payments ADD CONSTRAINT invoice_payments_payment_reference_key UNIQUE (payment_reference);
            END IF;
            RAISE NOTICE 'Added payment_reference column';
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoice_payments' AND column_name='status') THEN
            ALTER TABLE invoice_payments ADD COLUMN status VARCHAR(20) DEFAULT 'completed';
            RAISE NOTICE 'Added status column';
        END IF;
        
        -- Add transaction details columns
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoice_payments' AND column_name='transaction_reference') THEN
            ALTER TABLE invoice_payments ADD COLUMN transaction_reference VARCHAR(100);
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoice_payments' AND column_name='bank_name') THEN
            ALTER TABLE invoice_payments ADD COLUMN bank_name VARCHAR(100);
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoice_payments' AND column_name='cheque_number') THEN
            ALTER TABLE invoice_payments ADD COLUMN cheque_number VARCHAR(50);
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoice_payments' AND column_name='cheque_date') THEN
            ALTER TABLE invoice_payments ADD COLUMN cheque_date DATE;
        END IF;
        
        -- Add metadata columns
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoice_payments' AND column_name='notes') THEN
            ALTER TABLE invoice_payments ADD COLUMN notes TEXT;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoice_payments' AND column_name='created_at') THEN
            ALTER TABLE invoice_payments ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoice_payments' AND column_name='updated_at') THEN
            ALTER TABLE invoice_payments ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoice_payments' AND column_name='created_by') THEN
            ALTER TABLE invoice_payments ADD COLUMN created_by INTEGER;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoice_payments' AND column_name='cancellation_reason') THEN
            ALTER TABLE invoice_payments ADD COLUMN cancellation_reason TEXT;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='invoice_payments' AND column_name='cancelled_at') THEN
            ALTER TABLE invoice_payments ADD COLUMN cancelled_at TIMESTAMP;
        END IF;
        
    ELSE
        -- Create the table if it doesn't exist
        RAISE NOTICE 'Creating invoice_payments table from scratch';
        CREATE TABLE invoice_payments (
            payment_id SERIAL PRIMARY KEY,
            payment_reference VARCHAR(50) UNIQUE NOT NULL,
            invoice_id INTEGER NOT NULL REFERENCES invoices(invoice_id),
            payment_date DATE NOT NULL,
            payment_mode VARCHAR(20) NOT NULL,
            payment_amount DECIMAL(12,2) NOT NULL,
            transaction_reference VARCHAR(100),
            bank_name VARCHAR(100),
            cheque_number VARCHAR(50),
            cheque_date DATE,
            status VARCHAR(20) DEFAULT 'completed',
            cancellation_reason TEXT,
            cancelled_at TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER
        );
    END IF;
END $$;

-- ============================================
-- 12.4 Add constraints to invoice_payments
-- ============================================
DO $$
BEGIN
    -- Add payment_mode constraint if not exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'invoice_payments_payment_mode_check'
    ) THEN
        ALTER TABLE invoice_payments 
        ADD CONSTRAINT invoice_payments_payment_mode_check 
        CHECK (payment_mode IN ('cash', 'cheque', 'online', 'card', 'upi', 'neft', 'rtgs'));
        RAISE NOTICE 'Added payment_mode check constraint';
    END IF;
    
    -- Add status constraint if not exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'invoice_payments_status_check'
    ) THEN
        ALTER TABLE invoice_payments 
        ADD CONSTRAINT invoice_payments_status_check 
        CHECK (status IN ('completed', 'pending', 'cancelled', 'bounced'));
        RAISE NOTICE 'Added status check constraint';
    END IF;
    
    -- Add cheque details constraint if not exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'check_cheque_details'
    ) THEN
        ALTER TABLE invoice_payments 
        ADD CONSTRAINT check_cheque_details 
        CHECK (
            (payment_mode != 'cheque') OR 
            (payment_mode = 'cheque' AND cheque_number IS NOT NULL AND cheque_date IS NOT NULL)
        );
        RAISE NOTICE 'Added cheque details check constraint';
    END IF;
END $$;

-- ============================================
-- 12.5 Add payment_status to orders
-- ============================================
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='orders' AND column_name='payment_status') THEN
        ALTER TABLE orders ADD COLUMN payment_status VARCHAR(20) DEFAULT 'unpaid';
        
        -- Add constraint only if it doesn't exist
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint 
            WHERE conname = 'orders_payment_status_check'
        ) THEN
            ALTER TABLE orders ADD CONSTRAINT orders_payment_status_check 
            CHECK (payment_status IN ('unpaid', 'partial', 'paid', 'overdue'));
        END IF;
    END IF;
END $$;

-- ============================================
-- 12.6 Create triggers for updated_at
-- ============================================

-- Invoices trigger
CREATE OR REPLACE FUNCTION update_invoices_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_invoices_updated_at_trigger ON invoices;
CREATE TRIGGER update_invoices_updated_at_trigger
BEFORE UPDATE ON invoices
FOR EACH ROW
EXECUTE FUNCTION update_invoices_updated_at();

-- Invoice items trigger
CREATE OR REPLACE FUNCTION update_invoice_items_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_invoice_items_updated_at_trigger ON invoice_items;
CREATE TRIGGER update_invoice_items_updated_at_trigger
BEFORE UPDATE ON invoice_items
FOR EACH ROW
EXECUTE FUNCTION update_invoice_items_updated_at();

-- Invoice payments trigger
CREATE OR REPLACE FUNCTION update_invoice_payments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_invoice_payments_updated_at_trigger ON invoice_payments;
CREATE TRIGGER update_invoice_payments_updated_at_trigger
BEFORE UPDATE ON invoice_payments
FOR EACH ROW
EXECUTE FUNCTION update_invoice_payments_updated_at();

-- ============================================
-- 12.7 Create indexes for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_order_id ON invoices(order_id);
CREATE INDEX IF NOT EXISTS idx_invoices_invoice_date ON invoices(invoice_date);
CREATE INDEX IF NOT EXISTS idx_invoices_payment_status ON invoices(payment_status);
CREATE INDEX IF NOT EXISTS idx_invoices_org_id ON invoices(org_id);

CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice_id ON invoice_items(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_items_product_id ON invoice_items(product_id);

CREATE INDEX IF NOT EXISTS idx_invoice_payments_invoice_id ON invoice_payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_payments_payment_date ON invoice_payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_invoice_payments_payment_mode ON invoice_payments(payment_mode);
CREATE INDEX IF NOT EXISTS idx_invoice_payments_status ON invoice_payments(status);

-- ============================================
-- 12.8 Update existing records
-- ============================================
UPDATE invoices 
SET updated_at = COALESCE(updated_at, created_at, CURRENT_TIMESTAMP)
WHERE updated_at IS NULL;

-- ============================================
-- 12.9 Create payment analytics view
-- ============================================
CREATE OR REPLACE VIEW payment_analytics AS
SELECT 
    DATE_TRUNC('month', ip.payment_date) as month,
    COUNT(DISTINCT ip.payment_id) as payment_count,
    COUNT(DISTINCT ip.invoice_id) as invoices_paid,
    SUM(ip.payment_amount) as total_collected,
    AVG(ip.payment_amount) as avg_payment,
    COUNT(DISTINCT CASE WHEN ip.payment_mode = 'cash' THEN ip.payment_id END) as cash_payments,
    COUNT(DISTINCT CASE WHEN ip.payment_mode = 'cheque' THEN ip.payment_id END) as cheque_payments,
    COUNT(DISTINCT CASE WHEN ip.payment_mode IN ('online', 'upi', 'neft', 'rtgs') THEN ip.payment_id END) as digital_payments
FROM invoice_payments ip
WHERE ip.status = 'completed'
GROUP BY DATE_TRUNC('month', ip.payment_date);

-- ============================================
-- 12.10 Final verification
-- ============================================
DO $$
DECLARE
    payments_cols integer;
    invoices_updated boolean;
    items_exists boolean;
BEGIN
    SELECT COUNT(*) INTO payments_cols
    FROM information_schema.columns 
    WHERE table_name = 'invoice_payments';
    
    SELECT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'invoices' AND column_name = 'updated_at'
    ) INTO invoices_updated;
    
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'invoice_items'
    ) INTO items_exists;
    
    RAISE NOTICE '';
    RAISE NOTICE '========== Invoice Module Migration Complete ==========';
    RAISE NOTICE 'invoice_payments table has % columns', payments_cols;
    RAISE NOTICE 'invoices table has updated_at column: %', invoices_updated;
    RAISE NOTICE 'invoice_items table exists: %', items_exists;
    RAISE NOTICE '';
    RAISE NOTICE 'All invoice-related tables are ready for use!';
    RAISE NOTICE '✓ Invoice generation';
    RAISE NOTICE '✓ Invoice item tracking';
    RAISE NOTICE '✓ Payment recording';
    RAISE NOTICE '✓ PDF storage';
    RAISE NOTICE '=====================================================';
END $$;