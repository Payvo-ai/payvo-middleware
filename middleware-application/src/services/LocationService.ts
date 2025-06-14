import {Platform, PermissionsAndroid, Alert} from 'react-native';
import Geolocation from '@react-native-community/geolocation';

export interface LocationData {
  latitude: number;
  longitude: number;
  accuracy: number;
  altitude?: number;
  speed?: number;
  heading?: number;
  timestamp: number;
  source: 'gps' | 'network' | 'passive';
}

export interface LocationError {
  code: number;
  message: string;
  type: 'PERMISSION_DENIED' | 'POSITION_UNAVAILABLE' | 'TIMEOUT' | 'UNKNOWN';
}

class LocationService {
  private watchId: number | null = null;
  private lastKnownLocation: LocationData | null = null;
  private locationCallbacks: ((location: LocationData) => void)[] = [];
  private errorCallbacks: ((error: LocationError) => void)[] = [];

  constructor() {
    // Configure Geolocation
    Geolocation.setRNConfiguration({
      skipPermissionRequests: false,
      authorizationLevel: 'whenInUse',
      enableBackgroundLocationUpdates: false,
      locationProvider: 'auto',
    });
  }

  /**
   * Request location permissions based on platform
   */
  async requestLocationPermission(): Promise<boolean> {
    try {
      if (Platform.OS === 'ios') {
        // iOS permissions are handled automatically by react-native-geolocation-service
        return true;
      } else {
        // Android permissions
        const granted = await PermissionsAndroid.request(
          PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
          {
            title: 'Payvo Location Permission',
            message: 'Payvo needs access to your location to provide accurate merchant detection and optimal payment routing.',
            buttonNeutral: 'Ask Me Later',
            buttonNegative: 'Cancel',
            buttonPositive: 'OK',
          },
        );
        return granted === PermissionsAndroid.RESULTS.GRANTED;
      }
    } catch (error) {
      console.error('Error requesting location permission:', error);
      return false;
    }
  }

  /**
   * Get current location with high accuracy
   */
  async getCurrentLocation(): Promise<LocationData> {
    return new Promise((resolve, reject) => {
      Geolocation.getCurrentPosition(
        (position) => {
          const locationData: LocationData = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            altitude: position.coords.altitude ?? undefined,
            speed: position.coords.speed ?? undefined,
            heading: position.coords.heading ?? undefined,
            timestamp: position.timestamp,
            source: 'gps',
          };

          this.lastKnownLocation = locationData;
          console.log('📍 Current location obtained:', {
            lat: locationData.latitude.toFixed(6),
            lng: locationData.longitude.toFixed(6),
            accuracy: locationData.accuracy.toFixed(1) + 'm',
          });

          resolve(locationData);
        },
        (error) => {
          const locationError: LocationError = {
            code: error.code,
            message: error.message,
            type: this.getErrorType(error.code),
          };

          console.error('❌ Location error:', locationError);
          reject(locationError);
        },
        {
          enableHighAccuracy: true,
          timeout: 15000,
          maximumAge: 10000,
        }
      );
    });
  }

  /**
   * Start watching location changes
   */
  startLocationTracking(): void {
    if (this.watchId !== null) {
      console.log('📍 Location tracking already active');
      return;
    }

    this.watchId = Geolocation.watchPosition(
      (position) => {
        const locationData: LocationData = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          altitude: position.coords.altitude ?? undefined,
          speed: position.coords.speed ?? undefined,
          heading: position.coords.heading ?? undefined,
          timestamp: position.timestamp,
          source: 'gps',
        };

        this.lastKnownLocation = locationData;

        // Notify all callbacks
        this.locationCallbacks.forEach(callback => {
          try {
            callback(locationData);
          } catch (error) {
            console.error('Error in location callback:', error);
          }
        });

        console.log('📍 Location updated:', {
          lat: locationData.latitude.toFixed(6),
          lng: locationData.longitude.toFixed(6),
          accuracy: locationData.accuracy.toFixed(1) + 'm',
        });
      },
      (error) => {
        const locationError: LocationError = {
          code: error.code,
          message: error.message,
          type: this.getErrorType(error.code),
        };

        // Notify all error callbacks
        this.errorCallbacks.forEach(callback => {
          try {
            callback(locationError);
          } catch (callbackError) {
            console.error('Error in location error callback:', callbackError);
          }
        });

        console.error('❌ Location tracking error:', locationError);
      },
      {
        enableHighAccuracy: true,
        distanceFilter: 10, // Update every 10 meters
        interval: 5000,     // Update every 5 seconds
        fastestInterval: 2000, // Fastest update interval
      }
    );

    console.log('📍 Location tracking started');
  }

  /**
   * Stop watching location changes
   */
  stopLocationTracking(): void {
    if (this.watchId !== null) {
      Geolocation.clearWatch(this.watchId);
      this.watchId = null;
      console.log('📍 Location tracking stopped');
    }
  }

  /**
   * Get last known location
   */
  getLastKnownLocation(): LocationData | null {
    return this.lastKnownLocation;
  }

  /**
   * Add location update callback
   */
  addLocationCallback(callback: (location: LocationData) => void): void {
    this.locationCallbacks.push(callback);
  }

  /**
   * Remove location update callback
   */
  removeLocationCallback(callback: (location: LocationData) => void): void {
    const index = this.locationCallbacks.indexOf(callback);
    if (index > -1) {
      this.locationCallbacks.splice(index, 1);
    }
  }

  /**
   * Add location error callback
   */
  addErrorCallback(callback: (error: LocationError) => void): void {
    this.errorCallbacks.push(callback);
  }

  /**
   * Remove location error callback
   */
  removeErrorCallback(callback: (error: LocationError) => void): void {
    const index = this.errorCallbacks.indexOf(callback);
    if (index > -1) {
      this.errorCallbacks.splice(index, 1);
    }
  }

  /**
   * Format location data for Payvo API
   */
  formatLocationForAPI(location: LocationData): any {
    return {
      latitude: location.latitude,
      longitude: location.longitude,
      accuracy: location.accuracy,
      altitude: location.altitude,
      speed: location.speed,
      heading: location.heading,
      timestamp: new Date(location.timestamp).toISOString(),
      source: location.source,
    };
  }

  /**
   * Check if location services are available
   */
  async isLocationAvailable(): Promise<boolean> {
    try {
      const hasPermission = await this.requestLocationPermission();
      if (!hasPermission) {
        return false;
      }

      // Try to get current location to verify services are working
      await this.getCurrentLocation();
      return true;
    } catch (error) {
      console.error('Location services not available:', error);
      return false;
    }
  }

  /**
   * Show location permission dialog
   */
  showLocationPermissionDialog(): void {
    Alert.alert(
      'Location Permission Required',
      'Payvo needs access to your location to:\n\n• Detect merchants automatically\n• Provide accurate MCC predictions\n• Optimize your payment card selection\n• Enhance transaction security',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Enable Location',
          onPress: async () => {
            const granted = await this.requestLocationPermission();
            if (!granted) {
              Alert.alert(
                'Permission Denied',
                'Location access is required for optimal payment routing. You can enable it later in Settings.',
                [{text: 'OK'}]
              );
            }
          },
        },
      ]
    );
  }

  /**
   * Convert error code to error type
   */
  private getErrorType(code: number): LocationError['type'] {
    switch (code) {
      case 1:
        return 'PERMISSION_DENIED';
      case 2:
        return 'POSITION_UNAVAILABLE';
      case 3:
        return 'TIMEOUT';
      default:
        return 'UNKNOWN';
    }
  }

  /**
   * Get human-readable error message
   */
  getErrorMessage(error: LocationError): string {
    switch (error.type) {
      case 'PERMISSION_DENIED':
        return 'Location permission denied. Please enable location access in Settings.';
      case 'POSITION_UNAVAILABLE':
        return 'Location unavailable. Please check your GPS settings and try again.';
      case 'TIMEOUT':
        return 'Location request timed out. Please try again.';
      default:
        return `Location error: ${error.message}`;
    }
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    this.stopLocationTracking();
    this.locationCallbacks = [];
    this.errorCallbacks = [];
    this.lastKnownLocation = null;
  }
}

// Export singleton instance
export const LocationServiceInstance = new LocationService();
export default LocationService;
