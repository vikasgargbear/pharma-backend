-- =============================================
-- PHARMACEUTICAL ERP - PRODUCTION INITIAL DATA
-- =============================================
-- Version: 1.0 - Production Only Data
-- Description: ONLY essential system data for production
-- Deploy Order: 6th - After security
-- =============================================

-- =============================================
-- WARNING: PRODUCTION DATA ONLY
-- =============================================
-- This file contains ONLY the minimum required data
-- for a production system to function properly.
-- NO test data, NO sample organizations, NO demo users.
-- =============================================

-- =============================================
-- SYSTEM SETTINGS (GLOBAL)
-- =============================================

-- Core system settings required for operation
INSERT INTO system_settings (org_id, setting_key, setting_value, setting_type, description) VALUES
(NULL, 'system.version', '"1.0.0"', 'system', 'System version'),
(NULL, 'system.country', '"IN"', 'system', 'Default country code'),
(NULL, 'system.currency', '"INR"', 'system', 'Default currency'),
(NULL, 'system.date_format', '"DD/MM/YYYY"', 'system', 'Default date format'),
(NULL, 'system.time_zone', '"Asia/Kolkata"', 'system', 'Default timezone'),
(NULL, 'gst.enabled', 'true', 'system', 'GST feature flag'),
(NULL, 'inventory.negative_stock_allowed', 'false', 'system', 'Allow negative stock'),
(NULL, 'inventory.batch_tracking_required', 'true', 'system', 'Require batch tracking'),
(NULL, 'inventory.expiry_alert_days', '90', 'system', 'Days before expiry to alert'),
(NULL, 'prescription.required_for_schedule_h', 'true', 'system', 'Require prescription for Schedule H drugs'),
(NULL, 'billing.round_off_enabled', 'true', 'system', 'Enable round off in billing'),
(NULL, 'billing.default_payment_terms_days', '30', 'system', 'Default payment terms')
ON CONFLICT (org_id, setting_key) DO NOTHING;

-- =============================================
-- CRITICAL MASTER DATA
-- =============================================

-- =============================================
-- PHARMACEUTICAL PRODUCT TYPES (STANDARD)
-- =============================================
-- These are industry-standard types needed for any pharmacy

INSERT INTO product_types (org_id, type_code, type_name, form_category, is_system_defined) VALUES
(NULL, 'TAB', 'Tablet', 'solid', true),
(NULL, 'CAP', 'Capsule', 'solid', true),
(NULL, 'SYP', 'Syrup', 'liquid', true),
(NULL, 'INJ', 'Injection', 'liquid', true),
(NULL, 'OINT', 'Ointment/Cream', 'semi-solid', true),
(NULL, 'DROPS', 'Drops', 'liquid', true),
(NULL, 'POWDER', 'Powder', 'solid', true),
(NULL, 'GENERIC', 'Other', 'mixed', true)
ON CONFLICT (org_id, type_code) DO NOTHING;

-- =============================================
-- STANDARD UNITS OF MEASURE
-- =============================================
-- Essential units for pharmaceutical operations

INSERT INTO units_of_measure (org_id, uom_code, uom_name, uom_category, base_unit, is_system_defined) VALUES
-- Count based (most common)
(NULL, 'TABLET', 'Tablet', 'count', true, true),
(NULL, 'CAPSULE', 'Capsule', 'count', true, true),
(NULL, 'PIECE', 'Piece', 'count', true, true),
(NULL, 'STRIP', 'Strip', 'count', false, true),
(NULL, 'BOX', 'Box', 'count', false, true),
(NULL, 'BOTTLE', 'Bottle', 'count', false, true),
(NULL, 'VIAL', 'Vial', 'count', false, true),
(NULL, 'TUBE', 'Tube', 'count', false, true),
-- Volume based
(NULL, 'ML', 'Milliliter', 'volume', true, true),
(NULL, 'L', 'Liter', 'volume', false, true),
-- Weight based
(NULL, 'MG', 'Milligram', 'weight', true, true),
(NULL, 'GM', 'Gram', 'weight', false, true),
(NULL, 'KG', 'Kilogram', 'weight', false, true)
ON CONFLICT (org_id, uom_code) DO NOTHING;

-- =============================================
-- STANDARD PRODUCT CATEGORIES
-- =============================================
-- Common pharmaceutical categories for India

INSERT INTO categories (org_id, category_name, parent_category_id, description, is_active) VALUES
-- Prescription categories
(NULL, 'Prescription Medicines', NULL, 'Medicines requiring doctor prescription', true),
(NULL, 'Over-the-Counter (OTC)', NULL, 'Medicines available without prescription', true),
(NULL, 'Generic Medicines', NULL, 'Generic alternatives to branded drugs', true),
-- Therapeutic categories
(NULL, 'Antibiotics', NULL, 'Anti-bacterial medications', true),
(NULL, 'Pain Relief', NULL, 'Analgesics and pain management', true),
(NULL, 'Fever & Cold', NULL, 'Antipyretics and cold remedies', true),
(NULL, 'Digestive Health', NULL, 'Gastro-intestinal medications', true),
(NULL, 'Diabetes Care', NULL, 'Anti-diabetic drugs and supplies', true),
(NULL, 'Heart & Blood Pressure', NULL, 'Cardiovascular medications', true),
(NULL, 'Vitamins & Supplements', NULL, 'Nutritional supplements', true),
-- Product type categories
(NULL, 'First Aid', NULL, 'Emergency care supplies', true),
(NULL, 'Baby Care', NULL, 'Infant and child care products', true),
(NULL, 'Women Health', NULL, 'Women specific health products', true),
(NULL, 'Elderly Care', NULL, 'Geriatric care products', true),
-- Other essentials
(NULL, 'Medical Devices', NULL, 'Medical equipment and devices', true),
(NULL, 'Surgical Items', NULL, 'Surgical supplies and instruments', true),
(NULL, 'Ayurvedic & Herbal', NULL, 'Traditional medicine products', true),
(NULL, 'Homeopathy', NULL, 'Homeopathic medicines', true),
(NULL, 'Personal Care', NULL, 'Health and hygiene products', true),
(NULL, 'Nutrition & Fitness', NULL, 'Health supplements and fitness', true)
ON CONFLICT (org_id, category_name) DO NOTHING;

-- =============================================
-- GST RATES REFERENCE (FOR INFORMATION)
-- =============================================
-- Common HSN codes and GST rates for pharmaceutical products:
-- 
-- Life-saving drugs (0% GST):
-- - 30041011: Penicillins
-- - 30042020: Antibiotics (specific)
-- - 30049011: Anti-cancer drugs
-- - 30049020: Anti-TB drugs
-- - 30049030: Anti-HIV drugs
-- - 30049040: Anti-malarial drugs
--
-- Reduced rate (5% GST):
-- - 30049091: Medicines for diabetes
-- - 3002: Vaccines
-- - 300630: Blood grouping reagents
--
-- Standard rate (12% GST):
-- - 3004: Most medicaments
-- - 3005: Bandages, gauze
-- - 9018: Medical instruments
-- - 3006: Pharmaceutical goods
--
-- Higher rate (18% GST):
-- - 2106: Food supplements
-- - 3401: Medicated soaps
--
-- Note: Add HSN codes directly to products when creating them

-- =============================================
-- PRODUCTION DEPLOYMENT MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
PRODUCTION INITIAL DATA LOADED
=============================================
✓ System settings configured
✓ Minimal master data loaded
✓ NO test/demo data included

Next Steps for Production:
1. Create your organization using create_organization()
2. Set up your admin user through Supabase Auth
3. Configure organization-specific settings
4. Add your product types and units
5. Import your master data

Production Checklist:
□ Change all default passwords
□ Configure proper backup schedule
□ Set up monitoring alerts
□ Review security settings
□ Test disaster recovery plan
';
END $$;