-- =====================================================
-- Fix: Move inventory trigger from order_items to invoice_items
-- =====================================================
-- Issue: Inventory is being deducted when creating orders/challans
-- Solution: Inventory should ONLY be deducted when creating invoices

-- Step 1: Drop the incorrect trigger from order_items
DROP TRIGGER IF EXISTS allocate_batch_fefo_trigger ON order_items;

-- Step 2: Ensure invoice_items table has the trigger
-- First check if trigger already exists on invoice_items
DO $$
BEGIN
    -- Only create trigger if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'allocate_batch_fefo_trigger' 
        AND tgrelid = 'invoice_items'::regclass
    ) THEN
        -- Create the trigger on invoice_items (where it belongs)
        CREATE TRIGGER allocate_batch_fefo_trigger 
        AFTER INSERT ON invoice_items 
        FOR EACH ROW 
        EXECUTE FUNCTION allocate_batch_fefo();
    END IF;
END $$;

-- Step 3: Document the correct flow
COMMENT ON TABLE order_items IS 'Order line items - NO inventory impact';
COMMENT ON TABLE invoice_items IS 'Invoice line items - TRIGGERS inventory deduction';

-- The correct business flow:
-- 1. Order created (order_items) → No inventory change
-- 2. Challan created (references order_items) → No inventory change
-- 3. Invoice created (invoice_items) → Inventory deducted here

-- This ensures inventory is only deducted at the point of sale (invoice),
-- not at order placement or dispatch