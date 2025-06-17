import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import asyncio

from ..core.config import settings
from ..database.supabase_client import get_supabase_client
from .fingerprint_service import fingerprint_service
from .pos_terminal_service import pos_terminal_service

logger = logging.getLogger(__name__)

class PredictionService:
    """
    Enhanced prediction service that orchestrates WiFi and BLE analysis
    with advanced POS terminal detection for improved MCC accuracy
    """
    
    def __init__(self):
        self.supabase = None
        self.fingerprint_service = fingerprint_service
        self.pos_terminal_service = pos_terminal_service
        
    async def initialize(self):
        """Initialize the prediction service"""
        try:
            self.supabase = get_supabase_client()
            await self.fingerprint_service.initialize()
            await self.pos_terminal_service.initialize()
            logger.info("PredictionService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PredictionService: {str(e)}")
            raise
    
    async def predict_mcc(self, prediction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main prediction method that combines WiFi and BLE analysis
        with advanced POS terminal detection
        
        Args:
            prediction_data: Dictionary containing:
                - wifi_data: List of WiFi networks (optional)
                - ble_data: List of BLE beacons (optional)
                - location_data: Location context (optional)
                - user_id: User identifier for personalization
                - session_id: Session identifier for tracking
        
        Returns:
            Comprehensive prediction results with confidence scores
        """
        try:
            wifi_data = prediction_data.get('wifi_data', [])
            ble_data = prediction_data.get('ble_data', [])
            location_data = prediction_data.get('location_data', {})
            user_id = prediction_data.get('user_id')
            session_id = prediction_data.get('session_id')
            
            logger.info(f"Starting MCC prediction - WiFi: {len(wifi_data)} networks, BLE: {len(ble_data)} beacons")
            
            # Parallel analysis for maximum efficiency
            wifi_future = None
            ble_future = None
            
            if wifi_data:
                wifi_future = self.fingerprint_service.analyze_wifi_fingerprint(wifi_data, location_data)
            
            if ble_data:
                ble_future = self.fingerprint_service.analyze_ble_fingerprint(ble_data, location_data)
            
            # Wait for both analyses to complete
            wifi_result = None
            ble_result = None
            
            if wifi_future and ble_future:
                wifi_result, ble_result = await asyncio.gather(wifi_future, ble_future)
            elif wifi_future:
                wifi_result = await wifi_future
            elif ble_future:
                ble_result = await ble_future
            else:
                return self._get_empty_prediction_result("No WiFi or BLE data provided")
            
            # Combine results with intelligent prioritization
            combined_result = self._combine_prediction_results(wifi_result, ble_result, location_data)
            
            # Add metadata
            combined_result.update({
                'prediction_timestamp': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'session_id': session_id,
                'data_sources': {
                    'wifi_networks': len(wifi_data),
                    'ble_beacons': len(ble_data),
                    'has_location': bool(location_data)
                }
            })
            
            # Store prediction result for analytics and learning
            await self._store_prediction_result(combined_result, prediction_data)
            
            return combined_result
            
        except Exception as e:
            logger.error(f"Error in MCC prediction: {str(e)}")
            return self._get_empty_prediction_result(f"Prediction error: {str(e)}")
    
    def _combine_prediction_results(self, wifi_result: Optional[Dict], ble_result: Optional[Dict], 
                                  location_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligently combine WiFi and BLE prediction results
        with proper prioritization based on confidence and method type
        """
        predictions = []
        analysis_details = {}
        
        # Process BLE results (higher priority due to POS detection)
        if ble_result and ble_result.get('detected', False):
            predictions.append({
                'mcc': ble_result.get('mcc'),
                'confidence': ble_result.get('confidence', 0.0),
                'method': ble_result.get('method', 'ble_analysis'),
                'source': ble_result.get('source', 'ble'),
                'data_type': 'ble',
                'pos_influenced': ble_result.get('pos_influenced', False),
                'pos_type': ble_result.get('pos_type'),
                'reasoning': ble_result.get('reasoning')
            })
            analysis_details['ble'] = ble_result
        
        # Process WiFi results
        if wifi_result and wifi_result.get('detected', False):
            predictions.append({
                'mcc': wifi_result.get('mcc'),
                'confidence': wifi_result.get('confidence', 0.0),
                'method': wifi_result.get('method', 'wifi_analysis'),
                'source': wifi_result.get('source', 'wifi'),
                'data_type': 'wifi'
            })
            analysis_details['wifi'] = wifi_result
        
        # Apply intelligent weighting based on method reliability
        method_priorities = {
            'pos_terminal_detection': 1.0,          # Highest - direct POS detection
            'specialized_pos_detection': 1.0,       # Same priority
            'learned_terminal_mapping': 0.95,       # Very high - learned patterns
            'ble_beacon_detection': 0.8,            # High - known beacon patterns
            'wifi_brand_detection': 0.75,           # High - known WiFi patterns
            'ble_historical_match': 0.7,            # Medium-high
            'wifi_historical_match': 0.65,          # Medium-high
            'ble_venue_match': 0.6,                 # Medium
            'wifi_venue_match': 0.55,               # Medium
            'ble_deployment_pattern': 0.5,          # Lower
            'wifi_pattern_analysis': 0.45           # Lower
        }
        
        # Calculate weighted confidence scores
        for prediction in predictions:
            method = prediction['method']
            priority = method_priorities.get(method, 0.4)
            prediction['weighted_confidence'] = prediction['confidence'] * priority
            prediction['priority'] = priority
        
        # Select best prediction
        if predictions:
            best_prediction = max(predictions, key=lambda x: x['weighted_confidence'])
            
            # Determine final MCC and confidence
            final_mcc = best_prediction['mcc']
            final_confidence = best_prediction['confidence']
            
            # Boost confidence if multiple methods agree
            agreeing_predictions = [p for p in predictions if p['mcc'] == final_mcc]
            if len(agreeing_predictions) > 1:
                confidence_boost = min(0.2, (len(agreeing_predictions) - 1) * 0.1)
                final_confidence = min(1.0, final_confidence + confidence_boost)
            
            # Special handling for POS-detected MCCs
            pos_influenced = any(p.get('pos_influenced', False) for p in predictions)
            if pos_influenced:
                logger.info(f"POS terminal detected, MCC prediction: {final_mcc}")
            
            return {
                'detected': True,
                'mcc': final_mcc,
                'confidence': final_confidence,
                'method': best_prediction['method'],
                'source': best_prediction['source'],
                'data_type': best_prediction['data_type'],
                'pos_influenced': pos_influenced,
                'pos_type': best_prediction.get('pos_type'),
                'reasoning': best_prediction.get('reasoning'),
                'all_predictions': predictions,
                'analysis_details': analysis_details,
                'consensus_boost': len(agreeing_predictions) > 1
            }
        
        return self._get_empty_prediction_result("No valid predictions found")
    
    async def predict_mcc_from_ble_only(self, ble_data: List[Dict[str, Any]], 
                                       location_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Predict MCC using only BLE data - optimized for POS terminal detection
        """
        try:
            if not ble_data:
                return self._get_empty_prediction_result("No BLE data provided")
            
            result = await self.fingerprint_service.analyze_ble_fingerprint(ble_data, location_data)
            
            if result.get('detected', False):
                return {
                    'detected': True,
                    'mcc': result['mcc'],
                    'confidence': result['confidence'],
                    'method': result['method'],
                    'source': result.get('source', 'ble'),
                    'data_type': 'ble',
                    'pos_influenced': result.get('pos_influenced', False),
                    'pos_type': result.get('pos_type'),
                    'reasoning': result.get('reasoning'),
                    'beacon_count': len(ble_data),
                    'analysis_details': {'ble': result}
                }
            
            return self._get_empty_prediction_result("No BLE patterns matched")
            
        except Exception as e:
            logger.error(f"Error in BLE-only prediction: {str(e)}")
            return self._get_empty_prediction_result(f"BLE prediction error: {str(e)}")
    
    async def predict_mcc_from_wifi_only(self, wifi_data: List[Dict[str, Any]], 
                                        location_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Predict MCC using only WiFi data
        """
        try:
            if not wifi_data:
                return self._get_empty_prediction_result("No WiFi data provided")
            
            result = await self.fingerprint_service.analyze_wifi_fingerprint(wifi_data, location_data)
            
            if result.get('detected', False):
                return {
                    'detected': True,
                    'mcc': result['mcc'],
                    'confidence': result['confidence'],
                    'method': result['method'],
                    'source': result.get('source', 'wifi'),
                    'data_type': 'wifi',
                    'network_count': len(wifi_data),
                    'analysis_details': {'wifi': result}
                }
            
            return self._get_empty_prediction_result("No WiFi patterns matched")
            
        except Exception as e:
            logger.error(f"Error in WiFi-only prediction: {str(e)}")
            return self._get_empty_prediction_result(f"WiFi prediction error: {str(e)}")
    
    async def detect_pos_terminals(self, ble_data: List[Dict[str, Any]], 
                                  location_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Direct POS terminal detection method
        """
        try:
            return await self.pos_terminal_service.detect_pos_terminals(ble_data, location_data)
        except Exception as e:
            logger.error(f"Error in POS detection: {str(e)}")
            return {'detected': False, 'error': str(e)}
    
    async def _store_prediction_result(self, result: Dict[str, Any], original_data: Dict[str, Any]):
        """Store prediction result for analytics and learning"""
        try:
            if not self.supabase:
                return
            
            prediction_record = {
                'user_id': original_data.get('user_id'),
                'session_id': original_data.get('session_id'),
                'predicted_mcc': result.get('mcc'),
                'confidence': result.get('confidence'),
                'method': result.get('method'),
                'source': result.get('source'),
                'data_type': result.get('data_type'),
                'pos_influenced': result.get('pos_influenced', False),
                'pos_type': result.get('pos_type'),
                'wifi_network_count': len(original_data.get('wifi_data', [])),
                'ble_beacon_count': len(original_data.get('ble_data', [])),
                'has_location_data': bool(original_data.get('location_data')),
                'prediction_timestamp': datetime.utcnow().isoformat(),
                'full_result': result
            }
            
            await self.supabase.table('prediction_analytics').insert(prediction_record).execute()
            
        except Exception as e:
            logger.warning(f"Failed to store prediction result: {str(e)}")
    
    def _get_empty_prediction_result(self, reason: str = "No predictions available") -> Dict[str, Any]:
        """Return empty prediction result with reason"""
        return {
            'detected': False,
            'confidence': 0.0,
            'reason': reason,
            'prediction_timestamp': datetime.utcnow().isoformat()
        }

# Global instance
prediction_service = PredictionService() 