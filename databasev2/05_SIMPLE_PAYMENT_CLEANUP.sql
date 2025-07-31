-- =====================================================
-- SCRIPT 05: Simple Payment Table Cleanup
-- Works with existing payments table structure
-- =====================================================

-- Check what payment-related tables exist
SELECT 
    tablename as payment_tables
FROM pg_tables 
WHERE schemaname = 'public'
AND (tablename LIKE '%payment%' OR tablename LIKE '%receipt%')
ORDER BY tablename;

-- Drop redundant payment tables if they exist
DROP TABLE IF EXISTS customer_payments CASCADE;
DROP TABLE IF EXISTS supplier_payments CASCADE;
DROP TABLE IF EXISTS vendor_payments CASCADE;
DROP TABLE IF EXISTS invoice_payments CASCADE;
DROP TABLE IF EXISTS upi_payments CASCADE;
DROP TABLE IF EXISTS customer_advance_payments CASCADE;

-- Check final count
SELECT 
    'Payment cleanup complete' as status,
    COUNT(*) as remaining_tables
FROM pg_tables 
WHERE schemaname = 'public';

-- Show what payment tables remain
SELECT 
    'Remaining payment tables:' as category,
    STRING_AGG(tablename, ', ') as tables
FROM pg_tables 
WHERE schemaname = 'public'
AND (tablename LIKE '%payment%' OR tablename = 'payments');