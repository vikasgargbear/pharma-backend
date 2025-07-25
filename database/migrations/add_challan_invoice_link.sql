-- Add invoice linking columns to challans table
-- This allows tracking which challans have been invoiced

-- Add invoice_id column to link challan to invoice
ALTER TABLE challans 
ADD COLUMN IF NOT EXISTS invoice_id INTEGER REFERENCES invoices(invoice_id);

-- Add timestamp when challan was invoiced
ALTER TABLE challans
ADD COLUMN IF NOT EXISTS invoiced_at TIMESTAMP;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_challans_invoice_id ON challans(invoice_id);
CREATE INDEX IF NOT EXISTS idx_challans_status_invoice ON challans(status, invoice_id) WHERE status = 'delivered';

-- Add comment explaining the relationship
COMMENT ON COLUMN challans.invoice_id IS 'Links delivered challan to the invoice created from it';
COMMENT ON COLUMN challans.invoiced_at IS 'Timestamp when this challan was included in an invoice';