-- Payvo Middleware Database Schema for Supabase
-- Run these commands in your Supabase SQL editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Transaction Feedback Table
-- Stores feedback from completed transactions for learning
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
-- Tracks card performance metrics
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
-- Stores user preferences for card routing
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) UNIQUE NOT NULL,
    preferences JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Terminal Cache Table
-- Caches terminal ID to MCC mappings
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
-- Caches location to MCC mappings
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
-- Caches WiFi fingerprint to MCC mappings
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
-- Caches BLE fingerprint to MCC mappings
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_user_id ON transaction_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_session_id ON transaction_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_created_at ON transaction_feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_actual_mcc ON transaction_feedback(actual_mcc);

CREATE INDEX IF NOT EXISTS idx_mcc_predictions_session_id ON mcc_predictions(session_id);
CREATE INDEX IF NOT EXISTS idx_mcc_predictions_terminal_id ON mcc_predictions(terminal_id);
CREATE INDEX IF NOT EXISTS idx_mcc_predictions_location_hash ON mcc_predictions(location_hash);
CREATE INDEX IF NOT EXISTS idx_mcc_predictions_created_at ON mcc_predictions(created_at);

CREATE INDEX IF NOT EXISTS idx_card_performance_card_id ON card_performance(card_id);
CREATE INDEX IF NOT EXISTS idx_card_performance_user_id ON card_performance(user_id);
CREATE INDEX IF NOT EXISTS idx_card_performance_mcc ON card_performance(mcc);

CREATE INDEX IF NOT EXISTS idx_terminal_cache_terminal_id ON terminal_cache(terminal_id);
CREATE INDEX IF NOT EXISTS idx_location_cache_location_hash ON location_cache(location_hash);
CREATE INDEX IF NOT EXISTS idx_wifi_cache_wifi_hash ON wifi_cache(wifi_hash);
CREATE INDEX IF NOT EXISTS idx_ble_cache_ble_hash ON ble_cache(ble_hash);

-- Row Level Security (RLS) policies
ALTER TABLE transaction_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE mcc_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE card_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Allow service role to access all data
CREATE POLICY "Service role can access all transaction_feedback" ON transaction_feedback
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can access all mcc_predictions" ON mcc_predictions
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can access all card_performance" ON card_performance
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can access all user_preferences" ON user_preferences
    FOR ALL USING (auth.role() = 'service_role');

-- Cache tables don't need RLS as they don't contain sensitive user data
-- But we'll enable it for consistency
ALTER TABLE terminal_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE location_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE wifi_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE ble_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role can access all terminal_cache" ON terminal_cache
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can access all location_cache" ON location_cache
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can access all wifi_cache" ON wifi_cache
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can access all ble_cache" ON ble_cache
    FOR ALL USING (auth.role() = 'service_role');

-- Functions for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

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