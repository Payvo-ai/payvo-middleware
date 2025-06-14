-- =====================================================
-- Clear Specific User Data from Payvo Middleware Database
-- =====================================================
-- This script removes data for specific users while preserving:
-- - Table structure
-- - Other users' data
-- - Indexes and constraints
--
-- Usage: Replace 'USER_ID_HERE' with the actual user ID you want to delete
-- Or uncomment the section to delete all users

-- =====================================================
-- Option 1: Delete specific user data
-- =====================================================
-- Replace 'USER_ID_HERE' with the actual user UUID
/*
DO $$
DECLARE
    target_user_id UUID := 'USER_ID_HERE'; -- Replace with actual user ID
BEGIN
    -- Delete user-specific data in correct order
    DELETE FROM user_activity_logs WHERE user_id = target_user_id;
    DELETE FROM transaction_feedback WHERE user_id = target_user_id;
    DELETE FROM background_location_sessions WHERE user_id = target_user_id;
    DELETE FROM user_sessions WHERE user_id = target_user_id;
    DELETE FROM user_profiles WHERE id = target_user_id;
    
    RAISE NOTICE 'Deleted all data for user: %', target_user_id;
END $$;
*/

-- =====================================================
-- Option 2: Delete multiple specific users
-- =====================================================
-- Replace with actual user UUIDs
/*
DO $$
DECLARE
    target_user_ids UUID[] := ARRAY[
        'USER_ID_1_HERE',
        'USER_ID_2_HERE',
        'USER_ID_3_HERE'
    ]; -- Replace with actual user IDs
    user_id UUID;
BEGIN
    FOREACH user_id IN ARRAY target_user_ids
    LOOP
        -- Delete user-specific data in correct order
        DELETE FROM user_activity_logs WHERE user_id = user_id;
        DELETE FROM transaction_feedback WHERE user_id = user_id;
        DELETE FROM background_location_sessions WHERE user_id = user_id;
        DELETE FROM user_sessions WHERE user_id = user_id;
        DELETE FROM user_profiles WHERE id = user_id;
        
        RAISE NOTICE 'Deleted all data for user: %', user_id;
    END LOOP;
END $$;
*/

-- =====================================================
-- Option 3: Delete all user data (but keep cache tables)
-- =====================================================
-- Uncomment this section to delete all user data while preserving cache
/*
-- Delete all user-related data
DELETE FROM user_activity_logs;
DELETE FROM transaction_feedback;
DELETE FROM background_location_sessions;
DELETE FROM user_sessions;
DELETE FROM user_profiles;

-- Keep cache tables intact:
-- - terminal_cache
-- - location_cache
*/

-- =====================================================
-- Option 4: Interactive user selection
-- =====================================================
-- List all users first to help you choose
SELECT 
    id,
    username,
    full_name,
    created_at,
    last_login_at,
    is_active
FROM user_profiles
ORDER BY created_at DESC;

-- Count data for each user
SELECT 
    up.id,
    up.username,
    up.full_name,
    COUNT(DISTINCT us.id) as session_count,
    COUNT(DISTINCT ual.id) as activity_count,
    COUNT(DISTINCT tf.id) as transaction_count,
    COUNT(DISTINCT bls.session_id) as location_session_count
FROM user_profiles up
LEFT JOIN user_sessions us ON up.id = us.user_id
LEFT JOIN user_activity_logs ual ON up.id = ual.user_id
LEFT JOIN transaction_feedback tf ON up.id = tf.user_id
LEFT JOIN background_location_sessions bls ON up.id = bls.user_id
GROUP BY up.id, up.username, up.full_name
ORDER BY up.created_at DESC;

-- =====================================================
-- Verification queries
-- =====================================================
-- Check remaining data counts
SELECT 
    'user_profiles' as table_name, 
    COUNT(*) as row_count 
FROM user_profiles
UNION ALL
SELECT 
    'user_sessions' as table_name, 
    COUNT(*) as row_count 
FROM user_sessions
UNION ALL
SELECT 
    'user_activity_logs' as table_name, 
    COUNT(*) as row_count 
FROM user_activity_logs
UNION ALL
SELECT 
    'transaction_feedback' as table_name, 
    COUNT(*) as row_count 
FROM transaction_feedback
UNION ALL
SELECT 
    'background_location_sessions' as table_name, 
    COUNT(*) as row_count 
FROM background_location_sessions
ORDER BY table_name; 