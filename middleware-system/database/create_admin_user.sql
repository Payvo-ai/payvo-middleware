-- =====================================================
-- Create Admin User for Payvo Middleware
-- =====================================================
-- This script creates an admin user account using Supabase Auth
-- Execute this in Supabase SQL Editor after deploying the schema

-- Create the user account
-- Note: In production, you should use Supabase Dashboard or Auth API
-- This is a direct database approach for initial setup

INSERT INTO auth.users (
    instance_id,
    id,
    aud,
    role,
    email,
    encrypted_password,
    email_confirmed_at,
    recovery_sent_at,
    last_sign_in_at,
    raw_app_meta_data,
    raw_user_meta_data,
    created_at,
    updated_at,
    confirmation_token,
    email_change,
    email_change_token_new,
    recovery_token
) VALUES (
    '00000000-0000-0000-0000-000000000000',
    gen_random_uuid(),
    'authenticated',
    'authenticated',
    'iman@payvo.ai',
    crypt('TempPassword123!', gen_salt('bf')), -- Temporary password
    NOW(),
    NOW(),
    NOW(),
    '{"provider": "email", "providers": ["email"]}',
    '{"full_name": "Iman Malhi", "employee_id": "EMP001", "department": "Engineering", "role": "Admin"}',
    NOW(),
    NOW(),
    '',
    '',
    '',
    ''
);

-- The user profile will be automatically created by the trigger
-- But let's verify and update if needed
DO $$
DECLARE
    user_uuid UUID;
BEGIN
    -- Get the user ID we just created
    SELECT id INTO user_uuid FROM auth.users WHERE email = 'iman@payvo.ai';
    
    -- Update the user profile with additional details
    -- Note: username is optional - email is used as the user identifier
    UPDATE user_profiles 
    SET 
        full_name = 'Iman Malhi',
        employee_id = 'EMP001',
        department = 'Engineering',
        role = 'Admin',
        is_active = true,
        is_verified = true,
        preferences = jsonb_build_object(
            'notifications', jsonb_build_object(
                'email', true,
                'push', true,
                'transaction_alerts', true,
                'weekly_summary', true
            ),
            'privacy', jsonb_build_object(
                'location_tracking', true,
                'analytics', true,
                'data_sharing', false
            ),
            'app_settings', jsonb_build_object(
                'theme', 'light',
                'currency', 'USD',
                'auto_refresh', true,
                'refresh_interval', 30
            )
        )
    WHERE id = user_uuid;
    
    -- Output success message
    RAISE NOTICE 'Admin user created successfully for: iman@payvo.ai';
    RAISE NOTICE 'Temporary password: TempPassword123!';
    RAISE NOTICE 'User ID: %', user_uuid;
END $$;

-- Verify the user was created
SELECT 
    u.id,
    u.email,
    u.created_at,
    u.email_confirmed_at,
    p.full_name,
    p.username,
    p.employee_id,
    p.department,
    p.role,
    p.is_active,
    p.is_verified
FROM auth.users u
LEFT JOIN user_profiles p ON u.id = p.id
WHERE u.email = 'iman@payvo.ai';

-- =====================================================
-- IMPORTANT NOTES:
-- =====================================================
-- 1. The temporary password is: TempPassword123!
-- 2. You should change this password immediately after first login
-- 3. The user profile will be automatically created by the database trigger
-- 4. Username is optional - email is used as the user identifier for transactions
-- 5. This approach bypasses email verification - the account is immediately active
-- 6. You can change your password using the app's Settings > Change Password feature
-- ===================================================== 