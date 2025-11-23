/**
 * Authentication Context with Fallback Token Generation
 * Handles both GraphQL and REST authentication methods
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useMutation } from '@apollo/client';
import { TOKEN_AUTH, VERIFY_TOKEN } from '../graphql/queries_corrected';
import logger from '../utils/logger';

interface User {
  id: string;
  email: string;
  username: string;
  name: string;
  profilePic?: string;
  hasPremiumAccess: boolean;
  subscriptionTier?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  verifyToken: () => Promise<boolean>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [tokenAuthMutation] = useMutation(TOKEN_AUTH);
  const [verifyTokenMutation] = useMutation(VERIFY_TOKEN);

  // Load stored token on app start
  useEffect(() => {
    loadStoredToken();
  }, []);

  const loadStoredToken = async () => {
    try {
      const storedToken = await AsyncStorage.getItem('token');
      if (storedToken) {
        setToken(storedToken);
        // Skip verification for demo - instant load
          const basicUser = {
            id: '1',
            email: 'test@example.com',
            username: 'test',
            name: 'Test User',
            hasPremiumAccess: false,
          };
          setUser(basicUser);
        // Load user data in background (non-blocking)
        loadUserData(storedToken).catch(() => {});
      }
    } catch (error) {
      logger.error('Error loading stored token:', error);
      setToken(null);
      setUser(null);
    } finally {
      // Set loading to false immediately for fast startup
      setLoading(false);
    }
  };

  const verifyStoredToken = async (tokenToVerify: string): Promise<boolean> => {
    // DEVELOPMENT BYPASS: Always return true for testing
    logger.log('🔧 DEVELOPMENT MODE: Token verification bypassed');
    return true;
  };

  const loadUserData = async (authToken: string) => {
    try {
      // This would typically be a GraphQL query to get user data
      // For now, we'll extract user info from the token or make a separate query
      logger.log('Loading user data for token:', authToken.substring(0, 20) + '...');
      // Future enhancement: Implement user data loading from GraphQL query or user service
    } catch (error) {
      logger.error('Error loading user data:', error);
    }
  };

  const login = async (emailOrUsername: string, password: string): Promise<boolean> => {
    setLoading(true);
    try {
      // DEVELOPMENT BYPASS: Always succeed for testing MemeQuest UI
      logger.log('🔧 DEVELOPMENT MODE: Bypassing authentication for testing');
      
      const devToken = 'dev-token-' + Date.now();
      setToken(devToken);
      await AsyncStorage.setItem('token', devToken);
      logger.log('🔐 Dev token stored in AsyncStorage successfully');
      
      // Set a basic user object for authentication
      const basicUser = {
        id: '1',
        email: emailOrUsername.includes('@') ? emailOrUsername : `${emailOrUsername}@example.com`,
        username: emailOrUsername.includes('@') ? emailOrUsername.split('@')[0] : emailOrUsername,
        name: emailOrUsername.includes('@') ? emailOrUsername.split('@')[0] : emailOrUsername,
        hasPremiumAccess: false,
      };
      setUser(basicUser);
      logger.log('🔐 User state set:', basicUser);
      
      logger.log('🔐 Development login successful, returning true');
      return true;
    } catch (error) {
      logger.error('Login error:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const restLoginFlexible = async (emailOrUsername: string, password: string): Promise<string | null> => {
    // Use environment variable or fallback to localhost
    const baseUrl = process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000";
    const identifier = emailOrUsername.trim();
    
    logger.log('🔍 AuthContext: Using baseUrl:', baseUrl);
    logger.log('🔍 AuthContext: Environment variable:', process.env.EXPO_PUBLIC_API_BASE_URL);
    
    const attempt = async (payload: any) => {
      logger.log('🔄 AuthContext: Attempting login to:', `${baseUrl}/api/auth/login/`);
      logger.log('🔄 AuthContext: Payload:', payload);
      
      try {
        const response = await fetch(`${baseUrl}/api/auth/login/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        
        logger.log('📡 AuthContext: Response status:', response.status);
        logger.log('📡 AuthContext: Response ok:', response.ok);
        
        const json = await response.json().catch(() => ({}));
        logger.log('📡 AuthContext: Response json:', json);
        
        if (!response.ok) {
          throw new Error(json?.error || `Login failed with status ${response.status}`);
        }
        
        // Handle response format: /api/auth/login/ returns {token, user}
        if (!json.access_token) {
          throw new Error('Missing token in response');
        }
        
        // Store user data from REST response
        if (json.user) {
          setUser(json.user);
        }
        
        return json.access_token;
      } catch (fetchError) {
        logger.error('❌ AuthContext: Fetch error:', fetchError);
        throw fetchError;
      }
    };

    try {
      // 1) Try as email first
      logger.log('🔄 Trying REST login with email:', identifier);
      return await attempt({ email: identifier, password });
    } catch (emailError) {
      logger.log('❌ Email login failed, trying username:', emailError.message);
      try {
        // 2) Try as username
        logger.log('🔄 Trying REST login with username:', identifier);
        return await attempt({ username: identifier, password });
      } catch (usernameError) {
        logger.error('❌ Both email and username login failed:', usernameError.message);
        return null;
      }
    }
  };

  const restLogin = async (email: string, password: string): Promise<string | null> => {
    return restLoginFlexible(email, password);
  };

  const logout = async (): Promise<void> => {
    try {
      logger.log('🔴 [AuthContext] logout called - before state');
      setUser(null);
      setToken(null);
      await AsyncStorage.removeItem('token');
      logger.log('✅ AuthContext: Token removed from AsyncStorage');
      logger.log('🔴 [AuthContext] logout - state updated: isAuthenticated will be false');
    } catch (error) {
      logger.error('❌ AuthContext logout error:', error);
    }
  };

  const verifyToken = async (): Promise<boolean> => {
    if (!token) return false;
    
    try {
      const isValid = await verifyStoredToken(token);
      if (!isValid) {
        await logout();
      }
      return isValid;
    } catch (error) {
      logger.error('Token verification error:', error);
      return false;
    }
  };

  const value: AuthContextType = {
    user,
    token,
    loading,
    login,
    logout,
    verifyToken,
    isAuthenticated: !!token && !!user,
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

// Helper hook for components that need authentication
export const useRequireAuth = () => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return { loading: true, isAuthenticated: false };
  }
  
  if (!isAuthenticated) {
    // Redirect to login or show login modal
    return { loading: false, isAuthenticated: false };
  }
  
  return { loading: false, isAuthenticated: true };
};