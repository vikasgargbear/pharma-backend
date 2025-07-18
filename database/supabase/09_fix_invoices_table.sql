-- Fix invoices table by adding missing updated_at column and other improvements

-- Add updated_at column if it doesn't exist
ALTER TABLE invoices 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add cancelled_at for tracking cancellations
ALTER TABLE invoices
ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS cancellation_reason TEXT;

-- Add due_date for payment tracking
ALTER TABLE invoices
ADD COLUMN IF NOT EXISTS due_date DATE;

-- Add PDF storage fields
ALTER TABLE invoices
ADD COLUMN IF NOT EXISTS pdf_url TEXT,
ADD COLUMN IF NOT EXISTS pdf_generated_at TIMESTAMP;

-- Create trigger to auto-update updated_at
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

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_order_id ON invoices(order_id);
CREATE INDEX IF NOT EXISTS idx_invoices_invoice_date ON invoices(invoice_date);
CREATE INDEX IF NOT EXISTS idx_invoices_payment_status ON invoices(payment_status);

-- Update existing records to have updated_at if NULL
UPDATE invoices 
SET updated_at = COALESCE(updated_at, created_at, CURRENT_TIMESTAMP)
WHERE updated_at IS NULL;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Successfully updated invoices table with updated_at and additional fields';
END $$;