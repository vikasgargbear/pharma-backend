-- =============================================
-- Migration V004: Purchase System Enhancements
-- =============================================
-- Description: Consolidated fixes for purchase order system
-- Date: 2025-01-20
-- Author: AASO Pharma Team
-- =============================================

-- =============================================
-- 1. FIX INVENTORY MOVEMENT TRIGGER FOR PURCHASES
-- =============================================

-- Drop and recreate the validation function to support purchase movements
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

-- =============================================
-- 2. FIX SUPPLIER OUTSTANDING CONSTRAINT
-- =============================================

-- Add unique constraint for ON CONFLICT to work
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'supplier_outstanding_purchase_id_key'
    ) THEN
        ALTER TABLE supplier_outstanding 
        ADD CONSTRAINT supplier_outstanding_purchase_id_key UNIQUE (purchase_id);
    END IF;
END $$;

-- Update the function to handle existing entries properly
CREATE OR REPLACE FUNCTION create_supplier_outstanding_on_purchase()
RETURNS TRIGGER AS $$
BEGIN
    -- Create outstanding when purchase is received
    IF NEW.purchase_status = 'received' AND OLD.purchase_status != 'received' THEN
        -- First check if entry already exists
        IF EXISTS (SELECT 1 FROM supplier_outstanding WHERE purchase_id = NEW.purchase_id) THEN
            -- Update existing entry
            UPDATE supplier_outstanding
            SET 
                outstanding_amount = NEW.final_amount - COALESCE(NEW.paid_amount, 0),
                total_amount = NEW.final_amount,
                updated_at = CURRENT_TIMESTAMP
            WHERE purchase_id = NEW.purchase_id;
        ELSE
            -- Create new entry
            INSERT INTO supplier_outstanding (
                org_id, supplier_id, purchase_id,
                invoice_number, invoice_date,
                total_amount, outstanding_amount,
                due_date, status
            ) VALUES (
                NEW.org_id, NEW.supplier_id, NEW.purchase_id,
                NEW.supplier_invoice_number, NEW.supplier_invoice_date,
                NEW.final_amount, NEW.final_amount - COALESCE(NEW.paid_amount, 0),
                COALESCE(NEW.payment_due_date, NEW.purchase_date + INTERVAL '30 days'),
                'pending'
            );
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- 3. ENHANCE BATCH CREATION FOR AUTO-GENERATION
-- =============================================

-- Drop the trigger first if it exists
DROP TRIGGER IF EXISTS trigger_create_batches_from_purchase ON purchases;

-- Update the function to handle null batch numbers
CREATE OR REPLACE FUNCTION create_batches_from_purchase()
RETURNS TRIGGER AS $$
DECLARE
    v_item RECORD;
    v_batch_id INTEGER;
    v_batch_number TEXT;
BEGIN
    -- Only process when purchase is received
    IF NEW.purchase_status != 'received' OR OLD.purchase_status = 'received' THEN
        RETURN NEW;
    END IF;
    
    -- Create batches for each purchase item
    FOR v_item IN 
        SELECT * FROM purchase_items 
        WHERE purchase_id = NEW.purchase_id
        AND received_quantity > 0
    LOOP
        -- Generate batch number if null
        IF v_item.batch_number IS NULL OR v_item.batch_number = '' THEN
            -- Auto-generate batch number: AUTO-YYYYMMDD-PRODID-RANDOM
            v_batch_number := 'AUTO-' || 
                            TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || '-' ||
                            v_item.product_id || '-' ||
                            LPAD(FLOOR(RANDOM() * 10000)::TEXT, 4, '0');
        ELSE
            v_batch_number := v_item.batch_number;
        END IF;
        
        -- Check if batch already exists
        IF EXISTS (
            SELECT 1 FROM batches 
            WHERE org_id = NEW.org_id 
            AND product_id = v_item.product_id 
            AND batch_number = v_batch_number
        ) THEN
            -- Skip if batch already exists
            CONTINUE;
        END IF;
        
        -- Create batch
        INSERT INTO batches (
            org_id, product_id, batch_number,
            manufacturing_date, expiry_date,
            quantity_received, quantity_available,
            cost_price, mrp,
            supplier_id, purchase_id,
            purchase_invoice_number,
            created_by
        ) VALUES (
            NEW.org_id, 
            v_item.product_id, 
            v_batch_number,  -- Use generated or provided batch number
            COALESCE(v_item.manufacturing_date, CURRENT_DATE - INTERVAL '30 days'),
            COALESCE(v_item.expiry_date, CURRENT_DATE + INTERVAL '2 years'),
            v_item.received_quantity, 
            v_item.received_quantity,
            v_item.cost_price, 
            v_item.mrp,
            NEW.supplier_id, 
            NEW.purchase_id,
            NEW.supplier_invoice_number,
            NEW.created_by
        ) RETURNING batch_id INTO v_batch_id;
        
        -- Generate batch barcode if function exists
        IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'generate_batch_barcode') THEN
            PERFORM generate_batch_barcode(NEW.org_id, v_batch_id);
        END IF;
        
        -- Create inventory movement
        INSERT INTO inventory_movements (
            org_id, movement_date, movement_type,
            product_id, batch_id,
            quantity_in, quantity_out,
            reference_type, reference_id, reference_number,
            notes
        ) VALUES (
            NEW.org_id, CURRENT_TIMESTAMP, 'purchase',
            v_item.product_id, v_batch_id,
            v_item.received_quantity, 0,
            'purchase', NEW.purchase_id, NEW.purchase_number,
            'Auto-created from purchase receipt'
        );
    END LOOP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Recreate the trigger
CREATE TRIGGER trigger_create_batches_from_purchase
    AFTER UPDATE OF purchase_status ON purchases
    FOR EACH ROW
    EXECUTE FUNCTION create_batches_from_purchase();

-- =============================================
-- 4. UPDATE BATCH MOVEMENT FUNCTION
-- =============================================

-- Update the batch update function to handle purchases properly
CREATE OR REPLACE FUNCTION update_batch_after_movement()
RETURNS TRIGGER AS $$
BEGIN
    -- For purchases, the batch is already created with initial quantities
    IF NEW.movement_type = 'purchase' THEN
        -- Purchase movements typically happen when batch is created
        -- Update received quantity if needed
        UPDATE batches 
        SET 
            quantity_received = COALESCE(quantity_received, 0) + NEW.quantity_in,
            updated_at = CURRENT_TIMESTAMP
        WHERE batch_id = NEW.batch_id;
    ELSE
        -- For all other movements, update as normal
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
-- 5. ADD COMMENTS FOR DOCUMENTATION
-- =============================================

COMMENT ON FUNCTION validate_inventory_movement() IS 
'Validates inventory movements based on type. Handles purchase movements specially since they create new stock.';

COMMENT ON FUNCTION create_batches_from_purchase() IS 
'Creates batches automatically when purchase is received. Auto-generates batch numbers in format AUTO-YYYYMMDD-PRODUCTID-RANDOM when not provided.';

COMMENT ON FUNCTION create_supplier_outstanding_on_purchase() IS 
'Creates or updates supplier outstanding records when purchase is received.';

COMMENT ON FUNCTION update_batch_after_movement() IS 
'Updates batch quantities after inventory movement. Handles different movement types appropriately.';

-- =============================================
-- MIGRATION COMPLETE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
PURCHASE SYSTEM ENHANCEMENTS APPLIED
=============================================
✓ Inventory movement trigger supports purchases
✓ Supplier outstanding constraint added
✓ Batch auto-generation for null values
✓ Batch movement updates enhanced
✓ All functions documented

Features:
- Auto batch format: AUTO-YYYYMMDD-PRODUCTID-XXXX
- Default expiry: 2 years from today
- Default mfg date: 30 days ago
- Handles partial PDF data gracefully
=============================================';
END $$;