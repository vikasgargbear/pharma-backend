-- =============================================
-- CRITICAL INVENTORY TRIGGERS
-- =============================================
-- Priority: HIGHEST - Inventory accuracy is crucial
-- Deploy Order: Second - After financial triggers
-- =============================================

-- =============================================
-- 1. MULTI-LOCATION STOCK SYNC TRIGGER
-- =============================================
-- Maintains accurate stock across multiple locations
CREATE OR REPLACE FUNCTION sync_multi_location_stock()
RETURNS TRIGGER AS $$
DECLARE
    v_total_stock NUMERIC;
    v_location_count INTEGER;
    v_product_name TEXT;
BEGIN
    -- Handle inventory movements
    IF TG_TABLE_NAME = 'inventory_movements' THEN
        -- Update location-wise stock
        IF NEW.movement_type IN ('purchase', 'transfer_in', 'return_in', 'adjustment_increase') THEN
            -- Increase stock at location
            INSERT INTO inventory.location_wise_stock (
                product_id,
                batch_id,
                location_id,
                quantity_available,
                quantity_reserved,
                last_updated
            ) VALUES (
                NEW.product_id,
                NEW.batch_id,
                NEW.location_id,
                NEW.quantity,
                0,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT (product_id, batch_id, location_id) 
            DO UPDATE SET
                quantity_available = location_wise_stock.quantity_available + NEW.quantity,
                last_updated = CURRENT_TIMESTAMP;
                
        ELSIF NEW.movement_type IN ('sale', 'transfer_out', 'return_out', 'adjustment_decrease', 'expiry', 'damage') THEN
            -- Decrease stock at location
            UPDATE inventory.location_wise_stock
            SET 
                quantity_available = quantity_available - NEW.quantity,
                last_updated = CURRENT_TIMESTAMP
            WHERE product_id = NEW.product_id
            AND batch_id = NEW.batch_id
            AND location_id = NEW.location_id;
            
            -- Check for negative stock
            IF EXISTS (
                SELECT 1 
                FROM inventory.location_wise_stock
                WHERE product_id = NEW.product_id
                AND batch_id = NEW.batch_id
                AND location_id = NEW.location_id
                AND quantity_available < 0
            ) THEN
                SELECT product_name INTO v_product_name
                FROM inventory.products
                WHERE product_id = NEW.product_id;
                
                RAISE EXCEPTION 'Insufficient stock for product % at location. Movement would result in negative stock.', 
                    v_product_name;
            END IF;
        END IF;
        
        -- Update batch total
        SELECT 
            COALESCE(SUM(quantity_available), 0),
            COUNT(DISTINCT location_id)
        INTO v_total_stock, v_location_count
        FROM inventory.location_wise_stock
        WHERE product_id = NEW.product_id
        AND batch_id = NEW.batch_id;
        
        UPDATE inventory.batches
        SET 
            quantity_available = v_total_stock,
            location_count = v_location_count,
            primary_location_id = CASE 
                WHEN v_location_count = 1 THEN NEW.location_id
                ELSE primary_location_id
            END,
            updated_at = CURRENT_TIMESTAMP
        WHERE batch_id = NEW.batch_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_sync_multi_location_stock
    AFTER INSERT ON inventory.inventory_movements
    FOR EACH ROW
    EXECUTE FUNCTION sync_multi_location_stock();

-- =============================================
-- 2. PACK HIERARCHY CALCULATION TRIGGER
-- =============================================
-- Automatically calculates quantities across pack levels
CREATE OR REPLACE FUNCTION calculate_pack_hierarchy()
RETURNS TRIGGER AS $$
DECLARE
    v_base_quantity NUMERIC;
    v_pack_config RECORD;
    v_display_text TEXT;
BEGIN
    -- Get pack configuration
    SELECT * INTO v_pack_config
    FROM inventory.product_pack_configurations
    WHERE product_id = NEW.product_id
    AND is_active = TRUE
    ORDER BY is_default DESC
    LIMIT 1;
    
    IF v_pack_config IS NULL THEN
        RETURN NEW;
    END IF;
    
    -- Calculate base quantity based on pack type
    CASE NEW.pack_type
        WHEN 'base' THEN
            v_base_quantity := NEW.quantity;
            
        WHEN 'pack' THEN
            v_base_quantity := NEW.quantity * v_pack_config.base_units_per_pack;
            
        WHEN 'box' THEN
            v_base_quantity := NEW.quantity * v_pack_config.packs_per_box * v_pack_config.base_units_per_pack;
            
        WHEN 'case' THEN
            v_base_quantity := NEW.quantity * v_pack_config.boxes_per_case * 
                              v_pack_config.packs_per_box * v_pack_config.base_units_per_pack;
            
        ELSE
            v_base_quantity := NEW.quantity;
    END CASE;
    
    -- Set calculated fields
    NEW.base_quantity := v_base_quantity;
    
    -- Calculate quantities at each level
    NEW.case_quantity := v_base_quantity / 
        (v_pack_config.boxes_per_case * v_pack_config.packs_per_box * v_pack_config.base_units_per_pack);
    
    NEW.box_quantity := v_base_quantity / 
        (v_pack_config.packs_per_box * v_pack_config.base_units_per_pack);
        
    NEW.pack_quantity := v_base_quantity / v_pack_config.base_units_per_pack;
    
    -- Generate display text
    v_display_text := format_pack_display(
        NEW.quantity,
        NEW.pack_type,
        v_pack_config.base_units_per_pack,
        v_pack_config.packs_per_box,
        v_pack_config.boxes_per_case,
        v_pack_config.base_uom,
        v_pack_config.pack_uom,
        v_pack_config.box_uom,
        v_pack_config.case_uom
    );
    
    -- Store pack display data
    NEW.pack_display_data := jsonb_build_object(
        'display_text', v_display_text,
        'base_quantity', v_base_quantity,
        'pack_breakdown', jsonb_build_object(
            'cases', NEW.case_quantity,
            'boxes', NEW.box_quantity,
            'packs', NEW.pack_quantity,
            'units', v_base_quantity
        ),
        'configuration', to_jsonb(v_pack_config)
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to relevant tables
CREATE TRIGGER trigger_calculate_pack_hierarchy_orders
    BEFORE INSERT OR UPDATE ON sales.order_items
    FOR EACH ROW
    EXECUTE FUNCTION calculate_pack_hierarchy();

CREATE TRIGGER trigger_calculate_pack_hierarchy_invoices
    BEFORE INSERT OR UPDATE ON sales.invoice_items
    FOR EACH ROW
    EXECUTE FUNCTION calculate_pack_hierarchy();

CREATE TRIGGER trigger_calculate_pack_hierarchy_inventory
    BEFORE INSERT OR UPDATE ON inventory.inventory_movements
    FOR EACH ROW
    EXECUTE FUNCTION calculate_pack_hierarchy();

-- =============================================
-- 3. STOCK RESERVATION MANAGEMENT TRIGGER
-- =============================================
-- Manages stock reservations for orders
CREATE OR REPLACE FUNCTION manage_stock_reservation()
RETURNS TRIGGER AS $$
DECLARE
    v_available_stock NUMERIC;
    v_already_reserved NUMERIC;
    v_product_name TEXT;
    v_location_name TEXT;
BEGIN
    -- Check stock availability before reservation
    IF NEW.reservation_status = 'active' THEN
        -- Get current available stock
        SELECT 
            lws.quantity_available - COALESCE(lws.quantity_reserved, 0),
            p.product_name,
            l.location_name
        INTO v_available_stock, v_product_name, v_location_name
        FROM inventory.location_wise_stock lws
        JOIN inventory.products p ON p.product_id = lws.product_id
        JOIN inventory.storage_locations l ON l.location_id = lws.location_id
        WHERE lws.product_id = NEW.product_id
        AND lws.batch_id = NEW.batch_id
        AND lws.location_id = NEW.location_id;
        
        -- Check if already reserved for this order
        SELECT COALESCE(SUM(reserved_quantity), 0)
        INTO v_already_reserved
        FROM inventory.stock_reservations
        WHERE product_id = NEW.product_id
        AND batch_id = NEW.batch_id
        AND location_id = NEW.location_id
        AND reference_type = NEW.reference_type
        AND reference_id = NEW.reference_id
        AND reservation_status = 'active'
        AND reservation_id != COALESCE(NEW.reservation_id, -1);
        
        -- Available after considering existing reservations
        v_available_stock := v_available_stock + v_already_reserved;
        
        IF v_available_stock < NEW.reserved_quantity THEN
            RAISE EXCEPTION 'Insufficient stock for reservation. Product: %, Location: %, Available: %, Requested: %',
                v_product_name, v_location_name, v_available_stock, NEW.reserved_quantity;
        END IF;
        
        -- Update location stock reservation
        UPDATE inventory.location_wise_stock
        SET 
            quantity_reserved = COALESCE(quantity_reserved, 0) - v_already_reserved + NEW.reserved_quantity,
            last_updated = CURRENT_TIMESTAMP
        WHERE product_id = NEW.product_id
        AND batch_id = NEW.batch_id
        AND location_id = NEW.location_id;
        
    ELSIF NEW.reservation_status IN ('fulfilled', 'cancelled', 'expired') THEN
        -- Release the reservation
        UPDATE inventory.location_wise_stock
        SET 
            quantity_reserved = GREATEST(0, COALESCE(quantity_reserved, 0) - OLD.reserved_quantity),
            last_updated = CURRENT_TIMESTAMP
        WHERE product_id = OLD.product_id
        AND batch_id = OLD.batch_id
        AND location_id = OLD.location_id;
    END IF;
    
    -- Set expiry time if not set
    IF NEW.reservation_status = 'active' AND NEW.expires_at IS NULL THEN
        NEW.expires_at := CURRENT_TIMESTAMP + INTERVAL '24 hours';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_manage_stock_reservation
    BEFORE INSERT OR UPDATE OF reservation_status ON inventory.stock_reservations
    FOR EACH ROW
    EXECUTE FUNCTION manage_stock_reservation();

-- =============================================
-- 4. BATCH COST AVERAGING TRIGGER
-- =============================================
-- Calculates weighted average cost for batches
CREATE OR REPLACE FUNCTION calculate_batch_cost_average()
RETURNS TRIGGER AS $$
DECLARE
    v_existing_quantity NUMERIC;
    v_existing_cost NUMERIC;
    v_new_average_cost NUMERIC;
BEGIN
    -- Only calculate for purchase/adjustment increase
    IF NEW.movement_type NOT IN ('purchase', 'adjustment_increase') THEN
        RETURN NEW;
    END IF;
    
    -- Get existing batch info
    SELECT 
        quantity_available,
        weighted_average_cost
    INTO v_existing_quantity, v_existing_cost
    FROM inventory.batches
    WHERE batch_id = NEW.batch_id;
    
    -- Calculate new weighted average
    IF v_existing_quantity IS NULL OR v_existing_quantity = 0 THEN
        v_new_average_cost := NEW.unit_cost;
    ELSE
        v_new_average_cost := (
            (v_existing_quantity * COALESCE(v_existing_cost, 0)) + 
            (NEW.quantity * NEW.unit_cost)
        ) / (v_existing_quantity + NEW.quantity);
    END IF;
    
    -- Update batch with new average cost
    UPDATE inventory.batches
    SET 
        weighted_average_cost = v_new_average_cost,
        last_cost_update = CURRENT_TIMESTAMP,
        cost_calculation_method = 'weighted_average'
    WHERE batch_id = NEW.batch_id;
    
    -- Store cost details in movement
    NEW.cost_details := jsonb_build_object(
        'previous_quantity', v_existing_quantity,
        'previous_cost', v_existing_cost,
        'new_quantity', NEW.quantity,
        'new_cost', NEW.unit_cost,
        'calculated_average', v_new_average_cost
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_calculate_batch_cost_average
    BEFORE INSERT ON inventory.inventory_movements
    FOR EACH ROW
    WHEN (NEW.movement_type IN ('purchase', 'adjustment_increase') AND NEW.unit_cost > 0)
    EXECUTE FUNCTION calculate_batch_cost_average();

-- =============================================
-- 5. MINIMUM STOCK ALERT TRIGGER
-- =============================================
-- Creates alerts when stock falls below minimum levels
CREATE OR REPLACE FUNCTION check_minimum_stock_alert()
RETURNS TRIGGER AS $$
DECLARE
    v_product_config RECORD;
    v_total_stock NUMERIC;
    v_location_stock NUMERIC;
BEGIN
    -- Get product stock configuration
    SELECT 
        p.product_id,
        p.product_name,
        p.min_stock_quantity,
        p.reorder_level,
        p.reorder_quantity,
        p.critical_stock_level
    INTO v_product_config
    FROM inventory.products p
    WHERE p.product_id = NEW.product_id;
    
    -- Skip if no minimum levels defined
    IF v_product_config.min_stock_quantity IS NULL AND 
       v_product_config.reorder_level IS NULL THEN
        RETURN NEW;
    END IF;
    
    -- Get current stock levels
    -- Location level
    v_location_stock := NEW.quantity_available - COALESCE(NEW.quantity_reserved, 0);
    
    -- Total across all locations
    SELECT COALESCE(SUM(quantity_available - COALESCE(quantity_reserved, 0)), 0)
    INTO v_total_stock
    FROM inventory.location_wise_stock
    WHERE product_id = NEW.product_id;
    
    -- Check critical level first
    IF v_product_config.critical_stock_level IS NOT NULL 
       AND v_total_stock <= v_product_config.critical_stock_level THEN
        
        INSERT INTO system_config.system_notifications (
            org_id,
            notification_type,
            notification_category,
            title,
            message,
            priority,
            target_audience,
            notification_data
        ) VALUES (
            NEW.org_id,
            'error',
            'inventory',
            'Critical Stock Level',
            format('CRITICAL: %s stock at %s units. Immediate action required!', 
                v_product_config.product_name, v_total_stock),
            'urgent',
            'inventory_managers',
            jsonb_build_object(
                'product_id', NEW.product_id,
                'product_name', v_product_config.product_name,
                'current_stock', v_total_stock,
                'critical_level', v_product_config.critical_stock_level,
                'location_id', NEW.location_id
            )
        );
        
    -- Check reorder level
    ELSIF v_product_config.reorder_level IS NOT NULL 
          AND v_total_stock <= v_product_config.reorder_level THEN
        
        -- Create reorder suggestion
        INSERT INTO inventory.reorder_suggestions (
            product_id,
            current_stock,
            reorder_level,
            suggested_quantity,
            urgency,
            created_at
        ) VALUES (
            NEW.product_id,
            v_total_stock,
            v_product_config.reorder_level,
            COALESCE(v_product_config.reorder_quantity, v_product_config.reorder_level * 2),
            CASE 
                WHEN v_total_stock < v_product_config.min_stock_quantity THEN 'high'
                ELSE 'normal'
            END,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (product_id) 
        DO UPDATE SET
            current_stock = EXCLUDED.current_stock,
            updated_at = CURRENT_TIMESTAMP;
        
    -- Check minimum stock
    ELSIF v_product_config.min_stock_quantity IS NOT NULL 
          AND v_total_stock < v_product_config.min_stock_quantity THEN
        
        INSERT INTO system_config.system_notifications (
            org_id,
            notification_type,
            notification_category,
            title,
            message,
            priority,
            target_audience,
            notification_data
        ) VALUES (
            NEW.org_id,
            'warning',
            'inventory',
            'Low Stock Alert',
            format('%s stock below minimum. Current: %s, Minimum: %s', 
                v_product_config.product_name, v_total_stock, v_product_config.min_stock_quantity),
            'high',
            'inventory_managers',
            jsonb_build_object(
                'product_id', NEW.product_id,
                'product_name', v_product_config.product_name,
                'current_stock', v_total_stock,
                'minimum_stock', v_product_config.min_stock_quantity,
                'location_id', NEW.location_id
            )
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_minimum_stock_alert
    AFTER INSERT OR UPDATE OF quantity_available, quantity_reserved 
    ON inventory.location_wise_stock
    FOR EACH ROW
    EXECUTE FUNCTION check_minimum_stock_alert();

-- =============================================
-- 6. BATCH EXPIRY TRACKING TRIGGER
-- =============================================
-- Tracks and alerts on batch expiry
CREATE OR REPLACE FUNCTION track_batch_expiry()
RETURNS TRIGGER AS $$
DECLARE
    v_days_to_expiry INTEGER;
    v_product_name TEXT;
BEGIN
    -- Calculate days to expiry
    v_days_to_expiry := (NEW.expiry_date - CURRENT_DATE)::INTEGER;
    
    -- Update batch expiry status
    NEW.expiry_status := CASE
        WHEN v_days_to_expiry <= 0 THEN 'expired'
        WHEN v_days_to_expiry <= 30 THEN 'critical'
        WHEN v_days_to_expiry <= 90 THEN 'warning'
        WHEN v_days_to_expiry <= 180 THEN 'caution'
        ELSE 'normal'
    END;
    
    -- Get product name for notifications
    SELECT product_name INTO v_product_name
    FROM inventory.products
    WHERE product_id = NEW.product_id;
    
    -- Create notifications based on status change
    IF (TG_OP = 'UPDATE' AND OLD.expiry_status != NEW.expiry_status) OR
       (TG_OP = 'INSERT' AND NEW.expiry_status IN ('expired', 'critical', 'warning')) THEN
        
        INSERT INTO system_config.system_notifications (
            org_id,
            notification_type,
            notification_category,
            title,
            message,
            priority,
            target_audience,
            notification_data
        ) VALUES (
            NEW.org_id,
            CASE 
                WHEN NEW.expiry_status = 'expired' THEN 'error'
                WHEN NEW.expiry_status = 'critical' THEN 'error'
                ELSE 'warning'
            END,
            'inventory',
            format('Batch Expiry Alert - %s', NEW.expiry_status),
            format('Batch %s of %s expires in %s days', 
                NEW.batch_number, v_product_name, v_days_to_expiry),
            CASE 
                WHEN NEW.expiry_status IN ('expired', 'critical') THEN 'urgent'
                ELSE 'high'
            END,
            'inventory_managers',
            jsonb_build_object(
                'batch_id', NEW.batch_id,
                'batch_number', NEW.batch_number,
                'product_id', NEW.product_id,
                'product_name', v_product_name,
                'expiry_date', NEW.expiry_date,
                'days_to_expiry', v_days_to_expiry,
                'quantity_available', NEW.quantity_available
            )
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_track_batch_expiry
    BEFORE INSERT OR UPDATE OF expiry_date ON inventory.batches
    FOR EACH ROW
    EXECUTE FUNCTION track_batch_expiry();

-- =============================================
-- 7. INTER-LOCATION TRANSFER TRIGGER
-- =============================================
-- Handles stock transfers between locations
CREATE OR REPLACE FUNCTION handle_inter_location_transfer()
RETURNS TRIGGER AS $$
BEGIN
    -- Only process for transfer type movements
    IF NEW.movement_type != 'transfer' THEN
        RETURN NEW;
    END IF;
    
    -- Validate transfer data
    IF NEW.from_location_id IS NULL OR NEW.to_location_id IS NULL THEN
        RAISE EXCEPTION 'Both from_location_id and to_location_id required for transfers';
    END IF;
    
    IF NEW.from_location_id = NEW.to_location_id THEN
        RAISE EXCEPTION 'Cannot transfer to same location';
    END IF;
    
    -- Create paired movements
    IF NEW.transfer_type = 'out' THEN
        -- This is the source movement, create destination movement
        INSERT INTO inventory.inventory_movements (
            org_id,
            movement_type,
            movement_date,
            product_id,
            batch_id,
            location_id,
            from_location_id,
            to_location_id,
            quantity,
            pack_type,
            transfer_type,
            reference_type,
            reference_id,
            transfer_pair_id,
            created_by
        ) VALUES (
            NEW.org_id,
            'transfer',
            NEW.movement_date,
            NEW.product_id,
            NEW.batch_id,
            NEW.to_location_id,  -- Location for IN movement
            NEW.from_location_id,
            NEW.to_location_id,
            NEW.quantity,
            NEW.pack_type,
            'in',  -- Paired IN movement
            NEW.reference_type,
            NEW.reference_id,
            NEW.movement_id,  -- Link to this movement
            NEW.created_by
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_handle_inter_location_transfer
    AFTER INSERT ON inventory.inventory_movements
    FOR EACH ROW
    WHEN (NEW.movement_type = 'transfer' AND NEW.transfer_type = 'out')
    EXECUTE FUNCTION handle_inter_location_transfer();

-- =============================================
-- SUPPORTING INDEXES FOR INVENTORY TRIGGERS
-- =============================================
CREATE INDEX IF NOT EXISTS idx_location_wise_stock_lookup 
    ON inventory.location_wise_stock(product_id, batch_id, location_id);
    
CREATE INDEX IF NOT EXISTS idx_inventory_movements_sync 
    ON inventory.inventory_movements(product_id, batch_id, location_id, movement_type);
    
CREATE INDEX IF NOT EXISTS idx_stock_reservations_active 
    ON inventory.stock_reservations(product_id, batch_id, location_id, reservation_status);
    
CREATE INDEX IF NOT EXISTS idx_batches_expiry 
    ON inventory.batches(expiry_date, expiry_status)
    WHERE quantity_available > 0;