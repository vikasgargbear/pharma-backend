-- Add payment_mode column to purchases table
-- This column tracks how the purchase will be paid (cash, credit, etc.)

ALTER TABLE purchases 
ADD COLUMN IF NOT EXISTS payment_mode TEXT DEFAULT 'cash';

-- Add constraint to ensure valid payment modes
ALTER TABLE purchases
ADD CONSTRAINT check_payment_mode CHECK (payment_mode IN ('cash', 'credit', 'bank_transfer', 'cheque', 'upi', 'other'));

-- Update existing records to have a default payment mode based on payment_status
UPDATE purchases 
SET payment_mode = CASE 
    WHEN payment_status = 'paid' THEN 'cash'
    ELSE 'credit'
END
WHERE payment_mode IS NULL;

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_purchases_payment_mode ON purchases(payment_mode);

-- Also add selling_price to purchase_items if missing
ALTER TABLE purchase_items
ADD COLUMN IF NOT EXISTS selling_price DECIMAL(12,2);

-- Set default selling price to MRP if not set
UPDATE purchase_items
SET selling_price = mrp
WHERE selling_price IS NULL AND mrp IS NOT NULL;