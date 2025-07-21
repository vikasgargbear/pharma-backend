# Purchase System Deployment Guide

## Quick Start

For teams deploying the purchase system updates, follow these steps:

### 1. Database Migration

Run this single consolidated migration in your Supabase SQL editor:

```sql
-- File: database/migrations/V004__purchase_system_enhancements.sql
```

This migration includes:
- ✅ Purchase movement support in inventory triggers
- ✅ Supplier outstanding constraint fix
- ✅ Automatic batch number generation
- ✅ Enhanced batch update logic

### 2. Deploy Application

```bash
# Deploy to Railway
railway up

# Or deploy to your platform
git push production main
```

### 3. Verify Deployment

```bash
# Test auto batch generation
python test_auto_batch_fixed.py

# Test all scenarios
python test_complete_scenarios.py
```

## What Changed?

### Database Changes
1. **Inventory Movement Trigger**: Now supports 'purchase' type
2. **Batch Creation Trigger**: Auto-generates batch numbers when null
3. **Supplier Outstanding**: Added unique constraint on purchase_id

### API Changes
1. **New Endpoint**: `/receive-fixed` - Use this for goods receipt
2. **Deprecated**: Original `/receive` endpoint (creates duplicate batches)

### Feature Enhancements
1. **Auto Batch Generation**: `AUTO-YYYYMMDD-PRODUCTID-XXXX` format
2. **Smart Defaults**: 
   - Manufacturing date: 30 days ago
   - Expiry date: 2 years from today
3. **Duplicate Prevention**: Checks before creating batches

## Migration Notes

### From Old System
If you're migrating from the old system:

1. **Stop using** `/api/v1/purchases-enhanced/{id}/receive`
2. **Start using** `/api/v1/purchases-enhanced/{id}/receive-fixed`
3. **Run migration** V004 to update all triggers

### Rollback Plan
If issues occur:
```sql
-- Rollback to previous trigger versions
-- Contact team for rollback scripts
```

## Testing Checklist

- [ ] Create purchase without batch numbers
- [ ] Verify AUTO- batch generation
- [ ] Test custom batch override
- [ ] Check inventory movements created
- [ ] Verify supplier outstanding tracking

## Support

### Common Issues

**Q: Getting "batch already exists" error?**
A: The system now prevents duplicates. This is expected behavior.

**Q: Batch number is NULL error?**
A: Use the `/receive-fixed` endpoint instead of `/receive`.

**Q: How to identify auto-generated batches?**
A: They start with "AUTO-" prefix.

### Contact
- Technical Issues: Create GitHub issue
- Urgent Support: Contact DevOps team

## Production URLs

- API Base: `https://pharma-backend-production-0c09.up.railway.app`
- API Docs: `https://pharma-backend-production-0c09.up.railway.app/docs`

---

*Last Updated: 2025-01-20*