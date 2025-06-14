-- =====================================================
-- Clear All Data from Payvo Middleware Database
-- =====================================================
-- This script removes ALL DATA from all tables while preserving:
-- - Table structure
-- - Indexes
-- - Constraints
-- - Row Level Security policies
-- - Functions and triggers
--
-- ⚠️  WARNING: This will permanently delete ALL data!
-- ⚠️  Make sure you have backups if needed!
--
-- Execute this in Supabase SQL Editor to clear all data

-- =====================================================
-- Disable triggers temporarily to avoid cascading issues
-- =====================================================
SET session_replication_role = replica;

-- =====================================================
-- Clear all data from tables (order matters due to foreign keys)
-- =====================================================

-- 1. Clear cache tables first (no foreign key dependencies)
TRUNCATE TABLE terminal_cache RESTART IDENTITY CASCADE;
TRUNCATE TABLE location_cache RESTART IDENTITY CASCADE;

-- 2. Clear activity logs (references user_sessions)
TRUNCATE TABLE user_activity_logs RESTART IDENTITY CASCADE;

-- 3. Clear transaction feedback (references auth.users)
TRUNCATE TABLE transaction_feedback RESTART IDENTITY CASCADE;

-- 4. Clear background location sessions (references auth.users)
TRUNCATE TABLE background_location_sessions RESTART IDENTITY CASCADE;

-- 5. Clear user sessions (references auth.users)
TRUNCATE TABLE user_sessions RESTART IDENTITY CASCADE;

-- 6. Clear user profiles (references auth.users)
TRUNCATE TABLE user_profiles RESTART IDENTITY CASCADE;

-- =====================================================
-- Re-enable triggers
-- =====================================================
SET session_replication_role = DEFAULT;

-- =====================================================
-- Reset sequences (if any auto-increment columns exist)
-- =====================================================
-- Note: Most tables use UUID primary keys, so this may not be necessary
-- But included for completeness

-- =====================================================
-- Verification - Check that all tables are empty
-- =====================================================
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
UNION ALL
SELECT 
    'terminal_cache' as table_name, 
    COUNT(*) as row_count 
FROM terminal_cache
UNION ALL
SELECT 
    'location_cache' as table_name, 
    COUNT(*) as row_count 
FROM location_cache
ORDER BY table_name;

-- Success message
SELECT 'All table data cleared successfully! Tables and structure preserved.' as status; 