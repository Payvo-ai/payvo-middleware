-- =====================================================
-- Background Location Sessions Table
-- =====================================================
-- Manages active background location tracking sessions

CREATE TABLE IF NOT EXISTS background_location_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Session Configuration
    session_duration_minutes INTEGER DEFAULT 30,
    update_interval_seconds INTEGER DEFAULT 30,
    min_distance_filter_meters DECIMAL(8,2) DEFAULT 10.0,
    
    -- Session Status
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'paused', 'completed', 'expired', 'cancelled'
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timing
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    last_update TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Statistics
    location_count INTEGER DEFAULT 0,
    prediction_count INTEGER DEFAULT 0,
    total_distance_meters DECIMAL(10,2) DEFAULT 0,
    
    -- Configuration and Metadata
    metadata JSONB DEFAULT '{
        "device_info": {},
        "app_version": null,
        "settings": {}
    }'::jsonb,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add RLS
ALTER TABLE background_location_sessions ENABLE ROW LEVEL SECURITY;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_bg_sessions_user_id ON background_location_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_bg_sessions_status ON background_location_sessions(status);
CREATE INDEX IF NOT EXISTS idx_bg_sessions_is_active ON background_location_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_bg_sessions_expires_at ON background_location_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_bg_sessions_start_time ON background_location_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_bg_sessions_last_update ON background_location_sessions(last_update);

-- Composite indexes
CREATE INDEX IF NOT EXISTS idx_bg_sessions_user_active ON background_location_sessions(user_id, is_active, expires_at);
CREATE INDEX IF NOT EXISTS idx_bg_sessions_cleanup ON background_location_sessions(status, expires_at) WHERE status IN ('expired', 'completed');

-- Add updated_at trigger
CREATE TRIGGER update_bg_sessions_updated_at 
    BEFORE UPDATE ON background_location_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add constraints
ALTER TABLE background_location_sessions ADD CONSTRAINT session_duration_positive 
    CHECK (session_duration_minutes > 0 AND session_duration_minutes <= 1440); -- Max 24 hours

ALTER TABLE background_location_sessions ADD CONSTRAINT update_interval_positive 
    CHECK (update_interval_seconds > 0 AND update_interval_seconds <= 3600); -- Max 1 hour

ALTER TABLE background_location_sessions ADD CONSTRAINT distance_filter_positive 
    CHECK (min_distance_filter_meters >= 0 AND min_distance_filter_meters <= 1000); -- Max 1km 