/**
 * Yodlee Integration Service for React Native
 * Handles FastLink integration and bank account linking
 */

import { API_HTTP } from '../config/api';
import logger from '../utils/logger';

export interface FastLinkSession {
  accessToken: string;
  fastlink: {
    config: {
      fastLinkURL: string;
      params: {
        userExperienceFlow: string;
        force_link: string;
      };
    };
  };
  expiresAt: number;
  userId?: number;
}

export interface FastLinkResult {
  providerAccountId: string;
  accounts: Array<{
    accountId: string;
    accountName: string;
    accountType: string;
    accountNumber?: string;
    balance?: { amount: number };
    availableBalance?: { amount: number };
    currency?: string;
    providerId?: string;
  }>;
  institution: {
    id: string;
    name: string;
  };
}

export interface BankAccount {
  id: number;
  accountId: string;
  name: string;
  type: string;
  mask: string;
  currency: string;
  balance: number;
  availableBalance: number;
  institutionName: string;
  lastUpdated?: string;
}

export interface BankTransaction {
  id: number;
  transactionId: string;
  amount: number;
  description: string;
  merchantName: string;
  category: string;
  subcategory: string;
  date: string;
  postDate?: string;
  type: 'DEBIT' | 'CREDIT';
  status: string;
}

class YodleeService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_HTTP}/api/yodlee`;
  }

  /**
   * Create a FastLink session for bank account linking
   */
  async createFastLinkSession(): Promise<FastLinkSession> {
    try {
      // Get auth token from AsyncStorage - AuthContext stores it as 'token'
      const AsyncStorage = require('@react-native-async-storage/async-storage').default;
      
      // Try 'token' first (what AuthContext uses), then fallback to other keys
      let token = await AsyncStorage.getItem('token');
      if (!token) {
        token = await AsyncStorage.getItem('authToken') || 
                await AsyncStorage.getItem('access_token') ||
                await AsyncStorage.getItem('jwt_token');
      }
      
      logger.log('🔵 [YodleeService] Token retrieved:', token ? `${token.substring(0, 30)}...` : 'NOT FOUND');
      
      // Build headers - ALWAYS include Authorization if token exists
      const headers: Record<string, string> = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
        logger.log('🔵 [YodleeService] Authorization header set:', `Bearer ${token.substring(0, 30)}...`);
      } else {
        logger.error('❌ [YodleeService] No token found in AsyncStorage!');
        logger.error('❌ [YodleeService] Tried keys: token, authToken, access_token, jwt_token');
        throw new Error('Authentication token not found. Please log in again.');
      }
      
      logger.log('🔵 [YodleeService] Request URL:', `${this.baseUrl}/fastlink/start`);
      logger.log('🔵 [YodleeService] Request method: GET');
      logger.log('🔵 [YodleeService] Request headers:', Object.keys(headers).map(k => `${k}: ${k === 'Authorization' ? headers[k].substring(0, 30) + '...' : headers[k]}`));
      
      const response = await fetch(`${this.baseUrl}/fastlink/start`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const sessionData = await response.json();
      return sessionData;
    } catch (error) {
      logger.error('Failed to create FastLink session:', error);
      throw error;
    }
  }

  /**
   * Process FastLink callback after bank account linking
   */
  async processFastLinkCallback(callbackData: FastLinkResult): Promise<{
    success: boolean;
    message: string;
    bankLinkId?: number;
    accountsCount?: number;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/fastlink/callback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Add authentication header if needed
          // 'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(callbackData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      logger.error('Failed to process FastLink callback:', error);
      throw error;
    }
  }

  /**
   * Fetch user's linked bank accounts
   */
  async fetchAccounts(): Promise<{
    success: boolean;
    accounts: BankAccount[];
    count: number;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/accounts`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          // Add authentication header if needed
          // 'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      logger.error('Failed to fetch accounts:', error);
      throw error;
    }
  }

  /**
   * Refresh account data from Yodlee
   */
  async refreshAccount(bankLinkId: number): Promise<{
    success: boolean;
    message: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Add authentication header if needed
          // 'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ bankLinkId }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      logger.error('Failed to refresh account:', error);
      throw error;
    }
  }

  /**
   * Get transactions for a specific account
   */
  async getTransactions(accountId: number): Promise<{
    success: boolean;
    transactions: BankTransaction[];
    count: number;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/transactions?accountId=${accountId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          // Add authentication header if needed
          // 'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      logger.error('Failed to get transactions:', error);
      throw error;
    }
  }

  /**
   * Delete a bank link
   */
  async deleteBankLink(bankLinkId: number): Promise<{
    success: boolean;
    message: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/bank-link/${bankLinkId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          // Add authentication header if needed
          // 'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      logger.error('Failed to delete bank link:', error);
      throw error;
    }
  }

  /**
   * Check if Yodlee integration is available
   */
  async checkAvailability(): Promise<boolean> {
    try {
      // Get auth token for the request - try 'token' first (what AuthContext uses)
      const AsyncStorage = require('@react-native-async-storage/async-storage').default;
      let token = await AsyncStorage.getItem('token');
      if (!token) {
        token = await AsyncStorage.getItem('authToken') || 
                await AsyncStorage.getItem('access_token') ||
                await AsyncStorage.getItem('jwt_token');
      }
      
      const headers: Record<string, string> = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${this.baseUrl}/fastlink/start`, {
        method: 'GET',
        headers,
      });

      // If we get a 503, Yodlee is disabled
      if (response.status === 503) {
        logger.log('Yodlee is disabled (503 response)');
        return false;
      }
      
      // If we get 401, Yodlee is enabled but auth is required (which is expected)
      if (response.status === 401) {
        logger.log('Yodlee is available (401 = auth required, which is expected)');
        return true;
      }

      // If we get 200, Yodlee is available and working
      if (response.ok) {
        logger.log('Yodlee is available (200 response)');
        return true;
      }

      // Other status codes mean Yodlee might be available but there's an issue
      logger.log(`Yodlee availability check returned status ${response.status}`);
      return false;
    } catch (error) {
      logger.error('Failed to check Yodlee availability:', error);
      return false;
    }
  }
}

// Export singleton instance
export const yodleeService = new YodleeService();
export default yodleeService;
