import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import AuthService, { AuthUser, SignInCredentials, ForgotPasswordRequest } from '../services/AuthService';

interface AuthContextType {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  hasUsername: boolean;
  signIn: (credentials: SignInCredentials) => Promise<void>;
  signOut: () => Promise<void>;
  forgotPassword: (request: ForgotPasswordRequest) => Promise<void>;
  setUsername: (username: string) => Promise<void>;
  getUserId: () => Promise<string>;
  refreshAuthState: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasUsername, setHasUsername] = useState(false);

  // Initialize authentication state
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      setIsLoading(true);
      console.log('🔄 Initializing authentication state...');

      const currentUser = await AuthService.getCurrentUser();
      const usernameExists = await AuthService.hasUsername();

      setUser(currentUser);
      setHasUsername(usernameExists);

      console.log('✅ Authentication state initialized:', {
        user: currentUser?.email,
        hasUsername: usernameExists,
      });

    } catch (error) {
      console.error('❌ Failed to initialize authentication:', error);
      setUser(null);
      setHasUsername(false);
    } finally {
      setIsLoading(false);
    }
  };

  const signIn = async (credentials: SignInCredentials) => {
    try {
      console.log('🔐 Signing in user:', credentials.email);

      const authenticatedUser = await AuthService.signIn(credentials);
      const usernameExists = await AuthService.hasUsername();

      setUser(authenticatedUser);
      setHasUsername(usernameExists);

      console.log('✅ User signed in successfully');

    } catch (error) {
      console.error('❌ Sign in failed:', error);
      throw error;
    }
  };

  const signOut = async () => {
    try {
      console.log('🚪 Signing out user...');

      await AuthService.signOut();

      setUser(null);
      setHasUsername(false);

      console.log('✅ User signed out successfully');

    } catch (error) {
      console.error('❌ Sign out failed:', error);
      throw error;
    }
  };

  const forgotPassword = async (request: ForgotPasswordRequest) => {
    try {
      console.log('📧 Requesting password reset for:', request.email);

      await AuthService.forgotPassword(request);

      console.log('✅ Password reset email sent');

    } catch (error) {
      console.error('❌ Forgot password failed:', error);
      throw error;
    }
  };

  const setUsername = async (username: string) => {
    try {
      console.log('👤 Setting username:', username);

      await AuthService.setUsername(username);

      // Update user state with new username
      if (user) {
        const updatedUser: AuthUser = {
          ...user,
          username: username.trim(),
        };
        setUser(updatedUser);
      }

      setHasUsername(true);

      console.log('✅ Username set successfully');

    } catch (error) {
      console.error('❌ Set username failed:', error);
      throw error;
    }
  };

  const getUserId = async (): Promise<string> => {
    try {
      return await AuthService.getUserId();
    } catch (error) {
      console.error('❌ Get user ID failed:', error);
      throw error;
    }
  };

  const refreshAuthState = async () => {
    await initializeAuth();
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: user?.isAuthenticated === true,
    hasUsername,
    signIn,
    signOut,
    forgotPassword,
    setUsername,
    getUserId,
    refreshAuthState,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
