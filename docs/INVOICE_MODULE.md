# Invoice Module Documentation

## Overview
The Invoice module handles all invoice-related operations including creation, calculation, payment tracking, and PDF generation.

## Database Tables

### 1. `invoices`
Main invoice records table.

**Key Fields:**
- `invoice_id` (PK): Auto-incrementing primary key
- `order_id` (FK): Links to orders table
- `invoice_number`: Format `INV{YYYYMMDD}{SEQUENCE}` (e.g., INV202507240086)
- `customer_name`, `customer_phone`: Denormalized for data integrity
- `billing_address`, `shipping_address`: Full address details
- `gst_type`: 'cgst_sgst' or 'igst'
- `place_of_supply`: State code for GST
- `invoice_status`: 'generated', 'paid', 'cancelled'
- `payment_status`: 'paid', 'unpaid', 'partial'

**Financial Fields:**
- `subtotal_amount`: Sum of all items before tax
- `discount_amount`: Total discount applied
- `taxable_amount`: Amount on which tax is calculated
- `cgst_amount`, `sgst_amount`, `igst_amount`: Tax breakup
- `total_tax_amount`: Sum of all taxes
- `round_off_amount`: Rounding adjustment
- `total_amount`: Final invoice amount

### 2. `invoice_items`
Line items for each invoice.

**Key Fields:**
- `item_id` (PK): Auto-incrementing primary key
- `invoice_id` (FK): Links to invoices table
- `product_id` (FK): Links to products table
- `batch_id` (FK): Links to batches table (for tracking)
- `quantity`: Number of units
- `unit_price`: Price per unit
- `mrp`: Maximum retail price
- `discount_percent`, `discount_amount`: Item-level discount
- `gst_percent`: GST rate for the item
- `taxable_amount`: Amount after discount
- `total_amount`: Final amount for line item

### 3. `invoice_payments`
Payment records for invoices.

**Key Fields:**
- `payment_id` (PK): Auto-incrementing primary key
- `invoice_id` (FK): Links to invoices table
- `payment_date`: When payment was made
- `amount`: Payment amount (required)
- `payment_amount`: Same as amount (legacy compatibility)
- `payment_mode`: 'cash', 'card', 'upi', 'cheque', 'bank_transfer'
- `transaction_reference`: For digital payments
- `status`: 'completed', 'pending', 'failed', 'cancelled'

## API Endpoints

### 1. POST `/api/v1/invoices/calculate-live`
Calculate invoice totals without saving.

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
  "delivery_charges": "0.00",
  "net_amount": "266.00",
  "round_off": "0.00",
  "final_amount": "266.00"
}
```

### 2. GET `/api/v1/invoices/{invoice_id}`
Get invoice details.

### 3. GET `/api/v1/invoices/{invoice_id}/print`
Generate invoice PDF.

### 4. POST `/api/v1/invoices/{invoice_id}/payments`
Record a payment against invoice.

## Business Logic

### GST Calculation

1. **Determine Transaction Type:**
   ```python
   # Get seller state from organization settings
   seller_state = organization.business_settings.get('state')
   
   # Get buyer state from customer
   buyer_state = customer.state
   
   # If either is missing, default to intrastate
   is_interstate = seller_state != buyer_state if both exist else False
   ```

2. **Apply Tax Rules:**
   - **Intrastate (same state)**: Apply CGST + SGST (split GST rate equally)
   - **Interstate (different states)**: Apply IGST (full GST rate)

3. **Tax Calculation:**
   ```python
   taxable_amount = line_total - discount
   
   if is_interstate:
       igst = taxable_amount * gst_rate / 100
   else:
       cgst = taxable_amount * (gst_rate / 2) / 100
       sgst = taxable_amount * (gst_rate / 2) / 100
   ```

### Invoice Number Generation

Format: `INV{YYYYMMDD}{SEQUENCE}`

```sql
-- Get next sequence for today
SELECT COALESCE(MAX(
    CAST(SUBSTRING(invoice_number FROM 12) AS INTEGER)
), 0) + 1 
FROM invoices 
WHERE invoice_number LIKE 'INV20250724%'
```

### Rounding Logic

```python
# Calculate round off to nearest rupee
total_with_tax = subtotal - discount + total_tax + delivery_charges
final_amount = round(total_with_tax)
round_off = final_amount - total_with_tax
```

## Integration with Order Module

When an order is created through the Enterprise Order Service:

1. Order is created first
2. Invoice is automatically generated with:
   - Same customer details
   - Same items with pricing
   - Calculated taxes
   - Initial payment if provided
3. Invoice items are created
4. Payment record created if payment_amount > 0

## Frontend Integration

### Creating Invoice (Quick Sale)
```javascript
// Frontend sends to /api/v1/enterprise-orders/quick-sale
{
  customer_id: 34,
  items: [{
    product_id: 45,
    quantity: 10,
    batch_id: 70  // Optional
  }],
  payment_mode: "cash",
  payment_amount: 266.00,
  discount_amount: 0
}
```

### Response Handling
```javascript
// Success response
{
  success: true,
  order_id: 86,
  order_number: "ORD20250724-0015-225324",
  invoice_id: 20,
  invoice_number: "INV202507240086",
  total_amount: 266.00,
  payment_status: "paid",
  invoice_status: "generated"
}
```

## Common Issues & Solutions

### 1. CGST/SGST Not Showing
**Issue**: Tax shows as IGST instead of CGST/SGST
**Solution**: Ensure customer.state matches organization's state

### 2. Invoice Creation Fails
**Issue**: "Field required" validation errors
**Cause**: Missing required fields like customer_name
**Solution**: Enterprise Order Service ensures all fields are populated

### 3. Payment Amount Mismatch
**Issue**: `null value in column 'amount'`
**Solution**: Both `amount` and `payment_amount` fields must be populated

## SQL Queries

### Get Invoice Summary
```sql
SELECT 
    i.invoice_number,
    i.invoice_date,
    i.customer_name,
    i.total_amount,
    i.payment_status,
    COUNT(ii.item_id) as item_count
FROM invoices i
LEFT JOIN invoice_items ii ON i.invoice_id = ii.invoice_id
WHERE i.org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f'
GROUP BY i.invoice_id
ORDER BY i.invoice_date DESC;
```

### Get Unpaid Invoices
```sql
SELECT 
    invoice_number,
    customer_name,
    total_amount,
    paid_amount,
    (total_amount - COALESCE(paid_amount, 0)) as balance_due,
    DATE_PART('day', CURRENT_DATE - invoice_date) as days_overdue
FROM invoices
WHERE payment_status IN ('unpaid', 'partial')
AND org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f'
ORDER BY invoice_date;
```

## Future Enhancements

1. **Email Integration**: Send invoice PDF via email
2. **Recurring Invoices**: For subscription-based customers
3. **Credit Notes**: For returns and adjustments
4. **Bulk Invoice Generation**: For multiple orders
5. **Payment Reminders**: Automated follow-ups
6. **QR Code**: For UPI payments on invoice PDF

---

Last Updated: 2025-07-24