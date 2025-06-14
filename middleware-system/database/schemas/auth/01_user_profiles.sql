-- =====================================================
-- User Profiles Table
-- =====================================================
-- Extends auth.users with additional user information
-- This table has a 1:1 relationship with auth.users

CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username VARCHAR(50) UNIQUE,
    full_name VARCHAR(255),
    avatar_url TEXT,
    phone VARCHAR(20),
    date_of_birth DATE,
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    
    -- Employee/Organization Info
    employee_id VARCHAR(50) UNIQUE,
    department VARCHAR(100),
    role VARCHAR(100),
    manager_id UUID REFERENCES user_profiles(id),
    
    -- App Preferences
    preferences JSONB DEFAULT '{
        "notifications": {
            "email": true,
            "push": true,
            "transaction_alerts": true,
            "weekly_summary": true
        },
        "privacy": {
            "location_tracking": true,
            "analytics": true,
            "data_sharing": false
        },
        "app_settings": {
            "theme": "light",
            "currency": "USD",
            "auto_refresh": true,
            "refresh_interval": 30
        }
    }'::jsonb,
    
    -- Status and Metadata
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login_at TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_username ON user_profiles(username);
CREATE INDEX IF NOT EXISTS idx_user_profiles_employee_id ON user_profiles(employee_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_department ON user_profiles(department);
CREATE INDEX IF NOT EXISTS idx_user_profiles_is_active ON user_profiles(is_active);
CREATE INDEX IF NOT EXISTS idx_user_profiles_created_at ON user_profiles(created_at);

-- Add updated_at trigger
CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON user_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add constraint for username format
ALTER TABLE user_profiles ADD CONSTRAINT username_format 
    CHECK (username ~ '^[a-zA-Z0-9_-]{2,50}$');

-- Add constraint for phone format (basic validation)
ALTER TABLE user_profiles ADD CONSTRAINT phone_format 
    CHECK (phone IS NULL OR phone ~ '^\+?[1-9]\d{1,14}$'); 