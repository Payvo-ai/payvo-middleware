"""
POS Terminal BLE Detection Service
Specialized service for detecting Point-of-Sale terminals via BLE signatures
and mapping them to accurate MCCs for enhanced payment routing
"""

import asyncio
import logging
import re
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json

from ..core.config import settings
from ..database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class POSTerminalService:
    """Enhanced POS terminal detection via BLE signatures"""
    
    def __init__(self):
        self.supabase = None
        self.pos_ble_signatures = {}
        self.learned_terminal_mappings = {}
        self.terminal_usage_patterns = {}
        self.confidence_threshold = 0.7
        
    async def initialize(self):
        """Initialize the POS terminal service"""
        try:
            self.supabase = get_supabase_client()
            await self._load_pos_signatures()
            await self._load_learned_mappings()
            logger.info("POS Terminal service initialized successfully")
        except Exception as e:
            logger.error(f"POS Terminal service initialization failed: {e}")
            self.supabase = None
    
    async def _load_pos_signatures(self):
        """Load known POS system BLE signatures"""
        
        # Industry-specific POS systems with high MCC confidence
        self.pos_ble_signatures = {
            # Restaurant-focused POS systems
            'toast_pos': {
                'ble_patterns': [
                    r'.*toast.*',
                    r'.*kitchen.*display.*',
                    r'.*toasttab.*',
                    r'toast.*terminal.*'
                ],
                'service_uuids': [
                    '180A',  # Device Information Service
                    '1800',  # Generic Access Service
                    'FE26'   # Toast proprietary UUID
                ],
                'manufacturer_data_patterns': ['0x004C'],  # Apple devices
                'industry_focus': 'restaurants_only',
                'mcc_candidates': ['5812'],  # Restaurant - very high confidence
                'confidence_boost': 0.18,
                'reasoning': 'Toast POS is exclusively for restaurants'
            },
            
            'resy_pos': {
                'ble_patterns': [
                    r'.*resy.*',
                    r'.*reservation.*terminal.*',
                    r'resy.*pos.*'
                ],
                'service_uuids': ['180A', '1800'],
                'manufacturer_data_patterns': ['0x004C'],
                'industry_focus': 'restaurants_only',
                'mcc_candidates': ['5812'],
                'confidence_boost': 0.16,
                'reasoning': 'Resy POS is restaurant reservation + POS'
            },
            
            'lightspeed_restaurant': {
                'ble_patterns': [
                    r'.*lightspeed.*restaurant.*',
                    r'.*ls.*resto.*',
                    r'lightspeed.*r.*'
                ],
                'service_uuids': ['180A', '1800', 'FE28'],
                'manufacturer_data_patterns': ['0x004C', '0x0059'],
                'industry_focus': 'restaurants_bars',
                'mcc_candidates': ['5812', '5813'],
                'confidence_boost': 0.15,
                'reasoning': 'Lightspeed Restaurant is hospitality-focused'
            },
            
            # Gas station POS systems
            'verifone_gas': {
                'ble_patterns': [
                    r'.*verifone.*',
                    r'.*vx.*terminal.*',
                    r'.*pump.*display.*',
                    r'verifone.*pos.*'
                ],
                'service_uuids': ['180A', '1800', 'FE29'],
                'manufacturer_data_patterns': ['0x0075'],  # Verifone manufacturer ID
                'industry_focus': 'gas_stations',
                'mcc_candidates': ['5541'],
                'confidence_boost': 0.17,
                'reasoning': 'Verifone dominates gas station payment market'
            },
            
            'gilbarco_pos': {
                'ble_patterns': [
                    r'.*gilbarco.*',
                    r'.*encore.*',
                    r'.*fuel.*pos.*'
                ],
                'service_uuids': ['180A', '1800'],
                'manufacturer_data_patterns': ['0x0076'],
                'industry_focus': 'gas_stations',
                'mcc_candidates': ['5541'],
                'confidence_boost': 0.16,
                'reasoning': 'Gilbarco specializes in fuel dispensing systems'
            },
            
            # General retail POS systems
            'square_pos': {
                'ble_patterns': [
                    r'.*square.*terminal.*',
                    r'.*sq.*pos.*',
                    r'square.*reader.*',
                    r'.*square.*station.*'
                ],
                'service_uuids': ['180A', '1800', 'FE26'],
                'manufacturer_data_patterns': ['0x004C'],
                'industry_focus': 'retail_general',
                'mcc_candidates': ['5999', '5812', '5311', '5651'],
                'confidence_boost': 0.12,
                'reasoning': 'Square POS is versatile - use location context'
            },
            
            'clover_pos': {
                'ble_patterns': [
                    r'.*clover.*',
                    r'.*clv.*terminal.*',
                    r'clover.*station.*'
                ],
                'service_uuids': ['180A', '1800', 'FE27'],
                'manufacturer_data_patterns': ['0x0059'],  # First Data/Clover
                'industry_focus': 'restaurants_retail',
                'mcc_candidates': ['5812', '5999', '5311'],
                'confidence_boost': 0.13,
                'reasoning': 'Clover is popular in restaurants and retail'
            },
            
            'shopify_pos': {
                'ble_patterns': [
                    r'.*shopify.*pos.*',
                    r'.*shop.*terminal.*',
                    r'shopify.*reader.*'
                ],
                'service_uuids': ['180A', '1800'],
                'manufacturer_data_patterns': ['0x004C'],
                'industry_focus': 'retail_general',
                'mcc_candidates': ['5999', '5311', '5651'],
                'confidence_boost': 0.11,
                'reasoning': 'Shopify POS is general retail focused'
            },
            
            # Kitchen display systems (strong restaurant indicators)
            'kitchen_display_systems': {
                'ble_patterns': [
                    r'.*kitchen.*display.*',
                    r'.*kds.*',
                    r'.*order.*display.*',
                    r'.*expo.*screen.*'
                ],
                'service_uuids': ['180A', '1800'],
                'manufacturer_data_patterns': ['0x004C', '0x0059'],
                'industry_focus': 'restaurants_only',
                'mcc_candidates': ['5812'],
                'confidence_boost': 0.20,
                'reasoning': 'Kitchen display systems are restaurant-exclusive'
            },
            
            # Payment terminals (context-dependent)
            'ingenico_terminals': {
                'ble_patterns': [
                    r'.*ingenico.*',
                    r'.*ing.*terminal.*',
                    r'.*payment.*terminal.*'
                ],
                'service_uuids': ['180A', '1800', 'FE30'],
                'manufacturer_data_patterns': ['0x0077'],
                'industry_focus': 'general_payment',
                'mcc_candidates': ['5999'],  # Requires context
                'confidence_boost': 0.08,
                'reasoning': 'Generic payment terminal - needs location context'
            }
        }
    
    async def _load_learned_mappings(self):
        """Load previously learned terminal-to-MCC mappings"""
        try:
            if not self.supabase or not self.supabase.is_available:
                return
            
            # Load learned mappings from database
            result = self.supabase.client.table('pos_terminal_mappings').select(
                'ble_signature, mcc, confidence, confirmation_count, first_seen'
            ).execute()
            
            if result.data:
                for mapping in result.data:
                    self.learned_terminal_mappings[mapping['ble_signature']] = {
                        'mcc': mapping['mcc'],
                        'confidence': mapping['confidence'],
                        'confirmation_count': mapping['confirmation_count'],
                        'first_seen': mapping['first_seen']
                    }
                
                logger.info(f"Loaded {len(self.learned_terminal_mappings)} learned terminal mappings")
        
        except Exception as e:
            logger.error(f"Error loading learned terminal mappings: {e}")
    
    async def detect_pos_terminals(self, ble_data: List[Dict[str, Any]], 
                                 location_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main method to detect POS terminals from BLE data
        
        Args:
            ble_data: List of BLE devices with name, uuid, rssi, etc.
            location_data: Optional location context for disambiguation
            
        Returns:
            POS detection results with MCC predictions
        """
        try:
            if not ble_data:
                return self._get_empty_pos_result()
            
            # Step 1: Check learned mappings first (highest confidence)
            learned_result = await self._check_learned_mappings(ble_data)
            if learned_result and learned_result['confidence'] > 0.8:
                return learned_result
            
            # Step 2: Detect specialized POS systems
            specialized_result = await self._detect_specialized_pos_systems(ble_data)
            if specialized_result and specialized_result['confidence'] > 0.7:
                return specialized_result
            
            # Step 3: Analyze multi-terminal business ecosystem
            ecosystem_result = await self._analyze_business_pos_ecosystem(ble_data, location_data)
            if ecosystem_result and ecosystem_result['confidence'] > 0.6:
                return ecosystem_result
            
            # Step 4: Use location context to disambiguate generic POS
            if location_data:
                context_result = await self._infer_pos_mcc_from_context(ble_data, location_data)
                if context_result:
                    return context_result
            
            # Step 5: Proximity-based analysis
            proximity_result = self._analyze_pos_proximity(ble_data)
            if proximity_result:
                return proximity_result
            
            return self._get_empty_pos_result()
            
        except Exception as e:
            logger.error(f"Error detecting POS terminals: {e}")
            return self._get_empty_pos_result()
    
    async def _check_learned_mappings(self, ble_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Check if we have learned mappings for these BLE signatures"""
        
        for device in ble_data:
            signature = self._create_ble_signature(device)
            
            if signature in self.learned_terminal_mappings:
                mapping = self.learned_terminal_mappings[signature]
                
                # Adjust confidence based on confirmation count
                base_confidence = mapping['confidence']
                confirmation_factor = min(1.0, mapping['confirmation_count'] * 0.1)
                adjusted_confidence = min(0.95, base_confidence * confirmation_factor)
                
                if adjusted_confidence >= self.confidence_threshold:
                    return {
                        'detected': True,
                        'pos_type': 'learned_mapping',
                        'mcc': mapping['mcc'],
                        'confidence': adjusted_confidence,
                        'method': 'learned_terminal_mapping',
                        'reasoning': f"Previously learned mapping with {mapping['confirmation_count']} confirmations",
                        'device_info': device,
                        'metadata': {
                            'confirmations': mapping['confirmation_count'],
                            'first_seen': mapping['first_seen']
                        }
                    }
        
        return None
    
    async def _detect_specialized_pos_systems(self, ble_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Detect industry-specific POS systems with high MCC confidence"""
        
        detections = []
        
        for device in ble_data:
            device_name = device.get('name', '').lower()
            service_uuids = device.get('service_uuids', [])
            manufacturer_data = device.get('manufacturer_data', '')
            rssi = device.get('rssi', -100)
            
            # Check against known POS signatures
            for pos_type, signature in self.pos_ble_signatures.items():
                if self._matches_pos_signature(device, signature):
                    # Adjust confidence based on signal strength
                    base_confidence = signature['confidence_boost']
                    signal_factor = self._calculate_signal_factor(rssi)
                    adjusted_confidence = base_confidence + (0.6 * signal_factor)
                    
                    detections.append({
                        'pos_type': pos_type,
                        'confidence': adjusted_confidence,
                        'mcc_candidates': signature['mcc_candidates'],
                        'industry_focus': signature['industry_focus'],
                        'device_info': device,
                        'reasoning': signature['reasoning']
                    })
        
        if detections:
            # Return the highest confidence detection
            best_detection = max(detections, key=lambda x: x['confidence'])
            
            # Handle specialized systems (single MCC)
            if len(best_detection['mcc_candidates']) == 1:
                return {
                    'detected': True,
                    'pos_type': best_detection['pos_type'],
                    'mcc': best_detection['mcc_candidates'][0],
                    'confidence': best_detection['confidence'],
                    'method': 'specialized_pos_detection',
                    'reasoning': best_detection['reasoning'],
                    'device_info': best_detection['device_info'],
                    'all_detections': detections
                }
            else:
                # Multiple MCC candidates - need context
                return {
                    'detected': True,
                    'pos_type': best_detection['pos_type'],
                    'mcc_candidates': best_detection['mcc_candidates'],
                    'confidence': best_detection['confidence'],
                    'method': 'generic_pos_detection',
                    'reasoning': f"{best_detection['reasoning']} - requires context",
                    'device_info': best_detection['device_info'],
                    'needs_context': True
                }
        
        return None
    
    async def _analyze_business_pos_ecosystem(self, ble_data: List[Dict[str, Any]], 
                                           location_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze multiple POS terminals at location to infer business type"""
        
        pos_terminals = []
        
        # Identify all POS-related devices
        for device in ble_data:
            if self._is_pos_related_device(device):
                pos_terminals.append(device)
        
        if len(pos_terminals) < 2:
            return None
        
        # Analyze POS ecosystem patterns
        
        # Restaurant pattern: Kitchen display + POS + payment terminal
        kitchen_displays = [d for d in pos_terminals if self._is_kitchen_display(d)]
        payment_terminals = [d for d in pos_terminals if self._is_payment_terminal(d)]
        pos_stations = [d for d in pos_terminals if self._is_pos_station(d)]
        
        if kitchen_displays and (payment_terminals or pos_stations):
            return {
                'detected': True,
                'pos_type': 'restaurant_ecosystem',
                'mcc': '5812',
                'confidence': 0.88,
                'method': 'multi_terminal_restaurant_pattern',
                'reasoning': f'Detected {len(kitchen_displays)} kitchen displays + {len(payment_terminals + pos_stations)} terminals',
                'ecosystem_devices': pos_terminals,
                'device_breakdown': {
                    'kitchen_displays': len(kitchen_displays),
                    'payment_terminals': len(payment_terminals),
                    'pos_stations': len(pos_stations)
                }
            }
        
        # Retail pattern: Multiple checkout stations
        checkout_terminals = [d for d in pos_terminals if self._is_checkout_terminal(d)]
        
        if len(checkout_terminals) >= 3:
            # Large retail with multiple checkouts
            return {
                'detected': True,
                'pos_type': 'multi_checkout_retail',
                'mcc': '5311',  # Department store
                'confidence': 0.82,
                'method': 'multi_checkout_retail_pattern',
                'reasoning': f'Detected {len(checkout_terminals)} checkout stations',
                'ecosystem_devices': pos_terminals,
                'device_breakdown': {
                    'checkout_terminals': len(checkout_terminals)
                }
            }
        
        # Gas station pattern: Pump displays + payment terminals
        pump_displays = [d for d in pos_terminals if self._is_pump_display(d)]
        
        if pump_displays and payment_terminals:
            return {
                'detected': True,
                'pos_type': 'gas_station_ecosystem',
                'mcc': '5541',
                'confidence': 0.85,
                'method': 'gas_station_pattern',
                'reasoning': f'Detected {len(pump_displays)} pump displays + {len(payment_terminals)} payment terminals',
                'ecosystem_devices': pos_terminals,
                'device_breakdown': {
                    'pump_displays': len(pump_displays),
                    'payment_terminals': len(payment_terminals)
                }
            }
        
        return None
    
    async def _infer_pos_mcc_from_context(self, ble_data: List[Dict[str, Any]], 
                                        location_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Use location context to disambiguate generic POS systems"""
        
        # This would integrate with location service
        # For now, return basic logic
        
        generic_pos = self._find_generic_pos_terminals(ble_data)
        if not generic_pos:
            return None
        
        # Get location-based MCC hint (would call location service)
        location_mcc_hint = location_data.get('predicted_mcc') if location_data else None
        
        if location_mcc_hint:
            best_pos = max(generic_pos, key=lambda x: x.get('confidence', 0))
            
            return {
                'detected': True,
                'pos_type': best_pos['pos_type'],
                'mcc': location_mcc_hint,
                'confidence': best_pos['confidence'] + 0.15,  # Boost from context
                'method': 'pos_location_context',
                'reasoning': f'{best_pos["pos_type"]} detected with location context',
                'device_info': best_pos['device_info'],
                'location_context': location_data
            }
        
        return None
    
    def _analyze_pos_proximity(self, ble_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze proximity to POS terminals to determine transaction context"""
        
        pos_devices = []
        
        for device in ble_data:
            if self._is_pos_related_device(device):
                rssi = device.get('rssi', -100)
                pos_devices.append({
                    'device': device,
                    'rssi': rssi,
                    'proximity': self._calculate_proximity_zone(rssi)
                })
        
        if not pos_devices:
            return None
        
        # Check for immediate proximity (user at POS)
        immediate_pos = [d for d in pos_devices if d['proximity'] == 'immediate']
        
        if immediate_pos:
            closest_pos = max(immediate_pos, key=lambda x: x['rssi'])
            
            return {
                'detected': True,
                'pos_type': 'proximity_based',
                'mcc': '5999',  # Generic - needs more context
                'confidence': 0.65,
                'method': 'pos_proximity_analysis',
                'reasoning': f'User immediately adjacent to POS terminal (RSSI: {closest_pos["rssi"]})',
                'device_info': closest_pos['device'],
                'proximity_data': {
                    'immediate_count': len(immediate_pos),
                    'total_pos_count': len(pos_devices),
                    'closest_rssi': closest_pos['rssi']
                }
            }
        
        return None
    
    def _matches_pos_signature(self, device: Dict[str, Any], signature: Dict[str, Any]) -> bool:
        """Check if device matches POS signature patterns"""
        
        device_name = device.get('name', '').lower()
        service_uuids = device.get('service_uuids', [])
        manufacturer_data = device.get('manufacturer_data', '')
        
        # Check BLE name patterns
        for pattern in signature['ble_patterns']:
            if re.search(pattern, device_name, re.IGNORECASE):
                return True
        
        # Check service UUIDs
        if service_uuids:
            for uuid in signature['service_uuids']:
                if uuid.lower() in [u.lower() for u in service_uuids]:
                    return True
        
        # Check manufacturer data
        if manufacturer_data:
            for pattern in signature['manufacturer_data_patterns']:
                if pattern.lower() in manufacturer_data.lower():
                    return True
        
        return False
    
    def _is_pos_related_device(self, device: Dict[str, Any]) -> bool:
        """Check if device is POS-related"""
        
        device_name = device.get('name', '').lower()
        pos_keywords = [
            'pos', 'terminal', 'payment', 'checkout', 'register', 'square', 
            'clover', 'toast', 'kitchen', 'display', 'kds', 'verifone', 
            'ingenico', 'pump', 'fuel', 'station'
        ]
        
        return any(keyword in device_name for keyword in pos_keywords)
    
    def _is_kitchen_display(self, device: Dict[str, Any]) -> bool:
        """Check if device is a kitchen display system"""
        
        device_name = device.get('name', '').lower()
        kitchen_keywords = ['kitchen', 'kds', 'display', 'expo', 'order']
        
        return any(keyword in device_name for keyword in kitchen_keywords)
    
    def _is_payment_terminal(self, device: Dict[str, Any]) -> bool:
        """Check if device is a payment terminal"""
        
        device_name = device.get('name', '').lower()
        payment_keywords = ['payment', 'terminal', 'verifone', 'ingenico', 'card']
        
        return any(keyword in device_name for keyword in payment_keywords)
    
    def _is_pos_station(self, device: Dict[str, Any]) -> bool:
        """Check if device is a POS station"""
        
        device_name = device.get('name', '').lower()
        pos_keywords = ['pos', 'station', 'square', 'clover', 'toast', 'register']
        
        return any(keyword in device_name for keyword in pos_keywords)
    
    def _is_checkout_terminal(self, device: Dict[str, Any]) -> bool:
        """Check if device is a checkout terminal"""
        
        device_name = device.get('name', '').lower()
        checkout_keywords = ['checkout', 'register', 'lane', 'station']
        
        return any(keyword in device_name for keyword in checkout_keywords)
    
    def _is_pump_display(self, device: Dict[str, Any]) -> bool:
        """Check if device is a fuel pump display"""
        
        device_name = device.get('name', '').lower()
        pump_keywords = ['pump', 'fuel', 'gas', 'dispenser']
        
        return any(keyword in device_name for keyword in pump_keywords)
    
    def _find_generic_pos_terminals(self, ble_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find generic POS terminals that need context for MCC determination"""
        
        generic_terminals = []
        
        for device in ble_data:
            if self._is_pos_related_device(device):
                # Check if it's a generic/ambiguous POS system
                device_name = device.get('name', '').lower()
                
                if any(keyword in device_name for keyword in ['square', 'clover', 'shopify']):
                    generic_terminals.append({
                        'device_info': device,
                        'pos_type': 'generic_pos',
                        'confidence': 0.6
                    })
        
        return generic_terminals
    
    def _calculate_signal_factor(self, rssi: int) -> float:
        """Calculate signal strength factor for confidence adjustment"""
        
        if rssi > -50:  # Very close
            return 1.0
        elif rssi > -60:  # Close
            return 0.8
        elif rssi > -70:  # Medium
            return 0.6
        elif rssi > -80:  # Far
            return 0.4
        else:  # Very far
            return 0.2
    
    def _calculate_proximity_zone(self, rssi: int) -> str:
        """Calculate proximity zone based on RSSI"""
        
        if rssi > -50:
            return 'immediate'  # Within 3-5 meters
        elif rssi > -70:
            return 'near'       # Within 10-15 meters
        else:
            return 'far'        # Beyond 15 meters
    
    def _create_ble_signature(self, device: Dict[str, Any]) -> str:
        """Create a unique signature for BLE device"""
        
        name = device.get('name', '')
        uuid = device.get('uuid', '')
        major = device.get('major', 0)
        minor = device.get('minor', 0)
        
        signature_data = f"{name}|{uuid}|{major}|{minor}"
        return hashlib.md5(signature_data.encode()).hexdigest()[:16]
    
    def _get_empty_pos_result(self) -> Dict[str, Any]:
        """Return empty POS detection result"""
        
        return {
            'detected': False,
            'pos_type': None,
            'mcc': None,
            'confidence': 0.0,
            'method': 'no_pos_detected',
            'reasoning': 'No POS terminals detected in BLE data'
        }
    
    async def learn_from_transaction_feedback(self, ble_data: List[Dict[str, Any]], 
                                            actual_mcc: str, location_data: Optional[Dict[str, Any]] = None) -> None:
        """Learn from actual transaction outcomes to improve POS detection"""
        
        try:
            if not ble_data or not actual_mcc:
                return
            
            # Find POS-related devices in the transaction
            pos_devices = [d for d in ble_data if self._is_pos_related_device(d)]
            
            for device in pos_devices:
                signature = self._create_ble_signature(device)
                
                # Store or update learned mapping
                await self._store_learned_mapping(signature, actual_mcc, device, location_data)
        
        except Exception as e:
            logger.error(f"Error learning from transaction feedback: {e}")
    
    async def _store_learned_mapping(self, signature: str, mcc: str, 
                                   device: Dict[str, Any], location_data: Optional[Dict[str, Any]]) -> None:
        """Store learned terminal-to-MCC mapping"""
        
        try:
            if not self.supabase or not self.supabase.is_available:
                # Store in memory cache
                if signature in self.learned_terminal_mappings:
                    self.learned_terminal_mappings[signature]['confirmation_count'] += 1
                else:
                    self.learned_terminal_mappings[signature] = {
                        'mcc': mcc,
                        'confidence': 1.0,
                        'confirmation_count': 1,
                        'first_seen': datetime.now().isoformat()
                    }
                return
            
            # Check if mapping already exists
            existing = self.supabase.client.table('pos_terminal_mappings').select('*').eq(
                'ble_signature', signature
            ).execute()
            
            if existing.data:
                # Update existing mapping
                current = existing.data[0]
                
                if current['mcc'] == mcc:
                    # Confirmation - increase count
                    self.supabase.client.table('pos_terminal_mappings').update({
                        'confirmation_count': current['confirmation_count'] + 1,
                        'confidence': min(0.95, current['confidence'] + 0.1),
                        'last_confirmed': datetime.now().isoformat()
                    }).eq('ble_signature', signature).execute()
                else:
                    # Conflict - handle disagreement
                    logger.warning(f"MCC conflict for terminal {signature}: existing={current['mcc']}, new={mcc}")
            else:
                # Create new mapping
                self.supabase.client.table('pos_terminal_mappings').insert({
                    'ble_signature': signature,
                    'mcc': mcc,
                    'confidence': 1.0,
                    'confirmation_count': 1,
                    'device_name': device.get('name', ''),
                    'device_uuid': device.get('uuid', ''),
                    'location_hash': self._hash_location(location_data) if location_data else None,
                    'first_seen': datetime.now().isoformat(),
                    'last_confirmed': datetime.now().isoformat()
                }).execute()
            
            # Update memory cache
            if signature in self.learned_terminal_mappings:
                self.learned_terminal_mappings[signature]['confirmation_count'] += 1
            else:
                self.learned_terminal_mappings[signature] = {
                    'mcc': mcc,
                    'confidence': 1.0,
                    'confirmation_count': 1,
                    'first_seen': datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Error storing learned mapping: {e}")
    
    def _hash_location(self, location_data: Dict[str, Any]) -> str:
        """Create location hash for privacy"""
        
        if not location_data or 'latitude' not in location_data or 'longitude' not in location_data:
            return None
        
        lat = round(location_data['latitude'], 4)  # ~11m precision
        lng = round(location_data['longitude'], 4)
        
        location_string = f"{lat},{lng}"
        return hashlib.md5(location_string.encode()).hexdigest()[:12]
    
    async def get_pos_terminal_statistics(self) -> Dict[str, Any]:
        """Get statistics about POS terminal detection"""
        
        try:
            stats = {
                'total_learned_mappings': len(self.learned_terminal_mappings),
                'confidence_distribution': {},
                'mcc_distribution': {},
                'pos_system_distribution': {}
            }
            
            # Analyze learned mappings
            for mapping in self.learned_terminal_mappings.values():
                mcc = mapping['mcc']
                confidence = mapping['confidence']
                
                # MCC distribution
                stats['mcc_distribution'][mcc] = stats['mcc_distribution'].get(mcc, 0) + 1
                
                # Confidence distribution
                conf_bucket = f"{int(confidence * 10) * 10}%-{int(confidence * 10) * 10 + 9}%"
                stats['confidence_distribution'][conf_bucket] = stats['confidence_distribution'].get(conf_bucket, 0) + 1
            
            # POS system signature counts
            for pos_type in self.pos_ble_signatures.keys():
                stats['pos_system_distribution'][pos_type] = 0  # Would need tracking
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting POS statistics: {e}")
            return {}


# Global POS terminal service instance
pos_terminal_service = POSTerminalService() 