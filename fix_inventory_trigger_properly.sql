-- First, let's identify the specific trigger
SELECT 
    tgname as trigger_name,
    tgtype,
    proname as function_name
FROM pg_trigger t
JOIN pg_proc p ON t.tgfoid = p.oid
WHERE tgrelid = 'order_items'::regclass;

-- DON'T disable all triggers! Instead, we need to modify the trigger logic

-- The trigger should check the order type/status before deducting inventory
-- Here's how the trigger SHOULD work:

-- Option 1: Modify the allocate_batch_fefo function to check order status
CREATE OR REPLACE FUNCTION allocate_batch_fefo() RETURNS TRIGGER AS $$
DECLARE
    order_rec RECORD;
BEGIN
    -- Get the order details
    SELECT order_status, order_type 
    INTO order_rec
    FROM orders 
    WHERE order_id = NEW.order_id;
    
    -- Only allocate inventory if this is for an invoice
    -- Check if order_status = 'invoiced' or similar
    IF order_rec.order_status != 'invoiced' THEN
        -- Don't allocate inventory for regular orders
        RETURN NEW;
    END IF;
    
    -- Original inventory allocation logic here...
    -- (existing trigger code)
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Option 2: Create separate tables for invoice_items vs order_items
-- This is cleaner but requires more changes

-- Option 3: Add a flag to control inventory deduction
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS deduct_inventory BOOLEAN DEFAULT FALSE;

-- Then the trigger checks this flag
-- Only invoice creation sets deduct_inventory = TRUE