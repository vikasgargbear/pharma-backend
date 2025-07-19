-- =============================================
-- QUICK FIX: Add purchase support to inventory movement trigger
-- =============================================
-- Run this to fix the goods receipt functionality
-- =============================================

-- Just update the existing function without dropping
CREATE OR REPLACE FUNCTION validate_inventory_movement()
RETURNS TRIGGER AS $$
DECLARE
    v_current_stock INTEGER;
    v_batch RECORD;
BEGIN
    -- Skip validation for purchase movements (they create new stock)
    IF NEW.movement_type = 'purchase' THEN
        -- Just ensure quantity_in is positive
        IF NEW.quantity_in <= 0 THEN
            RAISE EXCEPTION 'Purchase quantity must be positive';
        END IF;
        
        -- Set product_id from batch if needed
        IF NEW.product_id IS NULL THEN
            SELECT product_id INTO NEW.product_id FROM batches WHERE batch_id = NEW.batch_id;
        END IF;
        
        -- Set movement date if not provided
        IF NEW.movement_date IS NULL THEN
            NEW.movement_date := CURRENT_TIMESTAMP;
        END IF;
        
        RETURN NEW;
    END IF;
    
    -- For other movement types, get batch details
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
            -- For other movement types, just pass through
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

-- Also update the batch update function to handle purchases
CREATE OR REPLACE FUNCTION update_batch_after_movement()
RETURNS TRIGGER AS $$
BEGIN
    -- For purchases, the batch is already created with initial quantities
    -- We just need to ensure it stays in sync
    IF NEW.movement_type = 'purchase' THEN
        -- Purchase movements typically happen when batch is created
        -- So we might not need to update quantity_available
        -- But we should track it was received
        UPDATE batches 
        SET 
            quantity_received = COALESCE(quantity_received, 0) + NEW.quantity_in,
            updated_at = CURRENT_TIMESTAMP
        WHERE batch_id = NEW.batch_id;
    ELSE
        -- For all other movements, update as before
        UPDATE batches 
        SET 
            quantity_available = quantity_available + NEW.quantity_in - NEW.quantity_out,
            quantity_sold = CASE 
                WHEN NEW.movement_type = 'sales' THEN quantity_sold + NEW.quantity_out
                WHEN NEW.movement_type = 'sales_return' THEN GREATEST(0, quantity_sold - NEW.quantity_in)
                ELSE quantity_sold
            END,
            quantity_damaged = CASE 
                WHEN NEW.movement_type = 'stock_damage' THEN quantity_damaged + NEW.quantity_out
                ELSE quantity_damaged
            END,
            quantity_returned = CASE 
                WHEN NEW.movement_type = 'sales_return' THEN quantity_returned + NEW.quantity_in
                ELSE quantity_returned
            END,
            updated_at = CURRENT_TIMESTAMP
        WHERE batch_id = NEW.batch_id;
        
        -- Update batch status if quantity reaches zero
        UPDATE batches
        SET batch_status = 'out_of_stock'
        WHERE batch_id = NEW.batch_id
        AND quantity_available = 0;
        
        -- Mark batch as expired if movement type is stock_expiry
        IF NEW.movement_type = 'stock_expiry' THEN
            UPDATE batches
            SET batch_status = 'expired'
            WHERE batch_id = NEW.batch_id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- SUCCESS MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
PURCHASE TRIGGER FIX APPLIED
=============================================
✓ Purchase movements now supported
✓ Goods receipt should work properly
✓ No need to drop existing triggers
=============================================
';
END $$;