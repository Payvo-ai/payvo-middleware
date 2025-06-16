-- =====================================================
-- Payvo Middleware Database Schema - Supabase Deployment
-- =====================================================
-- This consolidated script deploys the complete database schema
-- Execute this in Supabase SQL Editor to set up all tables, functions, and policies
--
-- AUTHENTICATION NOTES:
-- - Uses Supabase Auth for user management
-- - Email is used as the primary user identifier for transactions
-- - Username is optional and can be set in user preferences
-- - No password change requirement on first login
-- - Simplified sign-in flow: email + password only
--
-- DEPLOYMENT STEPS:
-- 1. Configure Supabase client with your project credentials
-- 2. Run this script in Supabase SQL Editor
-- 3. Use create_admin_user.sql to create initial admin account

-- =====================================================
-- 1. Setup and Extensions
-- =====================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis" SCHEMA extensions;

-- Create custom schemas if needed
CREATE SCHEMA IF NOT EXISTS payvo;

-- Set up timezone
SET timezone = 'UTC';

-- Create updated_at trigger function (used across multiple tables)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create location utility functions
CREATE OR REPLACE FUNCTION calculate_distance(
    lat1 DECIMAL(10,8),
    lng1 DECIMAL(11,8),
    lat2 DECIMAL(10,8),
    lng2 DECIMAL(11,8)
) RETURNS DECIMAL(10,2) AS $$
DECLARE
    earth_radius DECIMAL := 6371000; -- Earth radius in meters
    dlat DECIMAL;
    dlng DECIMAL;
    a DECIMAL;
    c DECIMAL;
BEGIN
    dlat := radians(lat2 - lat1);
    dlng := radians(lng2 - lng1);
    
    a := sin(dlat/2) * sin(dlat/2) + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2) * sin(dlng/2);
    c := 2 * atan2(sqrt(a), sqrt(1-a));
    
    RETURN earth_radius * c;
END;
$$ LANGUAGE plpgsql;

-- Create location hash function
CREATE OR REPLACE FUNCTION generate_location_hash(
    lat DECIMAL(10,8),
    lng DECIMAL(11,8),
    precision_meters INTEGER DEFAULT 50
) RETURNS VARCHAR(50) AS $$
DECLARE
    precision_factor DECIMAL;
    rounded_lat DECIMAL;
    rounded_lng DECIMAL;
BEGIN
    -- Calculate precision factor based on desired precision in meters
    -- Roughly 1 degree = 111,000 meters
    precision_factor := precision_meters / 111000.0;
    
    -- Round coordinates to the specified precision
    rounded_lat := ROUND(lat / precision_factor) * precision_factor;
    rounded_lng := ROUND(lng / precision_factor) * precision_factor;
    
    -- Generate hash
    RETURN MD5(rounded_lat::TEXT || ',' || rounded_lng::TEXT);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 2. Authentication Tables
-- =====================================================

-- User Profiles Table
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
    
    -- Password Management
    password_change_required BOOLEAN DEFAULT false,
    password_changed_at TIMESTAMP WITH TIME ZONE,
    
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

-- Enable RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_username ON user_profiles(username);
CREATE INDEX IF NOT EXISTS idx_user_profiles_employee_id ON user_profiles(employee_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_department ON user_profiles(department);
CREATE INDEX IF NOT EXISTS idx_user_profiles_is_active ON user_profiles(is_active);
CREATE INDEX IF NOT EXISTS idx_user_profiles_created_at ON user_profiles(created_at);

-- Add updated_at trigger
DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON user_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add constraint for username format
DO $$
BEGIN
    ALTER TABLE user_profiles ADD CONSTRAINT username_format 
        CHECK (username ~ '^[a-zA-Z0-9_-]{2,50}$');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Add constraint for phone format (basic validation)
DO $$
BEGIN
    ALTER TABLE user_profiles ADD CONSTRAINT phone_format 
        CHECK (phone IS NULL OR phone ~ '^\+?[1-9]\d{1,14}$');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- User Sessions Table
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

-- Enable RLS
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
DROP TRIGGER IF EXISTS update_user_sessions_updated_at ON user_sessions;
CREATE TRIGGER update_user_sessions_updated_at 
    BEFORE UPDATE ON user_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add constraint for risk score
DO $$
BEGIN
    ALTER TABLE user_sessions ADD CONSTRAINT risk_score_range 
        CHECK (risk_score >= 0 AND risk_score <= 100);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- User Activity Logs Table
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

-- Enable RLS
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

-- =====================================================
-- 3. Core Business Tables
-- =====================================================

-- Transaction Feedback Table
CREATE TABLE IF NOT EXISTS transaction_feedback (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_id UUID REFERENCES auth.users(id),
    predicted_mcc VARCHAR(4),
    actual_mcc VARCHAR(4),
    prediction_confidence DECIMAL(5,4),
    prediction_method VARCHAR(100),
    selected_card_id VARCHAR(255),
    network_used VARCHAR(50),
    transaction_success BOOLEAN,
    rewards_earned DECIMAL(10,2),
    transaction_amount DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    merchant_name VARCHAR(255),
    merchant_category VARCHAR(255),
    terminal_id VARCHAR(255),
    location_lat DECIMAL(10,8),
    location_lng DECIMAL(11,8),
    location_hash VARCHAR(255),
    location_accuracy DECIMAL(10,2),
    wifi_fingerprint TEXT,
    ble_fingerprint TEXT,
    context_features JSONB DEFAULT '{}',
    transaction_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE transaction_feedback ENABLE ROW LEVEL SECURITY;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_user_id ON transaction_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_session_id ON transaction_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_actual_mcc ON transaction_feedback(actual_mcc);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_created_at ON transaction_feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_location ON transaction_feedback(location_lat, location_lng);

-- Add updated_at trigger
DROP TRIGGER IF EXISTS update_transaction_feedback_updated_at ON transaction_feedback;
CREATE TRIGGER update_transaction_feedback_updated_at 
    BEFORE UPDATE ON transaction_feedback 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- MCC Predictions Table
CREATE TABLE IF NOT EXISTS mcc_predictions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    terminal_id VARCHAR(255),
    location_hash VARCHAR(255),
    wifi_fingerprint VARCHAR(255),
    ble_fingerprint VARCHAR(255),
    predicted_mcc VARCHAR(4) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    method_used VARCHAR(100) NOT NULL,
    context_features JSONB,
    location_lat DECIMAL(10,8),
    location_lng DECIMAL(11,8),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_mcc_predictions_session_id ON mcc_predictions(session_id);
CREATE INDEX IF NOT EXISTS idx_mcc_predictions_terminal_id ON mcc_predictions(terminal_id);
CREATE INDEX IF NOT EXISTS idx_mcc_predictions_location_hash ON mcc_predictions(location_hash);
CREATE INDEX IF NOT EXISTS idx_mcc_predictions_created_at ON mcc_predictions(created_at);

-- Card Performance Table
CREATE TABLE IF NOT EXISTS card_performance (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    card_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    mcc VARCHAR(4),
    network VARCHAR(50),
    transaction_success BOOLEAN NOT NULL,
    rewards_earned DECIMAL(10,2),
    transaction_amount DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    merchant_category VARCHAR(255),
    location_hash VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE card_performance ENABLE ROW LEVEL SECURITY;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_card_performance_user_id ON card_performance(user_id);
CREATE INDEX IF NOT EXISTS idx_card_performance_card_id ON card_performance(card_id);
CREATE INDEX IF NOT EXISTS idx_card_performance_mcc ON card_performance(mcc);
CREATE INDEX IF NOT EXISTS idx_card_performance_created_at ON card_performance(created_at);

-- User Preferences Table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    preferred_cards JSONB DEFAULT '[]',
    mcc_preferences JSONB DEFAULT '{}',
    network_preferences JSONB DEFAULT '{}',
    rewards_priority VARCHAR(50) DEFAULT 'cashback',
    risk_tolerance VARCHAR(50) DEFAULT 'medium',
    auto_routing BOOLEAN DEFAULT true,
    notification_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- Add updated_at trigger
DROP TRIGGER IF EXISTS update_user_preferences_updated_at ON user_preferences;
CREATE TRIGGER update_user_preferences_updated_at 
    BEFORE UPDATE ON user_preferences 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable RLS
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Location Intelligence Table
CREATE TABLE IF NOT EXISTS location_intelligence (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    location_hash VARCHAR(255) UNIQUE NOT NULL,
    location_lat DECIMAL(10,8) NOT NULL,
    location_lng DECIMAL(11,8) NOT NULL,
    dominant_mcc VARCHAR(4),
    mcc_distribution JSONB DEFAULT '{}',
    merchant_count INTEGER DEFAULT 0,
    confidence_score DECIMAL(5,4),
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_location_intelligence_hash ON location_intelligence(location_hash);
CREATE INDEX IF NOT EXISTS idx_location_intelligence_location ON location_intelligence(location_lat, location_lng);

-- Terminal Intelligence Table
CREATE TABLE IF NOT EXISTS terminal_intelligence (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    terminal_id VARCHAR(255) UNIQUE NOT NULL,
    confirmed_mcc VARCHAR(4),
    confidence_score DECIMAL(5,4),
    transaction_count INTEGER DEFAULT 0,
    location_hash VARCHAR(255),
    wifi_fingerprint VARCHAR(255),
    ble_fingerprint VARCHAR(255),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_terminal_intelligence_terminal_id ON terminal_intelligence(terminal_id);
CREATE INDEX IF NOT EXISTS idx_terminal_intelligence_location_hash ON terminal_intelligence(location_hash);

-- Session Analytics Table
CREATE TABLE IF NOT EXISTS session_analytics (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50),
    wallet_type VARCHAR(50),
    prediction_method VARCHAR(100),
    prediction_confidence DECIMAL(5,4),
    prediction_accuracy BOOLEAN,
    processing_time_ms INTEGER,
    data_sources_used JSONB DEFAULT '[]',
    location_precision VARCHAR(50),
    success BOOLEAN NOT NULL,
    error_type VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE session_analytics ENABLE ROW LEVEL SECURITY;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_session_analytics_user_id ON session_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_session_analytics_session_id ON session_analytics(session_id);
CREATE INDEX IF NOT EXISTS idx_session_analytics_created_at ON session_analytics(created_at);

-- System Analytics Table
CREATE TABLE IF NOT EXISTS system_analytics (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4),
    metric_unit VARCHAR(50),
    time_period VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_system_analytics_metric_name ON system_analytics(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_analytics_time_period ON system_analytics(time_period);

-- =====================================================
-- 4. Cache Tables
-- =====================================================

-- Terminal Cache Table
CREATE TABLE IF NOT EXISTS terminal_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    terminal_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- MCC Information
    mcc VARCHAR(4) NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 1.0,
    
    -- Merchant Information
    merchant_name VARCHAR(255),
    merchant_category VARCHAR(100),
    
    -- Statistics
    transaction_count INTEGER DEFAULT 1,
    success_count INTEGER DEFAULT 0,
    last_success_at TIMESTAMP WITH TIME ZONE,
    
    -- Location Context (optional)
    location_lat DECIMAL(10,8),
    location_lng DECIMAL(11,8),
    location_hash VARCHAR(50),
    
    -- Cache Management
    hit_count INTEGER DEFAULT 0,
    last_hit_at TIMESTAMP WITH TIME ZONE,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Validation
    is_verified BOOLEAN DEFAULT false,
    verification_source VARCHAR(50), -- 'manual', 'feedback', 'external_api'
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE terminal_cache ENABLE ROW LEVEL SECURITY;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_terminal_cache_terminal_id ON terminal_cache(terminal_id);
CREATE INDEX IF NOT EXISTS idx_terminal_cache_mcc ON terminal_cache(mcc);
CREATE INDEX IF NOT EXISTS idx_terminal_cache_confidence ON terminal_cache(confidence);
CREATE INDEX IF NOT EXISTS idx_terminal_cache_last_seen ON terminal_cache(last_seen);
CREATE INDEX IF NOT EXISTS idx_terminal_cache_transaction_count ON terminal_cache(transaction_count);
CREATE INDEX IF NOT EXISTS idx_terminal_cache_is_verified ON terminal_cache(is_verified);
CREATE INDEX IF NOT EXISTS idx_terminal_cache_location_hash ON terminal_cache(location_hash);

-- Composite indexes for performance
CREATE INDEX IF NOT EXISTS idx_terminal_cache_lookup ON terminal_cache(terminal_id, mcc, confidence) WHERE confidence > 0.5;
CREATE INDEX IF NOT EXISTS idx_terminal_cache_cleanup ON terminal_cache(last_seen, transaction_count) WHERE transaction_count < 5;

-- Add updated_at trigger
DROP TRIGGER IF EXISTS update_terminal_cache_updated_at ON terminal_cache;
CREATE TRIGGER update_terminal_cache_updated_at 
    BEFORE UPDATE ON terminal_cache 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add constraints
DO $$
BEGIN
    ALTER TABLE terminal_cache ADD CONSTRAINT confidence_range 
        CHECK (confidence >= 0.0 AND confidence <= 1.0);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    ALTER TABLE terminal_cache ADD CONSTRAINT transaction_count_positive 
        CHECK (transaction_count >= 0);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    ALTER TABLE terminal_cache ADD CONSTRAINT hit_count_positive 
        CHECK (hit_count >= 0);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Location Cache Table
CREATE TABLE IF NOT EXISTS location_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_hash VARCHAR(50) UNIQUE NOT NULL,
    
    -- Location Information
    location_lat DECIMAL(10,8) NOT NULL,
    location_lng DECIMAL(11,8) NOT NULL,
    precision_level INTEGER DEFAULT 3, -- Hash precision level
    radius_meters INTEGER DEFAULT 100,
    
    -- MCC Predictions
    predicted_mcc VARCHAR(4) NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 0.5,
    
    -- Context Information
    merchant_density INTEGER DEFAULT 0,
    dominant_category VARCHAR(100),
    business_hours JSONB DEFAULT '{}'::jsonb,
    
    -- Statistics
    prediction_count INTEGER DEFAULT 1,
    success_count INTEGER DEFAULT 0,
    accuracy_rate DECIMAL(3,2) DEFAULT 0.0,
    
    -- Cache Management
    hit_count INTEGER DEFAULT 0,
    last_hit_at TIMESTAMP WITH TIME ZONE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Validation
    is_verified BOOLEAN DEFAULT false,
    verification_source VARCHAR(50), -- 'manual', 'feedback', 'external_api'
    
    -- Environmental Context
    wifi_networks JSONB DEFAULT '[]'::jsonb,
    ble_beacons JSONB DEFAULT '[]'::jsonb,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE location_cache ENABLE ROW LEVEL SECURITY;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_location_cache_hash ON location_cache(location_hash);
CREATE INDEX IF NOT EXISTS idx_location_cache_mcc ON location_cache(predicted_mcc);
CREATE INDEX IF NOT EXISTS idx_location_cache_confidence ON location_cache(confidence);
CREATE INDEX IF NOT EXISTS idx_location_cache_last_updated ON location_cache(last_updated);
CREATE INDEX IF NOT EXISTS idx_location_cache_prediction_count ON location_cache(prediction_count);
CREATE INDEX IF NOT EXISTS idx_location_cache_is_verified ON location_cache(is_verified);

-- Spatial index for location queries
CREATE INDEX IF NOT EXISTS idx_location_cache_spatial ON location_cache USING GIST (
    ST_Point(location_lng, location_lat)
);

-- Composite indexes for performance
CREATE INDEX IF NOT EXISTS idx_location_cache_lookup ON location_cache(location_hash, predicted_mcc, confidence) 
    WHERE confidence > 0.3;
CREATE INDEX IF NOT EXISTS idx_location_cache_cleanup ON location_cache(last_updated, prediction_count) 
    WHERE prediction_count < 3;

-- Add updated_at trigger
DROP TRIGGER IF EXISTS update_location_cache_updated_at ON location_cache;
CREATE TRIGGER update_location_cache_updated_at 
    BEFORE UPDATE ON location_cache 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add constraints
DO $$
BEGIN
    ALTER TABLE location_cache ADD CONSTRAINT confidence_range_location 
        CHECK (confidence >= 0.0 AND confidence <= 1.0);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    ALTER TABLE location_cache ADD CONSTRAINT accuracy_rate_range 
        CHECK (accuracy_rate >= 0.0 AND accuracy_rate <= 1.0);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    ALTER TABLE location_cache ADD CONSTRAINT prediction_count_positive 
        CHECK (prediction_count >= 0);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    ALTER TABLE location_cache ADD CONSTRAINT hit_count_positive_location 
        CHECK (hit_count >= 0);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    ALTER TABLE location_cache ADD CONSTRAINT precision_level_valid 
        CHECK (precision_level >= 1 AND precision_level <= 12);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    ALTER TABLE location_cache ADD CONSTRAINT radius_positive 
        CHECK (radius_meters > 0);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- =====================================================
-- 5. Database Functions
-- =====================================================

-- Function to create user profile after auth.users insert
-- Username is optional - email is used as primary user identifier
CREATE OR REPLACE FUNCTION create_user_profile()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_profiles (
        id,
        username,
        full_name,
        created_at,
        updated_at
    ) VALUES (
        NEW.id,
        CASE 
            WHEN NEW.raw_user_meta_data->>'username' IS NOT NULL 
                 AND NEW.raw_user_meta_data->>'username' != '' 
            THEN NEW.raw_user_meta_data->>'username'
            ELSE NULL
        END,
        COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
        NOW(),
        NOW()
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to update user last login
CREATE OR REPLACE FUNCTION update_user_last_login(user_uuid UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE user_profiles 
    SET last_login_at = NOW(),
        updated_at = NOW()
    WHERE id = user_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to create user session
CREATE OR REPLACE FUNCTION create_user_session(
    p_user_id UUID,
    p_session_token TEXT,
    p_refresh_token TEXT DEFAULT NULL,
    p_device_id TEXT DEFAULT NULL,
    p_device_name TEXT DEFAULT NULL,
    p_device_type TEXT DEFAULT 'unknown',
    p_platform TEXT DEFAULT 'unknown',
    p_app_version TEXT DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_location_country TEXT DEFAULT NULL,
    p_location_city TEXT DEFAULT NULL,
    p_timezone TEXT DEFAULT 'UTC',
    p_login_method TEXT DEFAULT 'email',
    p_expires_hours INTEGER DEFAULT 24
)
RETURNS UUID AS $$
DECLARE
    session_id UUID;
BEGIN
    INSERT INTO user_sessions (
        user_id,
        session_token,
        refresh_token,
        device_id,
        device_name,
        device_type,
        platform,
        app_version,
        ip_address,
        user_agent,
        location_country,
        location_city,
        timezone,
        login_method,
        expires_at,
        started_at,
        last_activity_at
    ) VALUES (
        p_user_id,
        p_session_token,
        p_refresh_token,
        p_device_id,
        p_device_name,
        p_device_type,
        p_platform,
        p_app_version,
        p_ip_address,
        p_user_agent,
        p_location_country,
        p_location_city,
        p_timezone,
        p_login_method,
        NOW() + INTERVAL '1 hour' * p_expires_hours,
        NOW(),
        NOW()
    ) RETURNING id INTO session_id;
    
    -- Update user last login
    PERFORM update_user_last_login(p_user_id);
    
    RETURN session_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to cleanup expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    cleaned_count INTEGER;
BEGIN
    UPDATE user_sessions 
    SET is_active = false,
        ended_at = COALESCE(ended_at, NOW()),
        updated_at = NOW()
    WHERE expires_at < NOW() 
      AND is_active = true;
    
    GET DIAGNOSTICS cleaned_count = ROW_COUNT;
    RETURN cleaned_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 6. Row Level Security Policies
-- =====================================================

-- User Profiles Policies
DROP POLICY IF EXISTS "Users can view own profile" ON user_profiles;
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON user_profiles;
CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can insert own profile" ON user_profiles;
CREATE POLICY "Users can insert own profile" ON user_profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- User Sessions Policies
DROP POLICY IF EXISTS "Users can view own sessions" ON user_sessions;
CREATE POLICY "Users can view own sessions" ON user_sessions
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own sessions" ON user_sessions;
CREATE POLICY "Users can insert own sessions" ON user_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own sessions" ON user_sessions;
CREATE POLICY "Users can update own sessions" ON user_sessions
    FOR UPDATE USING (auth.uid() = user_id);

-- User Activity Logs Policies
DROP POLICY IF EXISTS "Users can view own activity" ON user_activity_logs;
CREATE POLICY "Users can view own activity" ON user_activity_logs
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "System can insert activity logs" ON user_activity_logs;
CREATE POLICY "System can insert activity logs" ON user_activity_logs
    FOR INSERT WITH CHECK (true);

-- Transaction Feedback Policies - Updated for middleware compatibility
DROP POLICY IF EXISTS "Users can view own transaction feedback" ON transaction_feedback;
CREATE POLICY "Users can view own transaction feedback" ON transaction_feedback
    FOR SELECT USING (auth.uid() = user_id OR auth.uid() IS NULL);

DROP POLICY IF EXISTS "Users can insert own transaction feedback" ON transaction_feedback;
CREATE POLICY "Users can insert own transaction feedback" ON transaction_feedback
    FOR INSERT WITH CHECK (auth.uid() = user_id OR auth.uid() IS NULL);

DROP POLICY IF EXISTS "System can insert transaction feedback" ON transaction_feedback;
CREATE POLICY "System can insert transaction feedback" ON transaction_feedback
    FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Users can update own transaction feedback" ON transaction_feedback;
CREATE POLICY "Users can update own transaction feedback" ON transaction_feedback
    FOR UPDATE USING (auth.uid() = user_id OR auth.uid() IS NULL);

-- User Preferences Policies
DROP POLICY IF EXISTS "Users can view own preferences" ON user_preferences;
CREATE POLICY "Users can view own preferences" ON user_preferences
    FOR SELECT USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can insert own preferences" ON user_preferences;
CREATE POLICY "Users can insert own preferences" ON user_preferences
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can update own preferences" ON user_preferences;
CREATE POLICY "Users can update own preferences" ON user_preferences
    FOR UPDATE USING (auth.uid()::text = user_id);

-- Card Performance Policies
DROP POLICY IF EXISTS "Users can view own card performance" ON card_performance;
CREATE POLICY "Users can view own card performance" ON card_performance
    FOR SELECT USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Service can insert card performance" ON card_performance;
CREATE POLICY "Service can insert card performance" ON card_performance
    FOR INSERT WITH CHECK (true);

-- Session Analytics Policies
DROP POLICY IF EXISTS "Users can view own session analytics" ON session_analytics;
CREATE POLICY "Users can view own session analytics" ON session_analytics
    FOR SELECT USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Service can insert session analytics" ON session_analytics;
CREATE POLICY "Service can insert session analytics" ON session_analytics
    FOR INSERT WITH CHECK (true);

-- MCC Predictions Policies
DROP POLICY IF EXISTS "System can manage predictions" ON mcc_predictions;
CREATE POLICY "System can manage predictions" ON mcc_predictions
    FOR ALL USING (true);

-- Background Location Sessions Policies (Skip if table doesn't exist)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'background_location_sessions') THEN
        DROP POLICY IF EXISTS "Users can view own location sessions" ON background_location_sessions;
        CREATE POLICY "Users can view own location sessions" ON background_location_sessions
            FOR SELECT USING (auth.uid() = user_id);

        DROP POLICY IF EXISTS "Users can insert own location sessions" ON background_location_sessions;
        CREATE POLICY "Users can insert own location sessions" ON background_location_sessions
            FOR INSERT WITH CHECK (auth.uid() = user_id);

        DROP POLICY IF EXISTS "Users can update own location sessions" ON background_location_sessions;
        CREATE POLICY "Users can update own location sessions" ON background_location_sessions
            FOR UPDATE USING (auth.uid() = user_id);
    END IF;
END $$;

-- Cache Tables Policies
DROP POLICY IF EXISTS "Authenticated users can read terminal cache" ON terminal_cache;
CREATE POLICY "Authenticated users can read terminal cache" ON terminal_cache
    FOR SELECT USING (auth.uid() IS NOT NULL OR auth.uid() IS NULL);

DROP POLICY IF EXISTS "System can manage terminal cache" ON terminal_cache;
CREATE POLICY "System can manage terminal cache" ON terminal_cache
    FOR ALL USING (true);

DROP POLICY IF EXISTS "Authenticated users can read location cache" ON location_cache;
CREATE POLICY "Authenticated users can read location cache" ON location_cache
    FOR SELECT USING (auth.uid() IS NOT NULL OR auth.uid() IS NULL);

DROP POLICY IF EXISTS "System can manage location cache" ON location_cache;
CREATE POLICY "System can manage location cache" ON location_cache
    FOR ALL USING (true);

-- =====================================================
-- 7. Triggers and Automation
-- =====================================================

-- Trigger to automatically create user profile when auth.users record is created
-- Drop existing trigger if it exists to avoid conflicts
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION create_user_profile();

-- =====================================================
-- 8. Realtime Configuration
-- =====================================================

-- Enable realtime for ALL tables to provide comprehensive live updates
-- This allows clients to receive real-time notifications when data changes
-- across the entire application ecosystem

-- Authentication & User Management Tables
-- User profiles - for profile updates, status changes, role modifications
DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE user_profiles;
EXCEPTION
    WHEN duplicate_object THEN NULL;
    WHEN undefined_table THEN NULL;
END $$;

-- User sessions - for login/logout status, session management, security monitoring
DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE user_sessions;
EXCEPTION
    WHEN duplicate_object THEN NULL;
    WHEN undefined_table THEN NULL;
END $$;

-- User activity logs - for live activity monitoring, security alerts, audit trails
DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE user_activity_logs;
EXCEPTION
    WHEN duplicate_object THEN NULL;
    WHEN undefined_table THEN NULL;
END $$;

-- Core Business Logic Tables
-- Transaction feedback - for live transaction monitoring, real-time analytics
DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE transaction_feedback;
EXCEPTION
    WHEN duplicate_object THEN NULL;
    WHEN undefined_table THEN NULL;
END $$;

-- Background location sessions - for real-time location tracking status, session updates
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'background_location_sessions') THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE background_location_sessions;
    END IF;
EXCEPTION
    WHEN duplicate_object THEN NULL;
    WHEN undefined_table THEN NULL;
END $$;

-- Cache Tables - for live cache updates, performance monitoring
-- Terminal cache - for real-time terminal data updates, MCC predictions
DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE terminal_cache;
EXCEPTION
    WHEN duplicate_object THEN NULL;
    WHEN undefined_table THEN NULL;
END $$;

-- Location cache - for live location-based predictions, spatial data updates
DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE location_cache;
EXCEPTION
    WHEN duplicate_object THEN NULL;
    WHEN undefined_table THEN NULL;
END $$;

-- =====================================================
-- Realtime Benefits by Table:
-- =====================================================
-- user_profiles: Live profile updates, status changes, role modifications
-- user_sessions: Real-time login/logout tracking, session security monitoring
-- user_activity_logs: Live audit trails, security monitoring, user behavior analytics
-- transaction_feedback: Real-time transaction monitoring, live prediction accuracy
-- background_location_sessions: Live location tracking status, session management
-- terminal_cache: Real-time terminal data updates, live MCC prediction improvements
-- location_cache: Live spatial predictions, real-time location-based insights
-- =====================================================

-- =====================================================
-- 9. Database Statistics and Health Check
-- =====================================================

-- Analyze tables for query optimization
ANALYZE user_profiles;
ANALYZE user_sessions;
ANALYZE user_activity_logs;
ANALYZE transaction_feedback;
ANALYZE background_location_sessions;
ANALYZE terminal_cache;
ANALYZE location_cache;

-- Verification message
SELECT 'Database schema deployment completed successfully!' as status; 