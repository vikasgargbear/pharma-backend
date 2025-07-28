-- Make order_id nullable in invoices table to allow creating invoices directly from challans
-- This allows flexible document flows: Direct Invoice, Challan->Invoice, Order->Invoice

ALTER TABLE invoices 
ALTER COLUMN order_id DROP NOT NULL;

-- Add comment for clarity
COMMENT ON COLUMN invoices.order_id IS 'Reference to order - optional, as invoices can be created directly or from challans';