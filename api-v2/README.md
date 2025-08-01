# Enterprise API v2 - World-Class Pharmaceutical ERP

## Overview
This is the next-generation API for the AASO Pharma ERP system, designed with enterprise-grade architecture matching our powerful PostgreSQL multi-schema backend.

## Architecture Principles
1. **Schema-First Design**: APIs directly mirror our 10 database schemas
2. **Type Safety**: Full TypeScript support with auto-generated types
3. **OpenAPI 3.0**: Complete API documentation and client generation
4. **Enterprise Security**: JWT with org-context, role-based access
5. **Performance**: Optimized queries, caching, pagination
6. **Consistency**: Unified response formats and error handling

## Folder Structure
```
api-v2/
├── core/               # Core functionality (auth, database, config)
├── endpoints/          # API endpoints organized by schema
│   ├── master/        # Master data APIs
│   ├── parties/       # Customer & Supplier APIs
│   ├── inventory/     # Product & Stock APIs
│   ├── sales/         # Sales operations APIs
│   ├── procurement/   # Purchase APIs
│   ├── financial/     # Payment & Accounting APIs
│   ├── gst/          # GST compliance APIs
│   ├── compliance/    # Regulatory APIs
│   ├── system/       # System configuration APIs
│   └── analytics/    # Business intelligence APIs
├── models/           # Pydantic/TypeScript models
├── schemas/          # Request/Response schemas
├── services/         # Business logic layer
├── middleware/       # Auth, logging, error handling
├── utils/           # Helpers and utilities
└── openapi/         # OpenAPI specifications
```

## Key Features

### 1. Direct Schema Mapping
Each API module corresponds to a database schema:
- `/api/v2/master/*` → master schema
- `/api/v2/parties/*` → parties schema
- `/api/v2/inventory/*` → inventory schema
- etc.

### 2. Consistent Endpoints
```
GET    /api/v2/{schema}/{resource}      # List with filtering
POST   /api/v2/{schema}/{resource}      # Create
GET    /api/v2/{schema}/{resource}/{id} # Get by ID
PUT    /api/v2/{schema}/{resource}/{id} # Update
DELETE /api/v2/{schema}/{resource}/{id} # Delete
POST   /api/v2/{schema}/{resource}/bulk # Bulk operations
```

### 3. Advanced Features
- **Pagination**: Cursor-based for large datasets
- **Filtering**: Advanced query parameters
- **Sorting**: Multi-column with direction
- **Includes**: Related data loading
- **Field Selection**: Partial responses
- **Batch Operations**: Bulk create/update/delete

### 4. Response Format
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "2.0",
    "pagination": { ... }
  },
  "errors": []
}
```

### 5. Error Handling
```json
{
  "success": false,
  "data": null,
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "field": "gst_number",
      "message": "Invalid GST number format"
    }
  ],
  "meta": { ... }
}
```

## Migration Strategy

### Phase 1: Parallel APIs (Current)
- Keep existing `/api/v1/*` endpoints
- Build new `/api/v2/*` endpoints
- Frontend can gradually migrate

### Phase 2: Feature Parity
- Implement all v1 features in v2
- Add new enterprise features
- Comprehensive testing

### Phase 3: Migration
- Update frontend module by module
- Maintain backward compatibility
- Monitor and optimize

### Phase 4: Deprecation
- Mark v1 as deprecated
- Full migration to v2
- Remove v1 after transition period

## Quick Start

### 1. Install Dependencies
```bash
pip install fastapi pydantic sqlalchemy alembic
npm install -g @openapitools/openapi-generator-cli
```

### 2. Generate Types
```bash
python scripts/generate_types.py
npm run generate:types
```

### 3. Start Development Server
```bash
uvicorn api_v2.main:app --reload
```

### 4. Access Documentation
- Swagger UI: http://localhost:8000/api/v2/docs
- ReDoc: http://localhost:8000/api/v2/redoc
- OpenAPI JSON: http://localhost:8000/api/v2/openapi.json

## API Modules

### 1. Master APIs (`/api/v2/master`)
- Units of measurement
- Product categories
- Tax rates
- Document series

### 2. Party APIs (`/api/v2/parties`)
- Customers (with credit management)
- Suppliers (with payment terms)
- Advanced search and filtering

### 3. Inventory APIs (`/api/v2/inventory`)
- Products with HSN/GST
- Real-time stock levels
- Batch tracking with expiry
- Multi-warehouse support

### 4. Sales APIs (`/api/v2/sales`)
- Orders → Invoices flow
- Delivery tracking
- Payment collection
- Returns processing

### 5. Financial APIs (`/api/v2/financial`)
- Payment recording
- Ledger management
- Outstanding tracking
- Bank reconciliation

### 6. GST APIs (`/api/v2/gst`)
- GSTR-1 generation
- E-invoice creation
- E-way bills
- Tax calculation

### 7. Analytics APIs (`/api/v2/analytics`)
- Real-time dashboards
- Business KPIs
- Custom reports
- Data exports

## Development Guidelines

### 1. Code Organization
- One file per resource
- Consistent naming
- Comprehensive tests
- Type annotations

### 2. Security
- JWT authentication required
- Organization context
- Role-based permissions
- Audit logging

### 3. Performance
- Database query optimization
- Response caching
- Lazy loading
- Connection pooling

### 4. Documentation
- OpenAPI annotations
- Example requests/responses
- Error scenarios
- Integration guides

## Support
- Documentation: `/docs`
- Schema Reference: `/database/schema-docs`
- API Status: `/api/v2/health`
- Version Info: `/api/v2/version`