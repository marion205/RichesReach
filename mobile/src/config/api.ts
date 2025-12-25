import Constants from 'expo-constants';
import { Platform } from 'react-native';

/**
 * API Configuration
 * Single source of truth for all API endpoints
 * 
 * For iOS Simulator: Use localhost (127.0.0.1)
 * For Android Emulator: Use 10.0.2.2
 * For Physical Devices: Use LAN IP (192.168.1.246)
 */

// Determine localhost address based on platform
const LOCALHOST = Platform.OS === 'android' ? '10.0.2.2' : '127.0.0.1';

// Your Mac's LAN IP - for physical devices only
// Current IP: 192.168.1.151 (updated automatically)
const LAN_IP = '192.168.1.151';

// For simulator/emulator, use localhost; for physical devices, use LAN IP
// In dev mode, prefer localhost for simulator (faster, more reliable)
const DEV_BACKEND = `http://${LOCALHOST}:8000`;  // Simulator/Emulator use localhost
const DEV_BACKEND_RUST = `http://${LOCALHOST}:3001`; // Rust backend

// Production host
const PROD_HOST = 'https://api.richesreach.com:8000';
const PROD_HOST_RUST = 'https://api.richesreach.com:3001';

// Check if we're in development mode
const isDev = __DEV__;

// Determine if we're on a simulator/emulator (for iOS/Android)
// This is a heuristic - in production you might want a more robust check
const isSimulator = Platform.OS === 'ios' || Platform.OS === 'android';

// Determine API base URL - Use localhost for simulator, LAN IP for physical devices
let apiBase: string;
let apiBaseRust: string;

if (isDev) {
  // Dev mode: Use localhost for simulator, LAN IP for physical devices
  // For now, default to localhost (works for simulator)
  // User can override with env var if on physical device
  apiBase = `http://${LOCALHOST}:8000`;
  apiBaseRust = `http://${LOCALHOST}:3001`;
  console.log('🔧 [API Config] Dev mode: using localhost for Python', apiBase);
  console.log('🔧 [API Config] Dev mode: using localhost for Rust', apiBaseRust);
  console.log('🔧 [API Config] If on physical device, set EXPO_PUBLIC_API_BASE_URL and EXPO_PUBLIC_RUST_API_URL');
} else {
  // Production mode
  apiBase = PROD_HOST;
  apiBaseRust = PROD_HOST_RUST;
  console.log('🔧 [API Config] Production mode (Python):', apiBase);
  console.log('🔧 [API Config] Production mode (Rust):', apiBaseRust);
}

// Check for environment variable override
const ENV_API_BASE_URL = 
  process.env.EXPO_PUBLIC_API_BASE_URL || 
  Constants.expoConfig?.extra?.API_BASE_URL ||
  Constants.expoConfig?.extra?.API_BASE;

if (ENV_API_BASE_URL) {
  // Check for old/stale IP addresses
  const hasOldIP = /10\.0\.0\.54|192\.168\.1\.240/.test(ENV_API_BASE_URL);
  const hasLocalhost = /localhost|127\.0\.0\.1/.test(ENV_API_BASE_URL);
  
  if (isDev) {
    // In dev mode, NEVER use localhost from env var (it breaks physical devices)
    // Always prefer LAN IP for physical devices
    if (hasLocalhost) {
      console.warn('⚠️ [API Config] ENV var has localhost - IGNORING (will break on physical devices)');
      console.warn('⚠️ [API Config] ENV var value:', ENV_API_BASE_URL);
      console.warn('⚠️ [API Config] Using LAN IP instead:', apiBase);
      // Don't use the env var - keep using LAN IP
    } else if (hasOldIP) {
      console.warn('⚠️ [API Config] ENV var has old/stale IP in dev mode!');
      console.warn('⚠️ [API Config] ENV var value:', ENV_API_BASE_URL);
      console.warn('⚠️ [API Config] Using current LAN IP instead:', apiBase);
      // Don't use the env var - keep using current LAN IP
    } else {
      // For physical devices, allow LAN IP override (if it's a valid LAN IP)
      apiBase = ENV_API_BASE_URL;
      console.log('🔧 [API Config] Using ENV var (LAN IP for physical device):', apiBase);
    }
  } else {
    // Production: use env var as-is
    apiBase = ENV_API_BASE_URL;
    console.log('🔧 [API Config] Using ENV var (production):', apiBase);
  }
}

export const API_BASE = apiBase;
export let API_RUST_BASE = apiBaseRust;

// Check for environment variable override for Rust backend
const ENV_API_BASE_URL_RUST =
  process.env.EXPO_PUBLIC_RUST_API_URL ||
  Constants.expoConfig?.extra?.RUST_API_URL;

if (ENV_API_BASE_URL_RUST) {
  const hasLocalhost = /localhost|127\.0\.0\.1/.test(ENV_API_BASE_URL_RUST);
  if (isDev && hasLocalhost) {
    // Allow localhost override in dev (for simulator)
    API_RUST_BASE = ENV_API_BASE_URL_RUST;
    console.log('🔧 [API Config] Using ENV var for Rust backend (localhost for simulator):', API_RUST_BASE);
  } else if (!hasLocalhost || !isDev) {
    // Use env var if it's not localhost (physical device) or in production
    API_RUST_BASE = ENV_API_BASE_URL_RUST;
    console.log('🔧 [API Config] Using ENV var for Rust backend:', API_RUST_BASE);
  }
}

// TTS API base URL
const TTS_PORT = process.env.EXPO_PUBLIC_TTS_PORT || "8002";
const TTS_HOST = isDev ? DEV_BACKEND.replace(/^https?:\/\//, '').split(':')[0] : PROD_HOST.replace(/^https?:\/\//, '').split(':')[0];
const defaultTTSUrl = `http://${TTS_HOST}:${TTS_PORT}`;

export const TTS_API_BASE_URL = 
  process.env.EXPO_PUBLIC_TTS_API_BASE_URL || 
  Constants.expoConfig?.extra?.TTS_API_BASE_URL ||
  defaultTTSUrl;

// Derived endpoints - normalize trailing slashes
const normalizeUrl = (url: string) => url.replace(/\/+$/, '');

export const API_HTTP    = normalizeUrl(API_BASE);
export const API_GRAPHQL = `${normalizeUrl(API_BASE)}/graphql/`;
export const API_AUTH    = `${normalizeUrl(API_BASE)}/api/auth/login/`;
export const API_WS      = API_BASE.startsWith("https")
  ? API_BASE.replace("https","wss").replace(/\/+$/, '') + "/ws/"
  : API_BASE.replace("http","ws").replace(/\/+$/, '') + "/ws/";

// Debug logging - CRITICAL for debugging
console.log('📡 [API Config] ========================================');
console.log('📡 [API Config] Final configuration:');
console.log('📡 [API Config]   API_BASE:', API_BASE);
console.log('📡 [API Config]   API_RUST_BASE:', API_RUST_BASE);
console.log('📡 [API Config]   API_HTTP:', API_HTTP);
console.log('📡 [API Config]   API_GRAPHQL:', API_GRAPHQL);
console.log('📡 [API Config]   API_AUTH:', API_AUTH);
console.log('📡 [API Config]   TTS_API_BASE_URL:', TTS_API_BASE_URL);
console.log('📡 [API Config]   Platform:', Platform.OS);
console.log('📡 [API Config]   isDev:', isDev);
console.log('📡 [API Config]   ENV_API_BASE_URL:', ENV_API_BASE_URL);
console.log('📡 [API Config] ========================================');

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
