# Payvo Middleware Database Schema

This directory contains the complete database schema for the Payvo Middleware system, organized into modular files for better maintainability and deployment flexibility.

## 📁 Directory Structure

```
database/
├── schemas/
│   ├── 00_setup.sql                    # Extensions and utility functions
│   ├── auth/                           # Authentication-related tables
│   │   ├── 01_user_profiles.sql        # Extended user profiles
│   │   ├── 02_user_sessions.sql        # Session management
│   │   └── 03_user_activity_logs.sql   # Audit trail
│   ├── core/                           # Core business tables
│   │   ├── 01_transaction_feedback.sql # ML training data
│   │   └── 02_background_location_sessions.sql # Location tracking
│   ├── cache/                          # Caching tables
│   │   ├── 01_terminal_cache.sql       # Terminal-to-MCC mapping
│   │   └── 02_location_cache.sql       # Location-based predictions
│   ├── functions/                      # Database functions
│   │   ├── 01_auth_functions.sql       # Authentication utilities
│   │   └── 02_cache_functions.sql      # Cache management
│   ├── policies/                       # Row Level Security
│   │   ├── 01_auth_policies.sql        # Auth table policies
│   │   └── 02_core_policies.sql        # Business table policies
│   ├── indexes/                        # Performance optimization
│   │   └── 01_performance_indexes.sql  # Query optimization indexes
│   └── 99_triggers.sql                 # Database triggers
├── deploy_schema.sql                   # Master deployment script
└── README.md                          # This file
```

## 🚀 Quick Deployment

### Option 1: Full Deployment (Recommended)
```bash
# Navigate to the database directory
cd middleware-system/database

# Execute the master deployment script
psql -h your-supabase-host -U postgres -d postgres -f deploy_schema.sql
```

### Option 2: Individual File Deployment
```bash
# Deploy files in order
psql -h your-supabase-host -U postgres -d postgres -f schemas/00_setup.sql
psql -h your-supabase-host -U postgres -d postgres -f schemas/auth/01_user_profiles.sql
# ... continue with other files in order
```

## 📊 Database Schema Overview

### Authentication System
- **user_profiles**: Extended user information beyond Supabase Auth
- **user_sessions**: Detailed session tracking with device information
- **user_activity_logs**: Comprehensive audit trail for compliance

### Core Business Logic
- **transaction_feedback**: ML training data and transaction history
- **background_location_sessions**: Location tracking session management

### Performance Optimization
- **terminal_cache**: Fast terminal-to-MCC lookups
- **location_cache**: Location-based MCC predictions

## 🔐 Security Features

### Row Level Security (RLS)
All tables have RLS enabled with policies ensuring:
- Users can only access their own data
- Admins have appropriate elevated access
- System operations are properly authorized
- Audit trails are immutable

### Data Privacy
- Personal data is isolated per user
- Analytics functions provide anonymized access
- Compliance with data retention policies
- Automatic cleanup of expired sessions

## 🛠️ Key Features

### 1. Authentication Integration
- Seamless integration with Supabase Auth
- Automatic user profile creation
- Session management with device tracking
- Comprehensive activity logging

### 2. Machine Learning Support
- Transaction feedback collection
- Confidence scoring for predictions
- Location-based learning
- Performance metrics tracking

### 3. Caching System
- Terminal-to-MCC mapping cache
- Location-based prediction cache
- Automatic cache invalidation
- Performance statistics

### 4. Location Services
- PostGIS integration for spatial queries
- Location hashing for privacy
- Distance calculations
- Geofenced predictions

## 📈 Performance Optimizations

### Indexes
- Composite indexes for common query patterns
- Partial indexes for filtered queries
- Spatial indexes for location queries
- Full-text search for merchant data

### Statistics
- Multi-column statistics for query optimization
- Regular ANALYZE operations
- Performance monitoring functions

## 🔧 Database Functions

### Authentication Functions
- `create_user_profile()`: Auto-create profiles for new users
- `create_user_session()`: Manage user sessions
- `validate_session_token()`: Token validation
- `cleanup_expired_sessions()`: Automatic cleanup

### Cache Functions
- `get_terminal_cache()`: Retrieve cached terminal data
- `update_terminal_cache()`: Update cache with new data
- `get_nearby_location_cache()`: Spatial cache queries
- `cleanup_cache_entries()`: Cache maintenance

### Utility Functions
- `calculate_distance()`: Haversine distance calculation
- `generate_location_hash()`: Privacy-preserving location hashing
- `anonymize_user_data()`: Data anonymization for analytics

## 🔄 Triggers and Automation

### Automatic Operations
- User profile creation on auth.users insert
- Activity logging for audit compliance
- Cache statistics updates
- Data validation on insert/update
- Expired session cleanup

### Data Validation
- MCC code format validation
- Coordinate range validation
- Confidence score validation
- Automatic location hash generation

## 📋 Migration and Maintenance

### Regular Maintenance Tasks
```sql
-- Clean up expired sessions
SELECT cleanup_expired_sessions();

-- Clean up old cache entries
SELECT * FROM cleanup_cache_entries(30, 30, 2);

-- Update database statistics
ANALYZE;

-- Check cache performance
SELECT * FROM get_cache_statistics();
```

### Backup Considerations
- All tables include audit fields (created_at, updated_at)
- Activity logs provide complete audit trail
- Cache tables can be rebuilt from source data
- Consider retention policies for large tables

## 🚨 Important Notes

### Before Deployment
1. Ensure Supabase project is created
2. Configure authentication providers
3. Set up environment variables
4. Review and adjust RLS policies for your use case

### After Deployment
1. Create your first admin user through Supabase Auth
2. Test authentication flows
3. Verify RLS policies are working
4. Set up monitoring and alerting
5. Configure backup schedules

### Security Considerations
- Review all RLS policies before production
- Ensure proper API key management
- Set up monitoring for suspicious activity
- Regular security audits of access patterns

## 📞 Support

For issues or questions:
1. Check the application logs
2. Review Supabase dashboard for errors
3. Verify RLS policies are correctly applied
4. Check database connection settings

## 🔄 Version History

- **v1.0**: Initial schema with authentication and core tables
- **v1.1**: Added caching system and performance optimizations
- **v1.2**: Enhanced security policies and audit trails
- **v1.3**: Added location services and spatial indexing

---

**Note**: This schema is designed for Supabase PostgreSQL. Some features may need adjustment for other PostgreSQL deployments. 