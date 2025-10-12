/**
 * Performance Timing Utilities
 * For measuring and logging performance metrics
 */

import { ENABLE_PERFORMANCE_LOGGING } from '../config/flags';

export interface TimingResult {
  label: string;
  ms: number;
  timestamp: number;
}

/**
 * Create a timing marker that returns a stop function
 */
export const mark = (label: string): (() => TimingResult) => {
  const startTime = Date.now();
  const timestamp = startTime;
  
  return (): TimingResult => {
    const duration = Date.now() - startTime;
    const result = { label, ms: duration, timestamp };
    
    if (ENABLE_PERFORMANCE_LOGGING) {
      console.log(`[PERF] ${label}: ${duration}ms`);
    }
    
    return result;
  };
};

/**
 * Measure the execution time of an async function
 */
export const measureAsync = async <T>(
  label: string,
  fn: () => Promise<T>
): Promise<{ result: T; timing: TimingResult }> => {
  const stop = mark(label);
  try {
    const result = await fn();
    const timing = stop();
    return { result, timing };
  } catch (error) {
    const timing = stop();
    if (ENABLE_PERFORMANCE_LOGGING) {
      console.error(`[PERF] ${label} failed after ${timing.ms}ms:`, error);
    }
    throw error;
  }
};

/**
 * Measure the execution time of a synchronous function
 */
export const measureSync = <T>(
  label: string,
  fn: () => T
): { result: T; timing: TimingResult } => {
  const stop = mark(label);
  try {
    const result = fn();
    const timing = stop();
    return { result, timing };
  } catch (error) {
    const timing = stop();
    if (ENABLE_PERFORMANCE_LOGGING) {
      console.error(`[PERF] ${label} failed after ${timing.ms}ms:`, error);
    }
    throw error;
  }
};

/**
 * Create a performance tracker for multiple related operations
 */
export class PerformanceTracker {
  private timings: TimingResult[] = [];
  private startTime: number;

  constructor(private label: string) {
    this.startTime = Date.now();
  }

  mark(subLabel: string): () => void {
    const startTime = Date.now();
    return () => {
      const duration = Date.now() - startTime;
      const timing: TimingResult = {
        label: `${this.label}.${subLabel}`,
        ms: duration,
        timestamp: Date.now(),
      };
      this.timings.push(timing);
      
      if (ENABLE_PERFORMANCE_LOGGING) {
        console.log(`[PERF] ${timing.label}: ${duration}ms`);
      }
    };
  }

  finish(): TimingResult[] {
    const totalDuration = Date.now() - this.startTime;
    const totalTiming: TimingResult = {
      label: `${this.label}.total`,
      ms: totalDuration,
      timestamp: Date.now(),
    };
    
    this.timings.push(totalTiming);
    
    if (ENABLE_PERFORMANCE_LOGGING) {
      console.log(`[PERF] ${totalTiming.label}: ${totalDuration}ms`);
      console.log(`[PERF] ${this.label} breakdown:`, this.timings);
    }
    
    return this.timings;
  }
}

/**
 * Log performance metrics to analytics service (if available)
 */
export const logPerformanceMetrics = (timings: TimingResult[]) => {
  if (!ENABLE_PERFORMANCE_LOGGING) return;
  
  // In production, you might want to send these to your analytics service
  // For now, just log them
  console.log('[PERF] Performance metrics:', timings);
  
  // Example: Send to analytics service
  // analytics.track('performance_metrics', {
  //   timings: timings.map(t => ({ label: t.label, duration: t.ms })),
  //   timestamp: Date.now(),
  // });
};

/**
 * Common performance markers for the app
 */
export const PerformanceMarkers = {
  LOGIN_TO_HOME: 'login->home',
  LOGIN_AUTH: 'login.auth',
  LOGIN_NAVIGATION: 'login.navigation',
  HOME_LOAD: 'home.load',
  PORTFOLIO_METRICS: 'portfolio.metrics',
  MARKET_DATA_FETCH: 'market_data.fetch',
  GRAPHQL_QUERY: 'graphql.query',
  SCREEN_NAVIGATION: 'screen.navigation',
} as const;
