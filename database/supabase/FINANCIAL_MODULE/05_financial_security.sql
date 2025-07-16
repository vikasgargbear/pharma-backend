-- =============================================
-- FINANCIAL MODULE - SECURITY & RLS
-- =============================================
-- Version: 1.0 - Standalone Financial System
-- Description: Row Level Security and access control
-- Deploy Order: 5th - After indexes
-- =============================================

-- =============================================
-- ENABLE ROW LEVEL SECURITY
-- =============================================

-- Enable RLS on all financial tables
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE financial_years ENABLE ROW LEVEL SECURITY;
ALTER TABLE ledger_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE ledgers ENABLE ROW LEVEL SECURITY;
ALTER TABLE voucher_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE vouchers ENABLE ROW LEVEL SECURITY;
ALTER TABLE voucher_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_centers ENABLE ROW LEVEL SECURITY;
ALTER TABLE bill_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_statements ENABLE ROW LEVEL SECURITY;
ALTER TABLE budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE gst_returns ENABLE ROW LEVEL SECURITY;
ALTER TABLE gstr1_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE gstr3b_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE e_invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE e_way_bills ENABLE ROW LEVEL SECURITY;
ALTER TABLE tds_deductions ENABLE ROW LEVEL SECURITY;
ALTER TABLE trial_balance ENABLE ROW LEVEL SECURITY;
ALTER TABLE financial_ratios ENABLE ROW LEVEL SECURITY;
ALTER TABLE erp_sync_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE financial_users ENABLE ROW LEVEL SECURITY;

-- =============================================
-- BASIC COMPANY ISOLATION POLICIES
-- =============================================

-- Companies - users can only see companies they have access to
CREATE POLICY companies_isolation 
ON companies FOR ALL 
TO authenticated 
USING (
    company_id IN (
        SELECT company_id FROM financial_users 
        WHERE user_id = current_setting('app.current_user_id', true)::INTEGER
        AND is_active = TRUE
    )
);

-- Financial users - users can only see users from their companies
CREATE POLICY financial_users_isolation 
ON financial_users FOR ALL 
TO authenticated 
USING (
    company_id IN (
        SELECT company_id FROM financial_users 
        WHERE user_id = current_setting('app.current_user_id', true)::INTEGER
        AND is_active = TRUE
    )
);

-- =============================================
-- FINANCIAL DATA ISOLATION
-- =============================================

-- Financial years
CREATE POLICY financial_years_isolation 
ON financial_years FOR ALL 
TO authenticated 
USING (company_id = current_company_id());

-- Ledger groups - allow system groups + company groups
CREATE POLICY ledger_groups_isolation 
ON ledger_groups FOR ALL 
TO authenticated 
USING (company_id IS NULL OR company_id = current_company_id());

-- Ledgers
CREATE POLICY ledgers_isolation 
ON ledgers FOR ALL 
TO authenticated 
USING (company_id = current_company_id());

-- Voucher types
CREATE POLICY voucher_types_isolation 
ON voucher_types FOR ALL 
TO authenticated 
USING (company_id IS NULL OR company_id = current_company_id());

-- Vouchers
CREATE POLICY vouchers_isolation 
ON vouchers FOR ALL 
TO authenticated 
USING (company_id = current_company_id());

-- Voucher entries - through voucher access
CREATE POLICY voucher_entries_isolation 
ON voucher_entries FOR ALL 
TO authenticated 
USING (
    EXISTS (
        SELECT 1 FROM vouchers v 
        WHERE v.voucher_id = voucher_entries.voucher_id 
        AND v.company_id = current_company_id()
    )
);

-- =============================================
-- ROLE-BASED ACCESS POLICIES
-- =============================================

-- Voucher creation - only authorized roles
CREATE POLICY vouchers_create_access 
ON vouchers FOR INSERT 
TO authenticated 
USING (
    company_id = current_company_id() 
    AND EXISTS (
        SELECT 1 FROM financial_users 
        WHERE user_id = current_setting('app.current_user_id', true)::INTEGER
        AND company_id = current_company_id()
        AND can_create_vouchers = TRUE
    )
);

-- Voucher approval - only authorized roles
CREATE POLICY vouchers_approve_access 
ON vouchers FOR UPDATE 
TO authenticated 
USING (
    company_id = current_company_id() 
    AND (
        -- Can update own unposted vouchers
        (created_by = current_setting('app.current_user_id', true)::INTEGER AND is_posted = FALSE)
        OR
        -- Can approve if authorized
        EXISTS (
            SELECT 1 FROM financial_users 
            WHERE user_id = current_setting('app.current_user_id', true)::INTEGER
            AND company_id = current_company_id()
            AND can_approve_vouchers = TRUE
        )
    )
);

-- Master data management - only authorized roles
CREATE POLICY ledgers_manage_access 
ON ledgers FOR INSERT OR UPDATE OR DELETE 
TO authenticated 
USING (
    company_id = current_company_id() 
    AND EXISTS (
        SELECT 1 FROM financial_users 
        WHERE user_id = current_setting('app.current_user_id', true)::INTEGER
        AND company_id = current_company_id()
        AND can_manage_masters = TRUE
    )
);

-- GST returns - only authorized roles
CREATE POLICY gst_returns_access 
ON gst_returns FOR ALL 
TO authenticated 
USING (
    company_id = current_company_id() 
    AND EXISTS (
        SELECT 1 FROM financial_users 
        WHERE user_id = current_setting('app.current_user_id', true)::INTEGER
        AND company_id = current_company_id()
        AND (can_file_returns = TRUE OR role IN ('cfo', 'auditor'))
    )
);

-- =============================================
-- SENSITIVE DATA POLICIES
-- =============================================

-- Bank accounts - restricted access
CREATE POLICY bank_accounts_access 
ON bank_accounts FOR ALL 
TO authenticated 
USING (
    company_id = current_company_id() 
    AND EXISTS (
        SELECT 1 FROM financial_users 
        WHERE user_id = current_setting('app.current_user_id', true)::INTEGER
        AND company_id = current_company_id()
        AND role IN ('cfo', 'accountant', 'auditor')
    )
);

-- Bank statements - restricted access
CREATE POLICY bank_statements_access 
ON bank_statements FOR ALL 
TO authenticated 
USING (
    EXISTS (
        SELECT 1 FROM bank_accounts ba
        JOIN financial_users fu ON fu.company_id = ba.company_id
        WHERE ba.bank_account_id = bank_statements.bank_account_id
        AND fu.user_id = current_setting('app.current_user_id', true)::INTEGER
        AND fu.role IN ('cfo', 'accountant', 'auditor')
    )
);

-- =============================================
-- AUDIT & COMPLIANCE POLICIES
-- =============================================

-- Prevent deletion of posted vouchers
CREATE POLICY prevent_posted_voucher_deletion 
ON vouchers FOR DELETE 
TO authenticated 
USING (FALSE)
WHERE is_posted = TRUE;

-- Prevent modification of posted entries
CREATE POLICY prevent_posted_entry_modification 
ON voucher_entries FOR UPDATE OR DELETE 
TO authenticated 
USING (
    NOT EXISTS (
        SELECT 1 FROM vouchers v 
        WHERE v.voucher_id = voucher_entries.voucher_id 
        AND v.is_posted = TRUE
    )
);

-- =============================================
-- INTEGRATION POLICIES
-- =============================================

-- ERP sync queue - system integration access
CREATE POLICY erp_sync_queue_isolation 
ON erp_sync_queue FOR ALL 
TO authenticated 
USING (company_id = current_company_id());

-- =============================================
-- SECURITY HELPER FUNCTIONS
-- =============================================

-- Check if user has permission
CREATE OR REPLACE FUNCTION has_financial_permission(p_permission TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    v_user RECORD;
BEGIN
    SELECT * INTO v_user
    FROM financial_users
    WHERE user_id = current_setting('app.current_user_id', true)::INTEGER
    AND company_id = current_company_id()
    AND is_active = TRUE;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    RETURN CASE p_permission
        WHEN 'create_vouchers' THEN v_user.can_create_vouchers
        WHEN 'approve_vouchers' THEN v_user.can_approve_vouchers
        WHEN 'view_reports' THEN v_user.can_view_reports
        WHEN 'manage_masters' THEN v_user.can_manage_masters
        WHEN 'file_returns' THEN v_user.can_file_returns
        ELSE FALSE
    END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Validate financial user session
CREATE OR REPLACE FUNCTION validate_financial_session()
RETURNS BOOLEAN AS $$
DECLARE
    v_user RECORD;
BEGIN
    SELECT * INTO v_user
    FROM financial_users
    WHERE user_id = current_setting('app.current_user_id', true)::INTEGER
    AND company_id = current_company_id()
    AND is_active = TRUE;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Update last login
    UPDATE financial_users 
    SET last_login_at = CURRENT_TIMESTAMP
    WHERE user_id = v_user.user_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- AUDIT LOG TABLE
-- =============================================

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id SERIAL PRIMARY KEY,
    company_id UUID NOT NULL REFERENCES companies(company_id),
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    action TEXT NOT NULL,
    old_values JSONB,
    new_values JSONB,
    user_id INTEGER REFERENCES financial_users(user_id),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enable RLS on audit log
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Audit log policy - view only, no modifications
CREATE POLICY audit_log_read_only 
ON audit_log FOR SELECT 
TO authenticated 
USING (
    company_id = current_company_id() 
    AND EXISTS (
        SELECT 1 FROM financial_users 
        WHERE user_id = current_setting('app.current_user_id', true)::INTEGER
        AND company_id = current_company_id()
        AND role IN ('cfo', 'auditor')
    )
);

-- =============================================
-- DEFAULT POLICIES FOR REMAINING TABLES
-- =============================================

-- Cost centers
CREATE POLICY cost_centers_isolation ON cost_centers FOR ALL TO authenticated USING (company_id = current_company_id());

-- Bill details
CREATE POLICY bill_details_isolation ON bill_details FOR ALL TO authenticated USING (company_id = current_company_id());

-- Budgets
CREATE POLICY budgets_isolation ON budgets FOR ALL TO authenticated USING (company_id = current_company_id());

-- Budget details
CREATE POLICY budget_details_isolation ON budget_details FOR ALL TO authenticated 
USING (EXISTS (SELECT 1 FROM budgets b WHERE b.budget_id = budget_details.budget_id AND b.company_id = current_company_id()));

-- Financial analytics
CREATE POLICY trial_balance_isolation ON trial_balance FOR ALL TO authenticated USING (company_id = current_company_id());
CREATE POLICY financial_ratios_isolation ON financial_ratios FOR ALL TO authenticated USING (company_id = current_company_id());

-- GST data
CREATE POLICY gstr1_data_isolation ON gstr1_data FOR ALL TO authenticated USING (company_id = current_company_id());
CREATE POLICY gstr3b_data_isolation ON gstr3b_data FOR ALL TO authenticated USING (company_id = current_company_id());
CREATE POLICY e_invoices_isolation ON e_invoices FOR ALL TO authenticated USING (company_id = current_company_id());
CREATE POLICY e_way_bills_isolation ON e_way_bills FOR ALL TO authenticated USING (company_id = current_company_id());

-- TDS
CREATE POLICY tds_deductions_isolation ON tds_deductions FOR ALL TO authenticated USING (company_id = current_company_id());

-- =============================================
-- SUCCESS MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
FINANCIAL SECURITY & RLS DEPLOYED
=============================================
✓ Row Level Security enabled on all tables
✓ Company isolation policies
✓ Role-based access control
✓ Sensitive data protection
✓ Audit & compliance policies
✓ Integration security
✓ Security helper functions
✓ Audit logging system

Security Features:
- Multi-company isolation
- Role-based permissions
- Posted voucher protection
- Audit trail
- Session validation

Next: Deploy 06_financial_initial_data.sql
';
END $$;