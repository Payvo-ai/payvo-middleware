-- =====================================================
-- User Sessions Table
-- =====================================================
-- Tracks user login sessions and activity

CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Session Information
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255),
    device_id VARCHAR(255),
    device_name VARCHAR(255),
    device_type VARCHAR(50), -- 'mobile', 'tablet', 'desktop', 'web'
    platform VARCHAR(50), -- 'ios', 'android', 'web', 'windows', 'macos'
    app_version VARCHAR(50),
    
    -- Location and Network Info
    ip_address INET,
    user_agent TEXT,
    location_country VARCHAR(2),
    location_city VARCHAR(100),
    timezone VARCHAR(50),
    
    -- Session Status
    is_active BOOLEAN DEFAULT true,
    is_trusted BOOLEAN DEFAULT false,
    
    -- Session Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    
    -- Security
    login_method VARCHAR(50), -- 'email', 'oauth', 'sso', 'magic_link'
    two_factor_verified BOOLEAN DEFAULT false,
    risk_score INTEGER DEFAULT 0, -- 0-100, higher = more risky
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add RLS
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_device_id ON user_sessions(device_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_started_at ON user_sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_last_activity ON user_sessions(last_activity_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_ip_address ON user_sessions(ip_address);

-- Add updated_at trigger
CREATE TRIGGER update_user_sessions_updated_at 
    BEFORE UPDATE ON user_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add constraint for risk score
ALTER TABLE user_sessions ADD CONSTRAINT risk_score_range 
    CHECK (risk_score >= 0 AND risk_score <= 100); 