import Constants from 'expo-constants';
import { Platform } from 'react-native';

/**
 * API Configuration
 * Single source of truth for all API endpoints
 */

// Check environment variable first, then fallback to hardcoded values
// Try multiple sources for the API base URL
// BUT: If it's localhost and we're on a physical device, ignore it and use device detection
let ENV_API_BASE_URL = 
  process.env.EXPO_PUBLIC_API_BASE_URL || 
  Constants.expoConfig?.extra?.API_BASE_URL ||
  Constants.expoConfig?.extra?.API_BASE;

// Force override: If env var has localhost, check if we're on a physical device
// Use multiple checks since Constants.isDevice might not be reliable in all cases
const isPhysicalDeviceCheck = Platform.OS === 'ios' && Constants.isDevice;
const isLikelyPhysicalDevice = Platform.OS === 'ios' && (
  Constants.isDevice || 
  !Constants.executionEnvironment || 
  Constants.executionEnvironment !== 'storeClient'
);

if (ENV_API_BASE_URL && /localhost|127\.0\.0\.1/.test(ENV_API_BASE_URL)) {
  // If we're likely on a physical device, ignore localhost
  if (isPhysicalDeviceCheck || (Platform.OS === 'ios' && !isSimulator)) {
    console.warn('⚠️ [API Config] Ignoring localhost env var - likely physical device, will use device detection');
    ENV_API_BASE_URL = undefined; // Force device detection to run
  }
}

const prodHost = "http://api.richesreach.com:8000";
// Default to LAN IP instead of localhost (localhost doesn't work on physical devices)
// For physical devices, use your Mac's LAN IP (update this to match your current IP)
const LAN_IP = "10.0.0.54"; // Update this to match your Mac's current LAN IP (was 192.168.1.240)

// Use localhost for iOS Simulator, LAN IP for physical devices
// Check if we're on a real device vs simulator
const isSimulator = Platform.OS === 'ios' && (
  !Constants.isDevice || 
  Constants.executionEnvironment === 'storeClient'
);

let apiBase: string;

// Debug logging
console.log('🔍 [API Config] ENV_API_BASE_URL:', ENV_API_BASE_URL);
console.log('🔍 [API Config] Platform.OS:', Platform.OS);
console.log('🔍 [API Config] Constants.isDevice:', Constants.isDevice);
console.log('🔍 [API Config] isSimulator:', isSimulator);

if (ENV_API_BASE_URL) {
  // Environment variable takes precedence, BUT override localhost on physical devices
  const isPhysicalDevice = Platform.OS === 'ios' && Constants.isDevice;
  const hasLocalhost = /localhost|127\.0\.0\.1/.test(ENV_API_BASE_URL);
  
  console.log('🔍 [API Config] isPhysicalDevice:', isPhysicalDevice);
  console.log('🔍 [API Config] hasLocalhost:', hasLocalhost);
  
  if (isPhysicalDevice && hasLocalhost) {
    // Override localhost on physical devices - use LAN IP instead
    console.warn('⚠️ [API Config] Overriding localhost in env var for physical device');
    apiBase = `http://${LAN_IP}:8000`;
    console.log('🔧 [API Config] Using LAN IP for physical device:', apiBase);
  } else {
    apiBase = ENV_API_BASE_URL;
    console.log('🔧 [API Config] Using EXPO_PUBLIC_API_BASE_URL:', apiBase);
  }
} else if (isSimulator) {
  // iOS Simulator - use localhost
  apiBase = "http://localhost:8000";
  console.log('🔧 [API Config] iOS Simulator detected: using localhost');
} else if (Platform.OS === 'ios' && Constants.isDevice) {
  // Real iOS device - use LAN IP
  apiBase = `http://${LAN_IP}:8000`;
  console.log('🔧 [API Config] Real iOS device detected: using LAN IP', apiBase);
} else {
  // Android or other - use LAN IP for real devices, localhost for emulator
  const isAndroidEmulator = Platform.OS === 'android' && !Constants.isDevice;
  apiBase = isAndroidEmulator ? "http://localhost:8000" : `http://${LAN_IP}:8000`;
  console.log('🔧 [API Config] Platform:', Platform.OS, 'Device:', Constants.isDevice, 'Using:', apiBase);
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