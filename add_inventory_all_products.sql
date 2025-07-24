-- Add test inventory for ALL products
-- Run this in Supabase SQL Editor to add inventory

-- Add batches for all products that don't have stock
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
    p.org_id,
    p.product_id,
    'TEST-' || TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || '-' || p.product_id as batch_number,
    100 as quantity_received,  -- Add 100 units
    100 as quantity_available,
    0 as quantity_sold,
    COALESCE(p.sale_price * 0.8, p.mrp * 0.7, 100) as cost_price,  -- 80% of sale price or default
    COALESCE(p.sale_price, p.mrp * 0.9, 125) as selling_price,
    COALESCE(p.mrp, p.sale_price * 1.2, 150) as mrp,
    CURRENT_DATE + INTERVAL '1 year' as expiry_date,  -- 1 year expiry
    CURRENT_TIMESTAMP as created_at,
    CURRENT_TIMESTAMP as updated_at
FROM products p
LEFT JOIN batches b ON p.product_id = b.product_id AND b.quantity_available > 0
WHERE b.batch_id IS NULL
AND p.org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f';  -- Your org ID

-- Verify the stock was added
SELECT 
    COUNT(DISTINCT p.product_id) as total_products,
    COUNT(DISTINCT CASE WHEN b.batch_id IS NOT NULL THEN p.product_id END) as products_with_stock,
    COUNT(DISTINCT CASE WHEN b.batch_id IS NULL THEN p.product_id END) as products_without_stock
FROM products p
LEFT JOIN batches b ON p.product_id = b.product_id AND b.quantity_available > 0
WHERE p.org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f';

-- Show sample of products with new stock
SELECT 
    p.product_name,
    p.sale_price,
    p.mrp,
    b.batch_number,
    b.quantity_available,
    b.expiry_date
FROM products p
JOIN batches b ON p.product_id = b.product_id
WHERE b.batch_number LIKE 'TEST-%'
AND p.org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f'
ORDER BY b.created_at DESC
LIMIT 10;