# AASO Pharma ERP - System Documentation

## Invoice Module

### Overview
The Invoice module handles all invoice-related operations including creation, calculation, payment tracking, and PDF generation. It's tightly integrated with the Order module for seamless transaction processing.

---

## Database Schema

### 1. `invoices` Table
Main invoice records with comprehensive financial tracking.

**Key Fields:**
```sql
invoice_id          INTEGER PK    -- Auto-incrementing
order_id            INTEGER FK    -- Links to orders table
invoice_number      VARCHAR(50)   -- Format: INV{YYYYMMDD}{SEQUENCE}
invoice_date        DATE          -- Invoice generation date
customer_id         INTEGER FK    -- Links to customers
customer_name       VARCHAR(200)  -- Denormalized for integrity
customer_gstin      VARCHAR(15)   -- GST number if registered
billing_address     TEXT          -- Full billing address
shipping_address    TEXT          -- Delivery address if different
invoice_status      VARCHAR(20)   -- 'generated', 'paid', 'cancelled'
payment_status      VARCHAR(20)   -- 'paid', 'unpaid', 'partial'
```

**Financial Fields:**
```sql
subtotal_amount     NUMERIC       -- Sum before tax/discount
discount_amount     NUMERIC       -- Invoice-level discount
taxable_amount      NUMERIC       -- Amount for tax calculation
cgst_amount         NUMERIC       -- Central GST (intrastate)
sgst_amount         NUMERIC       -- State GST (intrastate)
igst_amount         NUMERIC       -- Integrated GST (interstate)
total_tax_amount    NUMERIC       -- Sum of all taxes
round_off_amount    NUMERIC       -- Rounding adjustment
total_amount        NUMERIC       -- Final payable amount
paid_amount         NUMERIC       -- Amount paid so far
```

**GST Fields:**
```sql
gst_type            VARCHAR(20)   -- 'cgst_sgst' or 'igst'
place_of_supply     VARCHAR(2)    -- State code for GST
```

### 2. `invoice_items` Table
Line items with product and tax details.

```sql
item_id             INTEGER PK    -- Auto-incrementing
invoice_id          INTEGER FK    -- Links to invoices
product_id          INTEGER FK    -- Links to products
product_name        VARCHAR(200)  -- Denormalized
hsn_code            VARCHAR(10)   -- HSN/SAC code
batch_id            INTEGER FK    -- For batch tracking
batch_number        VARCHAR(50)   -- Batch identifier
quantity            INTEGER       -- Units sold
unit_price          NUMERIC       -- Price per unit
mrp                 NUMERIC       -- Maximum retail price
discount_percent    NUMERIC       -- Item discount %
discount_amount     NUMERIC       -- Item discount amount
gst_percent         NUMERIC       -- GST rate
cgst_amount         NUMERIC       -- Item CGST
sgst_amount         NUMERIC       -- Item SGST
igst_amount         NUMERIC       -- Item IGST
taxable_amount      NUMERIC       -- After discount
total_amount        NUMERIC       -- Item total
```

### 3. `invoice_payments` Table
Payment tracking with multiple payment support.

```sql
payment_id          INTEGER PK    -- Auto-incrementing
invoice_id          INTEGER FK    -- Links to invoices
payment_date        DATE          -- When paid
amount              NUMERIC       -- Payment amount (required)
payment_amount      NUMERIC       -- Same as amount (legacy)
payment_mode        VARCHAR(20)   -- 'cash','card','upi','cheque'
transaction_reference VARCHAR(100) -- For digital payments
bank_name           VARCHAR(100)  -- For cheque/transfer
cheque_number       VARCHAR(50)   -- If cheque payment
status              VARCHAR(20)   -- 'completed','pending','failed'
```

---

## API Endpoints

### 1. Calculate Invoice (`POST /api/v1/invoices/calculate-live`)
Calculates totals without creating invoice.

**Request:**
```json
{
  "customer_id": 34,
  "items": [
    {
      "product_id": 45,
      "quantity": 10,
      "discount_percent": 5
    }
  ],
  "discount_amount": 0,
  "delivery_charges": 0
}
```

**Response:**
```json
{
  "subtotal_amount": "250.00",
  "discount_amount": "12.50",
  "taxable_amount": "237.50",
  "cgst_amount": "14.25",
  "sgst_amount": "14.25",
  "igst_amount": "0.00",
  "total_tax_amount": "28.50",
  "round_off": "0.00",
  "final_amount": "266.00"
}
```

**Logic:**
1. Fetches product prices if not provided
2. Determines interstate/intrastate based on customer and seller states
3. Calculates item-wise tax
4. Applies invoice-level discount
5. Rounds to nearest rupee

### 2. Create Invoice (via Enterprise Order Service)
Invoices are created automatically when orders are placed.

**Flow:**
```python
# In enterprise_order_service.py
def create_order():
    # 1. Create order
    order_id = _create_order_record()
    
    # 2. Create invoice
    invoice_id, invoice_number = _create_comprehensive_invoice()
    
    # 3. Create invoice items
    _create_invoice_items()
    
    # 4. Process payment if provided
    if payment_amount > 0:
        _process_comprehensive_payment()
```

---

## Business Rules

### GST Calculation

**1. Determine Transaction Type:**
```python
# Get seller's state from organization
org_state = db.query("""
    SELECT business_settings->>'state' as state
    FROM organizations
    WHERE org_id = :org_id
""")

# Compare with customer state
if org_state and customer.state:
    is_interstate = org_state != customer.state
else:
    is_interstate = False  # Default to intrastate
```

**2. Apply Tax Rules:**
- **Intrastate**: CGST + SGST (GST rate split equally)
- **Interstate**: IGST (full GST rate)

**3. Calculation Example:**
```python
# For 12% GST on ₹100 taxable amount
if is_interstate:
    igst = 100 * 12 / 100 = ₹12
    cgst = 0, sgst = 0
else:
    cgst = 100 * 6 / 100 = ₹6
    sgst = 100 * 6 / 100 = ₹6
    igst = 0
```

### Invoice Number Generation

**Format:** `INV{YYYYMMDD}{SEQUENCE}`

```sql
-- Get next sequence for today
WITH today_invoices AS (
    SELECT invoice_number 
    FROM invoices 
    WHERE invoice_number LIKE 'INV20250724%'
)
SELECT COALESCE(
    MAX(CAST(SUBSTRING(invoice_number FROM 12) AS INTEGER)), 
    0
) + 1 as next_seq
FROM today_invoices;
```

**Example:** `INV202507240086` (86th invoice on 2025-07-24)

### Payment Processing

**Rules:**
1. Cash payments are marked as 'paid' immediately
2. Credit payments remain 'unpaid' until payment received
3. Partial payments update `paid_amount` and set status to 'partial'
4. Both `amount` and `payment_amount` fields must be populated (legacy)

---

## Integration Points

### With Order Module

**Tight Coupling:**
- One order = One invoice (1:1 relationship)
- Invoice created in same transaction as order
- Shared customer data (denormalized)
- Inventory updated before invoice creation

### With Frontend

**Quick Sale Flow:**
```javascript
// 1. Calculate totals (optional)
await api.post('/api/v1/invoices/calculate-live', {...})

// 2. Create order + invoice
const response = await api.post('/api/v1/enterprise-orders/quick-sale', {
    customer_id: 34,
    items: [{product_id: 45, quantity: 10}],
    payment_mode: "cash",
    payment_amount: 266.00
})

// 3. Response includes both order and invoice info
{
    order_id: 86,
    order_number: "ORD20250724-0015",
    invoice_id: 20,
    invoice_number: "INV202507240086",
    total_amount: 266.00
}
```

---

## Common Issues & Solutions

### 1. CGST/SGST Not Calculating
**Symptom:** Only IGST shows, CGST/SGST are 0
**Cause:** Customer state doesn't match seller state
**Fix:** Ensure organization has state set in business_settings

### 2. Invoice Items Missing Fields
**Symptom:** `column 'product_code' does not exist`
**Cause:** Schema mismatch between code and database
**Fix:** Use exact schema from PRODUCTION_TABLE_SCHEMAS.md

### 3. Payment Insert Fails
**Symptom:** `null value in column 'amount'`
**Cause:** Only payment_amount was set
**Fix:** Set both amount and payment_amount fields

---

## SQL Queries

### Daily Sales Summary
```sql
SELECT 
    DATE(invoice_date) as date,
    COUNT(*) as invoice_count,
    SUM(total_amount) as total_sales,
    SUM(total_tax_amount) as total_tax,
    SUM(CASE WHEN payment_status = 'paid' THEN total_amount ELSE 0 END) as paid_amount
FROM invoices
WHERE org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f'
GROUP BY DATE(invoice_date)
ORDER BY date DESC;
```

### Pending Payments Report
```sql
SELECT 
    i.invoice_number,
    i.customer_name,
    i.invoice_date,
    i.total_amount,
    COALESCE(i.paid_amount, 0) as paid,
    (i.total_amount - COALESCE(i.paid_amount, 0)) as balance
FROM invoices i
WHERE i.payment_status IN ('unpaid', 'partial')
AND i.org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f'
ORDER BY i.invoice_date;
```

---

## Files & Locations

### Backend Files
- `/api/services/enterprise_order_service.py` - Invoice creation logic
- `/api/routers/v1/invoices.py` - Invoice API endpoints
- `/api/models/invoice.py` - Pydantic models (if exists)

### Frontend Files
- `/src/components/sales/InvoiceFlow.js` - Invoice UI
- `/src/services/invoiceApiService.js` - API calls

### Database
- Schema: `/PRODUCTION_TABLE_SCHEMAS.md`
- Migrations: `/database/migrations/`

---

## Future Enhancements

1. **PDF Generation** - Full invoice PDF with logo, terms
2. **Email Integration** - Send invoice to customer
3. **Payment Gateway** - Online payment collection
4. **Credit Notes** - For returns/adjustments
5. **Recurring Invoices** - For subscriptions
6. **Bulk Operations** - Multiple invoice actions

---

*Last Updated: 2025-07-24*
*Note: Other modules will be documented as they are cleaned/solved*

---

## Delivery Challan Module

### Overview
The Delivery Challan module manages shipping documents for order delivery. Currently, it's implemented as a view over the orders table rather than a separate challan table.

### Database Schema

#### 1. `challans` Table
Main delivery challan records.

**Key Fields:**
```sql
challan_id              INTEGER PK    -- Auto-incrementing
order_id                INTEGER FK    -- Links to orders
customer_id             INTEGER FK    -- Links to customers
challan_number          TEXT          -- Unique challan number
challan_date            DATE          -- Challan creation date
dispatch_date           DATE          -- When dispatched
expected_delivery_date  DATE          -- Expected delivery
status                  TEXT          -- 'draft','dispatched','delivered','cancelled'
```

**Transport Details:**
```sql
vehicle_number          TEXT          -- Vehicle registration
driver_name             TEXT          -- Driver name
driver_phone            TEXT          -- Driver contact
transport_company       TEXT          -- Transport company name
lr_number               TEXT          -- LR/Docket number
freight_amount          NUMERIC       -- Freight charges
```

**Delivery Details:**
```sql
delivery_address        TEXT          -- Full address
delivery_city           TEXT          -- City
delivery_state          TEXT          -- State
delivery_pincode        TEXT          -- PIN code
delivery_contact_person TEXT          -- Contact person name
delivery_contact_phone  TEXT          -- Contact phone
```

**Tracking Fields:**
```sql
dispatch_time           TIMESTAMP     -- When dispatched
delivery_time           TIMESTAMP     -- When delivered
total_packages          INTEGER       -- Number of packages
total_weight            NUMERIC       -- Total weight
prepared_by             INTEGER       -- User who prepared
dispatched_by           INTEGER       -- User who dispatched
```

#### 2. `challan_items` Table
Items included in the challan.

```sql
challan_item_id         INTEGER PK    -- Auto-incrementing
challan_id              INTEGER FK    -- Links to challans
order_item_id           INTEGER FK    -- Links to order_items
batch_id                INTEGER FK    -- Links to batches
product_name            TEXT          -- Denormalized product name
batch_number            TEXT          -- Batch identifier
expiry_date             DATE          -- Batch expiry
ordered_quantity        INTEGER       -- Quantity ordered
dispatched_quantity     INTEGER       -- Quantity in this challan
pending_quantity        INTEGER       -- Remaining to dispatch
unit_price              NUMERIC       -- Price per unit
package_type            TEXT          -- Type of packaging
packages_count          INTEGER       -- Number of packages
```

#### 3. `challan_tracking` Table
Tracking history for challan status updates.

```sql
tracking_id             INTEGER PK    -- Auto-incrementing
challan_id              INTEGER FK    -- Links to challans
location                TEXT          -- Current location
status                  TEXT          -- Status at this point
timestamp               TIMESTAMP     -- When updated
remarks                 TEXT          -- Any remarks
updated_by              INTEGER       -- User who updated
updated_by_name         TEXT          -- User name (denormalized)
```

### Current Implementation Issues

**API Not Using Tables**: The current API (`delivery_challan.py`) is using orders table as a workaround instead of the actual challan tables.

**UPDATE (2025-07-24)**: Created new `enterprise_delivery_challan.py` that properly uses the actual challan tables!

### API Endpoints

#### Legacy Endpoints (uses orders table)

##### 1. GET `/api/v1/delivery-challan/`
List delivery challans with filtering options.

**Query Parameters:**
- `customer_id`: Filter by customer
- `status`: Filter by delivery status
- `start_date`, `end_date`: Date range filter
- `skip`, `limit`: Pagination

**Response:**
```json
[
  {
    "challan_id": 86,
    "customer_id": 35,
    "customer_name": "ABC Pharmacy",
    "challan_date": "2025-07-24",
    "total_amount": 246.00,
    "delivery_status": "pending",
    "delivery_address": "123 Main St",
    "delivery_date": null,
    "document_type": "challan"
  }
]
```

#### 2. GET `/api/v1/delivery-challan/{challan_id}`
Get detailed challan with items.

**Response:**
```json
{
  "challan_id": 86,
  "customer_name": "ABC Pharmacy",
  "delivery_status": "pending",
  "items": [
    {
      "product_id": 45,
      "product_name": "Paracetamol",
      "quantity": 10,
      "price": 24.60,
      "total_amount": 246.00
    }
  ]
}
```

#### 3. POST `/api/v1/delivery-challan/`
Creates a new challan (actually creates an order).

##### 4. PUT `/api/v1/delivery-challan/{challan_id}/status`
Update delivery status.

**Request:**
```json
{
  "status": "delivered",
  "delivery_date": "2025-07-24",
  "notes": "Delivered to front desk"
}
```

#### New Enterprise Endpoints (uses actual challan tables)

##### 1. POST `/api/v1/enterprise-delivery-challan/`
Create new delivery challan with proper tracking.

**Request:**
```json
{
  "order_id": 86,
  "customer_id": 35,
  "dispatch_date": "2025-07-24",
  "expected_delivery_date": "2025-07-25",
  "vehicle_number": "KA-01-AB-1234",
  "driver_name": "John Doe",
  "driver_phone": "9876543210",
  "transport_company": "ABC Logistics",
  "lr_number": "LR123456",
  "freight_amount": 500,
  "delivery_address": "123 Main St",
  "delivery_city": "Bengaluru",
  "delivery_state": "Karnataka", 
  "delivery_pincode": "560001",
  "delivery_contact_person": "Jane Smith",
  "delivery_contact_phone": "9876543211",
  "total_packages": 3,
  "total_weight": 15.5,
  "notes": "Handle with care",
  "items": [
    {
      "order_item_id": 101,
      "product_id": 45,
      "product_name": "Paracetamol",
      "batch_id": 123,
      "batch_number": "BATCH001",
      "expiry_date": "2026-12-31",
      "ordered_quantity": 100,
      "dispatched_quantity": 100,
      "unit_price": 2.50,
      "package_type": "Box",
      "packages_count": 2
    }
  ]
}
```

**Response:**
```json
{
  "challan_id": 1,
  "challan_number": "DC202507240001",
  "customer_name": "ABC Pharmacy",
  "status": "draft"
}
```

##### 2. GET `/api/v1/enterprise-delivery-challan/`
List all challans with comprehensive filtering.

##### 3. GET `/api/v1/enterprise-delivery-challan/{challan_id}`
Get detailed challan with items and tracking history.

##### 4. PUT `/api/v1/enterprise-delivery-challan/{challan_id}/dispatch`
Mark challan as dispatched.

**Request:**
```json
{
  "dispatch_date": "2025-07-24",
  "dispatch_location": "Main Warehouse",
  "vehicle_number": "KA-01-AB-1234",
  "driver_name": "John Doe",
  "driver_phone": "9876543210",
  "remarks": "Dispatched on time"
}
```

##### 5. PUT `/api/v1/enterprise-delivery-challan/{challan_id}/deliver`
Mark challan as delivered with GPS tracking.

**Request:**
```json
{
  "delivery_location": "Customer premise",
  "remarks": "Delivered to store manager",
  "latitude": 12.9716,
  "longitude": 77.5946
}
```

##### 6. POST `/api/v1/enterprise-delivery-challan/{challan_id}/tracking`
Add tracking update.

**Request:**
```json
{
  "location": "Highway checkpoint",
  "status": "in_transit",
  "remarks": "Crossed state border",
  "latitude": 12.8845,
  "longitude": 77.6036
}
```

##### 7. GET `/api/v1/enterprise-delivery-challan/analytics/summary`
Get delivery analytics and performance metrics.

### Issues with Current Implementation

1. **No Separate Challan Table**: 
   - Challans are just orders with delivery info
   - No unique challan numbering
   - Cannot have multiple challans per order

2. **Limited Functionality**:
   - No partial deliveries
   - No tracking of delivered vs ordered quantities
   - No vehicle/driver assignment
   - No proof of delivery

3. **Missing Features**:
   - Challan printing/PDF
   - Delivery route optimization
   - SMS/WhatsApp notifications
   - E-way bill integration

### Proposed Challan Schema

```sql
-- Delivery Challans Table
CREATE TABLE delivery_challans (
    challan_id SERIAL PRIMARY KEY,
    challan_number VARCHAR(50) UNIQUE NOT NULL,
    challan_date DATE NOT NULL DEFAULT CURRENT_DATE,
    order_id INTEGER REFERENCES orders(order_id),
    customer_id INTEGER REFERENCES customers(customer_id),
    
    -- Delivery Details
    delivery_type VARCHAR(20), -- 'full', 'partial'
    delivery_address TEXT,
    delivery_contact VARCHAR(100),
    delivery_phone VARCHAR(15),
    
    -- Status
    status VARCHAR(20), -- 'draft', 'ready', 'dispatched', 'delivered', 'cancelled'
    dispatched_at TIMESTAMP,
    delivered_at TIMESTAMP,
    
    -- Assignment
    vehicle_number VARCHAR(20),
    driver_name VARCHAR(100),
    driver_phone VARCHAR(15),
    
    -- E-way Bill
    eway_bill_number VARCHAR(50),
    eway_bill_date DATE,
    
    -- Tracking
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Challan Items
CREATE TABLE delivery_challan_items (
    item_id SERIAL PRIMARY KEY,
    challan_id INTEGER REFERENCES delivery_challans(challan_id),
    order_item_id INTEGER REFERENCES order_items(order_item_id),
    product_id INTEGER REFERENCES products(product_id),
    batch_id INTEGER REFERENCES batches(batch_id),
    
    ordered_quantity INTEGER NOT NULL,
    delivered_quantity INTEGER NOT NULL,
    pending_quantity INTEGER GENERATED ALWAYS AS (ordered_quantity - delivered_quantity) STORED,
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Delivery Tracking
CREATE TABLE delivery_tracking (
    tracking_id SERIAL PRIMARY KEY,
    challan_id INTEGER REFERENCES delivery_challans(challan_id),
    status VARCHAR(50),
    location TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    notes TEXT,
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tracked_by INTEGER
);
```

### Benefits of Separate Challan System

1. **Multiple Deliveries**: 
   - Split large orders into multiple challans
   - Partial deliveries with tracking

2. **Better Tracking**:
   - Unique challan numbers
   - Delivery timeline tracking
   - GPS coordinates for proof

3. **Compliance**:
   - E-way bill integration
   - GST compliant challan format
   - Digital signatures

4. **Operations**:
   - Driver/vehicle assignment
   - Route optimization
   - Delivery performance metrics

### Integration with Orders

**Flow:**
1. Order created and confirmed
2. Generate delivery challan(s)
3. Assign to driver/vehicle
4. Update status during delivery
5. Mark as delivered with proof
6. Update order delivery status

### Future Enhancements

1. **Mobile App for Drivers**
   - View assigned challans
   - Update delivery status
   - Capture signatures/photos
   - GPS tracking

2. **Customer Features**
   - Track delivery in real-time
   - SMS/WhatsApp notifications
   - Delivery feedback

3. **Analytics**
   - Delivery performance reports
   - Driver efficiency metrics
   - Route optimization

4. **Integration**
   - E-way bill API
   - Vehicle tracking systems
   - Customer notification systems