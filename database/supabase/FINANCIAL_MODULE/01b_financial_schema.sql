-- =============================================
-- PHARMACEUTICAL ERP - FINANCIAL & ACCOUNTING SCHEMA
-- =============================================
-- Version: 1.0 - Production Enterprise Ready
-- Description: Complete financial module with Tally-like features
-- Deploy Order: 1b - After core schema
-- =============================================

-- =============================================
-- FINANCIAL PERIODS & CONFIGURATION
-- =============================================

CREATE TABLE IF NOT EXISTS financial_years (
    year_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    year_code TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT FALSE,
    is_closed BOOLEAN DEFAULT FALSE,
    closed_by INTEGER REFERENCES org_users(user_id),
    closed_at TIMESTAMP WITH TIME ZONE,
    books_beginning_from DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, year_code)
);

-- Ledger groups (hierarchical)
CREATE TABLE IF NOT EXISTS ledger_groups (
    group_id SERIAL PRIMARY KEY,
    org_id UUID REFERENCES organizations(org_id),
    group_name TEXT NOT NULL,
    parent_group_id INTEGER REFERENCES ledger_groups(group_id),
    group_code TEXT,
    nature TEXT NOT NULL, -- 'Assets', 'Liabilities', 'Income', 'Expenses'
    is_system_group BOOLEAN DEFAULT FALSE,
    affects_gross_profit BOOLEAN DEFAULT FALSE,
    hierarchy_level INTEGER DEFAULT 0,
    full_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, group_name)
);

-- Complete ledger master
CREATE TABLE IF NOT EXISTS ledgers (
    ledger_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    ledger_name TEXT NOT NULL,
    ledger_code TEXT,
    group_id INTEGER NOT NULL REFERENCES ledger_groups(group_id),
    
    -- Opening balance
    opening_balance DECIMAL(15,2) DEFAULT 0,
    opening_balance_type TEXT DEFAULT 'Dr', -- 'Dr' or 'Cr'
    
    -- Current balance
    current_balance DECIMAL(15,2) DEFAULT 0,
    balance_type TEXT DEFAULT 'Dr',
    
    -- Linking
    customer_id INTEGER REFERENCES customers(customer_id),
    supplier_id INTEGER REFERENCES suppliers(supplier_id),
    bank_account_id INTEGER,
    
    -- Tax settings
    tax_type TEXT, -- 'GST', 'TDS', 'TCS'
    gst_registration_type TEXT,
    tds_applicable BOOLEAN DEFAULT FALSE,
    tds_rate DECIMAL(5,2),
    
    -- Properties
    is_subledger BOOLEAN DEFAULT FALSE,
    maintain_billwise BOOLEAN DEFAULT TRUE,
    credit_period_days INTEGER DEFAULT 0,
    credit_limit DECIMAL(15,2) DEFAULT 0,
    
    -- Bank details
    bank_name TEXT,
    account_number TEXT,
    ifsc_code TEXT,
    
    -- Mailing details
    mailing_name TEXT,
    mailing_address JSONB,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, ledger_name)
);

-- Voucher types configuration
CREATE TABLE IF NOT EXISTS voucher_types (
    voucher_type_id SERIAL PRIMARY KEY,
    org_id UUID REFERENCES organizations(org_id),
    voucher_type_name TEXT NOT NULL,
    voucher_class TEXT NOT NULL, -- 'Sales', 'Purchase', 'Payment', 'Receipt', 'Contra', 'Journal'
    abbreviation TEXT,
    
    -- Numbering
    numbering_method TEXT DEFAULT 'Automatic',
    prefix TEXT,
    suffix TEXT,
    starting_number INTEGER DEFAULT 1,
    current_number INTEGER DEFAULT 1,
    
    -- Settings
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    print_after_save BOOLEAN DEFAULT FALSE,
    use_common_narration BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, voucher_type_name)
);

-- Main voucher entries
CREATE TABLE IF NOT EXISTS vouchers (
    voucher_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Voucher details
    voucher_number TEXT NOT NULL,
    voucher_date DATE NOT NULL,
    voucher_type_id INTEGER NOT NULL REFERENCES voucher_types(voucher_type_id),
    
    -- Reference
    reference_number TEXT,
    reference_date DATE,
    
    -- Linked transactions
    order_id INTEGER REFERENCES orders(order_id),
    purchase_id INTEGER REFERENCES purchases(purchase_id),
    payment_id INTEGER REFERENCES payments(payment_id),
    
    -- Narration
    narration TEXT,
    
    -- Amounts
    total_amount DECIMAL(15,2) DEFAULT 0,
    
    -- Status
    is_posted BOOLEAN DEFAULT FALSE,
    is_cancelled BOOLEAN DEFAULT FALSE,
    is_optional BOOLEAN DEFAULT FALSE,
    
    -- Audit
    created_by INTEGER REFERENCES org_users(user_id),
    approved_by INTEGER REFERENCES org_users(user_id),
    posted_by INTEGER REFERENCES org_users(user_id),
    cancelled_by INTEGER REFERENCES org_users(user_id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    posted_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(org_id, voucher_number)
);

-- Voucher ledger entries
CREATE TABLE IF NOT EXISTS voucher_entries (
    entry_id SERIAL PRIMARY KEY,
    voucher_id INTEGER NOT NULL REFERENCES vouchers(voucher_id) ON DELETE CASCADE,
    ledger_id INTEGER NOT NULL REFERENCES ledgers(ledger_id),
    
    -- Amounts
    debit_amount DECIMAL(15,2) DEFAULT 0,
    credit_amount DECIMAL(15,2) DEFAULT 0,
    
    -- Bill allocation
    is_billwise BOOLEAN DEFAULT FALSE,
    bill_allocations JSONB,
    
    -- Cost center
    cost_center_id INTEGER,
    
    -- Bank details
    bank_date DATE,
    instrument_number TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Cost centers
CREATE TABLE IF NOT EXISTS cost_centers (
    cost_center_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    cost_center_name TEXT NOT NULL,
    parent_id INTEGER REFERENCES cost_centers(cost_center_id),
    category TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, cost_center_name)
);

-- Bill-wise details
CREATE TABLE IF NOT EXISTS bill_details (
    bill_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    ledger_id INTEGER NOT NULL REFERENCES ledgers(ledger_id),
    
    -- Bill info
    bill_number TEXT NOT NULL,
    bill_date DATE NOT NULL,
    bill_amount DECIMAL(15,2) NOT NULL,
    
    -- Outstanding
    paid_amount DECIMAL(15,2) DEFAULT 0,
    outstanding_amount DECIMAL(15,2) NOT NULL,
    
    -- Credit period
    due_date DATE,
    overdue_days INTEGER GENERATED ALWAYS AS (
        GREATEST(0, EXTRACT(DAYS FROM CURRENT_DATE - due_date)::INTEGER)
    ) STORED,
    
    -- Reference
    voucher_id INTEGER REFERENCES vouchers(voucher_id),
    
    -- Status
    status TEXT DEFAULT 'Outstanding', -- 'Outstanding', 'Paid', 'Partial'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bank accounts
CREATE TABLE IF NOT EXISTS bank_accounts (
    bank_account_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    ledger_id INTEGER NOT NULL REFERENCES ledgers(ledger_id),
    
    -- Bank details
    bank_name TEXT NOT NULL,
    branch_name TEXT,
    account_number TEXT NOT NULL,
    account_type TEXT,
    ifsc_code TEXT,
    swift_code TEXT,
    
    -- Integration
    bank_feed_enabled BOOLEAN DEFAULT FALSE,
    last_sync_date DATE,
    
    -- Balance
    current_balance DECIMAL(15,2) DEFAULT 0,
    available_balance DECIMAL(15,2) DEFAULT 0,
    
    -- Cheque management
    next_cheque_number INTEGER,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, account_number)
);

-- Bank statements
CREATE TABLE IF NOT EXISTS bank_statements (
    statement_id SERIAL PRIMARY KEY,
    bank_account_id INTEGER NOT NULL REFERENCES bank_accounts(bank_account_id),
    
    -- Transaction details
    transaction_date DATE NOT NULL,
    value_date DATE,
    description TEXT,
    reference_number TEXT,
    
    -- Amounts
    debit_amount DECIMAL(15,2) DEFAULT 0,
    credit_amount DECIMAL(15,2) DEFAULT 0,
    balance DECIMAL(15,2),
    
    -- Reconciliation
    is_reconciled BOOLEAN DEFAULT FALSE,
    reconciled_with INTEGER REFERENCES vouchers(voucher_id),
    reconciled_date DATE,
    reconciled_by INTEGER REFERENCES org_users(user_id),
    
    -- Import info
    import_batch_id TEXT,
    import_date TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Budget master
CREATE TABLE IF NOT EXISTS budgets (
    budget_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Budget info
    budget_name TEXT NOT NULL,
    financial_year_id INTEGER REFERENCES financial_years(year_id),
    budget_type TEXT NOT NULL, -- 'Income', 'Expense', 'Capital'
    
    -- Period
    period_type TEXT NOT NULL, -- 'Monthly', 'Quarterly', 'Yearly'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, budget_name, financial_year_id)
);

-- Budget details
CREATE TABLE IF NOT EXISTS budget_details (
    budget_detail_id SERIAL PRIMARY KEY,
    budget_id INTEGER NOT NULL REFERENCES budgets(budget_id) ON DELETE CASCADE,
    
    -- Account/Cost center
    ledger_id INTEGER REFERENCES ledgers(ledger_id),
    cost_center_id INTEGER REFERENCES cost_centers(cost_center_id),
    
    -- Period budgets
    period_number INTEGER NOT NULL,
    budgeted_amount DECIMAL(15,2) NOT NULL,
    
    -- Actuals
    actual_amount DECIMAL(15,2) DEFAULT 0,
    variance_amount DECIMAL(15,2) GENERATED ALWAYS AS (actual_amount - budgeted_amount) STORED,
    variance_percent DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE WHEN budgeted_amount = 0 THEN 0 
        ELSE ((actual_amount - budgeted_amount) / budgeted_amount * 100) 
        END
    ) STORED,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- GST COMPLIANCE TABLES
-- =============================================

-- GST rate master
CREATE TABLE IF NOT EXISTS gst_rates (
    rate_id SERIAL PRIMARY KEY,
    hsn_sac_code TEXT NOT NULL,
    description TEXT,
    gst_rate DECIMAL(5,2) NOT NULL,
    cgst_rate DECIMAL(5,2),
    sgst_rate DECIMAL(5,2),
    igst_rate DECIMAL(5,2),
    cess_rate DECIMAL(5,2) DEFAULT 0,
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hsn_sac_code, effective_from)
);

-- GSTR returns master
CREATE TABLE IF NOT EXISTS gst_returns (
    return_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Return details
    return_type TEXT NOT NULL, -- 'GSTR1', 'GSTR3B', 'GSTR9'
    return_period TEXT NOT NULL, -- 'MM-YYYY'
    
    -- Amounts
    total_taxable_value DECIMAL(15,2) DEFAULT 0,
    total_cgst DECIMAL(15,2) DEFAULT 0,
    total_sgst DECIMAL(15,2) DEFAULT 0,
    total_igst DECIMAL(15,2) DEFAULT 0,
    total_cess DECIMAL(15,2) DEFAULT 0,
    
    -- Filing
    filing_status TEXT DEFAULT 'Draft', -- 'Draft', 'Filed', 'Submitted'
    filing_date DATE,
    arn_number TEXT,
    
    -- JSON data
    return_data JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, return_type, return_period)
);

-- E-invoice details
CREATE TABLE IF NOT EXISTS e_invoices (
    e_invoice_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    order_id INTEGER REFERENCES orders(order_id),
    
    -- E-invoice details
    irn TEXT UNIQUE,
    ack_number TEXT,
    ack_date TIMESTAMP WITH TIME ZONE,
    signed_invoice TEXT,
    signed_qr_code TEXT,
    
    -- Status
    status TEXT DEFAULT 'Pending', -- 'Pending', 'Generated', 'Cancelled'
    cancellation_date TIMESTAMP WITH TIME ZONE,
    cancellation_reason TEXT,
    
    -- API response
    api_response JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- E-way bills
CREATE TABLE IF NOT EXISTS e_way_bills (
    e_way_bill_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Reference
    order_id INTEGER REFERENCES orders(order_id),
    purchase_id INTEGER REFERENCES purchases(purchase_id),
    
    -- E-way bill details
    ewb_number TEXT UNIQUE,
    ewb_date TIMESTAMP WITH TIME ZONE,
    valid_upto TIMESTAMP WITH TIME ZONE,
    
    -- Transport details
    transport_mode TEXT,
    transport_distance INTEGER,
    transporter_name TEXT,
    transporter_id TEXT,
    vehicle_number TEXT,
    vehicle_type TEXT,
    
    -- Status
    status TEXT DEFAULT 'Active', -- 'Active', 'Cancelled', 'Expired'
    
    -- API response
    api_response JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- TDS MANAGEMENT
-- =============================================

-- TDS rate master
CREATE TABLE IF NOT EXISTS tds_rates (
    tds_rate_id SERIAL PRIMARY KEY,
    section_code TEXT NOT NULL,
    nature_of_payment TEXT NOT NULL,
    threshold_limit DECIMAL(15,2),
    tds_rate_individual DECIMAL(5,2),
    tds_rate_company DECIMAL(5,2),
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- TDS deductions
CREATE TABLE IF NOT EXISTS tds_deductions (
    deduction_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Reference
    voucher_id INTEGER REFERENCES vouchers(voucher_id),
    supplier_id INTEGER REFERENCES suppliers(supplier_id),
    
    -- TDS details
    section_code TEXT NOT NULL,
    gross_amount DECIMAL(15,2) NOT NULL,
    tds_amount DECIMAL(15,2) NOT NULL,
    net_amount DECIMAL(15,2) NOT NULL,
    
    -- Challan details
    challan_number TEXT,
    challan_date DATE,
    bank_bsr_code TEXT,
    
    -- Certificate
    certificate_number TEXT,
    certificate_issued BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- ADVANCED FINANCIAL ANALYTICS
-- =============================================

-- Trial balance snapshot
CREATE TABLE IF NOT EXISTS trial_balance (
    tb_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    financial_year_id INTEGER REFERENCES financial_years(year_id),
    
    -- Period
    as_on_date DATE NOT NULL,
    
    -- Ledger details
    ledger_id INTEGER REFERENCES ledgers(ledger_id),
    opening_debit DECIMAL(15,2) DEFAULT 0,
    opening_credit DECIMAL(15,2) DEFAULT 0,
    transaction_debit DECIMAL(15,2) DEFAULT 0,
    transaction_credit DECIMAL(15,2) DEFAULT 0,
    closing_debit DECIMAL(15,2) DEFAULT 0,
    closing_credit DECIMAL(15,2) DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, financial_year_id, as_on_date, ledger_id)
);

-- Ratio analysis
CREATE TABLE IF NOT EXISTS financial_ratios (
    ratio_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Period
    period_type TEXT NOT NULL, -- 'Monthly', 'Quarterly', 'Yearly'
    period_date DATE NOT NULL,
    
    -- Liquidity ratios
    current_ratio DECIMAL(5,2),
    quick_ratio DECIMAL(5,2),
    cash_ratio DECIMAL(5,2),
    
    -- Profitability ratios
    gross_profit_margin DECIMAL(5,2),
    net_profit_margin DECIMAL(5,2),
    return_on_assets DECIMAL(5,2),
    return_on_equity DECIMAL(5,2),
    
    -- Efficiency ratios
    inventory_turnover DECIMAL(5,2),
    receivables_turnover DECIMAL(5,2),
    payables_turnover DECIMAL(5,2),
    asset_turnover DECIMAL(5,2),
    
    -- Leverage ratios
    debt_ratio DECIMAL(5,2),
    debt_equity_ratio DECIMAL(5,2),
    interest_coverage DECIMAL(5,2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, period_type, period_date)
);

-- =============================================
-- SUCCESS MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
FINANCIAL & ACCOUNTING SCHEMA DEPLOYED
=============================================
✓ Financial Years & Periods
✓ Complete Ledger System
✓ Voucher Management
✓ Cost Centers
✓ Bill-wise Tracking
✓ Bank Reconciliation
✓ Budget Management
✓ GST Compliance (GSTR, E-invoice, E-way bill)
✓ TDS Management
✓ Financial Analytics

Total Financial Tables: 23+

Next: Deploy 01c_inventory_advanced_schema.sql
';
END $$;