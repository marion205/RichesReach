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
      // Try REST login first
      logger.log('🔐 Attempting REST login...');
      const token = await restLoginFlexible(emailOrUsername, password);
      
      if (token) {
        setToken(token);
        await AsyncStorage.setItem('token', token);
        logger.log('🔐 Token stored in AsyncStorage successfully');
        logger.log('🔐 Login successful, returning true');
        return true;
      } else {
        // REST login failed - don't fallback automatically, return false
        logger.warn('🔐 REST login failed, no token received');
        return false;
      }
    } catch (error) {
      logger.error('Login error:', error);
      // Only return false on actual errors, don't fallback
      return false;
    } finally {
      setLoading(false);
    }
  };

  const restLoginFlexible = async (emailOrUsername: string, password: string): Promise<string | null> => {
    // Use the centralized API config which handles device detection (localhost for simulator, LAN IP for real device)
    const { API_BASE } = await import('../config/api');
    let baseUrl = API_BASE;
    const identifier = emailOrUsername.trim();
    
    // Final safety check: if baseUrl is still localhost, force LAN IP
    // This is a hard override - don't trust device detection, just force it
    if (/localhost|127\.0\.0\.1/.test(baseUrl)) {
      logger.warn('⚠️ AuthContext: baseUrl is localhost, FORCING LAN IP override');
      baseUrl = 'http://10.0.0.54:8000';
      logger.log('✅ AuthContext: Overridden to:', baseUrl);
    }
    
    logger.log('🔍 AuthContext: Final baseUrl being used:', baseUrl);
    logger.log('🔍 AuthContext: API_BASE imported was:', API_BASE);
    logger.log('🔍 AuthContext: API_BASE imported:', API_BASE);
    logger.log('🔍 AuthContext: Environment variable:', process.env.EXPO_PUBLIC_API_BASE_URL);
    logger.log('🔍 AuthContext: Platform.OS:', require('react-native').Platform.OS);
    logger.log('🔍 AuthContext: Constants.isDevice:', require('expo-constants').default.isDevice);
    
    const attempt = async (payload: any) => {
      const loginUrl = `${baseUrl}/api/auth/login/`;
      logger.log('🔄 AuthContext: Attempting login to:', loginUrl);
      logger.log('🔄 AuthContext: Payload:', { ...payload, password: '***' });
      
      try {
        const response = await fetch(loginUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        }).catch((fetchError) => {
          // Network errors (connection refused, timeout, etc.)
          logger.error('❌ AuthContext: Network error:', fetchError);
          if (fetchError.message?.includes('Network request failed') || 
              fetchError.message?.includes('Failed to fetch') ||
              fetchError.message?.includes('ECONNREFUSED')) {
            // Use the actual baseUrl that was attempted, not a hardcoded message
            const errorMsg = `Cannot connect to server at ${baseUrl}. ` +
              `Please check:\n` +
              `1. Backend is running on port 8000\n` +
              `2. Using correct IP address (not localhost on physical device)\n` +
              `3. Firewall allows connections`;
            logger.error('❌ AuthContext: Connection failed to:', baseUrl);
            throw new Error(errorMsg);
          }
          throw fetchError;
        });
        
        logger.log('📡 AuthContext: Response status:', response.status);
        logger.log('📡 AuthContext: Response ok:', response.ok);
        
        const json = await response.json().catch((parseError) => {
          logger.error('❌ AuthContext: Failed to parse response:', parseError);
          return { error: 'Invalid response from server' };
        });
        logger.log('📡 AuthContext: Response json:', json);
        
        if (!response.ok) {
          const errorDetail = json?.detail || json?.error || `Login failed with status ${response.status}`;
          logger.error('❌ AuthContext: Login failed:', {
            status: response.status,
            statusText: response.statusText,
            error: errorDetail,
            response: json
          });
          throw new Error(errorDetail);
        }
        
        // Handle response format: /api/auth/login/ returns {access_token, token, user}
        // Accept either access_token or token
        const token = json.access_token || json.token;
        if (!token) {
          throw new Error('Missing token in response');
        }
        
        // Store user data from REST response
        if (json.user) {
          setUser(json.user);
        }
        
        logger.log('✅ AuthContext: Login successful, token received');
        return token;
      } catch (fetchError: any) {
        logger.error('❌ AuthContext: Fetch error:', fetchError);
        // Re-throw with more context if it's a network error
        if (fetchError.message?.includes('Network request failed') || 
            fetchError.message?.includes('Failed to fetch')) {
          throw new Error(
            `Network error: Cannot reach ${baseUrl}/api/auth/login/\n\n` +
            `Possible fixes:\n` +
            `- Check backend is running: curl ${baseUrl}/health\n` +
            `- On physical device, use LAN IP instead of localhost\n` +
            `- Check EXPO_PUBLIC_API_BASE_URL environment variable`
          );
        }
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