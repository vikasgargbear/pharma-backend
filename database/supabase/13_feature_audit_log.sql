-- =============================================
-- FEATURE CHANGE AUDIT LOG
-- =============================================
-- Version: 1.0
-- Description: Audit trail for organization feature changes
-- Deploy Order: After core schema (can be run anytime)
-- =============================================

-- =============================================
-- FEATURE CHANGE LOG TABLE
-- =============================================
-- Tracks all changes to organization features and settings
CREATE TABLE IF NOT EXISTS feature_change_log (
    log_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    changed_by INTEGER REFERENCES org_users(user_id),
    
    -- What changed
    change_type TEXT NOT NULL CHECK (change_type IN ('features', 'settings', 'limits', 'profile')),
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[], -- Array of field names that changed
    
    -- Context
    change_reason TEXT,
    change_source TEXT DEFAULT 'web', -- web, api, admin, system
    ip_address INET,
    user_agent TEXT,
    
    -- Timestamp
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for quick lookups
CREATE INDEX idx_feature_change_log_org_id ON feature_change_log(org_id);
CREATE INDEX idx_feature_change_log_changed_at ON feature_change_log(changed_at DESC);
CREATE INDEX idx_feature_change_log_change_type ON feature_change_log(change_type);

-- =============================================
-- TRIGGER FUNCTION FOR AUTOMATIC LOGGING
-- =============================================
CREATE OR REPLACE FUNCTION log_organization_changes()
RETURNS TRIGGER AS $$
DECLARE
    v_changed_fields TEXT[];
    v_old_values JSONB;
    v_new_values JSONB;
    v_user_id INTEGER;
BEGIN
    -- Only log on UPDATE
    IF TG_OP != 'UPDATE' THEN
        RETURN NEW;
    END IF;
    
    -- Get current user from context (set by application)
    v_user_id := current_setting('app.current_user_id', true)::INTEGER;
    
    -- Check what changed
    v_changed_fields := ARRAY[]::TEXT[];
    
    -- Check features_enabled changes
    IF OLD.features_enabled IS DISTINCT FROM NEW.features_enabled THEN
        v_changed_fields := array_append(v_changed_fields, 'features_enabled');
        
        -- Convert arrays to JSONB for storage
        v_old_values := to_jsonb(OLD.features_enabled);
        v_new_values := to_jsonb(NEW.features_enabled);
        
        INSERT INTO feature_change_log (
            org_id, changed_by, change_type, 
            old_values, new_values, changed_fields,
            change_source
        ) VALUES (
            NEW.org_id, v_user_id, 'features',
            v_old_values, v_new_values, v_changed_fields,
            COALESCE(current_setting('app.change_source', true), 'system')
        );
    END IF;
    
    -- Check business_settings changes
    IF OLD.business_settings IS DISTINCT FROM NEW.business_settings THEN
        v_changed_fields := ARRAY[]::TEXT[];
        
        -- Find which settings changed
        SELECT array_agg(key) INTO v_changed_fields
        FROM (
            SELECT key FROM jsonb_each(OLD.business_settings)
            EXCEPT
            SELECT key FROM jsonb_each(NEW.business_settings)
            UNION
            SELECT key FROM jsonb_each(NEW.business_settings)
            EXCEPT
            SELECT key FROM jsonb_each(OLD.business_settings)
            UNION
            SELECT key FROM jsonb_each(OLD.business_settings) o
            JOIN jsonb_each(NEW.business_settings) n USING (key)
            WHERE o.value IS DISTINCT FROM n.value
        ) changes;
        
        IF array_length(v_changed_fields, 1) > 0 THEN
            INSERT INTO feature_change_log (
                org_id, changed_by, change_type, 
                old_values, new_values, changed_fields,
                change_source
            ) VALUES (
                NEW.org_id, v_user_id, 'settings',
                OLD.business_settings, NEW.business_settings, v_changed_fields,
                COALESCE(current_setting('app.change_source', true), 'system')
            );
        END IF;
    END IF;
    
    -- Check limit changes
    IF OLD.max_users != NEW.max_users OR 
       OLD.max_products != NEW.max_products OR
       OLD.max_customers != NEW.max_customers OR
       OLD.max_monthly_transactions != NEW.max_monthly_transactions THEN
        
        v_old_values := jsonb_build_object(
            'max_users', OLD.max_users,
            'max_products', OLD.max_products,
            'max_customers', OLD.max_customers,
            'max_monthly_transactions', OLD.max_monthly_transactions
        );
        
        v_new_values := jsonb_build_object(
            'max_users', NEW.max_users,
            'max_products', NEW.max_products,
            'max_customers', NEW.max_customers,
            'max_monthly_transactions', NEW.max_monthly_transactions
        );
        
        INSERT INTO feature_change_log (
            org_id, changed_by, change_type, 
            old_values, new_values,
            change_source
        ) VALUES (
            NEW.org_id, v_user_id, 'limits',
            v_old_values, v_new_values,
            COALESCE(current_setting('app.change_source', true), 'system')
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- ATTACH TRIGGER TO ORGANIZATIONS TABLE
-- =============================================
DROP TRIGGER IF EXISTS log_organization_changes_trigger ON organizations;
CREATE TRIGGER log_organization_changes_trigger
    AFTER UPDATE ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION log_organization_changes();

-- =============================================
-- HELPER FUNCTIONS
-- =============================================

-- Function to manually log feature changes (for API use)
CREATE OR REPLACE FUNCTION log_feature_change(
    p_org_id UUID,
    p_change_type TEXT,
    p_old_values JSONB,
    p_new_values JSONB,
    p_reason TEXT DEFAULT NULL,
    p_user_id INTEGER DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO feature_change_log (
        org_id, changed_by, change_type,
        old_values, new_values, change_reason,
        change_source
    ) VALUES (
        p_org_id, p_user_id, p_change_type,
        p_old_values, p_new_values, p_reason,
        'api'
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get feature change history
CREATE OR REPLACE FUNCTION get_feature_history(
    p_org_id UUID,
    p_days INTEGER DEFAULT 30
) RETURNS TABLE (
    change_date TIMESTAMP WITH TIME ZONE,
    change_type TEXT,
    changed_by_name TEXT,
    changes JSONB,
    reason TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        fcl.changed_at,
        fcl.change_type,
        ou.full_name,
        jsonb_build_object(
            'old', fcl.old_values,
            'new', fcl.new_values,
            'fields', fcl.changed_fields
        ),
        fcl.change_reason
    FROM feature_change_log fcl
    LEFT JOIN org_users ou ON fcl.changed_by = ou.user_id
    WHERE fcl.org_id = p_org_id
        AND fcl.changed_at > CURRENT_TIMESTAMP - (p_days || ' days')::INTERVAL
    ORDER BY fcl.changed_at DESC;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- USAGE EXAMPLES
-- =============================================

-- Example: Setting context before making changes (in your API)
/*
-- In your Python API:
db.execute(text("SET LOCAL app.current_user_id = :user_id"), {"user_id": current_user.id})
db.execute(text("SET LOCAL app.change_source = 'web'"))

-- Then update organization
org.business_settings = new_settings
db.commit()
*/

-- Example: Manual logging
/*
SELECT log_feature_change(
    '12de5e22-eee7-4d25-b3a7-d16d01c6170f'::uuid,
    'features',
    '{"allowNegativeStock": false}'::jsonb,
    '{"allowNegativeStock": true}'::jsonb,
    'Enabled for emergency medicine sales',
    1
);
*/

-- Example: View recent changes
/*
SELECT * FROM get_feature_history('12de5e22-eee7-4d25-b3a7-d16d01c6170f'::uuid, 90);
*/

-- =============================================
-- GRANT PERMISSIONS
-- =============================================
-- Grant read access to authenticated users for their own org
GRANT SELECT ON feature_change_log TO authenticated;

-- RLS Policy
ALTER TABLE feature_change_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their organization's audit log"
    ON feature_change_log
    FOR SELECT
    TO authenticated
    USING (org_id IN (
        SELECT org_id FROM org_users 
        WHERE user_id = current_setting('app.current_user_id', true)::INTEGER
    ));

-- =============================================
-- VERIFICATION
-- =============================================
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=============================================';
    RAISE NOTICE 'FEATURE AUDIT LOG SETUP COMPLETE';
    RAISE NOTICE '=============================================';
    RAISE NOTICE '✓ Feature change log table created';
    RAISE NOTICE '✓ Automatic logging trigger attached';
    RAISE NOTICE '✓ Helper functions created';
    RAISE NOTICE '✓ RLS policies configured';
    RAISE NOTICE '';
    RAISE NOTICE 'To use in your API:';
    RAISE NOTICE '1. Set app.current_user_id before updates';
    RAISE NOTICE '2. Changes will be automatically logged';
    RAISE NOTICE '3. Use get_feature_history() to view changes';
    RAISE NOTICE '=============================================';
END $$;