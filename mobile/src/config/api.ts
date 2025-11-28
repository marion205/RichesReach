import Constants from 'expo-constants';
import { Platform } from 'react-native';

/**
 * API Configuration
 * Single source of truth for all API endpoints
 * 
 * SIMPLIFIED: Always use LAN IP in dev mode to avoid localhost issues
 * No device detection - just use LAN IP for all dev builds
 */

// Your Mac's LAN IP - update this if your IP changes
const DEV_BACKEND = 'http://192.168.1.240:8000';

// Production host
const PROD_HOST = 'https://api.richesreach.com:8000';

// Check if we're in development mode
const isDev = __DEV__;

// Determine API base URL - SIMPLE: dev = LAN IP, prod = production
let apiBase: string;

if (isDev) {
  // Dev mode: ALWAYS use LAN IP (no localhost, no device detection)
  apiBase = DEV_BACKEND;
  console.log('🔧 [API Config] Dev mode: using LAN IP', apiBase);
} else {
  // Production mode
  apiBase = PROD_HOST;
  console.log('🔧 [API Config] Production mode:', apiBase);
}

// Check for environment variable override
const ENV_API_BASE_URL = 
  process.env.EXPO_PUBLIC_API_BASE_URL || 
  Constants.expoConfig?.extra?.API_BASE_URL ||
  Constants.expoConfig?.extra?.API_BASE;

if (ENV_API_BASE_URL) {
  // If env var has localhost in dev mode, warn and ignore it
  const hasLocalhost = /localhost|127\.0\.0\.1/.test(ENV_API_BASE_URL);
  
  if (isDev && hasLocalhost) {
    console.warn('⚠️ [API Config] ENV var has localhost in dev mode!');
    console.warn('⚠️ [API Config] Ignoring ENV var, using LAN IP instead:', apiBase);
    // Don't use the env var - keep using LAN IP
  } else {
    apiBase = ENV_API_BASE_URL;
    console.log('🔧 [API Config] Using ENV var:', apiBase);
  }
}

// Final safety check: if somehow we still have localhost in dev, force LAN IP
if (isDev && /localhost|127\.0\.0\.1/.test(apiBase)) {
  console.error('❌ [API Config] CRITICAL: Still have localhost in dev mode!');
  console.error('❌ [API Config] Forcing override to LAN IP');
  apiBase = DEV_BACKEND;
}

export const API_BASE = apiBase;

// TTS API base URL
const TTS_PORT = process.env.EXPO_PUBLIC_TTS_PORT || "8001";
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
