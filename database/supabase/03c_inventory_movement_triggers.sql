-- =============================================
-- PHARMACEUTICAL ERP - INVENTORY MOVEMENT TRIGGERS
-- =============================================
-- Version: 1.0
-- Description: Triggers for inventory movements (sales returns, stock adjustments)
-- Deploy Order: After core schema
-- =============================================

-- =============================================
-- INVENTORY MOVEMENT VALIDATION
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

-- =============================================
-- AUTO-UPDATE BATCH QUANTITIES
-- =============================================

-- Update batch quantities after inventory movement
CREATE OR REPLACE FUNCTION update_batch_after_movement()
RETURNS TRIGGER AS $$
BEGIN
    -- Update batch quantities based on movement
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
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_batch_after_movement
    AFTER INSERT ON inventory_movements
    FOR EACH ROW
    EXECUTE FUNCTION update_batch_after_movement();

-- =============================================
-- SALES RETURN SPECIFIC TRIGGERS
-- =============================================

-- Update order status when sales return is processed
CREATE OR REPLACE FUNCTION update_order_on_sales_return()
RETURNS TRIGGER AS $$
DECLARE
    v_order_total DECIMAL;
    v_returned_total DECIMAL;
BEGIN
    -- Only process sales returns with order reference
    IF NEW.movement_type = 'sales_return' AND NEW.reference_type = 'sales_return' AND NEW.reference_id IS NOT NULL THEN
        -- Calculate total returned amount for this order
        SELECT COALESCE(SUM(im.quantity_in * COALESCE(b.selling_price, p.sale_price)), 0)
        INTO v_returned_total
        FROM inventory_movements im
        JOIN products p ON im.product_id = p.product_id
        LEFT JOIN batches b ON im.batch_id = b.batch_id
        WHERE im.movement_type = 'sales_return'
        AND im.reference_id = NEW.reference_id;
        
        -- Get order total
        SELECT final_amount INTO v_order_total
        FROM orders WHERE order_id = NEW.reference_id;
        
        -- Update order status if fully returned
        IF v_returned_total >= v_order_total THEN
            UPDATE orders
            SET order_status = 'returned'
            WHERE order_id = NEW.reference_id;
        ELSIF v_returned_total > 0 THEN
            UPDATE orders
            SET order_status = 'partially_returned'
            WHERE order_id = NEW.reference_id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_order_on_return
    AFTER INSERT ON inventory_movements
    FOR EACH ROW
    WHEN (NEW.movement_type = 'sales_return')
    EXECUTE FUNCTION update_order_on_sales_return();

-- =============================================
-- STOCK ADJUSTMENT NOTIFICATIONS
-- =============================================

-- Create notifications for critical stock adjustments
CREATE OR REPLACE FUNCTION notify_critical_stock_adjustment()
RETURNS TRIGGER AS $$
DECLARE
    v_product_name TEXT;
    v_batch_number TEXT;
    v_notification_type TEXT;
    v_message TEXT;
BEGIN
    -- Get product and batch details
    SELECT p.product_name, b.batch_number 
    INTO v_product_name, v_batch_number
    FROM products p
    JOIN batches b ON b.product_id = p.product_id
    WHERE b.batch_id = NEW.batch_id;
    
    -- Determine notification type and message
    CASE NEW.movement_type
        WHEN 'stock_damage' THEN
            v_notification_type := 'stock_damage';
            v_message := format('Stock damaged: %s %s (Batch: %s), Quantity: %s',
                              NEW.quantity_out, v_product_name, v_batch_number, NEW.quantity_out);
                              
        WHEN 'stock_expiry' THEN
            v_notification_type := 'stock_expiry';
            v_message := format('Stock expired: %s %s (Batch: %s), Quantity: %s',
                              NEW.quantity_out, v_product_name, v_batch_number, NEW.quantity_out);
                              
        WHEN 'stock_count' THEN
            IF NEW.quantity_out > NEW.quantity_in THEN
                v_notification_type := 'stock_discrepancy';
                v_message := format('Stock discrepancy found: %s (Batch: %s), Shortage: %s',
                                  v_product_name, v_batch_number, NEW.quantity_out - NEW.quantity_in);
            ELSE
                RETURN NEW; -- Don't notify for positive adjustments
            END IF;
        ELSE
            RETURN NEW; -- No notification for other types
    END CASE;
    
    -- Create notification
    INSERT INTO system_notifications (
        notification_type,
        title,
        message,
        target_type,
        target_value,
        priority,
        action_required,
        created_at
    ) VALUES (
        v_notification_type,
        'Stock Adjustment Alert',
        v_message,
        'org',
        NEW.org_id::TEXT,
        'high',
        TRUE,
        CURRENT_TIMESTAMP
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_notify_critical_adjustment
    AFTER INSERT ON inventory_movements
    FOR EACH ROW
    WHEN (NEW.movement_type IN ('stock_damage', 'stock_expiry', 'stock_count'))
    EXECUTE FUNCTION notify_critical_stock_adjustment();

-- =============================================
-- AUTO-EXPIRE BATCHES
-- =============================================

-- Function to automatically expire batches (to be called by scheduler)
CREATE OR REPLACE FUNCTION process_expired_batches()
RETURNS INTEGER AS $$
DECLARE
    v_expired_count INTEGER := 0;
    v_batch RECORD;
BEGIN
    -- Find batches that expired and still have stock
    FOR v_batch IN 
        SELECT b.*, p.product_name
        FROM batches b
        JOIN products p ON b.product_id = p.product_id
        WHERE b.expiry_date <= CURRENT_DATE
        AND b.quantity_available > 0
        AND b.batch_status != 'expired'
    LOOP
        -- Create expiry movement
        INSERT INTO inventory_movements (
            org_id,
            movement_date,
            movement_type,
            product_id,
            batch_id,
            quantity_in,
            quantity_out,
            reference_type,
            reference_number,
            notes
        ) VALUES (
            v_batch.org_id,
            CURRENT_TIMESTAMP,
            'stock_expiry',
            v_batch.product_id,
            v_batch.batch_id,
            0,
            v_batch.quantity_available,
            'auto_expiry',
            'EXP-' || v_batch.batch_number,
            'Batch auto-expired on ' || CURRENT_DATE
        );
        
        v_expired_count := v_expired_count + 1;
    END LOOP;
    
    RETURN v_expired_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- AUDIT LOGGING
-- =============================================

-- Audit critical inventory movements
CREATE OR REPLACE FUNCTION audit_inventory_movement()
RETURNS TRIGGER AS $$
BEGIN
    -- Only audit specific movement types
    IF NEW.movement_type IN ('sales_return', 'stock_damage', 'stock_expiry', 'stock_count', 'stock_adjustment') THEN
        INSERT INTO activity_log (
            org_id,
            user_id,
            activity_type,
            activity_description,
            table_name,
            record_id,
            new_values,
            created_at
        ) VALUES (
            NEW.org_id,
            NEW.performed_by,
            'inventory_' || NEW.movement_type,
            format('%s: Product %s, Batch %s, Qty In: %s, Qty Out: %s',
                   NEW.movement_type, NEW.product_id, NEW.batch_id, 
                   COALESCE(NEW.quantity_in, 0), COALESCE(NEW.quantity_out, 0)),
            'inventory_movements',
            NEW.movement_id::TEXT,
            to_jsonb(NEW),
            CURRENT_TIMESTAMP
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_audit_inventory_movement
    AFTER INSERT ON inventory_movements
    FOR EACH ROW
    EXECUTE FUNCTION audit_inventory_movement();

-- =============================================
-- HELPER FUNCTIONS
-- =============================================

-- Get stock adjustment summary for a period
CREATE OR REPLACE FUNCTION get_stock_adjustment_summary(
    p_org_id UUID,
    p_start_date DATE,
    p_end_date DATE
) RETURNS TABLE (
    adjustment_type TEXT,
    total_quantity_in INTEGER,
    total_quantity_out INTEGER,
    product_count INTEGER,
    batch_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        movement_type,
        SUM(quantity_in)::INTEGER as total_quantity_in,
        SUM(quantity_out)::INTEGER as total_quantity_out,
        COUNT(DISTINCT product_id)::INTEGER as product_count,
        COUNT(DISTINCT batch_id)::INTEGER as batch_count
    FROM inventory_movements
    WHERE org_id = p_org_id
    AND movement_date >= p_start_date
    AND movement_date <= p_end_date
    AND movement_type IN ('sales_return', 'stock_damage', 'stock_expiry', 'stock_count', 'stock_adjustment')
    GROUP BY movement_type
    ORDER BY movement_type;
END;
$$ LANGUAGE plpgsql;

-- Get sales return summary for a customer
CREATE OR REPLACE FUNCTION get_customer_return_summary(
    p_customer_id INTEGER,
    p_days INTEGER DEFAULT 365
) RETURNS TABLE (
    total_returns INTEGER,
    total_quantity INTEGER,
    total_value DECIMAL,
    unique_products INTEGER,
    last_return_date DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_returns,
        SUM(im.quantity_in)::INTEGER as total_quantity,
        SUM(im.quantity_in * COALESCE(b.selling_price, p.sale_price)) as total_value,
        COUNT(DISTINCT im.product_id)::INTEGER as unique_products,
        MAX(im.movement_date::DATE) as last_return_date
    FROM inventory_movements im
    JOIN orders o ON im.reference_id = o.order_id
    JOIN products p ON im.product_id = p.product_id
    LEFT JOIN batches b ON im.batch_id = b.batch_id
    WHERE im.movement_type = 'sales_return'
    AND im.reference_type = 'sales_return'
    AND o.customer_id = p_customer_id
    AND im.movement_date >= CURRENT_DATE - INTERVAL '1 day' * p_days;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- SUCCESS MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
INVENTORY MOVEMENT TRIGGERS DEPLOYED
=============================================
✓ Movement validation triggers
✓ Batch quantity update triggers
✓ Sales return order update triggers
✓ Stock adjustment notifications
✓ Auto-expiry processing
✓ Audit logging
✓ Helper functions

These triggers work with the existing inventory_movements table
and support sales returns and stock adjustments without 
requiring new tables.
=============================================
';
END $$;