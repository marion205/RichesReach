/**
 * Feature Flags Configuration
 * Controls which features are enabled based on environment variables
 */

export const FEATURE_PORTFOLIO_METRICS =
  (process.env.EXPO_PUBLIC_FEATURE_PORTFOLIO_METRICS ?? 'false') === 'true';

export const FEATURE_REAL_TIME_MARKET_DATA =
  (process.env.EXPO_PUBLIC_FEATURE_REAL_TIME_MARKET_DATA ?? 'false') === 'true';

export const FEATURE_OPTIONS_TRADING =
  (process.env.EXPO_PUBLIC_FEATURE_OPTIONS_TRADING ?? 'false') === 'true';

export const FEATURE_AI_SCANS =
  (process.env.EXPO_PUBLIC_FEATURE_AI_SCANS ?? 'false') === 'true';

export const FEATURE_TAX_OPTIMIZATION =
  (process.env.EXPO_PUBLIC_FEATURE_TAX_OPTIMIZATION ?? 'false') === 'true';

// Performance and reliability flags
export const ENABLE_GRAPHQL_TIMEOUTS = true;
export const GRAPHQL_TIMEOUT_MS = 15000; // 15 seconds (increased for slow queries)
export const GRAPHQL_SLOW_QUERY_TIMEOUT_MS = 30000; // 30 seconds for slow operations
export const MARKET_DATA_HEALTH_CHECK_TIMEOUT = 3000; // 3 seconds

// Development flags
export const ENABLE_PERFORMANCE_LOGGING = __DEV__;
export const ENABLE_DEBUG_QUERIES = __DEV__;
