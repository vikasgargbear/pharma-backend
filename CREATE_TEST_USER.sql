-- Create a test user in the org_users table
-- Run this in your Supabase SQL editor

-- First, check if organizations exist
DO $$
DECLARE
    v_org_id UUID;
BEGIN
    -- Try to get the first active organization
    SELECT org_id INTO v_org_id
    FROM organizations
    WHERE is_active = TRUE
    LIMIT 1;
    
    IF v_org_id IS NULL THEN
        -- Create a default organization if none exists
        INSERT INTO organizations (
            org_name, 
            business_type, 
            primary_contact_name,
            primary_email,
            primary_phone,
            plan_type,
            is_active
        ) VALUES (
            'Default Pharmacy',
            'pharmaceutical',
            'Admin',
            'admin@pharmacy.com',
            '+91-9999999999',
            'starter',
            TRUE
        ) RETURNING org_id INTO v_org_id;
        
        RAISE NOTICE 'Created new organization with ID: %', v_org_id;
    ELSE
        RAISE NOTICE 'Using existing organization with ID: %', v_org_id;
    END IF;
    
    -- Now create admin user for this organization
    INSERT INTO org_users (
        org_id,
        full_name,
        email,
        phone,
        employee_id,
        password_hash,
        role,
        permissions,
        department,
        can_view_reports,
        can_modify_prices,
        can_approve_discounts,
        discount_limit_percent,
        is_active,
        email_verified
    ) VALUES (
        v_org_id,
        'Admin User',
        'admin@pharmacy.com',
        '+91-9999999999',
        'EMP001',
        '$2b$10$YourHashHere', -- In production, use proper bcrypt hash
        'admin',
        jsonb_build_object(
            'modules', ARRAY['sales', 'purchase', 'inventory', 'payment', 'reports', 'master', 'gst', 'returns', 'ledger', 'notes'],
            'sales', jsonb_build_object('create', true, 'view', true, 'edit', true, 'delete', true),
            'purchase', jsonb_build_object('create', true, 'view', true, 'edit', true, 'delete', true),
            'inventory', jsonb_build_object('create', true, 'view', true, 'edit', true, 'delete', true),
            'payment', jsonb_build_object('create', true, 'view', true, 'edit', true, 'delete', true),
            'reports', jsonb_build_object('create', true, 'view', true, 'edit', true, 'delete', true),
            'master', jsonb_build_object('create', true, 'view', true, 'edit', true, 'delete', true)
        ),
        'Management',
        TRUE,
        TRUE,
        TRUE,
        100,
        TRUE,
        TRUE
    ) ON CONFLICT (org_id, email) DO UPDATE SET
        updated_at = CURRENT_TIMESTAMP;
    
    -- Create a manager user
    INSERT INTO org_users (
        org_id,
        full_name,
        email,
        phone,
        employee_id,
        password_hash,
        role,
        permissions,
        department,
        can_view_reports,
        can_modify_prices,
        can_approve_discounts,
        discount_limit_percent,
        is_active,
        email_verified
    ) VALUES (
        v_org_id,
        'Sales Manager',
        'manager@pharmacy.com',
        '+91-9999999998',
        'EMP002',
        '$2b$10$YourHashHere', -- In production, use proper bcrypt hash
        'manager',
        jsonb_build_object(
            'modules', ARRAY['sales', 'payment', 'reports', 'returns'],
            'sales', jsonb_build_object('create', true, 'view', true, 'edit', true, 'delete', false),
            'payment', jsonb_build_object('create', true, 'view', true, 'edit', true, 'delete', false),
            'reports', jsonb_build_object('create', false, 'view', true, 'edit', false, 'delete', false),
            'returns', jsonb_build_object('create', true, 'view', true, 'edit', true, 'delete', false)
        ),
        'Sales',
        TRUE,
        TRUE,
        TRUE,
        20,
        TRUE,
        TRUE
    ) ON CONFLICT (org_id, email) DO UPDATE SET
        updated_at = CURRENT_TIMESTAMP;
    
    -- Create a billing user
    INSERT INTO org_users (
        org_id,
        full_name,
        email,
        phone,
        employee_id,
        password_hash,
        role,
        permissions,
        department,
        can_view_reports,
        can_modify_prices,
        can_approve_discounts,
        discount_limit_percent,
        is_active,
        email_verified
    ) VALUES (
        v_org_id,
        'Billing Staff',
        'billing@pharmacy.com',
        '+91-9999999997',
        'EMP003',
        '$2b$10$YourHashHere', -- In production, use proper bcrypt hash
        'billing',
        jsonb_build_object(
            'modules', ARRAY['sales', 'payment'],
            'sales', jsonb_build_object('create', true, 'view', true, 'edit', false, 'delete', false),
            'payment', jsonb_build_object('create', true, 'view', true, 'edit', false, 'delete', false)
        ),
        'Billing',
        FALSE,
        FALSE,
        FALSE,
        0,
        TRUE,
        TRUE
    ) ON CONFLICT (org_id, email) DO UPDATE SET
        updated_at = CURRENT_TIMESTAMP;
        
    RAISE NOTICE 'Successfully created test users!';
END $$;

-- Verify the users were created
SELECT 
    user_id,
    full_name,
    email,
    role,
    department,
    is_active,
    created_at
FROM org_users
ORDER BY created_at DESC;