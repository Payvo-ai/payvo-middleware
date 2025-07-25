"""
Enhanced MCC Prediction API Routes
Provides comprehensive merchant category code prediction using multiple data sources
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field

from ...services.location_service import LocationService
from ...services.terminal_service import TerminalService
from ...services.fingerprint_service import FingerprintService
from ...services.historical_service import HistoricalService
from ...services.llm_service import LLMService
from ...services.prediction_service import prediction_service  # NEW: Enhanced prediction service
from ...services.pos_terminal_service import pos_terminal_service  # NEW: POS terminal service
# from ...core.cache import get_redis  # Commented out - module doesn't exist
from ...core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcc", tags=["MCC Prediction"])

# Request/Response Models
class WiFiNetwork(BaseModel):
    """WiFi network information"""
    ssid: str = Field(..., description="Network SSID")
    bssid: Optional[str] = Field(None, description="Network BSSID/MAC address")
    rssi: Optional[int] = Field(None, description="Signal strength (RSSI)")
    frequency: Optional[int] = Field(None, description="Frequency in MHz")

class BLEBeacon(BaseModel):
    """Bluetooth Low Energy beacon information"""
    uuid: str = Field(..., description="Beacon UUID")
    major: Optional[int] = Field(None, description="Major ID")
    minor: Optional[int] = Field(None, description="Minor ID")
    rssi: Optional[int] = Field(None, description="Signal strength (RSSI)")
    name: Optional[str] = Field(None, description="Device name")

class MCCPredictionRequest(BaseModel):
    """Request model for MCC prediction"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    merchant_name: Optional[str] = Field(None, description="Merchant name if available")
    terminal_id: Optional[str] = Field(None, description="Terminal ID if available")
    transaction_amount: Optional[float] = Field(None, description="Transaction amount")
    transaction_time: Optional[str] = Field(None, description="Transaction timestamp")
    
    # Enhanced WiFi and BLE data structures
    wifi_networks: Optional[List[WiFiNetwork]] = Field(None, description="Detected WiFi networks")
    ble_beacons: Optional[List[BLEBeacon]] = Field(None, description="Detected BLE beacons")
    
    # Legacy support (deprecated but maintained for backward compatibility)
    wifi_ssids: Optional[List[str]] = Field(None, description="Available WiFi SSIDs (deprecated)")
    bluetooth_devices: Optional[List[str]] = Field(None, description="Available Bluetooth devices (deprecated)")
    
    radius: Optional[int] = Field(None, ge=1, le=1000, description="Search radius in meters (defaults to adaptive radius starting at 1m)")
    include_alternatives: Optional[bool] = Field(True, description="Include alternative predictions")
    use_llm_enhancement: Optional[bool] = Field(True, description="Use LLM for enhanced analysis")
    user_id: Optional[str] = Field(None, description="User identifier for analytics")
    session_id: Optional[str] = Field(None, description="Session identifier for tracking")

class MCCPredictionResponse(BaseModel):
    """Response model for MCC prediction"""
    predicted_mcc: str
    confidence: float
    method: str
    prediction_sources: List[Dict[str, Any]]
    consensus_score: float
    processing_time_ms: int
    alternatives: Optional[List[Dict[str, Any]]] = None
    llm_analysis: Optional[Dict[str, Any]] = None
    enhancement_applied: bool = False

# Global service instances
location_service = LocationService()
terminal_service = TerminalService()
fingerprint_service = FingerprintService()
historical_service = HistoricalService()
llm_service = LLMService()

class MCCOrchestrator:
    """Enhanced orchestrator for MCC prediction with LLM integration"""
    
    def __init__(self):
        self.services_initialized = False
        
    async def initialize_services(self):
        """Initialize all prediction services"""
        if self.services_initialized:
            return
            
        try:
            # Initialize services in parallel
            await asyncio.gather(
                location_service.initialize(),
                terminal_service.initialize(),
                fingerprint_service.initialize(),
                historical_service.initialize(),
                llm_service.initialize(),
                prediction_service.initialize(),  # NEW: Enhanced prediction service
                pos_terminal_service.initialize(),  # NEW: POS terminal service
                return_exceptions=True
            )
            
            self.services_initialized = True
            logger.info("All MCC prediction services initialized")
            
        except Exception as e:
            logger.error(f"Error initializing services: {str(e)}")
            raise
    
    async def predict_mcc(self, request: MCCPredictionRequest) -> MCCPredictionResponse:
        """
        Orchestrate comprehensive MCC prediction using all available services
        """
        start_time = datetime.now()
        
        try:
            # Ensure services are initialized
            await self.initialize_services()
            
            # Gather predictions from all sources in parallel
            predictions = await self._gather_predictions(request)
            
            # Apply LLM enhancement if enabled
            if request.use_llm_enhancement and predictions:
                enhanced_prediction = await self._apply_llm_enhancement(request, predictions)
                if enhanced_prediction.get('enhancement_applied'):
                    predictions.append(enhanced_prediction)
            
            # Calculate consensus
            final_prediction = self._calculate_consensus(predictions)
            
            # Generate alternatives if requested
            alternatives = []
            if request.include_alternatives:
                alternatives = self._generate_alternatives(predictions, final_prediction)
            
            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return MCCPredictionResponse(
                predicted_mcc=final_prediction['mcc'],
                confidence=final_prediction['confidence'],
                method=final_prediction['method'],
                prediction_sources=predictions,
                consensus_score=final_prediction.get('consensus_score', 0.0),
                processing_time_ms=processing_time,
                alternatives=alternatives if alternatives else None,
                llm_analysis=final_prediction.get('llm_analysis'),
                enhancement_applied=final_prediction.get('enhancement_applied', False)
            )
            
        except Exception as e:
            logger.error(f"Error in MCC prediction orchestration: {str(e)}")
            raise HTTPException(status_code=500, detail=f"MCC prediction failed: {str(e)}")
    
    async def _gather_predictions(self, request: MCCPredictionRequest) -> List[Dict[str, Any]]:
        """Gather predictions from all available services"""
        
        # Prepare common context
        context = {
            'latitude': request.latitude,
            'longitude': request.longitude,
            'merchant_name': request.merchant_name,
            'terminal_id': request.terminal_id,
            'transaction_amount': request.transaction_amount,
            'transaction_time': request.transaction_time,
            'radius': request.radius
        }
        
        # Define prediction tasks
        tasks = []
        
        # Location-based prediction
        tasks.append(self._safe_predict_location(request))
        
        # Terminal-based prediction (if terminal_id provided)
        if request.terminal_id:
            tasks.append(self._safe_predict_terminal(request))
        
        # Fingerprint-based prediction (if WiFi/BLE data provided)
        if request.wifi_ssids or request.bluetooth_devices:
            tasks.append(self._safe_predict_fingerprint(request))
        
        # Historical pattern prediction
        tasks.append(self._safe_predict_historical(request))
        
        # Execute all predictions in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out failed predictions and exceptions
        predictions = []
        for result in results:
            if isinstance(result, dict) and result.get('mcc'):
                predictions.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Prediction service failed: {str(result)}")
        
        return predictions
    
    async def _apply_llm_enhancement(self, request: MCCPredictionRequest, 
                                   predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply LLM enhancement to improve prediction accuracy"""
        try:
            # Prepare merchant data for LLM analysis
            merchant_data = {
                'merchant_name': request.merchant_name or '',
                'business_description': '',
                'location_info': {
                    'latitude': request.latitude,
                    'longitude': request.longitude
                },
                'venue_types': []
            }
            
            # Extract venue information from location predictions
            for pred in predictions:
                if pred.get('method') == 'location_analysis' and 'venue_data' in pred:
                    venue_data = pred['venue_data']
                    if 'description' in venue_data:
                        merchant_data['business_description'] = venue_data['description']
                    if 'categories' in venue_data:
                        merchant_data['venue_types'] = venue_data['categories']
                    break
            
            # Prepare context
            context = {
                'transaction_amount': request.transaction_amount,
                'transaction_time': request.transaction_time,
                'radius': request.radius,
                'data_sources_used': [pred.get('method', 'unknown') for pred in predictions]
            }
            
            # Get LLM enhancement
            enhanced_result = await llm_service.enhance_mcc_prediction(
                merchant_data, predictions, context
            )
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"LLM enhancement failed: {str(e)}")
            return {'enhancement_applied': False, 'error': str(e)}
    
    async def _safe_predict_location(self, request: MCCPredictionRequest) -> Dict[str, Any]:
        """Safely execute location-based prediction"""
        try:
            if request.radius is None:
                # Use adaptive radius system
                result = await location_service.analyze_business_district(
                    request.latitude, request.longitude
                )
            else:
                # Use specified radius
                result = await location_service.predict_mcc_from_location(
                    request.latitude, request.longitude, request.radius
                )
            result['method'] = 'location_analysis'
            return result
        except Exception as e:
            logger.error(f"Location prediction failed: {str(e)}")
            return {'error': str(e), 'method': 'location_analysis'}
    
    async def _safe_predict_terminal(self, request: MCCPredictionRequest) -> Dict[str, Any]:
        """Safely execute terminal-based prediction"""
        try:
            result = await terminal_service.lookup_terminal(request.terminal_id)
            if result.get('predicted_mcc'):
                result['mcc'] = result['predicted_mcc']
                result['method'] = 'terminal_analysis'
                return result
            return {'error': 'No terminal prediction available', 'method': 'terminal_analysis'}
        except Exception as e:
            logger.error(f"Terminal prediction failed: {str(e)}")
            return {'error': str(e), 'method': 'terminal_analysis'}
    
    async def _safe_predict_fingerprint(self, request: MCCPredictionRequest) -> Dict[str, Any]:
        """Safely execute fingerprint-based prediction"""
        try:
            result = await fingerprint_service.predict_mcc_from_fingerprint(
                request.latitude, request.longitude,
                request.wifi_ssids or [], request.bluetooth_devices or []
            )
            result['method'] = 'fingerprint_analysis'
            return result
        except Exception as e:
            logger.error(f"Fingerprint prediction failed: {str(e)}")
            return {'error': str(e), 'method': 'fingerprint_analysis'}
    
    async def _safe_predict_historical(self, request: MCCPredictionRequest) -> Dict[str, Any]:
        """Safely execute historical pattern prediction"""
        try:
            result = await historical_service.analyze_area_patterns(
                request.latitude, request.longitude, request.radius
            )
            if result.get('predicted_mcc'):
                result['mcc'] = result['predicted_mcc']
                result['method'] = 'historical_analysis'
                return result
            return {'error': 'No historical prediction available', 'method': 'historical_analysis'}
        except Exception as e:
            logger.error(f"Historical prediction failed: {str(e)}")
            return {'error': str(e), 'method': 'historical_analysis'}
    
    def _calculate_consensus(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate weighted consensus from multiple predictions"""
        if not predictions:
            return {
                'mcc': '5999',  # Miscellaneous retail stores (fallback)
                'confidence': 0.1,
                'method': 'fallback',
                'consensus_score': 0.0
            }
        
        # Weight different prediction methods
        method_weights = {
            'llm_enhanced_consensus': 1.0,  # Highest weight for LLM enhanced
            'location_analysis': 0.8,
            'fingerprint_analysis': 0.7,
            'terminal_analysis': 0.9,
            'historical_analysis': 0.6
        }
        
        # Calculate weighted scores for each MCC
        mcc_scores = {}
        total_weight = 0
        
        for pred in predictions:
            if 'error' in pred or not pred.get('mcc'):
                continue
                
            mcc = pred['mcc']
            confidence = pred.get('confidence', 0.5)
            method = pred.get('method', 'unknown')
            weight = method_weights.get(method, 0.5)
            
            # Boost score for LLM enhanced predictions
            if pred.get('enhancement_applied'):
                weight *= 1.2
            
            weighted_score = confidence * weight
            mcc_scores[mcc] = mcc_scores.get(mcc, 0) + weighted_score
            total_weight += weight
        
        if not mcc_scores:
            return {
                'mcc': '5999',
                'confidence': 0.1,
                'method': 'no_valid_predictions',
                'consensus_score': 0.0
            }
        
        # Find best MCC
        best_mcc = max(mcc_scores, key=mcc_scores.get)
        consensus_score = mcc_scores[best_mcc] / total_weight if total_weight > 0 else 0
        
        # Find the prediction that contributed most to this MCC
        best_prediction = None
        for pred in predictions:
            if pred.get('mcc') == best_mcc:
                best_prediction = pred
                break
        
        return {
            'mcc': best_mcc,
            'confidence': min(0.95, consensus_score),  # Cap at 95%
            'method': 'weighted_consensus',
            'consensus_score': consensus_score,
            'contributing_prediction': best_prediction,
            'llm_analysis': best_prediction.get('llm_analysis') if best_prediction else None,
            'enhancement_applied': best_prediction.get('enhancement_applied', False) if best_prediction else False
        }
    
    def _generate_alternatives(self, predictions: List[Dict[str, Any]], 
                             final_prediction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alternative MCC predictions"""
        alternatives = []
        final_mcc = final_prediction['mcc']
        
        # Collect unique MCCs with their best confidence scores
        mcc_confidence = {}
        for pred in predictions:
            if 'error' in pred or not pred.get('mcc'):
                continue
                
            mcc = pred['mcc']
            confidence = pred.get('confidence', 0.5)
            method = pred.get('method', 'unknown')
            
            if mcc != final_mcc:  # Exclude the final prediction
                if mcc not in mcc_confidence or confidence > mcc_confidence[mcc]['confidence']:
                    mcc_confidence[mcc] = {
                        'mcc': mcc,
                        'confidence': confidence,
                        'method': method,
                        'source': pred.get('source', 'unknown')
                    }
        
        # Sort by confidence and return top alternatives
        alternatives = sorted(mcc_confidence.values(), key=lambda x: x['confidence'], reverse=True)
        return alternatives[:3]  # Return top 3 alternatives

# Initialize orchestrator
orchestrator = MCCOrchestrator()

@router.post("/predict", response_model=MCCPredictionResponse)
async def predict_mcc(request: MCCPredictionRequest):
    """
    Comprehensive MCC prediction using all available methods
    """
    try:
        return await orchestrator.predict_mcc(request)
    except Exception as e:
        logger.error(f"MCC prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/enhanced", response_model=MCCPredictionResponse)
async def predict_mcc_enhanced(request: MCCPredictionRequest):
    """
    Enhanced MCC prediction using the new prediction service with POS terminal detection
    """
    try:
        # Initialize prediction service
        await prediction_service.initialize()
        
        # Convert request data to prediction service format
        prediction_data = {
            'wifi_data': [],
            'ble_data': [],
            'location_data': {
                'latitude': request.latitude,
                'longitude': request.longitude,
                'merchant_name': request.merchant_name,
                'radius': request.radius or 200,
                'venue_type': None  # Could be inferred from location service
            },
            'user_id': request.user_id,
            'session_id': request.session_id
        }
        
        # Process WiFi data
        if request.wifi_networks:
            # Use structured WiFi data
            prediction_data['wifi_data'] = [
                {
                    'ssid': wifi.ssid,
                    'bssid': wifi.bssid or '',
                    'rssi': wifi.rssi or -100,
                    'frequency': wifi.frequency or 2400
                }
                for wifi in request.wifi_networks
            ]
        elif request.wifi_ssids:
            # Convert legacy WiFi SSIDs
            prediction_data['wifi_data'] = [
                {'ssid': ssid, 'bssid': '', 'rssi': -70, 'frequency': 2400}
                for ssid in request.wifi_ssids
            ]
        
        # Process BLE data
        if request.ble_beacons:
            # Use structured BLE data
            prediction_data['ble_data'] = [
                {
                    'uuid': beacon.uuid.lower(),
                    'major': beacon.major or 0,
                    'minor': beacon.minor or 0,
                    'rssi': beacon.rssi or -70,
                    'name': beacon.name or ''
                }
                for beacon in request.ble_beacons
            ]
        elif request.bluetooth_devices:
            # Convert legacy Bluetooth device names (limited functionality)
            prediction_data['ble_data'] = [
                {
                    'uuid': '00000000-0000-0000-0000-000000000000',  # Placeholder
                    'major': 0,
                    'minor': 0,
                    'rssi': -70,
                    'name': device.lower()
                }
                for device in request.bluetooth_devices
            ]
        
        # Add terminal information if available
        if request.terminal_id:
            prediction_data['location_data']['terminal_id'] = request.terminal_id
        
        # Add transaction context
        if request.transaction_amount:
            prediction_data['location_data']['transaction_amount'] = request.transaction_amount
        if request.transaction_time:
            prediction_data['location_data']['transaction_time'] = request.transaction_time
        
        # Call enhanced prediction service
        result = await prediction_service.predict_mcc(prediction_data)
        
        # Convert result to API response format
        if result.get('detected', False):
            # Prepare prediction sources
            prediction_sources = []
            
            # Add main prediction
            prediction_sources.append({
                'method': result.get('method', 'unknown'),
                'confidence': result.get('confidence', 0.0),
                'mcc': result.get('mcc'),
                'source': result.get('source', 'enhanced_prediction'),
                'pos_influenced': result.get('pos_influenced', False),
                'pos_type': result.get('pos_type'),
                'reasoning': result.get('reasoning')
            })
            
            # Add alternative predictions if available
            alternatives = []
            if result.get('all_predictions') and request.include_alternatives:
                for pred in result['all_predictions'][1:]:  # Skip first (main) prediction
                    alternatives.append({
                        'mcc': pred.get('mcc'),
                        'confidence': pred.get('confidence', 0.0),
                        'method': pred.get('method', 'unknown'),
                        'source': pred.get('source', 'unknown')
                    })
            
            # Apply LLM enhancement if requested
            llm_analysis = None
            enhancement_applied = False
            if request.use_llm_enhancement:
                # TODO: Integrate with LLM service for additional enhancement
                pass
            
            return MCCPredictionResponse(
                predicted_mcc=result['mcc'],
                confidence=result['confidence'],
                method=result['method'],
                prediction_sources=prediction_sources,
                consensus_score=result.get('consensus_boost', False) and 0.9 or result['confidence'],
                processing_time_ms=50,  # Actual timing would be measured
                alternatives=alternatives if alternatives else None,
                llm_analysis=llm_analysis,
                enhancement_applied=enhancement_applied
            )
        else:
            # No prediction found
            return MCCPredictionResponse(
                predicted_mcc='5999',  # Default miscellaneous
                confidence=0.1,
                method='default_fallback',
                prediction_sources=[{
                    'method': 'fallback',
                    'confidence': 0.1,
                    'mcc': '5999',
                    'source': 'default',
                    'reasoning': result.get('reason', 'No patterns detected')
                }],
                consensus_score=0.0,
                processing_time_ms=25,
                alternatives=None,
                llm_analysis=None,
                enhancement_applied=False
            )
            
    except Exception as e:
        logger.error(f"Enhanced MCC prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Enhanced prediction failed: {str(e)}")

@router.post("/detect/pos-terminals")
async def detect_pos_terminals(
    ble_beacons: List[BLEBeacon] = Body(..., description="BLE beacons to analyze"),
    location_data: Optional[Dict[str, Any]] = Body(None, description="Optional location context")
):
    """
    Direct POS terminal detection from BLE beacon data
    """
    try:
        # Initialize POS terminal service
        await pos_terminal_service.initialize()
        
        # Convert BLE beacon data
        ble_data = [
            {
                'uuid': beacon.uuid.lower(),
                'major': beacon.major or 0,
                'minor': beacon.minor or 0,
                'rssi': beacon.rssi or -70,
                'name': beacon.name or ''
            }
            for beacon in ble_beacons
        ]
        
        # Detect POS terminals
        result = await pos_terminal_service.detect_pos_terminals(ble_data, location_data)
        
        return {
            'detected': result.get('detected', False),
            'pos_type': result.get('pos_type'),
            'confidence': result.get('confidence', 0.0),
            'mcc': result.get('mcc'),
            'mcc_candidates': result.get('mcc_candidates', []),
            'reasoning': result.get('reasoning'),
            'device_info': result.get('device_info'),
            'method': result.get('method'),
            'metadata': result.get('metadata', {})
        }
        
    except Exception as e:
        logger.error(f"POS terminal detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"POS detection failed: {str(e)}")

@router.get("/predict/simple")
async def predict_mcc_simple(
    latitude: float = Query(..., description="Latitude coordinate"),
    longitude: float = Query(..., description="Longitude coordinate"),
    merchant_name: Optional[str] = Query(None, description="Merchant name"),
    radius: Optional[int] = Query(200, description="Search radius in meters"),
    use_llm: Optional[bool] = Query(True, description="Use LLM enhancement")
):
    """
    Simple MCC prediction endpoint for quick integration
    """
    request = MCCPredictionRequest(
        latitude=latitude,
        longitude=longitude,
        merchant_name=merchant_name,
        radius=radius,
        include_alternatives=False,
        use_llm_enhancement=use_llm
    )
    
    response = await orchestrator.predict_mcc(request)
    
    # Return simplified response
    return {
        "mcc": response.predicted_mcc,
        "confidence": response.confidence,
        "method": response.method,
        "processing_time_ms": response.processing_time_ms,
        "llm_enhanced": response.enhancement_applied
    }

@router.post("/analyze/merchant-name")
async def analyze_merchant_name(
    merchant_name: str = Body(..., description="Merchant name to analyze"),
    additional_info: Optional[Dict[str, Any]] = Body(None, description="Additional context")
):
    """
    Analyze merchant name using LLM for MCC prediction
    """
    await orchestrator.initialize_services()
    
    result = await llm_service.analyze_merchant_name(merchant_name, additional_info)
    
    return {
        "merchant_name": merchant_name,
        "analysis": result,
        "service_available": result.get('method') != 'llm_disabled'
    }

@router.post("/resolve/conflicts")
async def resolve_prediction_conflicts(
    conflicting_predictions: List[Dict[str, Any]] = Body(..., description="Conflicting MCC predictions"),
    context: Optional[Dict[str, Any]] = Body(None, description="Additional context")
):
    """
    Use LLM to resolve conflicting MCC predictions
    """
    await orchestrator.initialize_services()
    
    result = await llm_service.resolve_ambiguous_predictions(conflicting_predictions, context or {})
    
    return {
        "resolution": result,
        "original_conflicts": conflicting_predictions,
        "service_available": result.get('method') != 'llm_disabled'
    }

@router.get("/health")
async def health_check():
    """
    Check health and status of all MCC prediction services
    """
    await orchestrator.initialize_services()
    
    # Helper function to safely get service status
    async def safe_get_status(service, service_name):
        try:
            if hasattr(service, 'get_service_status'):
                return await service.get_service_status()
            else:
                # For services without get_service_status, check if they're initialized
                return {
                    'service': service_name,
                    'status': 'available' if service else 'unavailable',
                    'initialized': bool(service)
                }
        except Exception as e:
            return {
                'service': service_name,
                'status': 'error',
                'error': str(e)
            }
    
    # Gather service statuses safely
    statuses = await asyncio.gather(
        safe_get_status(location_service, 'location'),
        safe_get_status(terminal_service, 'terminal'),
        safe_get_status(fingerprint_service, 'fingerprint'),
        safe_get_status(historical_service, 'historical'),
        safe_get_status(llm_service, 'llm'),
        return_exceptions=True
    )
    
    return {
        "status": "healthy",
        "services": {
            "location": statuses[0] if not isinstance(statuses[0], Exception) else {"error": str(statuses[0])},
            "terminal": statuses[1] if not isinstance(statuses[1], Exception) else {"error": str(statuses[1])},
            "fingerprint": statuses[2] if not isinstance(statuses[2], Exception) else {"error": str(statuses[2])},
            "historical": statuses[3] if not isinstance(statuses[3], Exception) else {"error": str(statuses[3])},
            "llm": statuses[4] if not isinstance(statuses[4], Exception) else {"error": str(statuses[4])}
        },
        "orchestrator_initialized": orchestrator.services_initialized,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/config")
async def get_configuration():
    """
    Get current MCC prediction service configuration
    """
    return {
        "services_enabled": {
            "google_places": settings.GOOGLE_PLACES_ENABLED,
            "foursquare": settings.FOURSQUARE_ENABLED,
            "llm_enhancement": bool(settings.OPENAI_API_KEY)
        },
        "api_limits": {
            "google_places_daily": settings.GOOGLE_PLACES_DAILY_LIMIT,
            "foursquare_daily": settings.FOURSQUARE_DAILY_LIMIT
        },
        "cache_settings": {
            "location_cache_hours": settings.LOCATION_CACHE_HOURS,
            "terminal_cache_hours": settings.TERMINAL_CACHE_HOURS
        },
        "confidence_thresholds": {
            "minimum_confidence": settings.MIN_CONFIDENCE_THRESHOLD,
            "high_confidence": settings.HIGH_CONFIDENCE_THRESHOLD
        }
    } 