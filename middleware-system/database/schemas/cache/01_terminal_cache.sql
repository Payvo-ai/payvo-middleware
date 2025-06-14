-- =====================================================
-- Terminal Cache Table
-- =====================================================
-- Caches terminal ID to MCC mappings for faster lookups

CREATE TABLE IF NOT EXISTS terminal_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    terminal_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- MCC Information
    mcc VARCHAR(4) NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 1.0,
    
    -- Merchant Information
    merchant_name VARCHAR(255),
    merchant_category VARCHAR(100),
    
    -- Statistics
    transaction_count INTEGER DEFAULT 1,
    success_count INTEGER DEFAULT 0,
    last_success_at TIMESTAMP WITH TIME ZONE,
    
    -- Location Context (optional)
    location_lat DECIMAL(10,8),
    location_lng DECIMAL(11,8),
    location_hash VARCHAR(50),
    
    -- Cache Management
    hit_count INTEGER DEFAULT 0,
    last_hit_at TIMESTAMP WITH TIME ZONE,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Validation
    is_verified BOOLEAN DEFAULT false,
    verification_source VARCHAR(50), -- 'manual', 'feedback', 'external_api'
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add RLS
ALTER TABLE terminal_cache ENABLE ROW LEVEL SECURITY;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_terminal_cache_terminal_id ON terminal_cache(terminal_id);
CREATE INDEX IF NOT EXISTS idx_terminal_cache_mcc ON terminal_cache(mcc);
CREATE INDEX IF NOT EXISTS idx_terminal_cache_confidence ON terminal_cache(confidence);
CREATE INDEX IF NOT EXISTS idx_terminal_cache_last_seen ON terminal_cache(last_seen);
CREATE INDEX IF NOT EXISTS idx_terminal_cache_transaction_count ON terminal_cache(transaction_count);
CREATE INDEX IF NOT EXISTS idx_terminal_cache_is_verified ON terminal_cache(is_verified);
CREATE INDEX IF NOT EXISTS idx_terminal_cache_location_hash ON terminal_cache(location_hash);

-- Composite indexes for performance
CREATE INDEX IF NOT EXISTS idx_terminal_cache_lookup ON terminal_cache(terminal_id, mcc, confidence) WHERE confidence > 0.5;
CREATE INDEX IF NOT EXISTS idx_terminal_cache_cleanup ON terminal_cache(last_seen, transaction_count) WHERE transaction_count < 5;

-- Add updated_at trigger
CREATE TRIGGER update_terminal_cache_updated_at 
    BEFORE UPDATE ON terminal_cache 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add constraints
ALTER TABLE terminal_cache ADD CONSTRAINT confidence_range 
    CHECK (confidence >= 0.0 AND confidence <= 1.0);

ALTER TABLE terminal_cache ADD CONSTRAINT transaction_count_positive 
    CHECK (transaction_count >= 0);

ALTER TABLE terminal_cache ADD CONSTRAINT hit_count_positive 
    CHECK (hit_count >= 0); 