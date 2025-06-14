-- =====================================================
-- Cache Management Functions
-- =====================================================

-- Function to get or create terminal cache entry
CREATE OR REPLACE FUNCTION get_terminal_cache(p_terminal_id TEXT)
RETURNS TABLE (
    terminal_id TEXT,
    mcc TEXT,
    confidence DECIMAL,
    merchant_name TEXT,
    transaction_count INTEGER,
    last_seen TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    -- Update hit count and last hit time
    UPDATE terminal_cache 
    SET hit_count = hit_count + 1,
        last_hit_at = NOW()
    WHERE terminal_cache.terminal_id = p_terminal_id;
    
    -- Return the cached data
    RETURN QUERY
    SELECT 
        tc.terminal_id,
        tc.mcc,
        tc.confidence,
        tc.merchant_name,
        tc.transaction_count,
        tc.last_seen
    FROM terminal_cache tc
    WHERE tc.terminal_id = p_terminal_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to update terminal cache
CREATE OR REPLACE FUNCTION update_terminal_cache(
    p_terminal_id TEXT,
    p_mcc TEXT,
    p_confidence DECIMAL DEFAULT 1.0,
    p_merchant_name TEXT DEFAULT NULL,
    p_merchant_category TEXT DEFAULT NULL,
    p_location_lat DECIMAL DEFAULT NULL,
    p_location_lng DECIMAL DEFAULT NULL,
    p_success BOOLEAN DEFAULT true
)
RETURNS VOID AS $$
DECLARE
    location_hash_val TEXT;
BEGIN
    -- Generate location hash if coordinates provided
    IF p_location_lat IS NOT NULL AND p_location_lng IS NOT NULL THEN
        location_hash_val := generate_location_hash(p_location_lat, p_location_lng, 3);
    END IF;
    
    INSERT INTO terminal_cache (
        terminal_id,
        mcc,
        confidence,
        merchant_name,
        merchant_category,
        location_lat,
        location_lng,
        location_hash,
        transaction_count,
        success_count,
        last_success_at,
        last_seen
    ) VALUES (
        p_terminal_id,
        p_mcc,
        p_confidence,
        p_merchant_name,
        p_merchant_category,
        p_location_lat,
        p_location_lng,
        location_hash_val,
        1,
        CASE WHEN p_success THEN 1 ELSE 0 END,
        CASE WHEN p_success THEN NOW() ELSE NULL END,
        NOW()
    )
    ON CONFLICT (terminal_id) DO UPDATE SET
        mcc = CASE 
            WHEN p_confidence > terminal_cache.confidence THEN p_mcc
            ELSE terminal_cache.mcc
        END,
        confidence = CASE 
            WHEN p_confidence > terminal_cache.confidence THEN p_confidence
            ELSE terminal_cache.confidence
        END,
        merchant_name = COALESCE(p_merchant_name, terminal_cache.merchant_name),
        merchant_category = COALESCE(p_merchant_category, terminal_cache.merchant_category),
        location_lat = COALESCE(p_location_lat, terminal_cache.location_lat),
        location_lng = COALESCE(p_location_lng, terminal_cache.location_lng),
        location_hash = COALESCE(location_hash_val, terminal_cache.location_hash),
        transaction_count = terminal_cache.transaction_count + 1,
        success_count = terminal_cache.success_count + CASE WHEN p_success THEN 1 ELSE 0 END,
        last_success_at = CASE WHEN p_success THEN NOW() ELSE terminal_cache.last_success_at END,
        last_seen = NOW(),
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get location cache
CREATE OR REPLACE FUNCTION get_location_cache(p_location_hash TEXT)
RETURNS TABLE (
    location_hash TEXT,
    predicted_mcc TEXT,
    confidence DECIMAL,
    merchant_density INTEGER,
    prediction_count INTEGER,
    accuracy_rate DECIMAL
) AS $$
BEGIN
    -- Update hit count and last hit time
    UPDATE location_cache 
    SET hit_count = hit_count + 1,
        last_hit_at = NOW()
    WHERE location_cache.location_hash = p_location_hash;
    
    -- Return the cached data
    RETURN QUERY
    SELECT 
        lc.location_hash,
        lc.predicted_mcc,
        lc.confidence,
        lc.merchant_density,
        lc.prediction_count,
        lc.accuracy_rate
    FROM location_cache lc
    WHERE lc.location_hash = p_location_hash;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to update location cache
CREATE OR REPLACE FUNCTION update_location_cache(
    p_location_hash TEXT,
    p_location_lat DECIMAL,
    p_location_lng DECIMAL,
    p_predicted_mcc TEXT,
    p_confidence DECIMAL DEFAULT 0.5,
    p_precision_level INTEGER DEFAULT 3,
    p_success BOOLEAN DEFAULT true
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO location_cache (
        location_hash,
        location_lat,
        location_lng,
        predicted_mcc,
        confidence,
        precision_level,
        prediction_count,
        success_count,
        accuracy_rate,
        last_updated
    ) VALUES (
        p_location_hash,
        p_location_lat,
        p_location_lng,
        p_predicted_mcc,
        p_confidence,
        p_precision_level,
        1,
        CASE WHEN p_success THEN 1 ELSE 0 END,
        CASE WHEN p_success THEN 1.0 ELSE 0.0 END,
        NOW()
    )
    ON CONFLICT (location_hash) DO UPDATE SET
        predicted_mcc = CASE 
            WHEN p_confidence > location_cache.confidence THEN p_predicted_mcc
            ELSE location_cache.predicted_mcc
        END,
        confidence = CASE 
            WHEN p_confidence > location_cache.confidence THEN p_confidence
            ELSE location_cache.confidence
        END,
        prediction_count = location_cache.prediction_count + 1,
        success_count = location_cache.success_count + CASE WHEN p_success THEN 1 ELSE 0 END,
        accuracy_rate = CASE 
            WHEN location_cache.prediction_count + 1 > 0 THEN 
                (location_cache.success_count + CASE WHEN p_success THEN 1 ELSE 0 END)::DECIMAL / 
                (location_cache.prediction_count + 1)
            ELSE 0.0
        END,
        last_updated = NOW(),
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to find nearby location cache entries
CREATE OR REPLACE FUNCTION get_nearby_location_cache(
    p_lat DECIMAL,
    p_lng DECIMAL,
    p_radius_meters INTEGER DEFAULT 500,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    location_hash TEXT,
    predicted_mcc TEXT,
    confidence DECIMAL,
    distance_meters DECIMAL,
    prediction_count INTEGER,
    accuracy_rate DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        lc.location_hash,
        lc.predicted_mcc,
        lc.confidence,
        calculate_distance(p_lat, p_lng, lc.location_lat, lc.location_lng) as distance_meters,
        lc.prediction_count,
        lc.accuracy_rate
    FROM location_cache lc
    WHERE calculate_distance(p_lat, p_lng, lc.location_lat, lc.location_lng) <= p_radius_meters
      AND lc.confidence > 0.3
    ORDER BY distance_meters ASC, lc.confidence DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to cleanup old cache entries
CREATE OR REPLACE FUNCTION cleanup_cache_entries(
    p_terminal_days_old INTEGER DEFAULT 30,
    p_location_days_old INTEGER DEFAULT 30,
    p_min_transaction_count INTEGER DEFAULT 2
)
RETURNS TABLE (
    terminals_cleaned INTEGER,
    locations_cleaned INTEGER
) AS $$
DECLARE
    terminal_count INTEGER;
    location_count INTEGER;
BEGIN
    -- Clean up terminal cache
    DELETE FROM terminal_cache 
    WHERE last_seen < NOW() - INTERVAL '1 day' * p_terminal_days_old
      AND transaction_count < p_min_transaction_count;
    
    GET DIAGNOSTICS terminal_count = ROW_COUNT;
    
    -- Clean up location cache
    DELETE FROM location_cache 
    WHERE last_updated < NOW() - INTERVAL '1 day' * p_location_days_old
      AND prediction_count < p_min_transaction_count;
    
    GET DIAGNOSTICS location_count = ROW_COUNT;
    
    RETURN QUERY SELECT terminal_count, location_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get cache statistics
CREATE OR REPLACE FUNCTION get_cache_statistics()
RETURNS TABLE (
    terminal_cache_count BIGINT,
    terminal_cache_hit_rate DECIMAL,
    location_cache_count BIGINT,
    location_cache_hit_rate DECIMAL,
    avg_terminal_confidence DECIMAL,
    avg_location_confidence DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM terminal_cache) as terminal_cache_count,
        (SELECT 
            CASE WHEN SUM(transaction_count) > 0 THEN 
                SUM(hit_count)::DECIMAL / SUM(transaction_count) 
            ELSE 0.0 END
         FROM terminal_cache) as terminal_cache_hit_rate,
        (SELECT COUNT(*) FROM location_cache) as location_cache_count,
        (SELECT 
            CASE WHEN SUM(prediction_count) > 0 THEN 
                SUM(hit_count)::DECIMAL / SUM(prediction_count) 
            ELSE 0.0 END
         FROM location_cache) as location_cache_hit_rate,
        (SELECT AVG(confidence) FROM terminal_cache) as avg_terminal_confidence,
        (SELECT AVG(confidence) FROM location_cache) as avg_location_confidence;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER; 