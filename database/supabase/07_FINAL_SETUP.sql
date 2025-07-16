-- =============================================
-- 07_FINAL_SETUP.sql
-- =============================================
-- Run this AFTER all schema files (00-06) for a complete setup
-- This consolidates all fixes and lessons learned
-- =============================================

-- STEP 1: Create your organization
INSERT INTO organizations (
    org_name,
    business_type,
    company_registration_number,
    pan_number,
    gst_number,
    drug_license_number,
    primary_contact_name,
    primary_email,
    primary_phone,
    business_address,
    plan_type,
    subscription_status,
    max_users,
    max_products,
    max_customers,
    max_monthly_transactions,
    business_settings,
    features_enabled,
    is_active,
    onboarding_completed
) VALUES (
    'Aaso Pharmaceuticals Pvt Ltd',
    'pharmaceutical',
    'U24239MH2020PTC123456',
    'AASOP1234F',
    '27AASOP1234F1Z5',
    'MH-DL-2024-001234',
    'Vikas Garg',
    'vikasgarg304@gmail.com',
    '+91-9876543210',
    jsonb_build_object(
        'street', '123 Pharma Park, Andheri East',
        'city', 'Mumbai',
        'state', 'Maharashtra',
        'postal_code', '400069',
        'country', 'India'
    ),
    'professional',
    'active',
    50,
    10000,
    10000,
    5000,
    jsonb_build_object(
        'sms_enabled', true,
        'whatsapp_enabled', true,
        'email_enabled', true,
        'invoice_prefix', 'INV',
        'current_invoice_number', 1001,
        'fiscal_year_start', '2024-04-01',
        'currency_code', 'INR',
        'timezone', 'Asia/Kolkata',
        'locale', 'en-IN',
        'business_hours', jsonb_build_object(
            'monday', '09:00-18:00',
            'tuesday', '09:00-18:00',
            'wednesday', '09:00-18:00',
            'thursday', '09:00-18:00',
            'friday', '09:00-18:00',
            'saturday', '09:00-14:00',
            'sunday', 'closed'
        )
    ),
    ARRAY['basic_erp', 'inventory', 'billing', 'gst', 'reports', 'sms', 'whatsapp'],
    true,
    true
) ON CONFLICT (gst_number) DO NOTHING;

-- STEP 2: Link admin user to organization
-- First, create admin user in Supabase Dashboard, then run this
UPDATE org_users 
SET org_id = (SELECT org_id FROM organizations WHERE org_name = 'Aaso Pharmaceuticals Pvt Ltd')
WHERE email = 'vikasgarg304@gmail.com';

-- STEP 3: Create RLS helper function
CREATE OR REPLACE FUNCTION get_auth_user_org_id()
RETURNS UUID AS $$
    SELECT org_id 
    FROM org_users 
    WHERE auth_uid = auth.uid()
    AND is_active = TRUE
    LIMIT 1;
$$ LANGUAGE sql SECURITY DEFINER STABLE;

GRANT EXECUTE ON FUNCTION get_auth_user_org_id() TO authenticated;
GRANT EXECUTE ON FUNCTION get_auth_user_org_id() TO anon;

-- STEP 4: Fix RLS policies (handles the issues we discovered)
-- Drop any existing problematic policies
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT tablename, policyname 
        FROM pg_policies 
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I', r.policyname, r.tablename);
    END LOOP;
END $$;

-- Create working policies for core tables
CREATE POLICY "organizations_policy" ON organizations
    FOR ALL USING (org_id = get_auth_user_org_id());

CREATE POLICY "org_users_policy" ON org_users
    FOR ALL USING (org_id = get_auth_user_org_id());

CREATE POLICY "products_policy" ON products
    FOR ALL USING (org_id = get_auth_user_org_id());

CREATE POLICY "customers_policy" ON customers
    FOR ALL USING (org_id = get_auth_user_org_id());

CREATE POLICY "orders_policy" ON orders
    FOR ALL USING (org_id = get_auth_user_org_id());

CREATE POLICY "batches_policy" ON batches
    FOR ALL USING (org_id = get_auth_user_org_id());

-- CRITICAL: Allow anon users to read organizations (fixes frontend issue)
CREATE POLICY "anon_read_orgs" ON organizations
    FOR SELECT 
    USING (true);

-- STEP 5: Add Indian GST tax setup
INSERT INTO gst_tax_setup (org_id, hsn_code, product_category, cgst_rate, sgst_rate, igst_rate, description)
SELECT 
    org_id,
    hsn_code,
    category,
    cgst,
    sgst,
    igst,
    description
FROM (
    VALUES 
        ('3004', 'Medicines', 6.0, 6.0, 12.0, 'Medicines and pharmaceutical preparations'),
        ('3005', 'Surgical', 6.0, 6.0, 12.0, 'Surgical dressings and medical supplies'),
        ('3006', 'Blood Products', 2.5, 2.5, 5.0, 'Blood grouping reagents'),
        ('2106', 'Food Supplements', 9.0, 9.0, 18.0, 'Food supplements and nutraceuticals'),
        ('3003', 'Ayurvedic', 6.0, 6.0, 12.0, 'Ayurvedic medicinal preparations')
) AS tax_data(hsn_code, category, cgst, sgst, igst, description)
CROSS JOIN organizations
WHERE org_name = 'Aaso Pharmaceuticals Pvt Ltd'
ON CONFLICT DO NOTHING;

-- STEP 6: Add payment terms
INSERT INTO payment_terms (org_id, term_name, days, description, is_active)
SELECT 
    org_id,
    term_name,
    days,
    description,
    true
FROM (
    VALUES 
        ('Cash', 0, 'Payment on delivery'),
        ('Net 7', 7, 'Payment within 7 days'),
        ('Net 15', 15, 'Payment within 15 days'),
        ('Net 30', 30, 'Payment within 30 days'),
        ('Net 45', 45, 'Payment within 45 days')
) AS terms_data(term_name, days, description)
CROSS JOIN organizations
WHERE org_name = 'Aaso Pharmaceuticals Pvt Ltd'
ON CONFLICT DO NOTHING;

-- STEP 7: Verification
DO $$
DECLARE
    v_org_count INTEGER;
    v_user_linked BOOLEAN;
    v_tax_count INTEGER;
    v_payment_terms INTEGER;
BEGIN
    -- Check organization
    SELECT COUNT(*) INTO v_org_count FROM organizations;
    
    -- Check user linkage
    SELECT EXISTS(
        SELECT 1 FROM org_users 
        WHERE email = 'vikasgarg304@gmail.com' 
        AND org_id IS NOT NULL
    ) INTO v_user_linked;
    
    -- Check tax setup
    SELECT COUNT(*) INTO v_tax_count FROM gst_tax_setup;
    
    -- Check payment terms
    SELECT COUNT(*) INTO v_payment_terms FROM payment_terms;
    
    RAISE NOTICE '';
    RAISE NOTICE '🎉 SETUP COMPLETE!';
    RAISE NOTICE '';
    RAISE NOTICE '✅ Organization created: %', CASE WHEN v_org_count > 0 THEN 'YES' ELSE 'NO' END;
    RAISE NOTICE '✅ Admin user linked: %', CASE WHEN v_user_linked THEN 'YES' ELSE 'NO' END;
    RAISE NOTICE '✅ GST tax categories: %', v_tax_count;
    RAISE NOTICE '✅ Payment terms: %', v_payment_terms;
    RAISE NOTICE '';
    RAISE NOTICE '📋 Next Steps:';
    RAISE NOTICE '1. Create admin user in Supabase Dashboard';
    RAISE NOTICE '2. Test login with working-login.html';
    RAISE NOTICE '3. Start backend: python start_server.py';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Your pharmaceutical ERP is ready!';
END $$;