import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Keychain from 'react-native-keychain';

export interface AuthUser {
  id: string;
  email: string;
  username?: string;
  isAuthenticated: boolean;
}

export interface SignInCredentials {
  email: string;
  password: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

class AuthService {
  private static instance: AuthService;
  private readonly STORAGE_KEYS = {
    USER: '@payvo_auth_user',
    USERNAME: '@payvo_username',
    SESSION: '@payvo_session',
  };

  private readonly KEYCHAIN_SERVICE = 'PayvoEmployeeAuth';

  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  /**
   * Sign in with email and password
   * Note: This is a mock implementation since we're manually managing users in Supabase
   * In production, this would integrate with Supabase Auth
   */
  async signIn(credentials: SignInCredentials): Promise<AuthUser> {
    try {
      console.log('🔐 Attempting sign in for:', credentials.email);

      // Mock authentication - in production, this would call Supabase Auth
      // For now, we'll validate against a predefined list of Payvo employee emails
      const validEmployees = [
        'test@payvo.ai',
        'demo@payvo.ai',
        'employee@payvo.ai',
        'admin@payvo.ai',
        'dev@payvo.ai',
      ];

      const isValidEmployee = validEmployees.includes(credentials.email.toLowerCase());

      if (!isValidEmployee) {
        throw new Error('Access denied. This app is only available to Payvo employees.');
      }

      // Mock password validation (in production, Supabase would handle this)
      if (credentials.password.length < 6) {
        throw new Error('Invalid credentials. Please check your email and password.');
      }

      // Create user object
      const user: AuthUser = {
        id: `payvo_${Date.now()}`,
        email: credentials.email.toLowerCase(),
        isAuthenticated: true,
      };

      // Store credentials securely
      await Keychain.setInternetCredentials(
        this.KEYCHAIN_SERVICE,
        credentials.email,
        credentials.password
      );

      // Store user data
      await AsyncStorage.setItem(this.STORAGE_KEYS.USER, JSON.stringify(user));

      console.log('✅ Sign in successful for:', user.email);
      return user;

    } catch (error) {
      console.error('❌ Sign in failed:', error);
      throw error;
    }
  }

  /**
   * Send forgot password email
   * Note: This is a mock implementation
   */
  async forgotPassword(request: ForgotPasswordRequest): Promise<void> {
    try {
      console.log('📧 Sending forgot password email to:', request.email);

      // Mock validation
      const validEmployees = [
        'test@payvo.ai',
        'demo@payvo.ai',
        'employee@payvo.ai',
        'admin@payvo.ai',
        'dev@payvo.ai',
      ];

      const isValidEmployee = validEmployees.includes(request.email.toLowerCase());

      if (!isValidEmployee) {
        throw new Error('Email not found. Please contact your administrator.');
      }

      // Mock delay to simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));

      console.log('✅ Password reset email sent to:', request.email);

    } catch (error) {
      console.error('❌ Forgot password failed:', error);
      throw error;
    }
  }

  /**
   * Set username for the authenticated user
   */
  async setUsername(username: string): Promise<void> {
    try {
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

      // Update user with username
      const updatedUser: AuthUser = {
        ...currentUser,
        username: trimmedUsername,
      };

      // Store updated user data
      await AsyncStorage.setItem(this.STORAGE_KEYS.USER, JSON.stringify(updatedUser));
      await AsyncStorage.setItem(this.STORAGE_KEYS.USERNAME, trimmedUsername);

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
      const userJson = await AsyncStorage.getItem(this.STORAGE_KEYS.USER);
      if (!userJson) {
        return null;
      }

      const user: AuthUser = JSON.parse(userJson);
      return user;

    } catch (error) {
      console.error('❌ Get current user failed:', error);
      return null;
    }
  }

  /**
   * Get stored username
   */
  async getUsername(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(this.STORAGE_KEYS.USERNAME);
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
      const user = await this.getCurrentUser();
      return user?.isAuthenticated === true;
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
      console.log('🚪 Signing out user...');

      // Clear stored data
      await AsyncStorage.multiRemove([
        this.STORAGE_KEYS.USER,
        this.STORAGE_KEYS.USERNAME,
        this.STORAGE_KEYS.SESSION,
      ]);

      // Clear keychain
      await Keychain.resetInternetCredentials(this.KEYCHAIN_SERVICE);

      console.log('✅ Sign out successful');

    } catch (error) {
      console.error('❌ Sign out failed:', error);
      throw error;
    }
  }

  /**
   * Get user ID for transactions (uses username if available, otherwise email)
   */
  async getUserId(): Promise<string> {
    try {
      const user = await this.getCurrentUser();
      if (!user) {
        throw new Error('No authenticated user found.');
      }

      // Use username if available, otherwise use email prefix
      if (user.username) {
        return user.username;
      }

      // Fallback to email prefix
      return user.email.split('@')[0];

    } catch (error) {
      console.error('❌ Get user ID failed:', error);
      throw error;
    }
  }

  /**
   * Clear all stored data (for development/testing)
   */
  async clearAllData(): Promise<void> {
    try {
      console.log('🧹 Clearing all authentication data...');

      await AsyncStorage.multiRemove([
        this.STORAGE_KEYS.USER,
        this.STORAGE_KEYS.USERNAME,
        this.STORAGE_KEYS.SESSION,
      ]);

      await Keychain.resetInternetCredentials(this.KEYCHAIN_SERVICE);

      console.log('✅ All authentication data cleared');

    } catch (error) {
      console.error('❌ Clear all data failed:', error);
      throw error;
    }
  }
}

export default AuthService.getInstance();
