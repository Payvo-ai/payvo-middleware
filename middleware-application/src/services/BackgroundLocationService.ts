import {AppState, AppStateStatus} from 'react-native';
import BackgroundTimer from 'react-native-background-timer';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {LocationServiceInstance, LocationData} from './LocationService';
import {PayvoAPI} from './PayvoAPI';

export interface BackgroundLocationConfig {
  updateInterval: number; // milliseconds (3-5 seconds)
  minDistanceFilter: number; // meters
  enableWhenClosed: boolean;
  maxCacheSize: number;
  sessionDuration: number; // minutes
}

export interface LocationSession {
  sessionId: string;
  userId: string;
  startTime: number;
  lastUpdate: number;
  locations: LocationPrediction[];
  isActive: boolean;
  expiresAt: number;
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

class BackgroundLocationService {
  private config: BackgroundLocationConfig = {
    updateInterval: 4000, // 4 seconds
    minDistanceFilter: 5, // 5 meters
    enableWhenClosed: true,
    maxCacheSize: 100,
    sessionDuration: 30, // 30 minutes
  };

  private isTracking = false;
  private currentSession: LocationSession | null = null;
  private backgroundTimer: any = null;
  private appState: AppStateStatus = 'active';
  private lastLocation: LocationData | null = null;
  private locationCache: LocationPrediction[] = [];
  private appStateSubscription: any = null;

  constructor() {
    this.initializeAppStateListener();
  }

  /**
   * Initialize app state listener for background/foreground transitions
   */
  private initializeAppStateListener(): void {
    this.appStateSubscription = AppState.addEventListener('change', this.handleAppStateChange);
  }

  /**
   * Handle app state changes (background/foreground)
   */
  private handleAppStateChange = (nextAppState: AppStateStatus): void => {
    console.log(`📱 App state changed: ${this.appState} -> ${nextAppState}`);

    if (this.appState.match(/inactive|background/) && nextAppState === 'active') {
      // App came to foreground
      console.log('📱 App came to foreground - resuming location tracking');
      this.resumeForegroundTracking();
    } else if (this.appState === 'active' && nextAppState.match(/inactive|background/)) {
      // App went to background
      console.log('📱 App went to background - starting background tracking');
      this.startBackgroundTracking();
    }

    this.appState = nextAppState;
  };

  /**
   * Start continuous location tracking and MCC prediction
   */
  async startContinuousTracking(userId: string): Promise<string> {
    try {
      console.log('🚀 Starting continuous location tracking for user:', userId);

      // Request location permissions
      const hasPermission = await LocationServiceInstance.requestLocationPermission();
      if (!hasPermission) {
        throw new Error('Location permission required for background tracking');
      }

      // Create new session
      const sessionId = this.generateSessionId();
      this.currentSession = {
        sessionId,
        userId,
        startTime: Date.now(),
        lastUpdate: Date.now(),
        locations: [],
        isActive: true,
        expiresAt: Date.now() + (this.config.sessionDuration * 60 * 1000),
      };

      // Save session to storage
      await this.saveSessionToStorage();

      // Start location tracking
      this.isTracking = true;
      this.startLocationUpdates();

      console.log('✅ Continuous tracking started with session:', sessionId);
      return sessionId;

    } catch (error) {
      console.error('❌ Failed to start continuous tracking:', error);
      throw error;
    }
  }

  /**
   * Stop continuous location tracking
   */
  async stopContinuousTracking(): Promise<void> {
    console.log('🛑 Stopping continuous location tracking');

    this.isTracking = false;

    // Clear background timer
    if (this.backgroundTimer) {
      BackgroundTimer.clearInterval(this.backgroundTimer);
      this.backgroundTimer = null;
    }

    // Stop location tracking
    LocationServiceInstance.stopLocationTracking();

    // Mark session as inactive
    if (this.currentSession) {
      this.currentSession.isActive = false;
      await this.saveSessionToStorage();
    }

    console.log('✅ Continuous tracking stopped');
  }

  /**
   * Start location updates with background timer
   */
  private startLocationUpdates(): void {
    console.log('📍 Starting location updates every', this.config.updateInterval, 'ms');

    // Start immediate location tracking
    LocationServiceInstance.startLocationTracking();

    // Set up background timer for continuous updates
    this.backgroundTimer = BackgroundTimer.setInterval(async () => {
      if (!this.isTracking || !this.currentSession) {
        return;
      }

      try {
        await this.performLocationUpdate();
      } catch (error) {
        console.error('❌ Location update failed:', error);
      }
    }, this.config.updateInterval);
  }

  /**
   * Perform a single location update with MCC prediction
   */
  private async performLocationUpdate(): Promise<void> {
    try {
      // Get current location
      const location = await LocationServiceInstance.getCurrentLocation();

      // Check if location changed significantly
      if (this.lastLocation && this.calculateDistance(this.lastLocation, location) < this.config.minDistanceFilter) {
        console.log('📍 Location change too small, skipping update');
        return;
      }

      console.log('📍 Location update:', {
        lat: location.latitude.toFixed(6),
        lng: location.longitude.toFixed(6),
        accuracy: location.accuracy.toFixed(1) + 'm',
      });

      // Get MCC prediction for this location
      const mccPrediction = await this.getMCCPrediction(location);

      // Create location prediction entry
      const locationPrediction: LocationPrediction = {
        location,
        mccPrediction,
        timestamp: Date.now(),
        accuracy: location.accuracy,
      };

      // Add to current session
      if (this.currentSession) {
        this.currentSession.locations.push(locationPrediction);
        this.currentSession.lastUpdate = Date.now();

        // Limit cache size
        if (this.currentSession.locations.length > this.config.maxCacheSize) {
          this.currentSession.locations = this.currentSession.locations.slice(-this.config.maxCacheSize);
        }

        // Save to storage
        await this.saveSessionToStorage();
      }

      // Send to backend
      await this.sendLocationToBackend(locationPrediction);

      this.lastLocation = location;

    } catch (error) {
      console.error('❌ Location update failed:', error);
    }
  }

  /**
   * Get MCC prediction for a location
   */
  private async getMCCPrediction(location: LocationData): Promise<LocationPrediction['mccPrediction']> {
    try {
      console.log('🔮 Getting MCC prediction for location');

      const response = await PayvoAPI.predictMCC({
        latitude: location.latitude,
        longitude: location.longitude,
        radius: 50, // Start with 50m radius for background predictions
        include_alternatives: false,
        use_llm_enhancement: false, // Disable for background to save resources
      });

      return {
        mcc: response.predicted_mcc,
        confidence: response.confidence,
        method: response.method,
        timestamp: Date.now(),
      };

    } catch (error) {
      console.error('❌ MCC prediction failed:', error);
      return undefined;
    }
  }

  /**
   * Send location and prediction to backend
   */
  private async sendLocationToBackend(locationPrediction: LocationPrediction): Promise<void> {
    try {
      if (!this.currentSession) {
        return;
      }

      await PayvoAPI.updateBackgroundLocation({
        sessionId: this.currentSession.sessionId,
        userId: this.currentSession.userId,
        location: locationPrediction.location,
        mccPrediction: locationPrediction.mccPrediction,
        timestamp: locationPrediction.timestamp,
      });

      console.log('📡 Location sent to backend successfully');

    } catch (error) {
      console.error('❌ Failed to send location to backend:', error);
      // Cache for retry later
      this.locationCache.push(locationPrediction);
    }
  }

  /**
   * Start background location tracking when app goes to background
   */
  private startBackgroundTracking(): void {
    if (!this.isTracking || !this.currentSession) {
      return;
    }

    console.log('🌙 Starting background location tracking');

    try {
      // Continue with existing location tracking - no special background methods needed
      console.log('✅ Background tracking mode activated');
    } catch (error) {
      console.error('❌ Failed to start background tracking:', error);
    }
  }

  /**
   * Resume foreground location tracking when app comes to foreground
   */
  private resumeForegroundTracking(): void {
    if (!this.isTracking || !this.currentSession) {
      return;
    }

    console.log('☀️ Resuming foreground location tracking');

    try {
      // Continue with existing location tracking - no special foreground methods needed
      console.log('✅ Foreground tracking mode activated');
    } catch (error) {
      console.error('❌ Failed to resume foreground tracking:', error);
    }
  }

  /**
   * Retry sending cached locations
   */
  private async retryCachedLocations(): Promise<void> {
    if (this.locationCache.length === 0) {
      return;
    }

    console.log('🔄 Retrying', this.locationCache.length, 'cached locations');

    const cachedLocations = [...this.locationCache];
    this.locationCache = [];

    for (const locationPrediction of cachedLocations) {
      try {
        await this.sendLocationToBackend(locationPrediction);
      } catch (error) {
        console.error('❌ Retry failed for cached location:', error);
        // Re-add to cache if still failing
        this.locationCache.push(locationPrediction);
      }
    }
  }

  /**
   * Get the best MCC prediction for current location based on session history
   */
  async getBestMCCForCurrentLocation(): Promise<{mcc: string; confidence: number; method: string} | null> {
    try {
      if (!this.currentSession || this.currentSession.locations.length === 0) {
        return null;
      }

      const currentLocation = await LocationServiceInstance.getCurrentLocation();
      const recentPredictions = this.currentSession.locations
        .filter(lp => lp.mccPrediction && Date.now() - lp.timestamp < 300000) // Last 5 minutes
        .filter(lp => this.calculateDistance(lp.location, currentLocation) < 100) // Within 100m
        .sort((a, b) => b.timestamp - a.timestamp); // Most recent first

      if (recentPredictions.length === 0) {
        return null;
      }

      // Use weighted consensus of recent predictions
      const mccScores: {[mcc: string]: {score: number; count: number}} = {};

      for (const prediction of recentPredictions) {
        if (!prediction.mccPrediction) {continue;}

        const mcc = prediction.mccPrediction.mcc;
        const confidence = prediction.mccPrediction.confidence;
        const distance = this.calculateDistance(prediction.location, currentLocation);
        const timeWeight = Math.max(0.1, 1 - (Date.now() - prediction.timestamp) / 300000); // Decay over 5 minutes
        const distanceWeight = Math.max(0.1, 1 - distance / 100); // Decay over 100m

        const weight = confidence * timeWeight * distanceWeight;

        if (!mccScores[mcc]) {
          mccScores[mcc] = {score: 0, count: 0};
        }

        mccScores[mcc].score += weight;
        mccScores[mcc].count += 1;
      }

      // Find best MCC
      let bestMcc = '';
      let bestScore = 0;

      for (const [mcc, data] of Object.entries(mccScores)) {
        const finalScore = data.score * Math.log(data.count + 1); // Boost for consensus
        if (finalScore > bestScore) {
          bestScore = finalScore;
          bestMcc = mcc;
        }
      }

      if (bestMcc) {
        const confidence = Math.min(0.95, bestScore);
        return {
          mcc: bestMcc,
          confidence,
          method: 'background_session_consensus',
        };
      }

      return null;

    } catch (error) {
      console.error('❌ Failed to get best MCC:', error);
      return null;
    }
  }

  /**
   * Get current session data
   */
  getCurrentSession(): LocationSession | null {
    return this.currentSession;
  }

  /**
   * Check if session is still valid
   */
  isSessionValid(): boolean {
    if (!this.currentSession) {
      return false;
    }

    return this.currentSession.isActive && Date.now() < this.currentSession.expiresAt;
  }

  /**
   * Extend current session
   */
  async extendSession(additionalMinutes: number = 30): Promise<void> {
    if (!this.currentSession) {
      return;
    }

    this.currentSession.expiresAt = Date.now() + (additionalMinutes * 60 * 1000);
    await this.saveSessionToStorage();

    console.log('⏰ Session extended by', additionalMinutes, 'minutes');
  }

  /**
   * Save session to local storage
   */
  private async saveSessionToStorage(): Promise<void> {
    try {
      if (!this.currentSession) {
        return;
      }

      await AsyncStorage.setItem(
        'background_location_session',
        JSON.stringify(this.currentSession)
      );
    } catch (error) {
      console.error('❌ Failed to save session to storage:', error);
    }
  }

  /**
   * Load session from local storage
   */
  async loadSessionFromStorage(): Promise<LocationSession | null> {
    try {
      const sessionData = await AsyncStorage.getItem('background_location_session');
      if (!sessionData) {
        return null;
      }

      const session: LocationSession = JSON.parse(sessionData);

      // Check if session is still valid
      if (Date.now() > session.expiresAt) {
        await AsyncStorage.removeItem('background_location_session');
        return null;
      }

      this.currentSession = session;
      return session;

    } catch (error) {
      console.error('❌ Failed to load session from storage:', error);
      return null;
    }
  }

  /**
   * Calculate distance between two locations in meters
   */
  private calculateDistance(loc1: LocationData, loc2: LocationData): number {
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
  }

  /**
   * Generate unique session ID
   */
  private generateSessionId(): string {
    return `bg_session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig: Partial<BackgroundLocationConfig>): void {
    this.config = {...this.config, ...newConfig};
    console.log('⚙️ Background location config updated:', this.config);
  }

  /**
   * Get service status
   */
  getStatus(): {
    isTracking: boolean;
    hasActiveSession: boolean;
    sessionId: string | null;
    locationsCount: number;
    lastUpdate: number | null;
  } {
    return {
      isTracking: this.isTracking,
      hasActiveSession: this.isSessionValid(),
      sessionId: this.currentSession?.sessionId || null,
      locationsCount: this.currentSession?.locations.length || 0,
      lastUpdate: this.currentSession?.lastUpdate || null,
    };
  }

  /**
   * Cleanup resources and stop tracking
   */
  cleanup(): void {
    console.log('🧹 Cleaning up BackgroundLocationService');

    // Stop tracking
    this.isTracking = false;

    // Clear background timer
    if (this.backgroundTimer) {
      BackgroundTimer.clearInterval(this.backgroundTimer);
      this.backgroundTimer = null;
    }

    // Stop location tracking
    LocationServiceInstance.stopLocationTracking();

    // Remove app state listener
    if (this.appStateSubscription) {
      this.appStateSubscription.remove();
      this.appStateSubscription = null;
    }

    // Clear session
    this.currentSession = null;
    this.locationCache = [];

    console.log('✅ BackgroundLocationService cleanup completed');
  }
}

// Export singleton instance
export const BackgroundLocationServiceInstance = new BackgroundLocationService();
export default BackgroundLocationServiceInstance;
