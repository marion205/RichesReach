// JWTAuthService.ts
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ApolloClient } from '@apollo/client';
import { gql } from '@apollo/client';

const REFRESH_TOKEN_MUTATION = gql`
  mutation RefreshToken {
    refreshToken {
      token
    }
  }
`;

const LOGIN_MUTATION = gql`
  mutation Login($email: String!, $password: String!) {
    tokenAuth(email: $email, password: $password) {
      token
    }
  }
`;

interface TokenPayload {
  email: string;
  exp: number;
  origIat: number;
}

class JWTAuthService {
  private static instance: JWTAuthService;
  private refreshTimer: NodeJS.Timeout | null = null;
  private apolloClient: ApolloClient<any> | null = null;
  private onTokenRefreshFailure: (() => void) | null = null;

  private constructor() {}

  static getInstance(): JWTAuthService {
    if (!JWTAuthService.instance) {
      JWTAuthService.instance = new JWTAuthService();
    }
    return JWTAuthService.instance;
  }

  setApolloClient(client: ApolloClient<any>) {
    this.apolloClient = client;
  }

  setTokenRefreshFailureCallback(callback: () => void) {
    this.onTokenRefreshFailure = callback;
  }

  /**
   * Decode JWT token without verification (client-side only)
   */
  private decodeToken(token: string): TokenPayload | null {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('Error decoding token:', error);
      return null;
    }
  }

  /**
   * Check if token is expired or will expire soon (within 5 minutes)
   */
  private isTokenExpiredOrExpiringSoon(token: string): boolean {
    const payload = this.decodeToken(token);
    if (!payload) return true;

    const now = Math.floor(Date.now() / 1000);
    const expirationTime = payload.exp;
    const fiveMinutesInSeconds = 5 * 60;

    return (expirationTime - now) < fiveMinutesInSeconds;
  }

  /**
   * Get current token from storage
   */
  async getCurrentToken(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem('token');
    } catch (error) {
      console.error('Error getting token from storage:', error);
      return null;
    }
  }

  /**
   * Store token in AsyncStorage
   */
  async storeToken(token: string): Promise<void> {
    try {
      await AsyncStorage.setItem('token', token);
    } catch (error) {
      console.error('Error storing token:', error);
      throw error;
    }
  }

  /**
   * Remove token from storage
   */
  async removeToken(): Promise<void> {
    try {
      await AsyncStorage.removeItem('token');
      this.clearRefreshTimer();
    } catch (error) {
      console.error('Error removing token:', error);
    }
  }

  /**
   * Login with email and password
   */
  async login(email: string, password: string): Promise<{ token: string; payload: any }> {
    if (!this.apolloClient) {
      throw new Error('Apollo client not initialized');
    }

    try {
      const result = await this.apolloClient.mutate({
        mutation: LOGIN_MUTATION,
        variables: { email, password },
      });

      if (result.data?.tokenAuth) {
        const { token, payload } = result.data.tokenAuth;
        await this.storeToken(token);
        this.scheduleTokenRefresh(token);
        return { token, payload };
      } else {
        throw new Error('Login failed: No token received');
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  /**
   * Refresh the current token
   */
  async refreshToken(): Promise<string | null> {
    if (!this.apolloClient) {
      console.error('Apollo client not initialized');
      return null;
    }

    try {
      // For now, since refresh token requires additional setup, 
      // we'll just return the current token if it's still valid
      const currentToken = await this.getCurrentToken();
      if (currentToken && !this.isTokenExpiredOrExpiringSoon(currentToken)) {
        return currentToken;
      }

      // If token is expired, we need to login again
      console.log('Token is expired, user needs to login again');
      await this.removeToken();
      return null;
    } catch (error) {
      console.error('Token refresh error:', error);
      await this.removeToken();
      return null;
    }
  }

  /**
   * Check if user is authenticated and token is valid
   */
  async isAuthenticated(): Promise<boolean> {
    const token = await this.getCurrentToken();
    if (!token) return false;

    // For now, just check if token exists and is not expired
    // We'll handle refresh separately
    const payload = this.decodeToken(token);
    if (!payload) return false;

    const now = Math.floor(Date.now() / 1000);
    const expirationTime = payload.exp;
    
    // Token is valid if it hasn't expired yet
    return expirationTime > now;
  }

  /**
   * Get a valid token (refresh if needed)
   */
  async getValidToken(): Promise<string | null> {
    const token = await this.getCurrentToken();
    if (!token) return null;

    // For now, just return the token if it exists and is not expired
    const payload = this.decodeToken(token);
    if (!payload) return null;

    const now = Math.floor(Date.now() / 1000);
    const expirationTime = payload.exp;
    
    // Return token if it hasn't expired yet
    if (expirationTime > now) {
      return token;
    }

    // Token is expired, remove it
    await this.removeToken();
    return null;
  }

  /**
   * Schedule automatic token refresh
   */
  private scheduleTokenRefresh(token: string): void {
    this.clearRefreshTimer();

    const payload = this.decodeToken(token);
    if (!payload) return;

    const now = Math.floor(Date.now() / 1000);
    const expirationTime = payload.exp;
    const timeUntilExpiration = (expirationTime - now) * 1000; // Convert to milliseconds

    // For now, just log when the token will expire
    // In a production app, you would implement proper token refresh here
    console.log(`Token will expire in ${Math.round(timeUntilExpiration / 1000 / 60)} minutes`);
    
    // Set a timer to warn when token is about to expire
    const warningTime = Math.max(timeUntilExpiration - (5 * 60 * 1000), 60000); // 5 minutes before expiration
    
    this.refreshTimer = setTimeout(() => {
      console.log('Token is about to expire, user may need to login again soon');
      if (this.onTokenRefreshFailure) {
        this.onTokenRefreshFailure();
      }
    }, warningTime);
  }

  /**
   * Clear the refresh timer
   */
  private clearRefreshTimer(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    this.clearRefreshTimer();
    await this.removeToken();
  }

  /**
   * Initialize the service with a valid token
   */
  async initializeWithToken(token: string): Promise<void> {
    await this.storeToken(token);
    this.scheduleTokenRefresh(token);
  }
}

export default JWTAuthService;
