-- Check what values exist in payment_terms column
SELECT DISTINCT payment_terms, COUNT(*) as count
FROM orders
GROUP BY payment_terms
ORDER BY count DESC;

-- Check if there are any orders with invalid payment_terms
SELECT order_id, order_number, payment_terms
FROM orders
WHERE payment_terms NOT IN ('cash', 'credit', 'advance')
   OR payment_terms IS NULL
LIMIT 10;

-- Fix any invalid payment_terms values
UPDATE orders 
SET payment_terms = 'credit'
WHERE payment_terms NOT IN ('cash', 'credit', 'advance')
   OR payment_terms IS NULL;

-- Add constraint to ensure only valid values (optional - may fail if invalid data exists)
-- ALTER TABLE orders 
-- ADD CONSTRAINT check_payment_terms 
-- CHECK (payment_terms IN ('cash', 'credit', 'advance'));