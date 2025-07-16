-- =============================================
-- FINANCIAL MODULE - TRIGGERS & AUTOMATION
-- =============================================
-- Version: 1.0 - Standalone Financial System
-- Description: Financial automation and business rules
-- Deploy Order: 3rd - After functions
-- =============================================

-- =============================================
-- VOUCHER MANAGEMENT TRIGGERS
-- =============================================

-- Update voucher totals
CREATE OR REPLACE FUNCTION update_voucher_totals()
RETURNS TRIGGER AS $$
DECLARE
    v_total DECIMAL(15,2);
BEGIN
    -- Calculate total from entries
    SELECT SUM(GREATEST(debit_amount, credit_amount))
    INTO v_total
    FROM voucher_entries
    WHERE voucher_id = COALESCE(NEW.voucher_id, OLD.voucher_id);
    
    -- Update voucher
    UPDATE vouchers
    SET total_amount = v_total,
        updated_at = CURRENT_TIMESTAMP
    WHERE voucher_id = COALESCE(NEW.voucher_id, OLD.voucher_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_voucher_totals
    AFTER INSERT OR UPDATE OR DELETE ON voucher_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_voucher_totals();

-- Validate double entry
CREATE OR REPLACE FUNCTION validate_double_entry()
RETURNS TRIGGER AS $$
DECLARE
    v_debit_total DECIMAL(15,2);
    v_credit_total DECIMAL(15,2);
BEGIN
    -- Only validate when posting
    IF NEW.is_posted = TRUE AND (OLD.is_posted = FALSE OR OLD.is_posted IS NULL) THEN
        -- Check if debits equal credits
        SELECT 
            SUM(debit_amount),
            SUM(credit_amount)
        INTO v_debit_total, v_credit_total
        FROM voucher_entries
        WHERE voucher_id = NEW.voucher_id;
        
        IF v_debit_total != v_credit_total THEN
            RAISE EXCEPTION 'Double entry validation failed. Debit: %, Credit: %', 
                v_debit_total, v_credit_total;
        END IF;
        
        -- Must have at least 2 entries
        IF (SELECT COUNT(*) FROM voucher_entries WHERE voucher_id = NEW.voucher_id) < 2 THEN
            RAISE EXCEPTION 'Voucher must have at least 2 entries';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validate_double_entry
    BEFORE UPDATE OF is_posted ON vouchers
    FOR EACH ROW
    EXECUTE FUNCTION validate_double_entry();

-- =============================================
-- LEDGER BALANCE TRIGGERS
-- =============================================

-- Update ledger current balance
CREATE OR REPLACE FUNCTION update_ledger_balance()
RETURNS TRIGGER AS $$
DECLARE
    v_ledger RECORD;
    v_balance_data RECORD;
BEGIN
    -- Get affected ledger
    IF TG_OP = 'DELETE' THEN
        v_ledger.ledger_id := OLD.ledger_id;
    ELSE
        v_ledger.ledger_id := NEW.ledger_id;
    END IF;
    
    -- Only update if voucher is posted
    IF EXISTS (
        SELECT 1 FROM vouchers v 
        WHERE v.voucher_id = COALESCE(NEW.voucher_id, OLD.voucher_id)
        AND v.is_posted = TRUE
    ) THEN
        -- Get new balance
        SELECT * INTO v_balance_data
        FROM get_ledger_balance(v_ledger.ledger_id);
        
        -- Update ledger
        UPDATE ledgers
        SET current_balance = v_balance_data.closing_balance,
            balance_type = v_balance_data.balance_type,
            updated_at = CURRENT_TIMESTAMP
        WHERE ledger_id = v_ledger.ledger_id;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_ledger_balance
    AFTER INSERT OR UPDATE OR DELETE ON voucher_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_ledger_balance();

-- =============================================
-- FINANCIAL YEAR TRIGGERS
-- =============================================

-- Ensure only one current financial year
CREATE OR REPLACE FUNCTION ensure_single_current_year()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_current = TRUE THEN
        -- Set all other years as not current
        UPDATE financial_years
        SET is_current = FALSE
        WHERE company_id = NEW.company_id
        AND year_id != NEW.year_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_ensure_single_current_year
    BEFORE INSERT OR UPDATE OF is_current ON financial_years
    FOR EACH ROW
    EXECUTE FUNCTION ensure_single_current_year();

-- Prevent changes to closed year
CREATE OR REPLACE FUNCTION prevent_closed_year_changes()
RETURNS TRIGGER AS $$
DECLARE
    v_year_closed BOOLEAN;
BEGIN
    -- Check if financial year is closed
    SELECT fy.is_closed INTO v_year_closed
    FROM financial_years fy
    WHERE fy.company_id = NEW.company_id
    AND NEW.voucher_date BETWEEN fy.start_date AND fy.end_date;
    
    IF v_year_closed = TRUE THEN
        RAISE EXCEPTION 'Cannot create/modify vouchers in closed financial year';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_prevent_closed_year_changes
    BEFORE INSERT OR UPDATE ON vouchers
    FOR EACH ROW
    EXECUTE FUNCTION prevent_closed_year_changes();

-- =============================================
-- BILL-WISE TRACKING TRIGGERS
-- =============================================

-- Auto-create bills for credit transactions
CREATE OR REPLACE FUNCTION auto_create_bills()
RETURNS TRIGGER AS $$
DECLARE
    v_ledger RECORD;
BEGIN
    -- Only for posted vouchers
    IF NEW.is_posted = TRUE AND (OLD.is_posted = FALSE OR OLD.is_posted IS NULL) THEN
        -- Check each entry for billwise tracking
        FOR v_ledger IN 
            SELECT ve.*, l.maintain_billwise
            FROM voucher_entries ve
            JOIN ledgers l ON ve.ledger_id = l.ledger_id
            WHERE ve.voucher_id = NEW.voucher_id
            AND l.maintain_billwise = TRUE
        LOOP
            -- Create bill for credit entries (parties)
            IF v_ledger.credit_amount > 0 THEN
                INSERT INTO bill_details (
                    company_id, ledger_id, bill_number, bill_date,
                    bill_amount, outstanding_amount, voucher_id,
                    due_date
                ) VALUES (
                    NEW.company_id, v_ledger.ledger_id, NEW.voucher_number,
                    NEW.voucher_date, v_ledger.credit_amount, v_ledger.credit_amount,
                    NEW.voucher_id,
                    NEW.voucher_date + INTERVAL '30 days'
                );
            END IF;
        END LOOP;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_create_bills
    AFTER UPDATE OF is_posted ON vouchers
    FOR EACH ROW
    EXECUTE FUNCTION auto_create_bills();

-- =============================================
-- SYNC MANAGEMENT TRIGGERS
-- =============================================

-- Process ERP sync queue
CREATE OR REPLACE FUNCTION process_erp_sync()
RETURNS TRIGGER AS $$
BEGIN
    -- Create voucher based on sync type
    IF NEW.sync_status = 'processing' AND OLD.sync_status = 'pending' THEN
        BEGIN
            -- Call appropriate function based on type
            PERFORM create_voucher_from_erp_sync(NEW.sync_data);
            
            -- Mark as completed
            NEW.sync_status := 'completed';
            NEW.completed_at := CURRENT_TIMESTAMP;
            
        EXCEPTION WHEN OTHERS THEN
            -- Mark as failed
            NEW.sync_status := 'failed';
            NEW.error_message := SQLERRM;
            NEW.retry_count := NEW.retry_count + 1;
        END;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_process_erp_sync
    BEFORE UPDATE OF sync_status ON erp_sync_queue
    FOR EACH ROW
    EXECUTE FUNCTION process_erp_sync();

-- =============================================
-- AUDIT TRIGGERS
-- =============================================

-- Audit voucher changes
CREATE OR REPLACE FUNCTION audit_voucher_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        -- Log significant changes
        IF OLD.is_posted != NEW.is_posted OR OLD.is_cancelled != NEW.is_cancelled THEN
            INSERT INTO audit_log (
                company_id, table_name, record_id, action,
                old_values, new_values, user_id, created_at
            ) VALUES (
                NEW.company_id, 'vouchers', NEW.voucher_id::TEXT, TG_OP,
                jsonb_build_object(
                    'is_posted', OLD.is_posted,
                    'is_cancelled', OLD.is_cancelled,
                    'total_amount', OLD.total_amount
                ),
                jsonb_build_object(
                    'is_posted', NEW.is_posted,
                    'is_cancelled', NEW.is_cancelled,
                    'total_amount', NEW.total_amount
                ),
                current_setting('app.current_user_id', true)::INTEGER,
                CURRENT_TIMESTAMP
            );
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_audit_voucher_changes
    AFTER UPDATE ON vouchers
    FOR EACH ROW
    EXECUTE FUNCTION audit_voucher_changes();

-- =============================================
-- GST COMPLIANCE TRIGGERS
-- =============================================

-- Auto-calculate GST on voucher entries
CREATE OR REPLACE FUNCTION auto_calculate_gst()
RETURNS TRIGGER AS $$
DECLARE
    v_gst_rate DECIMAL(5,2);
    v_supply_type TEXT;
    v_gst_breakup RECORD;
BEGIN
    -- Only for GST applicable ledgers
    IF EXISTS (
        SELECT 1 FROM ledgers l
        WHERE l.ledger_id = NEW.ledger_id
        AND l.tax_type = 'GST'
    ) THEN
        -- Get GST rate and determine supply type
        -- This is simplified - implement based on your requirements
        v_gst_rate := 18; -- Default rate
        v_supply_type := 'intra_state'; -- Default
        
        -- Calculate GST
        SELECT * INTO v_gst_breakup
        FROM calculate_gst_breakup(
            GREATEST(NEW.debit_amount, NEW.credit_amount),
            v_gst_rate,
            v_supply_type
        );
        
        -- Store GST details in JSON
        NEW.gst_details := jsonb_build_object(
            'taxable_amount', v_gst_breakup.taxable_amount,
            'cgst_amount', v_gst_breakup.cgst_amount,
            'sgst_amount', v_gst_breakup.sgst_amount,
            'igst_amount', v_gst_breakup.igst_amount,
            'gst_rate', v_gst_rate
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add GST details column if not exists
ALTER TABLE voucher_entries ADD COLUMN IF NOT EXISTS gst_details JSONB;

CREATE TRIGGER trigger_auto_calculate_gst
    BEFORE INSERT OR UPDATE ON voucher_entries
    FOR EACH ROW
    EXECUTE FUNCTION auto_calculate_gst();

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
CREATE TRIGGER trigger_companies_updated_at BEFORE UPDATE ON companies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_ledgers_updated_at BEFORE UPDATE ON ledgers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_vouchers_updated_at BEFORE UPDATE ON vouchers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_bill_details_updated_at BEFORE UPDATE ON bill_details FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- SUCCESS MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
FINANCIAL TRIGGERS DEPLOYED SUCCESSFULLY
=============================================
✓ Voucher Management Triggers
✓ Double Entry Validation
✓ Ledger Balance Updates
✓ Financial Year Controls
✓ Bill-wise Tracking
✓ ERP Sync Processing
✓ Audit Logging
✓ GST Automation
✓ Timestamp Updates

Next: Deploy 04_financial_indexes.sql
';
END $$;