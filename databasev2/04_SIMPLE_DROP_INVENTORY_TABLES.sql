-- Simple approach - just drop the extra inventory tables
-- Since we already have inventory_movements working

-- Drop if exists
DROP TABLE IF EXISTS inventory_transactions CASCADE;
DROP TABLE IF EXISTS stock_transfers CASCADE;
DROP TABLE IF EXISTS stock_transfer_items CASCADE;
DROP TABLE IF EXISTS batch_inventory_status CASCADE;
DROP TABLE IF EXISTS batch_locations CASCADE;
DROP TABLE IF EXISTS stock_movements CASCADE;

-- Check what's left
SELECT 
    'Inventory tables remaining' as status,
    COUNT(*) as count
FROM pg_tables 
WHERE schemaname = 'public'
AND tablename LIKE '%inventory%' OR tablename LIKE '%stock%';