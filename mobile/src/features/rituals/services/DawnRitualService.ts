/**
 * Dawn Ritual Service (Ritual Dawn)
 * Handles API communication for the tactical morning check-in.
 * Fetches portfolio snapshot, market context, and action suggestions.
 * Retains legacy performDawnRitual() for backward compatibility.
 */

import { API_HTTP } from '../../../config/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import logger from '../../../utils/logger';
import type { RitualDawnResult } from '../types/RitualDawnTypes';

// Legacy interface (kept for backward compat)
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
   * Perform the Ritual Dawn: portfolio snapshot, market context, action suggestion.
   * This is the primary method for the new 5-phase experience.
   */
  async performRitualDawn(): Promise<RitualDawnResult> {
    try {
      const headers = await this.getAuthHeaders();
      const clientHour = new Date().getHours();

      const response = await fetch(`${this.baseUrl}/perform`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ client_hour: clientHour }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      logger.error('[RitualDawn] Failed to fetch ritual data:', error);
      return this.getFallbackRitualData();
    }
  }

  /**
   * Record the user's commitment action. Pass greetingKey for A/B analysis.
   */
  async completeRitualDawn(commitmentAction: string, greetingKey?: string | null): Promise<void> {
    try {
      const headers = await this.getAuthHeaders();
      await fetch(`${this.baseUrl}/complete`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          action_taken: commitmentAction,
          greeting_key: greetingKey ?? undefined,
        }),
      });
    } catch (error) {
      logger.error('[RitualDawn] Failed to record completion:', error);
    }
  }

  /**
   * Report that the user opened a target screen (follow-through on ritual commitment).
   * Call when user navigates to e.g. StockDetail with a symbol after committing "I'll review AAPL today".
   */
  async recordFollowThrough(targetScreen: string, targetParams?: Record<string, string>): Promise<void> {
    try {
      const headers = await this.getAuthHeaders();
      const res = await fetch(`${this.baseUrl}/follow-through`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          target_screen: targetScreen,
          target_params: targetParams ?? {},
        }),
      });
      if (!res.ok) return;
      const data = await res.json();
      if (data.recorded) {
        logger.log('[RitualDawn] Follow-through recorded:', targetScreen, targetParams);
      }
    } catch (error) {
      logger.warn('[RitualDawn] Follow-through request failed:', error);
    }
  }

  /**
   * Legacy: Perform the dawn ritual (old API shape).
   * Kept for backward compatibility.
   */
  async performDawnRitual(): Promise<DawnRitualResult> {
    try {
      const headers = await this.getAuthHeaders();
      const clientHour = new Date().getHours();

      const response = await fetch(`${this.baseUrl}/perform`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ client_hour: clientHour }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        transactionsSynced: data.transactionsSynced ?? 0,
        haiku: data.haiku ?? this.getFallbackHaiku(),
        timestamp: data.timestamp ?? new Date().toISOString(),
      };
    } catch (error) {
      logger.error('[DawnRitual] Failed to perform ritual:', error);
      return {
        transactionsSynced: 0,
        haiku: this.getFallbackHaiku(),
        timestamp: new Date().toISOString(),
      };
    }
  }

  /**
   * Fallback data when the API is unreachable.
   */
  private getFallbackRitualData(): RitualDawnResult {
    return {
      greeting: 'Good morning. Your money didn\'t sleep.',
      tagline: 'Let\'s see what changed overnight.',
      portfolio: {
        total_value: 0,
        previous_total_value: 0,
        change_dollars: 0,
        change_percent: 0,
        top_holdings: [],
        holdings_count: 0,
        has_portfolio: false,
      },
      market: {
        sp500_change_percent: 0,
        sp500_direction: 'flat',
        market_sentiment: 'neutral',
        notable_indices: [],
        headline: 'Market data is currently unavailable.',
        volatility_level: 'moderate',
      },
      action: {
        action_type: 'no_action',
        headline: 'Start your day with awareness.',
        detail: 'Review your portfolio when you\'re ready.',
        action_label: 'Open portfolio',
        target_screen: 'portfolio-management',
        urgency: 'low',
      },
      streak: 0,
      timestamp: new Date().toISOString(),
      transactionsSynced: 0,
      haiku: this.getFallbackHaiku(),
    };
  }

  /**
   * Legacy fallback haiku.
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
   * Get auth headers.
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
