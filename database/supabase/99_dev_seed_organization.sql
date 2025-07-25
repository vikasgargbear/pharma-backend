-- =============================================
-- DEVELOPMENT SEED DATA - ORGANIZATION
-- =============================================
-- This file creates a development organization for testing
-- DO NOT USE IN PRODUCTION
-- =============================================

-- Create development organization with the hardcoded ID used in frontend
INSERT INTO organizations (
    org_id,
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
    business_settings,
    features_enabled,
    plan_type,
    subscription_status,
    is_active,
    max_users,
    max_products,
    max_customers,
    max_monthly_transactions
) VALUES (
    '12de5e22-eee7-4d25-b3a7-d16d01c6170f'::uuid,
    'Demo Pharmacy',
    'pharmaceutical',
    'REG123456',
    'AABCP1234C',
    '29AABCP1234C1Z1',
    'KA-B-123456',
    'Admin User',
    'admin@demopharmacy.com',
    '+91-9876543210',
    jsonb_build_object(
        'line1', '123 Main Street',
        'city', 'Bangalore',
        'state', 'Karnataka',
        'state_code', '29',
        'pincode', '560001',
        'country', 'India'
    ),
    jsonb_build_object(
        'tagline', 'Your Health, Our Priority',
        'financial_year_start', '2024-04-01',
        'financial_year_end', '2025-03-31',
        'currency', 'INR',
        'currency_symbol', '₹',
        'invoice_prefix', 'INV/',
        'challan_prefix', 'DC/',
        'po_prefix', 'PO/',
        'return_prefix', 'RTN/',
        'credit_note_prefix', 'CN/',
        'debit_note_prefix', 'DN/',
        'print_format', 'A4',
        'show_signature', true,
        'show_logo', true,
        'show_bank_details', true
    ),
    ARRAY['basic_erp', 'inventory_management', 'sales', 'purchase', 'gst'],
    'professional',
    'active',
    true,
    10,      -- max_users
    10000,   -- max_products
    5000,    -- max_customers
    50000    -- max_monthly_transactions
) ON CONFLICT (org_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- Update business_settings with feature configuration
UPDATE organizations 
SET business_settings = business_settings || jsonb_build_object(
    'features', jsonb_build_object(
        -- Inventory Features
        'allowNegativeStock', false,
        'expiryDateMandatory', true,
        'batchWiseTracking', true,
        'stockAdjustmentApproval', false,
        'lowStockAlerts', true,
        
        -- Sales Features
        'creditLimitForParties', true,
        'creditLimitThreshold', 100000,
        'salesReturnFlow', 'with-credit-note',
        'salesApprovalRequired', false,
        'discountLimit', 20,
        
        -- Purchase Features
        'grnWorkflow', true,
        'purchaseApprovalLimit', 50000,
        'autoGeneratePurchaseOrder', false,
        'vendorRatingSystem', false,
        
        -- E-Way Bill
        'ewayBillEnabled', true,
        'ewayBillThreshold', 50000,
        'autoGenerateEwayBill', false,
        
        -- GST Features
        'gstRoundOff', true,
        'reverseChargeApplicable', false,
        'compositionScheme', false,
        'tcsApplicable', false,
        
        -- Payment Features
        'allowPartialPayments', true,
        'autoReconciliation', false,
        'paymentReminders', true,
        'reminderDays', ARRAY[7, 15, 30],
        
        -- General Features
        'multiCurrency', false,
        'multiLocation', true,
        'barcodeScannerIntegration', false,
        'smsNotifications', false,
        'emailNotifications', true,
        'whatsappNotifications', false,
        
        -- Security Features
        'twoFactorAuth', false,
        'ipRestriction', false,
        'sessionTimeout', 30,
        'passwordComplexity', 'medium',
        
        -- Workflow Features
        'purchaseWorkflow', true,
        'salesWorkflow', false,
        'paymentApproval', true,
        'returnApproval', true
    )
)
WHERE org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f'::uuid;

-- Create a demo user for this organization
INSERT INTO org_users (
    org_id,
    full_name,
    email,
    phone,
    role,
    password_hash,
    can_view_reports,
    can_modify_prices,
    can_approve_discounts,
    is_active
) VALUES (
    '12de5e22-eee7-4d25-b3a7-d16d01c6170f'::uuid,
    'Admin User',
    'admin@demopharmacy.com',
    '+91-9876543210',
    'owner',
    'supabase_auth', -- This indicates auth is handled by Supabase
    true,
    true,
    true,
    true
) ON CONFLICT (org_id, email) DO NOTHING;

-- Output confirmation
DO $$
BEGIN
    RAISE NOTICE '
=============================================
DEVELOPMENT ORGANIZATION CREATED
=============================================
Organization ID: 12de5e22-eee7-4d25-b3a7-d16d01c6170f
Organization Name: Demo Pharmacy
Email: admin@demopharmacy.com

This organization is now ready for use with the frontend.
';
END $$;