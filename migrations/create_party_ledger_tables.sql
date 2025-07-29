-- =============================================
-- PARTY LEDGER TABLES
-- =============================================
-- For tracking customer and supplier transactions
-- =============================================

-- Create party_ledger table for tracking all financial transactions
CREATE TABLE IF NOT EXISTS party_ledger (
    ledger_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Party details
    party_id UUID NOT NULL,
    party_type TEXT NOT NULL CHECK (party_type IN ('customer', 'supplier')),
    
    -- Transaction details
    transaction_date DATE NOT NULL,
    transaction_type TEXT NOT NULL, -- 'invoice', 'payment', 'credit_note', 'debit_note', 'adjustment', 'opening_balance'
    
    -- Reference to source document
    reference_type TEXT, -- 'sale', 'purchase', 'payment', 'receipt', 'sale_return', 'purchase_return'
    reference_id TEXT, -- ID of the source document
    reference_number TEXT, -- Invoice/Payment number
    
    -- Amounts
    debit_amount DECIMAL(15,2) DEFAULT 0,
    credit_amount DECIMAL(15,2) DEFAULT 0,
    
    -- Running balance (denormalized for performance)
    running_balance DECIMAL(15,2) DEFAULT 0,
    balance_type TEXT DEFAULT 'Dr', -- 'Dr' or 'Cr'
    
    -- Additional details
    description TEXT,
    narration TEXT,
    
    -- Cheque/online payment details
    payment_mode TEXT,
    instrument_number TEXT,
    instrument_date DATE,
    bank_name TEXT,
    
    -- Status
    is_reconciled BOOLEAN DEFAULT FALSE,
    reconciliation_date DATE,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID,
    
    -- Indexes
    CONSTRAINT party_ledger_amounts_check CHECK (
        (debit_amount = 0 AND credit_amount >= 0) OR 
        (credit_amount = 0 AND debit_amount >= 0)
    )
);

-- Create indexes for performance
CREATE INDEX idx_party_ledger_party_id ON party_ledger(party_id);
CREATE INDEX idx_party_ledger_org_party ON party_ledger(org_id, party_id);
CREATE INDEX idx_party_ledger_transaction_date ON party_ledger(transaction_date DESC);
CREATE INDEX idx_party_ledger_reference ON party_ledger(reference_type, reference_id);
CREATE INDEX idx_party_ledger_party_date ON party_ledger(party_id, transaction_date DESC);

-- Create party_balances view for current balances
CREATE OR REPLACE VIEW party_balances AS
SELECT 
    pl.org_id,
    pl.party_id,
    pl.party_type,
    CASE 
        WHEN pl.party_type = 'customer' THEN c.customer_name
        WHEN pl.party_type = 'supplier' THEN s.supplier_name
    END as party_name,
    CASE 
        WHEN pl.party_type = 'customer' THEN c.phone
        WHEN pl.party_type = 'supplier' THEN s.phone
    END as phone,
    COALESCE(SUM(pl.debit_amount - pl.credit_amount), 0) as balance,
    CASE 
        WHEN COALESCE(SUM(pl.debit_amount - pl.credit_amount), 0) >= 0 THEN 'Dr'
        ELSE 'Cr'
    END as balance_type,
    MAX(pl.transaction_date) as last_transaction_date,
    COUNT(*) as transaction_count
FROM party_ledger pl
LEFT JOIN customers c ON pl.party_type = 'customer' AND pl.party_id = c.customer_id
LEFT JOIN suppliers s ON pl.party_type = 'supplier' AND pl.party_id = s.supplier_id
GROUP BY pl.org_id, pl.party_id, pl.party_type, c.customer_name, s.supplier_name, c.phone, s.phone;

-- Create outstanding bills tracking
CREATE TABLE IF NOT EXISTS outstanding_bills (
    bill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Party details
    party_id UUID NOT NULL,
    party_type TEXT NOT NULL CHECK (party_type IN ('customer', 'supplier')),
    
    -- Bill details
    bill_type TEXT NOT NULL, -- 'invoice', 'purchase_bill', 'credit_note', 'debit_note'
    bill_number TEXT NOT NULL,
    bill_date DATE NOT NULL,
    due_date DATE,
    
    -- Reference
    reference_type TEXT,
    reference_id TEXT,
    
    -- Amounts
    bill_amount DECIMAL(15,2) NOT NULL,
    paid_amount DECIMAL(15,2) DEFAULT 0,
    outstanding_amount DECIMAL(15,2) GENERATED ALWAYS AS (bill_amount - paid_amount) STORED,
    
    -- Status
    status TEXT DEFAULT 'outstanding', -- 'outstanding', 'partial', 'paid', 'overdue'
    
    -- Aging (updated via trigger)
    days_overdue INTEGER DEFAULT 0,
    aging_bucket TEXT, -- '0-30', '31-60', '61-90', '91-120', '>120'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, bill_number)
);

-- Create indexes
CREATE INDEX idx_outstanding_bills_party ON outstanding_bills(party_id);
CREATE INDEX idx_outstanding_bills_status ON outstanding_bills(status);
CREATE INDEX idx_outstanding_bills_due_date ON outstanding_bills(due_date);
CREATE INDEX idx_outstanding_bills_aging ON outstanding_bills(days_overdue);

-- Create payment allocations table
CREATE TABLE IF NOT EXISTS payment_allocations (
    allocation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Payment reference
    payment_ledger_id UUID NOT NULL REFERENCES party_ledger(ledger_id),
    
    -- Bill being paid
    bill_id UUID NOT NULL REFERENCES outstanding_bills(bill_id),
    
    -- Allocation details
    allocated_amount DECIMAL(15,2) NOT NULL,
    allocation_date DATE NOT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT payment_allocation_amount_check CHECK (allocated_amount > 0)
);

-- Create aging analysis view
CREATE OR REPLACE VIEW aging_analysis AS
SELECT 
    ob.org_id,
    ob.party_id,
    ob.party_type,
    CASE 
        WHEN ob.party_type = 'customer' THEN c.customer_name
        WHEN ob.party_type = 'supplier' THEN s.supplier_name
    END as party_name,
    SUM(CASE WHEN ob.days_overdue <= 0 THEN ob.outstanding_amount ELSE 0 END) as current_amount,
    SUM(CASE WHEN ob.days_overdue BETWEEN 1 AND 30 THEN ob.outstanding_amount ELSE 0 END) as overdue_0_30,
    SUM(CASE WHEN ob.days_overdue BETWEEN 31 AND 60 THEN ob.outstanding_amount ELSE 0 END) as overdue_31_60,
    SUM(CASE WHEN ob.days_overdue BETWEEN 61 AND 90 THEN ob.outstanding_amount ELSE 0 END) as overdue_61_90,
    SUM(CASE WHEN ob.days_overdue BETWEEN 91 AND 120 THEN ob.outstanding_amount ELSE 0 END) as overdue_91_120,
    SUM(CASE WHEN ob.days_overdue > 120 THEN ob.outstanding_amount ELSE 0 END) as overdue_above_120,
    SUM(ob.outstanding_amount) as total_outstanding,
    MAX(ob.days_overdue) as max_days_overdue
FROM outstanding_bills ob
LEFT JOIN customers c ON ob.party_type = 'customer' AND ob.party_id = c.customer_id
LEFT JOIN suppliers s ON ob.party_type = 'supplier' AND ob.party_id = s.supplier_id
WHERE ob.status IN ('outstanding', 'partial', 'overdue')
GROUP BY ob.org_id, ob.party_id, ob.party_type, c.customer_name, s.supplier_name;

-- Create collection reminders table
CREATE TABLE IF NOT EXISTS collection_reminders (
    reminder_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Party details
    party_id UUID NOT NULL,
    party_type TEXT NOT NULL DEFAULT 'customer',
    
    -- Reminder details
    reminder_type TEXT NOT NULL, -- 'sms', 'whatsapp', 'email', 'call'
    reminder_date DATE NOT NULL,
    reminder_time TIME,
    
    -- Message details
    message_template_id TEXT,
    message_content TEXT,
    
    -- Status
    status TEXT DEFAULT 'pending', -- 'pending', 'sent', 'failed', 'cancelled'
    sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Response
    response_received BOOLEAN DEFAULT FALSE,
    response_date DATE,
    response_notes TEXT,
    
    -- Amounts
    outstanding_amount DECIMAL(15,2),
    bills_count INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID
);

-- Create function to update running balance
CREATE OR REPLACE FUNCTION update_party_ledger_balance()
RETURNS TRIGGER AS $$
DECLARE
    v_prev_balance DECIMAL(15,2);
    v_balance_type TEXT;
BEGIN
    -- Get previous balance
    SELECT running_balance, balance_type
    INTO v_prev_balance, v_balance_type
    FROM party_ledger
    WHERE party_id = NEW.party_id
    AND transaction_date <= NEW.transaction_date
    AND ledger_id != NEW.ledger_id
    ORDER BY transaction_date DESC, created_at DESC
    LIMIT 1;
    
    -- If no previous balance, start from 0
    IF v_prev_balance IS NULL THEN
        v_prev_balance := 0;
        v_balance_type := 'Dr';
    END IF;
    
    -- Calculate new balance
    IF v_balance_type = 'Dr' THEN
        NEW.running_balance := v_prev_balance + NEW.debit_amount - NEW.credit_amount;
    ELSE
        NEW.running_balance := v_prev_balance + NEW.credit_amount - NEW.debit_amount;
    END IF;
    
    -- Determine balance type
    IF NEW.running_balance >= 0 THEN
        NEW.balance_type := v_balance_type;
    ELSE
        NEW.balance_type := CASE WHEN v_balance_type = 'Dr' THEN 'Cr' ELSE 'Dr' END;
        NEW.running_balance := ABS(NEW.running_balance);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for running balance
CREATE TRIGGER party_ledger_balance_trigger
BEFORE INSERT OR UPDATE ON party_ledger
FOR EACH ROW
EXECUTE FUNCTION update_party_ledger_balance();

-- Create function to update aging
CREATE OR REPLACE FUNCTION update_outstanding_bills_aging()
RETURNS TRIGGER AS $$
BEGIN
    NEW.days_overdue := GREATEST(0, CURRENT_DATE - NEW.due_date);
    
    NEW.aging_bucket := CASE
        WHEN NEW.days_overdue <= 0 THEN 'Current'
        WHEN NEW.days_overdue <= 30 THEN '0-30'
        WHEN NEW.days_overdue <= 60 THEN '31-60'
        WHEN NEW.days_overdue <= 90 THEN '61-90'
        WHEN NEW.days_overdue <= 120 THEN '91-120'
        ELSE '>120'
    END;
    
    -- Update status
    IF NEW.outstanding_amount <= 0 THEN
        NEW.status := 'paid';
    ELSIF NEW.paid_amount > 0 THEN
        NEW.status := 'partial';
    ELSIF NEW.days_overdue > 0 THEN
        NEW.status := 'overdue';
    ELSE
        NEW.status := 'outstanding';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for aging update
CREATE TRIGGER outstanding_bills_aging_trigger
BEFORE INSERT OR UPDATE ON outstanding_bills
FOR EACH ROW
EXECUTE FUNCTION update_outstanding_bills_aging();

-- Create scheduled job to update aging daily (to be run via cron or scheduler)
CREATE OR REPLACE FUNCTION update_all_bills_aging()
RETURNS VOID AS $$
BEGIN
    UPDATE outstanding_bills
    SET updated_at = CURRENT_TIMESTAMP
    WHERE status IN ('outstanding', 'partial', 'overdue');
END;
$$ LANGUAGE plpgsql;

-- Add comments
COMMENT ON TABLE party_ledger IS 'Comprehensive ledger for tracking all party transactions';
COMMENT ON TABLE outstanding_bills IS 'Tracks outstanding bills and their payment status';
COMMENT ON TABLE payment_allocations IS 'Maps payments to specific bills for reconciliation';
COMMENT ON TABLE collection_reminders IS 'Tracks collection reminders sent to customers';