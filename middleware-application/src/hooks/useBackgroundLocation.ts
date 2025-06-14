import { useState, useEffect, useCallback, useRef } from 'react';
import { AppState, AppStateStatus } from 'react-native';
import { LocationServiceInstance, LocationData } from '../services/LocationService';
import { PayvoAPI } from '../services/PayvoAPI';

export interface BackgroundLocationConfig {
  updateInterval: number; // milliseconds
  minDistanceFilter: number; // meters
  sessionDuration: number; // minutes
  enableWhenClosed: boolean;
}

export interface BackgroundLocationSession {
  sessionId: string;
  userId: string;
  startTime: Date;
  lastUpdate: Date;
  isActive: boolean;
  expiresAt: Date;
  locationCount: number;
  locations: LocationPrediction[];
}

export interface LocationPrediction {
  location: LocationData;
  mccPrediction?: {
    mcc: string;
    confidence: number;
    method: string;
    timestamp: number;
  };
  timestamp: number;
  accuracy: number;
}

export interface BackgroundLocationStatus {
  isTracking: boolean;
  hasActiveSession: boolean;
  sessionId: string | null;
  locationsCount: number;
  lastUpdate: Date | null;
  error: string | null;
}

const DEFAULT_CONFIG: BackgroundLocationConfig = {
  updateInterval: 4000, // 4 seconds
  minDistanceFilter: 5, // 5 meters
  sessionDuration: 30, // 30 minutes
  enableWhenClosed: true,
};

export const useBackgroundLocation = (userId: string, config: Partial<BackgroundLocationConfig> = {}) => {
  const [status, setStatus] = useState<BackgroundLocationStatus>({
    isTracking: false,
    hasActiveSession: false,
    sessionId: null,
    locationsCount: 0,
    lastUpdate: null,
    error: null,
  });

  const [currentSession, setCurrentSession] = useState<BackgroundLocationSession | null>(null);
  const [recentPredictions, setRecentPredictions] = useState<LocationPrediction[]>([]);

  const configRef = useRef<BackgroundLocationConfig>(DEFAULT_CONFIG);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastLocationRef = useRef<LocationData | null>(null);

  // Update config ref when config changes
  useEffect(() => {
    configRef.current = { ...DEFAULT_CONFIG, ...config };
  }, [config]);

  // Utility function to calculate distance
  const calculateDistance = (loc1: LocationData, loc2: LocationData): number => {
    const R = 6371e3; // Earth's radius in meters
    const φ1 = (loc1.latitude * Math.PI) / 180;
    const φ2 = (loc2.latitude * Math.PI) / 180;
    const Δφ = ((loc2.latitude - loc1.latitude) * Math.PI) / 180;
    const Δλ = ((loc2.longitude - loc1.longitude) * Math.PI) / 180;

    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c;
  };

  // Perform a single location update
  const performLocationUpdate = useCallback(async (): Promise<void> => {
    try {
      if (!currentSession) {
        return;
      }

      // Get current location
      const location = await LocationServiceInstance.getCurrentLocation();

      // Check if location changed significantly
      if (lastLocationRef.current && calculateDistance(lastLocationRef.current, location) < configRef.current.minDistanceFilter) {
        console.log('📍 Location change too small, skipping update');
        return;
      }

      console.log('📍 Location update:', {
        lat: location.latitude.toFixed(6),
        lng: location.longitude.toFixed(6),
        accuracy: location.accuracy.toFixed(1) + 'm',
      });

      // Get MCC prediction
      let mccPrediction: LocationPrediction['mccPrediction'];
      try {
        const prediction = await PayvoAPI.predictMCC({
          latitude: location.latitude,
          longitude: location.longitude,
          radius: 50,
          include_alternatives: false,
          use_llm_enhancement: false,
        });

        mccPrediction = {
          mcc: prediction.predicted_mcc,
          confidence: prediction.confidence,
          method: prediction.method,
          timestamp: Date.now(),
        };
      } catch (error) {
        console.error('❌ MCC prediction failed:', error);
      }

      // Create location prediction
      const locationPrediction: LocationPrediction = {
        location,
        mccPrediction,
        timestamp: Date.now(),
        accuracy: location.accuracy,
      };

      // Update local session
      const updatedSession = {
        ...currentSession,
        lastUpdate: new Date(),
        locationCount: currentSession.locationCount + 1,
        locations: [...currentSession.locations.slice(-99), locationPrediction], // Keep last 100
      };

      setCurrentSession(updatedSession);
      setRecentPredictions(prev => [...prev.slice(-19), locationPrediction]); // Keep last 20

      // Send to backend
      await PayvoAPI.updateBackgroundLocation({
        sessionId: currentSession.sessionId,
        userId: currentSession.userId,
        location,
        mccPrediction,
        timestamp: Date.now(),
      });

      // Update status
      setStatus(prev => ({
        ...prev,
        locationsCount: prev.locationsCount + 1,
        lastUpdate: new Date(),
      }));

      // Store last location
      lastLocationRef.current = location;

    } catch (error) {
      console.error('❌ Location update failed:', error);
      setStatus(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Unknown error',
      }));
    }
  }, [currentSession]);

  // Start location updates with interval
  const startLocationUpdates = useCallback(() => {
    console.log('📍 Starting location updates every', configRef.current.updateInterval, 'ms');

    // Start immediate location tracking
    LocationServiceInstance.startLocationTracking();

    // Set up interval for continuous updates
    intervalRef.current = setInterval(async () => {
      if (!status.isTracking || !currentSession) {
        return;
      }

      try {
        await performLocationUpdate();
      } catch (error) {
        console.error('❌ Location update failed:', error);
      }
    }, configRef.current.updateInterval);
  }, [status.isTracking, currentSession, performLocationUpdate]);

  // Background tracking helpers
  const startBackgroundTracking = useCallback(() => {
    console.log('🌙 Starting background location tracking');
    // Platform-specific background location setup would go here
  }, []);

  const resumeForegroundTracking = useCallback(() => {
    console.log('☀️ Resuming foreground location tracking');
    // Resume normal tracking, retry any cached data
  }, []);

  // Handle app state changes for background/foreground transitions
  useEffect(() => {
    const handleAppStateChange = (nextAppState: AppStateStatus) => {
      console.log('📱 App state changed to:', nextAppState);

      if (nextAppState === 'background' && status.isTracking) {
        console.log('📱 App going to background, starting background tracking');
        startBackgroundTracking();
      } else if (nextAppState === 'active' && status.isTracking) {
        console.log('📱 App coming to foreground, resuming foreground tracking');
        resumeForegroundTracking();
      }
    };

    const subscription = AppState.addEventListener('change', handleAppStateChange);
    return () => subscription?.remove();
  }, [status.isTracking, startBackgroundTracking, resumeForegroundTracking]);

  // Start continuous location tracking
  const startTracking = useCallback(async (): Promise<string | null> => {
    try {
      console.log('🚀 Starting background location tracking for user:', userId);

      // Request location permissions
      const hasPermission = await LocationServiceInstance.requestLocationPermission();
      if (!hasPermission) {
        throw new Error('Location permission required for background tracking');
      }

      // Start backend session
      const response = await PayvoAPI.startBackgroundTracking({
        user_id: userId,
        session_duration_minutes: configRef.current.sessionDuration,
        update_interval_seconds: Math.floor(configRef.current.updateInterval / 1000),
        min_distance_filter_meters: configRef.current.minDistanceFilter,
      });

      const sessionId = response.session_id;

      // Create local session
      const newSession: BackgroundLocationSession = {
        sessionId,
        userId,
        startTime: new Date(response.start_time),
        lastUpdate: new Date(),
        isActive: true,
        expiresAt: new Date(response.expires_at),
        locationCount: 0,
        locations: [],
      };

      setCurrentSession(newSession);
      setStatus(prev => ({
        ...prev,
        isTracking: true,
        hasActiveSession: true,
        sessionId,
        error: null,
      }));

      // Start location updates
      startLocationUpdates();

      console.log('✅ Background tracking started with session:', sessionId);
      return sessionId;

    } catch (error) {
      console.error('❌ Failed to start background tracking:', error);
      setStatus(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Unknown error',
      }));
      return null;
    }
  }, [userId, startLocationUpdates]);

  // Stop continuous location tracking
  const stopTracking = useCallback(async (): Promise<void> => {
    try {
      console.log('🛑 Stopping background location tracking');

      // Clear interval
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }

      // Stop location service
      LocationServiceInstance.stopLocationTracking();

      // Stop backend session
      if (status.sessionId) {
        await PayvoAPI.stopBackgroundTracking(status.sessionId);
      }

      // Reset state
      setCurrentSession(null);
      setRecentPredictions([]);
      setStatus({
        isTracking: false,
        hasActiveSession: false,
        sessionId: null,
        locationsCount: 0,
        lastUpdate: null,
        error: null,
      });

      console.log('✅ Background tracking stopped');

    } catch (error) {
      console.error('❌ Failed to stop background tracking:', error);
      setStatus(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Unknown error',
      }));
    }
  }, [status.sessionId]);

  // Get optimal MCC for current location
  const getOptimalMCC = useCallback(async (): Promise<{
    mcc: string;
    confidence: number;
    method: string;
  } | null> => {
    try {
      if (!currentSession) {
        return null;
      }

      const currentLocation = await LocationServiceInstance.getCurrentLocation();

      const response = await PayvoAPI.getOptimalMCC(
        currentSession.sessionId,
        currentLocation.latitude,
        currentLocation.longitude,
        100 // 100m radius
      );

      return {
        mcc: response.mcc,
        confidence: response.confidence,
        method: response.method,
      };

    } catch (error) {
      console.error('❌ Failed to get optimal MCC:', error);
      return null;
    }
  }, [currentSession]);

  // Extend current session
  const extendSession = useCallback(async (additionalMinutes: number = 30): Promise<boolean> => {
    try {
      if (!currentSession) {
        return false;
      }

      await PayvoAPI.extendBackgroundSession(currentSession.sessionId, additionalMinutes);

      const newExpiresAt = new Date(currentSession.expiresAt.getTime() + additionalMinutes * 60 * 1000);

      setCurrentSession(prev => prev ? {
        ...prev,
        expiresAt: newExpiresAt,
      } : null);

      console.log('⏰ Session extended by', additionalMinutes, 'minutes');
      return true;

    } catch (error) {
      console.error('❌ Failed to extend session:', error);
      return false;
    }
  }, [currentSession]);

  // Check if session is still valid
  const isSessionValid = useCallback((): boolean => {
    if (!currentSession) {
      return false;
    }

    return currentSession.isActive && new Date() < currentSession.expiresAt;
  }, [currentSession]);

  // Get session status from backend
  const refreshSessionStatus = useCallback(async (): Promise<void> => {
    try {
      if (!status.sessionId) {
        return;
      }

      const response = await PayvoAPI.getBackgroundSessionStatus(status.sessionId);

      setStatus(prev => ({
        ...prev,
        hasActiveSession: response.is_active,
        locationsCount: response.location_count,
        lastUpdate: new Date(response.last_update),
      }));

    } catch (error) {
      console.error('❌ Failed to refresh session status:', error);
    }
  }, [status.sessionId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      LocationServiceInstance.stopLocationTracking();
    };
  }, []);

  return {
    // State
    status,
    currentSession,
    recentPredictions,

    // Actions
    startTracking,
    stopTracking,
    getOptimalMCC,
    extendSession,
    refreshSessionStatus,

    // Computed
    isSessionValid: isSessionValid(),
    isTracking: status.isTracking,
    hasActiveSession: status.hasActiveSession,
    sessionId: status.sessionId,
    locationsCount: status.locationsCount,
    lastUpdate: status.lastUpdate,
    error: status.error,
  };
};
