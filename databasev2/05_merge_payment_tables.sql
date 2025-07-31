-- =====================================================
-- SCRIPT 05: Merge Payment Tables
-- Purpose: Consolidate all payment tracking into unified structure
-- =====================================================

BEGIN;

-- Step 1: Create unified payments table if not exists
CREATE TABLE IF NOT EXISTS payments (
    payment_id BIGSERIAL PRIMARY KEY,
    org_id UUID NOT NULL,
    payment_type VARCHAR(50) NOT NULL, -- 'customer_payment', 'vendor_payment', 'advance', 'refund'
    party_type VARCHAR(20) NOT NULL, -- 'customer', 'supplier'
    party_id INTEGER NOT NULL,
    payment_date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    payment_mode VARCHAR(50) NOT NULL,
    payment_reference VARCHAR(100),
    bank_name VARCHAR(100),
    bank_account VARCHAR(50),
    transaction_details JSONB,
    status VARCHAR(20) DEFAULT 'completed',
    notes TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 2: Create payment allocations table for invoice linkage
CREATE TABLE IF NOT EXISTS payment_allocations (
    allocation_id BIGSERIAL PRIMARY KEY,
    payment_id BIGINT REFERENCES payments(payment_id),
    invoice_type VARCHAR(20), -- 'sales_invoice', 'purchase_invoice'
    invoice_id INTEGER,
    allocated_amount DECIMAL(12,2) NOT NULL,
    allocation_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 3: Migrate customer payments from invoice_payments
INSERT INTO payments (
    org_id,
    payment_type,
    party_type,
    party_id,
    payment_date,
    amount,
    payment_mode,
    payment_reference,
    bank_name,
    transaction_details,
    status,
    notes,
    created_by,
    created_at
)
SELECT 
    i.org_id,
    'customer_payment' as payment_type,
    'customer' as party_type,
    i.customer_id as party_id,
    ip.payment_date,
    ip.amount,
    ip.payment_mode,
    ip.payment_reference,
    ip.bank_name,
    jsonb_build_object(
        'cheque_number', ip.cheque_number,
        'cheque_date', ip.cheque_date,
        'transaction_id', ip.transaction_id
    ) as transaction_details,
    CASE 
        WHEN ip.payment_status = 'completed' THEN 'completed'
        WHEN ip.payment_status = 'pending' THEN 'pending'
        ELSE 'completed'
    END as status,
    ip.notes,
    ip.created_by,
    ip.created_at
FROM invoice_payments ip
JOIN invoices i ON ip.invoice_id = i.invoice_id
WHERE NOT EXISTS (
    SELECT 1 FROM payments p 
    WHERE p.payment_reference = ip.payment_reference 
    AND p.payment_date = ip.payment_date
);

-- Step 4: Create payment allocations for migrated payments
INSERT INTO payment_allocations (
    payment_id,
    invoice_type,
    invoice_id,
    allocated_amount,
    allocation_date
)
SELECT 
    p.payment_id,
    'sales_invoice' as invoice_type,
    ip.invoice_id,
    ip.amount,
    ip.payment_date
FROM invoice_payments ip
JOIN invoices i ON ip.invoice_id = i.invoice_id
JOIN payments p ON p.payment_reference = ip.payment_reference 
    AND p.payment_date = ip.payment_date
    AND p.party_id = i.customer_id;

-- Step 5: Migrate vendor payments if exists
INSERT INTO payments (
    org_id,
    payment_type,
    party_type,
    party_id,
    payment_date,
    amount,
    payment_mode,
    payment_reference,
    bank_name,
    transaction_details,
    status,
    notes,
    created_by,
    created_at
)
SELECT 
    vp.org_id,
    'vendor_payment' as payment_type,
    'supplier' as party_type,
    vp.supplier_id as party_id,
    vp.payment_date,
    vp.amount,
    vp.payment_mode,
    vp.payment_reference,
    vp.bank_name,
    vp.transaction_details,
    vp.status,
    vp.notes,
    vp.created_by,
    vp.created_at
FROM vendor_payments vp
WHERE NOT EXISTS (
    SELECT 1 FROM payments p 
    WHERE p.payment_reference = vp.payment_reference 
    AND p.payment_date = vp.payment_date
);

-- Step 6: Migrate customer advances
INSERT INTO payments (
    org_id,
    payment_type,
    party_type,
    party_id,
    payment_date,
    amount,
    payment_mode,
    payment_reference,
    status,
    notes,
    created_at
)
SELECT 
    c.org_id,
    'advance' as payment_type,
    'customer' as party_type,
    cap.customer_id as party_id,
    p.payment_date,
    cap.advance_amount,
    p.payment_mode,
    p.payment_reference,
    cap.status,
    'Customer advance payment' as notes,
    cap.created_at
FROM customer_advance_payments cap
JOIN payments p ON cap.payment_id = p.payment_id
JOIN customers c ON cap.customer_id = c.customer_id
WHERE NOT EXISTS (
    SELECT 1 FROM payments p2 
    WHERE p2.payment_reference = p.payment_reference 
    AND p2.payment_type = 'advance'
);

-- Step 7: Create unified credit/debit notes table
CREATE TABLE IF NOT EXISTS credit_debit_notes (
    note_id BIGSERIAL PRIMARY KEY,
    org_id UUID NOT NULL,
    note_type VARCHAR(20) NOT NULL, -- 'credit', 'debit'
    party_type VARCHAR(20) NOT NULL, -- 'customer', 'supplier'
    party_id INTEGER NOT NULL,
    note_number VARCHAR(50) UNIQUE NOT NULL,
    note_date DATE NOT NULL,
    reference_type VARCHAR(50), -- 'invoice', 'purchase', 'return'
    reference_id INTEGER,
    amount DECIMAL(12,2) NOT NULL,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    total_amount DECIMAL(12,2) NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    used_amount DECIMAL(12,2) DEFAULT 0,
    balance_amount DECIMAL(12,2),
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 8: Migrate customer credit notes
INSERT INTO credit_debit_notes (
    org_id,
    note_type,
    party_type,
    party_id,
    note_number,
    note_date,
    reference_type,
    reference_id,
    amount,
    total_amount,
    reason,
    status,
    used_amount,
    balance_amount,
    created_at
)
SELECT 
    c.org_id,
    'credit' as note_type,
    'customer' as party_type,
    ccn.customer_id,
    'CN-' || ccn.credit_note_id as note_number,
    ccn.issue_date,
    CASE 
        WHEN ccn.order_id IS NOT NULL THEN 'order'
        ELSE ccn.credit_type
    END as reference_type,
    ccn.order_id as reference_id,
    ccn.credit_amount as amount,
    ccn.credit_amount as total_amount,
    ccn.reason,
    ccn.status,
    COALESCE(ccn.used_amount, 0),
    COALESCE(ccn.remaining_amount, ccn.credit_amount),
    ccn.created_at
FROM customer_credit_notes ccn
JOIN customers c ON ccn.customer_id = c.customer_id;

-- Step 9: Create payment summary views
CREATE OR REPLACE VIEW payment_summary AS
SELECT 
    p.org_id,
    p.party_type,
    p.party_id,
    CASE 
        WHEN p.party_type = 'customer' THEN c.customer_name
        WHEN p.party_type = 'supplier' THEN s.supplier_name
    END as party_name,
    COUNT(*) as total_payments,
    SUM(p.amount) as total_amount,
    SUM(CASE WHEN p.payment_type = 'advance' THEN p.amount ELSE 0 END) as advance_amount,
    MAX(p.payment_date) as last_payment_date
FROM payments p
LEFT JOIN customers c ON p.party_type = 'customer' AND p.party_id = c.customer_id
LEFT JOIN suppliers s ON p.party_type = 'supplier' AND p.party_id = s.supplier_id
GROUP BY p.org_id, p.party_type, p.party_id, c.customer_name, s.supplier_name;

-- Step 10: Create outstanding calculation view
CREATE OR REPLACE VIEW party_outstanding_summary AS
WITH invoice_totals AS (
    -- Customer invoices
    SELECT 
        i.org_id,
        'customer' as party_type,
        i.customer_id as party_id,
        SUM(i.total_amount) as total_invoiced
    FROM invoices i
    WHERE i.status != 'cancelled'
    GROUP BY i.org_id, i.customer_id
    
    UNION ALL
    
    -- Supplier invoices (purchases)
    SELECT 
        p.org_id,
        'supplier' as party_type,
        p.supplier_id as party_id,
        SUM(p.total_amount) as total_invoiced
    FROM purchases p
    WHERE p.status != 'cancelled'
    GROUP BY p.org_id, p.supplier_id
),
payment_totals AS (
    SELECT 
        org_id,
        party_type,
        party_id,
        SUM(amount) as total_paid
    FROM payments
    WHERE status = 'completed'
    GROUP BY org_id, party_type, party_id
),
credit_totals AS (
    SELECT 
        org_id,
        party_type,
        party_id,
        SUM(balance_amount) as total_credits
    FROM credit_debit_notes
    WHERE note_type = 'credit' AND status = 'active'
    GROUP BY org_id, party_type, party_id
)
SELECT 
    it.org_id,
    it.party_type,
    it.party_id,
    it.total_invoiced,
    COALESCE(pt.total_paid, 0) as total_paid,
    COALESCE(ct.total_credits, 0) as total_credits,
    it.total_invoiced - COALESCE(pt.total_paid, 0) - COALESCE(ct.total_credits, 0) as outstanding_amount
FROM invoice_totals it
LEFT JOIN payment_totals pt ON it.org_id = pt.org_id 
    AND it.party_type = pt.party_type 
    AND it.party_id = pt.party_id
LEFT JOIN credit_totals ct ON it.org_id = ct.org_id 
    AND it.party_type = ct.party_type 
    AND it.party_id = ct.party_id;

-- Step 11: Drop old tables (after verification)
-- DROP TABLE IF EXISTS invoice_payments CASCADE;
-- DROP TABLE IF EXISTS vendor_payments CASCADE;
-- DROP TABLE IF EXISTS customer_advance_payments CASCADE;
-- DROP TABLE IF EXISTS customer_credit_notes CASCADE;
-- DROP TABLE IF EXISTS payment_allocations CASCADE;  -- if old version exists
-- DROP TABLE IF EXISTS upi_payments CASCADE;

-- Step 12: Create indexes
CREATE INDEX idx_payments_party ON payments(party_type, party_id);
CREATE INDEX idx_payments_date ON payments(payment_date);
CREATE INDEX idx_payments_reference ON payments(payment_reference);
CREATE INDEX idx_payment_allocations_invoice ON payment_allocations(invoice_type, invoice_id);
CREATE INDEX idx_credit_notes_party ON credit_debit_notes(party_type, party_id);
CREATE INDEX idx_credit_notes_reference ON credit_debit_notes(reference_type, reference_id);

-- Log the consolidation
INSERT INTO activity_log (org_id, activity_type, activity_description, created_at)
SELECT 
    org_id,
    'PAYMENT_CONSOLIDATION',
    'Consolidated payment tables into unified structure',
    CURRENT_TIMESTAMP
FROM organizations
LIMIT 1;

COMMIT;