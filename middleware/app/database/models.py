"""
Pydantic models for database schema
Provides type safety and validation for all database operations
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


class TransactionFeedback(BaseModel):
    """Model for transaction feedback data"""
    id: UUID = Field(default_factory=uuid4)
    session_id: str = Field(..., max_length=255)
    user_id: str = Field(..., max_length=255)
    predicted_mcc: Optional[str] = Field(None, max_length=4)
    actual_mcc: Optional[str] = Field(None, max_length=4)
    prediction_confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    prediction_method: Optional[str] = Field(None, max_length=50)
    selected_card_id: Optional[str] = Field(None, max_length=255)
    network_used: Optional[str] = Field(None, max_length=20)
    transaction_success: Optional[bool] = None
    rewards_earned: Optional[Decimal] = Field(None, ge=0)
    merchant_name: Optional[str] = Field(None, max_length=255)
    transaction_amount: Optional[Decimal] = Field(None, ge=0)
    location_lat: Optional[Decimal] = Field(None, ge=-90, le=90)
    location_lng: Optional[Decimal] = Field(None, ge=-180, le=180)
    location_hash: Optional[str] = Field(None, max_length=50)
    terminal_id: Optional[str] = Field(None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator('predicted_mcc', 'actual_mcc')
    def validate_mcc(cls, v):
        if v is not None and (len(v) != 4 or not v.isdigit()):
            raise ValueError('MCC must be a 4-digit string')
        return v

    class Config:
        validate_assignment = True
        use_enum_values = True


class MCCPrediction(BaseModel):
    """Model for MCC prediction results"""
    id: UUID = Field(default_factory=uuid4)
    session_id: str = Field(..., max_length=255)
    terminal_id: Optional[str] = Field(None, max_length=255)
    location_hash: Optional[str] = Field(None, max_length=50)
    wifi_fingerprint: Optional[str] = None
    ble_fingerprint: Optional[str] = None
    predicted_mcc: str = Field(..., max_length=4)
    confidence: Decimal = Field(..., ge=0, le=1)
    method_used: str = Field(..., max_length=50)
    context_features: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)

    @validator('predicted_mcc')
    def validate_mcc(cls, v):
        if len(v) != 4 or not v.isdigit():
            raise ValueError('MCC must be a 4-digit string')
        return v

    class Config:
        validate_assignment = True


class CardPerformance(BaseModel):
    """Model for card performance metrics"""
    id: UUID = Field(default_factory=uuid4)
    card_id: str = Field(..., max_length=255)
    user_id: str = Field(..., max_length=255)
    mcc: Optional[str] = Field(None, max_length=4)
    network: Optional[str] = Field(None, max_length=20)
    transaction_success: Optional[bool] = None
    rewards_earned: Optional[Decimal] = Field(None, ge=0)
    transaction_amount: Optional[Decimal] = Field(None, ge=0)
    created_at: datetime = Field(default_factory=datetime.now)

    @validator('mcc')
    def validate_mcc(cls, v):
        if v is not None and (len(v) != 4 or not v.isdigit()):
            raise ValueError('MCC must be a 4-digit string')
        return v

    class Config:
        validate_assignment = True


class UserPreferences(BaseModel):
    """Model for user preferences"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str = Field(..., max_length=255)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        validate_assignment = True


class TerminalCache(BaseModel):
    """Model for terminal cache data"""
    id: UUID = Field(default_factory=uuid4)
    terminal_id: str = Field(..., max_length=255)
    mcc: str = Field(..., max_length=4)
    confidence: Decimal = Field(default=1.0, ge=0, le=1)
    transaction_count: int = Field(default=1, ge=1)
    last_seen: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator('mcc')
    def validate_mcc(cls, v):
        if len(v) != 4 or not v.isdigit():
            raise ValueError('MCC must be a 4-digit string')
        return v

    class Config:
        validate_assignment = True


class LocationCache(BaseModel):
    """Model for location cache data"""
    id: UUID = Field(default_factory=uuid4)
    location_hash: str = Field(..., max_length=50)
    mcc: str = Field(..., max_length=4)
    confidence: Decimal = Field(default=1.0, ge=0, le=1)
    transaction_count: int = Field(default=1, ge=1)
    merchant_name: Optional[str] = Field(None, max_length=255)
    last_seen: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator('mcc')
    def validate_mcc(cls, v):
        if len(v) != 4 or not v.isdigit():
            raise ValueError('MCC must be a 4-digit string')
        return v

    class Config:
        validate_assignment = True


class WiFiCache(BaseModel):
    """Model for WiFi cache data"""
    id: UUID = Field(default_factory=uuid4)
    wifi_hash: str = Field(..., max_length=50)
    mcc: str = Field(..., max_length=4)
    confidence: Decimal = Field(default=1.0, ge=0, le=1)
    transaction_count: int = Field(default=1, ge=1)
    last_seen: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator('mcc')
    def validate_mcc(cls, v):
        if len(v) != 4 or not v.isdigit():
            raise ValueError('MCC must be a 4-digit string')
        return v

    class Config:
        validate_assignment = True


class BLECache(BaseModel):
    """Model for BLE cache data"""
    id: UUID = Field(default_factory=uuid4)
    ble_hash: str = Field(..., max_length=50)
    mcc: str = Field(..., max_length=4)
    confidence: Decimal = Field(default=1.0, ge=0, le=1)
    transaction_count: int = Field(default=1, ge=1)
    last_seen: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator('mcc')
    def validate_mcc(cls, v):
        if len(v) != 4 or not v.isdigit():
            raise ValueError('MCC must be a 4-digit string')
        return v

    class Config:
        validate_assignment = True


# Analytics response models
class CardPerformanceStats(BaseModel):
    """Model for card performance statistics"""
    card_id: str
    total_transactions: int
    success_rate: float
    total_rewards: Decimal
    average_transaction_amount: Decimal
    most_common_mcc: Optional[str] = None
    best_network: Optional[str] = None

    class Config:
        validate_assignment = True


class SystemAnalytics(BaseModel):
    """Model for system analytics"""
    period_days: int
    total_transactions: int
    total_users: int
    avg_prediction_confidence: float
    most_common_mcc: Optional[str] = None
    prediction_accuracy: Optional[float] = None
    network_distribution: Dict[str, int]
    
    class Config:
        validate_assignment = True 