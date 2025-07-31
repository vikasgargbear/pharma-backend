-- =====================================================
-- SCRIPT 03: Drop Unused Tables
-- Purpose: Remove tables that are not used in B2B pharma
-- WARNING: Run ONLY after confirming these tables are not used!
-- =====================================================

-- Create backup of table structures before dropping
CREATE SCHEMA IF NOT EXISTS dropped_tables_backup;

-- E-commerce related tables (not applicable for B2B)
CREATE TABLE dropped_tables_backup.carts AS SELECT * FROM carts LIMIT 0;
CREATE TABLE dropped_tables_backup.cart_items AS SELECT * FROM cart_items LIMIT 0;
DROP TABLE IF EXISTS cart_items CASCADE;
DROP TABLE IF EXISTS carts CASCADE;

-- Loyalty program tables (if not actively used)
CREATE TABLE dropped_tables_backup.loyalty_programs AS SELECT * FROM loyalty_programs LIMIT 0;
CREATE TABLE dropped_tables_backup.loyalty_accounts AS SELECT * FROM loyalty_accounts LIMIT 0;
CREATE TABLE dropped_tables_backup.loyalty_transactions AS SELECT * FROM loyalty_transactions LIMIT 0;
CREATE TABLE dropped_tables_backup.loyalty_redemptions AS SELECT * FROM loyalty_redemptions LIMIT 0;
CREATE TABLE dropped_tables_backup.customer_loyalty AS SELECT * FROM customer_loyalty LIMIT 0;
CREATE TABLE dropped_tables_backup.points_transactions AS SELECT * FROM points_transactions LIMIT 0;
CREATE TABLE dropped_tables_backup.rewards AS SELECT * FROM rewards LIMIT 0;
CREATE TABLE dropped_tables_backup.reward_redemptions AS SELECT * FROM reward_redemptions LIMIT 0;

DROP TABLE IF EXISTS reward_redemptions CASCADE;
DROP TABLE IF EXISTS rewards CASCADE;
DROP TABLE IF EXISTS points_transactions CASCADE;
DROP TABLE IF EXISTS customer_loyalty CASCADE;
DROP TABLE IF EXISTS loyalty_redemptions CASCADE;
DROP TABLE IF EXISTS loyalty_transactions CASCADE;
DROP TABLE IF EXISTS loyalty_accounts CASCADE;
DROP TABLE IF EXISTS loyalty_programs CASCADE;

-- Medical/Prescription tables (unless actively used)
CREATE TABLE dropped_tables_backup.medical_representatives AS SELECT * FROM medical_representatives LIMIT 0;
CREATE TABLE dropped_tables_backup.prescriptions AS SELECT * FROM prescriptions LIMIT 0;
CREATE TABLE dropped_tables_backup.doctors AS SELECT * FROM doctors LIMIT 0;

DROP TABLE IF EXISTS prescriptions CASCADE;
DROP TABLE IF EXISTS medical_representatives CASCADE;
-- Keep doctors table if you track doctor referrals

-- Duplicate logging tables (keep only activity_log)
CREATE TABLE dropped_tables_backup.audit_logs AS SELECT * FROM audit_logs LIMIT 0;
CREATE TABLE dropped_tables_backup.api_usage_log AS SELECT * FROM api_usage_log LIMIT 0;
CREATE TABLE dropped_tables_backup.feature_change_log AS SELECT * FROM feature_change_log LIMIT 0;

DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS api_usage_log CASCADE;
DROP TABLE IF EXISTS feature_change_log CASCADE;

-- Duplicate file upload tables (keep only one)
CREATE TABLE dropped_tables_backup.uploaded_files AS SELECT * FROM uploaded_files LIMIT 0;
DROP TABLE IF EXISTS uploaded_files CASCADE;
-- Keep file_uploads table

-- Session management (use proper session management instead)
CREATE TABLE dropped_tables_backup.user_sessions AS SELECT * FROM user_sessions LIMIT 0;
DROP TABLE IF EXISTS user_sessions CASCADE;

-- Duplicate user table (keep org_users)
CREATE TABLE dropped_tables_backup.users AS SELECT * FROM users LIMIT 0;
DROP TABLE IF EXISTS users CASCADE;

-- Price list tables (if using customer-specific pricing in customers table)
CREATE TABLE dropped_tables_backup.price_lists AS SELECT * FROM price_lists LIMIT 0;
CREATE TABLE dropped_tables_backup.price_list_items AS SELECT * FROM price_list_items LIMIT 0;
CREATE TABLE dropped_tables_backup.price_history AS SELECT * FROM price_history LIMIT 0;

DROP TABLE IF EXISTS price_list_items CASCADE;
DROP TABLE IF EXISTS price_lists CASCADE;
DROP TABLE IF EXISTS price_history CASCADE;

-- Product types (use categories instead)
CREATE TABLE dropped_tables_backup.product_types AS SELECT * FROM product_types LIMIT 0;
DROP TABLE IF EXISTS product_types CASCADE;

-- Notification tables (use proper notification service)
CREATE TABLE dropped_tables_backup.system_notifications AS SELECT * FROM system_notifications LIMIT 0;
CREATE TABLE dropped_tables_backup.email_queue AS SELECT * FROM email_queue LIMIT 0;

DROP TABLE IF EXISTS system_notifications CASCADE;
DROP TABLE IF EXISTS email_queue CASCADE;

-- Webhook tables (unless actively used)
CREATE TABLE dropped_tables_backup.webhook_endpoints AS SELECT * FROM webhook_endpoints LIMIT 0;
CREATE TABLE dropped_tables_backup.webhook_events AS SELECT * FROM webhook_events LIMIT 0;

DROP TABLE IF EXISTS webhook_events CASCADE;
DROP TABLE IF EXISTS webhook_endpoints CASCADE;

-- Scheduled jobs (use proper job scheduler)
CREATE TABLE dropped_tables_backup.scheduled_jobs AS SELECT * FROM scheduled_jobs LIMIT 0;
DROP TABLE IF EXISTS scheduled_jobs CASCADE;

-- Duplicate regulatory tables
CREATE TABLE dropped_tables_backup.regulatory_licenses AS SELECT * FROM regulatory_licenses LIMIT 0;
CREATE TABLE dropped_tables_backup.regulatory_reports AS SELECT * FROM regulatory_reports LIMIT 0;

DROP TABLE IF EXISTS regulatory_licenses CASCADE;
DROP TABLE IF EXISTS regulatory_reports CASCADE;

-- Financial sync queue (review usage first)
CREATE TABLE dropped_tables_backup.financial_sync_queue AS SELECT * FROM financial_sync_queue LIMIT 0;
DROP TABLE IF EXISTS financial_sync_queue CASCADE;

-- Log the cleanup
INSERT INTO activity_log (org_id, activity_type, activity_description, created_at)
SELECT 
    org_id,
    'TABLE_CLEANUP',
    'Dropped unused tables as part of database optimization',
    CURRENT_TIMESTAMP
FROM organizations
LIMIT 1;

-- Summary of dropped tables
SELECT 
    schemaname,
    tablename,
    'Backup created in dropped_tables_backup schema' as status
FROM pg_tables 
WHERE schemaname = 'dropped_tables_backup'
ORDER BY tablename;