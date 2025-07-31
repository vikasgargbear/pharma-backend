-- Check all tables named 'users' across all schemas

-- 1. Find all users tables with their schemas
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE tablename = 'users'
ORDER BY schemaname;

-- 2. Check if there's a users table in auth schema (Supabase auth)
SELECT 
    'auth.users' as table_name,
    COUNT(*) as row_count
FROM auth.users;

-- 3. Check public.users specifically
SELECT 
    'public.users exists' as check,
    EXISTS (SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'users') as exists;

-- 4. Try to drop public.users specifically
DROP TABLE IF EXISTS public.users CASCADE;

-- 5. Check again after drop
SELECT 
    schemaname,
    tablename,
    'After DROP attempt' as status
FROM pg_tables 
WHERE tablename = 'users'
ORDER BY schemaname;