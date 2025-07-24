-- Check stock for Flipkart product
-- Run this in Supabase SQL Editor

-- Find the product
SELECT 
    product_id, 
    product_name, 
    product_code,
    mrp,
    sale_price
FROM products 
WHERE product_name LIKE '%Flipkart%' 
   OR product_name LIKE '%flipkart%';

-- Check batches for the product (replace PRODUCT_ID with actual ID from above)
SELECT 
    b.batch_id,
    b.batch_number,
    b.quantity_received,
    b.quantity_available,
    b.quantity_sold,
    b.expiry_date,
    b.created_at
FROM batches b
WHERE b.product_id = [PRODUCT_ID] -- Replace with actual product_id
ORDER BY b.created_at DESC;

-- Get total available stock
SELECT 
    p.product_id,
    p.product_name,
    COALESCE(SUM(b.quantity_available), 0) as total_available_stock
FROM products p
LEFT JOIN batches b ON p.product_id = b.product_id 
    AND b.quantity_available > 0
    AND (b.expiry_date IS NULL OR b.expiry_date > CURRENT_DATE)
WHERE p.product_name LIKE '%Flipkart%'
GROUP BY p.product_id, p.product_name;