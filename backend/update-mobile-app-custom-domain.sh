#!/bin/bash

# Update Mobile App Configuration for Custom Domain
# Run this after setting up your custom domain

set -e

echo "📱 Updating Mobile App Configuration for Custom Domain..."

# Check if domain is provided
if [ -z "$1" ]; then
    echo "❌ Error: Custom domain is required"
    echo "Usage: $0 <CUSTOM_DOMAIN>"
    echo ""
    echo "Example:"
    echo "$0 app.richesreach.com"
    exit 1
fi

CUSTOM_DOMAIN="$1"

echo "🌐 Custom Domain: $CUSTOM_DOMAIN"
echo ""

# Update mobile app configuration files
echo "📝 Updating mobile app configuration files..."

# Update env.production
echo "   Updating backend/mobile/env.production..."
cat > backend/mobile/env.production << EOF
# Production Environment Configuration - Custom Domain
EXPO_PUBLIC_API_URL=https://$CUSTOM_DOMAIN
EXPO_PUBLIC_GRAPHQL_URL=https://$CUSTOM_DOMAIN/graphql
EXPO_PUBLIC_RUST_API_URL=https://$CUSTOM_DOMAIN
EXPO_PUBLIC_ENVIRONMENT=production
EXPO_PUBLIC_APP_VERSION=1.0.0
EXPO_PUBLIC_BUILD_NUMBER=1

# API Keys (these should be secured in production)
EXPO_PUBLIC_ALPHA_VANTAGE_API_KEY=OHYSFF1AE446O7CR
EXPO_PUBLIC_FINNHUB_API_KEY=d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0
EXPO_PUBLIC_NEWS_API_KEY=94a335c7316145f79840edd62f77e11e
EXPO_PUBLIC_POLYGON_API_KEY=uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2

# OpenAI Configuration
EXPO_PUBLIC_OPENAI_API_KEY=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
EXPO_PUBLIC_OPENAI_MODEL=gpt-4o-mini
EXPO_PUBLIC_OPENAI_MAX_TOKENS=1200

# Feature Flags
EXPO_PUBLIC_USE_OPENAI=true
EXPO_PUBLIC_OPENAI_ENABLE_FALLBACK=true
EXPO_PUBLIC_USE_FINNHUB=true
EXPO_PUBLIC_DISABLE_ALPHA_VANTAGE=true

# Development Settings
EXPO_PUBLIC_DEBUG=false
EXPO_PUBLIC_LOG_LEVEL=error
EOF

# Update config/api.ts
echo "   Updating backend/mobile/config/api.ts..."
# Create a temporary file with the updated content
cat > backend/mobile/config/api.ts << 'EOF'
/*
 * API Configuration for RichesReach Mobile App
 * This file contains the API endpoints and configuration
 */

// Development API endpoints
export const API_BASE_URL = 'http://192.168.1.151:8123';
export const GRAPHQL_URL = 'http://192.168.1.151:8123/graphql/';
export const WS_URL = 'ws://192.168.1.151:8123/ws';

// Production API endpoints (can be overridden by environment variables)
export const PRODUCTION_API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'https://app.richesreach.com';
export const PRODUCTION_GRAPHQL_URL = process.env.EXPO_PUBLIC_GRAPHQL_URL || 'https://app.richesreach.com/graphql';
export const PRODUCTION_WS_URL = process.env.EXPO_PUBLIC_WS_URL || 'wss://app.richesreach.com/ws';

// Get the appropriate API URL based on environment
export const getApiBaseUrl = (): string => {
  return __DEV__ ? API_BASE_URL : PRODUCTION_API_BASE_URL;
};

export const getGraphQLUrl = (): string => {
  return __DEV__ ? GRAPHQL_URL : PRODUCTION_GRAPHQL_URL;
};

export const getWebSocketUrl = (): string => {
  return __DEV__ ? WS_URL : PRODUCTION_WS_URL;
};

// API Configuration
export const API_CONFIG = {
  timeout: 30000,
  retries: 3,
  retryDelay: 1000,
};

// GraphQL Configuration
export const GRAPHQL_CONFIG = {
  uri: getGraphQLUrl(),
  timeout: 30000,
  retries: 3,
};

// WebSocket Configuration
export const WS_CONFIG = {
  url: getWebSocketUrl(),
  reconnectInterval: 5000,
  maxReconnectAttempts: 5,
};
EOF

# Update src/config/production.ts
echo "   Updating backend/mobile/src/config/production.ts..."
cat > backend/mobile/src/config/production.ts << EOF
// Production Configuration
export const PRODUCTION_CONFIG = {
  API_BASE_URL: 'https://$CUSTOM_DOMAIN',
  GRAPHQL_URL: 'https://$CUSTOM_DOMAIN/graphql/',
  WS_URL: 'wss://$CUSTOM_DOMAIN/ws/',
  ENABLE_ANALYTICS: true,
  ENABLE_ERROR_REPORTING: true,
  ENABLE_PERFORMANCE_MONITORING: true,
  LOG_LEVEL: 'error' as const,
  CACHE_TTL: 300000, // 5 minutes
  REQUEST_TIMEOUT: 30000, // 30 seconds
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000, // 1 second
};

// Production API endpoints
export const PRODUCTION_API_ENDPOINTS = {
  BASE_URL: 'https://$CUSTOM_DOMAIN',
  GRAPHQL: 'https://$CUSTOM_DOMAIN/graphql/',
  WEBSOCKET: 'wss://$CUSTOM_DOMAIN/ws/',
  HEALTH: 'https://$CUSTOM_DOMAIN/health/',
  AI_STATUS: 'https://$CUSTOM_DOMAIN/api/ai-status',
  AI_OPTIONS: 'https://$CUSTOM_DOMAIN/api/ai-options/recommendations',
};

// Production feature flags
export const PRODUCTION_FEATURE_FLAGS = {
  ENABLE_AI_FEATURES: true,
  ENABLE_REAL_TIME_DATA: true,
  ENABLE_PUSH_NOTIFICATIONS: true,
  ENABLE_ANALYTICS: true,
  ENABLE_ERROR_REPORTING: true,
  ENABLE_PERFORMANCE_MONITORING: true,
};

// Production security settings
export const PRODUCTION_SECURITY = {
  REQUIRE_HTTPS: true,
  ENABLE_CERTIFICATE_PINNING: false, // Set to true for enhanced security
  ENABLE_BIOMETRIC_AUTH: true,
  SESSION_TIMEOUT: 3600000, // 1 hour
  MAX_LOGIN_ATTEMPTS: 5,
  LOCKOUT_DURATION: 900000, // 15 minutes
};

// Production logging configuration
export const PRODUCTION_LOGGING = {
  LEVEL: 'error' as const,
  ENABLE_CONSOLE_LOGS: false,
  ENABLE_REMOTE_LOGGING: true,
  LOG_RETENTION_DAYS: 30,
  MAX_LOG_SIZE: 10485760, // 10MB
};

// Production performance settings
export const PRODUCTION_PERFORMANCE = {
  ENABLE_CACHING: true,
  CACHE_TTL: 300000, // 5 minutes
  ENABLE_IMAGE_OPTIMIZATION: true,
  ENABLE_LAZY_LOADING: true,
  ENABLE_CODE_SPLITTING: true,
  ENABLE_SERVICE_WORKER: true,
};

// Production utilities
export const PRODUCTION_UTILS = {
  logError: (error: any) => console.error('Production Error:', error),
  logPerformance: (metric: string, value: number) => console.log(\`Performance: \${metric} = \${value}ms\`),
  sanitizeData: (data: any) => data, // Placeholder for data sanitization
  getWebSocketUrl: () => 'wss://$CUSTOM_DOMAIN/ws/',
};

// Export default configuration
export default PRODUCTION_CONFIG;
EOF

echo "✅ Mobile app configuration updated successfully!"
echo ""
echo "📋 Updated Configuration:"
echo "   API Base URL: https://$CUSTOM_DOMAIN"
echo "   GraphQL URL: https://$CUSTOM_DOMAIN/graphql/"
echo "   WebSocket URL: wss://$CUSTOM_DOMAIN/ws/"
echo ""
echo "🚀 Next Steps:"
echo "   1. Test the custom domain: curl https://$CUSTOM_DOMAIN/health/"
echo "   2. Deploy the mobile app with new configuration"
echo "   3. Verify all endpoints work correctly"
echo ""
echo "📱 Mobile App is now configured for custom domain: $CUSTOM_DOMAIN"
