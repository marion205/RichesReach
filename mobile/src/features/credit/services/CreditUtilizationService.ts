/**
 * Credit Utilization Service
 * Calculates and tracks credit utilization
 */

import { API_HTTP } from '../../../config/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { CreditUtilization } from '../types/CreditTypes';

class CreditUtilizationService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_HTTP}/api/credit`;
  }

  /**
   * Get credit utilization data
   */
  async getUtilization(): Promise<CreditUtilization> {
    try {
      const headers = await this.getAuthHeaders();
      
      const response = await fetch(`${this.baseUrl}/utilization`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        totalLimit: data.totalLimit || 0,
        totalBalance: data.totalBalance || 0,
        currentUtilization: data.currentUtilization || 0,
        optimalUtilization: data.optimalUtilization || 0.3,
        paydownSuggestion: data.paydownSuggestion || 0,
        projectedScoreGain: data.projectedScoreGain || 0,
      };
    } catch (error) {
      console.error('[CreditUtilization] Failed to get utilization:', error);
      // Return fallback
      return {
        totalLimit: 1000,
        totalBalance: 450,
        currentUtilization: 0.45,
        optimalUtilization: 0.3,
        paydownSuggestion: 150,
        projectedScoreGain: 8,
      };
    }
  }

  /**
   * Get optimal paydown suggestion
   */
  async getOptimalPaydown(): Promise<{ amount: number; projectedGain: number }> {
    const utilization = await this.getUtilization();
    return {
      amount: utilization.paydownSuggestion,
      projectedGain: utilization.projectedScoreGain,
    };
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

export const creditUtilizationService = new CreditUtilizationService();

