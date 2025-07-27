-- =============================================
-- RLS CHECK AND FIX - Safe to run multiple times
-- =============================================
-- This script checks current status and only fixes what's needed
-- =============================================

-- STEP 1: Show current security status
SELECT 
    tablename,
    rowsecurity,
    CASE 
        WHEN rowsecurity THEN '✅ RLS Enabled'
        ELSE '❌ RLS DISABLED - INSECURE!'
    END as status,
    (SELECT COUNT(*) FROM pg_policies p WHERE p.tablename = t.tablename) as policy_count
FROM pg_tables t
WHERE schemaname = 'public'
AND tablename NOT IN ('schema_migrations', 'spatial_ref_sys')
ORDER BY rowsecurity ASC, tablename;

-- STEP 2: Enable RLS on all tables that need it
DO $$ 
DECLARE
    tbl RECORD;
    policy_exists BOOLEAN;
BEGIN
    -- Loop through all tables
    FOR tbl IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename NOT IN ('schema_migrations', 'spatial_ref_sys')
    LOOP
        -- Enable RLS if not already enabled
        IF NOT EXISTS (
            SELECT 1 FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename = tbl.tablename 
            AND rowsecurity = true
        ) THEN
            EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', tbl.tablename);
            RAISE NOTICE 'Enabled RLS on table: %', tbl.tablename;
        END IF;
        
        -- Check if any policy exists
        SELECT EXISTS (
            SELECT 1 FROM pg_policies 
            WHERE schemaname = 'public' 
            AND tablename = tbl.tablename
        ) INTO policy_exists;
        
        -- Create basic policy if none exists
        IF NOT policy_exists THEN
            EXECUTE format('CREATE POLICY "authenticated_access" ON %I FOR ALL TO authenticated USING (true) WITH CHECK (true)', tbl.tablename);
            RAISE NOTICE 'Created policy for table: %', tbl.tablename;
        END IF;
    END LOOP;
END $$;

-- STEP 3: Final security report
SELECT 
    'Total Tables' as metric,
    COUNT(*) as count
FROM pg_tables
WHERE schemaname = 'public'
UNION ALL
SELECT 
    'RLS Enabled' as metric,
    COUNT(*) as count
FROM pg_tables
WHERE schemaname = 'public' AND rowsecurity = true
UNION ALL
SELECT 
    'RLS DISABLED' as metric,
    COUNT(*) as count
FROM pg_tables
WHERE schemaname = 'public' AND rowsecurity = false
UNION ALL
SELECT 
    'Tables with Policies' as metric,
    COUNT(DISTINCT tablename) as count
FROM pg_policies
WHERE schemaname = 'public';

-- STEP 4: Show any remaining unprotected tables
SELECT 
    tablename as "⚠️ UNPROTECTED TABLES"
FROM pg_tables
WHERE schemaname = 'public'
AND rowsecurity = false
AND tablename NOT IN ('schema_migrations', 'spatial_ref_sys');