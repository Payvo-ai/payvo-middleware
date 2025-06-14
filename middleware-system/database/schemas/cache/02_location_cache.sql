-- =====================================================
-- Location Cache Table
-- =====================================================
-- Caches location-based MCC predictions for faster lookups

CREATE TABLE IF NOT EXISTS location_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_hash VARCHAR(50) UNIQUE NOT NULL,
    
    -- Location Information
    location_lat DECIMAL(10,8) NOT NULL,
    location_lng DECIMAL(11,8) NOT NULL,
    precision_level INTEGER DEFAULT 3, -- Hash precision level
    radius_meters INTEGER DEFAULT 100,
    
    -- MCC Predictions
    predicted_mcc VARCHAR(4) NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 0.5,
    
    -- Context Information
    merchant_density INTEGER DEFAULT 0,
    dominant_category VARCHAR(100),
    business_hours JSONB DEFAULT '{}'::jsonb,
    
    -- Statistics
    prediction_count INTEGER DEFAULT 1,
    success_count INTEGER DEFAULT 0,
    accuracy_rate DECIMAL(3,2) DEFAULT 0.0,
    
    -- Cache Management
    hit_count INTEGER DEFAULT 0,
    last_hit_at TIMESTAMP WITH TIME ZONE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Validation
    is_verified BOOLEAN DEFAULT false,
    verification_source VARCHAR(50), -- 'manual', 'feedback', 'external_api'
    
    -- Environmental Context
    wifi_networks JSONB DEFAULT '[]'::jsonb,
    ble_beacons JSONB DEFAULT '[]'::jsonb,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add RLS
ALTER TABLE location_cache ENABLE ROW LEVEL SECURITY;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_location_cache_hash ON location_cache(location_hash);
CREATE INDEX IF NOT EXISTS idx_location_cache_mcc ON location_cache(predicted_mcc);
CREATE INDEX IF NOT EXISTS idx_location_cache_confidence ON location_cache(confidence);
CREATE INDEX IF NOT EXISTS idx_location_cache_last_updated ON location_cache(last_updated);
CREATE INDEX IF NOT EXISTS idx_location_cache_prediction_count ON location_cache(prediction_count);
CREATE INDEX IF NOT EXISTS idx_location_cache_is_verified ON location_cache(is_verified);

-- Spatial index for location queries
CREATE INDEX IF NOT EXISTS idx_location_cache_spatial ON location_cache USING GIST (
    ST_Point(location_lng, location_lat)
);

-- Composite indexes for performance
CREATE INDEX IF NOT EXISTS idx_location_cache_lookup ON location_cache(location_hash, predicted_mcc, confidence) 
    WHERE confidence > 0.3;
CREATE INDEX IF NOT EXISTS idx_location_cache_cleanup ON location_cache(last_updated, prediction_count) 
    WHERE prediction_count < 3;

-- Add updated_at trigger
CREATE TRIGGER update_location_cache_updated_at 
    BEFORE UPDATE ON location_cache 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add constraints
ALTER TABLE location_cache ADD CONSTRAINT confidence_range 
    CHECK (confidence >= 0.0 AND confidence <= 1.0);

ALTER TABLE location_cache ADD CONSTRAINT accuracy_rate_range 
    CHECK (accuracy_rate >= 0.0 AND accuracy_rate <= 1.0);

ALTER TABLE location_cache ADD CONSTRAINT prediction_count_positive 
    CHECK (prediction_count >= 0);

ALTER TABLE location_cache ADD CONSTRAINT hit_count_positive 
    CHECK (hit_count >= 0);

ALTER TABLE location_cache ADD CONSTRAINT precision_level_valid 
    CHECK (precision_level >= 1 AND precision_level <= 12);

ALTER TABLE location_cache ADD CONSTRAINT radius_positive 
    CHECK (radius_meters > 0); 