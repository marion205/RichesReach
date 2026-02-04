import Constants from 'expo-constants';
import { Platform } from 'react-native';
import logger from '../utils/logger';

/**
 * API Configuration
 * Single source of truth for all API endpoints
 * 
 * For iOS Simulator: Use localhost (127.0.0.1)
 * For Android Emulator: Use 10.0.2.2
 * For Physical Devices: Use LAN IP (10.0.0.54)
 */

// Determine localhost address based on platform
const LOCALHOST = Platform.OS === 'android' ? '10.0.2.2' : '127.0.0.1';

// Your Mac's LAN IP - for physical devices only
// Current IP: 192.168.1.246 (updated from 10.0.0.54 - that IP doesn't exist on this machine)
const LAN_IP = '192.168.1.246';

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
// Check if we're on a physical device
// More robust detection: check multiple indicators
const deviceName = Constants.deviceName?.toLowerCase() || '';
const isSimulator = deviceName.includes('simulator') || 
                    deviceName.includes('iphone simulator') || 
                    deviceName.includes('ipad simulator') ||
                    deviceName.includes('apple tv simulator');
const isPhysicalDevice = Constants.isDevice && !isSimulator;

// Debug logging for device detection
logger.log('🔧 [API Config] Device Detection:', {
  isDevice: Constants.isDevice,
  deviceName: Constants.deviceName,
  isSimulator,
  isPhysicalDevice,
  platform: Platform.OS,
});

// Determine API base URL - Use localhost for simulator, LAN IP for physical devices
let apiBase: string;
let apiBaseRust: string;

if (isDev) {
  // Dev mode: Use LAN IP for physical devices, localhost for simulator
  if (isPhysicalDevice) {
    // Physical device - use LAN IP
    apiBase = `http://${LAN_IP}:8000`;
    apiBaseRust = `http://${LAN_IP}:3001`;
    logger.log('🔧 [API Config] Dev mode: Physical device detected, using LAN IP for Python', apiBase);
    logger.log('🔧 [API Config] Dev mode: Physical device detected, using LAN IP for Rust', apiBaseRust);
  } else {
    // Simulator/Emulator - use localhost
    apiBase = `http://${LOCALHOST}:8000`;
    apiBaseRust = `http://${LOCALHOST}:3001`;
    logger.log('🔧 [API Config] Dev mode: Simulator/Emulator detected, using localhost for Python', apiBase);
    logger.log('🔧 [API Config] Dev mode: Simulator/Emulator detected, using localhost for Rust', apiBaseRust);
  }
} else {
  // Production mode
  apiBase = PROD_HOST;
  apiBaseRust = PROD_HOST_RUST;
  logger.log('🔧 [API Config] Production mode (Python):', apiBase);
  logger.log('🔧 [API Config] Production mode (Rust):', apiBaseRust);
}

// Check for environment variable override
const ENV_API_BASE_URL = 
  process.env.EXPO_PUBLIC_API_BASE_URL || 
  Constants.expoConfig?.extra?.API_BASE_URL ||
  Constants.expoConfig?.extra?.API_BASE;

logger.log('🔧 [API Config] Environment check:', {
  ENV_API_BASE_URL,
  isPhysicalDevice,
  isDev,
});

if (ENV_API_BASE_URL) {
  // Check for old/stale IP addresses
  const hasOldIP = /10\.0\.0\.54|192\.168\.1\.240/.test(ENV_API_BASE_URL);
  const hasLocalhost = /localhost|127\.0\.0\.1/.test(ENV_API_BASE_URL);
  
  logger.log('🔧 [API Config] ENV var detected:', {
    value: ENV_API_BASE_URL,
    hasLocalhost,
    hasOldIP,
  });
  
  if (isDev) {
    // In dev mode, NEVER use localhost from env var for physical devices (it breaks them)
    // Always prefer LAN IP for physical devices
    if (hasLocalhost && isPhysicalDevice) {
      logger.warn('⚠️ [API Config] ENV var has localhost - IGNORING (will break on physical devices)');
      logger.warn('⚠️ [API Config] ENV var value:', ENV_API_BASE_URL);
      logger.warn('⚠️ [API Config] Using LAN IP instead:', apiBase);
      // Don't use the env var - keep using LAN IP
    } else if (hasOldIP && isPhysicalDevice) {
      logger.warn('⚠️ [API Config] ENV var has old/stale IP in dev mode!');
      logger.warn('⚠️ [API Config] ENV var value:', ENV_API_BASE_URL);
      logger.warn('⚠️ [API Config] Using current LAN IP instead:', apiBase);
      // Don't use the env var - keep using current LAN IP
    } else if (hasLocalhost && !isPhysicalDevice) {
      // Simulator can use localhost from env var
      apiBase = ENV_API_BASE_URL;
      logger.log('🔧 [API Config] Using ENV var (localhost for simulator):', apiBase);
    } else {
      // For physical devices, allow LAN IP override (if it's a valid LAN IP)
      apiBase = ENV_API_BASE_URL;
      logger.log('🔧 [API Config] Using ENV var (LAN IP for physical device):', apiBase);
    }
  } else {
    // Production: use env var as-is
    apiBase = ENV_API_BASE_URL;
    logger.log('🔧 [API Config] Using ENV var (production):', apiBase);
  }
}

// AGGRESSIVE Safety check: If we're in dev mode and using localhost,
// check multiple indicators to determine if we're on a physical device
// This catches cases where device detection failed
if (isDev && apiBase.includes('127.0.0.1')) {
  // Multiple checks to determine if we're on a physical device:
  // 1. Constants.isDevice is true (most reliable)
  // 2. Platform.OS is 'ios' or 'android' (not web)
  // 3. deviceName doesn't contain 'simulator'
  const likelyPhysicalDevice = 
    Constants.isDevice || 
    (Platform.OS !== 'web' && !deviceName.includes('simulator'));
  
  if (likelyPhysicalDevice) {
    logger.warn('⚠️ [API Config] Safety check: Using localhost in dev mode but likely on physical device');
    logger.warn('⚠️ [API Config] Constants.isDevice:', Constants.isDevice);
    logger.warn('⚠️ [API Config] Platform.OS:', Platform.OS);
    logger.warn('⚠️ [API Config] deviceName:', Constants.deviceName);
    logger.warn('⚠️ [API Config] Forcing LAN IP as fallback');
    apiBase = `http://${LAN_IP}:8000`;
    apiBaseRust = `http://${LAN_IP}:3001`;
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
    logger.log('🔧 [API Config] Using ENV var for Rust backend (localhost for simulator):', API_RUST_BASE);
  } else if (!hasLocalhost || !isDev) {
    // Use env var if it's not localhost (physical device) or in production
    API_RUST_BASE = ENV_API_BASE_URL_RUST;
    logger.log('🔧 [API Config] Using ENV var for Rust backend:', API_RUST_BASE);
  }
}

// TTS API base URL (uses port 8002 for FastAPI voice endpoints)
const TTS_PORT = process.env.EXPO_PUBLIC_TTS_PORT || "8002";
const TTS_HOST = isDev ? DEV_BACKEND.replace(/^https?:\/\//, '').split(':')[0] : PROD_HOST.replace(/^https?:\/\//, '').split(':')[0];
const defaultTTSUrl = `http://${TTS_HOST}:${TTS_PORT}`;

export const TTS_API_BASE_URL = 
  process.env.EXPO_PUBLIC_TTS_API_BASE_URL || 
  Constants.expoConfig?.extra?.TTS_API_BASE_URL ||
  defaultTTSUrl;

// Voice API base URL (FastAPI on port 8002)
export const VOICE_API_BASE_URL = TTS_API_BASE_URL;

// Derived endpoints - normalize trailing slashes
const normalizeUrl = (url: string) => url.replace(/\/+$/, '');

export const API_HTTP    = normalizeUrl(API_BASE);
export const API_GRAPHQL = `${normalizeUrl(API_BASE)}/graphql/`;
export const API_AUTH    = `${normalizeUrl(API_BASE)}/api/auth/login/`;
export const API_WS      = API_BASE.startsWith("https")
  ? API_BASE.replace("https","wss").replace(/\/+$/, '') + "/ws/"
  : API_BASE.replace("http","ws").replace(/\/+$/, '') + "/ws/";

// Debug logging - CRITICAL for debugging
logger.log('📡 [API Config] ========================================');
logger.log('📡 [API Config] Final configuration:');
logger.log('📡 [API Config]   API_BASE:', API_BASE);
logger.log('📡 [API Config]   API_RUST_BASE:', API_RUST_BASE);
logger.log('📡 [API Config]   API_HTTP:', API_HTTP);
logger.log('📡 [API Config]   API_GRAPHQL:', API_GRAPHQL);
logger.log('📡 [API Config]   API_AUTH:', API_AUTH);
logger.log('📡 [API Config]   TTS_API_BASE_URL:', TTS_API_BASE_URL);
logger.log('📡 [API Config]   Platform:', Platform.OS);
logger.log('📡 [API Config]   isDev:', isDev);
logger.log('📡 [API Config]   isPhysicalDevice:', isPhysicalDevice);
logger.log('📡 [API Config]   Constants.isDevice:', Constants.isDevice);
logger.log('📡 [API Config]   Constants.deviceName:', Constants.deviceName);
logger.log('📡 [API Config]   ENV_API_BASE_URL:', ENV_API_BASE_URL);
logger.log('📡 [API Config] ========================================');

// Legacy exports for backward compatibility
export const API_BASE_URL = API_HTTP;
export const GRAPHQL_URL = API_GRAPHQL;
export const WS_URL = API_WS;

// Get the appropriate API URL based on environment
export const getApiBaseUrl = (): string => API_BASE;
export const getGraphQLUrl = (): string => API_GRAPHQL;
export const getWebSocketUrl = (): string => API_WS;

// Transparency & methodology (same host as API; backtests use same methodology as live signals)
const base = (API_BASE || '').replace(/\/$/, '');
export const getTransparencyUrl = (): string => `${base}/transparency`;
export const getMethodologyUrl = (): string => `${base}/methodology`;

// Runtime override function - can be called to force LAN IP if device detection failed
export function forceLANIPForPhysicalDevice(): void {
  if (isDev && (API_BASE.includes('127.0.0.1') || API_BASE.includes('localhost'))) {
    logger.warn('🔧 [API Config] Runtime override: Forcing LAN IP for physical device');
    // Note: This won't update the exported constants, but services can call getApiBaseUrl()
    // For now, we'll log a warning and suggest restart
    logger.warn('⚠️ [API Config] Config changes require app restart. Current API_BASE:', API_BASE);
    logger.warn('⚠️ [API Config] Expected LAN IP:', `http://${LAN_IP}:8000`);
  }
}

// Default export for backward compatibility
export default {
  API_BASE_URL: API_BASE,
  GRAPHQL_URL: API_GRAPHQL,
  WS_URL: API_WS,
};
