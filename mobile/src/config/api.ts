import Constants from 'expo-constants';
import { Platform } from 'react-native';

/**
 * API Configuration
 * Single source of truth for all API endpoints
 */

// Check environment variable first, then fallback to hardcoded values
// Try multiple sources for the API base URL
const ENV_API_BASE_URL = 
  process.env.EXPO_PUBLIC_API_BASE_URL || 
  Constants.expoConfig?.extra?.API_BASE_URL ||
  Constants.expoConfig?.extra?.API_BASE;

const prodHost = "http://api.richesreach.com:8000";
// Default to LAN IP instead of localhost (localhost doesn't work on physical devices)
// For physical devices, use your Mac's LAN IP (update this to match your current IP)
const LAN_IP = "192.168.1.240"; // Update this to match your Mac's current LAN IP

// CRITICAL: In development mode, ALWAYS use localhost for iOS
// This prevents connection issues in the simulator
let apiBase: string;

if (__DEV__ && Platform.OS === 'ios') {
  console.log('🔧 [API Config] DEV MODE + iOS: FORCING localhost');
  apiBase = ENV_API_BASE_URL || "http://localhost:8000";
} else {
  // Use localhost for iOS Simulator, LAN IP for physical devices
  const isSimulator = Platform.OS === 'ios' && (
    !Constants.isDevice || 
    Constants.executionEnvironment === 'storeClient'
  );
  const localHost = isSimulator ? "http://localhost:8000" : `http://${LAN_IP}:8000`;
  
  // Log detection for debugging
  console.log('[API Config] Platform:', Platform.OS);
  console.log('[API Config] Constants.isDevice:', Constants.isDevice);
  console.log('[API Config] Constants.executionEnvironment:', Constants.executionEnvironment);
  console.log('[API Config] __DEV__:', __DEV__);
  console.log('[API Config] isSimulator:', isSimulator);
  console.log('[API Config] localHost:', localHost);
  
  // Use environment variable if available, otherwise use localHost
  apiBase = ENV_API_BASE_URL || localHost;
}

export const API_BASE = apiBase;

// TTS API base URL (can be same as API_BASE or separate service)
// TTS service runs on port 8001 by default
const TTS_PORT = process.env.EXPO_PUBLIC_TTS_PORT || "8001";
const TTS_HOST = process.env.EXPO_PUBLIC_TTS_HOST || LAN_IP; // Use LAN IP instead of localhost
const defaultTTSUrl = `http://${TTS_HOST}:${TTS_PORT}`;

export const TTS_API_BASE_URL = 
  process.env.EXPO_PUBLIC_TTS_API_BASE_URL || 
  Constants.expoConfig?.extra?.TTS_API_BASE_URL ||
  defaultTTSUrl; // Default to port 8001

// Runtime guardrails to prevent bad hosts
console.log("[API_BASE at runtime]", API_BASE);

// Prevent bad hosts on real devices or release builds
const badHost = /localhost:8001|127\.0\.0\.1:8001/i.test(API_BASE);
if (!__DEV__ && badHost) {
  throw new Error(`Invalid API_BASE in release: ${API_BASE}`);
}

// iOS Simulator can use localhost, physical devices need LAN IP
// Auto-detect if we're on a physical device and using localhost
const isPhysicalDevice = Platform.OS !== 'web' && !__DEV__ || (Platform.OS === 'ios' && !Constants.isDevice);
if (isPhysicalDevice && /localhost|127\.0\.0\.1/.test(API_BASE)) {
  console.warn("⚠️ API_BASE points to localhost on a physical device. Use LAN IP instead.");
  // Try to auto-detect Mac IP from device IP (if device is on same network)
  // For now, user must set EXPO_PUBLIC_API_BASE_URL
}

// Fail fast if no API base URL is configured
if (!API_BASE) {
  throw new Error('EXPO_PUBLIC_API_BASE_URL is required in Expo Go');
}

// Debug logging to see what URL is actually being used
console.log('[API_BASE]', ENV_API_BASE_URL, '-> resolved to:', API_BASE);
console.log('[API_BASE] graphql ->', `${API_BASE}/graphql`);

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