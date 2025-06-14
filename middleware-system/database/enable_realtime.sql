-- =====================================================
-- Payvo Middleware - Enable Realtime for All Tables
-- =====================================================
-- This script enables Supabase Realtime for all database tables
-- Execute this in Supabase SQL Editor to enable live updates
-- 
-- IMPORTANT: Run this AFTER deploying the main schema (supabase_deploy.sql)
--
-- What is Realtime?
-- Supabase Realtime allows clients to listen to database changes in real-time
-- using WebSockets, enabling live updates without polling
--
-- Benefits:
-- - Instant UI updates when data changes
-- - Real-time collaboration features
-- - Live monitoring and analytics
-- - Reduced server load (no polling)
-- - Better user experience with instant feedback

-- =====================================================
-- Enable Realtime for All Tables
-- =====================================================

-- Authentication & User Management Tables
-- =====================================================

-- User Profiles - Live profile updates, status changes, role modifications
-- Use cases: Profile editing, status indicators, role-based UI updates
ALTER PUBLICATION supabase_realtime ADD TABLE user_profiles;

-- User Sessions - Real-time login/logout tracking, session security monitoring
-- Use cases: Active user indicators, session management, security alerts
ALTER PUBLICATION supabase_realtime ADD TABLE user_sessions;

-- User Activity Logs - Live audit trails, security monitoring, user behavior analytics
-- Use cases: Real-time security monitoring, live activity feeds, audit dashboards
ALTER PUBLICATION supabase_realtime ADD TABLE user_activity_logs;

-- Core Business Logic Tables
-- =====================================================

-- Transaction Feedback - Real-time transaction monitoring, live prediction accuracy
-- Use cases: Live transaction status, real-time analytics, prediction monitoring
ALTER PUBLICATION supabase_realtime ADD TABLE transaction_feedback;

-- Background Location Sessions - Live location tracking status, session management
-- Use cases: Real-time location tracking, session status updates, live maps
ALTER PUBLICATION supabase_realtime ADD TABLE background_location_sessions;

-- Cache Tables - Performance & Intelligence
-- =====================================================

-- Terminal Cache - Real-time terminal data updates, MCC predictions
-- Use cases: Live terminal intelligence, prediction accuracy updates, cache monitoring
ALTER PUBLICATION supabase_realtime ADD TABLE terminal_cache;

-- Location Cache - Live spatial predictions, real-time location-based insights
-- Use cases: Live location intelligence, spatial analytics, prediction updates
ALTER PUBLICATION supabase_realtime ADD TABLE location_cache;

-- =====================================================
-- Realtime Use Cases by Table
-- =====================================================

/*
USER_PROFILES:
- Live profile picture updates
- Real-time status changes (online/offline)
- Role and permission changes
- Preference updates
- Department/team changes

USER_SESSIONS:
- Active session indicators
- Login/logout notifications
- Device management updates
- Security alerts for suspicious sessions
- Session expiration warnings

USER_ACTIVITY_LOGS:
- Live activity feeds
- Real-time security monitoring
- Audit trail updates
- User behavior analytics
- Compliance monitoring

TRANSACTION_FEEDBACK:
- Live transaction status updates
- Real-time prediction accuracy metrics
- Transaction success/failure notifications
- Live analytics dashboards
- Merchant category predictions

BACKGROUND_LOCATION_SESSIONS:
- Real-time location tracking status
- Live session management
- Location-based notifications
- Geofencing alerts
- Session expiration updates

TERMINAL_CACHE:
- Live terminal intelligence updates
- MCC prediction improvements
- Cache hit/miss monitoring
- Terminal verification status
- Performance metrics

LOCATION_CACHE:
- Live spatial predictions
- Location-based intelligence updates
- Cache performance monitoring
- Spatial analytics updates
- Prediction accuracy improvements
*/

-- =====================================================
-- Client-Side Usage Examples
-- =====================================================

/*
JavaScript/TypeScript Example:

import { createClient } from '@supabase/supabase-js'

const supabase = createClient(url, key)

// Listen to user profile changes
supabase
  .channel('user_profiles')
  .on('postgres_changes', 
    { event: '*', schema: 'public', table: 'user_profiles' },
    (payload) => {
      console.log('Profile updated:', payload)
      // Update UI in real-time
    }
  )
  .subscribe()

// Listen to transaction feedback
supabase
  .channel('transactions')
  .on('postgres_changes',
    { event: 'INSERT', schema: 'public', table: 'transaction_feedback' },
    (payload) => {
      console.log('New transaction:', payload)
      // Show live transaction updates
    }
  )
  .subscribe()

// Listen to location sessions
supabase
  .channel('location_sessions')
  .on('postgres_changes',
    { event: '*', schema: 'public', table: 'background_location_sessions' },
    (payload) => {
      console.log('Location session updated:', payload)
      // Update live location tracking UI
    }
  )
  .subscribe()
*/

-- =====================================================
-- Performance Considerations
-- =====================================================

/*
IMPORTANT NOTES:

1. HIGH VOLUME TABLES:
   - user_activity_logs can generate high volume of events
   - Consider filtering by specific users or actions on client-side
   - Use row-level security to limit what users can see

2. BANDWIDTH USAGE:
   - Realtime uses WebSocket connections
   - Monitor bandwidth usage in production
   - Consider using filters to reduce unnecessary updates

3. CONNECTION LIMITS:
   - Supabase has connection limits per plan
   - Implement connection pooling for high-traffic applications
   - Use presence features for user status tracking

4. SECURITY:
   - All realtime events respect Row Level Security (RLS)
   - Users only receive updates for data they have access to
   - Sensitive data is automatically filtered

5. DEBUGGING:
   - Use Supabase Dashboard to monitor realtime connections
   - Check realtime logs for troubleshooting
   - Test with multiple clients to ensure proper filtering
*/

-- Verification Query
SELECT 
    schemaname,
    tablename,
    'Realtime enabled' as status
FROM pg_publication_tables 
WHERE pubname = 'supabase_realtime'
ORDER BY tablename;

-- Success message
SELECT 'All tables enabled for Supabase Realtime successfully!' as status; 