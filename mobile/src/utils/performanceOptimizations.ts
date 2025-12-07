/**
 * Performance Optimization Utilities
 * 
 * Centralized performance optimizations for React components, queries, and rendering.
 */

import React from 'react';
import { QueryHookOptions } from '@apollo/client';
import { useMemo, useCallback, DependencyList } from 'react';

// ============================================================================
// GraphQL Query Optimization
// ============================================================================

/**
 * Optimized query options for data that changes infrequently
 * (e.g., user settings, strategy definitions)
 */
export const stableQueryOptions: QueryHookOptions<any, any> = {
  fetchPolicy: 'cache-first',
  nextFetchPolicy: 'cache-first',
  notifyOnNetworkStatusChange: false,
  errorPolicy: 'all',
};

/**
 * Optimized query options for real-time data
 * (e.g., prices, signals, orders)
 */
export const realtimeQueryOptions: QueryHookOptions<any, any> = {
  fetchPolicy: 'cache-and-network',
  nextFetchPolicy: 'cache-first',
  notifyOnNetworkStatusChange: true,
  errorPolicy: 'all',
  pollInterval: 30000, // Poll every 30 seconds
};

/**
 * Optimized query options for one-time fetches
 * (e.g., backtest results, historical data)
 */
export const oneTimeQueryOptions: QueryHookOptions<any, any> = {
  fetchPolicy: 'network-only',
  nextFetchPolicy: 'cache-first',
  notifyOnNetworkStatusChange: false,
  errorPolicy: 'all',
};

/**
 * Optimized query options for paginated lists
 */
export const paginatedQueryOptions: QueryHookOptions<any, any> = {
  fetchPolicy: 'cache-and-network',
  nextFetchPolicy: 'cache-first',
  notifyOnNetworkStatusChange: false,
  errorPolicy: 'all',
};

// ============================================================================
// React Component Optimization
// ============================================================================

/**
 * Memoized callback factory - prevents unnecessary re-renders
 */
export function useStableCallback<T extends (...args: any[]) => any>(
  callback: T,
  deps: DependencyList
): T {
  return useCallback(callback, deps) as T;
}

/**
 * Memoized value factory - prevents unnecessary recalculations
 */
export function useStableMemo<T>(
  factory: () => T,
  deps: DependencyList
): T {
  return useMemo(factory, deps);
}

/**
 * Debounce utility for expensive operations
 */
export function useDebounce<T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  deps: DependencyList
): T {
  const timeoutRef = React.useRef<NodeJS.Timeout>();
  
  return useCallback(
    ((...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(() => {
        callback(...args);
      }, delay);
    }) as T,
    [delay, ...deps]
  );
}

// ============================================================================
// List Rendering Optimization
// ============================================================================

/**
 * Optimized FlatList props for large lists
 */
export const optimizedFlatListProps = {
  removeClippedSubviews: true,
  initialNumToRender: 10,
  maxToRenderPerBatch: 5,
  windowSize: 10,
  updateCellsBatchingPeriod: 50,
  getItemLayout: undefined as ((data: any, index: number) => {
    length: number;
    offset: number;
    index: number;
  }) | undefined,
};

/**
 * Calculate item layout for FlatList (if items have fixed height)
 */
export function createItemLayout(itemHeight: number) {
  return (_: any, index: number) => ({
    length: itemHeight,
    offset: itemHeight * index,
    index,
  });
}

// ============================================================================
// Cache Key Generation
// ============================================================================

/**
 * Generate stable cache keys for memoization
 */
export function generateCacheKey(prefix: string, ...args: any[]): string {
  return `${prefix}_${args.map(arg => 
    typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
  ).join('_')}`;
}

// ============================================================================
// Performance Monitoring
// ============================================================================

/**
 * Measure component render time (dev only)
 */
export function useRenderTime(componentName: string) {
  if (__DEV__) {
    const renderStart = useMemo(() => Date.now(), []);
    React.useEffect(() => {
      const renderTime = Date.now() - renderStart;
      if (renderTime > 16) { // Warn if render takes longer than one frame (16ms)
        console.warn(`⚠️ [PERF] ${componentName} render took ${renderTime}ms`);
      }
    }, [componentName, renderStart]);
  }
}

/**
 * Measure async operation time
 */
export async function measureAsync<T>(
  operation: () => Promise<T>,
  label: string
): Promise<T> {
  const start = Date.now();
  try {
    const result = await operation();
    const duration = Date.now() - start;
    if (__DEV__ && duration > 100) {
      console.warn(`⚠️ [PERF] ${label} took ${duration}ms`);
    }
    return result;
  } catch (error) {
    const duration = Date.now() - start;
    console.error(`❌ [PERF] ${label} failed after ${duration}ms:`, error);
    throw error;
  }
}

