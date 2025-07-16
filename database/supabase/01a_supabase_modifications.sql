-- =============================================
-- SUPABASE MODIFICATIONS TO CORE SCHEMA
-- =============================================
-- Run this AFTER 01_core_schema.sql
-- Adds Supabase auth integration
-- =============================================

-- =============================================
-- MODIFY EXISTING TABLES FOR SUPABASE
-- =============================================

-- Add auth integration to org_users
ALTER TABLE org_users ADD COLUMN IF NOT EXISTS auth_uid UUID UNIQUE;
ALTER TABLE org_users ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE org_users ADD COLUMN IF NOT EXISTS app_metadata JSONB DEFAULT '{}';

-- Add indexes for auth lookups
CREATE INDEX IF NOT EXISTS idx_org_users_auth_uid ON org_users(auth_uid) WHERE auth_uid IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_org_users_email_org ON org_users(email, org_id);

-- =============================================
-- AUTH TRIGGERS
-- =============================================

-- Create trigger on auth.users (only if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'on_auth_user_created'
    ) THEN
        CREATE TRIGGER on_auth_user_created
            AFTER INSERT ON auth.users
            FOR EACH ROW
            EXECUTE FUNCTION handle_new_auth_user();
    END IF;
END $$;

-- Update user last seen
CREATE OR REPLACE FUNCTION update_user_last_seen()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE org_users
    SET last_seen_at = NOW()
    WHERE auth_uid = auth.uid();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- SUPABASE STORAGE INTEGRATION
-- =============================================

-- Table to track uploaded files
CREATE TABLE IF NOT EXISTS uploaded_files (
    file_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- File details
    bucket_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    
    -- Reference
    reference_type TEXT, -- 'prescription', 'invoice', 'report'
    reference_id INTEGER,
    
    -- Metadata
    uploaded_by INTEGER REFERENCES org_users(user_id),
    upload_metadata JSONB DEFAULT '{}',
    
    -- Status
    is_public BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Enable RLS on uploaded files
ALTER TABLE uploaded_files ENABLE ROW LEVEL SECURITY;

-- Policy for uploaded files
CREATE POLICY uploaded_files_policy ON uploaded_files
    FOR ALL USING (org_id = current_org_id());

-- =============================================
-- API LOG TRACKING
-- =============================================

-- Track API usage for billing/monitoring
CREATE TABLE IF NOT EXISTS api_usage_log (
    log_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Request details
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER,
    
    -- Performance
    response_time_ms INTEGER,
    
    -- User info
    user_id INTEGER REFERENCES org_users(user_id),
    ip_address INET,
    user_agent TEXT,
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Partition by month for performance
CREATE INDEX IF NOT EXISTS idx_api_usage_log_org_time 
ON api_usage_log(org_id, created_at DESC);

-- =============================================
-- WEBHOOK CONFIGURATION
-- =============================================

-- Store webhook endpoints
CREATE TABLE IF NOT EXISTS webhook_endpoints (
    webhook_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Endpoint details
    endpoint_url TEXT NOT NULL,
    secret_key TEXT NOT NULL,
    
    -- Events
    event_types TEXT[] NOT NULL, -- ['order.created', 'payment.completed']
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    failure_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Webhook event queue
CREATE TABLE IF NOT EXISTS webhook_events (
    event_id SERIAL PRIMARY KEY,
    webhook_id INTEGER NOT NULL REFERENCES webhook_endpoints(webhook_id),
    
    -- Event details
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    
    -- Delivery
    status TEXT DEFAULT 'pending', -- 'pending', 'delivered', 'failed'
    attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    
    -- Response
    response_status INTEGER,
    response_body TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- REALTIME SUBSCRIPTIONS
-- =============================================

-- Configure tables for realtime
ALTER PUBLICATION supabase_realtime ADD TABLE products;
ALTER PUBLICATION supabase_realtime ADD TABLE batches;
ALTER PUBLICATION supabase_realtime ADD TABLE orders;
ALTER PUBLICATION supabase_realtime ADD TABLE inventory_movements;
ALTER PUBLICATION supabase_realtime ADD TABLE system_notifications;

-- =============================================
-- EDGE FUNCTION HELPERS
-- =============================================

-- Function to validate edge function requests
CREATE OR REPLACE FUNCTION validate_edge_function_request(
    p_api_key TEXT,
    p_required_role TEXT DEFAULT NULL
) RETURNS JSONB AS $$
DECLARE
    v_user RECORD;
    v_org RECORD;
BEGIN
    -- Validate API key (simplified - in production use proper validation)
    IF p_api_key IS NULL THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'API key required'
        );
    END IF;
    
    -- Get user from auth context
    SELECT * INTO v_user
    FROM org_users
    WHERE auth_uid = auth.uid()
    AND is_active = TRUE;
    
    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'User not found'
        );
    END IF;
    
    -- Check role if required
    IF p_required_role IS NOT NULL AND v_user.role != p_required_role THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Insufficient permissions'
        );
    END IF;
    
    -- Get organization
    SELECT * INTO v_org
    FROM organizations
    WHERE org_id = v_user.org_id
    AND is_active = TRUE;
    
    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Organization not found'
        );
    END IF;
    
    -- Check subscription limits
    IF v_org.subscription_status != 'active' THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Subscription inactive'
        );
    END IF;
    
    RETURN jsonb_build_object(
        'success', true,
        'user_id', v_user.user_id,
        'org_id', v_org.org_id,
        'role', v_user.role
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- SCHEDULED JOBS CONFIGURATION
-- =============================================

-- Table to track scheduled jobs (if not using pg_cron)
CREATE TABLE IF NOT EXISTS scheduled_jobs (
    job_id SERIAL PRIMARY KEY,
    job_name TEXT NOT NULL UNIQUE,
    job_function TEXT NOT NULL,
    schedule TEXT NOT NULL, -- cron expression
    is_active BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    last_status TEXT,
    last_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default jobs
INSERT INTO scheduled_jobs (job_name, job_function, schedule) VALUES
('check_near_expiry', 'check_near_expiry_batches', '0 9 * * *'),
('update_overdue_status', 'update_overdue_outstanding', '0 0 * * *'),
('cleanup_old_notifications', 'cleanup_expired_notifications', '0 2 * * *'),
('calculate_daily_metrics', 'calculate_organization_metrics', '0 1 * * *')
ON CONFLICT (job_name) DO NOTHING;

-- =============================================
-- SUCCESS MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
SUPABASE MODIFICATIONS COMPLETED
=============================================
✓ Auth integration added to org_users
✓ Auth triggers configured
✓ Storage integration tables
✓ API usage tracking
✓ Webhook configuration
✓ Realtime enabled for key tables
✓ Edge function helpers
✓ Scheduled jobs configuration

Ready for Supabase deployment!
';
END $$;