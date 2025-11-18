/**
 * Configuration constants for stocks feature
 */

// Polling intervals (in milliseconds)
export const POLLING_INTERVALS = {
  ORDERS: 30_000, // 30 seconds
  QUOTES: 10_000, // 10 seconds
  POSITIONS: 60_000, // 1 minute
} as const;

// Timeout values (in milliseconds)
export const TIMEOUTS = {
  QUOTE_FETCH: 5000, // 5 seconds
  RESEARCH_LOADING: 3000, // 3 seconds
  STOCK_MOMENTS: 1500, // 1.5 seconds
  NETWORK_REQUEST: 3000, // 3 seconds
  GRAPHQL_OPERATION: 5000, // 5 seconds
} as const;

// Cache TTL values (in milliseconds)
export const CACHE_TTL = {
  QUOTES: 10_000, // 10 seconds
  ACCOUNT: 60_000, // 1 minute
  POSITIONS: 30_000, // 30 seconds
  ORDERS: 15_000, // 15 seconds
} as const;

// Debounce delays (in milliseconds)
export const DEBOUNCE_DELAYS = {
  SYMBOL_SEARCH: 250,
  QUOTE_FETCH: 500,
} as const;

