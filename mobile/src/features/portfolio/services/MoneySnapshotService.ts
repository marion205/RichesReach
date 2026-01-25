/**
 * Money Snapshot Service
 * Fetches unified financial snapshot (bank + portfolio + cash flow)
 */

import { API_HTTP } from '../../../config/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import logger from '../../../utils/logger';

export interface MoneySnapshot {
  netWorth: number;
  cashflow: {
    period: string;
    in: number;
    out: number;
    delta: number;
  };
  positions: Array<{
    symbol: string;
    value: number;
    shares: number;
  }>;
  shield: Array<{
    type: 'LOW_BALANCE' | 'BILL_DUE' | 'RISKY_ORDER';
    inDays: number | null;
    suggestion: string;
    message: string;
  }>;
  breakdown: {
    bankBalance: number;
    portfolioValue: number;
    bankAccountsCount: number;
  };
  credit?: {
    score: number;
    scoreRange: 'Poor' | 'Fair' | 'Good' | 'Very Good' | 'Excellent';
    lastUpdated: string;
    provider: string;
    utilization?: number;
    projection?: {
      scoreGain6m: number;
      topAction: string;
      confidence: number;
    };
  };
}

class MoneySnapshotService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_HTTP}/api/money`;
  }

  /**
   * Fetch unified money snapshot
   */
  async getSnapshot(): Promise<MoneySnapshot> {
    try {
      // Get auth token from AsyncStorage
      const token = await AsyncStorage.getItem('token') || await AsyncStorage.getItem('authToken');
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${this.baseUrl}/snapshot`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      logger.error('Failed to fetch money snapshot:', error);
      throw error;
    }
  }

  /**
   * Check if user has bank accounts linked
   */
  async hasBankLinked(): Promise<boolean> {
    try {
      const snapshot = await this.getSnapshot();
      return snapshot.breakdown.bankAccountsCount > 0;
    } catch (error) {
      logger.error('Failed to check bank link status:', error);
      return false;
    }
  }
}

// Export singleton instance
export const moneySnapshotService = new MoneySnapshotService();
export default moneySnapshotService;

