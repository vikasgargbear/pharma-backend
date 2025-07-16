-- =============================================
-- PHARMACEUTICAL ERP - ADDITIONAL TRIGGERS
-- =============================================
-- Version: 1.0 - Production Ready
-- Description: Additional triggers for complete schema
-- Deploy Order: 3b - After core triggers
-- =============================================

-- =============================================
-- FINANCIAL INTEGRATION TRIGGERS
-- =============================================

-- Queue payments for financial sync
CREATE TRIGGER trigger_queue_payment_financial_sync
    AFTER UPDATE OF payment_status ON payments
    FOR EACH ROW
    EXECUTE FUNCTION queue_payment_for_financial_sync();

-- =============================================
-- PURCHASE TRIGGERS
-- =============================================

-- Create batches when purchase is received
CREATE TRIGGER trigger_create_batches_from_purchase
    AFTER UPDATE OF purchase_status ON purchases
    FOR EACH ROW
    EXECUTE FUNCTION create_batches_from_purchase();

-- Update supplier outstanding on purchase
CREATE OR REPLACE FUNCTION create_supplier_outstanding_on_purchase()
RETURNS TRIGGER AS $$
BEGIN
    -- Create outstanding when purchase is received
    IF NEW.purchase_status = 'received' AND OLD.purchase_status != 'received' THEN
        INSERT INTO supplier_outstanding (
            org_id, supplier_id, purchase_id,
            invoice_number, invoice_date,
            total_amount, outstanding_amount,
            due_date, status
        ) VALUES (
            NEW.org_id, NEW.supplier_id, NEW.purchase_id,
            NEW.supplier_invoice_number, NEW.supplier_invoice_date,
            NEW.final_amount, NEW.final_amount - NEW.paid_amount,
            COALESCE(NEW.payment_due_date, NEW.purchase_date + INTERVAL '30 days'),
            'pending'
        )
        ON CONFLICT (purchase_id) DO UPDATE
        SET outstanding_amount = EXCLUDED.total_amount - NEW.paid_amount;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_supplier_outstanding_on_purchase
    AFTER UPDATE OF purchase_status ON purchases
    FOR EACH ROW
    EXECUTE FUNCTION create_supplier_outstanding_on_purchase();

-- =============================================
-- BARCODE TRIGGERS
-- =============================================

-- Auto-generate product barcode
CREATE OR REPLACE FUNCTION auto_generate_product_barcode()
RETURNS TRIGGER AS $$
BEGIN
    -- Generate barcode for new products without barcode
    IF NEW.barcode IS NULL AND TG_OP = 'INSERT' THEN
        NEW.barcode := generate_gtin(NEW.org_id, NEW.product_id);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_generate_product_barcode
    AFTER INSERT ON products
    FOR EACH ROW
    WHEN (NEW.barcode IS NULL)
    EXECUTE FUNCTION auto_generate_product_barcode();

-- =============================================
-- CUSTOMER METRICS TRIGGERS
-- =============================================

-- Update customer business metrics
CREATE OR REPLACE FUNCTION update_customer_metrics()
RETURNS TRIGGER AS $$
DECLARE
    v_total_business DECIMAL(15,2);
    v_last_order_date DATE;
    v_order_count INTEGER;
BEGIN
    -- Calculate metrics
    SELECT 
        COALESCE(SUM(final_amount), 0),
        MAX(order_date),
        COUNT(*)
    INTO v_total_business, v_last_order_date, v_order_count
    FROM orders
    WHERE customer_id = NEW.customer_id
    AND order_status IN ('delivered', 'invoiced');
    
    -- Update customer
    UPDATE customers
    SET 
        total_business = v_total_business,
        last_order_date = v_last_order_date,
        order_count = v_order_count,
        updated_at = CURRENT_TIMESTAMP
    WHERE customer_id = NEW.customer_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_customer_metrics
    AFTER INSERT OR UPDATE OF order_status ON orders
    FOR EACH ROW
    WHEN (NEW.order_status IN ('delivered', 'invoiced'))
    EXECUTE FUNCTION update_customer_metrics();

-- =============================================
-- SUPPLIER METRICS TRIGGERS
-- =============================================

-- Update supplier metrics
CREATE OR REPLACE FUNCTION update_supplier_metrics()
RETURNS TRIGGER AS $$
DECLARE
    v_total_purchases DECIMAL(15,2);
    v_last_purchase_date DATE;
BEGIN
    -- Calculate metrics
    SELECT 
        COALESCE(SUM(final_amount), 0),
        MAX(purchase_date)
    INTO v_total_purchases, v_last_purchase_date
    FROM purchases
    WHERE supplier_id = NEW.supplier_id
    AND purchase_status = 'received';
    
    -- Update supplier
    UPDATE suppliers
    SET 
        total_purchases = v_total_purchases,
        last_purchase_date = v_last_purchase_date,
        updated_at = CURRENT_TIMESTAMP
    WHERE supplier_id = NEW.supplier_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_supplier_metrics
    AFTER UPDATE OF purchase_status ON purchases
    FOR EACH ROW
    WHEN (NEW.purchase_status = 'received')
    EXECUTE FUNCTION update_supplier_metrics();

-- =============================================
-- EMAIL QUEUE TRIGGERS
-- =============================================

-- Queue email for near expiry batches
CREATE OR REPLACE FUNCTION queue_near_expiry_email()
RETURNS TRIGGER AS $$
DECLARE
    v_product_name TEXT;
    v_org_email TEXT;
BEGIN
    -- Only queue if just became near expiry
    IF NEW.is_near_expiry = TRUE AND (OLD.is_near_expiry = FALSE OR OLD.is_near_expiry IS NULL) THEN
        -- Get product name
        SELECT product_name INTO v_product_name
        FROM products WHERE product_id = NEW.product_id;
        
        -- Get organization email
        SELECT primary_email INTO v_org_email
        FROM organizations WHERE org_id = NEW.org_id;
        
        -- Queue email
        INSERT INTO email_queue (
            org_id, to_email, subject, body_html, priority
        ) VALUES (
            NEW.org_id,
            ARRAY[v_org_email],
            'Near Expiry Alert - ' || v_product_name,
            '<h3>Near Expiry Alert</h3>' ||
            '<p>Batch <strong>' || NEW.batch_number || '</strong> of <strong>' || v_product_name || '</strong> is nearing expiry.</p>' ||
            '<p>Expiry Date: ' || NEW.expiry_date || '</p>' ||
            '<p>Days Remaining: ' || NEW.days_to_expiry || '</p>' ||
            '<p>Quantity Available: ' || NEW.quantity_available || '</p>',
            3
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_queue_near_expiry_email
    AFTER UPDATE OF is_near_expiry ON batches
    FOR EACH ROW
    EXECUTE FUNCTION queue_near_expiry_email();

-- =============================================
-- SESSION MANAGEMENT TRIGGERS
-- =============================================

-- Auto-expire sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS TRIGGER AS $$
BEGIN
    -- Mark expired sessions as inactive
    UPDATE user_sessions
    SET is_active = FALSE,
        terminated_at = CURRENT_TIMESTAMP,
        termination_reason = 'expired'
    WHERE expires_at < CURRENT_TIMESTAMP
    AND is_active = TRUE;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- This trigger runs on any insert to check for expired sessions
CREATE TRIGGER trigger_cleanup_expired_sessions
    AFTER INSERT ON user_sessions
    FOR EACH STATEMENT
    EXECUTE FUNCTION cleanup_expired_sessions();

-- =============================================
-- ADDITIONAL TIMESTAMP TRIGGERS
-- =============================================

-- Add missing timestamp triggers
CREATE TRIGGER trigger_purchases_updated_at BEFORE UPDATE ON purchases FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_org_branches_updated_at BEFORE UPDATE ON org_branches FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_customer_outstanding_updated_at BEFORE UPDATE ON customer_outstanding FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_supplier_outstanding_updated_at BEFORE UPDATE ON supplier_outstanding FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- SUCCESS MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
ADDITIONAL TRIGGERS DEPLOYED SUCCESSFULLY
=============================================
✓ Financial Triggers
✓ Purchase Triggers
✓ Barcode Triggers
✓ Customer Metrics Triggers
✓ Supplier Metrics Triggers
✓ Email Queue Triggers
✓ Session Management Triggers
✓ Additional Timestamp Triggers

Next: Deploy 04_indexes_performance.sql
';
END $$;