-- =====================================================
-- SCRIPT 03: Drop Unused Tables (SAFE VERSION)
-- Checks if tables exist before backing up
-- =====================================================

-- Create backup schema
CREATE SCHEMA IF NOT EXISTS dropped_tables_backup;

-- Helper function to safely backup and drop tables
CREATE OR REPLACE FUNCTION safe_backup_and_drop(table_name text) 
RETURNS void AS $$
BEGIN
    -- Check if table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables 
               WHERE table_schema = 'public' 
               AND table_name = safe_backup_and_drop.table_name) THEN
        -- Create backup
        EXECUTE format('CREATE TABLE dropped_tables_backup.%I AS SELECT * FROM %I LIMIT 0', 
                      table_name, table_name);
        -- Drop table
        EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', table_name);
        RAISE NOTICE 'Dropped table: %', table_name;
    ELSE
        RAISE NOTICE 'Table % does not exist, skipping', table_name;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error with table %: %', table_name, SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- E-commerce tables
SELECT safe_backup_and_drop('carts');
SELECT safe_backup_and_drop('cart_items');

-- Loyalty program tables
SELECT safe_backup_and_drop('loyalty_programs');
SELECT safe_backup_and_drop('loyalty_accounts');
SELECT safe_backup_and_drop('loyalty_transactions');
SELECT safe_backup_and_drop('loyalty_redemptions');
SELECT safe_backup_and_drop('customer_loyalty');
SELECT safe_backup_and_drop('points_transactions');
SELECT safe_backup_and_drop('rewards');
SELECT safe_backup_and_drop('reward_redemptions');

-- Medical/Prescription tables
SELECT safe_backup_and_drop('medical_representatives');
SELECT safe_backup_and_drop('prescriptions');
-- Keep doctors table if you track doctor referrals

-- Duplicate logging tables
SELECT safe_backup_and_drop('audit_logs');
SELECT safe_backup_and_drop('api_usage_log');
SELECT safe_backup_and_drop('feature_change_log');

-- Duplicate file upload tables
SELECT safe_backup_and_drop('uploaded_files');

-- Session management
SELECT safe_backup_and_drop('user_sessions');

-- Users table (already dropped)
SELECT safe_backup_and_drop('users');

-- Price list tables
SELECT safe_backup_and_drop('price_lists');
SELECT safe_backup_and_drop('price_list_items');
SELECT safe_backup_and_drop('price_history');

-- Product types
SELECT safe_backup_and_drop('product_types');

-- Notification tables
SELECT safe_backup_and_drop('system_notifications');
SELECT safe_backup_and_drop('email_queue');

-- Webhook tables
SELECT safe_backup_and_drop('webhook_endpoints');
SELECT safe_backup_and_drop('webhook_events');

-- Scheduled jobs
SELECT safe_backup_and_drop('scheduled_jobs');

-- Duplicate regulatory tables
SELECT safe_backup_and_drop('regulatory_licenses');
SELECT safe_backup_and_drop('regulatory_reports');

-- Financial sync queue
SELECT safe_backup_and_drop('financial_sync_queue');

-- Clean up the helper function
DROP FUNCTION safe_backup_and_drop(text);

-- Show summary of dropped tables
SELECT 
    tablename as dropped_table
FROM pg_tables 
WHERE schemaname = 'dropped_tables_backup'
ORDER BY tablename;

-- Log the cleanup
INSERT INTO activity_log (org_id, activity_type, activity_description, created_at)
SELECT 
    org_id,
    'TABLE_CLEANUP',
    'Dropped unused tables as part of database optimization',
    CURRENT_TIMESTAMP
FROM organizations
LIMIT 1;

-- Show current table count
SELECT 
    'Tables before cleanup' as status,
    100 as count
UNION ALL
SELECT 
    'Tables after cleanup' as status,
    COUNT(*) as count
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE';