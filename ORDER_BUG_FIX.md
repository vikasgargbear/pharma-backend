# Order Creation Bug Fix

## Issue
Order creation was failing with the error:
```
null value in column "selling_price" of relation "order_items" violates not-null constraint
```

## Root Cause
The `order_items` table in the database has a `selling_price` column that is marked as `NOT NULL`, but the INSERT statement in `/api/routers/v1/orders.py` was not including this field.

## Fix Applied
Updated the order creation endpoint to include `selling_price` in the INSERT statement:

```python
# Add selling_price (same as unit_price for now)
item_data["selling_price"] = item_data.get("selling_price", item_data["unit_price"])

db.execute(text("""
    INSERT INTO order_items (
        order_id, product_id, batch_id, quantity,
        unit_price, selling_price, discount_percent, discount_amount,
        tax_percent, tax_amount, line_total
    ) VALUES (
        :order_id, :product_id, :batch_id, :quantity,
        :unit_price, :selling_price, :discount_percent, :discount_amount,
        :tax_percent, :tax_amount, :line_total
    )
"""), item_data)
```

## File Changed
- `/api/routers/v1/orders.py` - Line 123: Added selling_price assignment
- `/api/routers/v1/orders.py` - Line 128: Added selling_price to INSERT columns
- `/api/routers/v1/orders.py` - Line 132: Added :selling_price to VALUES

## Testing Required
1. Create a new order through the API
2. Verify order items are created with selling_price
3. Check that existing functionality still works

## Deployment Steps
1. Commit the changes to git
2. Push to the repository
3. Deploy to Railway (will auto-deploy if connected to GitHub)
4. Test the fix in production

## Note
The `selling_price` is currently set to the same value as `unit_price`. In a real scenario, you might want to:
- Calculate selling_price based on MRP and discounts
- Allow it to be passed in the API request
- Add it to the OrderItemCreate schema for better control