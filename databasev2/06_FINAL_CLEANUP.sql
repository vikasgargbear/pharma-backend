-- Final cleanup to reach target of 45-50 tables
-- Current: 63 tables, need to drop ~13-18 more

-- Show all current tables to identify candidates
SELECT 
    tablename,
    CASE 
        -- Keep these core tables
        WHEN tablename IN ('organizations', 'org_users', 'customers', 'suppliers', 'products', 
                          'categories', 'batches', 'locations', 'warehouses',
                          'orders', 'order_items', 'invoices', 'invoice_items', 
                          'purchases', 'purchase_items', 'challans', 'challan_items',
                          'sales_returns', 'sales_return_items', 'purchase_returns', 
                          'purchase_return_items', 'inventory_movements', 'opening_stock',
                          'payments', 'payment_allocations', 'activity_log') 
        THEN 'KEEP - Core Business'
        
        -- These might be droppable
        WHEN tablename IN ('api_usage_log', 'feature_change_log', 'audit_logs',
                          'uploaded_files', 'user_sessions', 'email_queue',
                          'system_notifications', 'webhook_endpoints', 'webhook_events',
                          'scheduled_jobs', 'price_lists', 'price_list_items',
                          'price_history', 'regulatory_reports', 'regulatory_licenses',
                          'financial_sync_queue', 'backup_log', 'report_schedules',
                          'saved_reports', 'dashboard_widgets')
        THEN 'DROP CANDIDATE'
        
        ELSE 'REVIEW NEEDED'
    END as action,
    'Table: ' || tablename as details
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY action, tablename;

-- Count by action
SELECT 
    action,
    COUNT(*) as count
FROM (
    SELECT 
        tablename,
        CASE 
            WHEN tablename IN ('organizations', 'org_users', 'customers', 'suppliers', 'products', 
                              'categories', 'batches', 'locations', 'warehouses',
                              'orders', 'order_items', 'invoices', 'invoice_items', 
                              'purchases', 'purchase_items', 'challans', 'challan_items',
                              'sales_returns', 'sales_return_items', 'purchase_returns', 
                              'purchase_return_items', 'inventory_movements', 'opening_stock',
                              'payments', 'payment_allocations', 'activity_log') 
            THEN 'KEEP - Core Business'
            
            WHEN tablename IN ('api_usage_log', 'feature_change_log', 'audit_logs',
                              'uploaded_files', 'user_sessions', 'email_queue',
                              'system_notifications', 'webhook_endpoints', 'webhook_events',
                              'scheduled_jobs', 'price_lists', 'price_list_items',
                              'price_history', 'regulatory_reports', 'regulatory_licenses',
                              'financial_sync_queue', 'backup_log', 'report_schedules',
                              'saved_reports', 'dashboard_widgets')
            THEN 'DROP CANDIDATE'
            
            ELSE 'REVIEW NEEDED'
        END as action
    FROM pg_tables 
    WHERE schemaname = 'public'
) t
GROUP BY action;