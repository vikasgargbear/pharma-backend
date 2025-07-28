-- Disable inventory deduction trigger on order_items
-- Inventory should only be deducted when creating invoices, not orders or challans

-- First, let's see what triggers exist
SELECT 
    trigger_name,
    event_object_table,
    action_statement
FROM information_schema.triggers 
WHERE event_object_table = 'order_items';

-- Disable the allocate_batch_fefo trigger if it exists
-- This trigger is incorrectly deducting inventory on order creation
ALTER TABLE order_items DISABLE TRIGGER IF EXISTS allocate_batch_fefo_trigger;

-- If you need to drop it completely (be careful with this):
-- DROP TRIGGER IF EXISTS allocate_batch_fefo_trigger ON order_items;

-- Note: Inventory deduction should only happen in:
-- 1. invoice_items table (when invoice is created)
-- 2. Manual inventory adjustments
-- 3. Stock returns

-- Orders and Challans should NEVER deduct inventory