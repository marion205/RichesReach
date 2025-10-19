import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE } from '../config/api';

class CSRFService {
  private static instance: CSRFService;
  private csrfToken: string | null = null;

  private constructor() {}

  public static getInstance(): CSRFService {
    if (!CSRFService.instance) {
      CSRFService.instance = new CSRFService();
    }
    return CSRFService.instance;
  }

  /**
   * Fetch CSRF token from the server
   */
  public async fetchCSRFToken(): Promise<string | null> {
    try {
      console.log('🔐 Fetching CSRF token from server...');
      
      const response = await fetch(`${API_BASE}/csrf-token/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies for CSRF
      });

      if (response.ok) {
        const data = await response.json();
        const token = data.csrfToken || data.csrf_token;
        
        if (token) {
          this.csrfToken = token;
          await AsyncStorage.setItem('csrfToken', token);
          console.log('✅ CSRF token fetched and stored');
          return token;
        }
      } else {
        console.warn('⚠️ Failed to fetch CSRF token:', response.status);
      }
    } catch (error) {
      console.error('❌ Error fetching CSRF token:', error);
    }

    return null;
  }

  /**
   * Get stored CSRF token or fetch new one
   */
  public async getCSRFToken(): Promise<string | null> {
    // First try to get from memory
    if (this.csrfToken) {
      return this.csrfToken;
    }

    // Then try to get from storage
    try {
      const storedToken = await AsyncStorage.getItem('csrfToken');
      if (storedToken) {
        this.csrfToken = storedToken;
        return storedToken;
      }
    } catch (error) {
      console.error('❌ Error reading CSRF token from storage:', error);
    }

    // Finally, fetch from server
    return await this.fetchCSRFToken();
  }

  /**
   * Clear CSRF token (on logout)
   */
  public async clearCSRFToken(): Promise<void> {
    this.csrfToken = null;
    try {
      await AsyncStorage.removeItem('csrfToken');
      console.log('🧹 CSRF token cleared');
    } catch (error) {
      console.error('❌ Error clearing CSRF token:', error);
    }
  }

  /**
   * Refresh CSRF token (call this periodically or on 403 errors)
   */
  public async refreshCSRFToken(): Promise<string | null> {
    console.log('🔄 Refreshing CSRF token...');
    await this.clearCSRFToken();
    return await this.fetchCSRFToken();
  }
}

export default CSRFService;
