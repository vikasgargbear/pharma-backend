-- DEBUG: Check what's happening with your migration

-- 1. Check if temporary table exists
SELECT 
    tablename,
    schemaname
FROM pg_tables 
WHERE tablename LIKE '%user%mapping%';

-- 2. Check current users and org_users
SELECT 
    'users count' as table_name,
    COUNT(*) as count
FROM users
UNION ALL
SELECT 
    'org_users count' as table_name,
    COUNT(*) as count
FROM org_users;

-- 3. Check if there are any users not in org_users
SELECT 
    u.user_id,
    u.email,
    u.name,
    'No match in org_users' as status
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM org_users ou WHERE ou.email = u.email
)
LIMIT 10;

-- 4. Check which tables have FKs to users
SELECT 
    conrelid::regclass AS table_name,
    conname AS constraint_name
FROM pg_constraint
WHERE confrelid = 'users'::regclass
AND contype = 'f'
ORDER BY conrelid::regclass::text;

-- 5. Simple test: Create mapping table with basic structure
DROP TABLE IF EXISTS user_migration_map;
CREATE TABLE user_migration_map AS
SELECT 
    u.user_id as old_user_id,
    u.email as user_email,
    ou.user_id as new_user_id,
    ou.email as org_user_email
FROM users u
LEFT JOIN org_users ou ON u.email = ou.email;

-- Check the mapping
SELECT * FROM user_migration_map LIMIT 10;