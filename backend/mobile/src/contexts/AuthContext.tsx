import React, { createContext, useContext, useState, useEffect } from 'react';

interface AuthContextType {
  token: string | null;
  user: any | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<any | null>(null);

  // Check for existing token on app start
  useEffect(() => {
    // TODO: Check for stored token in AsyncStorage
    // For now, we'll start without authentication
    setToken(null);
    setUser(null);
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      // TODO: Implement real authentication API call
      // For now, return false to indicate no authentication
      console.log('Login attempt:', email);
      return false;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    // TODO: Clear stored token from AsyncStorage
  };

  const value: AuthContextType = {
    token,
    user,
    login,
    logout,
    isAuthenticated: !!token,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
