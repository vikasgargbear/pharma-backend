# AASO Pharma Backend - System Architecture

## Overview
This document provides a comprehensive view of the AASO Pharma ERP system architecture, including database structure, API organization, deployment details, and development guidelines.

## System Components

### 1. Database Architecture

#### Database Location: Supabase (PostgreSQL)
- **Connection**: `postgresql://postgres:xxx@db.xfytbzavuvpbmxkhqvkb.supabase.co:5432/postgres`
- **Environment**: Production database hosted on Supabase
- **SSL**: Required for all connections

#### Database Schema Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    CORE BUSINESS ENTITIES                    │
├─────────────────────────────────────────────────────────────┤
│ organizations                                               │
│ ├── org_id (UUID, PK)                                      │
│ ├── org_name, gstin, address, etc.                        │
│ └── created_at, updated_at                                │
│                                                            │
│ customers                                                  │
│ ├── customer_id (SERIAL, PK)                              │
│ ├── org_id (FK -> organizations)                          │
│ ├── customer_code, customer_name, gstin                   │
│ ├── credit_limit, credit_days                             │
│ └── address, contact details                              │
│                                                            │
│ products                                                   │
│ ├── product_id (SERIAL, PK)                              │
│ ├── org_id (FK -> organizations)                          │
│ ├── product_code, product_name                            │
│ ├── category, manufacturer, composition                    │
│ └── hsn_code, gst_percent                                │
│                                                            │
│ batches                                                    │
│ ├── batch_id (SERIAL, PK)                                │
│ ├── product_id (FK -> products)                          │
│ ├── batch_number, expiry_date                            │
│ ├── quantity_available, quantity_sold                     │
│ └── mrp, purchase_price, selling_price                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    TRANSACTION ENTITIES                      │
├─────────────────────────────────────────────────────────────┤
│ orders                                                      │
│ ├── order_id (SERIAL, PK)                                 │
│ ├── org_id (FK -> organizations)                          │
│ ├── customer_id (FK -> customers)                         │
│ ├── order_number, order_date, order_status                │
│ ├── final_amount, paid_amount                             │
│ └── delivery details, payment terms                       │
│                                                            │
│ order_items                                                │
│ ├── order_item_id (SERIAL, PK)                           │
│ ├── order_id (FK -> orders)                              │
│ ├── product_id (FK -> products)                          │
│ ├── batch_id (FK -> batches)                             │
│ ├── quantity, selling_price                              │
│ └── discount, tax details                                │
│                                                            │
│ invoices                                                   │
│ ├── invoice_id (SERIAL, PK)                              │
│ ├── org_id (FK -> organizations)                          │
│ ├── order_id (FK -> orders)                              │
│ ├── invoice_number, invoice_date                         │
│ ├── total_amount, paid_amount                            │
│ └── gst details, payment status                          │
│                                                            │
│ invoice_items                                             │
│ ├── invoice_item_id (SERIAL, PK)                         │
│ ├── invoice_id (FK -> invoices)                          │
│ └── product details, pricing, tax                        │
│                                                            │
│ invoice_payments                                          │
│ ├── payment_id (SERIAL, PK)                              │
│ ├── invoice_id (FK -> invoices)                          │
│ └── payment details, mode, reference                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    INVENTORY ENTITIES                        │
├─────────────────────────────────────────────────────────────┤
│ inventory_movements                                         │
│ ├── movement_id (SERIAL, PK)                              │
│ ├── batch_id (FK -> batches)                              │
│ ├── movement_type (purchase/sale/adjustment/return)       │
│ └── quantity_in, quantity_out, reference                  │
│                                                            │
│ stock_adjustments                                          │
│ ├── adjustment_id (SERIAL, PK)                            │
│ └── adjustment details, reason, approval                  │
└─────────────────────────────────────────────────────────────┘

## 2. Application Architecture

### Directory Structure (Proposed Enterprise Standard)
```
pharma-backend/
├── api/
│   ├── core/                    # Core utilities
│   │   ├── config.py           # Settings management
│   │   ├── database.py         # Database connection
│   │   ├── security.py         # Auth & security
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── middleware.py       # Custom middleware
│   │
│   ├── models/                  # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── organization.py
│   │   ├── customer.py
│   │   ├── product.py
│   │   ├── order.py
│   │   ├── invoice.py
│   │   └── inventory.py
│   │
│   ├── schemas/                 # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── v1/                 # Version 1 schemas
│   │   │   ├── customer.py
│   │   │   ├── product.py
│   │   │   ├── order.py
│   │   │   ├── invoice.py
│   │   │   └── inventory.py
│   │   └── v2/                 # Version 2 schemas (future)
│   │
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   ├── customer_service.py
│   │   ├── order_service.py
│   │   ├── billing_service.py
│   │   ├── inventory_service.py
│   │   └── report_service.py
│   │
│   ├── routers/                # API endpoints
│   │   ├── __init__.py
│   │   ├── v1/                 # Version 1 endpoints
│   │   │   ├── __init__.py
│   │   │   ├── customers.py
│   │   │   ├── products.py
│   │   │   ├── orders.py
│   │   │   ├── billing.py
│   │   │   ├── inventory.py
│   │   │   └── reports.py
│   │   └── health.py           # Health checks
│   │
│   ├── migrations/             # Database migrations
│   │   ├── versions/
│   │   └── alembic.ini
│   │
│   └── main.py                 # FastAPI application
│
├── tests/                      # Test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── scripts/                    # Utility scripts
│   ├── init_db.py
│   ├── seed_data.py
│   └── backup_db.py
│
├── docs/                       # Documentation
│   ├── api/
│   ├── database/
│   └── deployment/
│
├── .env.example               # Environment template
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 3. API Structure

### Endpoint Organization
All APIs follow RESTful conventions with consistent versioning:

```
BASE_URL: https://pharma-backend-production-0c09.up.railway.app

/api/v1/
├── /customers
│   ├── GET    /                    # List customers
│   ├── POST   /                    # Create customer
│   ├── GET    /{id}               # Get customer
│   ├── PUT    /{id}               # Update customer
│   ├── DELETE /{id}               # Delete customer
│   ├── GET    /{id}/ledger        # Customer ledger
│   ├── GET    /{id}/outstanding   # Outstanding invoices
│   └── POST   /{id}/payment       # Record payment
│
├── /products
│   ├── GET    /                    # List products
│   ├── POST   /                    # Create product
│   ├── GET    /{id}               # Get product
│   ├── PUT    /{id}               # Update product
│   ├── GET    /{id}/batches       # Product batches
│   └── GET    /{id}/stock         # Stock levels
│
├── /orders
│   ├── GET    /                    # List orders
│   ├── POST   /                    # Create order
│   ├── GET    /{id}               # Get order
│   ├── PUT    /{id}               # Update order
│   ├── POST   /{id}/confirm       # Confirm order
│   ├── POST   /{id}/cancel        # Cancel order
│   └── POST   /{id}/deliver       # Mark delivered
│
├── /billing
│   ├── POST   /invoices           # Generate invoice
│   ├── GET    /invoices           # List invoices
│   ├── GET    /invoices/{id}      # Get invoice
│   ├── PUT    /invoices/{id}/cancel # Cancel invoice
│   ├── POST   /payments           # Record payment
│   ├── GET    /payments           # List payments
│   ├── GET    /gst/gstr1          # GSTR-1 report
│   └── GET    /summary            # Billing summary
│
├── /inventory
│   ├── GET    /stock              # Current stock
│   ├── GET    /movements          # Stock movements
│   ├── POST   /adjustments        # Stock adjustment
│   ├── GET    /expiring           # Expiring items
│   └── GET    /reorder            # Reorder report
│
└── /reports
    ├── GET    /sales              # Sales reports
    ├── GET    /purchase           # Purchase reports
    ├── GET    /gst                # GST reports
    └── GET    /analytics          # Analytics dashboard
```

## 4. Deployment Architecture

### Current Deployment
```
┌─────────────────────────────────────────────────────────────┐
│                         PRODUCTION                           │
├─────────────────────────────────────────────────────────────┤
│ Railway.app                                                 │
│ ├── Application: pharma-backend                            │
│ ├── URL: pharma-backend-production-0c09.up.railway.app    │
│ ├── Auto-deploy: From GitHub main branch                   │
│ └── Environment: Production                                │
│                                                            │
│ Supabase                                                   │
│ ├── Database: PostgreSQL                                   │
│ ├── Project: xfytbzavuvpbmxkhqvkb                        │
│ ├── Region: AWS us-east-1                                 │
│ └── Connection: Pooled with SSL                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                        DEVELOPMENT                           │
├─────────────────────────────────────────────────────────────┤
│ Local Machine                                               │
│ ├── Application: Running on localhost:8080                 │
│ ├── Database: Connected to Supabase (same as prod)        │
│ └── Hot reload: Enabled with --reload flag                │
└─────────────────────────────────────────────────────────────┘
```

## 5. Key Design Decisions

### Database Naming Conventions
- **Tables**: snake_case, plural (e.g., `customers`, `order_items`)
- **Columns**: snake_case (e.g., `customer_name`, `created_at`)
- **Primary Keys**: `{table_singular}_id` (e.g., `customer_id`)
- **Foreign Keys**: Same as referenced primary key
- **Timestamps**: `created_at`, `updated_at`

### API Conventions
- **Versioning**: All APIs versioned under `/api/v1/`
- **Response Format**: Consistent JSON structure
- **Error Handling**: Standardized error responses
- **Authentication**: Bearer token (to be implemented)
- **Pagination**: `skip` and `limit` parameters
- **Filtering**: Query parameters for filtering

### Code Organization
- **Models**: One file per major entity
- **Schemas**: Grouped by version for backward compatibility
- **Services**: Business logic separated from routes
- **Routers**: Thin controllers, delegate to services

## 6. Development Workflow

### Local Development
1. Clone repository
2. Copy `.env.example` to `.env`
3. Install dependencies: `pip install -r requirements.txt`
4. Run migrations: `python -m api.migrations.run_all`
5. Start server: `uvicorn api.main:app --reload --port 8080`

### Adding New Features
1. Create/update database schema
2. Generate migration script
3. Create/update SQLAlchemy models
4. Create/update Pydantic schemas
5. Implement service layer
6. Add API endpoints
7. Write tests
8. Update documentation

### Deployment Process
1. Push to GitHub main branch
2. Railway auto-deploys
3. Run migrations if needed
4. Verify health checks
5. Test in production

## 7. Current Issues to Fix

### Immediate Actions Required
1. **Database**: Run billing migration on production
2. **API Consistency**: Standardize all endpoints to use `/api/v1/` prefix
3. **Schema Alignment**: Fix mismatches between code and database
4. **File Organization**: Restructure according to proposed layout
5. **Documentation**: Complete API documentation

### Technical Debt
1. Mixed schema versions (v1, v2, base_schemas)
2. Inconsistent file naming and organization
3. Missing proper migration system
4. No automated tests
5. No proper error logging system

## 8. Security Considerations

### Current Implementation
- CORS configured for specific origins
- SQL injection prevention via parameterized queries
- Input validation with Pydantic
- Rate limiting middleware

### To Be Implemented
- JWT authentication
- Role-based access control
- API key management
- Audit logging
- Data encryption at rest

## 9. Monitoring & Observability

### Current
- Basic health check endpoints
- Process time headers
- Console logging

### Planned
- Structured logging with correlation IDs
- Metrics collection (Prometheus)
- Distributed tracing
- Error tracking (Sentry)
- Performance monitoring

## 10. Contact & Support

### Development Team
- Repository: GitHub (to be specified)
- Issues: GitHub Issues
- Documentation: This file and `/docs` directory

### Infrastructure
- Railway Dashboard: [Access Required]
- Supabase Dashboard: [Access Required]
- Monitoring: [To be implemented]