import {useState, useEffect, useCallback} from 'react';
import {LocationServiceInstance, LocationData, LocationError} from '../services/LocationService';

export const useLocation = () => {
  const [location, setLocation] = useState<LocationData | null>(null);
  const [error, setError] = useState<LocationError | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);

  const requestPermission = useCallback(async () => {
    try {
      setIsLoading(true);
      const granted = await LocationServiceInstance.requestLocationPermission();
      setHasPermission(granted);
      return granted;
    } catch (err) {
      setError({
        code: 1,
        message: 'Failed to request location permission',
        type: 'PERMISSION_DENIED',
      });
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getCurrentLocation = useCallback(async () => {
    if (!hasPermission) {
      const granted = await requestPermission();
      if (!granted) {
        return;
      }
    }

    try {
      setIsLoading(true);
      const currentLocation = await LocationServiceInstance.getCurrentLocation();
      setLocation(currentLocation);
      setError(null);
      return currentLocation;
    } catch (err) {
      const locationError = err as LocationError;
      setError(locationError);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [hasPermission, requestPermission]);

  const startLocationTracking = useCallback(() => {
    if (!hasPermission) {
      requestPermission();
      return;
    }

    LocationServiceInstance.addLocationCallback((newLocation) => {
      setLocation(newLocation);
      setError(null);
    });

    LocationServiceInstance.addErrorCallback((newError) => {
      setError(newError);
    });

    LocationServiceInstance.startLocationTracking();
  }, [hasPermission, requestPermission]);

  const stopLocationTracking = useCallback(() => {
    LocationServiceInstance.stopLocationTracking();
  }, []);

  useEffect(() => {
    // Check initial permission status
    LocationServiceInstance.isLocationAvailable().then(setHasPermission);

    // Cleanup on unmount
    return () => {
      LocationServiceInstance.cleanup();
    };
  }, []);

  return {
    location,
    error,
    isLoading,
    hasPermission,
    requestPermission,
    getCurrentLocation,
    startLocationTracking,
    stopLocationTracking,
  };
};
