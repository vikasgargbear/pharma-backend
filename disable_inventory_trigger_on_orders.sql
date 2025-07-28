-- The real issue: There's a trigger on order_items that deducts inventory
-- This is WRONG - only invoices should deduct inventory

-- Check what triggers exist on order_items
SELECT 
    tgname as trigger_name,
    tgtype,
    proname as function_name
FROM pg_trigger t
JOIN pg_proc p ON t.tgfoid = p.oid
WHERE tgrelid = 'order_items'::regclass;

-- Disable the inventory allocation trigger on order_items
-- This trigger should NOT exist on orders
ALTER TABLE order_items DISABLE TRIGGER ALL;

-- Or specifically disable the allocate_batch_fefo trigger
-- DROP TRIGGER IF EXISTS allocate_batch_fefo_trigger ON order_items;

-- The correct flow should be:
-- 1. Order created → NO inventory change
-- 2. Challan created → NO inventory change  
-- 3. Invoice created → Inventory deducted

-- Run this to disable the problematic trigger