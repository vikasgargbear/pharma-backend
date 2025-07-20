-- =============================================
-- FIX: Batch Creation Trigger to Handle Null Batch Numbers
-- =============================================
-- This fixes the trigger to auto-generate batch numbers when null
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

-- Also update the comment
COMMENT ON FUNCTION create_batches_from_purchase() IS 
'Enhanced: Auto-generates batch numbers when null and avoids duplicates. Format: AUTO-YYYYMMDD-PRODUCTID-RANDOM';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '
=============================================
BATCH CREATION TRIGGER FIXED
=============================================
✓ Auto-generates batch numbers when null
✓ Format: AUTO-YYYYMMDD-PRODUCTID-RANDOM
✓ Skips if batch already exists
✓ Sets default expiry date (2 years)
✓ Sets default manufacturing date (30 days ago)
=============================================';
END $$;