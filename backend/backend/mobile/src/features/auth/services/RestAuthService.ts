// RestAuthService.ts - REST-based authentication service
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_AUTH } from '../../../config';

interface TokenPayload {
  sub: string;
  email: string;
  username: string;
  iss: string;
  aud: string;
  iat: number;
  exp: number;
}

class RestAuthService {
  private static instance: RestAuthService;
  private refreshTimer: NodeJS.Timeout | null = null;
  private onTokenRefreshFailure: (() => void) | null = null;

  private constructor() {}

  static getInstance(): RestAuthService {
    if (!RestAuthService.instance) {
      RestAuthService.instance = new RestAuthService();
    }
    return RestAuthService.instance;
  }

  setTokenRefreshFailureCallback(callback: () => void) {
    this.onTokenRefreshFailure = callback;
  }

  /**
   * Decode JWT token without verification (client-side only)
   */
  private decodeToken(token: string): TokenPayload | null {
    try {
      // Check if token exists and is a string
      if (!token || typeof token !== 'string') {
        console.warn('Token is undefined or not a string:', token);
        return null;
      }
      
      // Check if token has the expected JWT format (3 parts separated by dots)
      const parts = token.split('.');
      if (parts.length !== 3) {
        console.warn('Invalid JWT format - expected 3 parts, got:', parts.length);
        return null;
      }
      
      const base64Url = parts[1];
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
    if (!token || typeof token !== 'string') {
      return true; // No token means expired
    }
    
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
   * Login with email and password using REST API
   */
  async login(email: string, password: string): Promise<{ token: string; payload: any }> {
    try {
      console.log('🔐 Attempting login to:', API_AUTH);
      
      const response = await fetch(API_AUTH, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Login failed with status ${response.status}`);
      }

      const data = await response.json();
      
      if (data.token) {
        const token = data.token;
        const payload = this.decodeToken(token);
        
        if (!payload) {
          throw new Error('Invalid token received from server');
        }
        
        await this.storeToken(token);
        this.scheduleTokenRefresh(token);
        
        console.log('✅ Login successful, token stored');
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
   * Check if user is authenticated and token is valid
   */
  async isAuthenticated(): Promise<boolean> {
    const token = await this.getCurrentToken();
    if (!token) return false;

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

export default RestAuthService;
