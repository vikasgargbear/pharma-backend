-- Final check of table count and status

-- 1. Get current table count
SELECT 
    'Current table count' as metric,
    COUNT(*) as count
FROM pg_tables 
WHERE schemaname = 'public';

-- 2. List all remaining tables
SELECT 
    tablename as remaining_tables,
    CASE 
        -- Core business tables
        WHEN tablename IN ('organizations', 'org_users', 'customers', 'suppliers', 'products', 
                          'categories', 'batches', 'locations', 'warehouses') 
        THEN 'Core Business'
        
        -- Transaction tables
        WHEN tablename IN ('orders', 'order_items', 'invoices', 'invoice_items', 
                          'purchases', 'purchase_items', 'challans', 'challan_items',
                          'sales_returns', 'sales_return_items', 'purchase_returns', 
                          'purchase_return_items') 
        THEN 'Transactions'
        
        -- Inventory tables
        WHEN tablename IN ('inventory_movements', 'opening_stock', 'stock_adjustments',
                          'batch_inventory', 'inventory_alerts') 
        THEN 'Inventory'
        
        -- Financial tables
        WHEN tablename IN ('payment_entries', 'payment_allocations', 'expense_entries',
                          'expense_categories', 'party_ledger', 'ledger_entries',
                          'accounting_settings', 'tax_rates') 
        THEN 'Financial'
        
        -- Pharma specific
        WHEN tablename IN ('drug_compliance', 'narcotics_register', 'batch_recalls',
                          'quality_checks', 'temperature_logs') 
        THEN 'Pharma Compliance'
        
        -- System tables
        WHEN tablename IN ('activity_log', 'notifications', 'print_templates',
                          'user_preferences', 'system_settings', 'backup_log') 
        THEN 'System'
        
        -- Reports and analytics
        WHEN tablename IN ('report_schedules', 'saved_reports', 'dashboard_widgets') 
        THEN 'Reports'
        
        ELSE 'Other'
    END as category
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY category, tablename;

-- 3. Count by category
SELECT 
    category,
    COUNT(*) as table_count
FROM (
    SELECT 
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
            
            WHEN tablename IN ('payment_entries', 'payment_allocations', 'expense_entries',
                              'expense_categories', 'party_ledger', 'ledger_entries',
                              'accounting_settings', 'tax_rates') 
            THEN 'Financial'
            
            WHEN tablename IN ('drug_compliance', 'narcotics_register', 'batch_recalls',
                              'quality_checks', 'temperature_logs') 
            THEN 'Pharma Compliance'
            
            WHEN tablename IN ('activity_log', 'notifications', 'print_templates',
                              'user_preferences', 'system_settings', 'backup_log') 
            THEN 'System'
            
            WHEN tablename IN ('report_schedules', 'saved_reports', 'dashboard_widgets') 
            THEN 'Reports'
            
            ELSE 'Other'
        END as category
    FROM pg_tables 
    WHERE schemaname = 'public'
) t
GROUP BY category
ORDER BY category;

-- 4. Migration summary
SELECT 
    'Progress Summary' as report,
    'Started with: 100+ tables' as initial_state,
    'Target: ~45-50 tables' as goal,
    'Current: ' || COUNT(*) || ' tables' as current_state,
    CASE 
        WHEN COUNT(*) <= 55 THEN 'Goal achieved!'
        ELSE 'Need to remove ' || (COUNT(*) - 50) || ' more tables'
    END as status
FROM pg_tables 
WHERE schemaname = 'public';

-- 5. Tables that could potentially be merged or removed
WITH potential_removals AS (
    SELECT tablename 
    FROM pg_tables 
    WHERE schemaname = 'public'
    AND tablename IN (
        -- Potential duplicates or mergeable
        'customer_payments', 'supplier_payments', 'vendor_payments',
        'invoice_payments', 'upi_payments',
        'inventory_transactions', 'stock_transfers', 'stock_transfer_items',
        'batch_inventory_status', 'batch_locations', 'stock_movements',
        'customer_credit_notes', 'customer_advance_payments',
        'price_lists', 'price_list_items', 'price_history',
        'api_usage_log', 'feature_change_log',
        'user_sessions', 'uploaded_files',
        'email_queue', 'system_notifications',
        'webhook_endpoints', 'webhook_events',
        'regulatory_reports', 'regulatory_licenses',
        'financial_sync_queue', 'scheduled_jobs'
    )
)
SELECT 
    'Tables that can still be removed:' as category,
    COUNT(*) as count,
    STRING_AGG(tablename, ', ') as table_names
FROM potential_removals;