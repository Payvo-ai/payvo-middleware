-- =====================================================
-- Performance Optimization Indexes
-- =====================================================

-- Composite indexes for common query patterns

-- User authentication and session management
CREATE INDEX IF NOT EXISTS idx_user_profiles_auth_lookup 
    ON user_profiles(username, is_active, is_verified) 
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_user_sessions_active_lookup 
    ON user_sessions(user_id, is_active, expires_at) 
    WHERE is_active = true AND expires_at > NOW();

CREATE INDEX IF NOT EXISTS idx_user_sessions_device_tracking 
    ON user_sessions(device_id, user_id, started_at) 
    WHERE is_active = true;

-- Transaction feedback analytics
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_analytics 
    ON transaction_feedback(user_id, actual_mcc, created_at) 
    WHERE actual_mcc IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_transaction_feedback_ml_training 
    ON transaction_feedback(predicted_mcc, actual_mcc, prediction_confidence) 
    WHERE actual_mcc IS NOT NULL AND prediction_confidence > 0.5;

CREATE INDEX IF NOT EXISTS idx_transaction_feedback_location_analysis 
    ON transaction_feedback(location_hash, actual_mcc, transaction_timestamp) 
    WHERE location_hash IS NOT NULL;

-- Location-based queries
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_spatial_time 
    ON transaction_feedback USING GIST (
        ST_Point(location_lng, location_lat), 
        transaction_timestamp
    ) WHERE location_lat IS NOT NULL AND location_lng IS NOT NULL;

-- Background location sessions optimization
CREATE INDEX IF NOT EXISTS idx_location_sessions_active 
    ON background_location_sessions(user_id, status, expires_at) 
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_location_sessions_cleanup 
    ON background_location_sessions(expires_at, status) 
    WHERE status IN ('expired', 'completed');

-- Activity logs for audit and monitoring
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_action_time 
    ON user_activity_logs(user_id, action, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_activity_logs_resource_monitoring 
    ON user_activity_logs(resource, status_code, created_at DESC) 
    WHERE status_code >= 400;

CREATE INDEX IF NOT EXISTS idx_activity_logs_session_tracking 
    ON user_activity_logs(session_id, created_at DESC) 
    WHERE session_id IS NOT NULL;

-- Cache performance indexes
CREATE INDEX IF NOT EXISTS idx_terminal_cache_performance 
    ON terminal_cache(terminal_id, confidence DESC, last_seen DESC) 
    WHERE confidence > 0.7;

CREATE INDEX IF NOT EXISTS idx_location_cache_performance 
    ON location_cache(location_hash, confidence DESC, accuracy_rate DESC) 
    WHERE confidence > 0.5 AND accuracy_rate > 0.6;

-- Partial indexes for common filters
CREATE INDEX IF NOT EXISTS idx_user_profiles_employees 
    ON user_profiles(employee_id, department, is_active) 
    WHERE employee_id IS NOT NULL AND is_active = true;

CREATE INDEX IF NOT EXISTS idx_transaction_feedback_successful 
    ON transaction_feedback(user_id, transaction_success, created_at DESC) 
    WHERE transaction_success = true;

CREATE INDEX IF NOT EXISTS idx_transaction_feedback_high_confidence 
    ON transaction_feedback(predicted_mcc, actual_mcc, prediction_confidence) 
    WHERE prediction_confidence > 0.8;

-- Time-series optimization for reporting
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_daily_reports 
    ON transaction_feedback(DATE(transaction_timestamp), actual_mcc) 
    WHERE actual_mcc IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_user_activity_daily_reports 
    ON user_activity_logs(DATE(created_at), action, status_code);

-- Network and device analysis
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_network_analysis 
    ON transaction_feedback(network_used, transaction_success, created_at) 
    WHERE network_used IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_user_sessions_platform_analysis 
    ON user_sessions(platform, device_type, started_at) 
    WHERE platform IS NOT NULL;

-- =====================================================
-- Maintenance and Cleanup Indexes
-- =====================================================

-- Indexes to support automated cleanup operations
CREATE INDEX IF NOT EXISTS idx_user_sessions_cleanup 
    ON user_sessions(expires_at, ended_at) 
    WHERE is_active = false OR expires_at < NOW();

CREATE INDEX IF NOT EXISTS idx_terminal_cache_cleanup 
    ON terminal_cache(last_seen, transaction_count) 
    WHERE transaction_count < 5 AND last_seen < NOW() - INTERVAL '30 days';

CREATE INDEX IF NOT EXISTS idx_location_cache_cleanup 
    ON location_cache(last_updated, prediction_count) 
    WHERE prediction_count < 3 AND last_updated < NOW() - INTERVAL '30 days';

-- =====================================================
-- Full-text Search Indexes
-- =====================================================

-- Full-text search for merchant names and categories
CREATE INDEX IF NOT EXISTS idx_transaction_feedback_merchant_search 
    ON transaction_feedback USING GIN (
        to_tsvector('english', COALESCE(merchant_name, '') || ' ' || COALESCE(merchant_category, ''))
    ) WHERE merchant_name IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_terminal_cache_merchant_search 
    ON terminal_cache USING GIN (
        to_tsvector('english', COALESCE(merchant_name, '') || ' ' || COALESCE(merchant_category, ''))
    ) WHERE merchant_name IS NOT NULL;

-- =====================================================
-- Statistics and Monitoring
-- =====================================================

-- Create statistics for query optimization
CREATE STATISTICS IF NOT EXISTS stats_transaction_feedback_location_mcc 
    ON location_lat, location_lng, actual_mcc 
    FROM transaction_feedback;

CREATE STATISTICS IF NOT EXISTS stats_user_sessions_device_platform 
    ON device_type, platform, user_id 
    FROM user_sessions;

CREATE STATISTICS IF NOT EXISTS stats_terminal_cache_confidence_usage 
    ON confidence, transaction_count, hit_count 
    FROM terminal_cache; 