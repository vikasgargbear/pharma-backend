# Backend Modules Overview

## Core API Modules

### 1. Products Module (`/api/products`)
**Purpose**: Product catalog management and search

**Key Endpoints**:
- `GET /products/search` - Search products with batch info
- `POST /products` - Create new products with batch
- `GET /products/{id}` - Get product details
- `PUT /products/{id}` - Update product information

**Features**:
- Pack configuration (10*10, 100ML formats)
- Automatic batch creation with expiry tracking
- HSN code management for GST compliance
- Inventory integration with real-time stock

**Current Status**: ❌ 500 errors due to schema mismatches

---

### 2. Customers Module (`/api/customers`)
**Purpose**: Customer relationship management

**Key Endpoints**:
- `GET /customers/search` - Find customers by name/phone/GSTIN
- `POST /customers` - Create new customers
- `GET /customers/{id}` - Customer details with outstanding balance
- `PUT /customers/{id}` - Update customer information

**Features**:
- GSTIN validation for GST compliance
- Credit limit management
- Outstanding balance tracking
- Multi-location customer support

**Current Status**: ✅ Basic functionality working

---

### 3. Sales Module (`/api/sales`)
**Purpose**: Invoice generation and sales processing

**Key Endpoints**:
- `POST /sales/invoices` - Create GST-compliant invoices
- `GET /sales/invoices/{id}` - Invoice details
- `GET /sales/invoices/search` - Search invoices
- `PUT /sales/invoices/{id}/payment` - Update payment status

**Features**:
- Automatic GST calculation (CGST/SGST/IGST)
- Multiple payment modes
- Stock validation and adjustment
- PDF invoice generation
- Sequential invoice numbering

**Current Status**: 🚧 Basic structure in place, needs completion

---

### 4. Purchase Module (`/api/purchases`)
**Purpose**: Procurement and vendor management

**Key Endpoints**:
- `POST /purchases/orders` - Create purchase orders
- `POST /purchases/grn` - Goods receipt note
- `GET /purchases/orders/{id}` - Purchase order details
- `POST /purchases/bills` - Vendor bill entry

**Features**:
- Automatic batch number generation
- Supplier management
- Three-way matching (PO-GRN-Bill)
- Payment terms and credit tracking
- GST input credit management

**Current Status**: 🚧 Partial implementation

---

### 5. Inventory Module (`/api/inventory`)
**Purpose**: Stock management and tracking

**Key Endpoints**:
- `GET /inventory/stock` - Current stock levels
- `POST /inventory/adjustments` - Stock adjustments
- `POST /inventory/writeoff` - Stock write-offs
- `GET /inventory/movements` - Stock movement history

**Features**:
- Batch-wise tracking with expiry dates
- FIFO/LIFO cost calculation
- Stock adjustment with reasons
- Expiry alerts and management
- Multi-location inventory

**Current Status**: 🚧 Basic endpoints exist, needs enhancement

---

### 6. Returns Module (`/api/returns`)
**Purpose**: Sales and purchase returns processing

**Key Endpoints**:
- `POST /returns/sales` - Customer returns with credit notes
- `POST /returns/purchase` - Supplier returns with debit notes
- `GET /returns/{id}` - Return details
- `POST /returns/approve` - Return approval workflow

**Features**:
- GST-compliant credit/debit notes
- Automatic stock adjustments
- Return reason tracking
- Partial return support
- ITC reversal for write-offs

**Current Status**: 🚧 Planned implementation

---

### 7. Reports Module (`/api/reports`)
**Purpose**: Analytics and business intelligence

**Key Endpoints**:
- `GET /reports/sales` - Sales analytics
- `GET /reports/inventory` - Stock reports
- `GET /reports/gst/gstr1` - GST return generation
- `GET /reports/aging` - Receivables aging

**Features**:
- Customizable date ranges
- Export to Excel/PDF
- Real-time dashboards
- Regulatory compliance reports
- Business KPI tracking

**Current Status**: 🚧 Framework in place, reports to be built

---

### 8. Payments Module (`/api/payments`)
**Purpose**: Payment processing and reconciliation

**Key Endpoints**:
- `POST /payments` - Record customer payments
- `POST /payments/allocate` - Allocate payments to invoices
- `GET /payments/customer-statement` - Customer statement
- `GET /payments/aging` - Aging analysis

**Features**:
- Multiple payment modes (Cash, UPI, Card, Cheque)
- Payment allocation to multiple invoices
- Advance payment handling
- Bank reconciliation support
- Payment reminder system

**Current Status**: 🚧 Basic structure planned

---

## System Modules

### Authentication (`/api/auth`)
**Purpose**: User authentication and authorization
- JWT token management
- Role-based access control
- Supabase Auth integration
- Session management

**Current Status**: ✅ Basic auth working

### Database Tools (`/api/database-tools`)
**Purpose**: Database inspection and management
- Schema inspection
- Table analysis
- Migration support
- Debugging utilities

**Current Status**: ✅ Operational

### Health Check (`/api/health`)
**Purpose**: System monitoring
- API health status
- Database connectivity
- Version information
- Performance metrics

**Current Status**: ✅ Working

---

## Module Dependencies

### Data Flow Between Modules
```
Products → Inventory → Sales → Payments
    ↓         ↓         ↓         ↓
Purchase → Stock → Returns → Receivables
    ↓         ↓         ↓         ↓
Vendors → Batches → Credits → Reports
```

### Shared Components
- **CRUD Base Classes**: Common database operations
- **Schema Validation**: Pydantic models
- **Auth Dependencies**: JWT validation
- **Error Handling**: Standardized error responses
- **Logging**: Centralized logging system

---

## Implementation Priority

### Phase 1 (Critical)
1. Fix Products module 500 errors
2. Complete basic CRUD for all modules
3. Implement core sales workflow
4. Basic inventory operations

### Phase 2 (Important)
1. Purchase workflow completion
2. Returns processing
3. Payment allocation
4. Basic reporting

### Phase 3 (Enhancement)
1. Advanced analytics
2. GST compliance features
3. Integration capabilities
4. Performance optimizations

---

*Current Focus: Stabilizing core modules and fixing critical errors*