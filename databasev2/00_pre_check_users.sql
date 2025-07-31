-- =====================================================
-- Pre-Check Script: Analyze Users Tables Before Migration
-- Run this BEFORE executing 00_update_user_foreign_keys.sql
-- =====================================================

-- 1. Check structure of both user tables
\echo '=== USERS TABLE STRUCTURE ==='
\d users

\echo '\n=== ORG_USERS TABLE STRUCTURE ==='
\d org_users

-- 2. Count records in each table
\echo '\n=== RECORD COUNTS ==='
SELECT 
    'users' as table_name, 
    COUNT(*) as record_count 
FROM users
UNION ALL
SELECT 
    'org_users' as table_name, 
    COUNT(*) as record_count 
FROM org_users;

-- 3. Check for duplicate emails
\echo '\n=== DUPLICATE EMAILS BETWEEN TABLES ==='
SELECT 
    u.email,
    u.user_id as users_id,
    u.name as users_name,
    ou.user_id as org_users_id,
    ou.full_name as org_users_name,
    ou.org_id
FROM users u
JOIN org_users ou ON u.email = ou.email;

-- 4. Users without org_users match
\echo '\n=== USERS WITHOUT ORG_USERS MATCH ==='
SELECT 
    u.user_id,
    u.email,
    u.name,
    u.role
FROM users u
WHERE u.email NOT IN (SELECT email FROM org_users);

-- 5. Check all tables referencing users
\echo '\n=== TABLES WITH FOREIGN KEYS TO USERS ==='
SELECT 
    conrelid::regclass AS table_name,
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE confrelid = 'users'::regclass
AND contype = 'f'
ORDER BY conrelid::regclass::text;

-- 6. Check all tables referencing org_users
\echo '\n=== TABLES WITH FOREIGN KEYS TO ORG_USERS ==='
SELECT 
    conrelid::regclass AS table_name,
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE confrelid = 'org_users'::regclass
AND contype = 'f'
ORDER BY conrelid::regclass::text;

-- 7. Summary of migration complexity
\echo '\n=== MIGRATION SUMMARY ==='
WITH user_stats AS (
    SELECT 
        (SELECT COUNT(*) FROM users) as users_count,
        (SELECT COUNT(*) FROM org_users) as org_users_count,
        (SELECT COUNT(*) FROM users WHERE email IN (SELECT email FROM org_users)) as matched_users,
        (SELECT COUNT(*) FROM users WHERE email NOT IN (SELECT email FROM org_users)) as unmatched_users
),
fk_stats AS (
    SELECT 
        (SELECT COUNT(*) FROM pg_constraint WHERE confrelid = 'users'::regclass AND contype = 'f') as users_fk_count,
        (SELECT COUNT(*) FROM pg_constraint WHERE confrelid = 'org_users'::regclass AND contype = 'f') as org_users_fk_count
)
SELECT 
    us.users_count,
    us.org_users_count,
    us.matched_users,
    us.unmatched_users,
    fs.users_fk_count as "tables_referencing_users",
    fs.org_users_fk_count as "tables_referencing_org_users",
    CASE 
        WHEN us.unmatched_users = 0 THEN 'Simple - All users have org_users match'
        ELSE 'Complex - ' || us.unmatched_users || ' users need org_users creation'
    END as migration_complexity
FROM user_stats us, fk_stats fs;

-- 8. Check for potential issues
\echo '\n=== POTENTIAL ISSUES ==='
-- Check for null emails
SELECT 'Users with NULL email' as issue, COUNT(*) as count
FROM users WHERE email IS NULL
UNION ALL
SELECT 'Org_users with NULL email' as issue, COUNT(*) as count
FROM org_users WHERE email IS NULL
UNION ALL
-- Check for duplicate emails within tables
SELECT 'Duplicate emails in users table' as issue, COUNT(*) as count
FROM (SELECT email, COUNT(*) as cnt FROM users GROUP BY email HAVING COUNT(*) > 1) t
UNION ALL
SELECT 'Duplicate emails in org_users table' as issue, COUNT(*) as count
FROM (SELECT email, COUNT(*) as cnt FROM org_users GROUP BY email HAVING COUNT(*) > 1) t;