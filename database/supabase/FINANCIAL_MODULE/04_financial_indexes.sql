-- =============================================
-- FINANCIAL MODULE - INDEXES & PERFORMANCE
-- =============================================
-- Version: 1.0 - Standalone Financial System
-- Description: Performance optimization indexes
-- Deploy Order: 4th - After triggers
-- =============================================

-- =============================================
-- COMPANY & USER INDEXES
-- =============================================

-- Company lookups
CREATE INDEX IF NOT EXISTS idx_companies_gst ON companies(gst_number) WHERE gst_number IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_companies_active ON companies(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_companies_erp_org ON companies(erp_org_id) WHERE erp_org_id IS NOT NULL;

-- Financial users
CREATE INDEX IF NOT EXISTS idx_financial_users_company ON financial_users(company_id);
CREATE INDEX IF NOT EXISTS idx_financial_users_email ON financial_users(company_id, email);
CREATE INDEX IF NOT EXISTS idx_financial_users_role ON financial_users(company_id, role) WHERE is_active = TRUE;

-- =============================================
-- LEDGER MANAGEMENT INDEXES
-- =============================================

-- Ledger groups hierarchy
CREATE INDEX IF NOT EXISTS idx_ledger_groups_company ON ledger_groups(company_id);
CREATE INDEX IF NOT EXISTS idx_ledger_groups_parent ON ledger_groups(parent_group_id) WHERE parent_group_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ledger_groups_nature ON ledger_groups(company_id, nature);

-- Ledgers
CREATE INDEX IF NOT EXISTS idx_ledgers_company ON ledgers(company_id);
CREATE INDEX IF NOT EXISTS idx_ledgers_group ON ledgers(group_id);
CREATE INDEX IF NOT EXISTS idx_ledgers_external_ref ON ledgers(external_ref_type, external_ref_id) WHERE external_ref_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ledgers_active ON ledgers(company_id, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_ledgers_tax_type ON ledgers(company_id, tax_type) WHERE tax_type IS NOT NULL;

-- =============================================
-- VOUCHER INDEXES
-- =============================================

-- Voucher types
CREATE INDEX IF NOT EXISTS idx_voucher_types_company_class ON voucher_types(company_id, voucher_class);
CREATE INDEX IF NOT EXISTS idx_voucher_types_default ON voucher_types(company_id, is_default) WHERE is_default = TRUE;

-- Vouchers
CREATE INDEX IF NOT EXISTS idx_vouchers_company_date ON vouchers(company_id, voucher_date);
CREATE INDEX IF NOT EXISTS idx_vouchers_type ON vouchers(voucher_type_id);
CREATE INDEX IF NOT EXISTS idx_vouchers_posted ON vouchers(company_id, is_posted) WHERE is_posted = TRUE;
CREATE INDEX IF NOT EXISTS idx_vouchers_cancelled ON vouchers(is_cancelled) WHERE is_cancelled = TRUE;
CREATE INDEX IF NOT EXISTS idx_vouchers_number ON vouchers(company_id, voucher_number);

-- Voucher entries
CREATE INDEX IF NOT EXISTS idx_voucher_entries_voucher ON voucher_entries(voucher_id);
CREATE INDEX IF NOT EXISTS idx_voucher_entries_ledger ON voucher_entries(ledger_id);
CREATE INDEX IF NOT EXISTS idx_voucher_entries_billwise ON voucher_entries(is_billwise) WHERE is_billwise = TRUE;

-- Composite index for ledger balance calculation
CREATE INDEX IF NOT EXISTS idx_voucher_entries_balance_calc ON voucher_entries(ledger_id, voucher_id)
INCLUDE (debit_amount, credit_amount);

-- =============================================
-- FINANCIAL YEAR INDEXES
-- =============================================

-- Financial years
CREATE INDEX IF NOT EXISTS idx_financial_years_company ON financial_years(company_id);
CREATE INDEX IF NOT EXISTS idx_financial_years_current ON financial_years(company_id, is_current) WHERE is_current = TRUE;
CREATE INDEX IF NOT EXISTS idx_financial_years_dates ON financial_years(company_id, start_date, end_date);

-- =============================================
-- BILL-WISE TRACKING INDEXES
-- =============================================

-- Bill details
CREATE INDEX IF NOT EXISTS idx_bill_details_company ON bill_details(company_id);
CREATE INDEX IF NOT EXISTS idx_bill_details_ledger ON bill_details(ledger_id);
CREATE INDEX IF NOT EXISTS idx_bill_details_status ON bill_details(status) WHERE status IN ('Outstanding', 'Partial');
CREATE INDEX IF NOT EXISTS idx_bill_details_due_date ON bill_details(due_date) WHERE status IN ('Outstanding', 'Partial');
CREATE INDEX IF NOT EXISTS idx_bill_details_overdue ON bill_details(overdue_days) WHERE status IN ('Outstanding', 'Partial') AND overdue_days > 0;

-- =============================================
-- COST CENTER INDEXES
-- =============================================

-- Cost centers
CREATE INDEX IF NOT EXISTS idx_cost_centers_company ON cost_centers(company_id);
CREATE INDEX IF NOT EXISTS idx_cost_centers_parent ON cost_centers(parent_id) WHERE parent_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_cost_centers_active ON cost_centers(company_id, is_active) WHERE is_active = TRUE;

-- =============================================
-- BANK RECONCILIATION INDEXES
-- =============================================

-- Bank accounts
CREATE INDEX IF NOT EXISTS idx_bank_accounts_company ON bank_accounts(company_id);
CREATE INDEX IF NOT EXISTS idx_bank_accounts_ledger ON bank_accounts(ledger_id);
CREATE INDEX IF NOT EXISTS idx_bank_accounts_active ON bank_accounts(company_id, is_active) WHERE is_active = TRUE;

-- Bank statements
CREATE INDEX IF NOT EXISTS idx_bank_statements_account_date ON bank_statements(bank_account_id, transaction_date);
CREATE INDEX IF NOT EXISTS idx_bank_statements_unreconciled ON bank_statements(bank_account_id, is_reconciled) WHERE is_reconciled = FALSE;
CREATE INDEX IF NOT EXISTS idx_bank_statements_import_batch ON bank_statements(import_batch_id) WHERE import_batch_id IS NOT NULL;

-- =============================================
-- GST COMPLIANCE INDEXES
-- =============================================

-- GST rates
CREATE INDEX IF NOT EXISTS idx_gst_rates_hsn ON gst_rates(hsn_sac_code, effective_from);
CREATE INDEX IF NOT EXISTS idx_gst_rates_active ON gst_rates(hsn_sac_code, is_active) WHERE is_active = TRUE;

-- GST returns
CREATE INDEX IF NOT EXISTS idx_gst_returns_company_period ON gst_returns(company_id, return_type, return_period);
CREATE INDEX IF NOT EXISTS idx_gst_returns_status ON gst_returns(company_id, filing_status);

-- GSTR data
CREATE INDEX IF NOT EXISTS idx_gstr1_data_company_period ON gstr1_data(company_id, return_period);
CREATE INDEX IF NOT EXISTS idx_gstr3b_data_company_period ON gstr3b_data(company_id, return_period);

-- E-invoices
CREATE INDEX IF NOT EXISTS idx_e_invoices_company ON e_invoices(company_id);
CREATE INDEX IF NOT EXISTS idx_e_invoices_irn ON e_invoices(irn) WHERE irn IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_e_invoices_status ON e_invoices(status) WHERE status = 'Pending';

-- E-way bills
CREATE INDEX IF NOT EXISTS idx_e_way_bills_company ON e_way_bills(company_id);
CREATE INDEX IF NOT EXISTS idx_e_way_bills_number ON e_way_bills(ewb_number) WHERE ewb_number IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_e_way_bills_status ON e_way_bills(status) WHERE status = 'Active';

-- =============================================
-- TDS MANAGEMENT INDEXES
-- =============================================

-- TDS rates
CREATE INDEX IF NOT EXISTS idx_tds_rates_section ON tds_rates(section_code, effective_from);
CREATE INDEX IF NOT EXISTS idx_tds_rates_active ON tds_rates(section_code, is_active) WHERE is_active = TRUE;

-- TDS deductions
CREATE INDEX IF NOT EXISTS idx_tds_deductions_company ON tds_deductions(company_id);
CREATE INDEX IF NOT EXISTS idx_tds_deductions_supplier ON tds_deductions(supplier_id) WHERE supplier_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tds_deductions_challan ON tds_deductions(challan_date) WHERE challan_number IS NOT NULL;

-- =============================================
-- BUDGET INDEXES
-- =============================================

-- Budgets
CREATE INDEX IF NOT EXISTS idx_budgets_company_year ON budgets(company_id, financial_year_id);
CREATE INDEX IF NOT EXISTS idx_budgets_active ON budgets(company_id, is_active) WHERE is_active = TRUE;

-- Budget details
CREATE INDEX IF NOT EXISTS idx_budget_details_budget ON budget_details(budget_id);
CREATE INDEX IF NOT EXISTS idx_budget_details_ledger ON budget_details(ledger_id) WHERE ledger_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_budget_details_variance ON budget_details(variance_percent) WHERE ABS(variance_percent) > 10;

-- =============================================
-- INTEGRATION INDEXES
-- =============================================

-- ERP sync queue
CREATE INDEX IF NOT EXISTS idx_erp_sync_queue_pending ON erp_sync_queue(company_id, sync_status, created_at) WHERE sync_status = 'pending';
CREATE INDEX IF NOT EXISTS idx_erp_sync_queue_failed ON erp_sync_queue(company_id, sync_status, retry_count) WHERE sync_status = 'failed' AND retry_count < max_retries;
CREATE INDEX IF NOT EXISTS idx_erp_sync_queue_reference ON erp_sync_queue(erp_reference_type, erp_reference_id);

-- Integration logs
CREATE INDEX IF NOT EXISTS idx_integration_logs_company_time ON integration_logs(company_id, request_timestamp);
CREATE INDEX IF NOT EXISTS idx_integration_logs_endpoint ON integration_logs(api_endpoint, http_method);
CREATE INDEX IF NOT EXISTS idx_integration_logs_failed ON integration_logs(is_success, request_timestamp) WHERE is_success = FALSE;

-- =============================================
-- ANALYTICS INDEXES
-- =============================================

-- Trial balance
CREATE INDEX IF NOT EXISTS idx_trial_balance_company_date ON trial_balance(company_id, as_on_date);
CREATE INDEX IF NOT EXISTS idx_trial_balance_year_ledger ON trial_balance(financial_year_id, ledger_id);

-- Financial ratios
CREATE INDEX IF NOT EXISTS idx_financial_ratios_company_period ON financial_ratios(company_id, period_type, period_date);

-- =============================================
-- COMPOSITE INDEXES FOR REPORTS
-- =============================================

-- Profit & Loss query optimization
CREATE INDEX IF NOT EXISTS idx_vouchers_pl_report ON vouchers(company_id, voucher_date, is_posted, is_cancelled)
WHERE is_posted = TRUE AND is_cancelled = FALSE;

-- Balance Sheet query optimization
CREATE INDEX IF NOT EXISTS idx_ledgers_balance_sheet ON ledgers(company_id, group_id, is_active)
INCLUDE (current_balance, balance_type)
WHERE is_active = TRUE;

-- Cash Flow optimization
CREATE INDEX IF NOT EXISTS idx_voucher_entries_cash_flow ON voucher_entries(ledger_id)
WHERE ledger_id IN (
    SELECT ledger_id FROM ledgers WHERE group_id IN (
        SELECT group_id FROM ledger_groups WHERE group_name IN ('Cash-in-hand', 'Bank Accounts')
    )
);

-- Outstanding analysis
CREATE INDEX IF NOT EXISTS idx_bill_details_aging ON bill_details(company_id, status, overdue_days, outstanding_amount)
WHERE status IN ('Outstanding', 'Partial') AND outstanding_amount > 0;

-- =============================================
-- FULL TEXT SEARCH INDEXES
-- =============================================

-- Ledger search
CREATE INDEX IF NOT EXISTS idx_ledgers_search ON ledgers USING gin(
    to_tsvector('english', ledger_name || ' ' || COALESCE(ledger_code, ''))
);

-- Voucher narration search
CREATE INDEX IF NOT EXISTS idx_vouchers_narration_search ON vouchers USING gin(
    to_tsvector('english', COALESCE(narration, ''))
);

-- =============================================
-- STATISTICS UPDATE
-- =============================================

-- Update statistics for all tables
ANALYZE companies;
ANALYZE financial_years;
ANALYZE ledger_groups;
ANALYZE ledgers;
ANALYZE voucher_types;
ANALYZE vouchers;
ANALYZE voucher_entries;
ANALYZE cost_centers;
ANALYZE bill_details;
ANALYZE bank_accounts;
ANALYZE bank_statements;
ANALYZE budgets;
ANALYZE budget_details;
ANALYZE gst_rates;
ANALYZE gst_returns;
ANALYZE gstr1_data;
ANALYZE gstr3b_data;
ANALYZE e_invoices;
ANALYZE e_way_bills;
ANALYZE tds_rates;
ANALYZE tds_deductions;
ANALYZE trial_balance;
ANALYZE financial_ratios;
ANALYZE erp_sync_queue;
ANALYZE integration_logs;

-- =============================================
-- SUCCESS MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
FINANCIAL INDEXES DEPLOYED SUCCESSFULLY
=============================================
✓ Company & User Indexes
✓ Ledger Management Indexes
✓ Voucher Indexes (with INCLUDE)
✓ Financial Year Indexes
✓ Bill-wise Tracking Indexes
✓ Bank Reconciliation Indexes
✓ GST Compliance Indexes
✓ TDS Management Indexes
✓ Budget Indexes
✓ Integration Indexes
✓ Analytics Indexes
✓ Composite Report Indexes
✓ Full Text Search Indexes
✓ Statistics Updated

Total Indexes: 80+

Next: Deploy 05_financial_security.sql
';
END $$;