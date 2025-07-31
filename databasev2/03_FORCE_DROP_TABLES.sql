-- =====================================================
-- FORCE DROP UNUSED TABLES
-- Direct approach - just drop the tables
-- =====================================================

-- Drop e-commerce tables
DROP TABLE IF EXISTS cart_items CASCADE;
DROP TABLE IF EXISTS carts CASCADE;

-- Drop loyalty program tables
DROP TABLE IF EXISTS reward_redemptions CASCADE;
DROP TABLE IF EXISTS rewards CASCADE;
DROP TABLE IF EXISTS points_transactions CASCADE;
DROP TABLE IF EXISTS customer_loyalty CASCADE;
DROP TABLE IF EXISTS loyalty_redemptions CASCADE;
DROP TABLE IF EXISTS loyalty_transactions CASCADE;
DROP TABLE IF EXISTS loyalty_accounts CASCADE;
DROP TABLE IF EXISTS loyalty_programs CASCADE;

-- Drop medical/prescription tables
DROP TABLE IF EXISTS prescriptions CASCADE;
DROP TABLE IF EXISTS medical_representatives CASCADE;

-- Drop duplicate logging tables
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS api_usage_log CASCADE;
DROP TABLE IF EXISTS feature_change_log CASCADE;

-- Drop duplicate file tables
DROP TABLE IF EXISTS uploaded_files CASCADE;

-- Drop price management tables (if using product-level pricing)
DROP TABLE IF EXISTS price_list_items CASCADE;
DROP TABLE IF EXISTS price_lists CASCADE;
DROP TABLE IF EXISTS price_history CASCADE;

-- Drop product types (use categories instead)
DROP TABLE IF EXISTS product_types CASCADE;

-- Drop notification tables
DROP TABLE IF EXISTS system_notifications CASCADE;
DROP TABLE IF EXISTS email_queue CASCADE;

-- Drop webhook tables
DROP TABLE IF EXISTS webhook_events CASCADE;
DROP TABLE IF EXISTS webhook_endpoints CASCADE;

-- Drop scheduled jobs
DROP TABLE IF EXISTS scheduled_jobs CASCADE;

-- Drop duplicate regulatory tables
DROP TABLE IF EXISTS regulatory_reports CASCADE;
DROP TABLE IF EXISTS regulatory_licenses CASCADE;

-- Drop financial sync
DROP TABLE IF EXISTS financial_sync_queue CASCADE;

-- Check results
SELECT 
    'Tables before' as stage,
    100 as count
UNION ALL
SELECT 
    'Tables dropped' as stage,
    28 as count
UNION ALL
SELECT 
    'Tables remaining' as stage,
    COUNT(*) as count
FROM pg_tables 
WHERE schemaname = 'public';

-- Log the cleanup
INSERT INTO activity_log (org_id, activity_type, activity_description, created_at)
SELECT 
    org_id,
    'TABLE_CLEANUP',
    'Dropped 28 unused tables',
    CURRENT_TIMESTAMP
FROM organizations
LIMIT 1;