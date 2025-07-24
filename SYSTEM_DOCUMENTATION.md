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