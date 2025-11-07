/**
 * Gesture Analytics Service
 * Tracks user interactions with Constellation Orb gestures
 */

import { logUX } from '../../../utils/telemetry';
import AsyncStorage from '@react-native-async-storage/async-storage';

export type GestureType = 
  | 'tap' 
  | 'double_tap' 
  | 'long_press' 
  | 'swipe_left' 
  | 'swipe_right' 
  | 'pinch';

export interface GestureEvent {
  gesture: GestureType;
  timestamp: number;
  snapshot?: {
    netWorth: number;
    hasPositions: boolean;
    cashflowDelta: number;
  };
  sessionId?: string;
}

class GestureAnalyticsService {
  private sessionId: string;
  private gestureCounts: Map<GestureType, number> = new Map();
  private sessionStartTime: number;

  constructor() {
    this.sessionId = this.generateSessionId();
    this.sessionStartTime = Date.now();
    this.initializeCounts();
  }

  private generateSessionId(): string {
    return `gesture_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private initializeCounts(): void {
    const gestures: GestureType[] = ['tap', 'double_tap', 'long_press', 'swipe_left', 'swipe_right', 'pinch'];
    gestures.forEach(gesture => this.gestureCounts.set(gesture, 0));
  }

  /**
   * Track a gesture event
   */
  public trackGesture(
    gesture: GestureType,
    snapshot?: {
      netWorth: number;
      hasPositions: boolean;
      cashflowDelta: number;
    }
  ): void {
    try {
      const count = (this.gestureCounts.get(gesture) || 0) + 1;
      this.gestureCounts.set(gesture, count);

      const event: GestureEvent = {
        gesture,
        timestamp: Date.now(),
        snapshot,
        sessionId: this.sessionId,
      };

      // Log to telemetry
      logUX('constellation_orb_gesture', {
        gesture,
        count,
        sessionId: this.sessionId,
        timeSinceSessionStart: Date.now() - this.sessionStartTime,
        ...(snapshot && {
          netWorth: snapshot.netWorth,
          hasPositions: snapshot.hasPositions,
          cashflowDelta: snapshot.cashflowDelta,
        }),
      });

      // Store locally for analytics
      this.storeGestureEvent(event);

      // In production, you might want to batch and send to analytics service
      if (__DEV__) {
        console.log(`[GestureAnalytics] ${gesture} (count: ${count})`, event);
      }
    } catch (error) {
      // Don't let analytics break the app
      if (__DEV__) {
        console.warn('Gesture analytics error:', error);
      }
    }
  }

  /**
   * Store gesture event locally
   */
  private async storeGestureEvent(event: GestureEvent): Promise<void> {
    try {
      const key = `gesture_${event.gesture}_${event.timestamp}`;
      await AsyncStorage.setItem(key, JSON.stringify(event));
      
      // Clean up old events (keep last 100)
      await this.cleanupOldEvents();
    } catch (error) {
      // Silently fail
    }
  }

  /**
   * Clean up old gesture events
   */
  private async cleanupOldEvents(): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const gestureKeys = keys.filter(k => k.startsWith('gesture_'));
      
      if (gestureKeys.length > 100) {
        // Sort by timestamp and remove oldest
        const sortedKeys = gestureKeys.sort();
        const keysToRemove = sortedKeys.slice(0, gestureKeys.length - 100);
        await AsyncStorage.multiRemove(keysToRemove);
      }
    } catch (error) {
      // Silently fail
    }
  }

  /**
   * Get gesture statistics for current session
   */
  public getSessionStats(): {
    totalGestures: number;
    gestureBreakdown: Record<GestureType, number>;
    sessionDuration: number;
  } {
    const totalGestures = Array.from(this.gestureCounts.values()).reduce((a, b) => a + b, 0);
    const gestureBreakdown: Record<GestureType, number> = {
      tap: this.gestureCounts.get('tap') || 0,
      double_tap: this.gestureCounts.get('double_tap') || 0,
      long_press: this.gestureCounts.get('long_press') || 0,
      swipe_left: this.gestureCounts.get('swipe_left') || 0,
      swipe_right: this.gestureCounts.get('swipe_right') || 0,
      pinch: this.gestureCounts.get('pinch') || 0,
    };

    return {
      totalGestures,
      gestureBreakdown,
      sessionDuration: Date.now() - this.sessionStartTime,
    };
  }

  /**
   * Reset session
   */
  public resetSession(): void {
    this.sessionId = this.generateSessionId();
    this.sessionStartTime = Date.now();
    this.initializeCounts();
  }
}

// Export singleton instance
export const gestureAnalyticsService = new GestureAnalyticsService();
export default gestureAnalyticsService;

