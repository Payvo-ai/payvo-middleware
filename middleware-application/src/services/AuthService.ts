import { supabase, isSupabaseReady } from '../config/supabase';

export interface AuthUser {
  id: string;
  email: string;
  username?: string;
  full_name?: string;
  isAuthenticated: boolean;
  password_change_required?: boolean;
}

export interface SignInCredentials {
  email: string;
  password: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
}

export interface UserProfile {
  id: string;
  username: string | null;
  full_name: string | null;
  avatar_url: string | null;
  phone: string | null;
  employee_id: string | null;
  department: string | null;
  role: string | null;
  preferences: any;
  is_active: boolean;
  password_change_required: boolean;
  password_changed_at: string | null;
  created_at: string;
  updated_at: string;
}

class AuthService {
  private static instance: AuthService;

  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  /**
   * Check if authentication service is available
   */
  isAvailable(): boolean {
    return isSupabaseReady;
  }

  /**
   * Sign in with email and password using Supabase Auth
   */
  async signIn(credentials: SignInCredentials): Promise<AuthUser> {
    try {
      if (!this.isAvailable()) {
        throw new Error('Authentication service is not configured. Please set up Supabase credentials.');
      }

      console.log('🔐 Attempting sign in for:', credentials.email);

      const { data, error } = await supabase.auth.signInWithPassword({
        email: credentials.email,
        password: credentials.password,
      });

      if (error) {
        console.error('❌ Supabase sign in error:', error);
        throw new Error(error.message);
      }

      if (!data.user || !data.session) {
        throw new Error('Sign in failed - no user or session returned');
      }

      // Get user profile
      const profile = await this.getUserProfile(data.user.id);

      const user: AuthUser = {
        id: data.user.id,
        email: data.user.email!,
        username: profile?.username || undefined,
        full_name: profile?.full_name || undefined,
        isAuthenticated: true,
        password_change_required: profile?.password_change_required || false,
      };

      console.log('✅ Sign in successful for:', user.email);
      return user;

    } catch (error) {
      console.error('❌ Sign in failed:', error);
      throw error;
    }
  }

  /**
   * Send forgot password email using Supabase Auth
   */
  async forgotPassword(request: ForgotPasswordRequest): Promise<void> {
    try {
      if (!this.isAvailable()) {
        throw new Error('Authentication service is not configured. Please set up Supabase credentials.');
      }

      console.log('📧 Sending forgot password email to:', request.email);

      const { error } = await supabase.auth.resetPasswordForEmail(request.email, {
        redirectTo: 'ai.payvo.middleware://reset-password', // Deep link for mobile app
      });

      if (error) {
        console.error('❌ Forgot password error:', error);
        throw new Error(error.message);
      }

      console.log('✅ Password reset email sent to:', request.email);

    } catch (error) {
      console.error('❌ Forgot password failed:', error);
      throw error;
    }
  }

  /**
   * Change password using Supabase Auth
   */
  async changePassword(request: ChangePasswordRequest): Promise<void> {
    try {
      if (!this.isAvailable()) {
        throw new Error('Authentication service is not configured. Please set up Supabase credentials.');
      }

      console.log('🔐 Changing password for authenticated user...');

      // First verify current password by attempting to sign in
      const currentUser = await this.getCurrentUser();
      if (!currentUser) {
        throw new Error('No authenticated user found.');
      }

      // Verify current password
      const { error: verifyError } = await supabase.auth.signInWithPassword({
        email: currentUser.email,
        password: request.currentPassword,
      });

      if (verifyError) {
        throw new Error('Current password is incorrect.');
      }

      // Update password
      const { error } = await supabase.auth.updateUser({
        password: request.newPassword,
      });

      if (error) {
        console.error('❌ Change password error:', error);
        throw new Error(error.message);
      }

      // Clear password change requirement and update timestamp
      const { error: profileError } = await supabase
        .from('user_profiles')
        .update({
          password_change_required: false,
          password_changed_at: new Date().toISOString(),
        })
        .eq('id', currentUser.id);

      if (profileError) {
        console.warn('⚠️ Failed to update password change status:', profileError);
        // Don't throw error here as password was successfully changed
      }

      console.log('✅ Password changed successfully');

    } catch (error) {
      console.error('❌ Change password failed:', error);
      throw error;
    }
  }

  /**
   * Set username for the authenticated user
   */
  async setUsername(username: string): Promise<void> {
    try {
      if (!this.isAvailable()) {
        throw new Error('Authentication service is not configured. Please set up Supabase credentials.');
      }

      console.log('👤 Setting username:', username);

      if (!username || username.trim().length < 2) {
        throw new Error('Username must be at least 2 characters long.');
      }

      const trimmedUsername = username.trim();

      // Get current user
      const currentUser = await this.getCurrentUser();
      if (!currentUser) {
        throw new Error('No authenticated user found.');
      }

      // Update user profile
      const { error } = await supabase
        .from('user_profiles')
        .update({ username: trimmedUsername })
        .eq('id', currentUser.id);

      if (error) {
        console.error('❌ Set username error:', error);
        throw new Error(error.message);
      }

      console.log('✅ Username set successfully:', trimmedUsername);

    } catch (error) {
      console.error('❌ Set username failed:', error);
      throw error;
    }
  }

  /**
   * Get current authenticated user
   */
  async getCurrentUser(): Promise<AuthUser | null> {
    try {
      if (!this.isAvailable()) {
        console.warn('⚠️ Authentication service not available - returning null user');
        return null;
      }

      const { data: { session } } = await supabase.auth.getSession();

      if (!session?.user) {
        return null;
      }

      // Get user profile
      const profile = await this.getUserProfile(session.user.id);

      const user: AuthUser = {
        id: session.user.id,
        email: session.user.email!,
        username: profile?.username || undefined,
        full_name: profile?.full_name || undefined,
        isAuthenticated: true,
        password_change_required: profile?.password_change_required || false,
      };

      return user;

    } catch (error) {
      console.error('❌ Get current user failed:', error);
      return null;
    }
  }

  /**
   * Get user profile from database
   */
  async getUserProfile(userId: string): Promise<UserProfile | null> {
    try {
      if (!this.isAvailable()) {
        return null;
      }

      const { data, error } = await supabase
        .from('user_profiles')
        .select('*')
        .eq('id', userId)
        .single();

      if (error) {
        console.error('❌ Get user profile error:', error);
        return null;
      }

      return data;

    } catch (error) {
      console.error('❌ Get user profile failed:', error);
      return null;
    }
  }

  /**
   * Get stored username
   */
  async getUsername(): Promise<string | null> {
    try {
      const user = await this.getCurrentUser();
      return user?.username || null;
    } catch (error) {
      console.error('❌ Get username failed:', error);
      return null;
    }
  }

  /**
   * Check if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    try {
      if (!this.isAvailable()) {
        return false;
      }

      const { data: { session } } = await supabase.auth.getSession();
      return session?.user != null;
    } catch (error) {
      console.error('❌ Check authentication failed:', error);
      return false;
    }
  }

  /**
   * Check if username is set
   */
  async hasUsername(): Promise<boolean> {
    try {
      const username = await this.getUsername();
      return username !== null && username.trim().length > 0;
    } catch (error) {
      console.error('❌ Check username failed:', error);
      return false;
    }
  }

  /**
   * Sign out user
   */
  async signOut(): Promise<void> {
    try {
      if (!this.isAvailable()) {
        console.log('✅ Sign out successful (auth service not configured)');
        return;
      }

      console.log('🚪 Signing out user...');

      const { error } = await supabase.auth.signOut();

      if (error) {
        console.error('❌ Sign out error:', error);
        throw new Error(error.message);
      }

      console.log('✅ Sign out successful');

    } catch (error) {
      console.error('❌ Sign out failed:', error);
      throw error;
    }
  }

  /**
   * Get user ID for transactions (uses email as the identifier)
   */
  async getUserId(): Promise<string> {
    try {
      const user = await this.getCurrentUser();
      if (!user) {
        throw new Error('No authenticated user found.');
      }

      // Always use email as the user ID for transactions
      return user.email;

    } catch (error) {
      console.error('❌ Get user ID failed:', error);
      throw error;
    }
  }

  /**
   * Listen to auth state changes
   */
  onAuthStateChange(callback: (user: AuthUser | null) => void) {
    if (!this.isAvailable()) {
      console.warn('⚠️ Auth state change listener not available - Supabase not configured');
      // Return a mock subscription that immediately calls callback with null
      setTimeout(() => callback(null), 0);
      return {
        data: {
          subscription: {
            unsubscribe: () => console.log('Mock auth subscription unsubscribed'),
          },
        },
      };
    }

    return supabase.auth.onAuthStateChange(async (event, session) => {
      console.log('🔄 Auth state changed:', event);

      if (session?.user) {
        const profile = await this.getUserProfile(session.user.id);
        const user: AuthUser = {
          id: session.user.id,
          email: session.user.email!,
          username: profile?.username || undefined,
          full_name: profile?.full_name || undefined,
          isAuthenticated: true,
          password_change_required: profile?.password_change_required || false,
        };
        callback(user);
      } else {
        callback(null);
      }
    });
  }

  /**
   * Create user account (admin function)
   */
  async createUser(email: string, password: string, userData?: Partial<UserProfile>): Promise<AuthUser> {
    try {
      if (!this.isAvailable()) {
        throw new Error('Authentication service is not configured. Please set up Supabase credentials.');
      }

      console.log('👤 Creating user account for:', email);

      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: userData?.full_name || '',
            employee_id: userData?.employee_id || '',
            department: userData?.department || '',
            role: userData?.role || '',
          },
        },
      });

      if (error) {
        console.error('❌ Create user error:', error);
        throw new Error(error.message);
      }

      if (!data.user) {
        throw new Error('User creation failed - no user returned');
      }

      const user: AuthUser = {
        id: data.user.id,
        email: data.user.email!,
        full_name: userData?.full_name,
        isAuthenticated: true,
      };

      console.log('✅ User created successfully:', user.email);
      return user;

    } catch (error) {
      console.error('❌ Create user failed:', error);
      throw error;
    }
  }
}

export default AuthService.getInstance();
