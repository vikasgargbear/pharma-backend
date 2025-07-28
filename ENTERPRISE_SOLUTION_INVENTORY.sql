-- ENTERPRISE SOLUTION FOR INVENTORY MANAGEMENT
-- ===========================================

-- The Problem:
-- There's a trigger on order_items that deducts inventory
-- This is WRONG - only invoices should deduct inventory

-- Enterprise Solution:
-- 1. Find and DROP the trigger on order_items
DROP TRIGGER IF EXISTS allocate_batch_fefo_trigger ON order_items;

-- 2. Ensure invoice_items table exists and has the trigger
-- Invoice items should be the ONLY place inventory is deducted

-- 3. The proper flow:
-- Order (order_items) → No inventory change
-- Challan (references order_items) → No inventory change  
-- Invoice (creates invoice_items) → Inventory deducted HERE

-- Check if invoice_items has the inventory trigger
SELECT 
    tgname as trigger_name,
    tgtype,
    proname as function_name
FROM pg_trigger t
JOIN pg_proc p ON t.tgfoid = p.oid
WHERE tgrelid = 'invoice_items'::regclass;

-- If invoice_items doesn't have the trigger, add it there
-- CREATE TRIGGER allocate_batch_fefo_trigger 
-- AFTER INSERT ON invoice_items 
-- FOR EACH ROW EXECUTE FUNCTION allocate_batch_fefo();