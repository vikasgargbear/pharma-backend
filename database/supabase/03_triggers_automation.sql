-- =============================================
-- PHARMACEUTICAL ERP - TRIGGERS & AUTOMATION
-- =============================================
-- Version: 1.0 - Production Ready
-- Description: Business triggers and automation
-- Deploy Order: 3rd - After business functions
-- =============================================

-- =============================================
-- PRODUCT MANAGEMENT TRIGGERS
-- =============================================

-- Update product search data
CREATE OR REPLACE FUNCTION update_product_search_data()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_keywords := ARRAY[
        LOWER(NEW.product_name),
        LOWER(COALESCE(NEW.generic_name, '')),
        LOWER(COALESCE(NEW.manufacturer, '')),
        LOWER(COALESCE(NEW.category, '')),
        COALESCE(NEW.hsn_code, ''),
        COALESCE(NEW.barcode, '')
    ];
    
    NEW.category_path := COALESCE(NEW.category, '') || 
        CASE WHEN NEW.subcategory IS NOT NULL THEN ' > ' || NEW.subcategory ELSE '' END;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_product_search_data
    BEFORE INSERT OR UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_product_search_data();

-- Auto-setup product UOM
CREATE OR REPLACE FUNCTION auto_setup_product_uom()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.product_type_id IS NOT NULL AND NEW.base_uom_code IS NULL THEN
        SELECT 
            default_base_uom,
            default_purchase_uom,
            default_display_uom
        INTO 
            NEW.base_uom_code,
            NEW.purchase_uom_code,
            NEW.display_uom_code
        FROM product_types
        WHERE type_id = NEW.product_type_id;
        
        IF NEW.base_uom_code IN ('TABLET', 'CAPSULE') THEN
            NEW.sale_uom_code := 'STRIP';
            NEW.allow_loose_units := TRUE;
        ELSE
            NEW.sale_uom_code := NEW.base_uom_code;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_setup_product_uom
    BEFORE INSERT OR UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION auto_setup_product_uom();

-- =============================================
-- BATCH MANAGEMENT TRIGGERS
-- =============================================

-- Update batch status
CREATE OR REPLACE FUNCTION update_batch_status()
RETURNS TRIGGER AS $$
BEGIN
    NEW.days_to_expiry := (NEW.expiry_date - CURRENT_DATE)::INTEGER;
    NEW.is_near_expiry := NEW.days_to_expiry <= 90;
    
    NEW.current_stock_status := CASE
        WHEN NEW.quantity_available <= 0 THEN 'out_of_stock'
        WHEN NEW.quantity_available <= 10 THEN 'low_stock'
        WHEN NEW.is_near_expiry THEN 'near_expiry'
        ELSE 'in_stock'
    END;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_batch_status
    BEFORE INSERT OR UPDATE ON batches
    FOR EACH ROW
    EXECUTE FUNCTION update_batch_status();

-- =============================================
-- ORDER MANAGEMENT TRIGGERS
-- =============================================

-- Credit limit enforcement
CREATE OR REPLACE FUNCTION check_credit_limit_on_order()
RETURNS TRIGGER AS $$
DECLARE
    v_customer_record RECORD;
    v_current_outstanding DECIMAL(15,2);
    v_total_exposure DECIMAL(15,2);
BEGIN
    SELECT 
        c.credit_limit,
        c.customer_name,
        c.customer_type
    INTO v_customer_record
    FROM customers c
    WHERE c.customer_id = NEW.customer_id;
    
    IF NEW.payment_mode = 'cash' THEN
        RETURN NEW;
    END IF;
    
    IF v_customer_record.credit_limit = 0 THEN
        RETURN NEW;
    END IF;
    
    SELECT COALESCE(SUM(outstanding_amount), 0)
    INTO v_current_outstanding
    FROM customer_outstanding
    WHERE customer_id = NEW.customer_id
    AND org_id = NEW.org_id
    AND status IN ('pending', 'overdue');
    
    v_total_exposure := v_current_outstanding + NEW.final_amount;
    
    IF v_total_exposure > v_customer_record.credit_limit THEN
        INSERT INTO system_notifications (
            notification_type, title, message, 
            target_type, target_value, priority, action_required
        ) VALUES (
            'alert',
            'CREDIT LIMIT EXCEEDED',
            'Order #' || NEW.order_number || ' for ' || v_customer_record.customer_name || 
            ' exceeds credit limit. Outstanding: ₹' || v_current_outstanding || 
            ', Order: ₹' || NEW.final_amount || ', Limit: ₹' || v_customer_record.credit_limit,
            'role', 'sales_manager', 'urgent', TRUE
        );
        
        -- For now, just warn - don't block
        NEW.order_status = 'credit_hold';
        NEW.notes = COALESCE(NEW.notes || E'\n', '') || 
            '[SYSTEM] Credit limit exceeded. Approval required.';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_credit_limit_on_order
    BEFORE INSERT ON orders
    FOR EACH ROW
    EXECUTE FUNCTION check_credit_limit_on_order();

-- Outstanding creation on delivery
CREATE OR REPLACE FUNCTION create_outstanding_on_order_completion()
RETURNS TRIGGER AS $$
BEGIN
    IF (NEW.order_status IN ('delivered', 'invoiced') 
        AND OLD.order_status NOT IN ('delivered', 'invoiced')
        AND NEW.payment_mode = 'credit') THEN
        
        IF NOT EXISTS (
            SELECT 1 FROM customer_outstanding 
            WHERE order_id = NEW.order_id
        ) THEN
            INSERT INTO customer_outstanding (
                org_id, customer_id, order_id,
                total_amount, outstanding_amount, paid_amount,
                invoice_date, due_date, status
            ) VALUES (
                NEW.org_id, NEW.customer_id, NEW.order_id,
                NEW.final_amount, NEW.final_amount, 0,
                COALESCE(NEW.invoice_date, CURRENT_DATE),
                COALESCE(NEW.payment_due_date, CURRENT_DATE + INTERVAL '30 days'),
                'pending'
            );
        END IF;
    END IF;
    
    IF NEW.order_status = 'cancelled' AND OLD.order_status != 'cancelled' THEN
        UPDATE customer_outstanding
        SET status = 'cancelled',
            outstanding_amount = 0,
            updated_at = CURRENT_TIMESTAMP
        WHERE order_id = NEW.order_id
        AND status IN ('pending', 'overdue');
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_outstanding_on_order_completion
    AFTER UPDATE OF order_status ON orders
    FOR EACH ROW
    EXECUTE FUNCTION create_outstanding_on_order_completion();

-- =============================================
-- INVENTORY MANAGEMENT TRIGGERS
-- =============================================

-- Inventory update with concurrency control
CREATE OR REPLACE FUNCTION update_inventory_on_order_enhanced()
RETURNS TRIGGER AS $$
DECLARE
    v_batch RECORD;
    v_org_id UUID;
BEGIN
    SELECT org_id INTO v_org_id FROM orders WHERE order_id = NEW.order_id;
    
    IF TG_OP = 'INSERT' THEN
        SELECT * INTO v_batch
        FROM batches
        WHERE batch_id = NEW.batch_id
        FOR UPDATE NOWAIT;
        
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Batch % not found', NEW.batch_id;
        END IF;
        
        IF v_batch.quantity_available < NEW.quantity THEN
            RAISE EXCEPTION 'Insufficient stock in batch %. Available: %, Required: %',
                NEW.batch_id, v_batch.quantity_available, NEW.quantity;
        END IF;
        
        UPDATE batches 
        SET quantity_available = quantity_available - NEW.quantity,
            quantity_sold = quantity_sold + NEW.quantity,
            updated_at = CURRENT_TIMESTAMP
        WHERE batch_id = NEW.batch_id
        AND quantity_available >= NEW.quantity;
        
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Failed to update batch inventory';
        END IF;
        
        INSERT INTO inventory_movements (
            org_id, product_id, batch_id, movement_type, 
            quantity_out, balance_quantity, reference_type, reference_id
        ) VALUES (
            v_org_id, NEW.product_id, NEW.batch_id, 'sale', 
            NEW.quantity,
            (SELECT quantity_available FROM batches WHERE batch_id = NEW.batch_id),
            'order', NEW.order_id
        );
        
    ELSIF TG_OP = 'UPDATE' THEN
        IF NEW.quantity != OLD.quantity OR NEW.batch_id != OLD.batch_id THEN
            UPDATE batches 
            SET quantity_available = quantity_available + OLD.quantity,
                quantity_sold = quantity_sold - OLD.quantity
            WHERE batch_id = OLD.batch_id;
            
            UPDATE batches 
            SET quantity_available = quantity_available - NEW.quantity,
                quantity_sold = quantity_sold + NEW.quantity
            WHERE batch_id = NEW.batch_id
            AND quantity_available >= NEW.quantity;
            
            IF NOT FOUND THEN
                UPDATE batches 
                SET quantity_available = quantity_available - OLD.quantity,
                    quantity_sold = quantity_sold + OLD.quantity
                WHERE batch_id = OLD.batch_id;
                
                RAISE EXCEPTION 'Insufficient stock for modification';
            END IF;
        END IF;
        
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE batches 
        SET quantity_available = quantity_available + OLD.quantity,
            quantity_sold = GREATEST(0, quantity_sold - OLD.quantity),
            updated_at = CURRENT_TIMESTAMP
        WHERE batch_id = OLD.batch_id;
        
        INSERT INTO inventory_movements (
            org_id, product_id, batch_id, movement_type, 
            quantity_in, balance_quantity, reference_type, reference_id, notes
        ) VALUES (
            v_org_id, OLD.product_id, OLD.batch_id, 'return', 
            OLD.quantity,
            (SELECT quantity_available FROM batches WHERE batch_id = OLD.batch_id),
            'order', OLD.order_id, 'Order item cancelled/deleted'
        );
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_inventory_on_order_enhanced
    AFTER INSERT OR UPDATE OR DELETE ON order_items
    FOR EACH ROW
    EXECUTE FUNCTION update_inventory_on_order_enhanced();

-- FEFO batch allocation
CREATE TRIGGER trigger_allocate_batch_fefo
    BEFORE INSERT ON order_items
    FOR EACH ROW
    WHEN (NEW.batch_id IS NULL)
    EXECUTE FUNCTION allocate_batch_fefo();

-- =============================================
-- PAYMENT TRIGGERS
-- =============================================

-- Payment allocation (FIFO)
CREATE OR REPLACE FUNCTION update_outstanding_on_payment()
RETURNS TRIGGER AS $$
DECLARE
    v_payment_amount DECIMAL(12,2);
    v_outstanding_record RECORD;
BEGIN
    IF NEW.payment_status = 'completed' AND (OLD.payment_status IS NULL OR OLD.payment_status != 'completed') THEN
        v_payment_amount := NEW.amount;
        
        FOR v_outstanding_record IN 
            SELECT outstanding_id, outstanding_amount 
            FROM customer_outstanding 
            WHERE customer_id = NEW.customer_id 
            AND org_id = NEW.org_id
            AND status IN ('pending', 'overdue')
            AND outstanding_amount > 0
            ORDER BY invoice_date ASC
        LOOP
            EXIT WHEN v_payment_amount <= 0;
            
            IF v_payment_amount >= v_outstanding_record.outstanding_amount THEN
                UPDATE customer_outstanding 
                SET 
                    paid_amount = paid_amount + v_outstanding_record.outstanding_amount,
                    outstanding_amount = 0,
                    status = 'paid',
                    updated_at = CURRENT_TIMESTAMP
                WHERE outstanding_id = v_outstanding_record.outstanding_id;
                
                v_payment_amount := v_payment_amount - v_outstanding_record.outstanding_amount;
            ELSE
                UPDATE customer_outstanding 
                SET 
                    paid_amount = paid_amount + v_payment_amount,
                    outstanding_amount = outstanding_amount - v_payment_amount,
                    updated_at = CURRENT_TIMESTAMP
                WHERE outstanding_id = v_outstanding_record.outstanding_id;
                
                v_payment_amount := 0;
            END IF;
        END LOOP;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_outstanding_on_payment
    AFTER UPDATE OF payment_status
    ON payments
    FOR EACH ROW
    EXECUTE FUNCTION update_outstanding_on_payment();

-- =============================================
-- TIMESTAMP TRIGGERS
-- =============================================

-- Update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for all tables with updated_at
CREATE TRIGGER trigger_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_suppliers_updated_at BEFORE UPDATE ON suppliers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_products_updated_at BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_batches_updated_at BEFORE UPDATE ON batches FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_payments_updated_at BEFORE UPDATE ON payments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- NOTIFICATION TRIGGERS
-- =============================================

-- Low stock notification
CREATE OR REPLACE FUNCTION check_low_stock_notification()
RETURNS TRIGGER AS $$
DECLARE
    v_product_name TEXT;
    v_total_stock INTEGER;
    v_min_stock INTEGER;
BEGIN
    SELECT p.product_name, p.minimum_stock_level
    INTO v_product_name, v_min_stock
    FROM products p
    WHERE p.product_id = NEW.product_id;
    
    SELECT SUM(quantity_available)
    INTO v_total_stock
    FROM batches
    WHERE product_id = NEW.product_id
    AND org_id = NEW.org_id;
    
    IF v_total_stock <= v_min_stock AND v_min_stock > 0 THEN
        INSERT INTO system_notifications (
            notification_type, title, message,
            target_type, target_value, priority
        ) VALUES (
            'warning',
            'Low Stock Alert',
            'Product "' || v_product_name || '" is running low. Current stock: ' || v_total_stock || ', Minimum: ' || v_min_stock,
            'role', 'inventory_manager', 'high'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_low_stock_notification
    AFTER UPDATE OF quantity_available ON batches
    FOR EACH ROW
    WHEN (OLD.quantity_available != NEW.quantity_available)
    EXECUTE FUNCTION check_low_stock_notification();

-- Near expiry notification
CREATE OR REPLACE FUNCTION check_near_expiry_notification()
RETURNS TRIGGER AS $$
DECLARE
    v_product_name TEXT;
BEGIN
    IF NEW.is_near_expiry = TRUE AND (OLD.is_near_expiry IS NULL OR OLD.is_near_expiry = FALSE) THEN
        SELECT product_name INTO v_product_name
        FROM products
        WHERE product_id = NEW.product_id;
        
        INSERT INTO system_notifications (
            notification_type, title, message,
            target_type, target_value, priority
        ) VALUES (
            'warning',
            'Near Expiry Alert',
            'Batch "' || NEW.batch_number || '" of "' || v_product_name || '" expires on ' || NEW.expiry_date || ' (' || NEW.days_to_expiry || ' days)',
            'role', 'inventory_manager', 'medium'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_near_expiry_notification
    AFTER UPDATE OF is_near_expiry ON batches
    FOR EACH ROW
    EXECUTE FUNCTION check_near_expiry_notification();

-- =============================================
-- OUTSTANDING TRANSACTIONS TRIGGERS
-- =============================================

-- Update days overdue for outstanding transactions
CREATE OR REPLACE FUNCTION update_outstanding_days()
RETURNS TRIGGER AS $$
BEGIN
    NEW.days_overdue := GREATEST(0, (CURRENT_DATE - NEW.due_date)::INTEGER);
    
    -- Update status based on days overdue
    NEW.status := CASE
        WHEN NEW.days_overdue = 0 THEN 'current'
        WHEN NEW.days_overdue <= 30 THEN 'overdue_30'
        WHEN NEW.days_overdue <= 60 THEN 'overdue_60'
        WHEN NEW.days_overdue <= 90 THEN 'overdue_90'
        ELSE 'overdue_90_plus'
    END;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for customer outstanding
CREATE TRIGGER trigger_update_customer_outstanding_days
    BEFORE INSERT OR UPDATE ON customer_outstanding
    FOR EACH ROW
    EXECUTE FUNCTION update_outstanding_days();

-- Trigger for supplier outstanding  
CREATE TRIGGER trigger_update_supplier_outstanding_days
    BEFORE INSERT OR UPDATE ON supplier_outstanding
    FOR EACH ROW
    EXECUTE FUNCTION update_outstanding_days();

-- =============================================
-- SUCCESS MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
TRIGGERS & AUTOMATION DEPLOYED SUCCESSFULLY
=============================================
✓ Product Management Triggers
✓ Batch Management Triggers
✓ Order Management Triggers
✓ Inventory Management Triggers
✓ Payment Triggers
✓ Timestamp Triggers
✓ Notification Triggers
✓ Outstanding Transactions Triggers

Next: Deploy 04_indexes_performance.sql
';
END $$;