/**
 * API Configuration
 * Single source of truth for all API endpoints
 */

// Check environment variable first, then fallback to hardcoded values
const ENV_API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL;

const prodHost = "http://54.160.139.56:8000";
const localHost = "http://192.168.1.236:8000";

// Use environment variable if available, otherwise use localhost for development
export const API_BASE = ENV_API_BASE_URL || localHost;

// Fail fast if no API base URL is configured
if (!API_BASE) {
  throw new Error('EXPO_PUBLIC_API_BASE_URL is required in Expo Go');
}

// Debug logging to see what URL is actually being used
console.log('[API_BASE]', ENV_API_BASE_URL, '-> resolved to:', API_BASE);
console.log('[API_BASE] graphql ->', `${API_BASE}/graphql`);

export const API_HTTP    = API_BASE;
export const API_GRAPHQL = `${API_BASE}/graphql/`;
export const API_AUTH    = `${API_BASE}/auth/`;
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