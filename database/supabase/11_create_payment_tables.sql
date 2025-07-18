-- Create invoice_payments table for payment tracking

CREATE TABLE IF NOT EXISTS invoice_payments (
    payment_id SERIAL PRIMARY KEY,
    payment_reference VARCHAR(50) UNIQUE NOT NULL,
    invoice_id INTEGER NOT NULL REFERENCES invoices(invoice_id),
    
    -- Payment details
    payment_date DATE NOT NULL,
    payment_mode VARCHAR(20) NOT NULL CHECK (payment_mode IN ('cash', 'cheque', 'online', 'card', 'upi', 'neft', 'rtgs')),
    payment_amount DECIMAL(12,2) NOT NULL,
    
    -- Transaction details
    transaction_reference VARCHAR(100),
    bank_name VARCHAR(100),
    cheque_number VARCHAR(50),
    cheque_date DATE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'completed' CHECK (status IN ('completed', 'pending', 'cancelled', 'bounced')),
    cancellation_reason TEXT,
    cancelled_at TIMESTAMP,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    
    -- Constraints
    CONSTRAINT check_cheque_details CHECK (
        (payment_mode != 'cheque') OR 
        (payment_mode = 'cheque' AND cheque_number IS NOT NULL AND cheque_date IS NOT NULL)
    )
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_invoice_payments_invoice_id ON invoice_payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_payments_payment_date ON invoice_payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_invoice_payments_payment_mode ON invoice_payments(payment_mode);
CREATE INDEX IF NOT EXISTS idx_invoice_payments_status ON invoice_payments(status);

-- Create trigger for updated_at
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

-- Add payment tracking columns to orders table if not exists
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20) DEFAULT 'unpaid' 
    CHECK (payment_status IN ('unpaid', 'partial', 'paid', 'overdue'));

-- Create a view for payment analytics
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

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Successfully created payment tracking tables and views';
END $$;