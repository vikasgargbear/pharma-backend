# AASO Pharma Backend - Component Dependency Visualization

This document provides a visual representation of how all components connect and depend on each other.

## Core Architecture Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         API ENTRY POINT                         │
│                         api/main.py                             │
│  - FastAPI app initialization                                   │
│  - Middleware configuration                                     │
│  - Router inclusion                                            │
└────────────────────────────┬───────────────────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
        ▼                                         ▼
┌───────────────────┐                    ┌──────────────────┐
│   ROUTERS (/api)  │                    │  ROUTERS (/api/v1)│
├───────────────────┤                    ├──────────────────┤
│ • products.py     │                    │ • customers.py    │
│ • simple_delivery │                    │ • orders.py       │
│ • db_inspect.py   │                    │ • inventory.py    │
│ • migrations.py   │                    │ • billing.py      │
│ • organizations.py│                    └────────┬──────────┘
│ • customers_simple│                             │
└─────────┬─────────┘                             │
          │                                       │
          └───────────────┬───────────────────────┘
                          │
                          ▼
              ┌──────────────────────┐
              │   SERVICE LAYER      │
              ├──────────────────────┤
              │ • customer_service   │
              │ • order_service      │
              │ • inventory_service  │
              │ • billing_service    │
              └──────────┬───────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
┌──────────────────┐           ┌──────────────────┐
│   SCHEMAS V2     │           │    DATABASE      │
├──────────────────┤           ├──────────────────┤
│ • customer.py    │           │ • models.py      │
│ • order.py       │           │ • database.py    │
│ • inventory.py   │           │ • core/database_ │
│ • billing.py     │           │   manager.py     │
└──────────────────┘           └──────────────────┘
```

## Component Import Dependencies

### 1. Main Application (api/main.py)
```python
# Core imports
from . import models, base_schemas as schemas
from .database import SessionLocal, engine, get_db
from .core.config import settings
from .core.database_manager import get_database_manager
from .core.audit import AuditLogger

# Router imports
from .routers import (products, simple_delivery, db_inspect, 
                     migrations, migrations_v2, organizations, 
                     customers_simple)
from .routers.v1 import customers_router, orders_router, 
                       inventory_router, billing_router
```

### 2. V1 API Routers Dependencies

#### api/routers/v1/customers.py
```python
from ...database import get_db
from ...schemas_v2.customer import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    CustomerListResponse, CustomerLedgerResponse,
    CustomerOutstandingResponse, PaymentRecord, PaymentResponse
)
from ...services.customer_service import CustomerService
```

#### api/routers/v1/orders.py
```python
from ...database import get_db
from ...schemas_v2.order import (
    OrderCreate, OrderUpdate, OrderResponse,
    OrderListResponse, OrderDetailResponse
)
from ...services.order_service import OrderService
```

#### api/routers/v1/inventory.py
```python
from ...database import get_db
from ...schemas_v2.inventory import (
    BatchCreate, BatchResponse, StockStatusResponse,
    InventoryMovementCreate, InventoryMovementResponse,
    StockAdjustmentCreate, ExpiryAlertResponse
)
from ...services.inventory_service import InventoryService
```

#### api/routers/v1/billing.py
```python
from ...database import get_db
from ...schemas_v2.billing import (
    InvoiceCreate, InvoiceResponse,
    PaymentCreate, PaymentResponse,
    GSTReportRequest, GSTR1Summary, InvoiceSummary
)
from ...services.billing_service import BillingService
```

### 3. Service Layer Dependencies

#### api/services/customer_service.py
```python
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..schemas_v2.customer import *
# Uses: customers, orders, invoices tables
```

#### api/services/order_service.py
```python
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..schemas_v2.order import *
# Uses: orders, order_items, products, batches, 
#       inventory_movements, customers tables
```

#### api/services/inventory_service.py
```python
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..schemas_v2.inventory import *
# Uses: products, batches, inventory_movements,
#       stock_adjustments, batch_locations tables
```

#### api/services/billing_service.py
```python
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..schemas_v2.billing import *
# Uses: invoices, invoice_items, invoice_payments,
#       orders, customers, organizations tables
```

## Database Table Usage Map

### Customer Module Tables
- **customers** → Used by: customer_service, order_service, billing_service
- **customer_advance_payments** → Used by: customer_service
- **customer_credit_notes** → Used by: customer_service

### Order Module Tables
- **orders** → Used by: order_service, billing_service, customer_service
- **order_items** → Used by: order_service, billing_service
- **order_status_history** → Used by: order_service

### Inventory Module Tables
- **products** → Used by: inventory_service, order_service
- **batches** → Used by: inventory_service, order_service
- **inventory_movements** → Used by: inventory_service, order_service
- **stock_adjustments** → Used by: inventory_service
- **batch_locations** → Used by: inventory_service
- **storage_locations** → Used by: inventory_service

### Billing Module Tables
- **invoices** → Used by: billing_service, customer_service
- **invoice_items** → Used by: billing_service
- **invoice_payments** → Used by: billing_service, customer_service

### Core Tables
- **organizations** → Used by: All services (for org_id)
- **users** → Used by: Authentication (future)
- **audit_logs** → Used by: Audit middleware

## Critical Dependencies

### 1. Order Creation Flow
```
POST /api/v1/orders/
    ↓
orders_router (api/routers/v1/orders.py)
    ↓
OrderService.create_order (api/services/order_service.py)
    ↓
    ├── Validate customer (customers table)
    ├── Validate inventory (products, batches tables)
    ├── Select batch FIFO (batches table)
    ├── Create order (orders table)
    ├── Create order items (order_items table)
    ├── Update inventory (batches table)
    └── Record movement (inventory_movements table)
```

### 2. Invoice Generation Flow
```
POST /api/v1/billing/invoices
    ↓
billing_router (api/routers/v1/billing.py)
    ↓
BillingService.create_invoice_from_order
    ↓
    ├── Validate order status (orders table)
    ├── Get customer details (customers table)
    ├── Get organization state (organizations table)
    ├── Calculate GST (CGST/SGST vs IGST)
    ├── Create invoice (invoices table)
    └── Create invoice items (invoice_items table)
```

### 3. Payment Recording Flow
```
POST /api/v1/billing/payments
    ↓
billing_router
    ↓
BillingService.record_payment
    ↓
    ├── Validate invoice (invoices table)
    ├── Record payment (invoice_payments table)
    ├── Update invoice status (invoices table)
    └── Update order paid amount (orders table)
```

## Module Isolation and Dependencies

### Standalone Modules (No internal dependencies)
- api/core/config.py
- api/schemas_v2/*.py (Pure Pydantic schemas)

### Core Dependencies (Used by all)
- api/database.py
- api/models.py
- api/core/database_manager.py

### Service Dependencies
- All services depend on:
  - SQLAlchemy Session
  - Respective schemas from schemas_v2
  - Database models
  - SQL queries via text()

### Router Dependencies
- All routers depend on:
  - FastAPI (Router, Depends, HTTPException)
  - Database session (get_db)
  - Respective service classes
  - Respective schemas

## Unused Code Identification

### High Priority for Removal
1. **crud.py** - 196 unused functions (legacy, replaced by services)
2. **schemas.py** - 47 unused classes (replaced by schemas_v2)
3. **business_logic.py** - Mixed usage, needs careful review

### Router Analysis
- Many endpoints in legacy routers are unused
- Focus on v1 routers for active functionality

### Safe to Remove Files
After thorough testing, these files appear unused:
- api/migrations/old_*.py (if any)
- api/scripts/* (one-time scripts)
- Test files not in use

## Cleanup Strategy

### Phase 1: Remove Obviously Unused
1. Delete crud.py (after verifying no imports)
2. Remove unused functions from business_logic.py
3. Clean up unused imports in all files

### Phase 2: Consolidate Schemas
1. Ensure all endpoints use schemas_v2
2. Remove schemas.py after migration
3. Update any remaining references

### Phase 3: Router Optimization
1. Identify truly used endpoints
2. Remove unused router files
3. Consolidate similar functionality

### Phase 4: Service Layer Enhancement
1. Move any remaining business logic to services
2. Ensure consistent patterns
3. Add missing service methods

## Testing Requirements

Before any cleanup:
1. Run full end-to-end tests
2. Test each API endpoint
3. Verify database operations
4. Check all import paths
5. Ensure deployment works

## Monitoring Points

Key files to never modify without extreme care:
- api/main.py (entry point)
- api/database.py (connection management)
- api/models.py (database schema)
- api/routers/v1/* (active endpoints)
- api/services/* (business logic)
- api/schemas_v2/* (data contracts)

---
This visualization should guide the cleanup and optimization process.