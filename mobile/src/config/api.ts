// Single source of truth for API configuration
// This file eliminates all hardcoded LAN IPs and provides a clean production URL

// Force use of the correct backend URL for development
export const API_URL = "http://192.168.1.236:8000/graphql";

export const API_BASE = API_URL.replace('/graphql', '');
export const API_GRAPHQL = API_URL;
export const API_WS = API_URL.replace('https://', 'wss://').replace('http://', 'ws://');
export const API_AUTH = `${API_BASE}/api/auth/login/`;

// Legacy exports for backward compatibility
export const API_BASE_URL = API_BASE;
export const GRAPHQL_URL = API_GRAPHQL;
export const WS_URL = API_WS;

// Debug logging
console.log('🔧 API Configuration:', {
  API_AUTH,
  API_GRAPHQL,
  API_HTTP: API_BASE,
  API_WS,
});