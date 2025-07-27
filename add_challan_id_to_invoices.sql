-- Add challan_id to invoices table for proper document linking
-- This allows invoices to be created from challans without requiring an order

-- 1. Add challan_id column to invoices table
ALTER TABLE invoices
ADD COLUMN challan_id INTEGER REFERENCES challans(challan_id);

-- 2. Add index for better query performance
CREATE INDEX idx_invoices_challan ON invoices(challan_id);

-- 3. Add conversion tracking to challans table
ALTER TABLE challans
ADD COLUMN converted_to_invoice BOOLEAN DEFAULT FALSE,
ADD COLUMN invoice_id INTEGER REFERENCES invoices(invoice_id),
ADD COLUMN conversion_date TIMESTAMP;

-- 4. Add index for challan invoice tracking
CREATE INDEX idx_challans_invoice ON challans(invoice_id);

-- 5. Update existing invoices that were created from challans
-- This query attempts to link existing invoices to their source challans
-- based on matching customer_id and dates
UPDATE invoices i
SET challan_id = c.challan_id
FROM challans c
WHERE i.customer_id = c.customer_id
  AND i.order_id = c.order_id
  AND i.order_id IS NOT NULL
  AND i.challan_id IS NULL
  AND DATE(i.invoice_date) >= DATE(c.challan_date);

-- 6. Mark challans that have been converted to invoices
UPDATE challans c
SET converted_to_invoice = TRUE,
    invoice_id = i.invoice_id,
    conversion_date = i.created_at
FROM invoices i
WHERE i.challan_id = c.challan_id;

-- 7. Add comments for documentation
COMMENT ON COLUMN invoices.challan_id IS 'Reference to the delivery challan this invoice was created from';
COMMENT ON COLUMN challans.converted_to_invoice IS 'Flag indicating if this challan has been converted to an invoice';
COMMENT ON COLUMN challans.invoice_id IS 'Reference to the invoice created from this challan';
COMMENT ON COLUMN challans.conversion_date IS 'Timestamp when the challan was converted to invoice';