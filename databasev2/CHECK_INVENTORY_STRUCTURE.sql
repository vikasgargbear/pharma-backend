-- Check current inventory table structures

-- 1. Check columns in inventory_movements
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'inventory_movements'
AND table_schema = 'public'
ORDER BY ordinal_position;

-- 2. Check if inventory_transactions table exists
SELECT 
    'inventory_transactions exists' as check,
    EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'inventory_transactions' 
        AND table_schema = 'public'
    ) as result;

-- 3. Check if stock_transfers table exists
SELECT 
    'stock_transfers exists' as check,
    EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'stock_transfers' 
        AND table_schema = 'public'
    ) as result;

-- 4. If inventory_transactions exists, show its columns
SELECT 
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'inventory_transactions'
AND table_schema = 'public'
ORDER BY ordinal_position;