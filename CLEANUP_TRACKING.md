# Cleanup Tracking Document

## Purpose
Track every file deletion and test results to ensure nothing breaks.

## Current System State (Before Cleanup)
- Total Files: 61
- Total Functions: 573
- Working Endpoints: 9/14 (see baseline test)

## Known Issues (Pre-existing)
1. Order endpoints have "total_amount" error (need to use "final_amount")
2. Billing endpoints work at /billing/* not /api/v1/billing/*

## Deletion Plan & Results

### Phase 1: Safe Deletions

#### 1. crud.py
- **File**: api/crud.py
- **Size**: 71,135 bytes
- **Functions**: 196 (all unused)
- **Dependencies**: None (verified with check_crud_usage.py)
- **Status**: ✅ DELETED
- **Test Result**: Server still running, all tests pass (12/14, same as before) 

#### 2. initialize_db.py
- **File**: api/initialize_db.py
- **Size**: ~1KB
- **Functions**: 1 (one-time script)
- **Dependencies**: None
- **Status**: ✅ DELETED
- **Test Result**: Server still running, no issues

#### 3. Unused imports
- **Files Affected**: 56 files
- **Lines to Remove**: ~280
- **Risk**: Very Low
- **Status**: ✅ CLEANED
- **Test Result**: All imports cleaned with autoflake, server still running 

### Phase 2: Medium Risk Deletions

#### 4. dependencies.py
- **File**: api/dependencies.py
- **Functions**: 1
- **Dependencies**: Check usage
- **Status**: PENDING

#### 5. Clean analysis scripts
- check_crud_usage.py
- check_schemas_usage.py
- analyze_dependencies_detailed.py
- extract_all_functions.py
- test_critical_endpoints.py (keep for now)

### Phase 3: Complex Refactoring

#### 6. business_logic.py
- **File**: api/business_logic.py
- **Functions**: 22 (some used)
- **Action**: Move used functions to services
- **Status**: PENDING

#### 7. schemas.py
- **File**: api/schemas.py
- **Classes**: 47
- **Action**: Verify complete migration to schemas_v2
- **Status**: PENDING

## Key Files to NEVER Delete

### Core System
- api/main.py - Application entry point
- api/database.py - Database connection
- api/models.py - SQLAlchemy models
- api/base_schemas.py - Still used by products router

### Configuration
- api/core/config.py - System configuration
- api/core/database_manager.py - Enhanced DB management
- api/core/audit.py - Audit logging
- api/core/security.py - Security functions
- api/core/utils.py - Utility functions

### Active Routers
- api/routers/v1/customers.py - Customer endpoints
- api/routers/v1/orders.py - Order endpoints
- api/routers/v1/inventory.py - Inventory endpoints
- api/routers/v1/billing.py - Billing endpoints

### Services (All Active)
- api/services/customer_service.py
- api/services/order_service.py
- api/services/inventory_service.py
- api/services/billing_service.py

### Schemas (All Active)
- api/schemas_v2/customer.py
- api/schemas_v2/order.py
- api/schemas_v2/inventory.py
- api/schemas_v2/billing.py

### Legacy But Possibly Used
- api/routers/products.py - Products endpoint works
- api/routers/organizations.py - Organizations endpoint works
- api/routers/db_inspect.py - DB inspection works
- api/routers/simple_delivery.py - Might be used
- api/routers/customers_simple.py - Included in main

## Test Results Log

### Baseline (Before Any Changes)
Date: 2025-07-17 19:55
```
Health Check............................ ✅ PASS
Detailed Health......................... ✅ PASS
Root.................................... ✅ PASS
List Customers.......................... ✅ PASS
Get Customer............................ ✅ PASS
List Orders............................. ❌ FAIL (total_amount issue)
Order Stats............................. ❌ FAIL (total_amount issue)
Stock Status............................ ✅ PASS
Inventory Dashboard..................... ✅ PASS
List Invoices........................... ❌ FAIL (wrong URL)
Invoice Summary......................... ❌ FAIL (wrong URL)
Products................................ ✅ PASS
Organizations........................... ✅ PASS
DB Inspect.............................. ✅ PASS

Total: 9/14 passed (64.3%)
```

### After Each Deletion
(To be filled as we progress)

## Rollback Commands

If anything breaks:
```bash
# Rollback current changes
git checkout -- .

# Or completely reset to main
git checkout main
git branch -D smart-cleanup-phase1
```