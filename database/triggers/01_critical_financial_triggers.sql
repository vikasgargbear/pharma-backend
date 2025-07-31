-- =============================================
-- CRITICAL FINANCIAL TRIGGERS
-- =============================================
-- Priority: HIGHEST - Financial integrity is paramount
-- Deploy Order: First - These protect money
-- =============================================

-- =============================================
-- 1. DOUBLE-ENTRY VALIDATION TRIGGER
-- =============================================
-- Ensures every journal entry balances (Debits = Credits)
CREATE OR REPLACE FUNCTION validate_double_entry()
RETURNS TRIGGER AS $$
DECLARE
    v_total_debit NUMERIC;
    v_total_credit NUMERIC;
    v_difference NUMERIC;
BEGIN
    -- Calculate totals for this journal entry
    SELECT 
        COALESCE(SUM(debit_amount), 0),
        COALESCE(SUM(credit_amount), 0)
    INTO v_total_debit, v_total_credit
    FROM financial.journal_entry_lines
    WHERE journal_entry_id = NEW.journal_entry_id;
    
    -- Add current line
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        v_total_debit := v_total_debit + COALESCE(NEW.debit_amount, 0);
        v_total_credit := v_total_credit + COALESCE(NEW.credit_amount, 0);
    END IF;
    
    -- For updates, subtract old values
    IF TG_OP = 'UPDATE' THEN
        v_total_debit := v_total_debit - COALESCE(OLD.debit_amount, 0);
        v_total_credit := v_total_credit - COALESCE(OLD.credit_amount, 0);
    END IF;
    
    -- Check balance
    v_difference := ABS(v_total_debit - v_total_credit);
    
    -- Allow small rounding differences (0.01)
    IF v_difference > 0.01 THEN
        RAISE EXCEPTION 'Journal entry does not balance. Debit: %, Credit: %, Difference: %', 
            v_total_debit, v_total_credit, v_difference;
    END IF;
    
    -- Update the journal entry header
    UPDATE financial.journal_entries
    SET 
        total_debit = v_total_debit,
        total_credit = v_total_credit,
        updated_at = CURRENT_TIMESTAMP
    WHERE journal_entry_id = NEW.journal_entry_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to journal entry lines
CREATE TRIGGER trigger_validate_double_entry
    AFTER INSERT OR UPDATE OR DELETE ON financial.journal_entry_lines
    FOR EACH ROW
    EXECUTE FUNCTION validate_double_entry();

-- =============================================
-- 2. PAYMENT ALLOCATION CASCADE TRIGGER
-- =============================================
-- Automatically updates outstanding amounts when payments are allocated
CREATE OR REPLACE FUNCTION cascade_payment_allocation()
RETURNS TRIGGER AS $$
DECLARE
    v_invoice_total NUMERIC;
    v_allocated_total NUMERIC;
    v_outstanding NUMERIC;
BEGIN
    IF NEW.reference_type = 'sales_invoice' THEN
        -- Get invoice total
        SELECT final_amount 
        INTO v_invoice_total
        FROM sales.invoices
        WHERE invoice_id = NEW.reference_id;
        
        -- Calculate total allocated to this invoice
        SELECT COALESCE(SUM(allocated_amount), 0)
        INTO v_allocated_total
        FROM financial.payment_allocations
        WHERE reference_type = 'sales_invoice'
        AND reference_id = NEW.reference_id
        AND allocation_status = 'active';
        
        -- Update outstanding
        v_outstanding := v_invoice_total - v_allocated_total;
        
        -- Update customer outstanding
        UPDATE financial.customer_outstanding
        SET 
            paid_amount = v_allocated_total,
            outstanding_amount = v_outstanding,
            status = CASE 
                WHEN v_outstanding <= 0 THEN 'paid'
                WHEN v_outstanding < v_invoice_total THEN 'partial'
                ELSE 'open'
            END,
            updated_at = CURRENT_TIMESTAMP
        WHERE transaction_type = 'invoice'
        AND transaction_id = NEW.reference_id;
        
        -- Update invoice payment status
        UPDATE sales.invoices
        SET 
            paid_amount = v_allocated_total,
            payment_status = CASE 
                WHEN v_outstanding <= 0 THEN 'paid'
                WHEN v_outstanding < v_invoice_total THEN 'partial'
                ELSE 'unpaid'
            END,
            updated_at = CURRENT_TIMESTAMP
        WHERE invoice_id = NEW.reference_id;
        
    ELSIF NEW.reference_type = 'purchase_invoice' THEN
        -- Similar logic for purchase invoices
        -- ... (implement similar pattern)
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_cascade_payment_allocation
    AFTER INSERT OR UPDATE ON financial.payment_allocations
    FOR EACH ROW
    EXECUTE FUNCTION cascade_payment_allocation();

-- =============================================
-- 3. CREDIT LIMIT ENFORCEMENT TRIGGER
-- =============================================
-- Prevents orders that exceed customer credit limit
CREATE OR REPLACE FUNCTION enforce_credit_limit()
RETURNS TRIGGER AS $$
DECLARE
    v_credit_limit NUMERIC;
    v_current_outstanding NUMERIC;
    v_order_value NUMERIC;
    v_total_exposure NUMERIC;
    v_customer_name TEXT;
BEGIN
    -- Skip if order is not confirmed
    IF NEW.order_status NOT IN ('confirmed', 'processing') THEN
        RETURN NEW;
    END IF;
    
    -- Get customer credit limit and name
    SELECT 
        COALESCE(credit_limit, 0),
        customer_name
    INTO v_credit_limit, v_customer_name
    FROM parties.customers
    WHERE customer_id = NEW.customer_id;
    
    -- If no credit limit set, allow (0 means no limit)
    IF v_credit_limit = 0 THEN
        RETURN NEW;
    END IF;
    
    -- Calculate current outstanding
    SELECT COALESCE(SUM(outstanding_amount), 0)
    INTO v_current_outstanding
    FROM financial.customer_outstanding
    WHERE customer_id = NEW.customer_id
    AND status IN ('open', 'partial');
    
    -- Get order value
    v_order_value := NEW.final_amount;
    
    -- Calculate total exposure
    v_total_exposure := v_current_outstanding + v_order_value;
    
    -- Check credit limit
    IF v_total_exposure > v_credit_limit THEN
        RAISE EXCEPTION 'Credit limit exceeded for customer %. Limit: %, Current Outstanding: %, Order Value: %, Total: %',
            v_customer_name, v_credit_limit, v_current_outstanding, v_order_value, v_total_exposure;
    END IF;
    
    -- Log credit check
    INSERT INTO audit.credit_checks (
        customer_id,
        order_id,
        credit_limit,
        outstanding_amount,
        order_amount,
        total_exposure,
        check_result,
        checked_at
    ) VALUES (
        NEW.customer_id,
        NEW.order_id,
        v_credit_limit,
        v_current_outstanding,
        v_order_value,
        v_total_exposure,
        'approved',
        CURRENT_TIMESTAMP
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_enforce_credit_limit
    BEFORE UPDATE OF order_status ON sales.orders
    FOR EACH ROW
    WHEN (NEW.order_status IN ('confirmed', 'processing'))
    EXECUTE FUNCTION enforce_credit_limit();

-- =============================================
-- 4. CUSTOMER OUTSTANDING AGING TRIGGER
-- =============================================
-- Automatically updates aging buckets for receivables
CREATE OR REPLACE FUNCTION update_outstanding_aging()
RETURNS TRIGGER AS $$
DECLARE
    v_days_overdue INTEGER;
BEGIN
    -- Calculate days overdue
    v_days_overdue := GREATEST(0, (CURRENT_DATE - NEW.due_date)::INTEGER);
    
    NEW.days_overdue := v_days_overdue;
    
    -- Set aging bucket
    NEW.aging_bucket := CASE
        WHEN v_days_overdue = 0 THEN 'current'
        WHEN v_days_overdue BETWEEN 1 AND 30 THEN '1-30'
        WHEN v_days_overdue BETWEEN 31 AND 60 THEN '31-60'
        WHEN v_days_overdue BETWEEN 61 AND 90 THEN '61-90'
        WHEN v_days_overdue BETWEEN 91 AND 120 THEN '91-120'
        ELSE '120+'
    END;
    
    -- Set collection priority based on amount and age
    IF v_days_overdue > 90 OR NEW.outstanding_amount > 100000 THEN
        NEW.collection_priority := 'urgent';
    ELSIF v_days_overdue > 60 OR NEW.outstanding_amount > 50000 THEN
        NEW.collection_priority := 'high';
    ELSIF v_days_overdue > 30 OR NEW.outstanding_amount > 25000 THEN
        NEW.collection_priority := 'normal';
    ELSE
        NEW.collection_priority := 'low';
    END IF;
    
    -- Set next follow-up date if not already set
    IF NEW.next_followup_date IS NULL AND NEW.status IN ('open', 'partial') THEN
        NEW.next_followup_date := CASE
            WHEN NEW.collection_priority = 'urgent' THEN CURRENT_DATE + INTERVAL '1 day'
            WHEN NEW.collection_priority = 'high' THEN CURRENT_DATE + INTERVAL '3 days'
            WHEN NEW.collection_priority = 'normal' THEN CURRENT_DATE + INTERVAL '7 days'
            ELSE CURRENT_DATE + INTERVAL '14 days'
        END;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_outstanding_aging
    BEFORE INSERT OR UPDATE ON financial.customer_outstanding
    FOR EACH ROW
    EXECUTE FUNCTION update_outstanding_aging();

-- =============================================
-- 5. PERIOD CLOSING ENFORCEMENT TRIGGER
-- =============================================
-- Prevents posting to closed financial periods
CREATE OR REPLACE FUNCTION enforce_period_closing()
RETURNS TRIGGER AS $$
DECLARE
    v_period_status TEXT;
    v_period_name TEXT;
BEGIN
    -- Check if the period is closed
    SELECT 
        period_status,
        period_name
    INTO v_period_status, v_period_name
    FROM financial.financial_periods
    WHERE org_id = NEW.org_id
    AND NEW.entry_date BETWEEN start_date AND end_date
    LIMIT 1;
    
    -- If no period found, it might be a future date
    IF v_period_status IS NULL THEN
        RAISE EXCEPTION 'No financial period defined for date %', NEW.entry_date;
    END IF;
    
    -- Check if period is closed
    IF v_period_status IN ('closed', 'locked') THEN
        RAISE EXCEPTION 'Cannot post to closed period %. Period status: %', 
            v_period_name, v_period_status;
    END IF;
    
    -- Additional check for backdated entries
    IF NEW.entry_date < CURRENT_DATE - INTERVAL '7 days' THEN
        -- Log backdated entry for audit
        INSERT INTO audit.backdated_entries (
            entry_type,
            entry_id,
            entry_date,
            current_date,
            days_backdated,
            user_id,
            created_at
        ) VALUES (
            'journal_entry',
            NEW.journal_entry_id,
            NEW.entry_date,
            CURRENT_DATE,
            (CURRENT_DATE - NEW.entry_date)::INTEGER,
            NEW.created_by,
            CURRENT_TIMESTAMP
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_enforce_period_closing
    BEFORE INSERT OR UPDATE OF entry_date ON financial.journal_entries
    FOR EACH ROW
    WHEN (NEW.is_posted = TRUE)
    EXECUTE FUNCTION enforce_period_closing();

-- =============================================
-- 6. BANK RECONCILIATION AUTO-MATCH TRIGGER
-- =============================================
-- Automatically matches bank transactions with book entries
CREATE OR REPLACE FUNCTION auto_match_bank_transactions()
RETURNS TRIGGER AS $$
DECLARE
    v_matched_entry RECORD;
    v_tolerance NUMERIC := 0.01; -- Tolerance for matching amounts
BEGIN
    -- Skip if already reconciled
    IF NEW.is_reconciled THEN
        RETURN NEW;
    END IF;
    
    -- Try to find matching journal entry
    -- Match by amount and date (within 3 days)
    SELECT 
        je.journal_entry_id,
        je.journal_number,
        je.total_debit,
        je.total_credit
    INTO v_matched_entry
    FROM financial.journal_entries je
    WHERE je.org_id = (
        SELECT org_id 
        FROM master.org_bank_accounts 
        WHERE bank_account_id = (
            SELECT bank_account_id 
            FROM financial.bank_reconciliation 
            WHERE reconciliation_id = NEW.reconciliation_id
        )
    )
    AND je.entry_date BETWEEN NEW.transaction_date - INTERVAL '3 days' 
        AND NEW.transaction_date + INTERVAL '3 days'
    AND je.is_posted = TRUE
    AND NOT EXISTS (
        SELECT 1 
        FROM financial.bank_statement_entries bse
        WHERE bse.matched_journal_entry_id = je.journal_entry_id
        AND bse.is_reconciled = TRUE
    )
    AND (
        (NEW.transaction_type = 'credit' AND 
         ABS(je.total_credit - NEW.amount) <= v_tolerance)
        OR
        (NEW.transaction_type = 'debit' AND 
         ABS(je.total_debit - NEW.amount) <= v_tolerance)
    )
    ORDER BY ABS(je.entry_date - NEW.transaction_date)
    LIMIT 1;
    
    -- If match found, update the entry
    IF v_matched_entry.journal_entry_id IS NOT NULL THEN
        NEW.is_reconciled := TRUE;
        NEW.matched_journal_entry_id := v_matched_entry.journal_entry_id;
        NEW.book_amount := CASE 
            WHEN NEW.transaction_type = 'credit' THEN v_matched_entry.total_credit
            ELSE v_matched_entry.total_debit
        END;
        NEW.difference_amount := NEW.amount - NEW.book_amount;
        
        -- Log the auto-match
        INSERT INTO audit.reconciliation_matches (
            statement_entry_id,
            journal_entry_id,
            match_type,
            match_confidence,
            matched_at
        ) VALUES (
            NEW.statement_entry_id,
            v_matched_entry.journal_entry_id,
            'auto_amount_date',
            0.95, -- 95% confidence for amount+date match
            CURRENT_TIMESTAMP
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_match_bank_transactions
    BEFORE INSERT OR UPDATE ON financial.bank_statement_entries
    FOR EACH ROW
    WHEN (NEW.is_reconciled = FALSE)
    EXECUTE FUNCTION auto_match_bank_transactions();

-- =============================================
-- 7. CREATE OUTSTANDING ON INVOICE TRIGGER
-- =============================================
-- Automatically creates outstanding record when invoice is created
CREATE OR REPLACE FUNCTION create_customer_outstanding_on_invoice()
RETURNS TRIGGER AS $$
DECLARE
    v_payment_terms INTEGER;
    v_due_date DATE;
BEGIN
    -- Only create for posted invoices
    IF NEW.invoice_status != 'posted' THEN
        RETURN NEW;
    END IF;
    
    -- Get payment terms from customer
    SELECT COALESCE(payment_terms_days, 30)
    INTO v_payment_terms
    FROM parties.customers
    WHERE customer_id = NEW.customer_id;
    
    -- Calculate due date
    v_due_date := NEW.invoice_date + (v_payment_terms || ' days')::INTERVAL;
    
    -- Create or update outstanding record
    INSERT INTO financial.customer_outstanding (
        org_id,
        customer_id,
        transaction_type,
        transaction_id,
        transaction_number,
        transaction_date,
        original_amount,
        paid_amount,
        outstanding_amount,
        due_date,
        status,
        created_at
    ) VALUES (
        NEW.org_id,
        NEW.customer_id,
        'invoice',
        NEW.invoice_id,
        NEW.invoice_number,
        NEW.invoice_date,
        NEW.final_amount,
        0,
        NEW.final_amount,
        v_due_date,
        'open',
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (transaction_type, transaction_id) 
    DO UPDATE SET
        original_amount = EXCLUDED.original_amount,
        outstanding_amount = EXCLUDED.original_amount - financial.customer_outstanding.paid_amount,
        updated_at = CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_customer_outstanding
    AFTER INSERT OR UPDATE OF invoice_status ON sales.invoices
    FOR EACH ROW
    WHEN (NEW.invoice_status = 'posted')
    EXECUTE FUNCTION create_customer_outstanding_on_invoice();

-- =============================================
-- CRITICAL INDEXES FOR FINANCIAL TRIGGERS
-- =============================================
CREATE INDEX IF NOT EXISTS idx_journal_entries_period 
    ON financial.journal_entries(org_id, entry_date);
    
CREATE INDEX IF NOT EXISTS idx_payment_allocations_reference 
    ON financial.payment_allocations(reference_type, reference_id);
    
CREATE INDEX IF NOT EXISTS idx_customer_outstanding_aging 
    ON financial.customer_outstanding(customer_id, aging_bucket, status);
    
CREATE INDEX IF NOT EXISTS idx_bank_statement_reconciliation 
    ON financial.bank_statement_entries(reconciliation_id, is_reconciled);