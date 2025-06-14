-- =====================================================
-- Database Triggers
-- =====================================================

-- Trigger to automatically create user profile when auth.users record is created
-- Drop existing trigger if it exists to avoid conflicts
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION create_user_profile();

-- =====================================================
-- Automated Cleanup Triggers
-- =====================================================

-- Function to log user activity
CREATE OR REPLACE FUNCTION log_user_activity()
RETURNS TRIGGER AS $$
DECLARE
    current_user_id UUID;
    current_session_id UUID;
BEGIN
    -- Get current user and session from context
    current_user_id := auth.uid();
    
    -- Only log if we have a valid user
    IF current_user_id IS NOT NULL THEN
        -- Try to get current session (this would need to be set in application context)
        current_session_id := current_setting('app.current_session_id', true)::UUID;
        
        -- Log the activity
        INSERT INTO user_activity_logs (
            user_id,
            session_id,
            action,
            resource,
            resource_id,
            method,
            description,
            metadata
        ) VALUES (
            current_user_id,
            current_session_id,
            TG_OP,
            TG_TABLE_NAME,
            CASE 
                WHEN TG_OP = 'DELETE' THEN OLD.id::TEXT
                ELSE NEW.id::TEXT
            END,
            'DATABASE',
            format('%s operation on %s', TG_OP, TG_TABLE_NAME),
            jsonb_build_object(
                'table', TG_TABLE_NAME,
                'operation', TG_OP,
                'timestamp', NOW()
            )
        );
    END IF;
    
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply activity logging to sensitive tables
CREATE TRIGGER log_user_profiles_activity
    AFTER INSERT OR UPDATE OR DELETE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION log_user_activity();

CREATE TRIGGER log_transaction_feedback_activity
    AFTER INSERT OR UPDATE OR DELETE ON transaction_feedback
    FOR EACH ROW EXECUTE FUNCTION log_user_activity();

-- =====================================================
-- Cache Maintenance Triggers
-- =====================================================

-- Function to update cache statistics
CREATE OR REPLACE FUNCTION update_cache_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Update terminal cache statistics
    IF TG_TABLE_NAME = 'terminal_cache' THEN
        -- Update hit rate and other metrics
        NEW.updated_at = NOW();
    END IF;
    
    -- Update location cache statistics
    IF TG_TABLE_NAME = 'location_cache' THEN
        NEW.updated_at = NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Data Validation Triggers
-- =====================================================

-- Function to validate transaction feedback data
CREATE OR REPLACE FUNCTION validate_transaction_feedback()
RETURNS TRIGGER AS $$
BEGIN
    -- Validate MCC codes (should be 4 digits)
    IF NEW.predicted_mcc IS NOT NULL AND LENGTH(NEW.predicted_mcc) != 4 THEN
        RAISE EXCEPTION 'Predicted MCC must be exactly 4 digits';
    END IF;
    
    IF NEW.actual_mcc IS NOT NULL AND LENGTH(NEW.actual_mcc) != 4 THEN
        RAISE EXCEPTION 'Actual MCC must be exactly 4 digits';
    END IF;
    
    -- Validate confidence score
    IF NEW.prediction_confidence IS NOT NULL AND 
       (NEW.prediction_confidence < 0 OR NEW.prediction_confidence > 1) THEN
        RAISE EXCEPTION 'Prediction confidence must be between 0 and 1';
    END IF;
    
    -- Validate location coordinates
    IF NEW.location_lat IS NOT NULL AND 
       (NEW.location_lat < -90 OR NEW.location_lat > 90) THEN
        RAISE EXCEPTION 'Latitude must be between -90 and 90';
    END IF;
    
    IF NEW.location_lng IS NOT NULL AND 
       (NEW.location_lng < -180 OR NEW.location_lng > 180) THEN
        RAISE EXCEPTION 'Longitude must be between -180 and 180';
    END IF;
    
    -- Generate location hash if coordinates are provided
    IF NEW.location_lat IS NOT NULL AND NEW.location_lng IS NOT NULL AND NEW.location_hash IS NULL THEN
        NEW.location_hash = generate_location_hash(NEW.location_lat, NEW.location_lng, 3);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply validation trigger
CREATE TRIGGER validate_transaction_feedback_trigger
    BEFORE INSERT OR UPDATE ON transaction_feedback
    FOR EACH ROW EXECUTE FUNCTION validate_transaction_feedback();

-- =====================================================
-- Session Management Triggers
-- =====================================================

-- Function to cleanup expired sessions periodically
CREATE OR REPLACE FUNCTION cleanup_expired_sessions_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Clean up expired sessions when new sessions are created
    PERFORM cleanup_expired_sessions();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to cleanup expired sessions on new session creation
CREATE TRIGGER cleanup_sessions_on_insert
    AFTER INSERT ON user_sessions
    FOR EACH STATEMENT EXECUTE FUNCTION cleanup_expired_sessions_trigger(); 