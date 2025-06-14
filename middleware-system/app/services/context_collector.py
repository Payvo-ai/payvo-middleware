"""
Pre-Tap Context Collector Service
Gathers environmental data before card selection
"""

import asyncio
import hashlib
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.models.schemas import (
    PreTapContext, LocationData, WiFiData, BLEData, TerminalData
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class ContextCollector:
    """
    Collects environmental context data for MCC prediction
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = timedelta(minutes=5)
    
    async def collect_context(
        self, 
        user_id: str, 
        session_id: str,
        platform: str = "unknown"
    ) -> PreTapContext:
        """
        Main method to collect all available context data
        """
        logger.info(f"Collecting context for user {user_id}, session {session_id}")
        
        # Collect data in parallel for efficiency
        tasks = [
            self._collect_location_data(user_id),
            self._collect_wifi_data(platform),
            self._collect_ble_data(platform),
            self._collect_terminal_data(session_id)
        ]
        
        location, wifi_networks, ble_devices, terminal_data = await asyncio.gather(
            *tasks, return_exceptions=True
        )
        
        # Handle exceptions gracefully
        location = location if not isinstance(location, Exception) else None
        wifi_networks = wifi_networks if not isinstance(wifi_networks, Exception) else []
        ble_devices = ble_devices if not isinstance(ble_devices, Exception) else []
        terminal_data = terminal_data if not isinstance(terminal_data, Exception) else None
        
        context = PreTapContext(
            user_id=user_id,
            session_id=session_id,
            location=location,
            wifi_networks=wifi_networks,
            ble_devices=ble_devices,
            terminal_data=terminal_data
        )
        
        # Cache the context
        self._cache_context(session_id, context)
        
        return context
    
    async def _collect_location_data(self, user_id: str) -> Optional[LocationData]:
        """
        Collect GPS location data
        Platform-specific implementation would be required
        """
        try:
            # This would integrate with platform-specific location services
            # For now, returning mock data structure
            
            # Check cache first
            cache_key = f"location:{user_id}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if datetime.utcnow() - timestamp < self.cache_ttl:
                    return cached_data
            
            # In real implementation, this would call:
            # - iOS: Core Location framework
            # - Android: FusedLocationProviderClient
            # - Web: navigator.geolocation
            
            location_data = await self._get_device_location()
            
            if location_data:
                self.cache[cache_key] = (location_data, datetime.utcnow())
                return location_data
                
        except Exception as e:
            logger.error(f"Failed to collect location data: {e}")
            
        return None
    
    async def _collect_wifi_data(self, platform: str) -> List[WiFiData]:
        """
        Collect nearby Wi-Fi networks
        """
        try:
            wifi_networks = []
            
            # Platform-specific Wi-Fi scanning
            if platform.lower() == "android":
                wifi_networks = await self._scan_wifi_android()
            elif platform.lower() == "ios":
                wifi_networks = await self._scan_wifi_ios()
            else:
                wifi_networks = await self._scan_wifi_generic()
            
            return wifi_networks
            
        except Exception as e:
            logger.error(f"Failed to collect Wi-Fi data: {e}")
            return []
    
    async def _collect_ble_data(self, platform: str) -> List[BLEData]:
        """
        Collect nearby BLE devices and beacons
        """
        try:
            ble_devices = []
            
            # Platform-specific BLE scanning
            if platform.lower() == "android":
                ble_devices = await self._scan_ble_android()
            elif platform.lower() == "ios":
                ble_devices = await self._scan_ble_ios()
            
            return ble_devices
            
        except Exception as e:
            logger.error(f"Failed to collect BLE data: {e}")
            return []
    
    async def _collect_terminal_data(self, session_id: str) -> Optional[TerminalData]:
        """
        Collect POS terminal identification data
        """
        try:
            # This would collect:
            # - Terminal ID from NFC communication
            # - Device fingerprinting data
            # - EMV kernel timing patterns
            
            terminal_data = await self._detect_terminal_info(session_id)
            return terminal_data
            
        except Exception as e:
            logger.error(f"Failed to collect terminal data: {e}")
            return None
    
    # Platform-specific implementations (mock for now)
    
    async def _get_device_location(self) -> Optional[LocationData]:
        """Mock location data - replace with actual platform integration"""
        # In production, this would use:
        # - iOS: CLLocationManager
        # - Android: FusedLocationProviderClient
        # - Web: Geolocation API
        
        await asyncio.sleep(0.1)  # Simulate API call
        
        # Return None for now - actual implementation would return real GPS data
        return None
    
    async def _scan_wifi_android(self) -> List[WiFiData]:
        """Android Wi-Fi scanning implementation"""
        await asyncio.sleep(0.1)
        
        # Mock data - real implementation would use Android WifiManager
        return [
            WiFiData(
                ssid="Starbucks_WiFi",
                bssid="aa:bb:cc:dd:ee:ff",
                signal_strength=-45,
                frequency=2437
            )
        ]
    
    async def _scan_wifi_ios(self) -> List[WiFiData]:
        """iOS Wi-Fi scanning (limited due to privacy restrictions)"""
        await asyncio.sleep(0.1)
        
        # iOS has limited Wi-Fi scanning capabilities
        # Can only get connected network info
        return []
    
    async def _scan_wifi_generic(self) -> List[WiFiData]:
        """Generic Wi-Fi scanning for other platforms"""
        await asyncio.sleep(0.1)
        return []
    
    async def _scan_ble_android(self) -> List[BLEData]:
        """Android BLE scanning implementation"""
        await asyncio.sleep(0.1)
        
        # Mock data - real implementation would use Android BluetoothAdapter
        return [
            BLEData(
                device_id="square_terminal_123",
                uuid="550e8400-e29b-41d4-a716-446655440000",
                major=1,
                minor=100,
                rssi=-60
            )
        ]
    
    async def _scan_ble_ios(self) -> List[BLEData]:
        """iOS BLE scanning implementation"""
        await asyncio.sleep(0.1)
        
        # Mock data - real implementation would use Core Bluetooth
        return []
    
    async def _detect_terminal_info(self, session_id: str) -> Optional[TerminalData]:
        """Detect POS terminal information"""
        await asyncio.sleep(0.1)
        
        # Mock data - real implementation would analyze NFC communication
        return TerminalData(
            terminal_id="SQ_TERM_12345",
            device_id="square_a1000",
            pos_type="square_terminal",
            kernel_version="2.6.1"
        )
    
    def _cache_context(self, session_id: str, context: PreTapContext):
        """Cache context data for potential reuse"""
        cache_key = f"context:{session_id}"
        self.cache[cache_key] = (context, datetime.utcnow())
        
        # Clean old cache entries
        self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Remove expired cache entries"""
        current_time = datetime.utcnow()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
    
    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data like SSIDs and BSSIDs for privacy"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# Global instance
context_collector = ContextCollector() 