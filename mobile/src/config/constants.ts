/**
 * Application Constants
 * Centralized constants to avoid magic numbers and improve maintainability
 */

// Timing Constants
export const TIMING = {
  // Polling intervals (in milliseconds)
  POLLING_INTERVAL_SHORT: 1000,      // 1 second
  POLLING_INTERVAL_MEDIUM: 5000,     // 5 seconds
  POLLING_INTERVAL_LONG: 30000,      // 30 seconds
  POLLING_INTERVAL_VERY_LONG: 60000, // 60 seconds
  
  // Navigation delays
  NAVIGATION_DELAY: 50,              // 50ms for navigation setup
  NAVIGATION_POLL_INTERVAL: 50,      // 50ms for navigation polling
  
  // Animation durations
  ANIMATION_DURATION_SHORT: 300,     // 300ms
  ANIMATION_DURATION_MEDIUM: 500,     // 500ms
  ANIMATION_DURATION_LONG: 800,      // 800ms
  
  // Timeout values
  TIMEOUT_SHORT: 3000,                // 3 seconds
  TIMEOUT_MEDIUM: 5000,               // 5 seconds
  TIMEOUT_LONG: 10000,                // 10 seconds
  TIMEOUT_VERY_LONG: 30000,           // 30 seconds
  
  // Debounce delays
  DEBOUNCE_SHORT: 300,                // 300ms
  DEBOUNCE_MEDIUM: 500,               // 500ms
  DEBOUNCE_LONG: 1000,                // 1 second
} as const;

// API Constants
export const API = {
  // Retry settings
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000,                  // 1 second
  
  // Timeout settings
  REQUEST_TIMEOUT: 8000,              // 8 seconds
  GRAPHQL_TIMEOUT: 8000,              // 8 seconds
  
  // Cache TTL (in milliseconds)
  CACHE_TTL_SHORT: 60000,             // 1 minute
  CACHE_TTL_MEDIUM: 300000,           // 5 minutes
  CACHE_TTL_LONG: 86400000,           // 24 hours
} as const;

// UI Constants
export const UI = {
  // Screen dimensions
  HEADER_HEIGHT: 60,
  TAB_BAR_HEIGHT: 50,
  
  // Spacing
  SPACING_XS: 4,
  SPACING_SM: 8,
  SPACING_MD: 16,
  SPACING_LG: 24,
  SPACING_XL: 32,
  
  // Border radius
  RADIUS_SM: 8,
  RADIUS_MD: 12,
  RADIUS_LG: 16,
  RADIUS_XL: 24,
  
  // Opacity
  OPACITY_DISABLED: 0.5,
  OPACITY_PRESSED: 0.7,
} as const;

// Security Constants
export const SECURITY = {
  // Score thresholds
  SCORE_EXCELLENT: 90,
  SCORE_GOOD: 70,
  SCORE_FAIR: 50,
  
  // Polling intervals
  SECURITY_EVENTS_POLL_INTERVAL: 30000, // 30 seconds
} as const;

// Performance Constants
export const PERFORMANCE = {
  // Memory thresholds (in MB)
  MEMORY_WARNING_THRESHOLD: 100,
  MEMORY_CRITICAL_THRESHOLD: 200,
  
  // Monitoring intervals
  MEMORY_MONITOR_INTERVAL: 30000,     // 30 seconds
  PERFORMANCE_MONITOR_INTERVAL: 60000, // 60 seconds
} as const;

// Animation Constants
export const ANIMATION = {
  // Scale values
  SCALE_NORMAL: 1,
  SCALE_PRESSED: 0.95,
  SCALE_PULSE_MIN: 1,
  SCALE_PULSE_MAX: 1.1,
  
  // Opacity values
  OPACITY_HIDDEN: 0,
  OPACITY_VISIBLE: 1,
  OPACITY_DISABLED: 0.5,
} as const;

// Validation Constants
export const VALIDATION = {
  // Input limits
  MIN_PASSWORD_LENGTH: 8,
  MAX_PASSWORD_LENGTH: 128,
  MIN_USERNAME_LENGTH: 3,
  MAX_USERNAME_LENGTH: 30,
  
  // Trading limits
  MIN_TRADE_AMOUNT: 1,
  MAX_TRADE_AMOUNT: 1000000,
} as const;

// Feature Flags (for quick reference)
export const FEATURES = {
  // Development flags
  ENABLE_DEBUG_LOGGING: __DEV__,
  ENABLE_PERFORMANCE_MONITORING: __DEV__,
} as const;

