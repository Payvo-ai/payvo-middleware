-- =====================================================
-- Payvo Middleware Database Schema Deployment
-- =====================================================
-- This script deploys the complete database schema for the Payvo Middleware system
-- Execute this script on a fresh Supabase database to set up all tables, functions, and policies

-- =====================================================
-- 1. Setup and Extensions
-- =====================================================
\echo 'Setting up database extensions and utilities...'
\i schemas/00_setup.sql

-- =====================================================
-- 2. Authentication Tables
-- =====================================================
\echo 'Creating authentication tables...'
\i schemas/auth/01_user_profiles.sql
\i schemas/auth/02_user_sessions.sql
\i schemas/auth/03_user_activity_logs.sql

-- =====================================================
-- 3. Core Business Tables
-- =====================================================
\echo 'Creating core business tables...'
\i schemas/core/01_transaction_feedback.sql
\i schemas/core/02_background_location_sessions.sql

-- =====================================================
-- 4. Cache Tables
-- =====================================================
\echo 'Creating cache tables...'
\i schemas/cache/01_terminal_cache.sql
\i schemas/cache/02_location_cache.sql

-- =====================================================
-- 5. Database Functions
-- =====================================================
\echo 'Creating database functions...'
\i schemas/functions/01_auth_functions.sql
\i schemas/functions/02_cache_functions.sql

-- =====================================================
-- 6. Row Level Security Policies
-- =====================================================
\echo 'Setting up Row Level Security policies...'
\i schemas/policies/01_auth_policies.sql
\i schemas/policies/02_core_policies.sql

-- =====================================================
-- 7. Performance Indexes
-- =====================================================
\echo 'Creating performance indexes...'
\i schemas/indexes/01_performance_indexes.sql

-- =====================================================
-- 8. Triggers and Automation
-- =====================================================
\echo 'Setting up triggers and automation...'
\i schemas/99_triggers.sql

-- =====================================================
-- 9. Initial Data and Configuration
-- =====================================================
\echo 'Setting up initial configuration...'

-- Create default admin user profile structure (to be populated after first admin signup)
-- This is just the structure - actual admin user will be created through Supabase Auth

-- Insert some sample MCC codes for reference
INSERT INTO terminal_cache (terminal_id, mcc, confidence, merchant_name, merchant_category, is_verified, verification_source) VALUES
('SAMPLE_GROCERY_001', '5411', 1.0, 'Sample Grocery Store', 'Grocery Stores', true, 'manual'),
('SAMPLE_GAS_001', '5542', 1.0, 'Sample Gas Station', 'Automated Fuel Dispensers', true, 'manual'),
('SAMPLE_RESTAURANT_001', '5812', 1.0, 'Sample Restaurant', 'Eating Places, Restaurants', true, 'manual'),
('SAMPLE_PHARMACY_001', '5912', 1.0, 'Sample Pharmacy', 'Drug Stores and Pharmacies', true, 'manual')
ON CONFLICT (terminal_id) DO NOTHING;

-- Insert some sample location cache entries
INSERT INTO location_cache (location_hash, location_lat, location_lng, predicted_mcc, confidence, is_verified, verification_source) VALUES
('sample_hash_001', 37.7749, -122.4194, '5411', 0.85, true, 'manual'),
('sample_hash_002', 37.7849, -122.4094, '5542', 0.90, true, 'manual'),
('sample_hash_003', 37.7649, -122.4294, '5812', 0.80, true, 'manual')
ON CONFLICT (location_hash) DO NOTHING;

-- =====================================================
-- 10. Database Statistics and Optimization
-- =====================================================
\echo 'Updating database statistics...'

-- Analyze tables for query optimization
ANALYZE user_profiles;
ANALYZE user_sessions;
ANALYZE user_activity_logs;
ANALYZE transaction_feedback;
ANALYZE background_location_sessions;
ANALYZE terminal_cache;
ANALYZE location_cache;

-- =====================================================
-- 11. Verification and Health Check
-- =====================================================
\echo 'Running database health check...'

-- Verify all tables exist
DO $$
DECLARE
    table_count INTEGER;
    expected_tables TEXT[] := ARRAY[
        'user_profiles',
        'user_sessions', 
        'user_activity_logs',
        'transaction_feedback',
        'background_location_sessions',
        'terminal_cache',
        'location_cache'
    ];
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY expected_tables
    LOOP
        SELECT COUNT(*) INTO table_count 
        FROM information_schema.tables 
        WHERE table_name = table_name AND table_schema = 'public';
        
        IF table_count = 0 THEN
            RAISE EXCEPTION 'Table % was not created successfully', table_name;
        ELSE
            RAISE NOTICE 'Table % created successfully', table_name;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'All tables created successfully!';
END $$;

-- Verify RLS is enabled
DO $$
DECLARE
    rls_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO rls_count
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relrowsecurity = true 
    AND n.nspname = 'public'
    AND c.relkind = 'r';
    
    RAISE NOTICE 'Row Level Security enabled on % tables', rls_count;
END $$;

-- Verify functions exist
DO $$
DECLARE
    function_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO function_count
    FROM information_schema.routines
    WHERE routine_schema = 'public'
    AND routine_type = 'FUNCTION';
    
    RAISE NOTICE '% custom functions created', function_count;
END $$;

\echo 'Database schema deployment completed successfully!'
\echo ''
\echo 'Next steps:'
\echo '1. Configure your Supabase project settings'
\echo '2. Set up authentication providers'
\echo '3. Create your first admin user through Supabase Auth'
\echo '4. Update your application connection strings'
\echo '5. Test the API endpoints'
\echo ''
\echo 'For more information, see the README.md file.' 