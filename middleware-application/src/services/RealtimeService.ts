import { supabase } from '../config/supabase';
import { RealtimeChannel } from '@supabase/supabase-js';

export interface TransactionUpdate {
  id: string;
  user_id: string;
  predicted_mcc: string;
  actual_mcc: string;
  merchant_name: string;
  transaction_success: boolean;
  transaction_amount: number;
  created_at: string;
}

export interface UserSessionUpdate {
  id: string;
  user_id: string;
  is_active: boolean;
  device_name: string;
  platform: string;
  last_activity_at: string;
}

export interface LocationSessionUpdate {
  session_id: string;
  user_id: string;
  status: 'active' | 'paused' | 'completed' | 'expired' | 'cancelled';
  location_count: number;
  prediction_count: number;
  last_update: string;
}

export interface UserProfileUpdate {
  id: string;
  username: string;
  full_name: string;
  is_active: boolean;
  last_login_at: string;
}

class RealtimeService {
  private channels: Map<string, RealtimeChannel> = new Map();

  /**
   * Subscribe to real-time transaction updates
   */
  subscribeToTransactions(
    userId: string,
    onInsert?: (transaction: TransactionUpdate) => void,
    onUpdate?: (transaction: TransactionUpdate) => void
  ): string {
    const channelName = `transactions-${userId}`;

    const channel = supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'transaction_feedback',
          filter: `user_id=eq.${userId}`,
        },
        (payload) => {
          console.log('New transaction:', payload.new);
          onInsert?.(payload.new as TransactionUpdate);
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'transaction_feedback',
          filter: `user_id=eq.${userId}`,
        },
        (payload) => {
          console.log('Transaction updated:', payload.new);
          onUpdate?.(payload.new as TransactionUpdate);
        }
      )
      .subscribe();

    this.channels.set(channelName, channel);
    return channelName;
  }

  /**
   * Subscribe to user session updates (login/logout status)
   */
  subscribeToUserSessions(
    userId: string,
    onSessionChange?: (session: UserSessionUpdate) => void
  ): string {
    const channelName = `sessions-${userId}`;

    const channel = supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'user_sessions',
          filter: `user_id=eq.${userId}`,
        },
        (payload) => {
          console.log('Session change:', payload);
          onSessionChange?.(payload.new as UserSessionUpdate);
        }
      )
      .subscribe();

    this.channels.set(channelName, channel);
    return channelName;
  }

  /**
   * Subscribe to location session updates
   */
  subscribeToLocationSessions(
    userId: string,
    onLocationUpdate?: (session: LocationSessionUpdate) => void
  ): string {
    const channelName = `location-${userId}`;

    const channel = supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'background_location_sessions',
          filter: `user_id=eq.${userId}`,
        },
        (payload) => {
          console.log('Location session update:', payload.new);
          onLocationUpdate?.(payload.new as LocationSessionUpdate);
        }
      )
      .subscribe();

    this.channels.set(channelName, channel);
    return channelName;
  }

  /**
   * Subscribe to user profile updates
   */
  subscribeToUserProfile(
    userId: string,
    onProfileUpdate?: (profile: UserProfileUpdate) => void
  ): string {
    const channelName = `profile-${userId}`;

    const channel = supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'user_profiles',
          filter: `id=eq.${userId}`,
        },
        (payload) => {
          console.log('Profile updated:', payload.new);
          onProfileUpdate?.(payload.new as UserProfileUpdate);
        }
      )
      .subscribe();

    this.channels.set(channelName, channel);
    return channelName;
  }

  /**
   * Subscribe to all user-related updates (comprehensive subscription)
   */
  subscribeToUserUpdates(
    userId: string,
    callbacks: {
      onTransaction?: (transaction: TransactionUpdate) => void;
      onSession?: (session: UserSessionUpdate) => void;
      onLocation?: (session: LocationSessionUpdate) => void;
      onProfile?: (profile: UserProfileUpdate) => void;
    }
  ): string[] {
    const subscriptions: string[] = [];

    if (callbacks.onTransaction) {
      subscriptions.push(
        this.subscribeToTransactions(userId, callbacks.onTransaction)
      );
    }

    if (callbacks.onSession) {
      subscriptions.push(
        this.subscribeToUserSessions(userId, callbacks.onSession)
      );
    }

    if (callbacks.onLocation) {
      subscriptions.push(
        this.subscribeToLocationSessions(userId, callbacks.onLocation)
      );
    }

    if (callbacks.onProfile) {
      subscriptions.push(
        this.subscribeToUserProfile(userId, callbacks.onProfile)
      );
    }

    return subscriptions;
  }

  /**
   * Unsubscribe from a specific channel
   */
  unsubscribe(channelName: string): void {
    const channel = this.channels.get(channelName);
    if (channel) {
      supabase.removeChannel(channel);
      this.channels.delete(channelName);
      console.log(`Unsubscribed from ${channelName}`);
    }
  }

  /**
   * Unsubscribe from all channels
   */
  unsubscribeAll(): void {
    this.channels.forEach((channel, channelName) => {
      supabase.removeChannel(channel);
      console.log(`Unsubscribed from ${channelName}`);
    });
    this.channels.clear();
  }

  /**
   * Get the status of a channel
   */
  getChannelStatus(channelName: string): string | null {
    const channel = this.channels.get(channelName);
    return channel ? channel.state : null;
  }

  /**
   * Get all active channel names
   */
  getActiveChannels(): string[] {
    return Array.from(this.channels.keys());
  }
}

export const realtimeService = new RealtimeService();
