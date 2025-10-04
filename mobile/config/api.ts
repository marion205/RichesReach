/**
 * API Configuration
 * Single source of truth for all API endpoints
 */

// Use production URL for all environments
const API_BASE = process.env.EXPO_PUBLIC_API_BASE
  ?? "https://app.richesreach.com"; // Production URL only

export const API_HTTP    = API_BASE;
export const API_GRAPHQL = `${API_BASE}/graphql/`;
export const API_AUTH    = `${API_BASE}/api/auth/login/`;
export const API_WS      = API_BASE.startsWith("https")
  ? API_BASE.replace("https","wss") + "/ws/"
  : API_BASE.replace("http","ws")   + "/ws/";

console.log("🔧 API Configuration:", { API_HTTP: API_BASE, API_GRAPHQL, API_AUTH, API_WS });

// Legacy exports for backward compatibility
export const API_BASE_URL = API_HTTP;
export const GRAPHQL_URL = API_GRAPHQL;
export const WS_URL = API_WS;

// Get the appropriate API URL based on environment
export const getApiBaseUrl = (): string => API_BASE;
export const getGraphQLUrl = (): string => API_GRAPHQL;
export const getWebSocketUrl = (): string => API_WS;

// Default export for backward compatibility
export default {
  API_BASE_URL: API_BASE,
  GRAPHQL_URL: API_GRAPHQL,
  WS_URL: API_WS,
};