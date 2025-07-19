# Inventory Movements API Documentation

## Overview

The AASO Pharma ERP uses a unified `inventory_movements` table to track all stock changes including:
- Sales and purchases
- Sales returns
- Stock adjustments (damage, expiry, physical count)
- Transfers between locations

This approach provides a complete audit trail and simplifies inventory tracking.

## Movement Types

### Core Movement Types
- `purchase` - Stock received from suppliers
- `sales` - Stock sold to customers
- `sales_return` - Stock returned by customers
- `purchase_return` - Stock returned to suppliers

### Adjustment Types
- `stock_damage` - Damaged stock write-off
- `stock_expiry` - Expired stock write-off
- `stock_count` - Physical count adjustments
- `stock_adjustment` - General adjustments

## API Endpoints

### Sales Returns

#### GET /api/v1/sales-returns/
Get list of sales returns

Query Parameters:
- `customer_id` - Filter by customer
- `product_id` - Filter by product
- `start_date` - Filter from date
- `end_date` - Filter to date
- `skip` - Pagination offset
- `limit` - Page size

Response includes return details with customer and product information.

#### POST /api/v1/sales-returns/
Create a sales return

Request Body:
```json
{
  "order_id": 123,
  "product_id": 456,
  "batch_id": 789,
  "quantity": 5,
  "reason": "Damaged packaging",
  "return_date": "2024-01-15",
  "performed_by": 1
}
```

This creates an inventory movement with:
- `movement_type`: "sales_return"
- `quantity_in`: The returned quantity (adds stock back)
- `reference_type`: "sales_return"
- `reference_id`: The original order_id

### Stock Adjustments

#### GET /api/v1/stock-adjustments/
Get list of stock adjustments

Query Parameters:
- `product_id` - Filter by product
- `batch_id` - Filter by batch
- `adjustment_type` - Filter by type: damage, expiry, count, other
- `start_date` - Filter from date
- `end_date` - Filter to date

#### POST /api/v1/stock-adjustments/
Create a stock adjustment

Request Body:
```json
{
  "batch_id": 789,
  "adjustment_type": "damage",
  "quantity_adjusted": -10,
  "reason": "Water damage in storage",
  "adjusted_by": 1
}
```

Movement type mapping:
- `damage` → `stock_damage`
- `expiry` → `stock_expiry`
- `count` → `stock_count`
- `other` → `stock_adjustment`

For negative adjustments (stock reduction):
- `quantity_out` is set to the absolute value
- `quantity_in` is 0

For positive adjustments (stock addition):
- `quantity_in` is set to the value
- `quantity_out` is 0

#### POST /api/v1/stock-adjustments/physical-count
Process physical inventory count

Request Body:
```json
{
  "count_date": "2024-01-15",
  "count_reference": "COUNT-JAN-2024",
  "counted_by": 1,
  "count_items": [
    {
      "batch_id": 789,
      "counted_quantity": 95
    },
    {
      "batch_id": 790,
      "counted_quantity": 48
    }
  ]
}
```

This compares counted quantities with system quantities and creates adjustments for differences.

#### POST /api/v1/stock-adjustments/expire-batches
Automatically expire batches past their expiry date

No request body needed. This finds all expired batches with available stock and creates `stock_expiry` movements.

### Tax Entries

#### GET /api/v1/tax-entries/
Get tax entries for GST reporting

Query Parameters:
- `entry_type` - sales or purchase
- `start_date` - Period start
- `end_date` - Period end
- `party_id` - Filter by customer/supplier

#### GET /api/v1/tax-entries/summary
Get tax summary for filing

Query Parameters:
- `month` - Month number (1-12)
- `year` - Year (e.g., 2024)

Returns:
- Total output tax (from sales)
- Total input tax (from purchases)
- Net tax payable
- HSN-wise breakup

#### GET /api/v1/tax-entries/gstr1
Get GSTR-1 data (sales tax return)

#### GET /api/v1/tax-entries/gstr2
Get GSTR-2 data (purchase tax return)

## Database Schema

### inventory_movements table
```sql
- movement_id (PK)
- org_id
- movement_date
- movement_type
- product_id
- batch_id
- quantity_in (stock additions)
- quantity_out (stock reductions)
- reference_type
- reference_id
- reference_number
- notes
- performed_by
```

### Key Relationships
- Links to `products` via product_id
- Links to `batches` via batch_id
- Links to `orders` via reference_id (for sales/returns)
- Links to `users` via performed_by

## Database Triggers

The following triggers are implemented in `03c_inventory_movement_triggers.sql`:

1. **validate_inventory_movement** - Validates quantities based on movement type
2. **update_batch_after_movement** - Updates batch quantities automatically
3. **update_order_on_sales_return** - Updates order status for returns
4. **notify_critical_stock_adjustment** - Creates notifications for damage/expiry
5. **audit_inventory_movement** - Logs all adjustments for audit trail

## Best Practices

1. **Always specify batch_id** when possible for accurate tracking
2. **Use appropriate movement_type** for clear reporting
3. **Include descriptive notes** for adjustments
4. **Set performed_by** to track who made changes
5. **Use reference fields** to link to source documents

## Example Workflows

### Processing a Sales Return
1. Customer returns 5 units of Product X from Order #123
2. Call POST /api/v1/sales-returns/ with order and product details
3. System creates inventory_movement with type 'sales_return'
4. Batch quantity is automatically increased by 5
5. Order status is updated if fully returned

### Recording Damaged Stock
1. Staff discovers 10 damaged units in Batch #789
2. Call POST /api/v1/stock-adjustments/ with type 'damage'
3. System creates inventory_movement with type 'stock_damage'
4. Batch quantity is reduced by 10
5. Notification is created for management

### Physical Stock Count
1. Monthly count shows 95 units but system shows 100
2. Call POST /api/v1/stock-adjustments/physical-count
3. System creates adjustment for -5 units
4. Audit log records the discrepancy