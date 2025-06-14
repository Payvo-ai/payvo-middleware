import { createClient } from '@supabase/supabase-js';

// Supabase configuration
const supabaseUrl = 'YOUR_SUPABASE_URL'; // Replace with your actual Supabase URL
const supabaseAnonKey = 'YOUR_SUPABASE_ANON_KEY'; // Replace with your actual Supabase anon key

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    // Enable automatic token refresh
    autoRefreshToken: true,
    // Persist session in AsyncStorage
    persistSession: true,
    // Detect session from URL (useful for deep linking)
    detectSessionInUrl: false,
  },
});

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