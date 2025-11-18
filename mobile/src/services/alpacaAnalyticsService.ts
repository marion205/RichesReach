/**
 * Alpaca Connect Analytics Service
 * Tracks OAuth connection flow and success rates
 */

import { logUX } from '../utils/telemetry';

export interface AlpacaConnectEvent {
  event: 
    | 'connect_initiated'
    | 'connect_modal_shown'
    | 'connect_has_account_yes'
    | 'connect_has_account_no'
    | 'connect_oauth_started'
    | 'connect_oauth_success'
    | 'connect_oauth_error'
    | 'connect_signup_redirected'
    | 'connect_signup_completed'
    | 'connect_account_linked'
    | 'connect_failed';
  userId?: string;
  timestamp: number;
  metadata?: {
    error?: string;
    errorCode?: string;
    hasAccount?: boolean;
    signupSource?: 'modal' | 'redirect';
    oauthState?: string;
    accountId?: string;
    source?: string; // e.g., 'order_placement'
    action?: string; // e.g., 'opened', 'closed'
  };
}

class AlpacaAnalyticsService {
  private events: AlpacaConnectEvent[] = [];
  private sessionId: string;

  constructor() {
    this.sessionId = `alpaca_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Track Alpaca connect event
   */
  track(event: AlpacaConnectEvent['event'], metadata?: AlpacaConnectEvent['metadata']): void {
    const connectEvent: AlpacaConnectEvent = {
      event,
      timestamp: Date.now(),
      metadata: {
        ...metadata,
        sessionId: this.sessionId,
      },
    };

    // Add to local queue
    this.events.push(connectEvent);

    // Log to telemetry
    logUX(`alpaca_connect_${event}`, {
      sessionId: this.sessionId,
      ...metadata,
    });

    // In production, send to analytics backend
    if (__DEV__) {
      console.log(`[AlpacaAnalytics] ${event}`, metadata);
    }
  }

  /**
   * Get connection success rate for current session
   */
  getSuccessRate(): number {
    const initiated = this.events.filter(e => e.event === 'connect_initiated').length;
    const succeeded = this.events.filter(e => e.event === 'connect_oauth_success' || e.event === 'connect_account_linked').length;
    
    if (initiated === 0) return 0;
    return succeeded / initiated;
  }

  /**
   * Get events for debugging
   */
  getEvents(): AlpacaConnectEvent[] {
    return [...this.events];
  }

  /**
   * Clear events (e.g., on logout)
   */
  clear(): void {
    this.events = [];
    this.sessionId = `alpaca_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get analytics summary
   */
  getSummary() {
    const events = this.events;
    return {
      totalAttempts: events.filter(e => e.event === 'connect_initiated').length,
      hasAccountCount: events.filter(e => e.event === 'connect_has_account_yes').length,
      noAccountCount: events.filter(e => e.event === 'connect_has_account_no').length,
      oauthStarted: events.filter(e => e.event === 'connect_oauth_started').length,
      oauthSuccess: events.filter(e => e.event === 'connect_oauth_success').length,
      oauthErrors: events.filter(e => e.event === 'connect_oauth_error').length,
      signupRedirects: events.filter(e => e.event === 'connect_signup_redirected').length,
      accountLinked: events.filter(e => e.event === 'connect_account_linked').length,
      successRate: this.getSuccessRate(),
      sessionId: this.sessionId,
    };
  }
}

// Singleton instance
export const alpacaAnalytics = new AlpacaAnalyticsService();

