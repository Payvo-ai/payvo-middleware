-- =====================================================
-- Transaction Feedback Table
-- =====================================================
-- Stores feedback from completed transactions for machine learning

CREATE TABLE IF NOT EXISTS transaction_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id VARCHAR(255) NOT NULL,
    
    -- MCC Prediction Data
    predicted_mcc VARCHAR(4),
    actual_mcc VARCHAR(4),
    prediction_confidence DECIMAL(3,2),
    prediction_method VARCHAR(50),
    
    -- Card and Payment Data
    selected_card_id VARCHAR(255),
    network_used VARCHAR(20), -- 'visa', 'mastercard', 'amex', 'discover'
    transaction_success BOOLEAN,
    rewards_earned DECIMAL(10,2),
    transaction_amount DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Merchant Information
    merchant_name VARCHAR(255),
    merchant_category VARCHAR(100),
    terminal_id VARCHAR(255),
    
    -- Location Data
    location_lat DECIMAL(10,8),
    location_lng DECIMAL(11,8),
    location_hash VARCHAR(50),
    location_accuracy DECIMAL(8,2),
    
    -- Context Data
    wifi_fingerprint TEXT,
    ble_fingerprint TEXT,
    context_features JSONB DEFAULT '{}'::jsonb,
    
    -- Timing
    transaction_timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add RLS
ALTER TABLE transaction_feedback ENABLE ROW LEVEL SECURITY;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_user_id ON transaction_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_session_id ON transaction_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_created_at ON transaction_feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_actual_mcc ON transaction_feedback(actual_mcc);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_predicted_mcc ON transaction_feedback(predicted_mcc);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_terminal_id ON transaction_feedback(terminal_id);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_location_hash ON transaction_feedback(location_hash);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_merchant_name ON transaction_feedback(merchant_name);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_network_used ON transaction_feedback(network_used);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_transaction_success ON transaction_feedback(transaction_success);

-- Composite indexes for analytics
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_mcc_comparison ON transaction_feedback(predicted_mcc, actual_mcc, prediction_confidence);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_location_analysis ON transaction_feedback(location_hash, actual_mcc, created_at);
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_user_patterns ON transaction_feedback(user_id, actual_mcc, created_at);

-- Add updated_at trigger
CREATE TRIGGER update_transaction_feedback_updated_at 
    BEFORE UPDATE ON transaction_feedback 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 