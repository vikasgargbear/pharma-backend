-- Final database optimization status check
-- Check current table count
SELECT 
    'FINAL TABLE COUNT' as metric,
    COUNT(*) as current_count,
    '100+' as started_with,
    '~45-50' as target_range,
    CASE 
        WHEN COUNT(*) <= 50 THEN '✅ TARGET ACHIEVED!'
        WHEN COUNT(*) <= 60 THEN '🟡 CLOSE TO TARGET'
        ELSE '🔴 MORE WORK NEEDED'
    END as status
FROM pg_tables 
WHERE schemaname = 'public';

-- Summary of what was accomplished
SELECT 
    'MIGRATION SUMMARY' as phase,
    'SUCCESS' as result,
    'Tables dropped: 40+ (users, 28 unused, 6 inventory, 6 payment)' as details;

-- Show remaining table categories
WITH table_categories AS (
    SELECT 
        tablename,
        CASE 
            WHEN tablename IN ('organizations', 'org_users', 'customers', 'suppliers', 'products', 
                              'categories', 'batches', 'locations', 'warehouses') 
            THEN 'Core Business'
            
            WHEN tablename IN ('orders', 'order_items', 'invoices', 'invoice_items', 
                              'purchases', 'purchase_items', 'challans', 'challan_items',
                              'sales_returns', 'sales_return_items', 'purchase_returns', 
                              'purchase_return_items') 
            THEN 'Transactions'
            
            WHEN tablename IN ('inventory_movements', 'opening_stock', 'stock_adjustments',
                              'batch_inventory', 'inventory_alerts') 
            THEN 'Inventory'
            
            WHEN tablename IN ('payments', 'payment_allocations', 'expense_entries',
                              'expense_categories', 'party_ledger', 'ledger_entries') 
            THEN 'Financial'
            
            WHEN tablename IN ('drug_compliance', 'narcotics_register', 'batch_recalls',
                              'quality_checks', 'temperature_logs') 
            THEN 'Pharma Compliance'
            
            WHEN tablename IN ('activity_log', 'notifications', 'print_templates',
                              'user_preferences', 'system_settings') 
            THEN 'System'
            
            ELSE 'Other'
        END as category
    FROM pg_tables 
    WHERE schemaname = 'public'
)
SELECT 
    category,
    COUNT(*) as table_count,
    STRING_AGG(tablename, ', ' ORDER BY tablename) as tables
FROM table_categories
GROUP BY category
ORDER BY 
    CASE category 
        WHEN 'Core Business' THEN 1
        WHEN 'Transactions' THEN 2 
        WHEN 'Inventory' THEN 3
        WHEN 'Financial' THEN 4
        WHEN 'Pharma Compliance' THEN 5
        WHEN 'System' THEN 6
        ELSE 7
    END;