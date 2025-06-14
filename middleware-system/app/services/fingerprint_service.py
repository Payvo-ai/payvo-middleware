"""
Enhanced WiFi/BLE Fingerprinting Service for MCC Prediction
Analyzes WiFi and Bluetooth Low Energy signals to predict merchant categories
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import json
import hashlib
import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import math

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from geopy.distance import geodesic

from ..core.config import settings
from ..database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class FingerprintService:
    """Enhanced WiFi/BLE fingerprinting service"""
    
    def __init__(self):
        self.supabase = None
        self.wifi_patterns = {}
        self.ble_patterns = {}
        self.brand_signatures = {}
        self.venue_fingerprints = {}
        self.confidence_threshold = 0.6
        
    async def initialize(self):
        """Initialize the fingerprint service with database connectivity"""
        try:
            # Initialize Supabase client
            self.supabase = get_supabase_client()
            
            # Test database connectivity if available
            if self.supabase.is_available:
                # Supabase operations are synchronous, no await needed
                self.supabase.client.table('wifi_fingerprints').select('*').limit(1).execute()
                self.supabase.client.table('ble_fingerprints').select('*').limit(1).execute()
                self.supabase.client.table('venue_fingerprints').select('*').limit(1).execute()
                logger.info("Fingerprint service database connectivity verified")
            else:
                logger.warning("Fingerprint service: Supabase not available, using fallback")
                
        except Exception as e:
            logger.warning(f"Fingerprint service database connection failed: {e}")
            self.supabase = None
    
    async def validate_database_connectivity(self):
        """Validate database connectivity for fingerprint operations"""
        try:
            if self.supabase and self.supabase.is_available:
                # Test all fingerprint tables
                self.supabase.client.table('wifi_fingerprints').select('*').limit(1).execute()
                self.supabase.client.table('ble_fingerprints').select('*').limit(1).execute()
                self.supabase.client.table('venue_fingerprints').select('*').limit(1).execute()
                logger.info("Fingerprint service database validation successful")
                return True
        except Exception as e:
            logger.error(f"Fingerprint service database validation failed: {e}")
        return False
    
    async def _create_fingerprint_tables(self):
        """Create database tables for fingerprinting data"""
        try:
            # Check if tables exist
            self.supabase.client.table('wifi_fingerprints').select('*').limit(1).execute()
            self.supabase.client.table('ble_fingerprints').select('*').limit(1).execute()
            self.supabase.client.table('venue_fingerprints').select('*').limit(1).execute()
        except:
            logger.info("Creating fingerprint tables")
            # In production, use proper database migrations
    
    async def _load_known_patterns(self):
        """Load known WiFi/BLE patterns for major brands and venues"""
        
        # Known WiFi SSID patterns for major brands
        self.wifi_patterns = {
            # Coffee shops
            'starbucks': {
                'patterns': [r'starbucks', r'sbux', r'google\s*starbucks'],
                'mcc': '5812',
                'confidence': 0.9,
                'category': 'coffee_shop'
            },
            'dunkin': {
                'patterns': [r'dunkin', r'dd\s*guest', r'dunkin.*wifi'],
                'mcc': '5812',
                'confidence': 0.85,
                'category': 'coffee_shop'
            },
            
            # Fast food
            'mcdonalds': {
                'patterns': [r'mcdonald', r'mcd\s*wifi', r'mcwifi'],
                'mcc': '5814',
                'confidence': 0.9,
                'category': 'fast_food'
            },
            'subway': {
                'patterns': [r'subway.*wifi', r'subwayeats'],
                'mcc': '5814',
                'confidence': 0.85,
                'category': 'fast_food'
            },
            
            # Retail
            'target': {
                'patterns': [r'target.*guest', r'targetwifi'],
                'mcc': '5311',
                'confidence': 0.9,
                'category': 'department_store'
            },
            'walmart': {
                'patterns': [r'walmart.*wifi', r'walmartguest'],
                'mcc': '5311',
                'confidence': 0.9,
                'category': 'department_store'
            },
            'apple': {
                'patterns': [r'apple\s*store', r'apple.*wifi'],
                'mcc': '5732',
                'confidence': 0.95,
                'category': 'electronics'
            },
            
            # Gas stations
            'shell': {
                'patterns': [r'shell.*wifi', r'shell.*guest'],
                'mcc': '5541',
                'confidence': 0.9,
                'category': 'gas_station'
            },
            'exxon': {
                'patterns': [r'exxon', r'mobil.*wifi'],
                'mcc': '5541',
                'confidence': 0.9,
                'category': 'gas_station'
            },
            
            # Hotels
            'marriott': {
                'patterns': [r'marriott', r'courtyard.*wifi'],
                'mcc': '7011',
                'confidence': 0.85,
                'category': 'hotel'
            },
            'hilton': {
                'patterns': [r'hilton.*wifi', r'hampton.*inn'],
                'mcc': '7011',
                'confidence': 0.85,
                'category': 'hotel'
            },
            
            # Banks
            'chase': {
                'patterns': [r'chase.*wifi', r'jpmorgan'],
                'mcc': '6011',
                'confidence': 0.9,
                'category': 'bank'
            },
            'wellsfargo': {
                'patterns': [r'wells.*fargo', r'wf.*wifi'],
                'mcc': '6011',
                'confidence': 0.9,
                'category': 'bank'
            }
        }
        
        # Known BLE beacon patterns
        self.ble_patterns = {
            # iBeacon UUIDs for major retailers
            'apple_stores': {
                'uuid_patterns': ['e2c56db5-dffb-48d2-b060-d0f5a71096e0'],
                'mcc': '5732',
                'confidence': 0.95,
                'category': 'electronics'
            },
            'target_beacons': {
                'uuid_patterns': ['f7826da6-4fa2-4e98-8024-bc5b71e0893e'],
                'mcc': '5311',
                'confidence': 0.9,
                'category': 'department_store'
            },
            'macy_beacons': {
                'uuid_patterns': ['b9407f30-f5f8-466e-aff9-25556b57fe6d'],
                'mcc': '5311',
                'confidence': 0.85,
                'category': 'department_store'
            },
            
            # Generic retail beacons
            'retail_generic': {
                'uuid_patterns': [
                    '6c9d5b8d-e3d2-4e8e-8b9f-1c2d3e4f5a6b',  # Common retail UUID
                    'f1826da6-4fa2-4e98-8024-bc5b71e0893e'
                ],
                'mcc': '5999',
                'confidence': 0.6,
                'category': 'retail'
            }
        }
    
    async def analyze_wifi_fingerprint(self, wifi_data: List[Dict[str, Any]], 
                                     location_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze WiFi fingerprint data for MCC prediction
        
        Args:
            wifi_data: List of WiFi networks with SSID, BSSID, signal strength
            location_data: Optional location context
        
        Returns:
            Analysis results with MCC prediction
        """
        try:
            if not wifi_data:
                return self._get_empty_wifi_result()
            
            # Extract WiFi features
            wifi_features = self._extract_wifi_features(wifi_data)
            
            # Brand detection
            brand_detection = await self._detect_brand_from_wifi(wifi_data)
            
            # Venue fingerprint matching
            venue_match = await self._match_venue_fingerprint(wifi_features, 'wifi')
            
            # Signal pattern analysis
            pattern_analysis = self._analyze_wifi_patterns(wifi_data)
            
            # Historical fingerprint lookup
            historical_match = await self._lookup_historical_wifi_fingerprint(wifi_features)
            
            # Combine all analyses
            combined_result = self._combine_wifi_analyses(
                brand_detection, venue_match, pattern_analysis, historical_match, wifi_features
            )
            
            # Store fingerprint for future use
            await self._store_wifi_fingerprint(wifi_features, combined_result)
            
            return combined_result
            
        except Exception as e:
            logger.error(f"Error analyzing WiFi fingerprint: {str(e)}")
            return self._get_empty_wifi_result()
    
    async def analyze_ble_fingerprint(self, ble_data: List[Dict[str, Any]], 
                                    location_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze BLE fingerprint data for MCC prediction
        
        Args:
            ble_data: List of BLE beacons with UUID, major, minor, RSSI
            location_data: Optional location context
        
        Returns:
            Analysis results with MCC prediction
        """
        try:
            if not ble_data:
                return self._get_empty_ble_result()
            
            # Extract BLE features
            ble_features = self._extract_ble_features(ble_data)
            
            # Brand/beacon detection
            beacon_detection = await self._detect_brand_from_ble(ble_data)
            
            # Venue fingerprint matching
            venue_match = await self._match_venue_fingerprint(ble_features, 'ble')
            
            # Proximity analysis
            proximity_analysis = self._analyze_ble_proximity(ble_data)
            
            # Historical fingerprint lookup
            historical_match = await self._lookup_historical_ble_fingerprint(ble_features)
            
            # Combine all analyses
            combined_result = self._combine_ble_analyses(
                beacon_detection, venue_match, proximity_analysis, historical_match, ble_features
            )
            
            # Store fingerprint for future use
            await self._store_ble_fingerprint(ble_features, combined_result)
            
            return combined_result
            
        except Exception as e:
            logger.error(f"Error analyzing BLE fingerprint: {str(e)}")
            return self._get_empty_ble_result()
    
    def _extract_wifi_features(self, wifi_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract features from WiFi data for fingerprinting"""
        
        ssids = []
        bssids = []
        signal_strengths = []
        frequencies = []
        
        for wifi in wifi_data:
            ssid = wifi.get('ssid', '').lower().strip()
            bssid = wifi.get('bssid', '').lower()
            rssi = wifi.get('rssi', wifi.get('signal_strength', -100))
            frequency = wifi.get('frequency', 2400)  # Default to 2.4GHz
            
            if ssid:  # Only include networks with SSIDs
                ssids.append(ssid)
                bssids.append(bssid)
                signal_strengths.append(rssi)
                frequencies.append(frequency)
        
        # Calculate fingerprint hash
        fingerprint_data = '|'.join(sorted(ssids)) + '|' + '|'.join(sorted(bssids))
        fingerprint_hash = hashlib.md5(fingerprint_data.encode()).hexdigest()
        
        return {
            'ssids': ssids,
            'bssids': bssids,
            'signal_strengths': signal_strengths,
            'frequencies': frequencies,
            'network_count': len(ssids),
            'avg_signal_strength': sum(signal_strengths) / len(signal_strengths) if signal_strengths else -100,
            'max_signal_strength': max(signal_strengths) if signal_strengths else -100,
            'fingerprint_hash': fingerprint_hash,
            'unique_vendors': self._extract_wifi_vendors(bssids),
            'frequency_bands': self._analyze_frequency_bands(frequencies)
        }
    
    def _extract_ble_features(self, ble_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract features from BLE data for fingerprinting"""
        
        uuids = []
        majors = []
        minors = []
        rssi_values = []
        device_names = []
        
        for beacon in ble_data:
            uuid = beacon.get('uuid', '').lower()
            major = beacon.get('major', 0)
            minor = beacon.get('minor', 0)
            rssi = beacon.get('rssi', -100)
            name = beacon.get('name', '').lower()
            
            uuids.append(uuid)
            majors.append(major)
            minors.append(minor)
            rssi_values.append(rssi)
            if name:
                device_names.append(name)
        
        # Calculate fingerprint hash
        fingerprint_data = '|'.join(sorted(uuids)) + '|' + '|'.join(map(str, sorted(majors + minors)))
        fingerprint_hash = hashlib.md5(fingerprint_data.encode()).hexdigest()
        
        return {
            'uuids': uuids,
            'majors': majors,
            'minors': minors,
            'rssi_values': rssi_values,
            'device_names': device_names,
            'beacon_count': len(uuids),
            'avg_rssi': sum(rssi_values) / len(rssi_values) if rssi_values else -100,
            'max_rssi': max(rssi_values) if rssi_values else -100,
            'fingerprint_hash': fingerprint_hash,
            'unique_uuids': len(set(uuids)),
            'proximity_zones': self._calculate_proximity_zones(rssi_values)
        }
    
    async def _detect_brand_from_wifi(self, wifi_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect specific brands from WiFi SSID patterns"""
        
        detected_brands = []
        confidence_scores = []
        
        for wifi in wifi_data:
            ssid = wifi.get('ssid', '').lower()
            
            for brand, pattern_info in self.wifi_patterns.items():
                for pattern in pattern_info['patterns']:
                    if re.search(pattern, ssid, re.IGNORECASE):
                        signal_strength = wifi.get('rssi', wifi.get('signal_strength', -100))
                        
                        # Adjust confidence based on signal strength
                        base_confidence = pattern_info['confidence']
                        signal_factor = min(1.0, max(0.3, (signal_strength + 100) / 50))  # -100 to -50 dBm range
                        adjusted_confidence = base_confidence * signal_factor
                        
                        detected_brands.append({
                            'brand': brand,
                            'mcc': pattern_info['mcc'],
                            'category': pattern_info['category'],
                            'confidence': adjusted_confidence,
                            'ssid': wifi.get('ssid', ''),
                            'signal_strength': signal_strength,
                            'pattern_matched': pattern
                        })
                        break
        
        if detected_brands:
            # Return the highest confidence brand
            best_brand = max(detected_brands, key=lambda x: x['confidence'])
            return {
                'detected': True,
                'brand': best_brand['brand'],
                'mcc': best_brand['mcc'],
                'confidence': best_brand['confidence'],
                'category': best_brand['category'],
                'all_detections': detected_brands
            }
        
        return {'detected': False, 'confidence': 0.0}
    
    async def _detect_brand_from_ble(self, ble_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect specific brands from BLE beacon UUIDs"""
        
        detected_beacons = []
        
        for beacon in ble_data:
            uuid = beacon.get('uuid', '').lower()
            rssi = beacon.get('rssi', -100)
            
            for brand, pattern_info in self.ble_patterns.items():
                if uuid in pattern_info['uuid_patterns']:
                    # Adjust confidence based on signal strength
                    base_confidence = pattern_info['confidence']
                    signal_factor = min(1.0, max(0.3, (rssi + 100) / 50))
                    adjusted_confidence = base_confidence * signal_factor
                    
                    detected_beacons.append({
                        'brand': brand,
                        'mcc': pattern_info['mcc'],
                        'category': pattern_info['category'],
                        'confidence': adjusted_confidence,
                        'uuid': uuid,
                        'rssi': rssi,
                        'major': beacon.get('major', 0),
                        'minor': beacon.get('minor', 0)
                    })
        
        if detected_beacons:
            # Return the highest confidence beacon
            best_beacon = max(detected_beacons, key=lambda x: x['confidence'])
            return {
                'detected': True,
                'brand': best_beacon['brand'],
                'mcc': best_beacon['mcc'],
                'confidence': best_beacon['confidence'],
                'category': best_beacon['category'],
                'all_detections': detected_beacons
            }
        
        return {'detected': False, 'confidence': 0.0}
    
    async def _match_venue_fingerprint(self, features: Dict[str, Any], fingerprint_type: str) -> Dict[str, Any]:
        """Match fingerprint against known venue signatures"""
        try:
            if not self.supabase:
                return {'matched': False, 'confidence': 0.0}
            
            fingerprint_hash = features['fingerprint_hash']
            
            # Query database for similar fingerprints
            table_name = f'{fingerprint_type}_fingerprints'
            result = self.supabase.client.table(table_name).select(
                'fingerprint_hash, mcc, confidence, venue_name, location_hash'
            ).execute()
            
            if not result.data:
                return {'matched': False, 'confidence': 0.0}
            
            # Find exact or similar matches
            exact_matches = [fp for fp in result.data if fp['fingerprint_hash'] == fingerprint_hash]
            
            if exact_matches:
                # Return the most confident exact match
                best_match = max(exact_matches, key=lambda x: x['confidence'])
                return {
                    'matched': True,
                    'mcc': best_match['mcc'],
                    'confidence': min(0.95, best_match['confidence'] + 0.1),  # Boost for exact match
                    'venue_name': best_match.get('venue_name', 'Unknown'),
                    'match_type': 'exact'
                }
            
            # Look for partial matches (similar fingerprints)
            similarity_matches = await self._find_similar_fingerprints(features, result.data, fingerprint_type)
            
            if similarity_matches:
                best_match = max(similarity_matches, key=lambda x: x['similarity_score'])
                if best_match['similarity_score'] > 0.7:  # Threshold for acceptable similarity
                    return {
                        'matched': True,
                        'mcc': best_match['mcc'],
                        'confidence': best_match['confidence'] * best_match['similarity_score'],
                        'venue_name': best_match.get('venue_name', 'Unknown'),
                        'match_type': 'similar',
                        'similarity_score': best_match['similarity_score']
                    }
            
        except Exception as e:
            logger.error(f"Error matching venue fingerprint: {str(e)}")
        
        return {'matched': False, 'confidence': 0.0}
    
    async def _find_similar_fingerprints(self, features: Dict[str, Any], 
                                       stored_fingerprints: List[Dict], 
                                       fingerprint_type: str) -> List[Dict]:
        """Find fingerprints similar to the current one"""
        
        similar_matches = []
        
        for stored_fp in stored_fingerprints:
            similarity_score = 0.0
            
            if fingerprint_type == 'wifi':
                # Compare WiFi features
                stored_features = json.loads(stored_fp.get('features', '{}'))
                similarity_score = self._calculate_wifi_similarity(features, stored_features)
            elif fingerprint_type == 'ble':
                # Compare BLE features
                stored_features = json.loads(stored_fp.get('features', '{}'))
                similarity_score = self._calculate_ble_similarity(features, stored_features)
            
            if similarity_score > 0.5:  # Minimum similarity threshold
                similar_matches.append({
                    'mcc': stored_fp['mcc'],
                    'confidence': stored_fp['confidence'],
                    'venue_name': stored_fp.get('venue_name', 'Unknown'),
                    'similarity_score': similarity_score
                })
        
        return similar_matches
    
    def _calculate_wifi_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity between two WiFi fingerprints"""
        
        ssids1 = set(features1.get('ssids', []))
        ssids2 = set(features2.get('ssids', []))
        
        bssids1 = set(features1.get('bssids', []))
        bssids2 = set(features2.get('bssids', []))
        
        # Calculate Jaccard similarity for SSIDs and BSSIDs
        ssid_similarity = len(ssids1 & ssids2) / len(ssids1 | ssids2) if ssids1 | ssids2 else 0
        bssid_similarity = len(bssids1 & bssids2) / len(bssids1 | bssids2) if bssids1 | bssids2 else 0
        
        # Weight BSSID similarity higher (more unique than SSIDs)
        overall_similarity = (ssid_similarity * 0.3) + (bssid_similarity * 0.7)
        
        return overall_similarity
    
    def _calculate_ble_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity between two BLE fingerprints"""
        
        uuids1 = set(features1.get('uuids', []))
        uuids2 = set(features2.get('uuids', []))
        
        # UUIDs are highly unique, so weight them heavily
        uuid_similarity = len(uuids1 & uuids2) / len(uuids1 | uuids2) if uuids1 | uuids2 else 0
        
        # Also consider major/minor value similarities for iBeacons
        majors1 = set(features1.get('majors', []))
        majors2 = set(features2.get('majors', []))
        major_similarity = len(majors1 & majors2) / len(majors1 | majors2) if majors1 | majors2 else 0
        
        overall_similarity = (uuid_similarity * 0.8) + (major_similarity * 0.2)
        
        return overall_similarity
    
    def _analyze_wifi_patterns(self, wifi_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze WiFi signal patterns for business type prediction"""
        
        analysis = {
            'network_density': len(wifi_data),
            'signal_distribution': {},
            'frequency_analysis': {},
            'business_indicators': {}
        }
        
        if not wifi_data:
            return analysis
        
        # Analyze signal strength distribution
        signal_strengths = [w.get('rssi', w.get('signal_strength', -100)) for w in wifi_data]
        analysis['signal_distribution'] = {
            'avg_strength': sum(signal_strengths) / len(signal_strengths),
            'max_strength': max(signal_strengths),
            'min_strength': min(signal_strengths),
            'strong_signals': len([s for s in signal_strengths if s > -50]),  # Very strong
            'weak_signals': len([s for s in signal_strengths if s < -80])     # Weak
        }
        
        # Analyze network names for business patterns
        ssids = [w.get('ssid', '').lower() for w in wifi_data if w.get('ssid')]
        
        business_keywords = {
            'guest': ['guest', 'visitor', 'free', 'public'],
            'retail': ['store', 'shop', 'mall', 'retail'],
            'food': ['restaurant', 'cafe', 'coffee', 'food', 'dining'],
            'corporate': ['corp', 'office', 'business', 'company'],
            'hotel': ['hotel', 'inn', 'lodge', 'resort', 'guest']
        }
        
        for category, keywords in business_keywords.items():
            count = sum(1 for ssid in ssids if any(kw in ssid for kw in keywords))
            analysis['business_indicators'][category] = count / len(ssids) if ssids else 0
        
        return analysis
    
    def _analyze_ble_proximity(self, ble_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze BLE proximity and beacon deployment patterns"""
        
        analysis = {
            'beacon_count': len(ble_data),
            'proximity_zones': {},
            'uuid_diversity': 0,
            'deployment_pattern': 'unknown'
        }
        
        if not ble_data:
            return analysis
        
        # Analyze RSSI distribution for proximity zones
        rssi_values = [b.get('rssi', -100) for b in ble_data]
        
        immediate = len([r for r in rssi_values if r > -50])    # Very close
        near = len([r for r in rssi_values if -70 <= r <= -50]) # Near
        far = len([r for r in rssi_values if r < -70])          # Far
        
        analysis['proximity_zones'] = {
            'immediate': immediate,
            'near': near,
            'far': far
        }
        
        # Analyze UUID diversity
        uuids = [b.get('uuid', '') for b in ble_data if b.get('uuid')]
        analysis['uuid_diversity'] = len(set(uuids))
        
        # Determine deployment pattern
        if len(ble_data) >= 5 and analysis['uuid_diversity'] <= 2:
            analysis['deployment_pattern'] = 'retail_store'  # Many beacons, few UUIDs
        elif len(ble_data) >= 3 and immediate >= 2:
            analysis['deployment_pattern'] = 'point_of_sale'  # Close beacons
        elif analysis['uuid_diversity'] == len(ble_data):
            analysis['deployment_pattern'] = 'mixed_area'     # Different services
        
        return analysis
    
    async def _lookup_historical_wifi_fingerprint(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Look up historical WiFi fingerprint data"""
        try:
            if not self.supabase:
                return {'found': False, 'confidence': 0.0}
            
            fingerprint_hash = features['fingerprint_hash']
            
            # Query historical data
            result = self.supabase.client.table('wifi_fingerprints').select(
                'mcc, confidence, created_at, transaction_count'
            ).eq('fingerprint_hash', fingerprint_hash).execute()
            
            if result.data:
                # Calculate weighted confidence based on historical success
                historical_entries = result.data
                total_transactions = sum(entry.get('transaction_count', 1) for entry in historical_entries)
                
                if total_transactions >= 3:  # Minimum threshold for reliability
                    # Weight by transaction count
                    weighted_mcc_scores = defaultdict(float)
                    for entry in historical_entries:
                        mcc = entry['mcc']
                        confidence = entry['confidence']
                        count = entry.get('transaction_count', 1)
                        weighted_mcc_scores[mcc] += confidence * count
                    
                    best_mcc = max(weighted_mcc_scores, key=weighted_mcc_scores.get)
                    historical_confidence = min(0.9, weighted_mcc_scores[best_mcc] / total_transactions)
                    
                    return {
                        'found': True,
                        'mcc': best_mcc,
                        'confidence': historical_confidence,
                        'transaction_count': total_transactions
                    }
        
        except Exception as e:
            logger.error(f"Error looking up historical WiFi fingerprint: {str(e)}")
        
        return {'found': False, 'confidence': 0.0}
    
    async def _lookup_historical_ble_fingerprint(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Look up historical BLE fingerprint data"""
        try:
            if not self.supabase:
                return {'found': False, 'confidence': 0.0}
            
            fingerprint_hash = features['fingerprint_hash']
            
            # Query historical data
            result = self.supabase.client.table('ble_fingerprints').select(
                'mcc, confidence, created_at, transaction_count'
            ).eq('fingerprint_hash', fingerprint_hash).execute()
            
            if result.data:
                historical_entries = result.data
                total_transactions = sum(entry.get('transaction_count', 1) for entry in historical_entries)
                
                if total_transactions >= 2:  # Lower threshold for BLE (less common)
                    weighted_mcc_scores = defaultdict(float)
                    for entry in historical_entries:
                        mcc = entry['mcc']
                        confidence = entry['confidence']
                        count = entry.get('transaction_count', 1)
                        weighted_mcc_scores[mcc] += confidence * count
                    
                    best_mcc = max(weighted_mcc_scores, key=weighted_mcc_scores.get)
                    historical_confidence = min(0.85, weighted_mcc_scores[best_mcc] / total_transactions)
                    
                    return {
                        'found': True,
                        'mcc': best_mcc,
                        'confidence': historical_confidence,
                        'transaction_count': total_transactions
                    }
        
        except Exception as e:
            logger.error(f"Error looking up historical BLE fingerprint: {str(e)}")
        
        return {'found': False, 'confidence': 0.0}
    
    def _combine_wifi_analyses(self, brand_detection: Dict, venue_match: Dict, 
                             pattern_analysis: Dict, historical_match: Dict, 
                             features: Dict) -> Dict[str, Any]:
        """Combine all WiFi analysis results"""
        
        predictions = []
        
        # Brand detection (highest priority)
        if brand_detection.get('detected', False):
            predictions.append({
                'mcc': brand_detection['mcc'],
                'confidence': brand_detection['confidence'],
                'method': 'wifi_brand_detection',
                'source': 'brand_patterns'
            })
        
        # Historical fingerprint match
        if historical_match.get('found', False):
            predictions.append({
                'mcc': historical_match['mcc'],
                'confidence': historical_match['confidence'],
                'method': 'wifi_historical_match',
                'source': 'historical_data'
            })
        
        # Venue fingerprint match
        if venue_match.get('matched', False):
            predictions.append({
                'mcc': venue_match['mcc'],
                'confidence': venue_match['confidence'],
                'method': 'wifi_venue_match',
                'source': 'venue_fingerprints'
            })
        
        # Pattern-based inference
        business_indicators = pattern_analysis.get('business_indicators', {})
        if business_indicators:
            pattern_mcc = self._infer_mcc_from_wifi_patterns(business_indicators)
            if pattern_mcc:
                predictions.append(pattern_mcc)
        
        # Select best prediction
        if predictions:
            best_prediction = max(predictions, key=lambda x: x['confidence'])
            return {
                'predicted': True,
                'mcc': best_prediction['mcc'],
                'confidence': best_prediction['confidence'],
                'method': best_prediction['method'],
                'all_predictions': predictions,
                'fingerprint_features': features,
                'analysis_details': {
                    'brand_detection': brand_detection,
                    'venue_match': venue_match,
                    'pattern_analysis': pattern_analysis,
                    'historical_match': historical_match
                }
            }
        
        # No predictions found
        return {
            'predicted': False,
            'confidence': 0.0,
            'fingerprint_features': features,
            'analysis_details': {
                'brand_detection': brand_detection,
                'venue_match': venue_match,
                'pattern_analysis': pattern_analysis,
                'historical_match': historical_match
            }
        }
    
    def _combine_ble_analyses(self, beacon_detection: Dict, venue_match: Dict, 
                            proximity_analysis: Dict, historical_match: Dict, 
                            features: Dict) -> Dict[str, Any]:
        """Combine all BLE analysis results"""
        
        predictions = []
        
        # Beacon/brand detection (highest priority)
        if beacon_detection.get('detected', False):
            predictions.append({
                'mcc': beacon_detection['mcc'],
                'confidence': beacon_detection['confidence'],
                'method': 'ble_beacon_detection',
                'source': 'beacon_patterns'
            })
        
        # Historical fingerprint match
        if historical_match.get('found', False):
            predictions.append({
                'mcc': historical_match['mcc'],
                'confidence': historical_match['confidence'],
                'method': 'ble_historical_match',
                'source': 'historical_data'
            })
        
        # Venue fingerprint match
        if venue_match.get('matched', False):
            predictions.append({
                'mcc': venue_match['mcc'],
                'confidence': venue_match['confidence'],
                'method': 'ble_venue_match',
                'source': 'venue_fingerprints'
            })
        
        # Proximity-based inference
        deployment_pattern = proximity_analysis.get('deployment_pattern', 'unknown')
        if deployment_pattern != 'unknown':
            pattern_mcc = self._infer_mcc_from_ble_deployment(deployment_pattern)
            if pattern_mcc:
                predictions.append(pattern_mcc)
        
        # Select best prediction
        if predictions:
            best_prediction = max(predictions, key=lambda x: x['confidence'])
            return {
                'predicted': True,
                'mcc': best_prediction['mcc'],
                'confidence': best_prediction['confidence'],
                'method': best_prediction['method'],
                'all_predictions': predictions,
                'fingerprint_features': features,
                'analysis_details': {
                    'beacon_detection': beacon_detection,
                    'venue_match': venue_match,
                    'proximity_analysis': proximity_analysis,
                    'historical_match': historical_match
                }
            }
        
        # No predictions found
        return {
            'predicted': False,
            'confidence': 0.0,
            'fingerprint_features': features,
            'analysis_details': {
                'beacon_detection': beacon_detection,
                'venue_match': venue_match,
                'proximity_analysis': proximity_analysis,
                'historical_match': historical_match
            }
        }
    
    def _infer_mcc_from_wifi_patterns(self, business_indicators: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """Infer MCC from WiFi pattern analysis"""
        
        pattern_mappings = {
            'food': {'mcc': '5812', 'confidence': 0.6},
            'retail': {'mcc': '5999', 'confidence': 0.5},
            'hotel': {'mcc': '7011', 'confidence': 0.7},
            'corporate': {'mcc': '7399', 'confidence': 0.4}  # Business services
        }
        
        for pattern, score in business_indicators.items():
            if score > 0.3 and pattern in pattern_mappings:  # Threshold for pattern significance
                mapping = pattern_mappings[pattern]
                return {
                    'mcc': mapping['mcc'],
                    'confidence': mapping['confidence'] * score,
                    'method': 'wifi_pattern_inference',
                    'source': 'pattern_analysis'
                }
        
        return None
    
    def _infer_mcc_from_ble_deployment(self, deployment_pattern: str) -> Optional[Dict[str, Any]]:
        """Infer MCC from BLE deployment pattern"""
        
        pattern_mappings = {
            'retail_store': {'mcc': '5999', 'confidence': 0.6},
            'point_of_sale': {'mcc': '5999', 'confidence': 0.7},
            'mixed_area': {'mcc': '5999', 'confidence': 0.4}
        }
        
        if deployment_pattern in pattern_mappings:
            mapping = pattern_mappings[deployment_pattern]
            return {
                'mcc': mapping['mcc'],
                'confidence': mapping['confidence'],
                'method': 'ble_deployment_inference',
                'source': 'proximity_analysis'
            }
        
        return None
    
    async def _store_wifi_fingerprint(self, features: Dict[str, Any], result: Dict[str, Any]):
        """Store WiFi fingerprint data for future reference"""
        try:
            if not self.supabase or not result.get('predicted', False):
                return
            
            self.supabase.client.table('wifi_fingerprints').upsert({
                'fingerprint_hash': features['fingerprint_hash'],
                'mcc': result['mcc'],
                'confidence': result['confidence'],
                'method': result['method'],
                'features': json.dumps(features),
                'created_at': datetime.now().isoformat(),
                'transaction_count': 1
            }).execute()
            
        except Exception as e:
            logger.error(f"Error storing WiFi fingerprint: {str(e)}")
    
    async def _store_ble_fingerprint(self, features: Dict[str, Any], result: Dict[str, Any]):
        """Store BLE fingerprint data for future reference"""
        try:
            if not self.supabase or not result.get('predicted', False):
                return
            
            self.supabase.client.table('ble_fingerprints').upsert({
                'fingerprint_hash': features['fingerprint_hash'],
                'mcc': result['mcc'],
                'confidence': result['confidence'],
                'method': result['method'],
                'features': json.dumps(features),
                'created_at': datetime.now().isoformat(),
                'transaction_count': 1
            }).execute()
            
        except Exception as e:
            logger.error(f"Error storing BLE fingerprint: {str(e)}")
    
    def _extract_wifi_vendors(self, bssids: List[str]) -> List[str]:
        """Extract WiFi vendor information from BSSIDs (MAC addresses)"""
        # This would typically use an OUI database lookup
        # For now, return a simplified vendor detection
        vendors = []
        for bssid in bssids:
            if bssid and len(bssid) >= 8:
                oui = bssid[:8].upper()
                # Sample OUI mappings (in production, use full OUI database)
                vendor_mapping = {
                    '00:50:56': 'VMware',
                    '00:1B:63': 'Apple',
                    '00:26:BB': 'Apple',
                    '00:23:DF': 'Apple',
                    '20:C9:D0': 'Apple',
                    '00:15:00': 'D-Link'
                }
                vendor = vendor_mapping.get(oui, 'Unknown')
                if vendor != 'Unknown':
                    vendors.append(vendor)
        return list(set(vendors))
    
    def _analyze_frequency_bands(self, frequencies: List[int]) -> Dict[str, int]:
        """Analyze WiFi frequency band distribution"""
        bands = {'2.4GHz': 0, '5GHz': 0, 'other': 0}
        
        for freq in frequencies:
            if 2400 <= freq <= 2500:
                bands['2.4GHz'] += 1
            elif 5000 <= freq <= 6000:
                bands['5GHz'] += 1
            else:
                bands['other'] += 1
        
        return bands
    
    def _calculate_proximity_zones(self, rssi_values: List[int]) -> Dict[str, int]:
        """Calculate BLE proximity zones based on RSSI values"""
        zones = {'immediate': 0, 'near': 0, 'far': 0}
        
        for rssi in rssi_values:
            if rssi > -50:
                zones['immediate'] += 1
            elif -70 <= rssi <= -50:
                zones['near'] += 1
            else:
                zones['far'] += 1
        
        return zones
    
    def _get_empty_wifi_result(self) -> Dict[str, Any]:
        """Return empty WiFi analysis result"""
        return {
            'predicted': False,
            'confidence': 0.0,
            'method': 'wifi_fingerprint',
            'fingerprint_features': {},
            'analysis_details': {}
        }
    
    def _get_empty_ble_result(self) -> Dict[str, Any]:
        """Return empty BLE analysis result"""
        return {
            'predicted': False,
            'confidence': 0.0,
            'method': 'ble_fingerprint',
            'fingerprint_features': {},
            'analysis_details': {}
        } 