/**
 * API Configuration
 * Single source of truth for all API endpoints
 */

import { Platform } from "react-native";
import Constants from "expo-constants";

function guessHost() {
  const host =
    (Constants as any)?.expoConfig?.hostUri ||
    (Constants as any)?.manifest?.debuggerHost || "";
  return host ? host.split(":")[0] : (Platform.OS === "android" ? "10.0.2.2" : "localhost");
}

const DEV_IP = "192.168.1.236"; // your Mac on Wi-Fi
const HOST = __DEV__ ? DEV_IP : "app.richesreach.com";

export const API_BASE = `http://${HOST}:8000`;

export const API_HTTP    = API_BASE;
export const API_GRAPHQL = `${API_BASE}/graphql/`;
export const API_AUTH    = `${API_BASE}/api/auth/login/`;
export const API_WS      = `ws://${HOST}:8000/ws/`;

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