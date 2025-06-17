-- =====================================================
-- Payvo Middleware - Complete Supabase Database Schema
-- =====================================================
-- Run this entire script in your Supabase SQL Editor
-- This creates all necessary tables, indexes, and policies

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis" SCHEMA extensions;

-- =====================================================
-- CORE TRANSACTION TABLES
-- =====================================================

-- Transaction Feedback Table
-- Stores feedback from completed transactions for machine learning
CREATE TABLE IF NOT EXISTS transaction_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    predicted_mcc VARCHAR(4),
    actual_mcc VARCHAR(4),
    prediction_confidence DECIMAL(3,2),
    prediction_method VARCHAR(50),
    selected_card_id VARCHAR(255),
    network_used VARCHAR(20),
    transaction_success BOOLEAN,
    rewards_earned DECIMAL(10,2),
    merchant_name VARCHAR(255),
    transaction_amount DECIMAL(10,2),
    location_lat DECIMAL(10,8),
    location_lng DECIMAL(11,8),
    location_hash VARCHAR(50),
    terminal_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- MCC Predictions Table
-- Stores all MCC predictions for learning and analysis
CREATE TABLE IF NOT EXISTS mcc_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    terminal_id VARCHAR(255),
    location_hash VARCHAR(50),
    wifi_fingerprint TEXT,
    ble_fingerprint TEXT,
    predicted_mcc VARCHAR(4) NOT NULL,
    confidence DECIMAL(3,2) NOT NULL,
    method_used VARCHAR(50) NOT NULL,
    context_features JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Card Performance Table
-- Tracks card performance metrics for routing optimization
CREATE TABLE IF NOT EXISTS card_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    card_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    mcc VARCHAR(4),
    network VARCHAR(20),
    transaction_success BOOLEAN,
    rewards_earned DECIMAL(10,2),
    transaction_amount DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Preferences Table
-- Stores user preferences for card routing and settings
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) UNIQUE NOT NULL,
    preferences JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- BACKGROUND LOCATION TRACKING TABLES
-- =====================================================

-- Background Location Sessions Table
-- Manages active background location tracking sessions
CREATE TABLE IF NOT EXISTS background_location_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    last_update TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    location_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Background Location Predictions Table
-- Stores continuous location updates and MCC predictions
CREATE TABLE IF NOT EXISTS background_location_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    accuracy DECIMAL(8,2) NOT NULL,
    predicted_mcc VARCHAR(4),
    confidence DECIMAL(3,2),
    prediction_method VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- CACHING TABLES FOR PERFORMANCE
-- =====================================================

-- Terminal Cache Table
-- Caches terminal ID to MCC mappings for faster lookups
CREATE TABLE IF NOT EXISTS terminal_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    terminal_id VARCHAR(255) UNIQUE NOT NULL,
    mcc VARCHAR(4) NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 1.0,
    transaction_count INTEGER DEFAULT 1,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Location Cache Table
-- Caches location to MCC mappings for GPS-based predictions
CREATE TABLE IF NOT EXISTS location_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_hash VARCHAR(50) NOT NULL,
    mcc VARCHAR(4) NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 1.0,
    transaction_count INTEGER DEFAULT 1,
    merchant_name VARCHAR(255),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- WiFi Cache Table
-- Caches WiFi fingerprint to MCC mappings for indoor location
CREATE TABLE IF NOT EXISTS wifi_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wifi_hash VARCHAR(50) UNIQUE NOT NULL,
    mcc VARCHAR(4) NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 1.0,
    transaction_count INTEGER DEFAULT 1,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- BLE Cache Table
-- Caches BLE fingerprint to MCC mappings for proximity detection
CREATE TABLE IF NOT EXISTS ble_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ble_hash VARCHAR(50) UNIQUE NOT NULL,
    mcc VARCHAR(4) NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 1.0,
    transaction_count INTEGER DEFAULT 1,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- POS Terminal Mappings Table
-- Stores learned BLE signature to MCC mappings for POS terminals
CREATE TABLE IF NOT EXISTS pos_terminal_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ble_signature VARCHAR(32) UNIQUE NOT NULL,
    mcc VARCHAR(4) NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 1.0,
    confirmation_count INTEGER DEFAULT 1,
    device_name VARCHAR(255),
    device_uuid VARCHAR(255),
    location_hash VARCHAR(12),
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_confirmed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- PERFORMANCE INDEXES
-- =====================================================

-- Transaction Feedback Indexes
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_user_id ON transaction_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_session_id ON transaction_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_created_at ON transaction_feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_actual_mcc ON transaction_feedback(actual_mcc);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_terminal_id ON transaction_feedback(terminal_id);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_location_hash ON transaction_feedback(location_hash);

-- MCC Predictions Indexes
CREATE INDEX IF NOT EXISTS idx_mcc_predictions_session_id ON mcc_predictions(session_id);
CREATE INDEX IF NOT EXISTS idx_mcc_predictions_terminal_id ON mcc_predictions(terminal_id);
CREATE INDEX IF NOT EXISTS idx_mcc_predictions_location_hash ON mcc_predictions(location_hash);
CREATE INDEX IF NOT EXISTS idx_mcc_predictions_created_at ON mcc_predictions(created_at);

-- Card Performance Indexes
CREATE INDEX IF NOT EXISTS idx_card_performance_card_id ON card_performance(card_id);
CREATE INDEX IF NOT EXISTS idx_card_performance_user_id ON card_performance(user_id);
CREATE INDEX IF NOT EXISTS idx_card_performance_mcc ON card_performance(mcc);

-- User Preferences Indexes
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- Background Location Session Indexes
CREATE INDEX IF NOT EXISTS idx_bg_sessions_user_id ON background_location_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_bg_sessions_is_active ON background_location_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_bg_sessions_expires_at ON background_location_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_bg_sessions_start_time ON background_location_sessions(start_time);

-- Background Location Predictions Indexes
CREATE INDEX IF NOT EXISTS idx_bg_predictions_session_id ON background_location_predictions(session_id);
CREATE INDEX IF NOT EXISTS idx_bg_predictions_user_id ON background_location_predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_bg_predictions_timestamp ON background_location_predictions(timestamp);
CREATE INDEX IF NOT EXISTS idx_bg_predictions_location ON background_location_predictions(latitude, longitude);

-- Cache Table Indexes
CREATE INDEX IF NOT EXISTS idx_terminal_cache_terminal_id ON terminal_cache(terminal_id);
CREATE INDEX IF NOT EXISTS idx_location_cache_location_hash ON location_cache(location_hash);
CREATE INDEX IF NOT EXISTS idx_wifi_cache_wifi_hash ON wifi_cache(wifi_hash);
CREATE INDEX IF NOT EXISTS idx_ble_cache_ble_hash ON ble_cache(ble_hash);
CREATE INDEX IF NOT EXISTS idx_ble_cache_mcc ON ble_cache(mcc);
CREATE INDEX IF NOT EXISTS idx_ble_cache_confidence ON ble_cache(confidence);

-- POS Terminal Mappings Indexes
CREATE INDEX IF NOT EXISTS idx_pos_terminal_mappings_signature ON pos_terminal_mappings(ble_signature);
CREATE INDEX IF NOT EXISTS idx_pos_terminal_mappings_mcc ON pos_terminal_mappings(mcc);
CREATE INDEX IF NOT EXISTS idx_pos_terminal_mappings_confidence ON pos_terminal_mappings(confidence);
CREATE INDEX IF NOT EXISTS idx_pos_terminal_mappings_confirmation_count ON pos_terminal_mappings(confirmation_count);
CREATE INDEX IF NOT EXISTS idx_pos_terminal_mappings_location_hash ON pos_terminal_mappings(location_hash);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) SETUP
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE transaction_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE mcc_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE card_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE background_location_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE background_location_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE terminal_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE location_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE wifi_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE ble_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE pos_terminal_mappings ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- RLS POLICIES FOR SERVICE ROLE ACCESS
-- =====================================================

-- Service role can access all data (for API operations)
CREATE POLICY "Service role full access transaction_feedback" ON transaction_feedback
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access mcc_predictions" ON mcc_predictions
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access card_performance" ON card_performance
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access user_preferences" ON user_preferences
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access bg_sessions" ON background_location_sessions
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access bg_predictions" ON background_location_predictions
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access terminal_cache" ON terminal_cache
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access location_cache" ON location_cache
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access wifi_cache" ON wifi_cache
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access ble_cache" ON ble_cache
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access pos_terminal_mappings" ON pos_terminal_mappings
    FOR ALL USING (auth.role() = 'service_role');

-- =====================================================
-- RLS POLICIES FOR AUTHENTICATED USERS
-- =====================================================

-- Users can only access their own data
CREATE POLICY "Users can view own transaction_feedback" ON transaction_feedback
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own transaction_feedback" ON transaction_feedback
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can view own card_performance" ON card_performance
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own card_performance" ON card_performance
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can manage own preferences" ON user_preferences
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can view own bg_sessions" ON background_location_sessions
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can view own bg_predictions" ON background_location_predictions
    FOR SELECT USING (auth.uid()::text = user_id);

-- MCC predictions are readable by all authenticated users (for learning)
CREATE POLICY "Authenticated users can view mcc_predictions" ON mcc_predictions
    FOR SELECT USING (auth.role() = 'authenticated');

-- =====================================================
-- AUTOMATIC TIMESTAMP UPDATE FUNCTIONS
-- =====================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =====================================================
-- AUTOMATIC TIMESTAMP UPDATE TRIGGERS
-- =====================================================

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_transaction_feedback_updated_at 
    BEFORE UPDATE ON transaction_feedback 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at 
    BEFORE UPDATE ON user_preferences 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_terminal_cache_updated_at 
    BEFORE UPDATE ON terminal_cache 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_location_cache_updated_at 
    BEFORE UPDATE ON location_cache 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_wifi_cache_updated_at 
    BEFORE UPDATE ON wifi_cache 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ble_cache_updated_at 
    BEFORE UPDATE ON ble_cache 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pos_terminal_mappings_updated_at 
    BEFORE UPDATE ON pos_terminal_mappings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- UTILITY FUNCTIONS FOR LOCATION PROCESSING
-- =====================================================

-- Function to calculate distance between two points (Haversine formula)
CREATE OR REPLACE FUNCTION calculate_distance(
    lat1 DECIMAL, lng1 DECIMAL, 
    lat2 DECIMAL, lng2 DECIMAL
) RETURNS DECIMAL AS $$
DECLARE
    r DECIMAL := 6371000; -- Earth's radius in meters
    dlat DECIMAL;
    dlng DECIMAL;
    a DECIMAL;
    c DECIMAL;
BEGIN
    dlat := radians(lat2 - lat1);
    dlng := radians(lng2 - lng1);
    
    a := sin(dlat/2) * sin(dlat/2) + 
         cos(radians(lat1)) * cos(radians(lat2)) * 
         sin(dlng/2) * sin(dlng/2);
    
    c := 2 * atan2(sqrt(a), sqrt(1-a));
    
    RETURN r * c;
END;
$$ LANGUAGE plpgsql;

-- Function to generate location hash for caching
CREATE OR REPLACE FUNCTION generate_location_hash(
    lat DECIMAL, lng DECIMAL, precision_meters INTEGER DEFAULT 10
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
    RETURN MD5(rounded_lat::text || ',' || rounded_lng::text);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- SAMPLE DATA FOR TESTING (OPTIONAL)
-- =====================================================

-- Insert sample user preferences (uncomment if needed for testing)
-- INSERT INTO user_preferences (user_id, preferences) 
-- VALUES ('test_user', '{"cards": [], "preferences": {}}') 
-- ON CONFLICT (user_id) DO NOTHING;

-- =====================================================
-- SCHEMA VALIDATION QUERIES
-- =====================================================

-- Verify all tables were created successfully
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN (
        'transaction_feedback', 'mcc_predictions', 'card_performance', 
        'user_preferences', 'background_location_sessions', 
        'background_location_predictions', 'terminal_cache', 
        'location_cache', 'wifi_cache', 'ble_cache', 'pos_terminal_mappings'
    );
    
    IF table_count = 11 THEN
        RAISE NOTICE '✅ All 11 Payvo Middleware tables created successfully!';
    ELSE
        RAISE NOTICE '⚠️ Expected 11 tables, found %', table_count;
    END IF;
END $$;

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

-- Final success message
DO $$
BEGIN
    RAISE NOTICE '🎉 Payvo Middleware Database Schema Setup Complete!';
    RAISE NOTICE '📊 Tables: Core transactions, Background location tracking, Performance caching';
    RAISE NOTICE '🔒 Security: Row Level Security enabled with proper policies';
    RAISE NOTICE '⚡ Performance: Comprehensive indexes for fast queries';
    RAISE NOTICE '🔧 Features: Auto-timestamps, location utilities, distance calculations';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Your Payvo Middleware database is ready for production!';
END $$; 