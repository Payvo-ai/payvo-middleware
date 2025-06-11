"""
Configuration settings for enhanced MCC prediction services
Manages API keys, service settings, and feature flags
"""

import os
from typing import Dict, Any, Optional
from decimal import Decimal
from app.utils.mcc_categories import get_all_mcc_categories


class EnhancedServicesConfig:
    """Configuration for enhanced MCC prediction services"""
    
    # Google Places API Configuration
    GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
    GOOGLE_PLACES_ENABLED = os.getenv("GOOGLE_PLACES_ENABLED", "false").lower() == "true"
    GOOGLE_PLACES_RADIUS_METERS = int(os.getenv("GOOGLE_PLACES_RADIUS_METERS", "200"))
    GOOGLE_PLACES_MAX_RESULTS = int(os.getenv("GOOGLE_PLACES_MAX_RESULTS", "20"))
    
    # Foursquare API Configuration
    FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY", "")
    FOURSQUARE_ENABLED = os.getenv("FOURSQUARE_ENABLED", "false").lower() == "true"
    FOURSQUARE_RADIUS_METERS = int(os.getenv("FOURSQUARE_RADIUS_METERS", "200"))
    FOURSQUARE_MAX_RESULTS = int(os.getenv("FOURSQUARE_MAX_RESULTS", "20"))
    
    # Cache Configuration
    LOCATION_CACHE_TTL_HOURS = int(os.getenv("LOCATION_CACHE_TTL_HOURS", "24"))
    TERMINAL_CACHE_TTL_HOURS = int(os.getenv("TERMINAL_CACHE_TTL_HOURS", "12"))
    FINGERPRINT_CACHE_TTL_HOURS = int(os.getenv("FINGERPRINT_CACHE_TTL_HOURS", "6"))
    HISTORICAL_CACHE_TTL_HOURS = int(os.getenv("HISTORICAL_CACHE_TTL_HOURS", "1"))
    
    # Service Feature Flags
    ENHANCED_LOCATION_ENABLED = os.getenv("ENHANCED_LOCATION_ENABLED", "true").lower() == "true"
    ENHANCED_TERMINAL_ENABLED = os.getenv("ENHANCED_TERMINAL_ENABLED", "true").lower() == "true"
    ENHANCED_FINGERPRINT_ENABLED = os.getenv("ENHANCED_FINGERPRINT_ENABLED", "true").lower() == "true"
    ENHANCED_HISTORICAL_ENABLED = os.getenv("ENHANCED_HISTORICAL_ENABLED", "true").lower() == "true"
    
    # Confidence Thresholds
    MIN_LOCATION_CONFIDENCE = float(os.getenv("MIN_LOCATION_CONFIDENCE", "0.5"))
    MIN_TERMINAL_CONFIDENCE = float(os.getenv("MIN_TERMINAL_CONFIDENCE", "0.6"))
    MIN_FINGERPRINT_CONFIDENCE = float(os.getenv("MIN_FINGERPRINT_CONFIDENCE", "0.4"))
    MIN_HISTORICAL_CONFIDENCE = float(os.getenv("MIN_HISTORICAL_CONFIDENCE", "0.5"))
    
    # Analysis Settings
    DEFAULT_SEARCH_RADIUS_METERS = int(os.getenv("DEFAULT_SEARCH_RADIUS_METERS", "200"))
    MAX_SEARCH_RADIUS_METERS = int(os.getenv("MAX_SEARCH_RADIUS_METERS", "1000"))
    MIN_SEARCH_RADIUS_METERS = int(os.getenv("MIN_SEARCH_RADIUS_METERS", "50"))
    
    # Database Settings
    ENABLE_DATA_COLLECTION = os.getenv("ENABLE_DATA_COLLECTION", "true").lower() == "true"
    ENABLE_LEARNING = os.getenv("ENABLE_LEARNING", "true").lower() == "true"
    
    # Performance Settings
    MAX_CONCURRENT_API_CALLS = int(os.getenv("MAX_CONCURRENT_API_CALLS", "5"))
    API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "10"))
    
    # Prediction Weights (must sum to ~1.0)
    LOCATION_WEIGHT = float(os.getenv("LOCATION_WEIGHT", "0.35"))
    HISTORICAL_WEIGHT = float(os.getenv("HISTORICAL_WEIGHT", "0.25"))
    TERMINAL_WEIGHT = float(os.getenv("TERMINAL_WEIGHT", "0.20"))
    WIFI_WEIGHT = float(os.getenv("WIFI_WEIGHT", "0.10"))
    BLE_WEIGHT = float(os.getenv("BLE_WEIGHT", "0.10"))
    
    @classmethod
    def get_google_places_config(cls) -> Dict[str, Any]:
        """Get Google Places API configuration"""
        return {
            "api_key": cls.GOOGLE_PLACES_API_KEY,
            "enabled": cls.GOOGLE_PLACES_ENABLED and bool(cls.GOOGLE_PLACES_API_KEY),
            "radius": cls.GOOGLE_PLACES_RADIUS_METERS,
            "max_results": cls.GOOGLE_PLACES_MAX_RESULTS,
            "timeout": cls.API_TIMEOUT_SECONDS
        }
    
    @classmethod
    def get_foursquare_config(cls) -> Dict[str, Any]:
        """Get Foursquare API configuration"""
        return {
            "api_key": cls.FOURSQUARE_API_KEY,
            "enabled": cls.FOURSQUARE_ENABLED and bool(cls.FOURSQUARE_API_KEY),
            "radius": cls.FOURSQUARE_RADIUS_METERS,
            "max_results": cls.FOURSQUARE_MAX_RESULTS,
            "timeout": cls.API_TIMEOUT_SECONDS
        }
    
    @classmethod
    def get_cache_config(cls) -> Dict[str, int]:
        """Get cache configuration for all services"""
        return {
            "location_ttl": cls.LOCATION_CACHE_TTL_HOURS,
            "terminal_ttl": cls.TERMINAL_CACHE_TTL_HOURS,
            "fingerprint_ttl": cls.FINGERPRINT_CACHE_TTL_HOURS,
            "historical_ttl": cls.HISTORICAL_CACHE_TTL_HOURS
        }
    
    @classmethod
    def get_service_weights(cls) -> Dict[str, float]:
        """Get prediction weights for different services"""
        return {
            "location": cls.LOCATION_WEIGHT,
            "historical": cls.HISTORICAL_WEIGHT,
            "terminal": cls.TERMINAL_WEIGHT,
            "wifi": cls.WIFI_WEIGHT,
            "ble": cls.BLE_WEIGHT
        }
    
    @classmethod
    def get_confidence_thresholds(cls) -> Dict[str, float]:
        """Get minimum confidence thresholds for each service"""
        return {
            "location": cls.MIN_LOCATION_CONFIDENCE,
            "terminal": cls.MIN_TERMINAL_CONFIDENCE,
            "fingerprint": cls.MIN_FINGERPRINT_CONFIDENCE,
            "historical": cls.MIN_HISTORICAL_CONFIDENCE
        }
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate configuration and return status"""
        issues = []
        warnings = []
        
        # Check API keys
        if cls.GOOGLE_PLACES_ENABLED and not cls.GOOGLE_PLACES_API_KEY:
            issues.append("Google Places API enabled but no API key provided")
        
        if cls.FOURSQUARE_ENABLED and not cls.FOURSQUARE_API_KEY:
            issues.append("Foursquare API enabled but no API key provided")
        
        # Check weights sum
        total_weight = (cls.LOCATION_WEIGHT + cls.HISTORICAL_WEIGHT + 
                       cls.TERMINAL_WEIGHT + cls.WIFI_WEIGHT + cls.BLE_WEIGHT)
        if abs(total_weight - 1.0) > 0.1:
            warnings.append(f"Prediction weights sum to {total_weight:.2f}, expected ~1.0")
        
        # Check radius limits
        if cls.DEFAULT_SEARCH_RADIUS_METERS > cls.MAX_SEARCH_RADIUS_METERS:
            issues.append("Default search radius exceeds maximum")
        
        if cls.DEFAULT_SEARCH_RADIUS_METERS < cls.MIN_SEARCH_RADIUS_METERS:
            issues.append("Default search radius below minimum")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "google_places_available": bool(cls.GOOGLE_PLACES_API_KEY),
            "foursquare_available": bool(cls.FOURSQUARE_API_KEY),
            "enhanced_services_enabled": any([
                cls.ENHANCED_LOCATION_ENABLED,
                cls.ENHANCED_TERMINAL_ENABLED,
                cls.ENHANCED_FINGERPRINT_ENABLED,
                cls.ENHANCED_HISTORICAL_ENABLED
            ])
        }


# Default MCC mappings for common business types - Use centralized utility
DEFAULT_MCC_MAPPINGS = get_all_mcc_categories()

# WiFi SSID patterns for brand detection
WIFI_BRAND_PATTERNS = {
    "starbucks": {"mcc": "5814", "confidence": 0.9},
    "mcdonalds": {"mcc": "5814", "confidence": 0.9},
    "walmart": {"mcc": "5411", "confidence": 0.85},
    "target": {"mcc": "5311", "confidence": 0.85},
    "bestbuy": {"mcc": "5732", "confidence": 0.85},
    "apple": {"mcc": "5732", "confidence": 0.9},
    "amazon": {"mcc": "5999", "confidence": 0.8},
    "costco": {"mcc": "5411", "confidence": 0.85},
    "home_depot": {"mcc": "5211", "confidence": 0.85},
    "cvs": {"mcc": "5912", "confidence": 0.85},
    "walgreens": {"mcc": "5912", "confidence": 0.85}
}

# BLE UUID patterns for common retailers
BLE_BRAND_PATTERNS = {
    # Apple iBeacon UUID
    "e2c56db5-dffb-48d2-b060-d0f5a71096e0": {"brand": "apple", "mcc": "5732", "confidence": 0.9},
    # Estimote UUID
    "b9407f30-f5f8-466e-aff9-25556b57fe6d": {"brand": "retail", "mcc": "5999", "confidence": 0.6},
    # Common retail UUIDs (examples)
    "550e8400-e29b-41d4-a716-446655440000": {"brand": "generic_retail", "mcc": "5999", "confidence": 0.5}
}

# Terminal ID patterns for different processors
TERMINAL_ID_PATTERNS = {
    "square": {
        "pattern": r"^sq\w+",
        "mcc_distribution": {"5814": 0.4, "5812": 0.3, "5999": 0.3},
        "confidence": 0.7
    },
    "stripe": {
        "pattern": r"^st_\w+",
        "mcc_distribution": {"5999": 0.5, "5814": 0.2, "5311": 0.3},
        "confidence": 0.6
    },
    "clover": {
        "pattern": r"^clv\w+",
        "mcc_distribution": {"5812": 0.4, "5814": 0.3, "5999": 0.3},
        "confidence": 0.7
    }
} 