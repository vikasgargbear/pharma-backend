-- Check status after inventory consolidation
SELECT 
    'Tables after inventory consolidation' as status,
    COUNT(*) as count
FROM pg_tables 
WHERE schemaname = 'public';

-- List tables that were dropped
SELECT 
    'Dropped inventory tables' as category,
    '6 tables removed' as result,
    'inventory_transactions, stock_transfers, stock_transfer_items, batch_inventory_status, batch_locations, stock_movements' as tables;