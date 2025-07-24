-- Query to get complete table schema from Supabase
-- Replace 'invoice_items' with any table name you want to inspect

SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'invoice_items'
ORDER BY ordinal_position;

-- Alternative query with more details
SELECT 
    c.column_name,
    c.data_type,
    c.is_nullable,
    c.column_default,
    c.character_maximum_length,
    c.numeric_precision,
    c.numeric_scale,
    c.ordinal_position
FROM information_schema.columns c
WHERE c.table_schema = 'public' 
  AND c.table_name = 'invoice_items'
ORDER BY c.ordinal_position;

-- Get all columns for multiple tables at once
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length
FROM information_schema.columns
WHERE table_name IN ('invoice_items', 'invoices', 'orders', 'order_items')
  AND table_schema = 'public'
ORDER BY table_name, ordinal_position;