-- Add test stock for products with no inventory
-- Run this in Supabase SQL Editor for testing

-- First, find products with no stock
WITH products_without_stock AS (
    SELECT 
        p.product_id,
        p.product_name,
        p.product_code,
        p.mrp,
        p.sale_price
    FROM products p
    LEFT JOIN batches b ON p.product_id = b.product_id 
        AND b.quantity_available > 0
    WHERE b.batch_id IS NULL
    AND p.org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f'
    LIMIT 10
)
-- Add test batches for these products
INSERT INTO batches (
    org_id,
    product_id,
    batch_number,
    quantity_received,
    quantity_available,
    quantity_sold,
    cost_price,
    selling_price,
    mrp,
    expiry_date,
    created_at,
    updated_at
)
SELECT
    '12de5e22-eee7-4d25-b3a7-d16d01c6170f' as org_id,
    product_id,
    'TEST-' || TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || '-' || product_id as batch_number,
    100 as quantity_received,  -- Add 100 units
    100 as quantity_available,
    0 as quantity_sold,
    COALESCE(sale_price * 0.8, mrp * 0.7) as cost_price,  -- 80% of sale price as cost
    sale_price,
    mrp,
    CURRENT_DATE + INTERVAL '1 year' as expiry_date,  -- 1 year expiry
    CURRENT_TIMESTAMP as created_at,
    CURRENT_TIMESTAMP as updated_at
FROM products_without_stock;

-- Verify the stock was added
SELECT 
    p.product_name,
    b.batch_number,
    b.quantity_available,
    b.expiry_date
FROM products p
JOIN batches b ON p.product_id = b.product_id
WHERE b.batch_number LIKE 'TEST-%'
ORDER BY b.created_at DESC;