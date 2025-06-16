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
from app.api.route_modules.background_location import router as background_location_router

logger = logging.getLogger(__name__)

router = APIRouter()

# Include background location routes
router.include_router(background_location_router, prefix="/api/v1")


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
        
        # Structure the response properly for APIResponse model
        return APIResponse(
            success=response.get("success", True),
            data={
                "session_id": response.get("session_id"),
                "status": response.get("status"),
                "message": response.get("message"),
                "predicted_mcc": response.get("predicted_mcc"),
                "confidence": response.get("confidence"),
                "prediction_method": response.get("prediction_method"),
                "recommended_card": response.get("recommended_card"),
                "location_source": response.get("location_source"),
                "real_time_data_used": response.get("real_time_data_used"),
                "expires_at": response.get("expires_at"),
                "analysis_details": response.get("analysis_details"),
                "platform_config": response.get("data", {}).get("platform_config") if response.get("data") else None,
                "token_status": response.get("data", {}).get("token_status") if response.get("data") else None
            },
            error=response.get("error")
        )
        
    except Exception as e:
        logger.error(f"Payment activation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/routing/{session_id}/complete", response_model=APIResponse)
async def complete_transaction(
    session_id: str,
    feedback: Optional[TransactionFeedback] = Body(default=None, description="Transaction feedback for learning")
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


@router.post("/feedback/transaction", response_model=APIResponse)
async def submit_transaction_feedback(feedback: TransactionFeedback):
    """
    Submit transaction feedback for machine learning improvement
    
    This endpoint allows submitting feedback about completed transactions
    to improve future MCC predictions and card recommendations.
    
    The feedback includes:
    - Actual MCC code observed
    - Transaction success/failure
    - Merchant information
    - Location data
    - Performance metrics
    """
    try:
        # Convert feedback to dict
        feedback_data = feedback.model_dump()
        
        # Process the feedback through the routing orchestrator
        response = await routing_orchestrator.process_transaction_feedback(feedback_data)
        
        if response.get("status") != "success":
            raise HTTPException(status_code=400, detail=response.get("message", "Failed to process feedback"))
        
        return APIResponse(
            success=True,
            data={
                "feedback_id": feedback_data.get("session_id"),
                "processed_at": response.get("timestamp"),
                "status": "processed"
            },
            message="Transaction feedback processed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transaction feedback submission failed: {e}")
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
    Get network acceptance rates data
    
    Returns comprehensive data about card network acceptance across:
    - Different merchant categories
    - Geographic regions
    - Transaction types
    """
    try:
        # Mock network acceptance data - would be from real analytics
        acceptance_data = {
            "success": True,
            "data": {
                "networks": {
                    "visa": {
                        "overall_acceptance": 99.8,
                        "by_category": {
                            "grocery": 99.9,
                            "gas": 99.8,
                            "restaurant": 99.9,
                            "retail": 99.7,
                            "travel": 99.9
                        }
                    },
                    "mastercard": {
                        "overall_acceptance": 99.7,
                        "by_category": {
                            "grocery": 99.8,
                            "gas": 99.7,
                            "restaurant": 99.8,
                            "retail": 99.6,
                            "travel": 99.8
                        }
                    },
                    "amex": {
                        "overall_acceptance": 87.2,
                        "by_category": {
                            "grocery": 92.1,
                            "gas": 83.4,
                            "restaurant": 91.8,
                            "retail": 85.7,
                            "travel": 98.2
                        }
                    },
                    "discover": {
                        "overall_acceptance": 82.5,
                        "by_category": {
                            "grocery": 89.3,
                            "gas": 78.2,
                            "restaurant": 85.1,
                            "retail": 80.4,
                            "travel": 79.8
                        }
                    }
                },
                "last_updated": datetime.now().isoformat()
            },
            "message": "Network acceptance rates retrieved successfully"
        }
        
        return acceptance_data
        
    except Exception as e:
        logger.error(f"Failed to get network acceptance rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/gps-payment", response_model=APIResponse)
async def test_payment_with_gps(
    user_id: str = Body(..., description="User identifier"),
    latitude: float = Body(..., description="GPS latitude coordinate"),
    longitude: float = Body(..., description="GPS longitude coordinate"),
    platform: str = Body(default="ios", description="Platform (ios/android/web)"),
    wallet_type: str = Body(default="apple_pay", description="Wallet type (apple_pay/google_pay/samsung_pay)"),
    amount: Optional[float] = Body(default=50.0, description="Transaction amount"),
    merchant_name: Optional[str] = Body(default=None, description="Known merchant name"),
    accuracy: Optional[float] = Body(default=None, description="GPS accuracy in meters"),
    altitude: Optional[float] = Body(default=None, description="GPS altitude"),
    speed: Optional[float] = Body(default=None, description="GPS speed"),
    heading: Optional[float] = Body(default=None, description="GPS heading/bearing")
):
    """
    Test endpoint for payment routing with real GPS coordinates
    
    This endpoint allows testing the payment system with actual GPS coordinates
    instead of using the hardcoded Union Square location. It provides a complete
    payment flow simulation using real location data.
    
    Steps:
    1. Initiates routing session with user data
    2. Activates payment with real GPS coordinates
    3. Returns MCC prediction and card selection based on actual location
    
    Use this endpoint to test how the system behaves at different real-world locations.
    """
    try:
        logger.info(f"Testing payment with GPS coordinates: {latitude:.6f}, {longitude:.6f}")
        
        # Step 1: Initiate routing session
        logger.info("Step 1: Initiating routing session...")
        initiate_response = await routing_orchestrator.initiate_routing(
            user_id=user_id,
            platform=platform,
            wallet_type=wallet_type,
            transaction_amount=amount
        )
        
        logger.info(f"Initiate response: {initiate_response}")
        
        if not initiate_response.get("success", False):
            logger.error(f"Failed to initiate routing: {initiate_response}")
            raise HTTPException(status_code=400, detail=initiate_response.get("error", "Failed to initiate routing"))
        
        # Extract session_id from the response
        session_id = None
        if "data" in initiate_response and "session_id" in initiate_response["data"]:
            session_id = initiate_response["data"]["session_id"]
        elif "session_id" in initiate_response:
            session_id = initiate_response["session_id"]
        
        if not session_id:
            logger.error(f"No session_id found in initiate response: {initiate_response}")
            raise HTTPException(status_code=500, detail="Failed to get session_id from initiate response")
        
        logger.info(f"Created test session {session_id} for GPS payment test")
        
        # Step 2: Prepare real GPS location data
        logger.info("Step 2: Preparing GPS location data...")
        location_data = {
            "latitude": latitude,
            "longitude": longitude,
            "source": "gps",
            "timestamp": datetime.now().isoformat(),
            "accuracy": accuracy,
            "altitude": altitude,
            "speed": speed,
            "heading": heading
        }
        
        # Remove None values
        location_data = {k: v for k, v in location_data.items() if v is not None}
        logger.info(f"Location data prepared: {location_data}")
        
        # Step 3: Activate payment with real GPS data
        logger.info("Step 3: Preparing payment data...")
        payment_data = {
            "location": location_data,
            "merchant_name": merchant_name,
            "amount": amount,
            "wifi_networks": [],  # Could be populated with mock WiFi data
            "ble_beacons": [],    # Could be populated with mock BLE data
            "context_info": {
                "test_mode": True,
                "gps_test": True,
                "coordinates": f"{latitude:.6f},{longitude:.6f}"
            }
        }
        logger.info(f"Payment data prepared: {payment_data}")
        
        logger.info("Step 4: Activating payment...")
        activate_response = await routing_orchestrator.activate_payment(session_id, payment_data)
        logger.info(f"Activate response received: {activate_response}")
        
        if not activate_response.get("success", False):
            logger.error(f"Payment activation failed: {activate_response}")
            raise HTTPException(status_code=400, detail=activate_response.get("error", "Failed to activate payment"))
        
        # Step 4: Prepare comprehensive response
        logger.info("Step 5: Preparing final response...")
        response_data = {
            "test_type": "gps_payment_simulation",
            "session_id": session_id,
            "location_tested": {
                "latitude": latitude,
                "longitude": longitude,
                "accuracy": accuracy
            },
            "mcc_prediction": {
                "predicted_mcc": activate_response.get("predicted_mcc", "unknown"),
                "confidence": activate_response.get("confidence", 0.0),
                "method": activate_response.get("prediction_method", "unknown"),
                "analysis_details": activate_response.get("analysis_details", {})
            },
            "card_selection": activate_response.get("recommended_card", {}),
            "data_sources": {
                "location_source": "real_gps",
                "fallback_used": False,
                "real_time_data": True
            },
            "platform_config": activate_response.get("data", {}).get("platform_config", {}),
            "expires_at": activate_response.get("expires_at", ""),
            "message": f"GPS payment test completed successfully at coordinates {latitude:.6f}, {longitude:.6f}"
        }
        
        logger.info(f"GPS payment test completed - MCC: {activate_response.get('predicted_mcc', 'unknown')}, Confidence: {activate_response.get('confidence', 0.0):.2f}")
        
        return {
            "success": True,
            "data": response_data,
            "error": None,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GPS payment test failed: {e}")
        logger.error(f"Exception type: {type(e)}")
        logger.error(f"Exception args: {e.args}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/transactions", response_model=APIResponse)
async def get_user_transactions(
    user_id: str,
    limit: int = Query(default=50, description="Maximum number of transactions to return"),
    offset: int = Query(default=0, description="Number of transactions to skip")
):
    """
    Get transaction history for a specific user including location data
    
    Returns:
    - List of user's transaction feedback records
    - Transaction details including MCC predictions, amounts, merchants, locations
    - Pagination support via limit and offset
    """
    try:
        from app.database.connection_manager import connection_manager
        
        # Get user transaction history
        transactions = await connection_manager.get_user_transaction_history(
            user_id=user_id, 
            limit=limit
        )
        
        # Apply offset if specified
        if offset > 0:
            transactions = transactions[offset:]
        
        # Format the response with location data
        formatted_transactions = []
        for tx in transactions:
            formatted_tx = {
                "id": tx.get("id"),
                "session_id": tx.get("session_id"),
                "merchant_name": tx.get("merchant_name"),
                "predicted_mcc": tx.get("predicted_mcc"),
                "actual_mcc": tx.get("actual_mcc"),
                "transaction_amount": tx.get("transaction_amount"),
                "transaction_success": tx.get("transaction_success"),
                "prediction_confidence": tx.get("prediction_confidence"),
                "network_used": tx.get("network_used"),
                "terminal_id": tx.get("terminal_id"),
                "location_hash": tx.get("location_hash"),
                "created_at": tx.get("created_at"),
                "transaction_timestamp": tx.get("transaction_timestamp"),
                # Add location information
                "location": {
                    "latitude": tx.get("latitude"),
                    "longitude": tx.get("longitude"),
                    "address": tx.get("address"),
                    "city": tx.get("city"),
                    "state": tx.get("state"),
                    "country": tx.get("country"),
                    "postal_code": tx.get("postal_code")
                }
            }
            formatted_transactions.append(formatted_tx)
        
        return APIResponse(
            success=True,
            data={
                "transactions": formatted_transactions,
                "total_count": len(transactions),
                "limit": limit,
                "offset": offset,
                "user_id": user_id
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch user transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 