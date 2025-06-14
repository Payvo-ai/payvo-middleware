-- =====================================================
-- Drop All Tables and Database Objects
-- =====================================================
-- This script completely removes ALL tables, functions, triggers, and policies
-- ⚠️  WARNING: This will permanently delete EVERYTHING!
-- ⚠️  You will need to re-run supabase_deploy.sql to recreate the schema
--
-- Execute this in Supabase SQL Editor to drop everything

-- =====================================================
-- Drop all triggers first
-- =====================================================
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
DROP TRIGGER IF EXISTS update_user_sessions_updated_at ON user_sessions;
DROP TRIGGER IF EXISTS update_transaction_feedback_updated_at ON transaction_feedback;
DROP TRIGGER IF EXISTS update_bg_sessions_updated_at ON background_location_sessions;
DROP TRIGGER IF EXISTS update_terminal_cache_updated_at ON terminal_cache;
DROP TRIGGER IF EXISTS update_location_cache_updated_at ON location_cache;

-- =====================================================
-- Remove tables from realtime publication (ignore errors if tables don't exist)
-- =====================================================
DO $$
BEGIN
    -- Remove tables from realtime publication
    -- Using DO block to handle cases where tables might not exist in publication
    BEGIN
        ALTER PUBLICATION supabase_realtime DROP TABLE user_profiles;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'user_profiles not in publication or does not exist';
    END;
    
    BEGIN
        ALTER PUBLICATION supabase_realtime DROP TABLE user_sessions;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'user_sessions not in publication or does not exist';
    END;
    
    BEGIN
        ALTER PUBLICATION supabase_realtime DROP TABLE user_activity_logs;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'user_activity_logs not in publication or does not exist';
    END;
    
    BEGIN
        ALTER PUBLICATION supabase_realtime DROP TABLE transaction_feedback;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'transaction_feedback not in publication or does not exist';
    END;
    
    BEGIN
        ALTER PUBLICATION supabase_realtime DROP TABLE background_location_sessions;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'background_location_sessions not in publication or does not exist';
    END;
    
    BEGIN
        ALTER PUBLICATION supabase_realtime DROP TABLE terminal_cache;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'terminal_cache not in publication or does not exist';
    END;
    
    BEGIN
        ALTER PUBLICATION supabase_realtime DROP TABLE location_cache;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'location_cache not in publication or does not exist';
    END;
END $$;

-- =====================================================
-- Drop all tables (order matters due to foreign keys)
-- =====================================================

-- Drop tables with foreign key dependencies first
DROP TABLE IF EXISTS user_activity_logs CASCADE;
DROP TABLE IF EXISTS transaction_feedback CASCADE;
DROP TABLE IF EXISTS background_location_sessions CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;

-- Drop cache tables
DROP TABLE IF EXISTS terminal_cache CASCADE;
DROP TABLE IF EXISTS location_cache CASCADE;

-- =====================================================
-- Drop all custom functions
-- =====================================================
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
DROP FUNCTION IF EXISTS create_user_profile() CASCADE;
DROP FUNCTION IF EXISTS update_user_last_login(UUID) CASCADE;
DROP FUNCTION IF EXISTS create_user_session(UUID, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, INET, TEXT, TEXT, TEXT, TEXT, TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS cleanup_expired_sessions() CASCADE;
DROP FUNCTION IF EXISTS calculate_distance(DECIMAL, DECIMAL, DECIMAL, DECIMAL) CASCADE;
DROP FUNCTION IF EXISTS generate_location_hash(DECIMAL, DECIMAL, INTEGER) CASCADE;

-- =====================================================
-- Drop custom schemas (if any)
-- =====================================================
DROP SCHEMA IF EXISTS payvo CASCADE;

-- =====================================================
-- Verification - List remaining tables
-- =====================================================
SELECT 
    schemaname,
    tablename,
    'Still exists' as status
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN (
    'user_profiles',
    'user_sessions', 
    'user_activity_logs',
    'transaction_feedback',
    'background_location_sessions',
    'terminal_cache',
    'location_cache'
  );

-- Success message
SELECT 'All tables and database objects dropped successfully!' as status; 