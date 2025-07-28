# Fix for inventory_movements table - it doesn't have updated_at column

# In api/services/order_service.py, find and fix these inserts:

# REPLACE THIS (around line 205-225):
"""
INSERT INTO inventory_movements (
    org_id, product_id, batch_id, movement_type, movement_date,
    quantity_out, reference_type, reference_id,
    created_at, updated_at
) VALUES (
    :org_id, :product_id, :batch_id, 'sale', CURRENT_DATE,
    :quantity_out, 'order', :order_id,
    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
)
"""

# WITH THIS:
"""
INSERT INTO inventory_movements (
    org_id, product_id, batch_id, movement_type, movement_date,
    quantity_out, reference_type, reference_id,
    created_at
) VALUES (
    :org_id, :product_id, :batch_id, 'sale', CURRENT_DATE,
    :quantity_out, 'order', :order_id,
    CURRENT_TIMESTAMP
)
"""

# BUT BETTER YET - REMOVE THE ENTIRE INVENTORY MOVEMENT INSERT!
# Orders should NOT deduct inventory at all!

# Also in enterprise_order_service.py, check any inventory_movements inserts
# and remove updated_at if present