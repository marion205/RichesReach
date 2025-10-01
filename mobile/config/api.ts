/**
* API Configuration
* Centralized API endpoint configuration
*/
// Development API endpoints
export const API_BASE_URL = 'http://54.162.138.209:8000';
export const GRAPHQL_URL = 'http://54.162.138.209:8000/graphql/';
export const WS_URL = 'ws://54.162.138.209:8000/ws';
// Production API endpoints (can be overridden by environment variables)
export const PRODUCTION_API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'https://app.richesreach.net';
export const PRODUCTION_GRAPHQL_URL = process.env.EXPO_PUBLIC_GRAPHQL_URL || 'https://app.richesreach.net/graphql/';
export const PRODUCTION_WS_URL = process.env.EXPO_PUBLIC_WS_URL || 'wss://app.richesreach.net/ws';
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
// Default export for backward compatibility
export default {
API_BASE_URL: getApiBaseUrl(),
GRAPHQL_URL: getGraphQLUrl(),
WS_URL: getWebSocketUrl(),
};
