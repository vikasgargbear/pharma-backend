-- =============================================
-- SUPABASE PREPARATION SCRIPT
-- =============================================
-- Run this FIRST before deploying to Supabase
-- This handles Supabase-specific requirements
-- =============================================

-- =============================================
-- COMPATIBILITY FUNCTIONS
-- =============================================

-- Create app settings function for compatibility
CREATE OR REPLACE FUNCTION current_setting_or_null(setting_name text)
RETURNS text AS $$
BEGIN
    RETURN current_setting(setting_name, true);
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- AUTH CONTEXT FUNCTIONS
-- =============================================

-- Override current_org_id to work with Supabase auth
CREATE OR REPLACE FUNCTION current_org_id() 
RETURNS UUID AS $$
BEGIN
    -- Try JWT claim first (Supabase auth)
    IF auth.jwt() IS NOT NULL AND auth.jwt() ->> 'org_id' IS NOT NULL THEN
        RETURN (auth.jwt() ->> 'org_id')::UUID;
    END IF;
    
    -- Try to get from user's organization
    IF auth.uid() IS NOT NULL THEN
        RETURN (
            SELECT org_id 
            FROM org_users 
            WHERE auth_uid = auth.uid() 
            LIMIT 1
        );
    END IF;
    
    -- Fallback to session setting (for testing/migration)
    RETURN COALESCE(
        current_setting('app.current_org_id', true)::UUID,
        '00000000-0000-0000-0000-000000000000'::UUID
    );
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Override current_user_id to work with Supabase auth
CREATE OR REPLACE FUNCTION current_user_id()
RETURNS INTEGER AS $$
DECLARE
    v_user_id INTEGER;
BEGIN
    -- Try to get from org_users table using auth.uid()
    IF auth.uid() IS NOT NULL THEN
        SELECT user_id INTO v_user_id
        FROM org_users
        WHERE auth_uid = auth.uid()
        LIMIT 1;
        
        IF v_user_id IS NOT NULL THEN
            RETURN v_user_id;
        END IF;
    END IF;
    
    -- Fallback to session setting (for testing)
    RETURN current_setting('app.current_user_id', true)::INTEGER;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Override current_user_role to work with Supabase auth
CREATE OR REPLACE FUNCTION current_user_role() 
RETURNS TEXT AS $$
DECLARE
    v_role TEXT;
BEGIN
    -- Get from JWT claim
    v_role := auth.jwt() ->> 'user_role';
    IF v_role IS NOT NULL THEN
        RETURN v_role;
    END IF;
    
    -- Get from org_users table
    IF auth.uid() IS NOT NULL THEN
        SELECT role INTO v_role
        FROM org_users
        WHERE auth_uid = auth.uid()
        LIMIT 1;
        
        IF v_role IS NOT NULL THEN
            RETURN v_role;
        END IF;
    END IF;
    
    -- Fallback
    RETURN 'viewer';
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- =============================================
-- SUPABASE SPECIFIC TABLES
-- =============================================

-- Table to map Supabase auth users to organizations
CREATE TABLE IF NOT EXISTS auth_org_mapping (
    mapping_id SERIAL PRIMARY KEY,
    auth_uid UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    org_id UUID NOT NULL,
    user_id INTEGER,
    is_default BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(auth_uid, org_id)
);

-- Enable RLS on mapping table
ALTER TABLE auth_org_mapping ENABLE ROW LEVEL SECURITY;

-- Policy for auth mapping
CREATE POLICY auth_org_mapping_policy ON auth_org_mapping
    FOR ALL USING (auth_uid = auth.uid());

-- =============================================
-- MODIFY AUTH.USERS HANDLING
-- =============================================

-- Function to handle new Supabase auth users
CREATE OR REPLACE FUNCTION handle_new_auth_user()
RETURNS TRIGGER AS $$
DECLARE
    v_org_id UUID;
    v_user_id INTEGER;
    v_role TEXT;
BEGIN
    -- Get org_id from metadata
    v_org_id := COALESCE(
        (NEW.raw_user_meta_data->>'org_id')::UUID,
        (SELECT org_id FROM organizations WHERE is_active = TRUE LIMIT 1)
    );
    
    -- Get role from metadata
    v_role := COALESCE(
        NEW.raw_user_meta_data->>'role',
        'staff'
    );
    
    -- Check if user already exists
    SELECT user_id INTO v_user_id
    FROM org_users
    WHERE email = NEW.email
    AND org_id = v_org_id;
    
    IF v_user_id IS NULL THEN
        -- Create new org user
        INSERT INTO org_users (
            org_id, 
            auth_uid, 
            email, 
            full_name, 
            role, 
            password_hash,
            phone,
            is_active
        ) VALUES (
            v_org_id,
            NEW.id,
            NEW.email,
            COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)),
            v_role,
            'supabase_auth', -- Placeholder since Supabase handles auth
            NEW.raw_user_meta_data->>'phone',
            TRUE
        ) RETURNING user_id INTO v_user_id;
    ELSE
        -- Update auth_uid if not set
        UPDATE org_users
        SET auth_uid = NEW.id
        WHERE user_id = v_user_id
        AND auth_uid IS NULL;
    END IF;
    
    -- Create auth mapping
    INSERT INTO auth_org_mapping (auth_uid, org_id, user_id)
    VALUES (NEW.id, v_org_id, v_user_id)
    ON CONFLICT (auth_uid, org_id) DO NOTHING;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- API SECURITY FUNCTIONS
-- =============================================

-- Function to validate API access
CREATE OR REPLACE FUNCTION validate_api_access(
    required_permission TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_user RECORD;
BEGIN
    -- Must be authenticated
    IF auth.uid() IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Get user details
    SELECT * INTO v_user
    FROM org_users
    WHERE auth_uid = auth.uid()
    AND is_active = TRUE
    LIMIT 1;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Check specific permission if required
    IF required_permission IS NOT NULL THEN
        RETURN CASE required_permission
            WHEN 'manage_products' THEN v_user.role IN ('owner', 'admin', 'inventory_manager')
            WHEN 'manage_orders' THEN v_user.role IN ('owner', 'admin', 'sales_manager', 'sales_rep')
            WHEN 'view_reports' THEN v_user.can_view_reports
            WHEN 'manage_users' THEN v_user.role IN ('owner', 'admin')
            ELSE FALSE
        END;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- GRANT PERMISSIONS
-- =============================================

-- Grant necessary permissions to authenticated users
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- =============================================
-- ORGANIZATION CREATION FUNCTION
-- =============================================
-- This function needs to be available early for signup

-- Create new organization with owner
CREATE OR REPLACE FUNCTION create_organization(
    p_org_name TEXT,
    p_owner_name TEXT,
    p_owner_email TEXT,
    p_owner_phone TEXT,
    p_business_type TEXT DEFAULT 'pharmaceutical',
    p_plan_type TEXT DEFAULT 'starter'
) RETURNS JSONB AS $$
DECLARE
    v_org_id UUID;
    v_user_id INTEGER;
BEGIN
    -- Create organization
    INSERT INTO organizations (
        org_name, business_type, primary_contact_name, 
        primary_email, primary_phone, plan_type,
        is_active, subscription_status
    ) VALUES (
        p_org_name, p_business_type, p_owner_name,
        p_owner_email, p_owner_phone, p_plan_type,
        TRUE, 'active'
    ) RETURNING org_id INTO v_org_id;
    
    -- Create owner user (without auth_uid initially)
    INSERT INTO org_users (
        org_id, full_name, email, phone, role, password_hash,
        can_view_reports, can_modify_prices, can_approve_discounts,
        is_active
    ) VALUES (
        v_org_id, p_owner_name, p_owner_email, p_owner_phone, 'owner', 'supabase_auth',
        TRUE, TRUE, TRUE, TRUE
    ) RETURNING user_id INTO v_user_id;
    
    -- Create default settings
    INSERT INTO org_settings (org_id, setting_key, setting_value) VALUES
    (v_org_id, 'default_currency', 'INR'),
    (v_org_id, 'gst_enabled', 'true'),
    (v_org_id, 'multi_branch', 'false'),
    (v_org_id, 'prescription_required', 'true');
    
    RETURN jsonb_build_object(
        'org_id', v_org_id,
        'user_id', v_user_id,
        'message', 'Organization created successfully'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant specific function access to anon (for signup)
GRANT EXECUTE ON FUNCTION create_organization TO anon;

-- =============================================
-- SUCCESS MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
SUPABASE PREPARATION COMPLETED
=============================================
✓ Compatibility functions created
✓ Auth context functions created
✓ Auth mapping table created
✓ API security functions created
✓ Permissions granted

Ready to deploy main schema files!
';
END $$;