# Fix: Remove inventory deduction from order creation
# Only invoices should deduct inventory, not orders or challans

# In api/services/order_service.py, you need to REMOVE or comment out:

# Around line 205-225, REMOVE this entire block:
"""
# Record inventory movement
db.execute(text('''
    INSERT INTO inventory_movements (
        org_id, product_id, batch_id, movement_type, movement_date,
        quantity_out, reference_type, reference_id,
        created_at, updated_at
    ) VALUES (
        :org_id, :product_id, :batch_id, 'sale', CURRENT_DATE,
        :quantity_out, 'order', :order_id,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    )
'''), {
    "org_id": org_id,
    "product_id": item['product_id'],
    "batch_id": item['batch_id'],
    "quantity_out": item['quantity'],
    "order_id": order_id
})
"""

# And around line 260-280, REMOVE this block too:
"""
# Record movement
db.execute(text('''
    INSERT INTO inventory_movements (
        org_id, product_id, batch_id, movement_type, movement_date,
        quantity_out, reference_type, reference_id,
        created_at, updated_at
    ) VALUES (
        :org_id, :product_id, :batch_id, 'sale', CURRENT_DATE,
        :quantity_out, 'order', :order_id,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    )
'''), {
    "org_id": org_id,
    "product_id": product_id,
    "batch_id": batch.batch_id,
    "quantity_out": remaining_quantity,
    "order_id": order_id
})
"""

# The issue is also that inventory_movements table doesn't have updated_at column
# But we shouldn't be inserting into it anyway from orders!

# IMPORTANT: Inventory should only be deducted in:
# 1. EnterpriseOrderService when creating invoices
# 2. When converting challans to invoices
# 3. Direct invoice creation

# NOT in:
# - Order creation
# - Challan creation