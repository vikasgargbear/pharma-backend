-- =============================================
-- UPDATE INVENTORY MOVEMENT TRIGGERS
-- =============================================
-- This script updates existing triggers to support purchase movements
-- =============================================

-- Drop existing triggers first
DROP TRIGGER IF EXISTS trigger_validate_inventory_movement ON inventory_movements;
DROP TRIGGER IF EXISTS trigger_update_batch_after_movement ON inventory_movements;

-- Drop existing functions
DROP FUNCTION IF EXISTS validate_inventory_movement();
DROP FUNCTION IF EXISTS update_batch_after_movement();

-- =============================================
-- RECREATE WITH PURCHASE SUPPORT
-- =============================================

-- Validate inventory movements based on type
CREATE OR REPLACE FUNCTION validate_inventory_movement()
RETURNS TRIGGER AS $$
DECLARE
    v_current_stock INTEGER;
    v_batch RECORD;
BEGIN
    -- Get batch details
    SELECT * INTO v_batch FROM batches WHERE batch_id = NEW.batch_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Batch ID % not found', NEW.batch_id;
    END IF;
    
    -- Validate based on movement type
    CASE NEW.movement_type
        WHEN 'purchase' THEN
            -- Purchases add stock (quantity_in)
            IF NEW.quantity_in <= 0 THEN
                RAISE EXCEPTION 'Purchase quantity must be positive';
            END IF;
            IF NEW.quantity_out != 0 THEN
                RAISE EXCEPTION 'Purchase should not have quantity_out';
            END IF;
            
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
            -- For other movement types (sales, etc.), just pass through
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

CREATE TRIGGER trigger_validate_inventory_movement
    BEFORE INSERT ON inventory_movements
    FOR EACH ROW
    EXECUTE FUNCTION validate_inventory_movement();

-- Update batch quantities after inventory movement
CREATE OR REPLACE FUNCTION update_batch_after_movement()
RETURNS TRIGGER AS $$
BEGIN
    -- Update batch quantities based on movement
    UPDATE batches 
    SET 
        quantity_available = quantity_available + NEW.quantity_in - NEW.quantity_out,
        quantity_received = CASE
            WHEN NEW.movement_type = 'purchase' THEN COALESCE(quantity_received, 0) + NEW.quantity_in
            ELSE quantity_received
        END,
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
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_batch_after_movement
    AFTER INSERT ON inventory_movements
    FOR EACH ROW
    EXECUTE FUNCTION update_batch_after_movement();

-- =============================================
-- SUCCESS MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
INVENTORY MOVEMENT TRIGGERS UPDATED
=============================================
✓ Added support for purchase movements
✓ Fixed CASE statement with ELSE clause
✓ Batch quantities will update on purchase receipt
✓ Ready for goods receipt functionality
=============================================
';
END $$;