"""
Pydantic schemas for Payvo middleware
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class NetworkType(str, Enum):
    VISA = "visa"
    MASTERCARD = "mastercard"
    AMEX = "amex"
    DISCOVER = "discover"


class ConfidenceLevel(str, Enum):
    HIGH = "high"      # 0.8+
    MEDIUM = "medium"  # 0.5-0.8
    LOW = "low"        # <0.5


class MCCDetectionMethod(str, Enum):
    TERMINAL_ID = "terminal_id"
    GPS = "gps"
    WIFI = "wifi"
    BLE = "ble"
    BEHAVIORAL = "behavioral"
    LLM = "llm"


class LocationData(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WiFiData(BaseModel):
    ssid: Optional[str] = None
    bssid: Optional[str] = None
    signal_strength: Optional[int] = None
    frequency: Optional[int] = None


class BLEData(BaseModel):
    device_id: str
    uuid: Optional[str] = None
    major: Optional[int] = None
    minor: Optional[int] = None
    rssi: Optional[int] = None
    tx_power: Optional[int] = None


class TerminalData(BaseModel):
    terminal_id: Optional[str] = None
    device_id: Optional[str] = None
    pos_type: Optional[str] = None
    kernel_version: Optional[str] = None
    nfc_timing_pattern: Optional[List[float]] = None


class PreTapContext(BaseModel):
    user_id: str
    session_id: str
    location: Optional[LocationData] = None
    wifi_networks: List[WiFiData] = []
    ble_devices: List[BLEData] = []
    terminal_data: Optional[TerminalData] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MCCPrediction(BaseModel):
    mcc: str = Field(..., pattern=r'^\d{4}$')
    confidence: float = Field(..., ge=0.0, le=1.0)
    method: MCCDetectionMethod
    confidence_level: ConfidenceLevel
    metadata: Dict[str, Any] = {}
    
    @validator('confidence_level', pre=True, always=True)
    def set_confidence_level(cls, v, values):
        confidence = values.get('confidence', 0)
        if confidence >= 0.8:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW


class CardInfo(BaseModel):
    card_id: str
    network: NetworkType
    last_four: str = Field(..., pattern=r'^\d{4}$')
    card_type: str  # credit, debit, prepaid
    issuer: Optional[str] = None
    rewards_multiplier: Dict[str, float] = {}  # MCC -> multiplier
    interchange_fee: Optional[float] = None


class OptimalCardSelection(BaseModel):
    card_id: str
    network: NetworkType
    selection_reason: str
    expected_rewards: Optional[float] = None
    interchange_savings: Optional[float] = None
    confidence: float = Field(..., ge=0.0, le=1.0)


class TokenProvisioningRequest(BaseModel):
    card_id: str
    network: NetworkType
    device_id: str
    platform: str  # ios, android
    wallet_type: str  # apple_pay, google_pay, samsung_pay


class TokenProvisioningResponse(BaseModel):
    token_id: str
    provisioning_status: str
    expires_at: Optional[datetime] = None
    activation_code: Optional[str] = None


class RoutingDecision(BaseModel):
    session_id: str
    mcc_prediction: MCCPrediction
    optimal_card: OptimalCardSelection
    token_info: Optional[TokenProvisioningResponse] = None
    routing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    fallback_used: bool = False


class TransactionFeedback(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    transaction_amount: Optional[float] = None
    predicted_mcc: Optional[str] = None
    actual_mcc: Optional[str] = None
    merchant_name: Optional[str] = None
    transaction_success: bool
    prediction_confidence: Optional[float] = None
    network_used: Optional[NetworkType] = None
    wallet_type: Optional[str] = None
    location: Optional[LocationData] = None
    terminal_id: Optional[str] = None
    timestamp: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    rewards_earned: Optional[float] = None


class LearningData(BaseModel):
    terminal_id: Optional[str] = None
    location_hash: Optional[str] = None
    wifi_hash: Optional[str] = None
    ble_hash: Optional[str] = None
    actual_mcc: str
    confidence_score: float
    method_used: MCCDetectionMethod
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheck(BaseModel):
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    components: Dict[str, str] = {}


class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow) 