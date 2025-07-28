-- URGENT: Drop the trigger that's blocking order creation
-- This trigger should NOT exist on order_items

-- First, see what triggers are on order_items
SELECT 
    tgname as trigger_name,
    tgtype,
    proname as function_name
FROM pg_trigger t
JOIN pg_proc p ON t.tgfoid = p.oid
WHERE tgrelid = 'order_items'::regclass;

-- DROP THE TRIGGER
DROP TRIGGER IF EXISTS allocate_batch_fefo_trigger ON order_items CASCADE;

-- Verify it's gone
SELECT 
    tgname as trigger_name
FROM pg_trigger 
WHERE tgrelid = 'order_items'::regclass;

-- The allocate_batch_fefo function should ONLY be triggered on invoice_items
-- NOT on order_items