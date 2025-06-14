import { useEffect, useRef } from 'react';
import { realtimeService, TransactionUpdate, UserSessionUpdate, LocationSessionUpdate, UserProfileUpdate } from '../services/RealtimeService';

interface UseRealtimeOptions {
  userId: string;
  onTransaction?: (transaction: TransactionUpdate) => void;
  onSession?: (session: UserSessionUpdate) => void;
  onLocation?: (session: LocationSessionUpdate) => void;
  onProfile?: (profile: UserProfileUpdate) => void;
  enabled?: boolean;
}

/**
 * Custom hook for managing real-time subscriptions
 * Automatically handles subscription lifecycle and cleanup
 */
export const useRealtime = ({
  userId,
  onTransaction,
  onSession,
  onLocation,
  onProfile,
  enabled = true
}: UseRealtimeOptions) => {
  const subscriptionsRef = useRef<string[]>([]);

  useEffect(() => {
    if (!enabled || !userId) {
      return;
    }

    console.log('Setting up realtime subscriptions for user:', userId);

    // Subscribe to updates
    const subscriptions = realtimeService.subscribeToUserUpdates(userId, {
      onTransaction,
      onSession,
      onLocation,
      onProfile
    });

    subscriptionsRef.current = subscriptions;

    // Cleanup function
    return () => {
      console.log('Cleaning up realtime subscriptions');
      subscriptions.forEach(channelName => {
        realtimeService.unsubscribe(channelName);
      });
      subscriptionsRef.current = [];
    };
  }, [userId, enabled, onTransaction, onSession, onLocation, onProfile]);

  return {
    activeChannels: subscriptionsRef.current,
    unsubscribeAll: () => {
      subscriptionsRef.current.forEach(channelName => {
        realtimeService.unsubscribe(channelName);
      });
      subscriptionsRef.current = [];
    }
  };
};

/**
 * Hook specifically for transaction updates
 */
export const useTransactionUpdates = (
  userId: string,
  onNewTransaction?: (transaction: TransactionUpdate) => void,
  onTransactionUpdate?: (transaction: TransactionUpdate) => void,
  enabled: boolean = true
) => {
  const subscriptionRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled || !userId) {
      return;
    }

    console.log('Setting up transaction updates for user:', userId);

    const channelName = realtimeService.subscribeToTransactions(
      userId,
      onNewTransaction,
      onTransactionUpdate
    );

    subscriptionRef.current = channelName;

    return () => {
      if (subscriptionRef.current) {
        realtimeService.unsubscribe(subscriptionRef.current);
        subscriptionRef.current = null;
      }
    };
  }, [userId, enabled, onNewTransaction, onTransactionUpdate]);

  return {
    channelName: subscriptionRef.current,
    unsubscribe: () => {
      if (subscriptionRef.current) {
        realtimeService.unsubscribe(subscriptionRef.current);
        subscriptionRef.current = null;
      }
    }
  };
};

/**
 * Hook specifically for location session updates
 */
export const useLocationUpdates = (
  userId: string,
  onLocationUpdate?: (session: LocationSessionUpdate) => void,
  enabled: boolean = true
) => {
  const subscriptionRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled || !userId) {
      return;
    }

    console.log('Setting up location updates for user:', userId);

    const channelName = realtimeService.subscribeToLocationSessions(
      userId,
      onLocationUpdate
    );

    subscriptionRef.current = channelName;

    return () => {
      if (subscriptionRef.current) {
        realtimeService.unsubscribe(subscriptionRef.current);
        subscriptionRef.current = null;
      }
    };
  }, [userId, enabled, onLocationUpdate]);

  return {
    channelName: subscriptionRef.current,
    unsubscribe: () => {
      if (subscriptionRef.current) {
        realtimeService.unsubscribe(subscriptionRef.current);
        subscriptionRef.current = null;
      }
    }
  };
};

/**
 * Hook for user profile updates
 */
export const useProfileUpdates = (
  userId: string,
  onProfileUpdate?: (profile: UserProfileUpdate) => void,
  enabled: boolean = true
) => {
  const subscriptionRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled || !userId) {
      return;
    }

    console.log('Setting up profile updates for user:', userId);

    const channelName = realtimeService.subscribeToUserProfile(
      userId,
      onProfileUpdate
    );

    subscriptionRef.current = channelName;

    return () => {
      if (subscriptionRef.current) {
        realtimeService.unsubscribe(subscriptionRef.current);
        subscriptionRef.current = null;
      }
    };
  }, [userId, enabled, onProfileUpdate]);

  return {
    channelName: subscriptionRef.current,
    unsubscribe: () => {
      if (subscriptionRef.current) {
        realtimeService.unsubscribe(subscriptionRef.current);
        subscriptionRef.current = null;
      }
    }
  };
}; 