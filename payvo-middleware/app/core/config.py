"""
Core configuration settings for Payvo middleware
"""

import os
import logging
from typing import Optional, List
from pydantic import BaseSettings, validator, Field
from dotenv import load_dotenv

# Load environment variables before creating settings
load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Payvo MCC Routing Middleware"
    VERSION: str = "1.0.0"
    
    # Server Configuration
    PAYVO_HOST: str = os.getenv("PAYVO_HOST", "0.0.0.0")
    PAYVO_PORT: int = int(os.getenv("PAYVO_PORT", "8000"))
    PAYVO_DEBUG: bool = os.getenv("PAYVO_DEBUG", "false").lower() == "true"
    
    # Legacy support for old config names
    HOST: str = os.getenv("PAYVO_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PAYVO_PORT", "8000"))
    DEBUG: bool = os.getenv("PAYVO_DEBUG", "false").lower() == "true"
    
    # Security
    PAYVO_SECRET_KEY: str = os.getenv("PAYVO_SECRET_KEY", "your-secret-key-change-in-production")
    SECRET_KEY: str = os.getenv("SECRET_KEY", os.getenv("PAYVO_SECRET_KEY", "your-secret-key-change-in-production"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8000",
        "http://10.0.0.207:8000",
        "http://10.0.0.207:8081"
    ]
    
    # Rate Limiting
    PAYVO_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("PAYVO_RATE_LIMIT_PER_MINUTE", "100"))
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("PAYVO_RATE_LIMIT_PER_MINUTE", "100"))
    
    # Supabase Configuration (Primary Database)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # Redis (Optional - for caching)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # MCC Detection Configuration
    MCC_CONFIDENCE_THRESHOLD: float = 0.7
    GPS_RADIUS_METERS: int = 10
    WIFI_SCAN_TIMEOUT: int = 5
    BLE_SCAN_TIMEOUT: int = 3
    
    # AI/ML Configuration
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key for LLM inference")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="OpenAI model to use")
    OPENAI_MAX_TOKENS: int = Field(default=1000, description="Maximum tokens for OpenAI responses")
    OPENAI_TEMPERATURE: float = Field(default=0.3, description="Temperature for OpenAI responses")
    
    # Network Configuration
    SUPPORTED_NETWORKS: List[str] = ["visa", "mastercard", "amex", "discover"]
    
    # Logging
    PAYVO_LOG_LEVEL: str = os.getenv("PAYVO_LOG_LEVEL", "INFO")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", os.getenv("PAYVO_LOG_LEVEL", "INFO"))
    
    # External APIs (Optional)
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    GOOGLE_PLACES_API_KEY: Optional[str] = os.getenv("GOOGLE_PLACES_API_KEY", os.getenv("GOOGLE_API_KEY"))
    FOURSQUARE_API_KEY: Optional[str] = os.getenv("FOURSQUARE_API_KEY")
    STRIPE_API_KEY: Optional[str] = os.getenv("STRIPE_API_KEY")
    
    # Location Service Configuration
    GOOGLE_PLACES_ENABLED: bool = True
    FOURSQUARE_ENABLED: bool = True
    GOOGLE_PLACES_DAILY_LIMIT: int = 1000
    FOURSQUARE_DAILY_LIMIT: int = 1000
    LOCATION_CACHE_HOURS: int = 6
    TERMINAL_CACHE_HOURS: int = 12
    
    # Confidence Thresholds
    MIN_CONFIDENCE_THRESHOLD: float = 0.3
    HIGH_CONFIDENCE_THRESHOLD: float = 0.8
    
    # Legacy support for old Google API key names
    @property
    def GOOGLE_MAPS_API_KEY(self) -> Optional[str]:
        """Legacy support - returns the main Google API key"""
        return self.GOOGLE_API_KEY
    
    @property
    def use_supabase(self) -> bool:
        """Check if Supabase is configured and should be used"""
        return bool(self.SUPABASE_URL and self.SUPABASE_ANON_KEY)
    
    @validator('OPENAI_API_KEY', pre=True, allow_reuse=True)
    def validate_openai_key(cls, v):
        return os.getenv("OPENAI_API_KEY", v or "")
    
    @validator('OPENAI_MODEL', pre=True, allow_reuse=True)
    def validate_openai_model(cls, v):
        return os.getenv("OPENAI_MODEL", v or "gpt-4o-mini")
    
    @validator('OPENAI_MAX_TOKENS', pre=True, allow_reuse=True)
    def validate_openai_tokens(cls, v):
        return int(os.getenv("OPENAI_MAX_TOKENS", v or 1000))
    
    @validator('OPENAI_TEMPERATURE', pre=True, allow_reuse=True)
    def validate_openai_temperature(cls, v):
        return float(os.getenv("OPENAI_TEMPERATURE", v or 0.3))
    
    @property
    def ALLOWED_HOSTS(self) -> List[str]:
        """Parse ALLOWED_HOSTS from environment variable"""
        allowed_hosts_str = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,10.0.0.207")
        if isinstance(allowed_hosts_str, str):
            return [host.strip().strip('"').strip("'") for host in allowed_hosts_str.split(",")]
        return ["localhost", "127.0.0.1", "10.0.0.207"]
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings() 