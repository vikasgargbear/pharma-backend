-- =============================================
-- COLLECTION CENTER TABLES
-- =============================================
-- For managing receivables collection and reminders
-- =============================================

-- Collection campaigns to group reminders
CREATE TABLE IF NOT EXISTS collection_campaigns (
    campaign_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Campaign details
    campaign_name TEXT NOT NULL,
    campaign_type TEXT NOT NULL, -- 'scheduled', 'manual', 'automatic'
    
    -- Target criteria
    target_criteria JSONB, -- Store complex filtering criteria
    min_days_overdue INTEGER,
    max_days_overdue INTEGER,
    min_amount DECIMAL(15,2),
    max_amount DECIMAL(15,2),
    customer_types TEXT[], -- Array of customer types to target
    
    -- Schedule
    frequency TEXT, -- 'daily', 'weekly', 'monthly', 'one-time'
    schedule_time TIME,
    schedule_days INTEGER[], -- Days of week (1-7) or month (1-31)
    next_run_date DATE,
    last_run_date DATE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    total_customers INTEGER DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID
);

-- Reminder templates for different channels
CREATE TABLE IF NOT EXISTS reminder_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Template details
    template_name TEXT NOT NULL,
    template_type TEXT NOT NULL, -- 'sms', 'whatsapp', 'email', 'call_script'
    
    -- Content with variables
    subject TEXT, -- For email
    content TEXT NOT NULL, -- Template with {{variables}}
    
    -- Variables available: {{customer_name}}, {{amount}}, {{days_overdue}}, {{invoice_numbers}}, {{company_name}}
    
    -- Settings
    language TEXT DEFAULT 'en',
    is_default BOOLEAN DEFAULT FALSE,
    
    -- Usage stats
    times_used INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, template_name)
);

-- Enhanced collection reminders with campaign support
CREATE TABLE IF NOT EXISTS collection_reminders_v2 (
    reminder_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    campaign_id UUID REFERENCES collection_campaigns(campaign_id),
    
    -- Party details
    party_id UUID NOT NULL,
    party_type TEXT NOT NULL DEFAULT 'customer',
    
    -- Reminder details
    reminder_type TEXT NOT NULL, -- 'sms', 'whatsapp', 'email', 'call'
    reminder_date DATE NOT NULL,
    reminder_time TIME,
    template_id UUID REFERENCES reminder_templates(template_id),
    
    -- Message details
    message_content TEXT NOT NULL, -- Rendered message
    phone_number TEXT,
    email_address TEXT,
    
    -- Outstanding details at time of reminder
    outstanding_amount DECIMAL(15,2),
    oldest_invoice_days INTEGER,
    invoice_count INTEGER,
    invoice_numbers TEXT[], -- Array of invoice numbers
    
    -- Delivery status
    status TEXT DEFAULT 'pending', -- 'pending', 'queued', 'sent', 'delivered', 'failed', 'cancelled'
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    failure_reason TEXT,
    
    -- Provider details
    provider TEXT, -- 'twilio', 'msg91', 'sendgrid', etc.
    provider_message_id TEXT,
    provider_status TEXT,
    delivery_cost DECIMAL(10,4),
    
    -- Response tracking
    response_received BOOLEAN DEFAULT FALSE,
    response_date DATE,
    response_type TEXT, -- 'payment', 'promise', 'dispute', 'callback_request'
    response_notes TEXT,
    promised_date DATE,
    promised_amount DECIMAL(15,2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    
    -- Indexes
    CONSTRAINT reminder_delivery_check CHECK (
        status IN ('pending', 'queued', 'sent', 'delivered', 'failed', 'cancelled')
    )
);

-- Create indexes for performance
CREATE INDEX idx_reminders_v2_party ON collection_reminders_v2(party_id);
CREATE INDEX idx_reminders_v2_status ON collection_reminders_v2(status);
CREATE INDEX idx_reminders_v2_date ON collection_reminders_v2(reminder_date);
CREATE INDEX idx_reminders_v2_campaign ON collection_reminders_v2(campaign_id);

-- Collection follow-ups
CREATE TABLE IF NOT EXISTS collection_followups (
    followup_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reminder_id UUID NOT NULL REFERENCES collection_reminders_v2(reminder_id),
    
    -- Follow-up details
    followup_date TIMESTAMP WITH TIME ZONE NOT NULL,
    followup_type TEXT NOT NULL, -- 'call', 'visit', 'email', 'whatsapp'
    
    -- Outcome
    outcome TEXT, -- 'promised_payment', 'dispute', 'no_response', 'payment_made'
    notes TEXT,
    
    -- Promise details
    promised_amount DECIMAL(15,2),
    promised_date DATE,
    
    -- Next action
    next_action TEXT,
    next_action_date DATE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID
);

-- Payment promises tracking
CREATE TABLE IF NOT EXISTS payment_promises (
    promise_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Party details
    party_id UUID NOT NULL,
    party_type TEXT NOT NULL DEFAULT 'customer',
    
    -- Promise details
    promise_date DATE NOT NULL,
    promised_amount DECIMAL(15,2) NOT NULL,
    
    -- Source
    source_type TEXT, -- 'reminder', 'call', 'visit', 'customer_portal'
    source_id UUID, -- Reference to reminder_id or followup_id
    
    -- Fulfillment
    status TEXT DEFAULT 'pending', -- 'pending', 'partial', 'fulfilled', 'broken'
    paid_amount DECIMAL(15,2) DEFAULT 0,
    payment_date DATE,
    payment_reference TEXT,
    
    -- Notes
    notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- WhatsApp conversation tracking
CREATE TABLE IF NOT EXISTS whatsapp_conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Party details
    party_id UUID NOT NULL,
    phone_number TEXT NOT NULL,
    
    -- WhatsApp details
    whatsapp_chat_id TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_message_at TIMESTAMP WITH TIME ZONE,
    
    -- Opt-out tracking
    opted_out BOOLEAN DEFAULT FALSE,
    opted_out_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- WhatsApp messages
CREATE TABLE IF NOT EXISTS whatsapp_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES whatsapp_conversations(conversation_id),
    reminder_id UUID REFERENCES collection_reminders_v2(reminder_id),
    
    -- Message details
    direction TEXT NOT NULL, -- 'outbound', 'inbound'
    message_type TEXT NOT NULL, -- 'text', 'template', 'media'
    content TEXT,
    media_url TEXT,
    
    -- WhatsApp details
    whatsapp_message_id TEXT,
    status TEXT, -- 'queued', 'sent', 'delivered', 'read', 'failed'
    
    -- Timestamps
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Collection performance metrics
CREATE TABLE IF NOT EXISTS collection_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Period
    metric_date DATE NOT NULL,
    metric_type TEXT NOT NULL, -- 'daily', 'weekly', 'monthly'
    
    -- Reminder metrics
    reminders_sent INTEGER DEFAULT 0,
    reminders_delivered INTEGER DEFAULT 0,
    reminders_failed INTEGER DEFAULT 0,
    
    -- Response metrics
    responses_received INTEGER DEFAULT 0,
    payments_received INTEGER DEFAULT 0,
    promises_made INTEGER DEFAULT 0,
    
    -- Amount metrics
    total_outstanding DECIMAL(15,2) DEFAULT 0,
    amount_collected DECIMAL(15,2) DEFAULT 0,
    amount_promised DECIMAL(15,2) DEFAULT 0,
    
    -- Efficiency metrics
    response_rate DECIMAL(5,2), -- Percentage
    collection_rate DECIMAL(5,2), -- Percentage
    promise_fulfillment_rate DECIMAL(5,2), -- Percentage
    
    -- Cost metrics
    total_reminder_cost DECIMAL(10,2) DEFAULT 0,
    cost_per_collection DECIMAL(10,2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, metric_date, metric_type)
);

-- Default reminder templates
INSERT INTO reminder_templates (org_id, template_name, template_type, content, is_default) VALUES
('12de5e22-eee7-4d25-b3a7-d16d01c6170f', 'Friendly Payment Reminder', 'whatsapp', 
'Dear {{customer_name}},

This is a friendly reminder that your payment of ₹{{amount}} is overdue by {{days_overdue}} days.

Invoice(s): {{invoice_numbers}}

Please make the payment at your earliest convenience to avoid any service interruption.

Thank you,
{{company_name}}', true),

('12de5e22-eee7-4d25-b3a7-d16d01c6170f', 'SMS Payment Reminder', 'sms', 
'Dear {{customer_name}}, your payment of Rs.{{amount}} is overdue by {{days_overdue}} days. Please pay immediately. {{company_name}}', true),

('12de5e22-eee7-4d25-b3a7-d16d01c6170f', 'Email Payment Reminder', 'email', 
'Dear {{customer_name}},

We hope this email finds you well.

We would like to bring to your attention that your account has an outstanding balance of ₹{{amount}} which is overdue by {{days_overdue}} days.

Invoice Details: {{invoice_numbers}}

We request you to kindly clear the outstanding amount at your earliest convenience to maintain a healthy business relationship.

If you have already made the payment, please ignore this reminder and share the payment details with us.

For any queries or clarifications, please feel free to contact us.

Best Regards,
{{company_name}}', true);

-- Create function to calculate collection metrics
CREATE OR REPLACE FUNCTION calculate_collection_metrics(
    p_org_id UUID,
    p_date DATE,
    p_type TEXT
) RETURNS VOID AS $$
DECLARE
    v_start_date DATE;
    v_end_date DATE;
    v_metrics RECORD;
BEGIN
    -- Determine date range based on type
    CASE p_type
        WHEN 'daily' THEN
            v_start_date := p_date;
            v_end_date := p_date;
        WHEN 'weekly' THEN
            v_start_date := date_trunc('week', p_date);
            v_end_date := v_start_date + INTERVAL '6 days';
        WHEN 'monthly' THEN
            v_start_date := date_trunc('month', p_date);
            v_end_date := date_trunc('month', p_date + INTERVAL '1 month') - INTERVAL '1 day';
    END CASE;
    
    -- Calculate metrics
    WITH reminder_stats AS (
        SELECT 
            COUNT(*) FILTER (WHERE status IN ('sent', 'delivered')) as sent,
            COUNT(*) FILTER (WHERE status = 'delivered') as delivered,
            COUNT(*) FILTER (WHERE status = 'failed') as failed,
            COUNT(*) FILTER (WHERE response_received = TRUE) as responses,
            SUM(delivery_cost) as total_cost
        FROM collection_reminders_v2
        WHERE org_id = p_org_id
        AND reminder_date BETWEEN v_start_date AND v_end_date
    ),
    payment_stats AS (
        SELECT 
            COUNT(DISTINCT party_id) as customers_paid,
            SUM(credit_amount) as amount_collected
        FROM party_ledger
        WHERE org_id = p_org_id
        AND transaction_date BETWEEN v_start_date AND v_end_date
        AND transaction_type = 'payment'
        AND party_id IN (
            SELECT DISTINCT party_id 
            FROM collection_reminders_v2 
            WHERE reminder_date BETWEEN v_start_date AND v_end_date
        )
    ),
    promise_stats AS (
        SELECT 
            COUNT(*) as promises_made,
            SUM(promised_amount) as amount_promised,
            COUNT(*) FILTER (WHERE status = 'fulfilled') as promises_kept
        FROM payment_promises
        WHERE org_id = p_org_id
        AND created_at BETWEEN v_start_date AND v_end_date + INTERVAL '1 day'
    )
    SELECT * INTO v_metrics FROM reminder_stats, payment_stats, promise_stats;
    
    -- Insert or update metrics
    INSERT INTO collection_metrics (
        org_id, metric_date, metric_type,
        reminders_sent, reminders_delivered, reminders_failed,
        responses_received, payments_received, promises_made,
        amount_collected, amount_promised,
        response_rate, promise_fulfillment_rate,
        total_reminder_cost
    ) VALUES (
        p_org_id, p_date, p_type,
        v_metrics.sent, v_metrics.delivered, v_metrics.failed,
        v_metrics.responses, v_metrics.customers_paid, v_metrics.promises_made,
        v_metrics.amount_collected, v_metrics.amount_promised,
        CASE WHEN v_metrics.sent > 0 THEN (v_metrics.responses::DECIMAL / v_metrics.sent) * 100 ELSE 0 END,
        CASE WHEN v_metrics.promises_made > 0 THEN (v_metrics.promises_kept::DECIMAL / v_metrics.promises_made) * 100 ELSE 0 END,
        COALESCE(v_metrics.total_cost, 0)
    )
    ON CONFLICT (org_id, metric_date, metric_type)
    DO UPDATE SET
        reminders_sent = EXCLUDED.reminders_sent,
        reminders_delivered = EXCLUDED.reminders_delivered,
        reminders_failed = EXCLUDED.reminders_failed,
        responses_received = EXCLUDED.responses_received,
        payments_received = EXCLUDED.payments_received,
        promises_made = EXCLUDED.promises_made,
        amount_collected = EXCLUDED.amount_collected,
        amount_promised = EXCLUDED.amount_promised,
        response_rate = EXCLUDED.response_rate,
        promise_fulfillment_rate = EXCLUDED.promise_fulfillment_rate,
        total_reminder_cost = EXCLUDED.total_reminder_cost,
        created_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Add comments
COMMENT ON TABLE collection_campaigns IS 'Manages collection reminder campaigns with targeting criteria';
COMMENT ON TABLE reminder_templates IS 'Stores message templates for different communication channels';
COMMENT ON TABLE collection_reminders_v2 IS 'Enhanced reminder tracking with delivery status and response monitoring';
COMMENT ON TABLE whatsapp_conversations IS 'Tracks WhatsApp conversations for two-way communication';
COMMENT ON TABLE collection_metrics IS 'Performance metrics for collection activities';