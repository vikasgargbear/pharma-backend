-- Connect org_users to Supabase Authentication
-- Run this after creating users in Supabase Auth Dashboard

-- 1. First, create users in Supabase Dashboard > Authentication > Users
-- 2. Then run this to link them to org_users

-- Update org_users with auth_uid from Supabase Auth
UPDATE org_users 
SET auth_uid = (
    SELECT id 
    FROM auth.users 
    WHERE email = org_users.email
)
WHERE email IN (
    SELECT email FROM auth.users
);

-- Verify the connection
SELECT 
    ou.user_id,
    ou.full_name,
    ou.email,
    ou.role,
    ou.auth_uid,
    au.email as auth_email,
    au.created_at as auth_created
FROM org_users ou
LEFT JOIN auth.users au ON ou.auth_uid = au.id
ORDER BY ou.created_at DESC;

-- Create a function to automatically link new auth users to org_users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
DECLARE
    default_org_id uuid;
BEGIN
    -- Get the default organization (or first active one)
    SELECT org_id INTO default_org_id
    FROM organizations
    WHERE is_active = true
    LIMIT 1;

    -- Check if org_user already exists for this email
    IF NOT EXISTS (
        SELECT 1 FROM org_users 
        WHERE email = NEW.email 
        AND org_id = default_org_id
    ) THEN
        -- Create new org_user linked to auth user
        INSERT INTO org_users (
            org_id,
            auth_uid,
            email,
            full_name,
            role,
            password_hash,
            is_active,
            email_verified
        ) VALUES (
            default_org_id,
            NEW.id,
            NEW.email,
            COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)),
            COALESCE(NEW.raw_user_meta_data->>'role', 'billing'),
            'supabase_auth', -- placeholder since Supabase handles auth
            true,
            NEW.email_confirmed_at IS NOT NULL
        );
    ELSE
        -- Update existing org_user with auth_uid
        UPDATE org_users
        SET 
            auth_uid = NEW.id,
            email_verified = NEW.email_confirmed_at IS NOT NULL,
            updated_at = now()
        WHERE email = NEW.email
        AND org_id = default_org_id
        AND auth_uid IS NULL;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for new Supabase auth users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Note: After running this, you need to:
-- 1. Create users in Supabase Dashboard with same emails
-- 2. Or use Supabase Auth signup flow in your app