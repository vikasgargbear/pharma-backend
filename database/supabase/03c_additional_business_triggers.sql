-- =============================================
-- PHARMACEUTICAL ERP - ADDITIONAL BUSINESS TRIGGERS
-- =============================================
-- Version: 1.0
-- Description: Triggers for sales returns, stock adjustments, and tax entries
-- Deploy Order: After 03b_additional_triggers.sql
-- =============================================

-- =============================================
-- SALES RETURN TRIGGERS
-- =============================================

-- Auto-update inventory when sales return is approved
CREATE OR REPLACE FUNCTION process_sales_return_approval()
RETURNS TRIGGER AS $$
BEGIN
    -- Only process when status changes to 'approved'
    IF NEW.return_status = 'approved' AND OLD.return_status != 'approved' THEN
        -- Update batch quantity (add stock back)
        UPDATE batches 
        SET 
            quantity_available = quantity_available + NEW.quantity,
            quantity_sold = GREATEST(0, quantity_sold - NEW.quantity)
        WHERE batch_id = NEW.batch_id;
        
        -- Create inventory movement record
        INSERT INTO inventory_movements (
            product_id, batch_id, movement_type,
            quantity, movement_date, reference_type,
            reference_id, notes
        ) VALUES (
            NEW.product_id, NEW.batch_id, 'sales_return',
            NEW.quantity, CURRENT_TIMESTAMP, 'sales_return',
            NEW.return_id, 'Stock returned - ' || NEW.reason
        );
        
        -- Update customer statistics (reduce purchase amount)
        UPDATE customers 
        SET 
            total_purchases = total_purchases - NEW.refund_amount,
            last_return_date = CURRENT_TIMESTAMP
        WHERE customer_id = (
            SELECT customer_id FROM orders WHERE order_id = NEW.order_id
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_process_sales_return_approval
    AFTER UPDATE OF return_status
    ON sales_returns
    FOR EACH ROW
    EXECUTE FUNCTION process_sales_return_approval();

-- Create credit note when return is approved
CREATE OR REPLACE FUNCTION create_credit_note_on_return()
RETURNS TRIGGER AS $$
DECLARE
    v_credit_note_number TEXT;
    v_customer_id INTEGER;
BEGIN
    IF NEW.return_status = 'approved' AND OLD.return_status != 'approved' THEN
        -- Generate credit note number
        v_credit_note_number := 'CN-' || TO_CHAR(CURRENT_DATE, 'YYYYMM') || '-' || 
                               LPAD(NEXTVAL('credit_note_seq')::TEXT, 5, '0');
        
        -- Get customer ID
        SELECT customer_id INTO v_customer_id 
        FROM orders WHERE order_id = NEW.order_id;
        
        -- Update return with credit note number
        NEW.credit_note_number := v_credit_note_number;
        
        -- Create accounting entry
        INSERT INTO accounting_entries (
            entry_type, entry_date, reference_type,
            reference_id, reference_number, party_id,
            debit_amount, credit_amount, notes
        ) VALUES (
            'credit_note', CURRENT_DATE, 'sales_return',
            NEW.return_id, v_credit_note_number, v_customer_id,
            NEW.refund_amount, 0, 'Sales return credit note'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_credit_note
    BEFORE UPDATE OF return_status
    ON sales_returns
    FOR EACH ROW
    EXECUTE FUNCTION create_credit_note_on_return();

-- =============================================
-- STOCK ADJUSTMENT TRIGGERS
-- =============================================

-- Validate stock adjustment quantities
CREATE OR REPLACE FUNCTION validate_stock_adjustment()
RETURNS TRIGGER AS $$
DECLARE
    v_current_stock INTEGER;
BEGIN
    -- Get current stock
    SELECT quantity_available INTO v_current_stock
    FROM batches WHERE batch_id = NEW.batch_id;
    
    -- For negative adjustments, check if enough stock
    IF NEW.quantity_adjusted < 0 THEN
        IF (v_current_stock + NEW.quantity_adjusted) < 0 THEN
            RAISE EXCEPTION 'Insufficient stock for adjustment. Available: %, Requested: %', 
                            v_current_stock, NEW.quantity_adjusted;
        END IF;
    END IF;
    
    -- Set old and new quantities
    NEW.old_quantity := v_current_stock;
    NEW.new_quantity := v_current_stock + NEW.quantity_adjusted;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validate_stock_adjustment
    BEFORE INSERT ON stock_adjustments
    FOR EACH ROW
    EXECUTE FUNCTION validate_stock_adjustment();

-- Auto-update batch quantities after adjustment
CREATE OR REPLACE FUNCTION apply_stock_adjustment()
RETURNS TRIGGER AS $$
BEGIN
    -- Update batch quantity
    UPDATE batches 
    SET quantity_available = NEW.new_quantity
    WHERE batch_id = NEW.batch_id;
    
    -- Create inventory movement
    INSERT INTO inventory_movements (
        product_id, batch_id, movement_type,
        quantity, movement_date, reference_type,
        reference_id, notes
    ) VALUES (
        NEW.product_id, 
        NEW.batch_id,
        CASE 
            WHEN NEW.quantity_adjusted > 0 THEN 'adjustment_in'
            ELSE 'adjustment_out'
        END,
        ABS(NEW.quantity_adjusted),
        CURRENT_TIMESTAMP,
        'stock_adjustment',
        NEW.adjustment_id,
        NEW.adjustment_type || ': ' || NEW.reason
    );
    
    -- Log audit entry
    INSERT INTO audit_log (
        table_name, record_id, action, 
        changed_by, changed_at, details
    ) VALUES (
        'stock_adjustments', 
        NEW.adjustment_id, 
        'CREATE',
        NEW.adjusted_by,
        CURRENT_TIMESTAMP,
        jsonb_build_object(
            'product_id', NEW.product_id,
            'batch_id', NEW.batch_id,
            'adjustment_type', NEW.adjustment_type,
            'quantity_adjusted', NEW.quantity_adjusted,
            'reason', NEW.reason
        )
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_apply_stock_adjustment
    AFTER INSERT ON stock_adjustments
    FOR EACH ROW
    EXECUTE FUNCTION apply_stock_adjustment();

-- Auto-expire batches daily
CREATE OR REPLACE FUNCTION auto_expire_batches()
RETURNS void AS $$
DECLARE
    v_expired_batch RECORD;
    v_adjustment_id INTEGER;
BEGIN
    -- Find batches that expired today
    FOR v_expired_batch IN 
        SELECT b.*, p.product_name
        FROM batches b
        JOIN products p ON b.product_id = p.product_id
        WHERE b.expiry_date = CURRENT_DATE
        AND b.quantity_available > 0
        AND b.batch_status != 'expired'
    LOOP
        -- Create expiry adjustment
        INSERT INTO stock_adjustments (
            product_id, batch_id, adjustment_type,
            quantity_adjusted, old_quantity, new_quantity,
            reason, adjustment_date
        ) VALUES (
            v_expired_batch.product_id,
            v_expired_batch.batch_id,
            'expiry',
            -v_expired_batch.quantity_available,
            v_expired_batch.quantity_available,
            0,
            'Batch expired on ' || v_expired_batch.expiry_date,
            CURRENT_DATE
        ) RETURNING adjustment_id INTO v_adjustment_id;
        
        -- Update batch status
        UPDATE batches 
        SET batch_status = 'expired'
        WHERE batch_id = v_expired_batch.batch_id;
        
        -- Send notification
        INSERT INTO notifications (
            notification_type, severity, title, message,
            created_at
        ) VALUES (
            'batch_expired', 'high',
            'Batch Expired',
            'Batch ' || v_expired_batch.batch_number || ' of ' || 
            v_expired_batch.product_name || ' has expired. ' ||
            'Quantity: ' || v_expired_batch.quantity_available,
            CURRENT_TIMESTAMP
        );
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- TAX ENTRY TRIGGERS
-- =============================================

-- Auto-create tax entries when invoice is created
CREATE OR REPLACE FUNCTION create_tax_entries_on_invoice()
RETURNS TRIGGER AS $$
DECLARE
    v_invoice_item RECORD;
    v_is_interstate BOOLEAN;
    v_company_state_code TEXT;
    v_party_state_code TEXT;
BEGIN
    -- Get company and party state codes
    v_company_state_code := '27'; -- Maharashtra (configure as needed)
    
    IF NEW.invoice_type = 'sales' THEN
        SELECT state_code INTO v_party_state_code
        FROM customers WHERE customer_id = NEW.customer_id;
    ELSE
        SELECT state_code INTO v_party_state_code
        FROM suppliers WHERE supplier_id = NEW.supplier_id;
    END IF;
    
    v_is_interstate := (v_company_state_code != v_party_state_code);
    
    -- Create tax entries for each invoice item
    FOR v_invoice_item IN 
        SELECT ii.*, p.hsn_code, p.gst_percent
        FROM invoice_items ii
        JOIN products p ON ii.product_id = p.product_id
        WHERE ii.invoice_id = NEW.invoice_id
    LOOP
        INSERT INTO tax_entries (
            entry_type, reference_type, reference_id,
            party_id, party_type, entry_date,
            hsn_code, product_description,
            taxable_amount, cgst_rate, cgst_amount,
            sgst_rate, sgst_amount, igst_rate, igst_amount,
            total_tax_amount, invoice_number, invoice_date,
            is_interstate
        ) VALUES (
            NEW.invoice_type,
            'invoice',
            NEW.invoice_id,
            CASE 
                WHEN NEW.invoice_type = 'sales' THEN NEW.customer_id
                ELSE NEW.supplier_id
            END,
            NEW.invoice_type,
            NEW.invoice_date,
            v_invoice_item.hsn_code,
            v_invoice_item.product_name,
            v_invoice_item.taxable_amount,
            CASE WHEN v_is_interstate THEN 0 ELSE v_invoice_item.gst_percent / 2 END,
            v_invoice_item.cgst_amount,
            CASE WHEN v_is_interstate THEN 0 ELSE v_invoice_item.gst_percent / 2 END,
            v_invoice_item.sgst_amount,
            CASE WHEN v_is_interstate THEN v_invoice_item.gst_percent ELSE 0 END,
            v_invoice_item.igst_amount,
            v_invoice_item.total_tax,
            NEW.invoice_number,
            NEW.invoice_date,
            v_is_interstate
        );
    END LOOP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_tax_entries
    AFTER INSERT ON invoices
    FOR EACH ROW
    EXECUTE FUNCTION create_tax_entries_on_invoice();

-- Update tax entries when invoice is modified
CREATE OR REPLACE FUNCTION update_tax_entries_on_invoice_change()
RETURNS TRIGGER AS $$
BEGIN
    -- If invoice is cancelled, mark tax entries as cancelled
    IF NEW.status = 'cancelled' AND OLD.status != 'cancelled' THEN
        UPDATE tax_entries 
        SET 
            status = 'cancelled',
            notes = COALESCE(notes || ' | ', '') || 'Invoice cancelled on ' || CURRENT_DATE
        WHERE reference_type = 'invoice' 
        AND reference_id = NEW.invoice_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_tax_entries
    AFTER UPDATE OF status ON invoices
    FOR EACH ROW
    EXECUTE FUNCTION update_tax_entries_on_invoice_change();

-- Validate GST rates
CREATE OR REPLACE FUNCTION validate_gst_rate()
RETURNS TRIGGER AS $$
BEGIN
    -- Validate GST rate is standard
    IF NEW.cgst_rate + NEW.sgst_rate + NEW.igst_rate NOT IN (0, 5, 12, 18, 28) THEN
        RAISE WARNING 'Non-standard GST rate detected: %', 
                      (NEW.cgst_rate + NEW.sgst_rate + NEW.igst_rate);
    END IF;
    
    -- Ensure either CGST+SGST or IGST, not both
    IF NEW.igst_rate > 0 AND (NEW.cgst_rate > 0 OR NEW.sgst_rate > 0) THEN
        RAISE EXCEPTION 'Cannot have both IGST and CGST/SGST in same entry';
    END IF;
    
    -- Ensure CGST = SGST for intrastate
    IF NEW.cgst_rate != NEW.sgst_rate AND NEW.igst_rate = 0 THEN
        RAISE EXCEPTION 'CGST and SGST rates must be equal';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validate_gst_rate
    BEFORE INSERT OR UPDATE ON tax_entries
    FOR EACH ROW
    EXECUTE FUNCTION validate_gst_rate();

-- =============================================
-- AUDIT AND NOTIFICATION TRIGGERS
-- =============================================

-- Generic audit trigger for sensitive operations
CREATE OR REPLACE FUNCTION audit_sensitive_operation()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (
        table_name, record_id, action,
        old_data, new_data, changed_by,
        changed_at, ip_address
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.return_id, NEW.adjustment_id, NEW.entry_id),
        TG_OP,
        to_jsonb(OLD),
        to_jsonb(NEW),
        COALESCE(NEW.adjusted_by, NEW.approved_by, current_setting('app.current_user_id', true)::INTEGER),
        CURRENT_TIMESTAMP,
        inet_client_addr()
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger to sensitive tables
CREATE TRIGGER trigger_audit_sales_returns
    AFTER INSERT OR UPDATE OR DELETE ON sales_returns
    FOR EACH ROW
    EXECUTE FUNCTION audit_sensitive_operation();

CREATE TRIGGER trigger_audit_stock_adjustments
    AFTER INSERT OR UPDATE OR DELETE ON stock_adjustments
    FOR EACH ROW
    EXECUTE FUNCTION audit_sensitive_operation();

CREATE TRIGGER trigger_audit_tax_entries
    AFTER INSERT OR UPDATE OR DELETE ON tax_entries
    FOR EACH ROW
    EXECUTE FUNCTION audit_sensitive_operation();

-- =============================================
-- HELPER FUNCTIONS
-- =============================================

-- Get net tax position
CREATE OR REPLACE FUNCTION get_net_tax_position(
    p_start_date DATE,
    p_end_date DATE
) RETURNS TABLE (
    output_tax DECIMAL,
    input_tax DECIMAL,
    net_payable DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(CASE WHEN entry_type = 'sales' THEN total_tax_amount END), 0) as output_tax,
        COALESCE(SUM(CASE WHEN entry_type = 'purchase' THEN total_tax_amount END), 0) as input_tax,
        COALESCE(SUM(CASE WHEN entry_type = 'sales' THEN total_tax_amount ELSE -total_tax_amount END), 0) as net_payable
    FROM tax_entries
    WHERE entry_date >= p_start_date
    AND entry_date <= p_end_date
    AND status != 'cancelled';
END;
$$ LANGUAGE plpgsql;

-- Create sequences if not exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE schemaname = 'public' AND sequencename = 'credit_note_seq') THEN
        CREATE SEQUENCE credit_note_seq START 1;
    END IF;
END $$;