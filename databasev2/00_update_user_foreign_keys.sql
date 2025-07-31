-- =====================================================
-- SCRIPT 00: Update User Foreign Keys
-- Purpose: Migrate all references from users to org_users
-- CRITICAL: Must run BEFORE any other migration scripts!
-- =====================================================

-- Create helper function to find all foreign keys
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

BEGIN;

-- Step 1: Create mapping between users and org_users
CREATE TEMP TABLE user_mapping AS
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
    oud.org_id
FROM user_data ud
LEFT JOIN org_user_data oud ON ud.email = oud.email;

-- Log unmapped users
DO $$
DECLARE
    unmapped_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO unmapped_count 
    FROM user_mapping WHERE new_user_id IS NULL;
    
    IF unmapped_count > 0 THEN
        RAISE NOTICE '% users have no corresponding org_users entry', unmapped_count;
        
        -- Create org_users entries for unmapped users
        INSERT INTO org_users (org_id, full_name, email, role, created_at)
        SELECT 
            (SELECT org_id FROM organizations LIMIT 1), -- Default org
            COALESCE(u.name, u.email),
            u.email,
            COALESCE(u.role, 'user'),
            u.created_at
        FROM users u
        WHERE u.email NOT IN (SELECT email FROM org_users);
        
        -- Update mapping
        UPDATE user_mapping um
        SET new_user_id = ou.user_id
        FROM org_users ou
        WHERE um.email = ou.email
        AND um.new_user_id IS NULL;
    END IF;
END $$;

-- Step 2: Update all foreign key references

-- audit_logs
ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey;
UPDATE audit_logs al 
SET user_id = um.new_user_id
FROM user_mapping um
WHERE al.user_id = um.old_user_id;
ALTER TABLE audit_logs 
    ADD CONSTRAINT audit_logs_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES org_users(user_id);

-- batch_locations
ALTER TABLE batch_locations DROP CONSTRAINT IF EXISTS batch_locations_moved_by_fkey;
UPDATE batch_locations bl 
SET moved_by = um.new_user_id
FROM user_mapping um
WHERE bl.moved_by = um.old_user_id;
ALTER TABLE batch_locations 
    ADD CONSTRAINT batch_locations_moved_by_fkey 
    FOREIGN KEY (moved_by) REFERENCES org_users(user_id);

-- challan_tracking
ALTER TABLE challan_tracking DROP CONSTRAINT IF EXISTS challan_tracking_updated_by_fkey;
UPDATE challan_tracking ct 
SET updated_by = um.new_user_id
FROM user_mapping um
WHERE ct.updated_by = um.old_user_id;
ALTER TABLE challan_tracking 
    ADD CONSTRAINT challan_tracking_updated_by_fkey 
    FOREIGN KEY (updated_by) REFERENCES org_users(user_id);

-- challans (prepared_by and dispatched_by)
ALTER TABLE challans DROP CONSTRAINT IF EXISTS challans_prepared_by_fkey;
ALTER TABLE challans DROP CONSTRAINT IF EXISTS challans_dispatched_by_fkey;
UPDATE challans c
SET 
    prepared_by = um1.new_user_id,
    dispatched_by = um2.new_user_id
FROM user_mapping um1, user_mapping um2
WHERE c.prepared_by = um1.old_user_id
AND c.dispatched_by = um2.old_user_id;
ALTER TABLE challans 
    ADD CONSTRAINT challans_prepared_by_fkey 
    FOREIGN KEY (prepared_by) REFERENCES org_users(user_id);
ALTER TABLE challans 
    ADD CONSTRAINT challans_dispatched_by_fkey 
    FOREIGN KEY (dispatched_by) REFERENCES org_users(user_id);

-- compliance_checks
ALTER TABLE compliance_checks DROP CONSTRAINT IF EXISTS compliance_checks_resolved_by_fkey;
UPDATE compliance_checks cc 
SET resolved_by = um.new_user_id
FROM user_mapping um
WHERE cc.resolved_by = um.old_user_id;
ALTER TABLE compliance_checks 
    ADD CONSTRAINT compliance_checks_resolved_by_fkey 
    FOREIGN KEY (resolved_by) REFERENCES org_users(user_id);

-- customer_credit_notes
ALTER TABLE customer_credit_notes DROP CONSTRAINT IF EXISTS customer_credit_notes_approved_by_fkey;
UPDATE customer_credit_notes ccn 
SET approved_by = um.new_user_id
FROM user_mapping um
WHERE ccn.approved_by = um.old_user_id;
ALTER TABLE customer_credit_notes 
    ADD CONSTRAINT customer_credit_notes_approved_by_fkey 
    FOREIGN KEY (approved_by) REFERENCES org_users(user_id);

-- file_uploads
ALTER TABLE file_uploads DROP CONSTRAINT IF EXISTS file_uploads_uploaded_by_fkey;
ALTER TABLE file_uploads DROP CONSTRAINT IF EXISTS file_uploads_verified_by_fkey;
UPDATE file_uploads fu
SET 
    uploaded_by = um1.new_user_id,
    verified_by = um2.new_user_id
FROM user_mapping um1, user_mapping um2
WHERE fu.uploaded_by = um1.old_user_id
AND fu.verified_by = um2.old_user_id;
ALTER TABLE file_uploads 
    ADD CONSTRAINT file_uploads_uploaded_by_fkey 
    FOREIGN KEY (uploaded_by) REFERENCES org_users(user_id);
ALTER TABLE file_uploads 
    ADD CONSTRAINT file_uploads_verified_by_fkey 
    FOREIGN KEY (verified_by) REFERENCES org_users(user_id);

-- inventory_transactions
ALTER TABLE inventory_transactions DROP CONSTRAINT IF EXISTS inventory_transactions_performed_by_fkey;
UPDATE inventory_transactions it 
SET performed_by = um.new_user_id
FROM user_mapping um
WHERE it.performed_by = um.old_user_id;
ALTER TABLE inventory_transactions 
    ADD CONSTRAINT inventory_transactions_performed_by_fkey 
    FOREIGN KEY (performed_by) REFERENCES org_users(user_id);

-- license_documents
ALTER TABLE license_documents DROP CONSTRAINT IF EXISTS license_documents_uploaded_by_fkey;
ALTER TABLE license_documents DROP CONSTRAINT IF EXISTS license_documents_verified_by_fkey;
UPDATE license_documents ld
SET 
    uploaded_by = um1.new_user_id,
    verified_by = um2.new_user_id
FROM user_mapping um1, user_mapping um2
WHERE ld.uploaded_by = um1.old_user_id
AND ld.verified_by = um2.old_user_id;
ALTER TABLE license_documents 
    ADD CONSTRAINT license_documents_uploaded_by_fkey 
    FOREIGN KEY (uploaded_by) REFERENCES org_users(user_id);
ALTER TABLE license_documents 
    ADD CONSTRAINT license_documents_verified_by_fkey 
    FOREIGN KEY (verified_by) REFERENCES org_users(user_id);

-- loyalty_redemptions
ALTER TABLE loyalty_redemptions DROP CONSTRAINT IF EXISTS loyalty_redemptions_processed_by_fkey;
ALTER TABLE loyalty_redemptions DROP CONSTRAINT IF EXISTS loyalty_redemptions_refunded_by_fkey;
UPDATE loyalty_redemptions lr
SET 
    processed_by = um1.new_user_id,
    refunded_by = um2.new_user_id
FROM user_mapping um1, user_mapping um2
WHERE lr.processed_by = um1.old_user_id
AND lr.refunded_by = um2.old_user_id;
ALTER TABLE loyalty_redemptions 
    ADD CONSTRAINT loyalty_redemptions_processed_by_fkey 
    FOREIGN KEY (processed_by) REFERENCES org_users(user_id);
ALTER TABLE loyalty_redemptions 
    ADD CONSTRAINT loyalty_redemptions_refunded_by_fkey 
    FOREIGN KEY (refunded_by) REFERENCES org_users(user_id);

-- loyalty_transactions
ALTER TABLE loyalty_transactions DROP CONSTRAINT IF EXISTS loyalty_transactions_processed_by_fkey;
UPDATE loyalty_transactions lt 
SET processed_by = um.new_user_id
FROM user_mapping um
WHERE lt.processed_by = um.old_user_id;
ALTER TABLE loyalty_transactions 
    ADD CONSTRAINT loyalty_transactions_processed_by_fkey 
    FOREIGN KEY (processed_by) REFERENCES org_users(user_id);

-- price_history
ALTER TABLE price_history DROP CONSTRAINT IF EXISTS price_history_changed_by_fkey;
UPDATE price_history ph 
SET changed_by = um.new_user_id
FROM user_mapping um
WHERE ph.changed_by = um.old_user_id;
ALTER TABLE price_history 
    ADD CONSTRAINT price_history_changed_by_fkey 
    FOREIGN KEY (changed_by) REFERENCES org_users(user_id);

-- purchase_returns
ALTER TABLE purchase_returns DROP CONSTRAINT IF EXISTS purchase_returns_processed_by_fkey;
UPDATE purchase_returns pr 
SET processed_by = um.new_user_id
FROM user_mapping um
WHERE pr.processed_by = um.old_user_id;
ALTER TABLE purchase_returns 
    ADD CONSTRAINT purchase_returns_processed_by_fkey 
    FOREIGN KEY (processed_by) REFERENCES org_users(user_id);

-- regulatory_licenses
ALTER TABLE regulatory_licenses DROP CONSTRAINT IF EXISTS regulatory_licenses_verified_by_fkey;
UPDATE regulatory_licenses rl 
SET verified_by = um.new_user_id
FROM user_mapping um
WHERE rl.verified_by = um.old_user_id;
ALTER TABLE regulatory_licenses 
    ADD CONSTRAINT regulatory_licenses_verified_by_fkey 
    FOREIGN KEY (verified_by) REFERENCES org_users(user_id);

-- uploaded_files (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'uploaded_files') THEN
        ALTER TABLE uploaded_files DROP CONSTRAINT IF EXISTS uploaded_files_uploaded_by_fkey;
        UPDATE uploaded_files uf 
        SET uploaded_by = um.new_user_id
        FROM user_mapping um
        WHERE uf.uploaded_by = um.old_user_id;
        ALTER TABLE uploaded_files 
            ADD CONSTRAINT uploaded_files_uploaded_by_fkey 
            FOREIGN KEY (uploaded_by) REFERENCES org_users(user_id);
    END IF;
END $$;

-- Step 3: Verify all updates
DO $$
DECLARE
    remaining_refs INTEGER;
    ref_record RECORD;
BEGIN
    -- Check for any remaining references to users table
    FOR ref_record IN 
        SELECT * FROM find_referencing_tables('users')
    LOOP
        RAISE WARNING 'Table % still has constraint % referencing users table', 
            ref_record.source_table, ref_record.constraint_name;
    END LOOP;
    
    -- Count successful mappings
    SELECT COUNT(*) INTO remaining_refs
    FROM user_mapping WHERE new_user_id IS NULL;
    
    IF remaining_refs > 0 THEN
        RAISE EXCEPTION '% users could not be mapped to org_users', remaining_refs;
    END IF;
END $$;

-- Step 4: Now safe to drop users table
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE; -- Also drop sessions

-- Log the migration
INSERT INTO activity_log (org_id, activity_type, activity_description, created_at)
SELECT 
    org_id,
    'USER_MIGRATION',
    'Migrated all user references from users to org_users table',
    CURRENT_TIMESTAMP
FROM organizations
LIMIT 1;

COMMIT;

-- Drop the helper function
DROP FUNCTION IF EXISTS find_referencing_tables(text);