# Sales Return Workflow Documentation

## Overview
This document outlines what happens when a sales return is processed in the system.

## Workflow Steps

### 1. Return Creation
When a sales return is created through the API (`POST /api/v1/sale-returns`), the following occurs:

#### A. Data Validation
- Customer existence is verified
- Original invoice is validated
- Return items are checked for validity
- GST status of customer is checked

#### B. Return Record Creation
- A unique return number is generated (format: `SR-YYYYMMDD-HHMMSS`)
- Main return record is inserted into `sale_returns` table
- Return items are inserted into `sale_return_items` table

#### C. Credit Note Generation
- **For GST Customers**: A GST credit note number is generated (format: `CN-YYYYMMDD-HHMMSS`)
- **For Non-GST Customers**: No credit note number is generated (just a return note)

### 2. Inventory Updates
For each returned item:

```sql
-- If batch_id is provided
UPDATE inventory 
SET current_stock = current_stock + :quantity
WHERE batch_id = :batch_id

-- If batch_id is not provided
INSERT INTO inventory (inventory_id, org_id, product_id, batch_number, current_stock)
VALUES (:inv_id, :org_id, :product_id, :batch, :stock)
ON CONFLICT (org_id, product_id, batch_number) 
DO UPDATE SET current_stock = inventory.current_stock + :stock
```

**Impact**: Stock levels increase for returned products

### 3. Customer Ledger Updates
If payment_mode is 'credit':

```sql
INSERT INTO party_ledger (
    ledger_id, org_id, party_id, transaction_date,
    transaction_type, reference_type, reference_id,
    debit_amount, credit_amount, description
) VALUES (
    :ledger_id, :org_id, :party_id, :date,
    'credit', 'sale_return', :return_id,
    0, :amount, :description
)
```

**Impact**: Customer gets a credit balance that can be used for future purchases

### 4. GST Implications

#### For GST-Registered Customers:
- GST credit note is generated
- Customer can claim Input Tax Credit (ITC) reversal
- GST liability is reduced for the seller

#### For Non-GST Customers:
- Simple return note is generated
- No GST reversal (customer cannot claim ITC)
- Full amount including taxes is returned

### 5. Financial Impact

#### Accounting Entries:
```
Debit: Sales Return Account     [Total Amount]
    Credit: Customer Account     [Total Amount]

If GST Customer:
Debit: Output GST Account        [Tax Amount]
    Credit: Sales Return Account [Tax Amount]
```

### 6. Stock Valuation
- Returned items are added back to inventory at their original cost
- FIFO/LIFO/Weighted Average calculations are updated
- Stock valuation reports reflect the increased inventory

### 7. Reports Affected
- **Sales Reports**: Return amounts are deducted from gross sales
- **GST Reports**: Credit notes appear in GSTR-1 (for GST customers)
- **Inventory Reports**: Stock levels and valuations are updated
- **Customer Statements**: Credit balance is shown
- **P&L Statement**: Sales returns reduce revenue

## Return Cancellation Workflow

If a return is cancelled (`DELETE /api/v1/sale-returns/{return_id}`):

1. **Inventory Reversal**: Stock quantities are decreased back
2. **Ledger Reversal**: Credit entries are removed
3. **Status Update**: Return status changed to 'cancelled'
4. **Credit Note**: Marked as cancelled (cannot be reused)

## Business Rules

1. **Time Limit**: Returns typically allowed within 30 days of sale
2. **Condition**: Products must be in saleable condition
3. **Batch Tracking**: Same batch should be returned if batch tracking is enabled
4. **Partial Returns**: System supports partial quantity returns
5. **Multiple Returns**: Multiple returns can be created for same invoice

## Integration Points

1. **Inventory Management**: Real-time stock updates
2. **Accounting**: Automated ledger entries
3. **GST Compliance**: Credit note generation and reporting
4. **Customer Portal**: Return status visibility
5. **Analytics**: Return trends and analysis

## Error Handling

Common errors and their handling:
- **Insufficient Original Quantity**: Cannot return more than sold
- **Expired Products**: Special handling for expired returns
- **Duplicate Returns**: Prevented by tracking returned quantities
- **Missing Batch**: System finds or creates appropriate batch