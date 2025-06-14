-- =====================================================
-- Authentication Functions
-- =====================================================

-- Function to create user profile after auth.users insert
-- Note: Username is optional - email is used as the primary user identifier
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
        -- Username is optional - only set if explicitly provided in metadata
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

-- Function to update session activity
CREATE OR REPLACE FUNCTION update_session_activity(
    p_session_id UUID,
    p_extend_hours INTEGER DEFAULT 1
)
RETURNS BOOLEAN AS $$
DECLARE
    session_exists BOOLEAN;
BEGIN
    UPDATE user_sessions 
    SET last_activity_at = NOW(),
        expires_at = CASE 
            WHEN p_extend_hours > 0 THEN NOW() + INTERVAL '1 hour' * p_extend_hours
            ELSE expires_at
        END,
        updated_at = NOW()
    WHERE id = p_session_id 
      AND is_active = true 
      AND expires_at > NOW();
    
    GET DIAGNOSTICS session_exists = FOUND;
    RETURN session_exists;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to end user session
CREATE OR REPLACE FUNCTION end_user_session(p_session_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    session_exists BOOLEAN;
BEGIN
    UPDATE user_sessions 
    SET is_active = false,
        ended_at = NOW(),
        updated_at = NOW()
    WHERE id = p_session_id;
    
    GET DIAGNOSTICS session_exists = FOUND;
    RETURN session_exists;
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

-- Function to get active user sessions
CREATE OR REPLACE FUNCTION get_user_active_sessions(p_user_id UUID)
RETURNS TABLE (
    session_id UUID,
    device_name TEXT,
    device_type TEXT,
    platform TEXT,
    ip_address INET,
    location_city TEXT,
    location_country TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    last_activity_at TIMESTAMP WITH TIME ZONE,
    is_current BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        us.id,
        us.device_name,
        us.device_type,
        us.platform,
        us.ip_address,
        us.location_city,
        us.location_country,
        us.started_at,
        us.last_activity_at,
        (us.last_activity_at > NOW() - INTERVAL '5 minutes') as is_current
    FROM user_sessions us
    WHERE us.user_id = p_user_id
      AND us.is_active = true
      AND us.expires_at > NOW()
    ORDER BY us.last_activity_at DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to validate session token
CREATE OR REPLACE FUNCTION validate_session_token(p_session_token TEXT)
RETURNS TABLE (
    user_id UUID,
    session_id UUID,
    is_valid BOOLEAN,
    expires_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        us.user_id,
        us.id,
        (us.is_active AND us.expires_at > NOW()) as is_valid,
        us.expires_at
    FROM user_sessions us
    WHERE us.session_token = p_session_token;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER; 