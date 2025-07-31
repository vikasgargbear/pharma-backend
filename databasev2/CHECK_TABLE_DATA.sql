-- Check if these tables have any data before dropping

-- Check auth tables
SELECT 'auth_org_mapping' as table_name, COUNT(*) as row_count FROM auth_org_mapping
UNION ALL
SELECT 'permissions', COUNT(*) FROM permissions
UNION ALL
SELECT 'roles', COUNT(*) FROM roles;

-- Check business tables that might have important data
SELECT 'customer_credit_notes' as table_name, COUNT(*) as row_count FROM customer_credit_notes
UNION ALL
SELECT 'schemes', COUNT(*) FROM schemes
UNION ALL
SELECT 'discount_schemes', COUNT(*) FROM discount_schemes
UNION ALL
SELECT 'units_of_measure', COUNT(*) FROM units_of_measure
UNION ALL
SELECT 'org_branches', COUNT(*) FROM org_branches;

-- Check compliance tables
SELECT 'drug_inspector_visits' as table_name, COUNT(*) as row_count FROM drug_inspector_visits
UNION ALL
SELECT 'narcotic_register', COUNT(*) FROM narcotic_register
UNION ALL
SELECT 'licenses', COUNT(*) FROM licenses;