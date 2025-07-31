-- =====================================================
-- SIMPLIFIED: Drop Empty Users Table
-- Since users table has 0 rows, we just need to:
-- 1. Drop all FK constraints
-- 2. Drop the empty table
-- =====================================================

-- STEP 1: Verify users table is indeed empty
SELECT 
    'users table row count' as check_type,
    COUNT(*) as count 
FROM users;

-- STEP 2: Drop all foreign key constraints referencing the empty users table
BEGIN;

-- Drop all the constraints
ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey;
ALTER TABLE batch_locations DROP CONSTRAINT IF EXISTS batch_locations_moved_by_fkey;
ALTER TABLE challan_tracking DROP CONSTRAINT IF EXISTS challan_tracking_updated_by_fkey;
ALTER TABLE challans DROP CONSTRAINT IF EXISTS challans_prepared_by_fkey;
ALTER TABLE challans DROP CONSTRAINT IF EXISTS challans_dispatched_by_fkey;
ALTER TABLE compliance_checks DROP CONSTRAINT IF EXISTS compliance_checks_resolved_by_fkey;
ALTER TABLE customer_credit_notes DROP CONSTRAINT IF EXISTS customer_credit_notes_approved_by_fkey;
ALTER TABLE file_uploads DROP CONSTRAINT IF EXISTS file_uploads_uploaded_by_fkey;
ALTER TABLE file_uploads DROP CONSTRAINT IF EXISTS file_uploads_verified_by_fkey;
ALTER TABLE inventory_transactions DROP CONSTRAINT IF EXISTS inventory_transactions_performed_by_fkey;
ALTER TABLE license_documents DROP CONSTRAINT IF EXISTS license_documents_uploaded_by_fkey;
ALTER TABLE license_documents DROP CONSTRAINT IF EXISTS license_documents_verified_by_fkey;
ALTER TABLE loyalty_redemptions DROP CONSTRAINT IF EXISTS loyalty_redemptions_processed_by_fkey;
ALTER TABLE loyalty_redemptions DROP CONSTRAINT IF EXISTS loyalty_redemptions_refunded_by_fkey;
ALTER TABLE loyalty_transactions DROP CONSTRAINT IF EXISTS loyalty_transactions_processed_by_fkey;
ALTER TABLE price_history DROP CONSTRAINT IF EXISTS price_history_changed_by_fkey;
ALTER TABLE purchase_returns DROP CONSTRAINT IF EXISTS purchase_returns_processed_by_fkey;
ALTER TABLE regulatory_licenses DROP CONSTRAINT IF EXISTS regulatory_licenses_verified_by_fkey;
ALTER TABLE storage_locations DROP CONSTRAINT IF EXISTS storage_locations_location_manager_fkey;
ALTER TABLE upi_payments DROP CONSTRAINT IF EXISTS upi_payments_reconciled_by_fkey;

COMMIT;

-- STEP 3: Check data in tables that had FKs to users
-- This will show if any of these tables have non-null user references
SELECT 
    'audit_logs' as table_name,
    COUNT(*) as total_rows,
    COUNT(user_id) as rows_with_user_id
FROM audit_logs
WHERE user_id IS NOT NULL
UNION ALL
SELECT 
    'batch_locations' as table_name,
    COUNT(*) as total_rows,
    COUNT(moved_by) as rows_with_user_id
FROM batch_locations
WHERE moved_by IS NOT NULL
UNION ALL
SELECT 
    'inventory_transactions' as table_name,
    COUNT(*) as total_rows,
    COUNT(performed_by) as rows_with_user_id
FROM inventory_transactions
WHERE performed_by IS NOT NULL
UNION ALL
SELECT 
    'file_uploads' as table_name,
    COUNT(*) as total_rows,
    COUNT(uploaded_by) + COUNT(verified_by) as rows_with_user_id
FROM file_uploads
WHERE uploaded_by IS NOT NULL OR verified_by IS NOT NULL;

-- STEP 4: Set any remaining user_id references to NULL (since users table is empty)
BEGIN;

-- Set all user references to NULL since there are no users to reference
UPDATE audit_logs SET user_id = NULL WHERE user_id IS NOT NULL;
UPDATE batch_locations SET moved_by = NULL WHERE moved_by IS NOT NULL;
UPDATE challan_tracking SET updated_by = NULL WHERE updated_by IS NOT NULL;
UPDATE challans SET prepared_by = NULL, dispatched_by = NULL 
    WHERE prepared_by IS NOT NULL OR dispatched_by IS NOT NULL;
UPDATE compliance_checks SET resolved_by = NULL WHERE resolved_by IS NOT NULL;
UPDATE customer_credit_notes SET approved_by = NULL WHERE approved_by IS NOT NULL;
UPDATE file_uploads SET uploaded_by = NULL, verified_by = NULL 
    WHERE uploaded_by IS NOT NULL OR verified_by IS NOT NULL;
UPDATE inventory_transactions SET performed_by = NULL WHERE performed_by IS NOT NULL;
UPDATE license_documents SET uploaded_by = NULL, verified_by = NULL 
    WHERE uploaded_by IS NOT NULL OR verified_by IS NOT NULL;
UPDATE loyalty_redemptions SET processed_by = NULL, refunded_by = NULL 
    WHERE processed_by IS NOT NULL OR refunded_by IS NOT NULL;
UPDATE loyalty_transactions SET processed_by = NULL WHERE processed_by IS NOT NULL;
UPDATE price_history SET changed_by = NULL WHERE changed_by IS NOT NULL;
UPDATE purchase_returns SET processed_by = NULL WHERE processed_by IS NOT NULL;
UPDATE regulatory_licenses SET verified_by = NULL WHERE verified_by IS NOT NULL;
UPDATE storage_locations SET location_manager = NULL WHERE location_manager IS NOT NULL;
UPDATE upi_payments SET reconciled_by = NULL WHERE reconciled_by IS NOT NULL;

COMMIT;

-- STEP 5: Now we can safely drop the empty users table
DROP TABLE IF EXISTS users CASCADE;

-- Also drop user_sessions if it exists
DROP TABLE IF EXISTS user_sessions CASCADE;

-- STEP 6: Verify the users table is gone
SELECT 
    'Tables named users' as check_type,
    COUNT(*) as count
FROM information_schema.tables 
WHERE table_name = 'users';

-- STEP 7: Log the cleanup
INSERT INTO activity_log (org_id, activity_type, activity_description, created_at)
SELECT 
    org_id,
    'USER_TABLE_CLEANUP',
    'Dropped empty users table and removed all foreign key constraints',
    CURRENT_TIMESTAMP
FROM organizations
LIMIT 1;

-- Final status
SELECT 
    'Migration Complete!' as status,
    'Empty users table dropped' as action,
    (SELECT COUNT(*) FROM org_users) as org_users_count;