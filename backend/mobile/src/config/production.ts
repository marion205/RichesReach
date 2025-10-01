// Production Configuration
export const PRODUCTION_CONFIG = {
  API_BASE_URL: 'https://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com',
  GRAPHQL_URL: 'https://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com/graphql/',
  WS_URL: 'wss://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com/ws/',
  ENABLE_ANALYTICS: true,
  ENABLE_ERROR_REPORTING: true,
  ENABLE_PERFORMANCE_MONITORING: true,
  LOG_LEVEL: 'error' as const,
  CACHE_TTL: 300000, // 5 minutes
  MAX_RETRIES: 3,
  TIMEOUT: 10000,
  LOGGING: {
    MAX_LOG_SIZE: 1000,
    MAX_ERROR_ENTRIES: 100,
    ENABLE_CONSOLE_LOGGING: false,
    ENABLE_REMOTE_LOGGING: true,
  },
  ANALYTICS: {
    ENABLED: true,
    GOOGLE_ANALYTICS_ID: 'GA-XXXXXXXXX',
    MIXPANEL_TOKEN: 'mixpanel-token',
  },
  ERROR_REPORTING: {
    ENABLED: true,
    SENTRY_DSN: 'https://your-sentry-dsn@sentry.io/project-id',
    FILTER_SENSITIVE_DATA: true,
  },
  SECURITY: {
    ENABLE_SSL_PINNING: true,
    ENABLE_CERTIFICATE_PINNING: true,
    MAX_LOGIN_ATTEMPTS: 5,
    LOCKOUT_DURATION: 300000, // 5 minutes
    TOKEN_REFRESH_INTERVAL: 3600000, // 1 hour
  },
  FEATURES: {
    ENABLE_CRYPTO: true,
    ENABLE_OPTIONS: true,
    ENABLE_SOCIAL: true,
    ENABLE_AI_PORTFOLIO: true,
    ENABLE_LEARNING: true,
    ENABLE_PERFORMANCE_MONITORING: true,
    ENABLE_BIOMETRIC_AUTH: true,
  },
};

export const PRODUCTION_UTILS = {
  logError: (error: any) => console.error('Production Error:', error),
  logPerformance: (metric: string, value: number) => console.log(`Performance: ${metric} = ${value}ms`),
  sanitizeData: (data: any) => data, // Placeholder for data sanitization
  getWebSocketUrl: () => 'wss://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com/ws/',
};
