/**
 * Optimized GraphQL Query Options
 * 
 * Provides standardized, performance-optimized query options for Apollo Client.
 * These options prioritize cache usage to reduce unnecessary network requests
 * and improve app responsiveness.
 */

import { QueryHookOptions } from '@apollo/client';

/**
 * Standard optimized query options for most use cases.
 * Uses cache-first policy to minimize network requests.
 */
export const optimizedQueryOptions = {
  fetchPolicy: 'cache-first' as const,
  nextFetchPolicy: 'cache-first' as const,
  notifyOnNetworkStatusChange: false,
  errorPolicy: 'all' as const,
};

/**
 * Options for queries that need fresh data on first load.
 * Still uses cache-first but will fetch if cache is stale.
 */
export const freshQueryOptions = {
  fetchPolicy: 'cache-first' as const,
  nextFetchPolicy: 'cache-first' as const,
  notifyOnNetworkStatusChange: false,
  errorPolicy: 'all' as const,
};

/**
 * Options for queries that should always fetch fresh data (e.g., on pull-to-refresh).
 * Use this sparingly for manual refresh operations.
 */
export const networkOnlyOptions = {
  fetchPolicy: 'network-only' as const,
  errorPolicy: 'all' as const,
};

/**
 * Helper function to create optimized query options with custom overrides.
 */
export function createOptimizedOptions<T>(
  overrides?: Partial<QueryHookOptions<T>>
): QueryHookOptions<T> {
  return {
    ...optimizedQueryOptions,
    ...overrides,
  };
}

/**
 * Helper function for queries that need to show loading state updates.
 * Use this when you need to show loading indicators during refetches.
 */
export function createOptimizedOptionsWithLoading<T>(
  overrides?: Partial<QueryHookOptions<T>>
): QueryHookOptions<T> {
  return {
    ...optimizedQueryOptions,
    notifyOnNetworkStatusChange: true,
    ...overrides,
  };
}

