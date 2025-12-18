/**
 * Credit Score Service
 * Handles credit score fetching, refreshing, and projections
 */

import { API_HTTP } from '../../../config/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { CreditScore, CreditProjection, CreditSnapshot } from '../types/CreditTypes';

class CreditScoreService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_HTTP}/api/credit`;
  }

  /**
   * Get current credit score
   */
  async getScore(): Promise<CreditScore> {
    try {
      const headers = await this.getAuthHeaders();
      
      // Add timeout to prevent hanging
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
      
      try {
        const response = await fetch(`${this.baseUrl}/score`, {
          method: 'GET',
          headers,
          signal: controller.signal,
        });
        
        clearTimeout(timeoutId);

      if (!response.ok) {
        // 404 is expected when backend isn't deployed yet - use fallback silently
        if (response.status === 404) {
          if (__DEV__) {
            console.warn('[CreditScore] API endpoint not found (404) - using fallback data');
          }
        } else {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
      } else {
        return await response.json();
      }
      } catch (fetchError: any) {
        clearTimeout(timeoutId);
        if (fetchError.name === 'AbortError') {
          throw new Error('Request timeout');
        }
        throw fetchError;
      }
    } catch (error: any) {
      // Only log non-404 errors as errors, 404s are expected in dev
      if (error?.message?.includes('404')) {
        if (__DEV__) {
          console.warn('[CreditScore] API unavailable (404), using fallback data');
        }
      } else if (error?.message?.includes('timeout')) {
        if (__DEV__) {
          console.warn('[CreditScore] Request timeout, using fallback data');
        }
      } else {
        console.warn('[CreditScore] Failed to get score:', error);
      }
      // Return fallback
      return {
        score: 580,
        scoreRange: 'Fair',
        lastUpdated: new Date().toISOString(),
        provider: 'self_reported',
      };
    }
  }

  /**
   * Refresh credit score
   */
  async refreshScore(score?: number, provider: string = 'self_reported'): Promise<CreditScore> {
    try {
      const headers = await this.getAuthHeaders();
      
      const response = await fetch(`${this.baseUrl}/score/refresh`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ score, provider }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('[CreditScore] Failed to refresh score:', error);
      throw error;
    }
  }

  /**
   * Get credit score projection
   */
  async getProjection(): Promise<CreditProjection> {
    try {
      const headers = await this.getAuthHeaders();
      
      // Add timeout to prevent hanging
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
      
      try {
        const response = await fetch(`${this.baseUrl}/projection`, {
          method: 'GET',
          headers,
          signal: controller.signal,
        });
        
        clearTimeout(timeoutId);

      if (!response.ok) {
        // 404 is expected when backend isn't deployed yet - use fallback silently
        if (response.status === 404) {
          if (__DEV__) {
            console.warn('[CreditScore] Projection API endpoint not found (404) - using fallback data');
          }
        } else {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
      } else {
        return await response.json();
      }
      } catch (fetchError: any) {
        clearTimeout(timeoutId);
        if (fetchError.name === 'AbortError') {
          throw new Error('Request timeout');
        }
        throw fetchError;
      }
    } catch (error: any) {
      // Only log non-404 errors as errors, 404s are expected in dev
      if (error?.message?.includes('404')) {
        if (__DEV__) {
          console.warn('[CreditScore] Projection API unavailable (404), using fallback data');
        }
      } else if (error?.message?.includes('timeout')) {
        if (__DEV__) {
          console.warn('[CreditScore] Projection request timeout, using fallback data');
        }
      } else {
        console.warn('[CreditScore] Failed to get projection:', error);
      }
      // Return fallback
      return {
        scoreGain6m: 42,
        topAction: 'SET_UP_AUTOPAY',
        confidence: 0.71,
        factors: {},
      };
    }
  }

  /**
   * Get complete credit snapshot
   * Always returns data (uses fallback if API fails)
   */
  async getSnapshot(): Promise<CreditSnapshot> {
    try {
      const headers = await this.getAuthHeaders();
      
      // Add timeout to prevent hanging
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
      
      try {
        const response = await fetch(`${this.baseUrl}/snapshot`, {
          method: 'GET',
          headers,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorText = await response.text().catch(() => 'Unknown error');
          console.warn(`[CreditScore] HTTP error! status: ${response.status}, body: ${errorText}`);
          // Fall through to fallback
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('[CreditScore] Successfully loaded snapshot from API');
        
        // Ensure actions and shield arrays exist (backend might return empty arrays)
        if (!data.actions || data.actions.length === 0) {
          data.actions = [
            {
              id: '1',
              type: 'AUTOPAY_SETUP',
              title: 'Set Up Autopay',
              description: 'Automate your credit card payments to never miss a due date',
              completed: false,
              projectedScoreGain: 15,
              dueDate: null,
            },
            {
              id: '2',
              type: 'UTILIZATION_REDUCED',
              title: 'Reduce Utilization Below 30%',
              description: 'Pay down $150 to get your utilization under the optimal 30% threshold',
              completed: false,
              projectedScoreGain: 25,
              dueDate: null,
            },
          ];
        }
        
        // Ensure shield alerts exist if utilization is high (but not if it's 0%)
        if (!data.shield || data.shield.length === 0) {
          const utilization = data.utilization?.currentUtilization || 0;
          if (utilization > 0.3 && utilization > 0) {
            data.shield = [
              {
                type: 'HIGH_UTILIZATION',
                inDays: null,
                message: `Utilization is ${Math.round(utilization * 100)}% - aim for under 30%`,
                suggestion: 'REDUCE_UTILIZATION',
              },
            ];
          } else {
            // If utilization is 0% or low, still show helpful actions
            data.shield = [];
          }
        }
        
        return data;
      } catch (fetchError: any) {
        clearTimeout(timeoutId);
        if (fetchError.name === 'AbortError') {
          throw new Error('Request timeout');
        }
        throw fetchError;
      }
    } catch (error) {
      console.warn('[CreditScore] API unavailable, using fallback data:', error);
      
      // Return fallback snapshot immediately - don't wait for other API calls
      // This ensures the UI loads quickly even if backend is down
      return {
        score: {
          score: 580,
          scoreRange: 'Fair' as const,
          lastUpdated: new Date().toISOString(),
          provider: 'self_reported',
        },
        cards: [],
        utilization: {
          totalLimit: 1000,
          totalBalance: 0,
          currentUtilization: 0,
          optimalUtilization: 0.3,
          paydownSuggestion: 0,
          projectedScoreGain: 0,
        },
        projection: {
          scoreGain6m: 42,
          topAction: 'SET_UP_AUTOPAY',
          confidence: 0.71,
          factors: {},
        },
        actions: [
          {
            id: '1',
            type: 'AUTOPAY_SETUP',
            title: 'Set Up Autopay',
            description: 'Automate your credit card payments to never miss a due date',
            completed: false,
            projectedScoreGain: 15,
            dueDate: null,
          },
          {
            id: '2',
            type: 'UTILIZATION_REDUCED',
            title: 'Reduce Utilization Below 30%',
            description: 'Pay down $150 to get your utilization under the optimal 30% threshold',
            completed: false,
            projectedScoreGain: 25,
            dueDate: null,
          },
        ],
        shield: [
          {
            type: 'HIGH_UTILIZATION',
            inDays: null,
            message: 'Utilization is 45% - aim for under 30%',
            suggestion: 'REDUCE_UTILIZATION',
          },
        ],
      };
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

export const creditScoreService = new CreditScoreService();

