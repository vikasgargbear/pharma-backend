-- Check what tables were actually dropped and what remains

-- 1. Check what was backed up (successfully dropped)
SELECT 
    'Dropped tables:' as category,
    COUNT(*) as count
FROM pg_tables 
WHERE schemaname = 'dropped_tables_backup';

-- 2. List the dropped tables
SELECT 
    tablename as successfully_dropped
FROM pg_tables 
WHERE schemaname = 'dropped_tables_backup'
ORDER BY tablename;

-- 3. Check current public tables
SELECT 
    'Remaining public tables:' as category,
    COUNT(*) as count
FROM pg_tables 
WHERE schemaname = 'public';

-- 4. Find tables that should have been dropped but weren't
WITH target_tables AS (
    SELECT unnest(ARRAY[
        'carts', 'cart_items', 'loyalty_programs', 'loyalty_accounts',
        'loyalty_transactions', 'loyalty_redemptions', 'customer_loyalty',
        'points_transactions', 'rewards', 'reward_redemptions',
        'medical_representatives', 'prescriptions', 'audit_logs',
        'api_usage_log', 'feature_change_log', 'uploaded_files',
        'user_sessions', 'users', 'price_lists', 'price_list_items',
        'price_history', 'product_types', 'system_notifications',
        'email_queue', 'webhook_endpoints', 'webhook_events',
        'scheduled_jobs', 'regulatory_licenses', 'regulatory_reports',
        'financial_sync_queue'
    ]) as table_name
)
SELECT 
    t.table_name as should_be_dropped_but_still_exists
FROM target_tables t
WHERE EXISTS (
    SELECT 1 FROM pg_tables pt 
    WHERE pt.schemaname = 'public' 
    AND pt.tablename = t.table_name
);

-- 5. Clean up any temporary tables we created
DROP TABLE IF EXISTS user_migration_map;
DROP TABLE IF EXISTS _user_migration_mapping;

-- 6. Check count again
SELECT 
    'Final table count after cleanup:' as status,
    COUNT(*) as count
FROM pg_tables 
WHERE schemaname = 'public';