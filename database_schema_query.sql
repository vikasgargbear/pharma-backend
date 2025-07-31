-- Query to get complete database schema information from Supabase

-- 1. Get all tables with their columns, data types, and constraints
SELECT 
    t.table_schema,
    t.table_name,
    t.table_type,
    c.column_name,
    c.data_type,
    c.character_maximum_length,
    c.numeric_precision,
    c.numeric_scale,
    c.is_nullable,
    c.column_default,
    c.udt_name,
    tc.constraint_type,
    cc.check_clause,
    col_description(pgc.oid, c.ordinal_position) as column_comment,
    obj_description(pgc.oid) as table_comment
FROM information_schema.tables t
JOIN information_schema.columns c 
    ON t.table_schema = c.table_schema 
    AND t.table_name = c.table_name
LEFT JOIN information_schema.table_constraints tc
    ON tc.table_schema = t.table_schema
    AND tc.table_name = t.table_name
    AND tc.constraint_name IN (
        SELECT constraint_name 
        FROM information_schema.key_column_usage 
        WHERE table_schema = t.table_schema 
        AND table_name = t.table_name 
        AND column_name = c.column_name
    )
LEFT JOIN information_schema.check_constraints cc
    ON cc.constraint_schema = tc.constraint_schema
    AND cc.constraint_name = tc.constraint_name
LEFT JOIN pg_catalog.pg_class pgc 
    ON pgc.relname = t.table_name
    AND pgc.relnamespace = (
        SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = t.table_schema
    )
WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
    AND t.table_schema NOT LIKE 'pg_%'
ORDER BY t.table_schema, t.table_name, c.ordinal_position;

-- 2. Get all foreign key relationships
SELECT
    tc.table_schema,
    tc.table_name,
    kcu.column_name,
    ccu.table_schema AS foreign_table_schema,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    tc.constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY tc.table_schema, tc.table_name;

-- 3. Get all indexes
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY schemaname, tablename, indexname;

-- 4. Get all functions/stored procedures
SELECT 
    n.nspname as schema_name,
    p.proname as function_name,
    pg_get_function_arguments(p.oid) as arguments,
    pg_get_functiondef(p.oid) as definition
FROM pg_proc p
LEFT JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
    AND n.nspname NOT LIKE 'pg_%'
ORDER BY n.nspname, p.proname;

-- 5. Get all views
SELECT 
    schemaname,
    viewname,
    definition
FROM pg_views
WHERE schemaname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY schemaname, viewname;

-- 6. Get row counts for each table (optional - can be slow on large tables)
SELECT 
    schemaname,
    tablename as table_name,
    n_live_tup as approximate_row_count
FROM pg_stat_user_tables
ORDER BY schemaname, tablename;