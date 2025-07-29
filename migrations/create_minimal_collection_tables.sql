-- =============================================
-- MINIMAL COLLECTION CENTER TABLES
-- =============================================
-- Only creating tables that don't exist in production
-- Using existing: customer_outstanding, supplier_outstanding, email_queue, system_notifications
-- =============================================

-- SMS Queue (similar to email_queue but for SMS)
CREATE TABLE IF NOT EXISTS sms_queue (
    sms_id SERIAL PRIMARY KEY,
    org_id UUID,
    to_phone TEXT NOT NULL,
    message TEXT NOT NULL,
    template_id TEXT,
    
    -- SMS specific
    provider TEXT DEFAULT 'default', -- 'twilio', 'msg91', etc.
    message_type TEXT DEFAULT 'transactional', -- 'transactional', 'promotional'
    
    -- Status tracking
    status TEXT DEFAULT 'pending', -- 'pending', 'sent', 'delivered', 'failed'
    attempts INTEGER DEFAULT 0,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    
    -- Provider response
    provider_message_id TEXT,
    provider_status TEXT,
    error_message TEXT,
    cost DECIMAL(10,4),
    
    -- Reference
    reference_type TEXT, -- 'payment_reminder', 'order_update', etc.
    reference_id TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- WhatsApp Queue (for WhatsApp Business API)
CREATE TABLE IF NOT EXISTS whatsapp_queue (
    whatsapp_id SERIAL PRIMARY KEY,
    org_id UUID,
    to_phone TEXT NOT NULL,
    
    -- Message content
    message_type TEXT NOT NULL, -- 'text', 'template', 'media'
    content TEXT,
    template_name TEXT,
    template_params JSONB,
    media_url TEXT,
    
    -- Status tracking
    status TEXT DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    
    -- Provider details
    provider TEXT DEFAULT 'whatsapp_business',
    provider_message_id TEXT,
    provider_status TEXT,
    error_message TEXT,
    cost DECIMAL(10,4),
    
    -- Reference
    reference_type TEXT,
    reference_id TEXT,
    
    -- Conversation tracking
    conversation_id TEXT,
    is_reply BOOLEAN DEFAULT FALSE,
    reply_to_message_id TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Collection Reminders (links to customer_outstanding)
CREATE TABLE IF NOT EXISTS collection_reminders (
    reminder_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL,
    customer_id INTEGER NOT NULL,
    outstanding_id INTEGER REFERENCES customer_outstanding(outstanding_id),
    
    -- Reminder details
    reminder_type TEXT NOT NULL, -- 'sms', 'whatsapp', 'email', 'call'
    reminder_date DATE NOT NULL,
    reminder_time TIME,
    
    -- Message sent
    message_id INTEGER, -- Reference to sms_queue, whatsapp_queue, or email_queue
    message_content TEXT,
    
    -- Response tracking
    response_received BOOLEAN DEFAULT FALSE,
    response_date TIMESTAMP WITH TIME ZONE,
    response_type TEXT, -- 'payment', 'promise', 'dispute', 'callback'
    response_notes TEXT,
    
    -- Status
    status TEXT DEFAULT 'pending', -- 'pending', 'sent', 'delivered', 'failed'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID
);

-- Payment Promises
CREATE TABLE IF NOT EXISTS payment_promises (
    promise_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL,
    customer_id INTEGER NOT NULL,
    
    -- Promise details
    promise_date DATE NOT NULL,
    promised_amount DECIMAL(15,2) NOT NULL,
    
    -- Source
    source_type TEXT, -- 'reminder', 'call', 'visit', 'portal'
    source_id INTEGER, -- Reference to reminder_id
    
    -- Fulfillment
    status TEXT DEFAULT 'pending', -- 'pending', 'partial', 'fulfilled', 'broken'
    paid_amount DECIMAL(15,2) DEFAULT 0,
    payment_date DATE,
    payment_reference TEXT,
    
    -- Outstanding bills covered
    outstanding_ids INTEGER[],
    
    notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Collection Follow-ups
CREATE TABLE IF NOT EXISTS collection_followups (
    followup_id SERIAL PRIMARY KEY,
    reminder_id INTEGER REFERENCES collection_reminders(reminder_id),
    
    -- Follow-up details
    followup_date TIMESTAMP WITH TIME ZONE NOT NULL,
    followup_type TEXT NOT NULL, -- 'call', 'visit', 'email', 'whatsapp'
    
    -- Outcome
    outcome TEXT, -- 'promised_payment', 'dispute', 'no_response', 'payment_made'
    notes TEXT,
    
    -- Promise details if any
    promise_id INTEGER REFERENCES payment_promises(promise_id),
    
    -- Next action
    next_action TEXT,
    next_action_date DATE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID
);

-- Create indexes
CREATE INDEX idx_sms_queue_status ON sms_queue(status);
CREATE INDEX idx_sms_queue_org ON sms_queue(org_id);
CREATE INDEX idx_whatsapp_queue_status ON whatsapp_queue(status);
CREATE INDEX idx_whatsapp_queue_org ON whatsapp_queue(org_id);
CREATE INDEX idx_collection_reminders_customer ON collection_reminders(customer_id);
CREATE INDEX idx_collection_reminders_date ON collection_reminders(reminder_date);
CREATE INDEX idx_payment_promises_customer ON payment_promises(customer_id);
CREATE INDEX idx_payment_promises_status ON payment_promises(status);

-- Create a view to combine all outstanding (customer + supplier)
CREATE OR REPLACE VIEW all_outstanding AS
SELECT 
    'customer' as party_type,
    customer_id as party_id,
    outstanding_id,
    org_id,
    invoice_number,
    invoice_date,
    total_amount,
    paid_amount,
    outstanding_amount,
    due_date,
    days_overdue,
    status,
    notes
FROM customer_outstanding
UNION ALL
SELECT 
    'supplier' as party_type,
    supplier_id as party_id,
    outstanding_id,
    org_id,
    invoice_number,
    invoice_date,
    total_amount,
    paid_amount,
    outstanding_amount,
    due_date,
    days_overdue,
    status,
    notes
FROM supplier_outstanding;

-- Function to update days overdue
CREATE OR REPLACE FUNCTION update_days_overdue()
RETURNS VOID AS $$
BEGIN
    -- Update customer outstanding
    UPDATE customer_outstanding
    SET days_overdue = GREATEST(0, CURRENT_DATE - due_date)
    WHERE status IN ('pending', 'partial');
    
    -- Update supplier outstanding
    UPDATE supplier_outstanding
    SET days_overdue = GREATEST(0, CURRENT_DATE - due_date)
    WHERE status IN ('pending', 'partial');
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update outstanding when payment is made
CREATE OR REPLACE FUNCTION update_outstanding_on_payment()
RETURNS TRIGGER AS $$
BEGIN
    -- This would be called from payment processing
    -- Update logic would go here based on your payment structure
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add comments
COMMENT ON TABLE sms_queue IS 'Queue for SMS messages similar to email_queue';
COMMENT ON TABLE whatsapp_queue IS 'Queue for WhatsApp messages';
COMMENT ON TABLE collection_reminders IS 'Tracks collection reminders sent to customers';
COMMENT ON TABLE payment_promises IS 'Tracks payment promises made by customers';
COMMENT ON TABLE collection_followups IS 'Follow-up actions on collection reminders';