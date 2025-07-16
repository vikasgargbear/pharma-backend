# 🔒 RLS Troubleshooting Guide - Lessons Learned

## 🎯 The Core Issue We Discovered

**Problem**: Frontend shows "0 organizations" even though data exists and SQL queries return results.

**Root Cause**: Row Level Security (RLS) policies were blocking access due to authentication context differences.

## 🔍 Key Learnings

### 1. **Authentication Context Matters**
- `auth.uid()` returns NULL in SQL Editor but works in frontend
- Frontend uses authenticated user context
- Backend with service_role key bypasses RLS

### 2. **The Infinite Recursion Trap**
```sql
-- ❌ BAD - Causes recursion
CREATE POLICY "org_users_policy" ON org_users
    USING (org_id IN (
        SELECT org_id FROM org_users WHERE auth_uid = auth.uid()
    ));
```

```sql
-- ✅ GOOD - No recursion
CREATE POLICY "org_users_policy" ON org_users
    USING (auth_uid = auth.uid());
```

### 3. **Helper Functions Save the Day**
```sql
-- Create once, use everywhere
CREATE FUNCTION get_auth_user_org_id()
RETURNS UUID AS $$
    SELECT org_id FROM org_users 
    WHERE auth_uid = auth.uid() 
    LIMIT 1;
$$ LANGUAGE sql SECURITY DEFINER STABLE;
```

### 4. **The Critical Frontend Fix**
```sql
-- This policy allows the frontend to see organizations
CREATE POLICY "anon_read_orgs" ON organizations
    FOR SELECT USING (true);
```

## 📋 Debugging Checklist

When frontend shows different results than SQL Editor:

1. **Check auth context**:
   ```sql
   SELECT auth.uid(), auth.role(), current_user;
   ```

2. **Test with RLS disabled**:
   ```sql
   ALTER TABLE your_table DISABLE ROW LEVEL SECURITY;
   -- Test query
   ALTER TABLE your_table ENABLE ROW LEVEL SECURITY;
   ```

3. **Check if user is properly linked**:
   ```sql
   SELECT * FROM org_users WHERE email = 'user@email.com';
   ```

4. **Test the exact frontend query**:
   ```sql
   -- Simulate frontend query
   SELECT * FROM organizations LIMIT 1;
   ```

## 🚨 Common Pitfalls

### 1. **Column doesn't exist**
- Not all tables have `org_id` (e.g., `order_items`)
- Solution: Use joins to parent tables

### 2. **Permission denied for schema auth**
- Can't create functions in `auth` schema
- Solution: Use `public` schema

### 3. **Duplicate key violations**
- Multiple users with same auth_uid
- Solution: Use ON CONFLICT clauses

### 4. **Missing tables**
- Running RLS on tables that don't exist yet
- Solution: Check table existence before applying policies

## 🛠️ Quick Fixes

### If login works but shows 0 organizations:
```sql
-- Quick fix - allow reading
CREATE POLICY "anon_read_orgs" ON organizations
    FOR SELECT USING (true);
```

### If you get infinite recursion:
```sql
-- Use helper function approach
CREATE FUNCTION get_auth_user_org_id()...
```

### If nothing works:
```sql
-- Nuclear option (dev only)
ALTER TABLE organizations DISABLE ROW LEVEL SECURITY;
```

## 📚 Best Practices

1. **Always test RLS policies** with actual frontend, not just SQL Editor
2. **Use helper functions** to avoid recursion
3. **Start simple** - basic policies first, complex logic later
4. **Document policies** - future you will thank you
5. **Test with different roles** - anon, authenticated, service_role

## 🔗 Related Files

- `07_FINAL_SETUP.sql` - Complete working setup
- `working-login.html` - Test your authentication
- `working-login-debug.html` - Debug authentication issues

## 💡 Pro Tips

1. **Frontend not matching SQL?** Check if anon users can read
2. **Getting recursion errors?** You're querying the same table in its policy
3. **Auth not working?** Ensure user exists in BOTH auth.users AND org_users
4. **RLS too complex?** Start with it disabled, add policies incrementally

Remember: RLS is powerful but tricky. When in doubt, disable it for development and enable it with proper testing before production!