# Backend Architecture

## System Overview
FastAPI-based microservice architecture with PostgreSQL database, deployed on Railway with Supabase for database hosting.

```
┌─────────────────────────────────────────────────────────┐
│                  Client Layer                           │
│  (React Frontend, Mobile Apps, Third-party APIs)       │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────┐
│                  API Gateway                            │
│              (FastAPI Routes)                           │
├─────────────────────────────────────────────────────────┤
│              Business Logic Layer                       │
│  ┌─────────────┬──────────────┬──────────────────────┐ │
│  │   Sales     │   Purchase   │      Inventory       │ │
│  │   Service   │   Service    │      Service         │ │
│  └─────────────┴──────────────┴──────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│              Data Access Layer                          │
│            (SQLAlchemy ORM + CRUD)                     │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────┐
│              Database Layer                             │
│            PostgreSQL (Supabase)                       │
└─────────────────────────────────────────────────────────┘
```

## Technology Stack
- **API Framework**: FastAPI 0.104+
- **Database**: PostgreSQL (hosted on Supabase)
- **ORM**: SQLAlchemy 2.0 with async support
- **Authentication**: JWT + Supabase Auth
- **Validation**: Pydantic 2.0
- **Deployment**: Railway
- **Migrations**: Alembic

## Project Structure
```
api/
├── main.py              # FastAPI app initialization
├── routers/             # API endpoints
│   ├── products.py      # Product management
│   ├── customers.py     # Customer operations
│   ├── sales.py         # Sales & invoicing
│   ├── purchases.py     # Purchase management
│   ├── inventory.py     # Stock operations
│   ├── returns.py       # Returns processing
│   └── reports.py       # Analytics
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
├── services/            # Business logic
├── utils/               # Utilities & helpers
└── dependencies.py      # FastAPI dependencies
```

## Core Modules

### 1. Sales Module
- **Purpose**: Invoice generation and sales processing
- **Key Components**: Order creation, GST calculation, payment tracking
- **Database Tables**: orders, invoices, invoice_items
- **Business Logic**: Price calculation, tax computation, stock validation

### 2. Purchase Module  
- **Purpose**: Vendor management and procurement
- **Key Components**: PO creation, GRN processing, vendor payments
- **Database Tables**: purchase_orders, grn, vendors
- **Business Logic**: Batch creation, cost tracking, supplier management

### 3. Inventory Module
- **Purpose**: Stock management and tracking
- **Key Components**: Batch tracking, expiry management, stock adjustments
- **Database Tables**: products, batches, stock_movements
- **Business Logic**: FIFO/LIFO, reorder points, write-offs

### 4. Returns Module
- **Purpose**: Sales and purchase returns
- **Key Components**: Credit notes, debit notes, GST reversal
- **Database Tables**: sales_returns, purchase_returns, credit_notes
- **Business Logic**: Return validation, tax adjustments, stock updates

## Data Flow Architecture

### Request Flow
```
Client Request → Router → Service Layer → CRUD → Database
      ↓
Response ← Schema ← Business Logic ← Data Access ← Query Result
```

### Key Patterns
- **Repository Pattern**: CRUD operations abstracted
- **Service Layer**: Business logic separation
- **Schema Validation**: Pydantic for request/response
- **Dependency Injection**: FastAPI dependencies for auth/db

## Database Design

### Multi-tenant Architecture
- Every table has `org_id` for organization isolation
- Row Level Security (RLS) enforced at database level
- Shared schema, isolated data approach

### Key Relationships
```sql
customers ←→ invoices ←→ invoice_items → products
                           ↓
products ←→ batches ←→ inventory_movements
    ↓
purchase_orders ←→ grn ←→ vendors
```

## Authentication & Security
- **JWT Tokens**: Supabase Auth integration
- **Role-based Access**: Admin, Manager, User roles
- **RLS Policies**: Database-level security
- **API Rate Limiting**: Planned implementation
- **Request Validation**: Comprehensive Pydantic schemas

## Performance Optimizations
- **Connection Pooling**: SQLAlchemy pool configuration
- **Query Optimization**: Eager loading, indexed queries
- **Response Caching**: For frequently accessed data
- **Async Operations**: Non-blocking database operations

## Current Status
- ✅ Core APIs operational
- ✅ Database schema deployed
- ✅ Authentication working
- 🚧 Schema alignment issues (some model-DB mismatches)
- 🚧 Advanced reporting features

## Deployment Architecture
- **Production**: Railway platform
- **Database**: Supabase PostgreSQL
- **Auto-deployment**: GitHub integration
- **Environment**: Environment variables via Railway
- **Monitoring**: Basic health checks implemented