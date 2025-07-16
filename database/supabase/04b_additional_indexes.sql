-- =============================================
-- PHARMACEUTICAL ERP - ADDITIONAL INDEXES
-- =============================================
-- Version: 1.0 - Production Ready
-- Description: Additional indexes for complete schema
-- Deploy Order: 4b - After core indexes
-- =============================================

-- =============================================
-- BARCODE INDEXES
-- =============================================

-- Barcode lookups
CREATE INDEX IF NOT EXISTS idx_barcode_master_org_value ON barcode_master(org_id, barcode_value);
CREATE INDEX IF NOT EXISTS idx_barcode_master_product ON barcode_master(product_id) WHERE product_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_barcode_master_batch ON barcode_master(batch_id) WHERE batch_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_barcode_master_active ON barcode_master(org_id, reference_type) WHERE is_active = TRUE;

-- Barcode sequences
CREATE INDEX IF NOT EXISTS idx_barcode_sequences_org_type ON barcode_sequences(org_id, sequence_type) WHERE is_active = TRUE;

-- =============================================
-- FINANCIAL INDEXES
-- =============================================

-- Chart of accounts
CREATE INDEX IF NOT EXISTS idx_chart_of_accounts_org ON chart_of_accounts(org_id);
CREATE INDEX IF NOT EXISTS idx_chart_of_accounts_parent ON chart_of_accounts(parent_account_id) WHERE parent_account_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_chart_of_accounts_type ON chart_of_accounts(org_id, account_type);
CREATE INDEX IF NOT EXISTS idx_chart_of_accounts_active ON chart_of_accounts(org_id, is_active);

-- Journal entries
CREATE INDEX IF NOT EXISTS idx_journal_entries_org_date ON journal_entries(org_id, entry_date);
CREATE INDEX IF NOT EXISTS idx_journal_entries_posted ON journal_entries(org_id, is_posted);
CREATE INDEX IF NOT EXISTS idx_journal_entries_reference ON journal_entries(reference_type, reference_id) WHERE reference_type IS NOT NULL;

-- Journal entry lines
CREATE INDEX IF NOT EXISTS idx_journal_entry_lines_entry ON journal_entry_lines(entry_id);
CREATE INDEX IF NOT EXISTS idx_journal_entry_lines_account ON journal_entry_lines(account_id);

-- =============================================
-- SESSION & ACTIVITY INDEXES
-- =============================================

-- User sessions
CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at) WHERE is_active = TRUE;

-- Activity log
CREATE INDEX IF NOT EXISTS idx_activity_log_org_date ON activity_log(org_id, created_at);
CREATE INDEX IF NOT EXISTS idx_activity_log_user ON activity_log(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_activity_log_table ON activity_log(table_name, record_id) WHERE table_name IS NOT NULL;

-- =============================================
-- EMAIL QUEUE INDEXES
-- =============================================

-- Email queue processing
CREATE INDEX IF NOT EXISTS idx_email_queue_pending ON email_queue(scheduled_for, priority) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_email_queue_org ON email_queue(org_id) WHERE org_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_email_queue_status ON email_queue(status, created_at);

-- =============================================
-- SUPPLIER OUTSTANDING INDEXES
-- =============================================

-- Supplier outstanding
CREATE INDEX IF NOT EXISTS idx_supplier_outstanding_org ON supplier_outstanding(org_id);
CREATE INDEX IF NOT EXISTS idx_supplier_outstanding_supplier ON supplier_outstanding(supplier_id);
CREATE INDEX IF NOT EXISTS idx_supplier_outstanding_status ON supplier_outstanding(org_id, status);
CREATE INDEX IF NOT EXISTS idx_supplier_outstanding_due ON supplier_outstanding(due_date) WHERE status IN ('pending', 'overdue');

-- =============================================
-- PURCHASE INDEXES
-- =============================================

-- Purchase items tracking
CREATE INDEX IF NOT EXISTS idx_purchase_items_pending ON purchase_items(purchase_id) WHERE item_status = 'pending';
CREATE INDEX IF NOT EXISTS idx_purchase_items_batch ON purchase_items(batch_number) WHERE batch_number IS NOT NULL;

-- =============================================
-- COMPOSITE INDEXES FOR REPORTS
-- =============================================

-- Financial reporting
CREATE INDEX IF NOT EXISTS idx_journal_financial_report ON journal_entries(org_id, entry_date, entry_type, is_posted) 
WHERE is_posted = TRUE;

-- Inventory valuation
CREATE INDEX IF NOT EXISTS idx_batches_valuation ON batches(org_id, product_id, cost_price, quantity_available) 
WHERE quantity_available > 0 AND batch_status = 'active';

-- Purchase analysis
CREATE INDEX IF NOT EXISTS idx_purchases_analysis ON purchases(org_id, supplier_id, purchase_date, purchase_status, final_amount)
WHERE purchase_status = 'received';

-- Outstanding aging
CREATE INDEX IF NOT EXISTS idx_customer_aging ON customer_outstanding(org_id, customer_id, days_overdue, outstanding_amount)
WHERE status IN ('pending', 'overdue') AND outstanding_amount > 0;

CREATE INDEX IF NOT EXISTS idx_supplier_aging ON supplier_outstanding(org_id, supplier_id, days_overdue, outstanding_amount)
WHERE status IN ('pending', 'overdue') AND outstanding_amount > 0;

-- =============================================
-- STATISTICS UPDATE
-- =============================================

-- Update statistics for new tables
ANALYZE barcode_master;
ANALYZE barcode_sequences;
ANALYZE chart_of_accounts;
ANALYZE journal_entries;
ANALYZE journal_entry_lines;
ANALYZE supplier_outstanding;
ANALYZE user_sessions;
ANALYZE activity_log;
ANALYZE system_settings;
ANALYZE email_queue;

-- =============================================
-- SUCCESS MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
ADDITIONAL INDEXES DEPLOYED SUCCESSFULLY
=============================================
✓ Barcode Indexes
✓ Financial Indexes
✓ Session & Activity Indexes
✓ Email Queue Indexes
✓ Supplier Outstanding Indexes
✓ Purchase Indexes
✓ Composite Report Indexes
✓ Statistics Updated

Next: Deploy 05_security_rls.sql
';
END $$;