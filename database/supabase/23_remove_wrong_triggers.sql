-- Remove inventory triggers from order_items table
-- These triggers should ONLY exist on invoice_items, not order_items

-- Drop the problematic triggers
DROP TRIGGER IF EXISTS trigger_allocate_batch_fefo ON order_items;
DROP TRIGGER IF EXISTS trigger_update_inventory_on_order_enhanced ON order_items;

-- Verify they're gone
SELECT 
    tgname as trigger_name
FROM pg_trigger 
WHERE tgrelid = 'order_items'::regclass
AND tgname NOT LIKE 'RI_ConstraintTrigger%';

-- Document the correct flow:
-- Orders (order_items) → No inventory impact
-- Invoices (invoice_items) → Should have the inventory triggers