"""
MCC Prediction Engine
Multi-layered MCC detection system with OpenAI-powered intelligence
"""

import asyncio
import logging
import json
import hashlib
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
from geopy.distance import geodesic
import numpy as np

from app.models.schemas import (
    PreTapContext, MCCPrediction, MCCDetectionMethod, 
    LocationData, WiFiData, BLEData, TerminalData
)
from app.core.config import settings
from app.services.ai_inference import ai_inference_service

logger = logging.getLogger(__name__)


class MCCPredictionEngine:
    """
    Advanced MCC prediction using layered detection methods with OpenAI intelligence
    """
    
    def __init__(self):
        self.terminal_cache = {}  # terminal_id -> mcc mapping
        self.location_cache = {}  # location_hash -> mcc mapping
        self.wifi_cache = {}     # wifi_hash -> mcc mapping
        self.ble_cache = {}      # ble_hash -> mcc mapping
        self.merchant_cache = {} # merchant_name -> mcc mapping
        self.behavioral_model = None
        
        # Load cached mappings
        self._load_cached_mappings()
    
    async def predict_mcc(self, context: PreTapContext) -> MCCPrediction:
        """
        Main MCC prediction method using layered approach with OpenAI integration
        """
        logger.info(f"Predicting MCC for session {context.session_id}")
        
        # Layer 1: Terminal ID Match
        prediction = await self._predict_from_terminal_id(context)
        if prediction and prediction.confidence >= settings.MCC_CONFIDENCE_THRESHOLD:
            return prediction
        
        # Layer 2: GPS Location Match
        prediction = await self._predict_from_location(context)
        if prediction and prediction.confidence >= settings.MCC_CONFIDENCE_THRESHOLD:
            return prediction
        
        # Layer 3: Wi-Fi Fingerprinting
        prediction = await self._predict_from_wifi(context)
        if prediction and prediction.confidence >= settings.MCC_CONFIDENCE_THRESHOLD:
            return prediction
        
        # Layer 4: BLE Beacon Detection
        prediction = await self._predict_from_ble(context)
        if prediction and prediction.confidence >= settings.MCC_CONFIDENCE_THRESHOLD:
            return prediction
        
        # Layer 5: Behavioral Prediction
        prediction = await self._predict_from_behavior(context)
        if prediction and prediction.confidence >= settings.MCC_CONFIDENCE_THRESHOLD:
            return prediction
        
        # Layer 6: Enhanced OpenAI Analysis
        prediction = await self._predict_from_openai_analysis(context)
        if prediction and prediction.confidence >= 0.4:  # Lower threshold for OpenAI
            return prediction
        
        # Layer 7: Basic OpenAI Fallback
        prediction = await self._predict_from_llm(context)
        if prediction:
            return prediction
        
        # Ultimate fallback - general retail
        return MCCPrediction(
            mcc="5999",  # Miscellaneous retail
            confidence=0.1,
            method=MCCDetectionMethod.LLM,
            confidence_level="low",
            metadata={"fallback": True}
        )
    
    async def predict_from_merchant_name(self, merchant_name: str, context: PreTapContext = None) -> Optional[MCCPrediction]:
        """
        Predict MCC from merchant name using OpenAI intelligence
        """
        if not merchant_name:
            return None
        
        # Check cache first
        cached_result = self.merchant_cache.get(merchant_name.lower())
        if cached_result:
            return MCCPrediction(
                mcc=cached_result["mcc"],
                confidence=min(cached_result["confidence"], 0.9),
                method=MCCDetectionMethod.MERCHANT_NAME,
                confidence_level="high",
                metadata={
                    "merchant_name": merchant_name,
                    "cached": True
                }
            )
        
        # Use OpenAI for merchant analysis
        try:
            openai_context = {}
            if context:
                openai_context = {
                    "time_of_day": context.timestamp.hour,
                    "day_of_week": context.timestamp.strftime("%A"),
                    "amount": getattr(context, 'amount', None)
                }
                if context.location:
                    openai_context["location_type"] = "available"
            
            result = await ai_inference_service.predict_merchant_category(merchant_name, openai_context)
            
            if result:
                # Cache the result
                self.merchant_cache[merchant_name.lower()] = {
                    "mcc": result["mcc"],
                    "confidence": result["confidence"],
                    "last_updated": datetime.utcnow()
                }
                
                return MCCPrediction(
                    mcc=result["mcc"],
                    confidence=result["confidence"],
                    method=MCCDetectionMethod.MERCHANT_NAME,
                    confidence_level=self._get_confidence_level(result["confidence"]),
                    metadata={
                        "merchant_name": merchant_name,
                        "reasoning": result.get("reasoning"),
                        "category": result.get("category"),
                        "merchant_type": result.get("merchant_type"),
                        "llm_provider": "openai"
                    }
                )
                
        except Exception as e:
            logger.error(f"OpenAI merchant prediction failed: {e}")
        
        return None

    async def _predict_from_terminal_id(self, context: PreTapContext) -> Optional[MCCPrediction]:
        """
        Layer 1: Terminal ID-based prediction with enhanced device analysis
        """
        if not context.terminal_data or not context.terminal_data.terminal_id:
            return None
        
        terminal_id = context.terminal_data.terminal_id
        
        # Check exact terminal cache
        if terminal_id in self.terminal_cache:
            cached_data = self.terminal_cache[terminal_id]
            return MCCPrediction(
                mcc=cached_data["mcc"],
                confidence=0.9,
                method=MCCDetectionMethod.TERMINAL_ID,
                confidence_level="high",
                metadata={
                    "terminal_id": terminal_id,
                    "last_seen": cached_data.get("last_seen"),
                    "usage_count": cached_data.get("count", 1)
                }
            )
        
        # Analyze device patterns with OpenAI if available
        device_prediction = await self._analyze_device_with_openai(context.terminal_data, context)
        if device_prediction:
            return device_prediction
        
        # Fallback to rule-based device analysis
        device_analysis = self._analyze_device_pattern(context.terminal_data)
        if device_analysis:
            return MCCPrediction(
                mcc=device_analysis["mcc"],
                confidence=device_analysis["confidence"],
                method=MCCDetectionMethod.TERMINAL_ID,
                confidence_level=self._get_confidence_level(device_analysis["confidence"]),
                metadata={
                    "terminal_id": terminal_id,
                    "device_pattern": True,
                    "pos_type": context.terminal_data.pos_type
                }
            )
        
        return None
    
    async def _predict_from_location(self, context: PreTapContext) -> Optional[MCCPrediction]:
        """
        Layer 2: GPS location-based prediction with OpenAI enhancement
        """
        if not context.location:
            return None
        
        location = context.location
        location_hash = self._hash_location(location.latitude, location.longitude)
        
        # Check exact location cache
        if location_hash in self.location_cache:
            cached_data = self.location_cache[location_hash]
            return MCCPrediction(
                mcc=cached_data["mcc"],
                confidence=0.85,
                method=MCCDetectionMethod.GPS,
                confidence_level="high",
                metadata={
                    "location_hash": location_hash,
                    "accuracy": location.accuracy,
                    "cached": True
                }
            )
        
        # Check nearby locations (within radius)
        nearby_prediction = await self._find_nearby_location_match(location)
        if nearby_prediction:
            return nearby_prediction
        
        # Use external location services (Google Places, etc.)
        places_prediction = await self._predict_from_places_api(location)
        if places_prediction:
            return places_prediction
        
        return None
    
    async def _predict_from_wifi(self, context: PreTapContext) -> Optional[MCCPrediction]:
        """
        Layer 3: Wi-Fi fingerprinting with OpenAI analysis
        """
        if not context.wifi_networks:
            return None
        
        wifi_hash = self._hash_wifi_fingerprint(context.wifi_networks)
        
        # Check Wi-Fi cache
        if wifi_hash in self.wifi_cache:
            cached_data = self.wifi_cache[wifi_hash]
            return MCCPrediction(
                mcc=cached_data["mcc"],
                confidence=0.75,
                method=MCCDetectionMethod.WIFI,
                confidence_level="medium",
                metadata={
                    "wifi_hash": wifi_hash,
                    "network_count": len(context.wifi_networks),
                    "cached": True
                }
            )
        
        # Use OpenAI to analyze WiFi patterns
        wifi_analysis = await self._analyze_wifi_with_openai(context.wifi_networks, context)
        if wifi_analysis:
            return wifi_analysis
        
        return None
    
    async def _predict_from_ble(self, context: PreTapContext) -> Optional[MCCPrediction]:
        """
        Layer 4: BLE beacon detection with OpenAI insights
        """
        if not context.ble_devices:
            return None
        
        ble_hash = self._hash_ble_fingerprint(context.ble_devices)
        
        # Check BLE cache
        if ble_hash in self.ble_cache:
            cached_data = self.ble_cache[ble_hash]
            return MCCPrediction(
                mcc=cached_data["mcc"],
                confidence=0.7,
                method=MCCDetectionMethod.BLE,
                confidence_level="medium",
                metadata={
                    "ble_hash": ble_hash,
                    "device_count": len(context.ble_devices),
                    "cached": True
                }
            )
        
        # Use OpenAI to analyze BLE patterns
        ble_analysis = await self._analyze_ble_with_openai(context.ble_devices, context)
        if ble_analysis:
            return ble_analysis
        
        return None
    
    async def _predict_from_behavior(self, context: PreTapContext) -> Optional[MCCPrediction]:
        """
        Layer 5: Behavioral pattern prediction enhanced with OpenAI
        """
        try:
            # Get user's historical patterns
            user_patterns = await self._get_user_patterns(context.user_id)
            
            if not user_patterns:
                return None
            
            # Analyze current context against patterns
            current_time = datetime.utcnow()
            time_features = {
                "hour": current_time.hour,
                "day_of_week": current_time.weekday(),
                "is_weekend": current_time.weekday() >= 5
            }
            
            # Simple pattern matching (in production, use ML model)
            best_match = self._find_behavioral_match(time_features, user_patterns)
            
            if best_match and best_match["confidence"] > 0.5:
                return MCCPrediction(
                    mcc=best_match["mcc"],
                    confidence=best_match["confidence"],
                    method=MCCDetectionMethod.BEHAVIORAL,
                    confidence_level="medium",
                    metadata={
                        "pattern_type": "temporal",
                        "historical_matches": best_match.get("count", 1)
                    }
                )
        
        except Exception as e:
            logger.error(f"Behavioral prediction failed: {e}")
        
        return None
    
    async def _predict_from_openai_analysis(self, context: PreTapContext) -> Optional[MCCPrediction]:
        """
        Layer 6: Enhanced OpenAI context analysis
        """
        try:
            # Prepare comprehensive context for OpenAI
            analysis_context = {
                "timestamp": context.timestamp.isoformat(),
                "time_of_day": context.timestamp.hour,
                "day_of_week": context.timestamp.strftime("%A"),
                "has_location": context.location is not None,
                "wifi_count": len(context.wifi_networks) if context.wifi_networks else 0,
                "ble_count": len(context.ble_devices) if context.ble_devices else 0,
                "has_terminal": context.terminal_data is not None
            }
            
            if context.terminal_data:
                analysis_context.update({
                    "pos_type": context.terminal_data.pos_type,
                    "terminal_type": getattr(context.terminal_data, 'terminal_type', None),
                    "device_id": context.terminal_data.device_id
                })
            
            if hasattr(context, 'amount') and context.amount:
                analysis_context["amount"] = float(context.amount)
            
            # Get detailed analysis from OpenAI
            analysis_result = await ai_inference_service.analyze_transaction_context(analysis_context)
            
            if analysis_result and analysis_result.get("merchant_insights"):
                insights = analysis_result["merchant_insights"]
                confidence = analysis_result.get("confidence", 0.4)
                
                # Extract MCC from insights
                if insights.get("type"):
                    mcc = self._category_to_mcc(insights["type"])
                    if mcc:
                        return MCCPrediction(
                            mcc=mcc,
                            confidence=min(confidence, 0.8),  # Cap confidence for context analysis
                            method=MCCDetectionMethod.LLM,
                            confidence_level=self._get_confidence_level(confidence),
                            metadata={
                                "analysis_type": "context_analysis",
                                "merchant_insights": insights,
                                "recommendations": analysis_result.get("recommendations", []),
                                "llm_provider": "openai"
                            }
                        )
        
        except Exception as e:
            logger.error(f"OpenAI context analysis failed: {e}")
        
        return None
    
    async def _predict_from_llm(self, context: PreTapContext) -> Optional[MCCPrediction]:
        """
        Layer 7: Basic OpenAI fallback prediction
        """
        try:
            # Prepare basic context for LLM
            llm_context = self._prepare_llm_context(context)
            
            # Get prediction from AI service
            prediction = await ai_inference_service.predict_mcc(llm_context)
            
            if prediction:
                return MCCPrediction(
                    mcc=prediction["mcc"],
                    confidence=min(prediction.get("confidence", 0.3), 0.6),  # Cap LLM confidence
                    method=MCCDetectionMethod.LLM,
                    confidence_level="low",
                    metadata={
                        "llm_reasoning": prediction.get("reasoning"),
                        "category": prediction.get("category"),
                        "llm_provider": prediction.get("llm_provider", "openai"),
                        "llm_model": prediction.get("llm_model"),
                        "context_used": llm_context
                    }
                )
        
        except Exception as e:
            logger.error(f"LLM prediction failed: {e}")
        
        return None
    
    # Enhanced helper methods with OpenAI integration
    
    async def _analyze_device_with_openai(self, terminal_data: TerminalData, context: PreTapContext) -> Optional[MCCPrediction]:
        """Analyze terminal device using OpenAI"""
        try:
            device_context = {
                "device_id": terminal_data.device_id,
                "pos_type": terminal_data.pos_type,
                "terminal_type": getattr(terminal_data, 'terminal_type', None),
                "time_of_day": context.timestamp.hour,
                "day_of_week": context.timestamp.strftime("%A")
            }
            
            if hasattr(context, 'amount'):
                device_context["amount"] = float(context.amount)
            
            # Use merchant prediction for device analysis
            analysis = await ai_inference_service.predict_merchant_category(
                f"{terminal_data.pos_type} {terminal_data.device_id}", 
                device_context
            )
            
            if analysis and analysis["confidence"] > 0.5:
                return MCCPrediction(
                    mcc=analysis["mcc"],
                    confidence=analysis["confidence"],
                    method=MCCDetectionMethod.TERMINAL_ID,
                    confidence_level=self._get_confidence_level(analysis["confidence"]),
                    metadata={
                        "terminal_id": terminal_data.terminal_id,
                        "openai_analysis": True,
                        "reasoning": analysis.get("reasoning"),
                        "category": analysis.get("category")
                    }
                )
        
        except Exception as e:
            logger.error(f"OpenAI device analysis failed: {e}")
        
        return None
    
    async def _analyze_wifi_with_openai(self, wifi_networks: List[WiFiData], context: PreTapContext) -> Optional[MCCPrediction]:
        """Analyze WiFi networks using OpenAI"""
        try:
            # Create WiFi context summary
            network_summary = []
            for network in wifi_networks[:5]:  # Top 5 networks
                if network.ssid and not network.ssid.startswith("__"):  # Filter out hidden/system networks
                    network_summary.append(f"'{network.ssid}' (signal: {network.signal_strength})")
            
            if not network_summary:
                return None
            
            wifi_context = {
                "wifi_networks": network_summary,
                "network_count": len(wifi_networks),
                "time_of_day": context.timestamp.hour,
                "location_available": context.location is not None
            }
            
            # Analyze with OpenAI
            analysis = await ai_inference_service.analyze_transaction_context(wifi_context)
            
            if analysis and analysis.get("merchant_insights"):
                insights = analysis["merchant_insights"]
                if insights.get("type"):
                    mcc = self._category_to_mcc(insights["type"])
                    if mcc:
                        confidence = min(analysis.get("confidence", 0.4), 0.7)  # Cap WiFi confidence
                        return MCCPrediction(
                            mcc=mcc,
                            confidence=confidence,
                            method=MCCDetectionMethod.WIFI,
                            confidence_level=self._get_confidence_level(confidence),
                            metadata={
                                "wifi_analysis": True,
                                "network_count": len(wifi_networks),
                                "insights": insights,
                                "llm_provider": "openai"
                            }
                        )
        
        except Exception as e:
            logger.error(f"OpenAI WiFi analysis failed: {e}")
        
        return None
    
    async def _analyze_ble_with_openai(self, ble_devices: List[BLEData], context: PreTapContext) -> Optional[MCCPrediction]:
        """Analyze BLE devices using OpenAI"""
        try:
            # Create BLE context summary
            device_summary = []
            for device in ble_devices[:5]:  # Top 5 devices
                device_info = f"{device.device_type or 'unknown'}"
                if device.device_name:
                    device_info += f" ({device.device_name})"
                device_summary.append(device_info)
            
            if not device_summary:
                return None
            
            ble_context = {
                "ble_devices": device_summary,
                "device_count": len(ble_devices),
                "time_of_day": context.timestamp.hour,
                "location_available": context.location is not None
            }
            
            # Analyze with OpenAI
            analysis = await ai_inference_service.analyze_transaction_context(ble_context)
            
            if analysis and analysis.get("merchant_insights"):
                insights = analysis["merchant_insights"]
                if insights.get("type"):
                    mcc = self._category_to_mcc(insights["type"])
                    if mcc:
                        confidence = min(analysis.get("confidence", 0.4), 0.6)  # Cap BLE confidence
                        return MCCPrediction(
                            mcc=mcc,
                            confidence=confidence,
                            method=MCCDetectionMethod.BLE,
                            confidence_level=self._get_confidence_level(confidence),
                            metadata={
                                "ble_analysis": True,
                                "device_count": len(ble_devices),
                                "insights": insights,
                                "llm_provider": "openai"
                            }
                        )
        
        except Exception as e:
            logger.error(f"OpenAI BLE analysis failed: {e}")
        
        return None

    # Helper methods
    
    def _analyze_device_pattern(self, terminal_data: TerminalData) -> Optional[Dict]:
        """Analyze device patterns for MCC hints"""
        device_patterns = {
            "square": {"mcc": "5999", "confidence": 0.6},
            "stripe": {"mcc": "5999", "confidence": 0.6},
            "clover": {"mcc": "5812", "confidence": 0.5},  # Restaurant bias
            "toast": {"mcc": "5812", "confidence": 0.7},   # Restaurant POS
            "revel": {"mcc": "5812", "confidence": 0.6},   # Restaurant POS
            "shopkeep": {"mcc": "5999", "confidence": 0.5}, # Retail
            "lightspeed": {"mcc": "5999", "confidence": 0.5} # Retail
        }
        
        device_id = terminal_data.device_id.lower() if terminal_data.device_id else ""
        pos_type = terminal_data.pos_type.lower() if terminal_data.pos_type else ""
        
        for pattern, data in device_patterns.items():
            if pattern in device_id or pattern in pos_type:
                return data
        
        return None
    
    def _category_to_mcc(self, category: str) -> Optional[str]:
        """Convert category to MCC code"""
        category_mapping = {
            "restaurant": "5812",
            "fast_food": "5814",
            "coffee": "5814",
            "grocery": "5411",
            "gas": "5541",
            "retail": "5999",
            "electronics": "5732",
            "department_store": "5311",
            "hotel": "7011",
            "transportation": "4111",
            "convenience": "5411",
            "pharmacy": "5912",
            "clothing": "5691",
            "automotive": "5511"
        }
        
        return category_mapping.get(category.lower())
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Convert confidence score to level"""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        else:
            return "low"

    async def _find_nearby_location_match(self, location: LocationData) -> Optional[MCCPrediction]:
        """Find MCC matches for nearby locations"""
        # This would query the database for nearby cached locations
        # For now, return None as this requires spatial database queries
        return None
    
    async def _predict_from_places_api(self, location: LocationData) -> Optional[MCCPrediction]:
        """Use Google Places API for location-based MCC prediction"""
        # This would integrate with Google Places API
        # For now, return None as this requires external API integration
        return None
    
    def _hash_location(self, lat: float, lng: float, precision: int = 4) -> str:
        """Create a hash for location coordinates"""
        lat_rounded = round(lat, precision)
        lng_rounded = round(lng, precision)
        location_string = f"{lat_rounded},{lng_rounded}"
        return hashlib.md5(location_string.encode()).hexdigest()[:12]
    
    def _hash_wifi_fingerprint(self, wifi_networks: List[WiFiData]) -> str:
        """Create a hash for WiFi fingerprint"""
        sorted_networks = sorted(wifi_networks, key=lambda x: x.signal_strength, reverse=True)[:5]
        fingerprint_data = [f"{net.ssid}:{net.bssid}" for net in sorted_networks if net.ssid]
        fingerprint_string = "|".join(fingerprint_data)
        return hashlib.md5(fingerprint_string.encode()).hexdigest()[:12]
    
    def _hash_ble_fingerprint(self, ble_devices: List[BLEData]) -> str:
        """Create a hash for BLE fingerprint"""
        sorted_devices = sorted(ble_devices, key=lambda x: x.rssi, reverse=True)[:5]
        fingerprint_data = [f"{device.device_type}:{device.device_name}" for device in sorted_devices]
        fingerprint_string = "|".join(fingerprint_data)
        return hashlib.md5(fingerprint_string.encode()).hexdigest()[:12]
    
    async def _get_user_patterns(self, user_id: str) -> Dict:
        """Get user behavioral patterns"""
        # This would query user transaction history
        # For now, return empty dict
        return {}
    
    def _find_behavioral_match(self, time_features: Dict, patterns: Dict) -> Optional[Dict]:
        """Find best behavioral pattern match"""
        current_hour = time_features["hour"]
        
        for pattern_name, pattern_data in patterns.items():
            if current_hour in pattern_data.get("hours", []):
                return {
                    "mcc": pattern_data["mcc"],
                    "confidence": pattern_data["confidence"],
                    "count": pattern_data.get("count", 1)
                }
        
        return None
    
    def _prepare_llm_context(self, context: PreTapContext) -> Dict:
        """Prepare context data for LLM inference"""
        llm_context = {
            "timestamp": context.timestamp.isoformat(),
            "has_location": context.location is not None,
            "wifi_count": len(context.wifi_networks) if context.wifi_networks else 0,
            "ble_count": len(context.ble_devices) if context.ble_devices else 0,
            "has_terminal": context.terminal_data is not None
        }
        
        # Add non-sensitive context
        if context.location:
            llm_context["time_of_day"] = context.timestamp.hour
            llm_context["day_of_week"] = context.timestamp.strftime("%A")
        
        if context.terminal_data and context.terminal_data.pos_type:
            llm_context["pos_type"] = context.terminal_data.pos_type
            llm_context["terminal_type"] = getattr(context.terminal_data, 'terminal_type', None)
        
        if hasattr(context, 'amount'):
            llm_context["amount"] = float(context.amount)
        
        return llm_context
    
    def _load_cached_mappings(self):
        """Load cached MCC mappings from storage"""
        # In production, this would load from Redis or database
        # For now, initialize with some sample data
        
        self.terminal_cache = {
            "SQ_TERM_12345": {"mcc": "5814", "last_seen": datetime.utcnow(), "count": 15},
            "STRIPE_T_67890": {"mcc": "5999", "last_seen": datetime.utcnow(), "count": 8},
            "TOAST_POS_111": {"mcc": "5812", "last_seen": datetime.utcnow(), "count": 25}
        }
        
        self.wifi_cache = {
            "abc123def456": {"mcc": "5814", "count": 12},
            "xyz789uvw012": {"mcc": "5411", "count": 6}
        }
        
        self.merchant_cache = {
            "starbucks": {"mcc": "5814", "confidence": 0.95, "last_updated": datetime.utcnow()},
            "mcdonald's": {"mcc": "5814", "confidence": 0.95, "last_updated": datetime.utcnow()},
            "whole foods": {"mcc": "5411", "confidence": 0.95, "last_updated": datetime.utcnow()}
        }
    
    async def learn_from_feedback(self, session_id: str, actual_mcc: str, prediction: MCCPrediction):
        """Learn from transaction feedback to improve predictions"""
        logger.info(f"Learning from feedback for session {session_id}")
        
        # Update caches based on successful predictions
        if prediction.method == MCCDetectionMethod.TERMINAL_ID:
            terminal_id = prediction.metadata.get("terminal_id")
            if terminal_id:
                self.terminal_cache[terminal_id] = {
                    "mcc": actual_mcc,
                    "last_seen": datetime.utcnow(),
                    "count": self.terminal_cache.get(terminal_id, {}).get("count", 0) + 1
                }
        
        elif prediction.method == MCCDetectionMethod.GPS:
            location_hash = prediction.metadata.get("location_hash")
            if location_hash:
                self.location_cache[location_hash] = {
                    "mcc": actual_mcc,
                    "last_seen": datetime.utcnow(),
                    "count": self.location_cache.get(location_hash, {}).get("count", 0) + 1
                }
        
        elif prediction.method == MCCDetectionMethod.MERCHANT_NAME:
            merchant_name = prediction.metadata.get("merchant_name")
            if merchant_name:
                self.merchant_cache[merchant_name.lower()] = {
                    "mcc": actual_mcc,
                    "confidence": min(0.95, prediction.confidence + 0.1),
                    "last_updated": datetime.utcnow()
                }
        
        # Similar updates for other methods...


# Global instance
mcc_prediction_engine = MCCPredictionEngine() 