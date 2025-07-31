-- =====================================================
-- SCRIPT 00: Update User Foreign Keys - STEP BY STEP VERSION
-- Run each section separately in Supabase SQL Editor
-- =====================================================

-- SECTION 1: Create helper function (run this first)
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

-- SECTION 2: Check current state (run this to see what we're dealing with)
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

-- SECTION 3: Create the mapping table (run this separately)
DROP TABLE IF EXISTS user_mapping_temp;
CREATE TEMPORARY TABLE user_mapping_temp AS
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
SELECT * FROM user_mapping_temp LIMIT 10;

-- SECTION 4: Create org_users for unmapped users (if any)
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

-- SECTION 5: Update the mapping table with new user IDs
UPDATE user_mapping_temp um
SET new_user_id = ou.user_id
FROM org_users ou
WHERE um.email = ou.email
AND um.new_user_id IS NULL;

-- Verify all users are now mapped
SELECT 
    COUNT(*) as total_mappings,
    COUNT(new_user_id) as mapped_users,
    COUNT(*) - COUNT(new_user_id) as unmapped_users
FROM user_mapping_temp;

-- SECTION 6: Now update each table's foreign keys one by one
-- Run each UPDATE statement separately to identify any issues

-- 6.1: Update audit_logs
UPDATE audit_logs al 
SET user_id = um.new_user_id
FROM user_mapping_temp um
WHERE al.user_id = um.old_user_id;

-- 6.2: Update batch_locations
UPDATE batch_locations bl 
SET moved_by = um.new_user_id
FROM user_mapping_temp um
WHERE bl.moved_by = um.old_user_id;

-- 6.3: Update challan_tracking
UPDATE challan_tracking ct 
SET updated_by = um.new_user_id
FROM user_mapping_temp um
WHERE ct.updated_by = um.old_user_id;

-- 6.4: Update challans (prepared_by)
UPDATE challans c
SET prepared_by = um.new_user_id
FROM user_mapping_temp um
WHERE c.prepared_by = um.old_user_id;

-- 6.5: Update challans (dispatched_by)
UPDATE challans c
SET dispatched_by = um.new_user_id
FROM user_mapping_temp um
WHERE c.dispatched_by = um.old_user_id;

-- 6.6: Update compliance_checks
UPDATE compliance_checks cc 
SET resolved_by = um.new_user_id
FROM user_mapping_temp um
WHERE cc.resolved_by = um.old_user_id;

-- 6.7: Update customer_credit_notes
UPDATE customer_credit_notes ccn 
SET approved_by = um.new_user_id
FROM user_mapping_temp um
WHERE ccn.approved_by = um.old_user_id;

-- 6.8: Update file_uploads (uploaded_by)
UPDATE file_uploads fu
SET uploaded_by = um.new_user_id
FROM user_mapping_temp um
WHERE fu.uploaded_by = um.old_user_id;

-- 6.9: Update file_uploads (verified_by)
UPDATE file_uploads fu
SET verified_by = um.new_user_id
FROM user_mapping_temp um
WHERE fu.verified_by = um.old_user_id;

-- 6.10: Update inventory_transactions
UPDATE inventory_transactions it 
SET performed_by = um.new_user_id
FROM user_mapping_temp um
WHERE it.performed_by = um.old_user_id;

-- 6.11: Update license_documents (uploaded_by)
UPDATE license_documents ld
SET uploaded_by = um.new_user_id
FROM user_mapping_temp um
WHERE ld.uploaded_by = um.old_user_id;

-- 6.12: Update license_documents (verified_by)
UPDATE license_documents ld
SET verified_by = um.new_user_id
FROM user_mapping_temp um
WHERE ld.verified_by = um.old_user_id;

-- 6.13: Update loyalty_redemptions (processed_by)
UPDATE loyalty_redemptions lr
SET processed_by = um.new_user_id
FROM user_mapping_temp um
WHERE lr.processed_by = um.old_user_id;

-- 6.14: Update loyalty_redemptions (refunded_by)
UPDATE loyalty_redemptions lr
SET refunded_by = um.new_user_id
FROM user_mapping_temp um
WHERE lr.refunded_by = um.old_user_id;

-- 6.15: Update loyalty_transactions
UPDATE loyalty_transactions lt 
SET processed_by = um.new_user_id
FROM user_mapping_temp um
WHERE lt.processed_by = um.old_user_id;

-- 6.16: Update price_history
UPDATE price_history ph 
SET changed_by = um.new_user_id
FROM user_mapping_temp um
WHERE ph.changed_by = um.old_user_id;

-- 6.17: Update purchase_returns
UPDATE purchase_returns pr 
SET processed_by = um.new_user_id
FROM user_mapping_temp um
WHERE pr.processed_by = um.old_user_id;

-- 6.18: Update regulatory_licenses
UPDATE regulatory_licenses rl 
SET verified_by = um.new_user_id
FROM user_mapping_temp um
WHERE rl.verified_by = um.old_user_id;

-- SECTION 7: Drop foreign key constraints referencing users table
-- Run each ALTER TABLE separately

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

-- SECTION 8: Add new foreign key constraints to org_users
-- Run each ALTER TABLE separately

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

-- SECTION 9: Final verification before dropping users table
-- Check if any references to users table remain
SELECT * FROM find_referencing_tables('users');

-- SECTION 10: Drop the users table (ONLY after verifying section 9 returns no rows)
-- CAUTION: Only run this after confirming all updates are successful
DROP TABLE IF EXISTS users CASCADE;

-- SECTION 11: Clean up
DROP TABLE IF EXISTS user_mapping_temp;
DROP FUNCTION IF EXISTS find_referencing_tables(text);

-- Log the migration
INSERT INTO activity_log (org_id, activity_type, activity_description, created_at)
SELECT 
    org_id,
    'USER_MIGRATION',
    'Migrated all user references from users to org_users table',
    CURRENT_TIMESTAMP
FROM organizations
LIMIT 1;