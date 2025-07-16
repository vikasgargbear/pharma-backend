-- =============================================
-- PHARMACEUTICAL ERP - ADDITIONAL BUSINESS FUNCTIONS
-- =============================================
-- Version: 1.0 - Production Ready
-- Description: Additional business functions for barcode and financial features
-- Deploy Order: 2b - After core business functions
-- =============================================

-- =============================================
-- BARCODE GENERATION FUNCTIONS
-- =============================================

-- Generate GTIN check digit
CREATE OR REPLACE FUNCTION calculate_gtin_check_digit(p_barcode TEXT)
RETURNS TEXT AS $$
DECLARE
    v_sum INTEGER := 0;
    v_digit INTEGER;
    v_multiplier INTEGER;
    i INTEGER;
BEGIN
    -- GTIN check digit calculation (mod 10)
    FOR i IN REVERSE LENGTH(p_barcode)..1 LOOP
        v_digit := SUBSTRING(p_barcode FROM i FOR 1)::INTEGER;
        v_multiplier := CASE WHEN (LENGTH(p_barcode) - i + 1) % 2 = 0 THEN 1 ELSE 3 END;
        v_sum := v_sum + (v_digit * v_multiplier);
    END LOOP;
    
    RETURN ((10 - (v_sum % 10)) % 10)::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Generate GTIN barcode
CREATE OR REPLACE FUNCTION generate_gtin(
    p_org_id UUID,
    p_product_id INTEGER
) RETURNS TEXT AS $$
DECLARE
    v_sequence RECORD;
    v_barcode TEXT;
    v_padded_value TEXT;
    v_check_digit TEXT;
BEGIN
    -- Get or create sequence for organization
    SELECT * INTO v_sequence
    FROM barcode_sequences
    WHERE org_id = p_org_id
    AND sequence_type = 'GTIN'
    FOR UPDATE;
    
    IF NOT FOUND THEN
        INSERT INTO barcode_sequences (org_id, sequence_type, prefix, current_value)
        VALUES (p_org_id, 'GTIN', '890', 1)
        RETURNING * INTO v_sequence;
    END IF;
    
    -- Generate barcode
    v_padded_value := LPAD(v_sequence.current_value::TEXT, 9, '0');
    v_barcode := v_sequence.prefix || v_padded_value;
    v_check_digit := calculate_gtin_check_digit(v_barcode);
    v_barcode := v_barcode || v_check_digit;
    
    -- Update sequence
    UPDATE barcode_sequences
    SET current_value = current_value + 1
    WHERE sequence_id = v_sequence.sequence_id;
    
    -- Store in barcode master
    INSERT INTO barcode_master (
        org_id, barcode_value, barcode_type, 
        reference_type, product_id
    ) VALUES (
        p_org_id, v_barcode, 'GTIN',
        'product', p_product_id
    );
    
    -- Update product
    UPDATE products
    SET barcode = v_barcode
    WHERE product_id = p_product_id
    AND barcode IS NULL;
    
    RETURN v_barcode;
END;
$$ LANGUAGE plpgsql;

-- Generate batch barcode
CREATE OR REPLACE FUNCTION generate_batch_barcode(
    p_org_id UUID,
    p_batch_id INTEGER
) RETURNS TEXT AS $$
DECLARE
    v_batch RECORD;
    v_barcode TEXT;
    v_serial_number TEXT;
BEGIN
    -- Get batch details
    SELECT b.*, p.barcode as product_barcode
    INTO v_batch
    FROM batches b
    JOIN products p ON p.product_id = b.product_id
    WHERE b.batch_id = p_batch_id;
    
    -- Generate serial number
    v_serial_number := TO_CHAR(CURRENT_DATE, 'YYMMDD') || 
                      LPAD(p_batch_id::TEXT, 6, '0');
    
    -- Create GS1-128 barcode
    v_barcode := '(01)' || v_batch.product_barcode || 
                 '(10)' || v_batch.batch_number ||
                 '(17)' || TO_CHAR(v_batch.expiry_date, 'YYMMDD') ||
                 '(21)' || v_serial_number;
    
    -- Store in barcode master
    INSERT INTO barcode_master (
        org_id, barcode_value, barcode_type,
        reference_type, product_id, batch_id,
        serial_number, is_serialized
    ) VALUES (
        p_org_id, v_barcode, 'GS1-128',
        'batch', v_batch.product_id, p_batch_id,
        v_serial_number, true
    );
    
    RETURN v_barcode;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- ACCOUNTING INTEGRATION HOOKS
-- =============================================

-- Create financial sync record for payments
CREATE OR REPLACE FUNCTION queue_payment_for_financial_sync()
RETURNS TRIGGER AS $$
BEGIN
    -- Only process completed payments
    IF NEW.payment_status != 'completed' OR OLD.payment_status = 'completed' THEN
        RETURN NEW;
    END IF;
    
    -- Insert into a sync queue table (if financial module is connected)
    INSERT INTO financial_sync_queue (
        org_id,
        sync_type,
        reference_type,
        reference_id,
        sync_data,
        created_at
    ) VALUES (
        NEW.org_id,
        'payment',
        NEW.payment_type,
        NEW.payment_id,
        jsonb_build_object(
            'payment_number', NEW.payment_number,
            'payment_date', NEW.payment_date,
            'amount', NEW.amount,
            'payment_mode', NEW.payment_mode,
            'customer_id', NEW.customer_id,
            'supplier_id', NEW.supplier_id,
            'reference_number', NEW.reference_number
        ),
        CURRENT_TIMESTAMP
    ) ON CONFLICT DO NOTHING;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create financial sync queue table (lightweight)
CREATE TABLE IF NOT EXISTS financial_sync_queue (
    sync_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    sync_type TEXT NOT NULL,
    reference_type TEXT NOT NULL,
    reference_id INTEGER NOT NULL,
    sync_data JSONB NOT NULL,
    sync_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP WITH TIME ZONE
);

-- =============================================
-- PURCHASE ORDER FUNCTIONS
-- =============================================

-- Create batches from purchase
CREATE OR REPLACE FUNCTION create_batches_from_purchase()
RETURNS TRIGGER AS $$
DECLARE
    v_item RECORD;
    v_batch_id INTEGER;
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
            NEW.org_id, v_item.product_id, v_item.batch_number,
            v_item.manufacturing_date, v_item.expiry_date,
            v_item.received_quantity, v_item.received_quantity,
            v_item.cost_price, v_item.mrp,
            NEW.supplier_id, NEW.purchase_id,
            NEW.supplier_invoice_number,
            NEW.created_by
        ) RETURNING batch_id INTO v_batch_id;
        
        -- Generate batch barcode
        PERFORM generate_batch_barcode(NEW.org_id, v_batch_id);
        
        -- Create inventory movement
        INSERT INTO inventory_movements (
            org_id, product_id, batch_id, movement_type,
            quantity_in, balance_quantity,
            reference_type, reference_id, reference_number,
            performed_by
        ) VALUES (
            NEW.org_id, v_item.product_id, v_batch_id, 'purchase',
            v_item.received_quantity,
            v_item.received_quantity,
            'purchase', NEW.purchase_id, NEW.purchase_number,
            NEW.created_by
        );
    END LOOP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- REPORTING FUNCTIONS
-- =============================================

-- Get sales summary
CREATE OR REPLACE FUNCTION get_sales_summary(
    p_org_id UUID,
    p_from_date DATE,
    p_to_date DATE
) RETURNS TABLE (
    order_date DATE,
    total_orders BIGINT,
    total_amount DECIMAL(15,2),
    cash_amount DECIMAL(15,2),
    credit_amount DECIMAL(15,2),
    avg_order_value DECIMAL(15,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.order_date,
        COUNT(*)::BIGINT as total_orders,
        SUM(o.final_amount) as total_amount,
        SUM(CASE WHEN o.payment_mode = 'cash' THEN o.final_amount ELSE 0 END) as cash_amount,
        SUM(CASE WHEN o.payment_mode = 'credit' THEN o.final_amount ELSE 0 END) as credit_amount,
        AVG(o.final_amount) as avg_order_value
    FROM orders o
    WHERE o.org_id = p_org_id
    AND o.order_date BETWEEN p_from_date AND p_to_date
    AND o.order_status IN ('delivered', 'invoiced')
    GROUP BY o.order_date
    ORDER BY o.order_date;
END;
$$ LANGUAGE plpgsql;

-- Get inventory valuation
CREATE OR REPLACE FUNCTION get_inventory_valuation(
    p_org_id UUID,
    p_as_of_date DATE DEFAULT CURRENT_DATE
) RETURNS TABLE (
    product_id INTEGER,
    product_name TEXT,
    total_quantity INTEGER,
    avg_cost DECIMAL(12,2),
    total_value DECIMAL(15,2),
    mrp_value DECIMAL(15,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.product_id,
        p.product_name,
        SUM(b.quantity_available)::INTEGER as total_quantity,
        AVG(b.cost_price) as avg_cost,
        SUM(b.quantity_available * b.cost_price) as total_value,
        SUM(b.quantity_available * b.mrp) as mrp_value
    FROM products p
    JOIN batches b ON b.product_id = p.product_id
    WHERE p.org_id = p_org_id
    AND b.quantity_available > 0
    AND b.batch_status = 'active'
    GROUP BY p.product_id, p.product_name
    ORDER BY total_value DESC;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- UPDATE CALCULATED FIELDS FUNCTION
-- =============================================

-- Function to update all calculated fields for existing data
CREATE OR REPLACE FUNCTION update_calculated_fields()
RETURNS TEXT AS $$
DECLARE
    v_updated_batches INTEGER;
    v_updated_customer_outstanding INTEGER;
    v_updated_supplier_outstanding INTEGER;
BEGIN
    -- Update batch days to expiry and status
    UPDATE batches SET 
        days_to_expiry = (expiry_date - CURRENT_DATE)::INTEGER,
        is_near_expiry = ((expiry_date - CURRENT_DATE)::INTEGER <= 90),
        current_stock_status = CASE
            WHEN quantity_available <= 0 THEN 'out_of_stock'
            WHEN quantity_available <= 10 THEN 'low_stock'
            WHEN ((expiry_date - CURRENT_DATE)::INTEGER <= 90) THEN 'near_expiry'
            ELSE 'in_stock'
        END;
    
    GET DIAGNOSTICS v_updated_batches = ROW_COUNT;
    
    -- Update customer outstanding days overdue
    UPDATE customer_outstanding SET 
        days_overdue = GREATEST(0, (CURRENT_DATE - due_date)::INTEGER),
        status = CASE
            WHEN GREATEST(0, (CURRENT_DATE - due_date)::INTEGER) = 0 THEN 'current'
            WHEN GREATEST(0, (CURRENT_DATE - due_date)::INTEGER) <= 30 THEN 'overdue_30'
            WHEN GREATEST(0, (CURRENT_DATE - due_date)::INTEGER) <= 60 THEN 'overdue_60'
            WHEN GREATEST(0, (CURRENT_DATE - due_date)::INTEGER) <= 90 THEN 'overdue_90'
            ELSE 'overdue_90_plus'
        END;
    
    GET DIAGNOSTICS v_updated_customer_outstanding = ROW_COUNT;
    
    -- Update supplier outstanding days overdue
    UPDATE supplier_outstanding SET 
        days_overdue = GREATEST(0, (CURRENT_DATE - due_date)::INTEGER),
        status = CASE
            WHEN GREATEST(0, (CURRENT_DATE - due_date)::INTEGER) = 0 THEN 'current'
            WHEN GREATEST(0, (CURRENT_DATE - due_date)::INTEGER) <= 30 THEN 'overdue_30'
            WHEN GREATEST(0, (CURRENT_DATE - due_date)::INTEGER) <= 60 THEN 'overdue_60'
            WHEN GREATEST(0, (CURRENT_DATE - due_date)::INTEGER) <= 90 THEN 'overdue_90'
            ELSE 'overdue_90_plus'
        END;
    
    GET DIAGNOSTICS v_updated_supplier_outstanding = ROW_COUNT;
    
    RETURN format('Updated calculated fields: %s batches, %s customer outstanding, %s supplier outstanding', 
                  v_updated_batches, v_updated_customer_outstanding, v_updated_supplier_outstanding);
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- SUCCESS MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
ADDITIONAL FUNCTIONS DEPLOYED SUCCESSFULLY
=============================================
✓ Barcode Generation Functions
✓ Financial Functions
✓ Purchase Order Functions
✓ Reporting Functions
✓ Calculated Fields Update Function

Next: Deploy 03_triggers_automation.sql
';
END $$;