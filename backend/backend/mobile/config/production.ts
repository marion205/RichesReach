/**
* Production Configuration for RichesReach Mobile App
* This file contains production-specific settings and optimizations
*/
export const PRODUCTION_CONFIG = {
// API Configuration
API: {
BASE_URL: process.env.EXPO_PUBLIC_API_URL || 'http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com',
GRAPHQL_URL: process.env.EXPO_PUBLIC_GRAPHQL_URL || 'http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com/graphql',
WS_URL: process.env.EXPO_PUBLIC_WS_URL || 'ws://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com/ws',
TIMEOUT: 30000, // 30 seconds
RETRY_ATTEMPTS: 3,
RETRY_DELAY: 1000, // 1 second
},
// Performance Configuration
PERFORMANCE: {
CACHE_DURATION: 3600000, // 1 hour
MAX_CACHE_SIZE: 100, // MB
IMAGE_CACHE_SIZE: 50, // MB
DEBOUNCE_DELAY: 300, // ms
THROTTLE_DELAY: 1000, // ms
},
// Security Configuration
SECURITY: {
ENABLE_SSL_PINNING: true,
ENABLE_CERTIFICATE_PINNING: true,
TOKEN_REFRESH_INTERVAL: 300000, // 5 minutes
MAX_LOGIN_ATTEMPTS: 5,
LOCKOUT_DURATION: 900000, // 15 minutes
},
// Analytics Configuration
ANALYTICS: {
ENABLED: true,
SAMPLE_RATE: 1.0, // 100% in production
BATCH_SIZE: 10,
FLUSH_INTERVAL: 30000, // 30 seconds
},
// Error Reporting Configuration
ERROR_REPORTING: {
ENABLED: true,
SENTRY_DSN: process.env.EXPO_PUBLIC_SENTRY_DSN,
MAX_ERRORS_PER_SESSION: 50,
FILTER_SENSITIVE_DATA: true,
},
// Feature Flags
FEATURES: {
ENABLE_BIOMETRIC_AUTH: true,
ENABLE_PUSH_NOTIFICATIONS: true,
ENABLE_ANALYTICS: true,
ENABLE_CRASH_REPORTING: true,
ENABLE_PERFORMANCE_MONITORING: true,
ENABLE_OFFLINE_MODE: true,
},
// Market Data Configuration
MARKET_DATA: {
POLLING_INTERVAL: 30000, // 30 seconds
MAX_SYMBOLS_PER_REQUEST: 50,
CACHE_DURATION: 3600000, // 1 hour
FALLBACK_TO_MOCK: false, // Never use mock data in production
},
// WebSocket Configuration
WEBSOCKET: {
RECONNECT_ATTEMPTS: 5,
RECONNECT_DELAY: 1000, // 1 second
PING_INTERVAL: 30000, // 30 seconds
PONG_TIMEOUT: 5000, // 5 seconds
},
// Logging Configuration
LOGGING: {
LEVEL: 'ERROR', // Only log errors in production
MAX_LOG_SIZE: 1000, // entries
ENABLE_REMOTE_LOGGING: true,
},
// App Configuration
APP: {
VERSION: process.env.EXPO_PUBLIC_APP_VERSION || '1.0.0',
BUILD_NUMBER: process.env.EXPO_PUBLIC_BUILD_NUMBER || '1',
ENVIRONMENT: 'production',
DEBUG_MODE: false,
},
};
// Production-specific utility functions
export const PRODUCTION_UTILS = {
/**
* Check if running in production mode
*/
isProduction: (): boolean => {
return !__DEV__ && PRODUCTION_CONFIG.APP.ENVIRONMENT === 'production';
},
/**
* Get API URL with fallback
*/
getApiUrl: (): string => {
return PRODUCTION_CONFIG.API.BASE_URL;
},
/**
* Get WebSocket URL with fallback
*/
getWebSocketUrl: (): string => {
return PRODUCTION_CONFIG.API.WS_URL;
},
/**
* Check if feature is enabled
*/
isFeatureEnabled: (feature: keyof typeof PRODUCTION_CONFIG.FEATURES): boolean => {
return PRODUCTION_CONFIG.FEATURES[feature];
},
/**
* Get performance configuration
*/
getPerformanceConfig: () => {
return PRODUCTION_CONFIG.PERFORMANCE;
},
/**
* Get security configuration
*/
getSecurityConfig: () => {
return PRODUCTION_CONFIG.SECURITY;
},
};
export default PRODUCTION_CONFIG;
