-- Drop additional tables to reach target of 45-50 tables
-- Current: 63 tables, dropping ~15-20 more

-- Drop authentication and backup tables (can use Supabase auth)
DROP TABLE IF EXISTS auth_org_mapping CASCADE;
DROP TABLE IF EXISTS backup_history CASCADE;
DROP TABLE IF EXISTS permissions CASCADE;
DROP TABLE IF EXISTS roles CASCADE;

-- Drop duplicate/redundant financial tables
DROP TABLE IF EXISTS customer_credit_notes CASCADE;
DROP TABLE IF EXISTS customer_outstanding CASCADE;
DROP TABLE IF EXISTS supplier_outstanding CASCADE;
DROP TABLE IF EXISTS journal_entries CASCADE;
DROP TABLE IF EXISTS journal_entry_lines CASCADE;
DROP TABLE IF EXISTS chart_of_accounts CASCADE;
DROP TABLE IF EXISTS tax_entries CASCADE;

-- Drop GST reporting tables (can be generated from invoices)
DROP TABLE IF EXISTS gst_adjustments CASCADE;
DROP TABLE IF EXISTS gstr1_data CASCADE;
DROP TABLE IF EXISTS gstr3b_data CASCADE;

-- Drop discount/scheme tables (can be handled in invoice items)
DROP TABLE IF EXISTS applied_discounts CASCADE;
DROP TABLE IF EXISTS discount_customers CASCADE;
DROP TABLE IF EXISTS discount_products CASCADE;
DROP TABLE IF EXISTS discount_schemes CASCADE;
DROP TABLE IF EXISTS scheme_products CASCADE;
DROP TABLE IF EXISTS schemes CASCADE;

-- Drop return tables (using sales_returns instead)
DROP TABLE IF EXISTS return_items CASCADE;
DROP TABLE IF EXISTS return_requests CASCADE;

-- Drop file management (can use Supabase storage)
DROP TABLE IF EXISTS file_uploads CASCADE;

-- Drop barcode tables (can be generated)
DROP TABLE IF EXISTS barcode_master CASCADE;
DROP TABLE IF EXISTS barcode_sequences CASCADE;

-- Drop writeoff tables (can use inventory_movements)
DROP TABLE IF EXISTS stock_writeoff_items CASCADE;
DROP TABLE IF EXISTS stock_writeoffs CASCADE;

-- Drop unit conversions (can be handled in products)
DROP TABLE IF EXISTS product_uom_conversions CASCADE;
DROP TABLE IF EXISTS units_of_measure CASCADE;

-- Drop branch management (using locations instead)
DROP TABLE IF EXISTS org_branches CASCADE;
DROP TABLE IF EXISTS storage_locations CASCADE;

-- Check final count
SELECT 
    'AFTER CLEANUP' as status,
    COUNT(*) as table_count,
    CASE 
        WHEN COUNT(*) <= 50 THEN '✅ TARGET ACHIEVED!'
        WHEN COUNT(*) <= 55 THEN '🟡 VERY CLOSE'
        ELSE '🔴 NEED MORE CLEANUP'
    END as result
FROM pg_tables 
WHERE schemaname = 'public';

-- Show tables dropped
SELECT 
    'Tables dropped in this cleanup' as info,
    '~30 tables removed' as count,
    'Auth, backup, financial duplicates, GST reports, discounts, returns, file management, barcodes, writeoffs, units, branches' as categories;