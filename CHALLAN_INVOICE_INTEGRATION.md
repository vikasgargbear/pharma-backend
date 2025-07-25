# Challan to Invoice Integration Guide

## Overview
This document explains how the challan system connects with invoices and other components.

## Data Flow Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Orders    │────>│  Challans   │────>│  Delivery   │────>│  Invoices   │
│             │     │             │     │             │     │             │
│ (Created)   │     │ (Dispatch)  │     │ (Complete)  │     │ (Billing)   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                    │                    │                    │
      ├────────────────────┴────────────────────┴────────────────────┤
      │                         Linked by IDs                         │
      └───────────────────────────────────────────────────────────────┘
```

## Table Relationships

### 1. Order → Challan
- **One Order** can have **Multiple Challans** (partial deliveries)
- Linked via: `challans.order_id` → `orders.order_id`

### 2. Challan → Invoice
- **Multiple Challans** can be combined into **One Invoice**
- Linked via: `challans.invoice_id` → `invoices.invoice_id`
- Only `delivered` challans can be invoiced

### 3. Order → Invoice (Traditional)
- **One Order** typically has **One Invoice** (direct billing)
- Linked via: `invoices.order_id` → `orders.order_id`

## Integration Endpoints

### 1. Create Challan from Order
```http
POST /api/v1/enterprise-delivery-challan/
```
- Creates delivery challan for an order
- Tracks items to be delivered
- Updates order delivery status to 'shipped'

### 2. Get Eligible Challans for Invoicing
```http
GET /api/v1/challan-to-invoice/eligible-challans?customer_id=35
```
- Lists all delivered challans not yet invoiced
- Filters by customer, date range
- Groups by customer for bulk invoicing

### 3. Preview Invoice from Challans
```http
GET /api/v1/challan-to-invoice/preview?challan_ids=1,2,3
```
- Shows what invoice would look like
- Calculates totals from challan items
- Validates all challans belong to same customer

### 4. Create Invoice from Challans
```http
POST /api/v1/challan-to-invoice/
```
```json
{
  "challan_ids": [1, 2, 3],
  "invoice_date": "2025-07-24",
  "payment_mode": "credit",
  "payment_amount": 0,
  "discount_amount": 100,
  "notes": "Bulk delivery invoice"
}
```

## Frontend Integration

### 1. In Invoice Creation Screen
Add option to:
- Import from Order (existing)
- Import from Challan (new)

```javascript
// Get eligible challans
const response = await api.get('/api/v1/challan-to-invoice/eligible-challans', {
  params: { customer_id: selectedCustomer.id }
});

// Show challan selection dialog
const selectedChallans = await showChallanSelector(response.data.eligible_challans);

// Create invoice
const invoice = await api.post('/api/v1/challan-to-invoice/', {
  challan_ids: selectedChallans.map(c => c.challan_id),
  payment_mode: 'credit'
});
```

### 2. In Challan List Screen
Add action to create invoice from selected delivered challans:

```javascript
// Check if all selected challans are delivered and from same customer
const canCreateInvoice = selectedChallans.every(c => 
  c.status === 'delivered' && 
  c.customer_id === selectedChallans[0].customer_id &&
  !c.invoice_id
);

if (canCreateInvoice) {
  // Show "Create Invoice" button
}
```

## Database Schema Additions

### challans table
```sql
invoice_id INTEGER REFERENCES invoices(invoice_id)  -- Links to invoice
invoiced_at TIMESTAMP                               -- When invoiced
```

### invoices table
Already has `order_id` for traditional flow, but invoice can be created from challans without direct order link.

## Business Rules

1. **Challan Status**: Only `delivered` challans can be invoiced
2. **Customer Validation**: All challans must belong to same customer
3. **Duplicate Prevention**: Challans already invoiced (`invoice_id NOT NULL`) are excluded
4. **Item Aggregation**: Items from multiple challans are combined in invoice
5. **GST Calculation**: Based on customer and organization states
6. **Payment**: Invoice can be created with immediate payment or on credit

## Typical Workflows

### Workflow 1: Single Order → Single Challan → Single Invoice
1. Create order for customer
2. Create challan for full order
3. Dispatch and deliver challan
4. Create invoice from delivered challan

### Workflow 2: Single Order → Multiple Challans → Single Invoice
1. Create large order
2. Create multiple challans for partial deliveries
3. Dispatch and deliver each challan
4. After all deliveries, create single invoice from all challans

### Workflow 3: Multiple Orders → Multiple Challans → Single Invoice
1. Customer places multiple orders over time
2. Each order gets its challan
3. Deliver all challans
4. Create consolidated monthly invoice from all delivered challans

## Benefits

1. **Flexibility**: Invoice when goods are delivered, not when ordered
2. **Accuracy**: Invoice only what was actually delivered
3. **Consolidation**: Combine multiple deliveries into single invoice
4. **Compliance**: Proper documentation trail from order to delivery to invoice
5. **Cash Flow**: Better payment tracking as invoices match deliveries

## API Response Examples

### Eligible Challans Response
```json
{
  "eligible_challans": [
    {
      "challan_id": 1,
      "challan_number": "DC202507240001",
      "challan_date": "2025-07-24",
      "order_id": 86,
      "customer_id": 35,
      "customer_name": "ABC Pharmacy",
      "delivery_time": "2025-07-24T14:30:00",
      "total_packages": 3,
      "order_number": "ORD202507240086",
      "total_amount": 2460.00,
      "item_count": 5
    }
  ],
  "total_count": 1
}
```

### Invoice Creation Response
```json
{
  "invoice_id": 101,
  "invoice_number": "INV202507240101",
  "order_ids": [86, 87, 88],
  "total_amount": 7380.00,
  "message": "Invoice INV202507240101 created successfully from 3 challan(s)"
}
```

## Error Handling

1. **No Delivered Challans**: Returns 404 if no eligible challans found
2. **Different Customers**: Returns 400 if challans belong to different customers
3. **Already Invoiced**: Challans with `invoice_id` are automatically excluded
4. **Invalid Status**: Only `delivered` status challans are processed

## Migration Path

For existing systems:
1. Run migration to add `invoice_id` and `invoiced_at` to challans table
2. Existing invoices remain linked to orders directly
3. New invoices can be created from either orders or challans
4. Frontend can show both options based on business preference