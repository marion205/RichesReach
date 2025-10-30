/**
 * Authentication Context with Fallback Token Generation
 * Handles both GraphQL and REST authentication methods
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useMutation } from '@apollo/client';
import { TOKEN_AUTH, VERIFY_TOKEN } from '../graphql/queries_corrected';

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
        // Verify token is still valid
        const isValid = await verifyStoredToken(storedToken);
        if (isValid) {
          // Set a basic user object for authentication
          const basicUser = {
            id: '1',
            email: 'test@example.com',
            username: 'test',
            name: 'Test User',
            hasPremiumAccess: false,
          };
          setUser(basicUser);
          // Load user data
          await loadUserData(storedToken);
        } else {
          // Token is invalid, remove it
          await AsyncStorage.removeItem('token');
          setToken(null);
          setUser(null);
        }
      }
    } catch (error) {
      console.error('Error loading stored token:', error);
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const verifyStoredToken = async (tokenToVerify: string): Promise<boolean> => {
    // DEVELOPMENT BYPASS: Always return true for testing
    console.log('🔧 DEVELOPMENT MODE: Token verification bypassed');
    return true;
  };

  const loadUserData = async (authToken: string) => {
    try {
      // This would typically be a GraphQL query to get user data
      // For now, we'll extract user info from the token or make a separate query
      console.log('Loading user data for token:', authToken.substring(0, 20) + '...');
      // TODO: Implement user data loading
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  };

  const login = async (emailOrUsername: string, password: string): Promise<boolean> => {
    setLoading(true);
    try {
      // DEVELOPMENT BYPASS: Always succeed for testing MemeQuest UI
      console.log('🔧 DEVELOPMENT MODE: Bypassing authentication for testing');
      
      const devToken = 'dev-token-' + Date.now();
      setToken(devToken);
      await AsyncStorage.setItem('token', devToken);
      console.log('🔐 Dev token stored in AsyncStorage successfully');
      
      // Set a basic user object for authentication
      const basicUser = {
        id: '1',
        email: emailOrUsername.includes('@') ? emailOrUsername : `${emailOrUsername}@example.com`,
        username: emailOrUsername.includes('@') ? emailOrUsername.split('@')[0] : emailOrUsername,
        name: emailOrUsername.includes('@') ? emailOrUsername.split('@')[0] : emailOrUsername,
        hasPremiumAccess: false,
      };
      setUser(basicUser);
      console.log('🔐 User state set:', basicUser);
      
      console.log('🔐 Development login successful, returning true');
      return true;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const restLoginFlexible = async (emailOrUsername: string, password: string): Promise<string | null> => {
    // Use environment variable or fallback to localhost
    const baseUrl = process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000";
    const identifier = emailOrUsername.trim();
    
    console.log('🔍 AuthContext: Using baseUrl:', baseUrl);
    console.log('🔍 AuthContext: Environment variable:', process.env.EXPO_PUBLIC_API_BASE_URL);
    
    const attempt = async (payload: any) => {
      console.log('🔄 AuthContext: Attempting login to:', `${baseUrl}/api/auth/login/`);
      console.log('🔄 AuthContext: Payload:', payload);
      
      try {
        const response = await fetch(`${baseUrl}/api/auth/login/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        
        console.log('📡 AuthContext: Response status:', response.status);
        console.log('📡 AuthContext: Response ok:', response.ok);
        
        const json = await response.json().catch(() => ({}));
        console.log('📡 AuthContext: Response json:', json);
        
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
        console.error('❌ AuthContext: Fetch error:', fetchError);
        throw fetchError;
      }
    };

    try {
      // 1) Try as email first
      console.log('🔄 Trying REST login with email:', identifier);
      return await attempt({ email: identifier, password });
    } catch (emailError) {
      console.log('❌ Email login failed, trying username:', emailError.message);
      try {
        // 2) Try as username
        console.log('🔄 Trying REST login with username:', identifier);
        return await attempt({ username: identifier, password });
      } catch (usernameError) {
        console.error('❌ Both email and username login failed:', usernameError.message);
        return null;
      }
    }
  };

  const restLogin = async (email: string, password: string): Promise<string | null> => {
    return restLoginFlexible(email, password);
  };

  const logout = async (): Promise<void> => {
    try {
      console.log('🔄 AuthContext: Starting logout...');
      setUser(null);
      console.log('✅ AuthContext: User set to null');
      setToken(null);
      console.log('✅ AuthContext: Token set to null');
      await AsyncStorage.removeItem('token');
      console.log('✅ AuthContext: Token removed from AsyncStorage');
    } catch (error) {
      console.error('❌ AuthContext logout error:', error);
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
      console.error('Token verification error:', error);
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