"""
FastAPI routes for Payvo middleware
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, Dict, List, Any
import logging
from datetime import datetime

from app.models.schemas import (
    APIResponse, TransactionFeedback, HealthCheck
)
from app.services.routing_orchestrator import routing_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/routing/initiate", response_model=APIResponse)
async def initiate_card_routing(
    user_id: str = Body(..., description="User identifier"),
    platform: str = Body(default="unknown", description="Platform (ios/android/web)"),
    wallet_type: str = Body(default="unknown", description="Wallet type (apple_pay/google_pay/samsung_pay)"),
    device_id: Optional[str] = Body(default=None, description="Device identifier"),
    transaction_amount: Optional[float] = Body(default=None, description="Expected transaction amount")
):
    """
    Initiate card routing flow with MCC prediction and optimal card selection
    
    This endpoint:
    1. Collects pre-tap context (location, Wi-Fi, BLE, terminal data)
    2. Predicts MCC using layered detection system
    3. Selects optimal card based on rewards and preferences
    4. Provisions payment token for the selected card
    
    Returns routing decision with session ID for tracking
    """
    try:
        response = await routing_orchestrator.initiate_routing(
            user_id=user_id,
            platform=platform,
            wallet_type=wallet_type,
            device_id=device_id,
            transaction_amount=transaction_amount
        )
        
        if not response.get("success", False):
            raise HTTPException(status_code=400, detail=response.get("error", "Unknown error"))
        
        return response
        
    except Exception as e:
        logger.error(f"Routing initiation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/routing/{session_id}/activate", response_model=APIResponse)
async def activate_payment_token(
    session_id: str,
    location: Optional[Dict[str, Any]] = Body(default=None, description="Real-time GPS location data"),
    terminal_id: Optional[str] = Body(default=None, description="Terminal ID if available"),
    merchant_name: Optional[str] = Body(default=None, description="Merchant name if known"),
    wifi_networks: Optional[List[Dict[str, Any]]] = Body(default=None, description="WiFi networks detected"),
    ble_beacons: Optional[List[Dict[str, Any]]] = Body(default=None, description="BLE beacons detected"),
    amount: Optional[float] = Body(default=None, description="Transaction amount"),
    context_info: Optional[Dict[str, Any]] = Body(default=None, description="Additional context information")
):
    """
    Activate the payment token for the selected card with real-time location data
    
    This prepares the token for NFC transaction by:
    - Using real-time location data for enhanced MCC prediction
    - Analyzing WiFi/BLE fingerprints for indoor positioning
    - Configuring platform-specific payment interfaces
    - Activating secure elements or HCE
    - Making the token available for POS interaction
    
    Real-time data significantly improves MCC prediction accuracy.
    """
    try:
        # Prepare real payment data if provided
        payment_data = None
        if any([location, terminal_id, merchant_name, wifi_networks, ble_beacons, amount, context_info]):
            payment_data = {
                "location": location or {},
                "terminal_id": terminal_id,
                "merchant_name": merchant_name,
                "wifi_networks": wifi_networks or [],
                "ble_beacons": ble_beacons or [],
                "amount": amount,
                "context_info": context_info or {}
            }
            
            # Log real-time data usage
            logger.info(f"Received real-time payment data for session {session_id}")
            if location and location.get("latitude") and location.get("longitude"):
                logger.info(f"Real-time location provided: {location['latitude']:.6f}, {location['longitude']:.6f}")
            if wifi_networks:
                logger.info(f"WiFi networks detected: {len(wifi_networks)} networks")
            if ble_beacons:
                logger.info(f"BLE beacons detected: {len(ble_beacons)} beacons")
        
        response = await routing_orchestrator.activate_payment(session_id, payment_data)
        
        if not response.get("success", False):
            raise HTTPException(status_code=400, detail=response.get("error", "Unknown error"))
        
        return response
        
    except Exception as e:
        logger.error(f"Payment activation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/routing/{session_id}/complete", response_model=APIResponse)
async def complete_transaction(
    session_id: str,
    feedback: Optional[TransactionFeedback] = None
):
    """
    Complete transaction and provide feedback for learning
    
    This endpoint:
    1. Processes transaction feedback for ML improvement
    2. Updates card performance metrics
    3. Deactivates payment tokens
    4. Cleans up session data
    
    Feedback helps improve future MCC predictions and card selections
    """
    try:
        response = await routing_orchestrator.complete_transaction(
            session_id=session_id,
            feedback=feedback
        )
        
        if not response.get("success", False):
            raise HTTPException(status_code=400, detail=response.get("error", "Unknown error"))
        
        return response
        
    except Exception as e:
        logger.error(f"Transaction completion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routing/{session_id}/status", response_model=APIResponse)
async def get_session_status(session_id: str):
    """
    Get current status of a routing session
    
    Returns:
    - Routing decision details
    - Token activation status
    - Session metadata
    """
    try:
        response = await routing_orchestrator.get_session_status(session_id)
        
        if not response.get("success", False):
            raise HTTPException(status_code=404, detail=response.get("error", "Unknown error"))
        
        return response
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/routing/{session_id}", response_model=APIResponse)
async def cancel_session(session_id: str):
    """
    Cancel an active routing session
    
    This will:
    - Deactivate any active payment tokens
    - Clean up session data
    - Release resources
    """
    try:
        response = await routing_orchestrator.cancel_session(session_id)
        
        if not response.get("success", False):
            raise HTTPException(status_code=404, detail=response.get("error", "Unknown error"))
        
        return response
        
    except Exception as e:
        logger.error(f"Session cancellation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=APIResponse)
async def get_performance_metrics():
    """
    Get system performance metrics
    
    Returns:
    - Request/response statistics
    - Prediction accuracy metrics
    - Token provisioning statistics
    - Success rates
    """
    try:
        response = await routing_orchestrator.get_performance_metrics()
        return response
        
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=APIResponse)
async def health_check():
    """
    System health check endpoint
    
    Returns:
    - Overall system status
    - Component health status
    - Active session count
    - System version
    """
    try:
        # Try to get health status from routing orchestrator
        response = await routing_orchestrator.health_check()
        return response
        
    except Exception as e:
        logger.warning(f"Routing orchestrator health check failed: {e}")
        
        # Return a basic health status when orchestrator is unavailable
        return APIResponse(
            success=True,
            data={
                "status": "degraded",
                "version": "2.0.0",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "routing_orchestrator": "unavailable",
                    "database": "unknown",
                    "supabase": "unknown"
                },
                "cache_stats": {
                    "mcc_cache_size": 0,
                    "location_cache_size": 0,
                    "terminal_cache_size": 0,
                    "wifi_cache_size": 0,
                    "ble_cache_size": 0
                },
                "system_info": {
                    "active_sessions": 0,
                    "background_tasks": 0
                }
            },
            message="System is running in degraded mode"
        )


# Additional utility endpoints

@router.get("/mcc/{mcc_code}/info")
async def get_mcc_info(mcc_code: str):
    """
    Get information about a specific MCC code
    """
    mcc_info = {
        "5812": {
            "category": "Eating Places, Restaurants",
            "description": "Full-service restaurants",
            "typical_rewards": "2-4x points/cashback"
        },
        "5814": {
            "category": "Fast Food Restaurants", 
            "description": "Quick service restaurants",
            "typical_rewards": "2-4x points/cashback"
        },
        "5411": {
            "category": "Grocery Stores, Supermarkets",
            "description": "Grocery and supermarket purchases",
            "typical_rewards": "1-6x points/cashback"
        },
        "5541": {
            "category": "Service Stations",
            "description": "Gas stations and fuel purchases", 
            "typical_rewards": "2-5x points/cashback"
        },
        "5732": {
            "category": "Electronics Stores",
            "description": "Consumer electronics retailers",
            "typical_rewards": "1-2x points/cashback"
        },
        "5999": {
            "category": "Miscellaneous Retail",
            "description": "General retail and miscellaneous",
            "typical_rewards": "1x points/cashback"
        }
    }
    
    info = mcc_info.get(mcc_code)
    if not info:
        raise HTTPException(status_code=404, detail="MCC code not found")
    
    return APIResponse(
        success=True,
        data={
            "mcc_code": mcc_code,
            **info
        }
    )


@router.get("/networks/acceptance")
async def get_network_acceptance_rates():
    """
    Get payment network acceptance rates by category
    """
    acceptance_data = {
        "visa": {
            "overall": 0.95,
            "restaurants": 0.98,
            "grocery": 0.99,
            "gas": 0.97,
            "retail": 0.96
        },
        "mastercard": {
            "overall": 0.93,
            "restaurants": 0.96,
            "grocery": 0.98,
            "gas": 0.95,
            "retail": 0.94
        },
        "amex": {
            "overall": 0.75,
            "restaurants": 0.85,
            "grocery": 0.70,
            "gas": 0.60,
            "retail": 0.80
        },
        "discover": {
            "overall": 0.65,
            "restaurants": 0.70,
            "grocery": 0.75,
            "gas": 0.80,
            "retail": 0.60
        }
    }
    
    return APIResponse(
        success=True,
        data=acceptance_data
    ) 