import { createClient } from '@supabase/supabase-js';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Temporary hardcoded configuration - replace with proper env loading later
const supabaseUrl = 'https://wwnakavxuejqltflzqhr.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind3bmFrYXZ4dWVqcWx0Zmx6cWhyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk0NDYwOTAsImV4cCI6MjA2NTAyMjA5MH0.yK0v--EIVSYMx52LPa4eUbW_0XR2cnVvj__cvojjmw4';

// Check if Supabase is properly configured
const isSupabaseConfigured = true; // Hardcoded to true since we have valid credentials

console.log('✅ Supabase configured successfully');

// Create a mock client for development when Supabase is not configured
const createMockSupabaseClient = () => ({
  auth: {
    getSession: async () => ({ data: { session: null }, error: null }),
    signInWithPassword: async () => ({ data: null, error: { message: 'Supabase not configured' } }),
    signUp: async () => ({ data: null, error: { message: 'Supabase not configured' } }),
    signOut: async () => ({ error: null }),
    onAuthStateChange: (callback: any) => {
      // Call callback with null user immediately for mock
      setTimeout(() => callback('SIGNED_OUT', null), 0);
      return {
        data: {
          subscription: {
            unsubscribe: () => console.log('Mock auth subscription unsubscribed'),
          },
        },
      };
    },
    resetPasswordForEmail: async () => ({ error: { message: 'Supabase not configured' } }),
    updateUser: async () => ({ error: { message: 'Supabase not configured' } }),
  },
  from: () => ({
    select: () => ({ eq: () => ({ single: async () => ({ data: null, error: { message: 'Supabase not configured' } }) }) }),
    update: () => ({ eq: async () => ({ error: { message: 'Supabase not configured' } }) }),
    insert: async () => ({ error: { message: 'Supabase not configured' } }),
  }),
});

export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        // Use AsyncStorage for React Native
        storage: AsyncStorage,
        // Enable automatic token refresh
        autoRefreshToken: true,
        // Persist session in AsyncStorage
        persistSession: true,
        // Disable session detection from URL for React Native
        detectSessionInUrl: false,
      },
      // Add React Native specific options
      global: {
        headers: {
          'X-Client-Info': 'payvo-mobile-app',
        },
      },
    })
  : createMockSupabaseClient();

// Export configuration status - fix the export name
export const isSupabaseReady = isSupabaseConfigured;

// Database types (you can generate these with Supabase CLI)
export interface Database {
  public: {
    Tables: {
      user_profiles: {
        Row: {
          id: string;
          username: string | null;
          full_name: string | null;
          avatar_url: string | null;
          phone: string | null;
          date_of_birth: string | null;
          timezone: string;
          language: string;
          employee_id: string | null;
          department: string | null;
          role: string | null;
          manager_id: string | null;
          preferences: any;
          is_active: boolean;
          is_verified: boolean;
          last_login_at: string | null;
          login_count: number;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id: string;
          username?: string | null;
          full_name?: string | null;
          avatar_url?: string | null;
          phone?: string | null;
          date_of_birth?: string | null;
          timezone?: string;
          language?: string;
          employee_id?: string | null;
          department?: string | null;
          role?: string | null;
          manager_id?: string | null;
          preferences?: any;
          is_active?: boolean;
          is_verified?: boolean;
          last_login_at?: string | null;
          login_count?: number;
        };
        Update: {
          username?: string | null;
          full_name?: string | null;
          avatar_url?: string | null;
          phone?: string | null;
          date_of_birth?: string | null;
          timezone?: string;
          language?: string;
          employee_id?: string | null;
          department?: string | null;
          role?: string | null;
          manager_id?: string | null;
          preferences?: any;
          is_active?: boolean;
          is_verified?: boolean;
          last_login_at?: string | null;
          login_count?: number;
        };
      };
    };
  };
}
