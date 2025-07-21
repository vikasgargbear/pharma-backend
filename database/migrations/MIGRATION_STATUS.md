# Migration Status

## Applied Migrations

### Production Environment (Supabase)

| Migration | Applied Date | Status | Notes |
|-----------|--------------|--------|-------|
| V001__initial_schema.sql | 2024-XX-XX | ✅ Applied | Initial database schema |
| V002__business_functions.sql | 2024-XX-XX | ✅ Applied | Business logic functions |
| V003__triggers_automation.sql | 2024-XX-XX | ✅ Applied | Initial triggers |
| V004__purchase_system_enhancements.sql | 2025-01-20 | ⚠️ Partially Applied | Applied as individual fixes |

### V004 Migration Details

The V004 migration consolidates the following fixes that were **already applied individually**:

1. **IMMEDIATE_FIX_purchase_trigger.sql** - ✅ Applied on 2025-01-20
   - Added purchase movement type support
   
2. **FIX_supplier_outstanding_trigger.sql** - ✅ Applied on 2025-01-20
   - Added unique constraint on purchase_id
   
3. **FIX_batch_creation_trigger_v2.sql** - ✅ Applied on 2025-01-20
   - Auto-generates batch numbers when null
   - Format: AUTO-YYYYMMDD-PRODUCTID-XXXX

## Important Notes

- **DO NOT RUN V004** on production - it's already applied as individual fixes
- **USE V004** for new environments or fresh deployments
- All fixes have been tested and verified in production

## Next Migration

The next migration should be `V005_` when adding new features.

---
*Last Updated: 2025-01-20*