/**
 * Dawn Ritual Service
 * Handles Yodlee transaction syncing and haiku generation
 */

import { API_HTTP } from '../../../config/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import logger from '../../../utils/logger';

export interface DawnRitualResult {
  transactionsSynced: number;
  haiku: string;
  timestamp: string;
}

class DawnRitualService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_HTTP}/api/rituals/dawn`;
  }

  /**
   * Perform the dawn ritual: sync transactions and get haiku
   */
  async performDawnRitual(): Promise<DawnRitualResult> {
    try {
      const headers = await this.getAuthHeaders();
      
      const response = await fetch(`${this.baseUrl}/perform`, {
        method: 'POST',
        headers,
        body: JSON.stringify({}),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      logger.error('[DawnRitual] Failed to perform ritual:', error);
      // Return fallback haiku if sync fails
      return {
        transactionsSynced: 0,
        haiku: this.getFallbackHaiku(),
        timestamp: new Date().toISOString(),
      };
    }
  }

  /**
   * Get fallback haiku if API fails
   */
  private getFallbackHaiku(): string {
    const haikus = [
      "From grocery shadows to investment light\nYour wealth awakens, bold and bright.",
      "Each transaction, a seed in the ground\nWatch your fortune grow, without a sound.",
      "Morning sun rises, accounts align\nFinancial freedom, truly divine.",
      "Small steps today, mountains tomorrow\nYour wealth path, no need to borrow.",
      "Dawn breaks through, clearing the way\nYour financial future, bright as day.",
    ];
    return haikus[Math.floor(Math.random() * haikus.length)];
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

export const dawnRitualService = new DawnRitualService();

