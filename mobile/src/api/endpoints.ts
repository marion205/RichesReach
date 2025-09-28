// API endpoint configuration
// This file centralizes all API endpoints to avoid URL mutation issues

const DEV_API_BASE = process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000';
const PROD_API_BASE = 'https://api.richesreach.com';

// Determine if we're in development mode
const isDev = __DEV__;

// HTTP endpoints
export const HTTP_GRAPHQL = isDev 
  ? `${DEV_API_BASE}/graphql/`
  : `${PROD_API_BASE}/graphql/`;

export const HTTP_API_BASE = isDev 
  ? DEV_API_BASE
  : PROD_API_BASE;

// WebSocket endpoints - using string replacement instead of URL mutation
export const WS_GRAPHQL = HTTP_GRAPHQL
  .replace(/^http:/, 'ws:')
  .replace(/^https:/, 'wss:');

export const WS_BASE = HTTP_API_BASE
  .replace(/^http:/, 'ws:')
  .replace(/^https:/, 'wss:');

// Specific WebSocket endpoints
export const WS_STOCK_PRICES = `${WS_BASE}/ws/stock-prices/`;
export const WS_DISCUSSIONS = `${WS_BASE}/ws/discussions/`;
export const WS_PORTFOLIO = `${WS_BASE}/ws/portfolio/`;

// Helper function to convert HTTP to WebSocket URLs
export const toWs = (httpUrl: string): string => {
  if (httpUrl.startsWith('https://')) {
    return httpUrl.replace('https://', 'wss://');
  }
  return httpUrl.replace('http://', 'ws://');
};

// Helper function to get API base URL
export const getApiBase = (): string => HTTP_API_BASE;

// Helper function to get WebSocket base URL
export const getWsBase = (): string => WS_BASE;
