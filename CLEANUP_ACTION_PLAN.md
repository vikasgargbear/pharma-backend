# AASO Pharma Backend - Cleanup Action Plan

This document provides a safe, iterative approach to cleaning up the codebase while maintaining functionality.

## Current State Analysis

### Statistics
- **Total Files**: 61
- **Total Functions**: 573 (422 unused)
- **Total Classes**: 165
- **Files with Unused Imports**: 56
- **No Circular Dependencies**: ✅

### Major Unused Components
1. **crud.py**: 196 functions (completely unused)
2. **schemas.py**: 47 classes (replaced by schemas_v2)
3. **business_logic.py**: Partially used (needs selective cleanup)

## Safe Cleanup Phases

### Phase 1: Low-Risk Cleanup (Immediate)
These can be done safely without breaking anything:

1. **Remove Unused Imports**
   ```bash
   # Files with most unused imports:
   - api/routers/*.py (legacy routers)
   - api/crud.py
   - api/schemas.py
   ```

2. **Delete Dead Code Files**
   ```bash
   # Safe to remove after verification:
   - api/crud.py (verify no imports first)
   - Any test_*.py files not in use
   - Migration scripts that have already run
   ```

3. **Clean Import Statements**
   ```python
   # Run this script to clean imports:
   autoflake --remove-all-unused-imports --recursive api/
   ```

### Phase 2: Schema Consolidation (Medium Risk)

1. **Verify Schema Usage**
   ```python
   # Check which schemas are actually used:
   grep -r "from.*schemas import" api/
   grep -r "from.*schemas_v2 import" api/
   ```

2. **Migration Plan**
   - Ensure all v1 routers use schemas_v2
   - Update any remaining legacy router imports
   - Remove schemas.py after full migration

### Phase 3: Router Consolidation (Medium-High Risk)

1. **Identify Active Endpoints**
   ```python
   # Currently active patterns:
   /api/v1/customers/*
   /api/v1/orders/*
   /api/v1/inventory/*
   /api/v1/billing/*
   
   # Legacy but possibly used:
   /products/*
   /api/simple-delivery/*
   /organizations/*
   ```

2. **Router Cleanup Strategy**
   - Keep all v1 routers (active)
   - Test each legacy endpoint
   - Remove truly unused endpoints
   - Consolidate similar functionality

### Phase 4: Service Layer Optimization (Low Risk)

1. **Enhance Service Classes**
   - Move business logic from routers to services
   - Ensure consistent error handling
   - Add missing service methods

2. **Remove business_logic.py**
   - Identify used functions
   - Move to appropriate service classes
   - Update imports
   - Delete file

## Specific File Actions

### DELETE These Files (After Verification)
```
api/crud.py                    # 196 unused functions
api/initialize_db.py           # One-time script
api/dependencies.py            # If unused
```

### REFACTOR These Files
```
api/schemas.py                 # Migrate to schemas_v2
api/business_logic.py          # Move to services
api/routers/customers.py       # Consolidate with v1
api/routers/orders.py          # Consolidate with v1
```

### KEEP These Files (Critical)
```
api/main.py                    # Entry point
api/models.py                  # Database models
api/database.py                # DB connection
api/base_schemas.py            # Basic schemas still used
api/core/*                     # Core functionality
api/routers/v1/*              # Active endpoints
api/services/*                # Business logic
api/schemas_v2/*              # Current schemas
```

## Implementation Steps

### Step 1: Create Backup
```bash
git checkout -b cleanup-phase-1
git add .
git commit -m "Backup before cleanup"
```

### Step 2: Remove Unused Imports
```python
# Create and run import cleaner script
python clean_imports.py
```

### Step 3: Test After Each Change
```bash
# Run server
python -m uvicorn api.main:app --reload

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/customers/
# ... test all critical endpoints
```

### Step 4: Remove Dead Files
```bash
# Remove with git
git rm api/crud.py
git rm api/initialize_db.py
# Commit after testing
```

### Step 5: Consolidate Gradually
- One module at a time
- Full testing between changes
- Commit working states

## Testing Checklist

Before committing any cleanup:

- [ ] Server starts without errors
- [ ] All health endpoints respond
- [ ] Customer CRUD operations work
- [ ] Order creation with batch selection works
- [ ] Invoice generation works
- [ ] Payment recording works
- [ ] Inventory tracking updates correctly
- [ ] No import errors in logs
- [ ] Railway deployment succeeds

## Rollback Plan

If anything breaks:
```bash
git checkout main
git branch -D cleanup-phase-1
```

## Metrics to Track

After each phase, verify:
1. Reduction in total lines of code
2. Reduction in unused imports
3. No new errors introduced
4. Performance remains same or improves
5. All tests still pass

## Long-term Goals

1. **Single Schema System**: Only schemas_v2
2. **Consistent Routing**: All under /api/v1
3. **Pure Service Layer**: No business logic in routers
4. **Zero Unused Code**: No dead functions/classes
5. **Clean Imports**: No unused imports
6. **Clear Dependencies**: Each module's purpose is clear

## Priority Order

1. **Immediate**: Remove crud.py and unused imports
2. **This Week**: Consolidate schemas
3. **Next Week**: Clean up routers
4. **Following Week**: Optimize services
5. **Ongoing**: Monitor and maintain

---
Follow this plan iteratively to achieve a clean, efficient codebase.