/**
 * Analytics Service
 * Centralized analytics tracking for key moments feature
 */

import type { MomentAnalyticsEvent } from "../components/charts/MomentStoryPlayer";

// Analytics backend configuration
const ANALYTICS_ENABLED = true; // Feature flag
const ANALYTICS_API_URL = process.env.EXPO_PUBLIC_ANALYTICS_API_URL || "";

// In-memory queue for offline support
let eventQueue: MomentAnalyticsEvent[] = [];
const MAX_QUEUE_SIZE = 100;

/**
 * Track an analytics event
 */
export async function trackMomentEvent(
  event: MomentAnalyticsEvent,
  metadata?: Record<string, any>
): Promise<void> {
  if (!ANALYTICS_ENABLED) {
    return;
  }

  const enrichedEvent = {
    ...event,
    timestamp: new Date().toISOString(),
    metadata: metadata || {},
  };

  // Add to queue
  eventQueue.push(enrichedEvent);

  // Prevent queue overflow
  if (eventQueue.length > MAX_QUEUE_SIZE) {
    eventQueue.shift(); // Remove oldest
  }

  // Try to send immediately (fire and forget)
  sendEvent(enrichedEvent).catch((error) => {
    console.warn("[Analytics] Failed to send event, will retry later:", error);
    // Event is already in queue, will be retried on flush
  });
}

/**
 * Send event to analytics backend
 */
async function sendEvent(event: MomentAnalyticsEvent & { timestamp: string; metadata: Record<string, any> }): Promise<void> {
  if (!ANALYTICS_API_URL) {
    // No backend configured, just log
    console.log("[Analytics] Event:", event);
    return;
  }

  try {
    const response = await fetch(`${ANALYTICS_API_URL}/events`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(event),
    });

    if (!response.ok) {
      throw new Error(`Analytics API returned ${response.status}`);
    }
  } catch (error) {
    throw error; // Re-throw to be caught by caller
  }
}

/**
 * Flush queued events (call on app foreground, network reconnect, etc.)
 */
export async function flushAnalyticsQueue(): Promise<void> {
  if (eventQueue.length === 0 || !ANALYTICS_API_URL) {
    return;
  }

  const eventsToSend = [...eventQueue];
  eventQueue = []; // Clear queue

  try {
    const response = await fetch(`${ANALYTICS_API_URL}/events/batch`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ events: eventsToSend }),
    });

    if (!response.ok) {
      // Re-queue failed events
      eventQueue.unshift(...eventsToSend);
      throw new Error(`Analytics batch API returned ${response.status}`);
    }

    console.log(`[Analytics] Flushed ${eventsToSend.length} events`);
  } catch (error) {
    console.warn("[Analytics] Failed to flush queue:", error);
    // Re-queue failed events
    eventQueue.unshift(...eventsToSend);
  }
}

/**
 * Calculate high-value metrics from events
 */
export interface MomentMetrics {
  storyCompletionRate: number; // listened / total
  avgMomentsListened: number;
  totalStoriesOpened: number;
  mostPlayedSymbols: Array<{ symbol: string; count: number }>;
}

/**
 * Get metrics for a symbol (would typically come from backend)
 */
export async function getMomentMetrics(symbol: string): Promise<MomentMetrics | null> {
  if (!ANALYTICS_API_URL) {
    return null;
  }

  try {
    const response = await fetch(`${ANALYTICS_API_URL}/metrics/${symbol}`);
    if (!response.ok) {
      return null;
    }
    return await response.json();
  } catch (error) {
    console.warn("[Analytics] Failed to fetch metrics:", error);
    return null;
  }
}

/**
 * Track a story session (helper for common pattern)
 */
export function trackStorySession(
  symbol: string,
  totalMoments: number,
  listenedCount: number,
  durationMs?: number
): void {
  const completionRate = totalMoments > 0 ? listenedCount / totalMoments : 0;
  
  trackMomentEvent(
    {
      type: "story_close",
      symbol,
      totalMoments,
      listenedCount,
    },
    {
      completionRate,
      durationMs,
    }
  );
}

