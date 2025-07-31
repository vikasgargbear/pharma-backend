-- Conservative cleanup - only drop clearly safe tables

-- Drop auth tables (Supabase handles this)
DROP TABLE IF EXISTS auth_org_mapping CASCADE;
DROP TABLE IF EXISTS permissions CASCADE;
DROP TABLE IF EXISTS roles CASCADE;

-- Drop backup/history tables
DROP TABLE IF EXISTS backup_history CASCADE;

-- Drop generated/reportable data
DROP TABLE IF EXISTS gstr1_data CASCADE;
DROP TABLE IF EXISTS gstr3b_data CASCADE;
DROP TABLE IF EXISTS gst_adjustments CASCADE;

-- Drop barcode generation tables
DROP TABLE IF EXISTS barcode_master CASCADE;
DROP TABLE IF EXISTS barcode_sequences CASCADE;

-- Drop file upload tracking (use Supabase storage)
DROP TABLE IF EXISTS file_uploads CASCADE;

-- Drop return tables (already have sales_returns)
DROP TABLE IF EXISTS return_items CASCADE;
DROP TABLE IF EXISTS return_requests CASCADE;

-- Drop applied discounts (can track in invoice_items)
DROP TABLE IF EXISTS applied_discounts CASCADE;

-- Check count
SELECT 
    'Conservative cleanup result' as status,
    COUNT(*) as remaining_tables
FROM pg_tables 
WHERE schemaname = 'public';