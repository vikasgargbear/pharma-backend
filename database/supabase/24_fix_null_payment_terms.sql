-- Fix null payment_terms in orders table
-- This is causing validation errors in the API

-- Update all existing orders with null payment_terms to have a default value
UPDATE orders 
SET payment_terms = 'credit' 
WHERE payment_terms IS NULL;

-- Add a default value to the column to prevent future nulls
ALTER TABLE orders 
ALTER COLUMN payment_terms SET DEFAULT 'credit';

-- Verify the fix
SELECT COUNT(*) as null_payment_terms_count 
FROM orders 
WHERE payment_terms IS NULL;