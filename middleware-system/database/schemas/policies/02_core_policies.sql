-- =====================================================
-- Core Business Tables Row Level Security Policies
-- =====================================================

-- Transaction Feedback Policies
-- Users can only see and modify their own transaction feedback
CREATE POLICY "Users can view own transaction feedback" ON transaction_feedback
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own transaction feedback" ON transaction_feedback
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own transaction feedback" ON transaction_feedback
    FOR UPDATE USING (auth.uid() = user_id);

-- Admin users can view all transaction feedback
CREATE POLICY "Admins can view all transaction feedback" ON transaction_feedback
    FOR SELECT USING (is_admin());

-- System can insert transaction feedback for any user (for ML processing)
CREATE POLICY "System can insert transaction feedback" ON transaction_feedback
    FOR INSERT WITH CHECK (true);

-- Analytics team can view aggregated data (no personal info)
CREATE POLICY "Analytics can view aggregated data" ON transaction_feedback
    FOR SELECT USING (
        user_in_department('analytics') OR 
        user_in_department('data_science')
    );

-- Background Location Sessions Policies
-- Users can only see and modify their own location sessions
CREATE POLICY "Users can view own location sessions" ON background_location_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own location sessions" ON background_location_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own location sessions" ON background_location_sessions
    FOR UPDATE USING (auth.uid() = user_id);

-- Admin users can view all location sessions
CREATE POLICY "Admins can view all location sessions" ON background_location_sessions
    FOR SELECT USING (is_admin());

-- System can manage location sessions
CREATE POLICY "System can manage location sessions" ON background_location_sessions
    FOR ALL WITH CHECK (true);

-- =====================================================
-- Cache Tables Policies
-- =====================================================

-- Terminal Cache Policies
-- All authenticated users can read terminal cache
CREATE POLICY "Authenticated users can read terminal cache" ON terminal_cache
    FOR SELECT USING (auth.uid() IS NOT NULL);

-- Only system and admins can modify terminal cache
CREATE POLICY "System can modify terminal cache" ON terminal_cache
    FOR ALL WITH CHECK (true);

CREATE POLICY "Admins can modify terminal cache" ON terminal_cache
    FOR ALL USING (is_admin());

-- Location Cache Policies
-- All authenticated users can read location cache
CREATE POLICY "Authenticated users can read location cache" ON location_cache
    FOR SELECT USING (auth.uid() IS NOT NULL);

-- Only system and admins can modify location cache
CREATE POLICY "System can modify location cache" ON location_cache
    FOR ALL WITH CHECK (true);

CREATE POLICY "Admins can modify location cache" ON location_cache
    FOR ALL USING (is_admin());

-- =====================================================
-- Data Privacy Policies
-- =====================================================

-- Function to check if user has data access permission
CREATE OR REPLACE FUNCTION has_data_access(table_name TEXT, user_id UUID DEFAULT auth.uid())
RETURNS BOOLEAN AS $$
BEGIN
    -- Admin users have access to all data
    IF is_admin(user_id) THEN
        RETURN true;
    END IF;
    
    -- Check specific table permissions
    CASE table_name
        WHEN 'transaction_feedback' THEN
            RETURN user_in_department('analytics', user_id) OR 
                   user_in_department('data_science', user_id) OR
                   user_in_department('product', user_id);
        WHEN 'location_sessions' THEN
            RETURN user_in_department('engineering', user_id) OR
                   user_in_department('data_science', user_id);
        ELSE
            RETURN false;
    END CASE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to anonymize sensitive data for analytics
CREATE OR REPLACE FUNCTION anonymize_user_data(user_id UUID)
RETURNS TEXT AS $$
BEGIN
    -- Return hashed user ID for analytics while preserving uniqueness
    RETURN encode(digest(user_id::text, 'sha256'), 'hex');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- Audit and Compliance Policies
-- =====================================================

-- Policy for data retention compliance
CREATE OR REPLACE FUNCTION enforce_data_retention()
RETURNS TRIGGER AS $$
BEGIN
    -- Prevent deletion of audit records less than 7 years old
    IF TG_TABLE_NAME = 'user_activity_logs' THEN
        IF OLD.created_at > NOW() - INTERVAL '7 years' THEN
            RAISE EXCEPTION 'Cannot delete audit records less than 7 years old';
        END IF;
    END IF;
    
    -- Prevent deletion of transaction feedback less than 5 years old
    IF TG_TABLE_NAME = 'transaction_feedback' THEN
        IF OLD.created_at > NOW() - INTERVAL '5 years' THEN
            RAISE EXCEPTION 'Cannot delete transaction records less than 5 years old';
        END IF;
    END IF;
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply data retention triggers
CREATE TRIGGER enforce_activity_logs_retention
    BEFORE DELETE ON user_activity_logs
    FOR EACH ROW EXECUTE FUNCTION enforce_data_retention();

CREATE TRIGGER enforce_transaction_feedback_retention
    BEFORE DELETE ON transaction_feedback
    FOR EACH ROW EXECUTE FUNCTION enforce_data_retention(); 