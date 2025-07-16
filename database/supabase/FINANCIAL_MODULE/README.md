# Financial Module - Separate from ERP

## Overview
This financial module is designed to be deployed separately from the main ERP system. It provides complete accounting functionality similar to Tally.

## Architecture Benefits
- **Independent Deployment**: Deploy financial module on separate servers
- **Independent Scaling**: Scale financial operations separately
- **Team Separation**: Different teams can manage ERP vs Finance
- **Compliance Isolation**: Financial compliance requirements isolated
- **Database Separation**: Can use different database if needed

## Integration Points
The financial module integrates with ERP through:
1. **API Integration**: RESTful APIs for data sync
2. **Event-Driven**: Using webhooks/events for real-time updates
3. **Batch Sync**: Nightly batch processes for reconciliation

## Key Features
- Complete double-entry bookkeeping
- GST compliance and returns
- TDS management
- Bank reconciliation
- Budget management
- Financial analytics
- Trial balance and P&L
- Balance sheet generation

## Deployment Order

Deploy these files in exact sequence:

```bash
# Deploy to separate database
psql "postgresql://postgres:[password]@[financial-host]:5432/financial_db"

# Run financial schema files in order
\i 01_financial_core_schema.sql
\i 02_financial_functions.sql
\i 03_financial_triggers.sql
\i 04_financial_indexes.sql
\i 05_financial_security.sql
\i 06_financial_initial_data.sql
```

## Complete File List

1. **01_financial_core_schema.sql** - Core financial tables (23+ tables)
2. **02_financial_functions.sql** - Business logic functions
3. **03_financial_triggers.sql** - Automation and validation
4. **04_financial_indexes.sql** - 80+ performance indexes
5. **05_financial_security.sql** - RLS and access control
6. **06_financial_initial_data.sql** - Default data and setup

## API Endpoints
The financial module exposes these key APIs:
- `/api/v1/vouchers` - Create accounting entries
- `/api/v1/ledgers` - Manage ledger accounts
- `/api/v1/gst/returns` - GST return filing
- `/api/v1/reports/trial-balance` - Financial reports
- `/api/v1/reconciliation` - Bank reconciliation

## Data Sync
Key data synced from ERP:
- Orders → Sales vouchers
- Purchases → Purchase vouchers
- Payments → Payment/Receipt vouchers
- Customers/Suppliers → Ledger accounts
- Products → Inventory valuation

## Security
- Separate authentication system
- Role-based access (Accountant, Auditor, CFO)
- Audit trail for all transactions
- Data encryption at rest