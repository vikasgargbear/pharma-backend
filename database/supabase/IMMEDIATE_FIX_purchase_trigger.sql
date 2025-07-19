-- =============================================
-- IMMEDIATE FIX: Add purchase support to inventory movement trigger
-- =============================================
-- This just updates the function to handle purchases
-- Run this in Supabase SQL Editor
-- =============================================

-- Update only the validation function
CREATE OR REPLACE FUNCTION validate_inventory_movement()
RETURNS TRIGGER AS $$
DECLARE
    v_current_stock INTEGER;
    v_batch RECORD;
BEGIN
    -- Special handling for purchase movements (they create new stock)
    IF NEW.movement_type = 'purchase' THEN
        -- Just ensure quantity_in is positive
        IF NEW.quantity_in <= 0 THEN
            RAISE EXCEPTION 'Purchase quantity must be positive';
        END IF;
        IF NEW.quantity_out != 0 THEN
            RAISE EXCEPTION 'Purchase should not have quantity_out';
        END IF;
        
        -- Set product_id from batch if needed
        IF NEW.product_id IS NULL AND NEW.batch_id IS NOT NULL THEN
            SELECT product_id INTO NEW.product_id FROM batches WHERE batch_id = NEW.batch_id;
        END IF;
        
        -- Set movement date if not provided
        IF NEW.movement_date IS NULL THEN
            NEW.movement_date := CURRENT_TIMESTAMP;
        END IF;
        
        RETURN NEW; -- Skip the rest of validation for purchases
    END IF;
    
    -- For all other movement types, get batch details
    SELECT * INTO v_batch FROM batches WHERE batch_id = NEW.batch_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Batch ID % not found', NEW.batch_id;
    END IF;
    
    -- Validate based on movement type
    CASE NEW.movement_type
        WHEN 'sales_return' THEN
            -- Sales returns add stock back (quantity_in)
            IF NEW.quantity_in <= 0 THEN
                RAISE EXCEPTION 'Sales return quantity must be positive';
            END IF;
            IF NEW.quantity_out != 0 THEN
                RAISE EXCEPTION 'Sales return should not have quantity_out';
            END IF;
            
        WHEN 'stock_damage', 'stock_expiry' THEN
            -- Damage and expiry reduce stock (quantity_out)
            IF NEW.quantity_out <= 0 THEN
                RAISE EXCEPTION 'Stock adjustment quantity must be positive';
            END IF;
            IF NEW.quantity_in != 0 THEN
                RAISE EXCEPTION 'Stock reduction should not have quantity_in';
            END IF;
            -- Check sufficient stock
            IF v_batch.quantity_available < NEW.quantity_out THEN
                RAISE EXCEPTION 'Insufficient stock. Available: %, Requested: %', 
                                v_batch.quantity_available, NEW.quantity_out;
            END IF;
            
        WHEN 'stock_count' THEN
            -- Stock count can be either in or out
            IF NEW.quantity_in > 0 AND NEW.quantity_out > 0 THEN
                RAISE EXCEPTION 'Stock count should have either quantity_in OR quantity_out, not both';
            END IF;
            IF NEW.quantity_in = 0 AND NEW.quantity_out = 0 THEN
                RAISE EXCEPTION 'Stock count must have a quantity adjustment';
            END IF;
            -- Check sufficient stock for reductions
            IF NEW.quantity_out > 0 AND v_batch.quantity_available < NEW.quantity_out THEN
                RAISE EXCEPTION 'Insufficient stock for count adjustment. Available: %, Requested: %', 
                                v_batch.quantity_available, NEW.quantity_out;
            END IF;
            
        WHEN 'stock_adjustment' THEN
            -- General adjustments can be either way
            IF NEW.quantity_out > 0 AND v_batch.quantity_available < NEW.quantity_out THEN
                RAISE EXCEPTION 'Insufficient stock for adjustment. Available: %, Requested: %', 
                                v_batch.quantity_available, NEW.quantity_out;
            END IF;
            
        ELSE
            -- For any other movement types, just pass through
            NULL;
    END CASE;
    
    -- Set product_id from batch if not provided
    IF NEW.product_id IS NULL THEN
        NEW.product_id := v_batch.product_id;
    END IF;
    
    -- Set movement date if not provided
    IF NEW.movement_date IS NULL THEN
        NEW.movement_date := CURRENT_TIMESTAMP;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Purchase trigger fix applied! Goods receipt should now work.';
END $$;