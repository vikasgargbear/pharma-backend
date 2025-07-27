-- Check what columns exist in key tables
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name IN ('invoices', 'orders')
AND column_name LIKE '%status%'
ORDER BY table_name, ordinal_position;