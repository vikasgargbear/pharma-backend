# AASO Pharma Backend - System Dependency Map

This document provides a comprehensive map of all system dependencies, file structure, and relationships in the working pharma backend system.

Generated on: 2025-07-18
System State: Working after revert from consolidation attempt

## Table of Contents
1. [Core Application Files](#core-application-files)
2. [Database Layer](#database-layer)
3. [API Router Structure](#api-router-structure)
4. [Schemas and Models](#schemas-and-models)
5. [Service Layer](#service-layer)
6. [Import Dependencies](#import-dependencies)
7. [External Dependencies](#external-dependencies)
8. [Deployment Configuration](#deployment-configuration)

## Core Application Files

### Main Entry Point
- **api/main.py**
  - Entry point for the FastAPI application
  - Imports: models, base_schemas, database, core.config, routers, routers.v1
  - Configures middleware: CORS, security headers, rate limiting, audit logging
  - Includes all routers from both `/routers` and `/routers/v1`
  - Health check endpoints: `/health`, `/health/detailed`, `/health/readiness`, `/health/liveness`

### Configuration
- **api/core/config.py**
  - System configuration using pydantic BaseSettings
  - Environment variables handling
  - Database URL construction (Supabase/SQLite)
  - Dependencies: pydantic, os, dotenv

## Database Layer

### Database Connection
- **api/database.py**
  - SQLAlchemy engine and session management
  - Imports: core.config, sqlalchemy
  - Functions: get_db(), init_database(), check_database_connection()

- **api/core/database_manager.py**
  - Enhanced database management with circuit breaker pattern
  - Connection pooling and retry logic
  - Health status monitoring
  - Imports: sqlalchemy, time, logging

### Database Models
- **api/models.py**
  - All SQLAlchemy ORM models
  - Tables: organizations, products, customers, orders, order_items, batches, invoices, invoice_items, etc.
  - Imports: sqlalchemy, uuid, datetime, decimal

## API Router Structure

### V1 API Routers (/api/v1)
1. **api/routers/v1/customers.py**
   - Customer management endpoints
   - Imports: schemas_v2.customer, services.customer_service
   - Endpoints: CRUD, ledger, outstanding, payments

2. **api/routers/v1/orders.py**
   - Order management endpoints
   - Imports: schemas_v2.order, services.order_service
   - Endpoints: create, list, get, update status
   - Features: Batch selection (FIFO), inventory allocation

3. **api/routers/v1/inventory.py**
   - Inventory management endpoints
   - Imports: schemas_v2.inventory, services.inventory_service
   - Endpoints: stock status, movements, adjustments, reports

4. **api/routers/v1/billing.py**
   - Billing and GST endpoints
   - Imports: schemas_v2.billing, services.billing_service
   - Router prefix: "/api/v1/billing" (NOT "/billing")
   - Endpoints: invoice generation, payments, GST reports

### Legacy Routers
- **api/routers/products.py** - Product management
- **api/routers/simple_delivery.py** - Delivery tracking
- **api/routers/db_inspect.py** - Database inspection tools
- **api/routers/migrations.py** - Migration endpoints
- **api/routers/migrations_v2.py** - V2 migration endpoints
- **api/routers/organizations.py** - Organization management
- **api/routers/customers_simple.py** - Simple customer endpoints

## Schemas and Models

### Pydantic V2 Schemas
Directory: **api/schemas_v2/**

1. **customer.py**
   - CustomerCreate, CustomerUpdate, CustomerResponse
   - CustomerLedgerResponse, CustomerOutstandingResponse
   - PaymentRecord, PaymentResponse

2. **order.py**
   - OrderCreate, OrderUpdate, OrderResponse
   - OrderItemBase, OrderItemCreate, OrderItemResponse
   - OrderStatus enum

3. **inventory.py**
   - StockStatus, InventoryMovement
   - BatchInfo, ExpiryAlert
   - StockReportResponse

4. **billing.py**
   - InvoiceCreate, InvoiceResponse
   - PaymentCreate, PaymentResponse
   - InvoiceStatus, PaymentMode, GSTType enums
   - GSTR1Summary, InvoiceSummary

### Base Schemas
- **api/base_schemas.py**
  - ProductBase, ProductCreate, ProductResponse
  - Simplified schemas for backward compatibility
  - DEFAULT_ORG_ID constant

## Service Layer

Directory: **api/services/**

1. **customer_service.py**
   - Customer business logic
   - Methods: generate_customer_code, get_customer_statistics
   - Credit limit validation, payment recording

2. **order_service.py**
   - Order processing logic
   - Methods: validate_inventory, allocate_inventory
   - Batch selection using FIFO
   - Status management

3. **inventory_service.py**
   - Inventory management logic
   - Stock tracking, movement recording
   - Expiry monitoring, reorder alerts

4. **billing_service.py**
   - Invoice generation from orders
   - GST calculations (CGST/SGST vs IGST)
   - Payment recording and allocation
   - GST report generation

## Import Dependencies

### Critical Import Paths
```python
# Main app imports
from . import models, base_schemas as schemas
from .database import SessionLocal, engine, get_db
from .core.config import settings

# Router imports
from .routers import products, simple_delivery, db_inspect
from .routers.v1 import customers_router, orders_router, inventory_router, billing_router

# Schema imports (v2)
from ...schemas_v2.customer import CustomerCreate, CustomerResponse
from ...schemas_v2.order import OrderCreate, OrderResponse
from ...schemas_v2.billing import InvoiceCreate, InvoiceResponse

# Service imports
from ...services.customer_service import CustomerService
from ...services.order_service import OrderService
from ...services.billing_service import BillingService
```

### Import Hierarchy
1. Core modules (database, config) have no internal dependencies
2. Models depend on database
3. Schemas have no dependencies (pure Pydantic)
4. Services depend on models and schemas
5. Routers depend on services, schemas, and database
6. Main app depends on all above

## External Dependencies

### Python Packages (requirements.txt)
```
fastapi==0.115.5
uvicorn[standard]==0.32.1
sqlalchemy==2.0.36
psycopg2-binary==2.9.10
pydantic==2.11.0
pydantic-settings==2.7.0
python-dotenv==1.0.1
python-multipart==0.0.12
```

### System Dependencies
- PostgreSQL (via Supabase)
- Python 3.11+
- Environment variables for configuration

## Deployment Configuration

### Railway Configuration
- **railway.toml**
  ```toml
  [build]
  builder = "NIXPACKS"
  
  [deploy]
  startCommand = "uvicorn api.main:app --host 0.0.0.0 --port $PORT"
  healthcheckPath = "/health"
  healthcheckTimeout = 100
  restartPolicyType = "ON_FAILURE"
  restartPolicyMaxRetries = 10
  ```

### Environment Variables
Required in production:
- `DATABASE_URL` - PostgreSQL connection string
- `DATABASE_TYPE` - Set to "postgresql"
- `SECRET_KEY` - Application secret
- `ENVIRONMENT` - Set to "production"

## Directory Structure
```
pharma-backend/
├── api/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── models.py               # SQLAlchemy models
│   ├── database.py             # Database connection
│   ├── base_schemas.py         # Basic Pydantic schemas
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration
│   │   ├── database_manager.py # Enhanced DB management
│   │   └── audit.py            # Audit logging
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── products.py
│   │   ├── simple_delivery.py
│   │   ├── db_inspect.py
│   │   ├── migrations.py
│   │   ├── migrations_v2.py
│   │   ├── organizations.py
│   │   ├── customers_simple.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── customers.py    # /api/v1/customers
│   │       ├── orders.py       # /api/v1/orders
│   │       ├── inventory.py    # /api/v1/inventory
│   │       └── billing.py      # /api/v1/billing
│   ├── schemas_v2/
│   │   ├── __init__.py
│   │   ├── customer.py
│   │   ├── order.py
│   │   ├── inventory.py
│   │   └── billing.py
│   └── services/
│       ├── __init__.py
│       ├── customer_service.py
│       ├── order_service.py
│       ├── inventory_service.py
│       └── billing_service.py
├── requirements.txt
├── railway.toml
├── runtime.txt
├── .gitignore
├── README.md
└── docs/
    ├── SYSTEM_ARCHITECTURE.md
    ├── DATABASE_SCHEMA.md
    └── DEPLOYMENT_GUIDE.md
```

## Critical System Dependencies

### Order Creation Flow
1. **Endpoint**: POST /api/v1/orders/
2. **Schema**: OrderCreate (requires org_id, items array)
3. **Service**: OrderService.validate_inventory → allocate_inventory
4. **Database**: Updates orders, order_items, batches, inventory_movements
5. **Features**: Automatic batch selection (FIFO), inventory tracking

### Invoice Generation Flow
1. **Endpoint**: POST /api/v1/billing/invoices
2. **Schema**: InvoiceCreate (requires order_id)
3. **Service**: BillingService.create_invoice_from_order
4. **Database**: Creates invoices, invoice_items
5. **Features**: GST calculation, state-based tax logic

### Key Database Relationships
- customers → orders → order_items → products/batches
- orders → invoices → invoice_items
- invoices → invoice_payments
- products → batches → inventory_movements

## Maintenance Notes

1. **Always test locally before deployment**
2. **Never consolidate files without mapping imports first**
3. **Router prefixes must match exactly (e.g., "/api/v1/billing")**
4. **Database column names must match exactly (e.g., final_amount not total_amount)**
5. **All financial calculations use Decimal type**
6. **FIFO batch selection is critical for pharmaceutical compliance**

## End-to-End Test Checklist

- [ ] Server starts without errors
- [ ] Health endpoints respond
- [ ] Customer CRUD operations work
- [ ] Order creation with automatic batch selection
- [ ] Invoice generation from orders
- [ ] Payment recording
- [ ] Inventory tracking updates
- [ ] GST calculations are correct

---
This dependency map should be updated whenever significant changes are made to the system structure.