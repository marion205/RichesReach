/**
 * Credit Card Service
 * Handles credit card recommendations and management
 */

import { API_HTTP } from '../../../config/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { CreditCard, CreditCardRecommendation } from '../types/CreditTypes';

class CreditCardService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_HTTP}/api/credit`;
  }

  /**
   * Get user's credit cards
   */
  async getCards(): Promise<CreditCard[]> {
    try {
      const headers = await this.getAuthHeaders();
      
      const response = await fetch(`${this.baseUrl}/cards`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('[CreditCard] Failed to get cards:', error);
      return [];
    }
  }

  /**
   * Get credit card recommendations
   */
  async getRecommendations(): Promise<CreditCardRecommendation[]> {
    try {
      const headers = await this.getAuthHeaders();
      
      const response = await fetch(`${this.baseUrl}/cards/recommendations`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('[CreditCard] Failed to get recommendations:', error);
      // Return fallback recommendations
      return [
        {
          id: 'capital_one_secured',
          name: 'Capital One Platinum Secured',
          type: 'secured',
          deposit: 49,
          annualFee: 0,
          apr: 26.99,
          description: '$49 deposit for $200 line. Auto-review for limit increases after 6 months.',
          benefits: ['No annual fee', 'Auto-review for upgrades', 'Reports to all 3 bureaus'],
          preQualified: true,
          applicationUrl: 'https://www.capitalone.com/credit-cards/secured/',
        },
      ];
    }
  }

  /**
   * Get auth headers
   */
  private async getAuthHeaders(): Promise<Record<string, string>> {
    const token = await AsyncStorage.getItem('token') || await AsyncStorage.getItem('authToken');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }
}

export const creditCardService = new CreditCardService();

