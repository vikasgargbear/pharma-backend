-- =============================================
-- FINANCIAL MODULE - BUSINESS FUNCTIONS
-- =============================================
-- Version: 1.0 - Standalone Financial System
-- Description: Core financial business logic
-- Deploy Order: 2nd - After core schema
-- =============================================

-- =============================================
-- UTILITY FUNCTIONS
-- =============================================

-- Get current company ID
CREATE OR REPLACE FUNCTION current_company_id() RETURNS UUID AS $$
    SELECT COALESCE(current_setting('app.current_company_id', true), '00000000-0000-0000-0000-000000000000')::UUID;
$$ LANGUAGE SQL STABLE;

-- Get current financial year
CREATE OR REPLACE FUNCTION current_financial_year_id() RETURNS INTEGER AS $$
    SELECT year_id FROM financial_years 
    WHERE company_id = current_company_id() 
    AND is_current = TRUE 
    LIMIT 1;
$$ LANGUAGE SQL STABLE;

-- =============================================
-- LEDGER MANAGEMENT FUNCTIONS
-- =============================================

-- Get ledger balance
CREATE OR REPLACE FUNCTION get_ledger_balance(
    p_ledger_id INTEGER,
    p_as_of_date DATE DEFAULT CURRENT_DATE
) RETURNS TABLE (
    debit_balance DECIMAL(15,2),
    credit_balance DECIMAL(15,2),
    closing_balance DECIMAL(15,2),
    balance_type TEXT
) AS $$
DECLARE
    v_opening_balance DECIMAL(15,2);
    v_opening_type TEXT;
    v_debit_total DECIMAL(15,2);
    v_credit_total DECIMAL(15,2);
    v_closing DECIMAL(15,2);
    v_type TEXT;
BEGIN
    -- Get opening balance
    SELECT opening_balance, opening_balance_type
    INTO v_opening_balance, v_opening_type
    FROM ledgers
    WHERE ledger_id = p_ledger_id;
    
    -- Get transaction totals
    SELECT 
        COALESCE(SUM(debit_amount), 0),
        COALESCE(SUM(credit_amount), 0)
    INTO v_debit_total, v_credit_total
    FROM voucher_entries ve
    JOIN vouchers v ON v.voucher_id = ve.voucher_id
    WHERE ve.ledger_id = p_ledger_id
    AND v.voucher_date <= p_as_of_date
    AND v.is_cancelled = FALSE;
    
    -- Calculate closing balance
    IF v_opening_type = 'Dr' THEN
        v_closing := v_opening_balance + v_debit_total - v_credit_total;
    ELSE
        v_closing := v_opening_balance + v_credit_total - v_debit_total;
    END IF;
    
    -- Determine balance type
    IF v_closing >= 0 THEN
        v_type := v_opening_type;
    ELSE
        v_type := CASE WHEN v_opening_type = 'Dr' THEN 'Cr' ELSE 'Dr' END;
        v_closing := ABS(v_closing);
    END IF;
    
    RETURN QUERY
    SELECT v_debit_total, v_credit_total, v_closing, v_type;
END;
$$ LANGUAGE plpgsql;

-- Create ledger from ERP sync
CREATE OR REPLACE FUNCTION create_ledger_from_erp(
    p_company_id UUID,
    p_ledger_name TEXT,
    p_group_name TEXT,
    p_external_ref_type TEXT,
    p_external_ref_id TEXT
) RETURNS INTEGER AS $$
DECLARE
    v_ledger_id INTEGER;
    v_group_id INTEGER;
BEGIN
    -- Get appropriate group
    SELECT group_id INTO v_group_id
    FROM ledger_groups
    WHERE company_id = p_company_id
    AND group_name = CASE 
        WHEN p_external_ref_type = 'customer' THEN 'Sundry Debtors'
        WHEN p_external_ref_type = 'supplier' THEN 'Sundry Creditors'
        ELSE 'Current Assets'
    END;
    
    -- Create ledger
    INSERT INTO ledgers (
        company_id, ledger_name, group_id,
        external_ref_type, external_ref_id,
        maintain_billwise
    ) VALUES (
        p_company_id, p_ledger_name, v_group_id,
        p_external_ref_type, p_external_ref_id,
        TRUE
    )
    ON CONFLICT (company_id, ledger_name) 
    DO UPDATE SET external_ref_id = EXCLUDED.external_ref_id
    RETURNING ledger_id INTO v_ledger_id;
    
    RETURN v_ledger_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- VOUCHER MANAGEMENT FUNCTIONS
-- =============================================

-- Get next voucher number
CREATE OR REPLACE FUNCTION get_next_voucher_number(
    p_voucher_type_id INTEGER
) RETURNS TEXT AS $$
DECLARE
    v_voucher_type RECORD;
    v_number TEXT;
BEGIN
    -- Get voucher type details
    SELECT * INTO v_voucher_type
    FROM voucher_types
    WHERE voucher_type_id = p_voucher_type_id
    FOR UPDATE;
    
    -- Generate number
    v_number := COALESCE(v_voucher_type.prefix, '') || 
                LPAD(v_voucher_type.current_number::TEXT, 6, '0') ||
                COALESCE(v_voucher_type.suffix, '');
    
    -- Update current number
    UPDATE voucher_types
    SET current_number = current_number + 1
    WHERE voucher_type_id = p_voucher_type_id;
    
    RETURN v_number;
END;
$$ LANGUAGE plpgsql;

-- Create voucher from ERP sync
CREATE OR REPLACE FUNCTION create_voucher_from_erp_sync(
    p_sync_data JSONB
) RETURNS INTEGER AS $$
DECLARE
    v_company_id UUID;
    v_voucher_id INTEGER;
    v_voucher_type_id INTEGER;
    v_voucher_number TEXT;
    v_ledger_id INTEGER;
    v_party_ledger_id INTEGER;
BEGIN
    -- Extract company ID
    v_company_id := (p_sync_data->>'company_id')::UUID;
    
    -- Determine voucher type
    SELECT voucher_type_id INTO v_voucher_type_id
    FROM voucher_types
    WHERE company_id = v_company_id
    AND voucher_class = CASE 
        WHEN p_sync_data->>'sync_type' = 'order' THEN 'Sales'
        WHEN p_sync_data->>'sync_type' = 'purchase' THEN 'Purchase'
        WHEN p_sync_data->>'sync_type' = 'payment' AND p_sync_data->>'payment_type' = 'receipt' THEN 'Receipt'
        WHEN p_sync_data->>'sync_type' = 'payment' AND p_sync_data->>'payment_type' = 'payment' THEN 'Payment'
    END
    AND is_default = TRUE;
    
    -- Get voucher number
    v_voucher_number := get_next_voucher_number(v_voucher_type_id);
    
    -- Create main voucher
    INSERT INTO vouchers (
        company_id, voucher_number, voucher_date,
        voucher_type_id, reference_number,
        narration, total_amount
    ) VALUES (
        v_company_id,
        v_voucher_number,
        (p_sync_data->>'transaction_date')::DATE,
        v_voucher_type_id,
        p_sync_data->>'reference_number',
        p_sync_data->>'narration',
        (p_sync_data->>'amount')::DECIMAL
    ) RETURNING voucher_id INTO v_voucher_id;
    
    -- Create entries based on type
    IF p_sync_data->>'sync_type' = 'order' THEN
        -- Sales voucher entries
        -- Dr: Customer/Cash
        -- Cr: Sales Account
        NULL; -- Implement based on your chart of accounts
        
    ELSIF p_sync_data->>'sync_type' = 'payment' THEN
        -- Payment/Receipt entries
        -- Implement based on payment type
        NULL;
    END IF;
    
    RETURN v_voucher_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- BILL-WISE TRACKING
-- =============================================

-- Allocate payment to bills (FIFO)
CREATE OR REPLACE FUNCTION allocate_payment_to_bills(
    p_ledger_id INTEGER,
    p_payment_amount DECIMAL(15,2),
    p_voucher_id INTEGER
) RETURNS VOID AS $$
DECLARE
    v_bill RECORD;
    v_remaining_amount DECIMAL(15,2);
    v_allocation_amount DECIMAL(15,2);
BEGIN
    v_remaining_amount := p_payment_amount;
    
    -- Process bills in FIFO order
    FOR v_bill IN 
        SELECT * FROM bill_details
        WHERE ledger_id = p_ledger_id
        AND status IN ('Outstanding', 'Partial')
        ORDER BY bill_date, bill_id
        FOR UPDATE
    LOOP
        EXIT WHEN v_remaining_amount <= 0;
        
        -- Calculate allocation amount
        v_allocation_amount := LEAST(v_remaining_amount, v_bill.outstanding_amount);
        
        -- Update bill
        UPDATE bill_details
        SET paid_amount = paid_amount + v_allocation_amount,
            outstanding_amount = outstanding_amount - v_allocation_amount,
            status = CASE 
                WHEN outstanding_amount - v_allocation_amount <= 0 THEN 'Paid'
                ELSE 'Partial'
            END,
            updated_at = CURRENT_TIMESTAMP
        WHERE bill_id = v_bill.bill_id;
        
        -- Reduce remaining amount
        v_remaining_amount := v_remaining_amount - v_allocation_amount;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- GST FUNCTIONS
-- =============================================

-- Calculate GST breakup
CREATE OR REPLACE FUNCTION calculate_gst_breakup(
    p_amount DECIMAL(15,2),
    p_gst_rate DECIMAL(5,2),
    p_supply_type TEXT -- 'inter_state' or 'intra_state'
) RETURNS TABLE (
    taxable_amount DECIMAL(15,2),
    cgst_amount DECIMAL(15,2),
    sgst_amount DECIMAL(15,2),
    igst_amount DECIMAL(15,2),
    total_amount DECIMAL(15,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p_amount as taxable_amount,
        CASE WHEN p_supply_type = 'intra_state' THEN ROUND(p_amount * p_gst_rate / 200, 2) ELSE 0 END as cgst_amount,
        CASE WHEN p_supply_type = 'intra_state' THEN ROUND(p_amount * p_gst_rate / 200, 2) ELSE 0 END as sgst_amount,
        CASE WHEN p_supply_type = 'inter_state' THEN ROUND(p_amount * p_gst_rate / 100, 2) ELSE 0 END as igst_amount,
        p_amount + ROUND(p_amount * p_gst_rate / 100, 2) as total_amount;
END;
$$ LANGUAGE plpgsql;

-- Generate GSTR-1 data
CREATE OR REPLACE FUNCTION generate_gstr1_data(
    p_company_id UUID,
    p_return_period TEXT -- 'MM-YYYY'
) RETURNS VOID AS $$
DECLARE
    v_month INTEGER;
    v_year INTEGER;
    v_start_date DATE;
    v_end_date DATE;
BEGIN
    -- Parse period
    v_month := SUBSTRING(p_return_period FROM 1 FOR 2)::INTEGER;
    v_year := SUBSTRING(p_return_period FROM 4 FOR 4)::INTEGER;
    v_start_date := (v_year || '-' || v_month || '-01')::DATE;
    v_end_date := (v_start_date + INTERVAL '1 month' - INTERVAL '1 day')::DATE;
    
    -- Delete existing data
    DELETE FROM gstr1_data 
    WHERE company_id = p_company_id 
    AND return_period = p_return_period;
    
    -- Insert new data
    INSERT INTO gstr1_data (
        company_id, return_period,
        b2b_supplies, b2b_count, b2b_taxable_value
        -- Add other fields
    )
    SELECT 
        p_company_id,
        p_return_period,
        jsonb_agg(b2b_data),
        COUNT(*),
        SUM(taxable_value)
    FROM (
        -- B2B supplies query
        SELECT 
            jsonb_build_object(
                'gstin', l.gst_registration_type,
                'invoice_number', v.voucher_number,
                'invoice_date', v.voucher_date,
                'taxable_value', SUM(ve.debit_amount)
            ) as b2b_data,
            SUM(ve.debit_amount) as taxable_value
        FROM vouchers v
        JOIN voucher_entries ve ON v.voucher_id = ve.voucher_id
        JOIN ledgers l ON ve.ledger_id = l.ledger_id
        WHERE v.company_id = p_company_id
        AND v.voucher_date BETWEEN v_start_date AND v_end_date
        AND l.gst_registration_type IS NOT NULL
        GROUP BY l.gst_registration_type, v.voucher_number, v.voucher_date
    ) b2b;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- FINANCIAL REPORTS
-- =============================================

-- Generate Trial Balance
CREATE OR REPLACE FUNCTION generate_trial_balance(
    p_company_id UUID,
    p_as_of_date DATE DEFAULT CURRENT_DATE
) RETURNS TABLE (
    group_name TEXT,
    ledger_name TEXT,
    debit_amount DECIMAL(15,2),
    credit_amount DECIMAL(15,2)
) AS $$
BEGIN
    RETURN QUERY
    WITH ledger_balances AS (
        SELECT 
            l.ledger_id,
            l.ledger_name,
            lg.group_name,
            lb.closing_balance,
            lb.balance_type
        FROM ledgers l
        JOIN ledger_groups lg ON l.group_id = lg.group_id
        CROSS JOIN LATERAL get_ledger_balance(l.ledger_id, p_as_of_date) lb
        WHERE l.company_id = p_company_id
    )
    SELECT 
        group_name,
        ledger_name,
        CASE WHEN balance_type = 'Dr' THEN closing_balance ELSE 0 END as debit_amount,
        CASE WHEN balance_type = 'Cr' THEN closing_balance ELSE 0 END as credit_amount
    FROM ledger_balances
    WHERE closing_balance > 0
    ORDER BY group_name, ledger_name;
END;
$$ LANGUAGE plpgsql;

-- Calculate financial ratios
CREATE OR REPLACE FUNCTION calculate_financial_ratios(
    p_company_id UUID,
    p_period_date DATE
) RETURNS VOID AS $$
DECLARE
    v_current_assets DECIMAL(15,2);
    v_current_liabilities DECIMAL(15,2);
    v_total_assets DECIMAL(15,2);
    v_total_liabilities DECIMAL(15,2);
    v_total_equity DECIMAL(15,2);
    v_net_profit DECIMAL(15,2);
    v_gross_profit DECIMAL(15,2);
    v_revenue DECIMAL(15,2);
BEGIN
    -- Get balance sheet figures
    -- This is simplified - in production, you'd calculate from ledger balances
    
    -- Insert/Update ratios
    INSERT INTO financial_ratios (
        company_id, period_type, period_date,
        current_ratio, quick_ratio,
        gross_profit_margin, net_profit_margin,
        debt_ratio, debt_equity_ratio
    ) VALUES (
        p_company_id, 'Monthly', p_period_date,
        v_current_assets / NULLIF(v_current_liabilities, 0),
        (v_current_assets - 0) / NULLIF(v_current_liabilities, 0), -- Subtract inventory
        v_gross_profit / NULLIF(v_revenue, 0) * 100,
        v_net_profit / NULLIF(v_revenue, 0) * 100,
        v_total_liabilities / NULLIF(v_total_assets, 0),
        v_total_liabilities / NULLIF(v_total_equity, 0)
    )
    ON CONFLICT (company_id, period_type, period_date)
    DO UPDATE SET
        current_ratio = EXCLUDED.current_ratio,
        quick_ratio = EXCLUDED.quick_ratio,
        gross_profit_margin = EXCLUDED.gross_profit_margin,
        net_profit_margin = EXCLUDED.net_profit_margin,
        debt_ratio = EXCLUDED.debt_ratio,
        debt_equity_ratio = EXCLUDED.debt_equity_ratio;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- SUCCESS MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
FINANCIAL FUNCTIONS DEPLOYED SUCCESSFULLY
=============================================
✓ Utility Functions
✓ Ledger Management
✓ Voucher Management
✓ Bill-wise Tracking
✓ GST Functions
✓ Financial Reports
✓ Trial Balance
✓ Financial Ratios

Next: Deploy 03_financial_triggers.sql
';
END $$;