-- =====================================================
-- Payvo Middleware - Database Setup & Extensions
-- =====================================================
-- Run this first to set up extensions and basic configuration
-- Version: 2.0
-- Created: 2024

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis" SCHEMA extensions;

-- Enable Row Level Security on auth.users (if not already enabled)
ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;

-- Create custom schemas if needed
CREATE SCHEMA IF NOT EXISTS payvo;

-- Set up timezone
SET timezone = 'UTC';

-- Create updated_at trigger function (used across multiple tables)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create location utility functions
CREATE OR REPLACE FUNCTION calculate_distance(
    lat1 DECIMAL(10,8),
    lng1 DECIMAL(11,8),
    lat2 DECIMAL(10,8),
    lng2 DECIMAL(11,8)
) RETURNS DECIMAL(10,2) AS $$
DECLARE
    earth_radius DECIMAL := 6371000; -- Earth radius in meters
    dlat DECIMAL;
    dlng DECIMAL;
    a DECIMAL;
    c DECIMAL;
BEGIN
    dlat := radians(lat2 - lat1);
    dlng := radians(lng2 - lng1);
    
    a := sin(dlat/2) * sin(dlat/2) + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2) * sin(dlng/2);
    c := 2 * atan2(sqrt(a), sqrt(1-a));
    
    RETURN earth_radius * c;
END;
$$ LANGUAGE plpgsql;

-- Create location hash function
CREATE OR REPLACE FUNCTION generate_location_hash(
    lat DECIMAL(10,8),
    lng DECIMAL(11,8),
    precision_meters INTEGER DEFAULT 50
) RETURNS VARCHAR(50) AS $$
DECLARE
    precision_factor DECIMAL;
    rounded_lat DECIMAL;
    rounded_lng DECIMAL;
BEGIN
    -- Calculate precision factor based on desired precision in meters
    -- Roughly 1 degree = 111,000 meters
    precision_factor := precision_meters / 111000.0;
    
    -- Round coordinates to the specified precision
    rounded_lat := ROUND(lat / precision_factor) * precision_factor;
    rounded_lng := ROUND(lng / precision_factor) * precision_factor;
    
    -- Generate hash
    RETURN MD5(rounded_lat::TEXT || ',' || rounded_lng::TEXT);
END;
$$ LANGUAGE plpgsql; 