-- =====================================================
-- User Activity Logs Table
-- =====================================================
-- Tracks user actions for audit trail and analytics

CREATE TABLE IF NOT EXISTS user_activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id UUID REFERENCES user_sessions(id) ON DELETE SET NULL,
    
    -- Activity Information
    action VARCHAR(100) NOT NULL, -- 'login', 'logout', 'transaction_initiated', 'settings_updated', etc.
    resource VARCHAR(100), -- 'user_profile', 'transaction', 'settings', etc.
    resource_id VARCHAR(255), -- ID of the affected resource
    
    -- Request Information
    method VARCHAR(10), -- 'GET', 'POST', 'PUT', 'DELETE'
    endpoint VARCHAR(255),
    status_code INTEGER,
    
    -- Context
    description TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Location and Device
    ip_address INET,
    user_agent TEXT,
    device_id VARCHAR(255),
    location_lat DECIMAL(10,8),
    location_lng DECIMAL(11,8),
    
    -- Timing
    duration_ms INTEGER, -- How long the action took
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add RLS
ALTER TABLE user_activity_logs ENABLE ROW LEVEL SECURITY;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_session_id ON user_activity_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON user_activity_logs(action);
CREATE INDEX IF NOT EXISTS idx_activity_logs_resource ON user_activity_logs(resource);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON user_activity_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_activity_logs_ip_address ON user_activity_logs(ip_address);
CREATE INDEX IF NOT EXISTS idx_activity_logs_status_code ON user_activity_logs(status_code);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_action_date ON user_activity_logs(user_id, action, created_at);
CREATE INDEX IF NOT EXISTS idx_activity_logs_resource_date ON user_activity_logs(resource, resource_id, created_at); 