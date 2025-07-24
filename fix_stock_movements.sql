-- SQL script to check what's happening with batches and inventory

-- Check if inventory table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'inventory'
) as inventory_table_exists;

-- Check batches for Chai products
SELECT 
    b.batch_id,
    b.batch_number,
    b.product_id,
    b.quantity_available,
    b.quantity_received,
    b.org_id,
    b.created_at,
    p.product_name
FROM batches b
JOIN products p ON b.product_id = p.product_id
WHERE p.product_name ILIKE '%chai%'
ORDER BY b.created_at DESC;

-- Check all batches created today
SELECT 
    b.batch_id,
    b.batch_number,
    b.product_id,
    b.quantity_available,
    b.org_id,
    b.created_at,
    p.product_name
FROM batches b
JOIN products p ON b.product_id = p.product_id
WHERE DATE(b.created_at) = CURRENT_DATE
ORDER BY b.created_at DESC;