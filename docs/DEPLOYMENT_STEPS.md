# Quick Deployment Steps

## 1. Run SQL in Supabase
```sql
-- Run these in order:
\i 99_dev_seed_organization.sql
\i 13_feature_audit_log.sql
```

## 2. Verify
- Open Master Settings in frontend
- Company Profile should load
- Feature Settings should load
- Save changes and check if they persist

## 3. If Error
Check Railway logs for backend errors