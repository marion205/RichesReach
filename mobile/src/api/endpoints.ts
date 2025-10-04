// API endpoint configuration
// This file centralizes all API endpoints to avoid URL mutation issues

// Import from single source of truth
import { API_BASE, API_GRAPHQL } from '../config/api';

// HTTP endpoints
export const HTTP_GRAPHQL = API_GRAPHQL;
export const HTTP_API_BASE = API_BASE;

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
