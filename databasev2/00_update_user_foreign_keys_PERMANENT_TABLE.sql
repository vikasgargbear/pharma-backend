-- =====================================================
-- SCRIPT 00: Update User Foreign Keys - Using Permanent Table
-- This version uses a permanent table instead of temporary
-- =====================================================

-- STEP 1: Create helper function (run this first)
CREATE OR REPLACE FUNCTION find_referencing_tables(target_table text)
RETURNS TABLE(
    source_table text,
    constraint_name text,
    source_column text,
    target_column text
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        conrelid::regclass::text as source_table,
        conname as constraint_name,
        a.attname as source_column,
        af.attname as target_column
    FROM pg_constraint c
    JOIN pg_attribute a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
    JOIN pg_attribute af ON af.attnum = ANY(c.confkey) AND af.attrelid = c.confrelid
    WHERE c.confrelid = target_table::regclass
    AND c.contype = 'f';
END;
$$ LANGUAGE plpgsql;

-- STEP 2: Check current state
SELECT 
    'users table count' as description,
    COUNT(*) as count 
FROM users
UNION ALL
SELECT 
    'org_users table count' as description,
    COUNT(*) as count 
FROM org_users
UNION ALL
SELECT 
    'users without org_users match' as description,
    COUNT(*) as count
FROM users u
WHERE u.email NOT IN (SELECT email FROM org_users);

-- STEP 3: Create a permanent mapping table
DROP TABLE IF EXISTS _user_migration_mapping;
CREATE TABLE _user_migration_mapping AS
WITH user_data AS (
    SELECT 
        u.user_id as old_user_id,
        u.email,
        u.name,
        u.role,
        u.created_at as user_created_at
    FROM users u
),
org_user_data AS (
    SELECT 
        ou.user_id as new_user_id,
        ou.email,
        ou.full_name,
        ou.org_id,
        ou.created_at as org_user_created_at
    FROM org_users ou
)
SELECT 
    ud.old_user_id,
    oud.new_user_id,
    ud.email,
    oud.org_id,
    ud.name,
    ud.role
FROM user_data ud
LEFT JOIN org_user_data oud ON ud.email = oud.email;

-- Verify the mapping was created
SELECT 
    COUNT(*) as total_users,
    COUNT(new_user_id) as already_mapped,
    COUNT(*) - COUNT(new_user_id) as need_creation
FROM _user_migration_mapping;

-- STEP 4: Create org_users for unmapped users (if any)
INSERT INTO org_users (org_id, full_name, email, role, password_hash, created_at)
SELECT 
    COALESCE(
        (SELECT org_id FROM organizations LIMIT 1),
        '00000000-0000-0000-0000-000000000000'::uuid
    ) as org_id,
    COALESCE(u.name, u.email) as full_name,
    u.email,
    COALESCE(u.role, 'user') as role,
    u.password_hash,
    u.created_at
FROM users u
WHERE u.email NOT IN (SELECT email FROM org_users);

-- STEP 5: Update the mapping table with new user IDs
UPDATE _user_migration_mapping um
SET new_user_id = ou.user_id
FROM org_users ou
WHERE um.email = ou.email
AND um.new_user_id IS NULL;

-- Verify all users are now mapped
SELECT 
    COUNT(*) as total_mappings,
    COUNT(new_user_id) as mapped_users,
    COUNT(*) - COUNT(new_user_id) as unmapped_users
FROM _user_migration_mapping;

-- STEP 6: Create a single update script that updates all tables at once
-- This combines all updates into one transaction
BEGIN;

-- Update all tables that reference users
UPDATE audit_logs SET user_id = m.new_user_id 
FROM _user_migration_mapping m WHERE audit_logs.user_id = m.old_user_id;

UPDATE batch_locations SET moved_by = m.new_user_id 
FROM _user_migration_mapping m WHERE batch_locations.moved_by = m.old_user_id;

UPDATE challan_tracking SET updated_by = m.new_user_id 
FROM _user_migration_mapping m WHERE challan_tracking.updated_by = m.old_user_id;

UPDATE challans SET prepared_by = m.new_user_id 
FROM _user_migration_mapping m WHERE challans.prepared_by = m.old_user_id;

UPDATE challans SET dispatched_by = m.new_user_id 
FROM _user_migration_mapping m WHERE challans.dispatched_by = m.old_user_id;

UPDATE compliance_checks SET resolved_by = m.new_user_id 
FROM _user_migration_mapping m WHERE compliance_checks.resolved_by = m.old_user_id;

UPDATE customer_credit_notes SET approved_by = m.new_user_id 
FROM _user_migration_mapping m WHERE customer_credit_notes.approved_by = m.old_user_id;

UPDATE file_uploads SET uploaded_by = m.new_user_id 
FROM _user_migration_mapping m WHERE file_uploads.uploaded_by = m.old_user_id;

UPDATE file_uploads SET verified_by = m.new_user_id 
FROM _user_migration_mapping m WHERE file_uploads.verified_by = m.old_user_id;

UPDATE inventory_transactions SET performed_by = m.new_user_id 
FROM _user_migration_mapping m WHERE inventory_transactions.performed_by = m.old_user_id;

UPDATE license_documents SET uploaded_by = m.new_user_id 
FROM _user_migration_mapping m WHERE license_documents.uploaded_by = m.old_user_id;

UPDATE license_documents SET verified_by = m.new_user_id 
FROM _user_migration_mapping m WHERE license_documents.verified_by = m.old_user_id;

UPDATE loyalty_redemptions SET processed_by = m.new_user_id 
FROM _user_migration_mapping m WHERE loyalty_redemptions.processed_by = m.old_user_id;

UPDATE loyalty_redemptions SET refunded_by = m.new_user_id 
FROM _user_migration_mapping m WHERE loyalty_redemptions.refunded_by = m.old_user_id;

UPDATE loyalty_transactions SET processed_by = m.new_user_id 
FROM _user_migration_mapping m WHERE loyalty_transactions.processed_by = m.old_user_id;

UPDATE price_history SET changed_by = m.new_user_id 
FROM _user_migration_mapping m WHERE price_history.changed_by = m.old_user_id;

UPDATE purchase_returns SET processed_by = m.new_user_id 
FROM _user_migration_mapping m WHERE purchase_returns.processed_by = m.old_user_id;

UPDATE regulatory_licenses SET verified_by = m.new_user_id 
FROM _user_migration_mapping m WHERE regulatory_licenses.verified_by = m.old_user_id;

COMMIT;

-- STEP 7: Drop all foreign key constraints referencing users table
BEGIN;

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

COMMIT;

-- STEP 8: Add new foreign key constraints to org_users
BEGIN;

ALTER TABLE audit_logs 
    ADD CONSTRAINT audit_logs_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES org_users(user_id);

ALTER TABLE batch_locations 
    ADD CONSTRAINT batch_locations_moved_by_fkey 
    FOREIGN KEY (moved_by) REFERENCES org_users(user_id);

ALTER TABLE challan_tracking 
    ADD CONSTRAINT challan_tracking_updated_by_fkey 
    FOREIGN KEY (updated_by) REFERENCES org_users(user_id);

ALTER TABLE challans 
    ADD CONSTRAINT challans_prepared_by_fkey 
    FOREIGN KEY (prepared_by) REFERENCES org_users(user_id);

ALTER TABLE challans 
    ADD CONSTRAINT challans_dispatched_by_fkey 
    FOREIGN KEY (dispatched_by) REFERENCES org_users(user_id);

ALTER TABLE compliance_checks 
    ADD CONSTRAINT compliance_checks_resolved_by_fkey 
    FOREIGN KEY (resolved_by) REFERENCES org_users(user_id);

ALTER TABLE customer_credit_notes 
    ADD CONSTRAINT customer_credit_notes_approved_by_fkey 
    FOREIGN KEY (approved_by) REFERENCES org_users(user_id);

ALTER TABLE file_uploads 
    ADD CONSTRAINT file_uploads_uploaded_by_fkey 
    FOREIGN KEY (uploaded_by) REFERENCES org_users(user_id);

ALTER TABLE file_uploads 
    ADD CONSTRAINT file_uploads_verified_by_fkey 
    FOREIGN KEY (verified_by) REFERENCES org_users(user_id);

ALTER TABLE inventory_transactions 
    ADD CONSTRAINT inventory_transactions_performed_by_fkey 
    FOREIGN KEY (performed_by) REFERENCES org_users(user_id);

ALTER TABLE license_documents 
    ADD CONSTRAINT license_documents_uploaded_by_fkey 
    FOREIGN KEY (uploaded_by) REFERENCES org_users(user_id);

ALTER TABLE license_documents 
    ADD CONSTRAINT license_documents_verified_by_fkey 
    FOREIGN KEY (verified_by) REFERENCES org_users(user_id);

ALTER TABLE loyalty_redemptions 
    ADD CONSTRAINT loyalty_redemptions_processed_by_fkey 
    FOREIGN KEY (processed_by) REFERENCES org_users(user_id);

ALTER TABLE loyalty_redemptions 
    ADD CONSTRAINT loyalty_redemptions_refunded_by_fkey 
    FOREIGN KEY (refunded_by) REFERENCES org_users(user_id);

ALTER TABLE loyalty_transactions 
    ADD CONSTRAINT loyalty_transactions_processed_by_fkey 
    FOREIGN KEY (processed_by) REFERENCES org_users(user_id);

ALTER TABLE price_history 
    ADD CONSTRAINT price_history_changed_by_fkey 
    FOREIGN KEY (changed_by) REFERENCES org_users(user_id);

ALTER TABLE purchase_returns 
    ADD CONSTRAINT purchase_returns_processed_by_fkey 
    FOREIGN KEY (processed_by) REFERENCES org_users(user_id);

ALTER TABLE regulatory_licenses 
    ADD CONSTRAINT regulatory_licenses_verified_by_fkey 
    FOREIGN KEY (verified_by) REFERENCES org_users(user_id);

COMMIT;

-- STEP 9: Verify no more references to users table
SELECT * FROM find_referencing_tables('users');

-- STEP 10: Drop the users table and cleanup
-- ONLY RUN THIS AFTER CONFIRMING STEP 9 RETURNS NO ROWS!
BEGIN;

-- Drop the users table
DROP TABLE IF EXISTS users CASCADE;

-- Drop the user_sessions table if it exists
DROP TABLE IF EXISTS user_sessions CASCADE;

-- Clean up the mapping table
DROP TABLE IF EXISTS _user_migration_mapping;

-- Drop the helper function
DROP FUNCTION IF EXISTS find_referencing_tables(text);

-- Log the migration
INSERT INTO activity_log (org_id, activity_type, activity_description, created_at)
SELECT 
    org_id,
    'USER_MIGRATION',
    'Successfully migrated all user references from users to org_users table',
    CURRENT_TIMESTAMP
FROM organizations
LIMIT 1;

COMMIT;

-- Final verification
SELECT 
    'Migration Complete!' as status,
    (SELECT COUNT(*) FROM org_users) as total_org_users,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users') as users_table_exists;