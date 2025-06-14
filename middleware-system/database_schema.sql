-- Payvo Middleware Database Schema
-- Run this in your Supabase SQL Editor

-- Transaction feedback table
CREATE TABLE IF NOT EXISTS transaction_feedback (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    predicted_mcc TEXT,
    actual_mcc TEXT,
    prediction_confidence DECIMAL,
    prediction_method TEXT,
    selected_card_id TEXT,
    network_used TEXT,
    transaction_success BOOLEAN,
    rewards_earned DECIMAL,
    merchant_name TEXT,
    transaction_amount DECIMAL,
    location_lat DECIMAL,
    location_lng DECIMAL,
    location_hash TEXT,
    terminal_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- MCC predictions table
CREATE TABLE IF NOT EXISTS mcc_predictions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT NOT NULL,
    terminal_id TEXT,
    location_hash TEXT,
    wifi_fingerprint TEXT,
    ble_fingerprint TEXT,
    predicted_mcc TEXT NOT NULL,
    confidence DECIMAL NOT NULL,
    method_used TEXT NOT NULL,
    context_features JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Card performance table
CREATE TABLE IF NOT EXISTS card_performance (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    card_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    mcc TEXT,
    network TEXT,
    transaction_success BOOLEAN,
    rewards_earned DECIMAL,
    transaction_amount DECIMAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    preferences JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_user_id ON transaction_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_session_id ON transaction_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_terminal_id ON transaction_feedback(terminal_id);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_location_hash ON transaction_feedback(location_hash);
CREATE INDEX IF NOT EXISTS idx_mcc_predictions_terminal_id ON mcc_predictions(terminal_id);
CREATE INDEX IF NOT EXISTS idx_mcc_predictions_location_hash ON mcc_predictions(location_hash);
CREATE INDEX IF NOT EXISTS idx_card_performance_card_id ON card_performance(card_id);
CREATE INDEX IF NOT EXISTS idx_card_performance_user_id ON card_performance(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- Enable Row Level Security (RLS) for better security
ALTER TABLE transaction_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE mcc_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE card_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated access
CREATE POLICY "Users can view their own data" ON transaction_feedback
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own data" ON transaction_feedback
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can view their own predictions" ON mcc_predictions
    FOR SELECT USING (true); -- Allow all authenticated users to read predictions

CREATE POLICY "Service can insert predictions" ON mcc_predictions
    FOR INSERT WITH CHECK (true); -- Allow service to insert predictions

CREATE POLICY "Users can view their own performance" ON card_performance
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own performance" ON card_performance
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can view their own preferences" ON user_preferences
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own preferences" ON user_preferences
    FOR ALL USING (auth.uid()::text = user_id);

-- Insert a test user preference record
INSERT INTO user_preferences (user_id, preferences) 
VALUES ('test_user', '{"cards": [], "preferences": {}}') 
ON CONFLICT (user_id) DO NOTHING; 