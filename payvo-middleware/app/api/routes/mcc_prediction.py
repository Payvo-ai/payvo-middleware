"""
MCC Prediction API endpoints for testing enhanced prediction services
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.services.routing_orchestrator import RoutingOrchestrator
from app.config.enhanced_services import EnhancedServicesConfig
from app.models.schemas import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mcc", tags=["MCC Prediction"])

# Global orchestrator instance
orchestrator = None

async def get_orchestrator():
    """Get the routing orchestrator instance"""
    global orchestrator
    if orchestrator is None:
        orchestrator = RoutingOrchestrator()
        await orchestrator.initialize()
    return orchestrator


class MCCPredictionRequest(BaseModel):
    """Request model for MCC prediction testing"""
    
    # Location data
    location: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Location data with latitude, longitude, and accuracy"
    )
    
    # Terminal information
    terminal_id: Optional[str] = Field(
        default=None,
        description="Terminal ID for transaction"
    )
    
    # WiFi and BLE data
    wifi_networks: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of detected WiFi networks"
    )
    
    ble_beacons: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of detected BLE beacons"
    )
    
    # Transaction context
    amount: Optional[float] = Field(
        default=None,
        description="Transaction amount"
    )
    
    merchant_name: Optional[str] = Field(
        default=None,
        description="Merchant name if known"
    )
    
    # Expected MCC for testing
    expected_mcc: Optional[str] = Field(
        default=None,
        description="Expected MCC for validation (test scenarios)"
    )
    
    # Additional context
    context_info: Optional[Dict[str, Any]] = Field(
        default={},
        description="Additional context information"
    )


class MCCPredictionResponse(BaseModel):
    """Response model for MCC prediction"""
    
    predicted_mcc: str
    confidence: float
    prediction_method: str
    prediction_sources: List[str]
    analysis_details: Dict[str, Any]
    prediction_count: int
    timestamp: str
    
    # Enhanced details
    all_predictions: Optional[Dict[str, Any]] = None
    consensus_count: Optional[int] = None
    primary_methods: Optional[List[str]] = None


@router.post("/predict", response_model=MCCPredictionResponse)
async def predict_mcc(
    request: MCCPredictionRequest,
    orchestrator: RoutingOrchestrator = Depends(get_orchestrator)
):
    """
    Test enhanced MCC prediction using multiple data sources
    """
    try:
        # Prepare payment data from request
        payment_data = {
            "session_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "user_id": "test_user",
            "amount": request.amount or 50.0,
            "location": request.location or {},
            "terminal_id": request.terminal_id,
            "wifi_networks": request.wifi_networks or [],
            "ble_beacons": request.ble_beacons or [],
            "merchant_name": request.merchant_name,
            "context_info": request.context_info or {}
        }
        
        # Add expected MCC to context if provided
        if request.expected_mcc:
            payment_data["context_info"]["expected_mcc"] = request.expected_mcc
        
        # Predict MCC using enhanced services
        prediction = await orchestrator._predict_mcc_enhanced(
            payment_data, 
            payment_data["session_id"]
        )
        
        return MCCPredictionResponse(
            predicted_mcc=prediction["mcc"],
            confidence=prediction["confidence"],
            prediction_method=prediction["method"],
            prediction_sources=prediction.get("sources", []),
            analysis_details=prediction.get("analysis_details", {}),
            prediction_count=prediction.get("prediction_count", 0),
            timestamp=datetime.now().isoformat(),
            all_predictions=prediction.get("all_predictions"),
            consensus_count=prediction.get("consensus_count"),
            primary_methods=prediction.get("primary_methods")
        )
        
    except Exception as e:
        logger.error(f"Error in MCC prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_enhanced_config():
    """
    Get configuration status for enhanced MCC prediction services
    """
    try:
        config_status = EnhancedServicesConfig.validate_config()
        
        return {
            "status": "ok" if config_status["valid"] else "warning",
            "configuration": {
                "google_places": EnhancedServicesConfig.get_google_places_config(),
                "foursquare": EnhancedServicesConfig.get_foursquare_config(),
                "cache": EnhancedServicesConfig.get_cache_config(),
                "weights": EnhancedServicesConfig.get_service_weights(),
                "thresholds": EnhancedServicesConfig.get_confidence_thresholds()
            },
            "validation": config_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting enhanced config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-scenarios")
async def test_prediction_scenarios(
    orchestrator: RoutingOrchestrator = Depends(get_orchestrator)
):
    """
    Test various MCC prediction scenarios with known outcomes
    """
    try:
        test_scenarios = [
            {
                "name": "Starbucks Coffee Shop",
                "data": {
                    "location": {"latitude": 37.7749, "longitude": -122.4194, "accuracy": 50},
                    "wifi_networks": [{"ssid": "Starbucks WiFi", "signal_strength": -45}],
                    "amount": 12.50,
                    "merchant_name": "Starbucks",
                    "context_info": {"expected_mcc": "5814"}
                },
                "expected_mcc": "5814"
            },
            {
                "name": "Apple Store",
                "data": {
                    "location": {"latitude": 37.7849, "longitude": -122.4094, "accuracy": 30},
                    "ble_beacons": [{"uuid": "e2c56db5-dffb-48d2-b060-d0f5a71096e0", "major": 1, "minor": 1}],
                    "amount": 999.00,
                    "merchant_name": "Apple Store",
                    "context_info": {"expected_mcc": "5732"}
                },
                "expected_mcc": "5732"
            },
            {
                "name": "Generic Restaurant",
                "data": {
                    "location": {"latitude": 40.7128, "longitude": -74.0060, "accuracy": 100},
                    "terminal_id": "sq_12345_restaurant",
                    "amount": 45.75,
                    "context_info": {"expected_mcc": "5812"}
                },
                "expected_mcc": "5812"
            },
            {
                "name": "Unknown Location",
                "data": {
                    "amount": 25.00
                },
                "expected_mcc": "5999"
            }
        ]
        
        results = []
        for scenario in test_scenarios:
            try:
                # Add session ID for tracking
                scenario["data"]["session_id"] = f"test_scenario_{len(results)}"
                
                prediction = await orchestrator._predict_mcc_enhanced(
                    scenario["data"],
                    scenario["data"]["session_id"]
                )
                
                # Calculate accuracy
                predicted_correct = prediction["mcc"] == scenario["expected_mcc"]
                
                results.append({
                    "scenario": scenario["name"],
                    "predicted_mcc": prediction["mcc"],
                    "expected_mcc": scenario["expected_mcc"],
                    "confidence": prediction["confidence"],
                    "method": prediction["method"],
                    "sources": prediction.get("sources", []),
                    "correct": predicted_correct,
                    "analysis_summary": {
                        "prediction_count": prediction.get("prediction_count", 0),
                        "consensus_count": prediction.get("consensus_count", 0),
                        "primary_methods": prediction.get("primary_methods", [])
                    }
                })
                
            except Exception as scenario_error:
                results.append({
                    "scenario": scenario["name"],
                    "error": str(scenario_error),
                    "correct": False
                })
        
        # Calculate overall accuracy
        correct_predictions = sum(1 for r in results if r.get("correct", False))
        total_predictions = len(results)
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        return {
            "test_summary": {
                "total_scenarios": total_predictions,
                "correct_predictions": correct_predictions,
                "accuracy": accuracy,
                "timestamp": datetime.now().isoformat()
            },
            "scenario_results": results
        }
        
    except Exception as e:
        logger.error(f"Error in test scenarios: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check for enhanced MCC prediction services
    """
    try:
        # Check service availability
        services_status = {
            "location_service": EnhancedServicesConfig.ENHANCED_LOCATION_ENABLED,
            "terminal_service": EnhancedServicesConfig.ENHANCED_TERMINAL_ENABLED,
            "fingerprint_service": EnhancedServicesConfig.ENHANCED_FINGERPRINT_ENABLED,
            "historical_service": EnhancedServicesConfig.ENHANCED_HISTORICAL_ENABLED,
            "google_places_api": bool(EnhancedServicesConfig.GOOGLE_PLACES_API_KEY),
            "foursquare_api": bool(EnhancedServicesConfig.FOURSQUARE_API_KEY)
        }
        
        enabled_services = sum(1 for status in services_status.values() if status)
        
        return {
            "status": "healthy",
            "enhanced_services": services_status,
            "enabled_services_count": enabled_services,
            "total_services": len(services_status),
            "configuration_valid": EnhancedServicesConfig.validate_config()["valid"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        } 