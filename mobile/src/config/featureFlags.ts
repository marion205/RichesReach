/**
 * Production Feature Flags for React Native App
 * Ensures no mock data in production builds
 */
import { Platform } from 'react-native';

// Production build detection
const isRelease = !__DEV__;

// Feature flags from environment variables
export const FEATURES = {
  MARKET_DATA_ENABLED: (process.env.EXPO_PUBLIC_MARKET_DATA_ENABLED ?? 'true').toLowerCase() !== 'false',
  AI_RECS_ENABLED: (process.env.EXPO_PUBLIC_AI_RECS_ENABLED ?? 'true').toLowerCase() !== 'false',
  SBLOC_ENABLED: (process.env.EXPO_PUBLIC_SBLOC_ENABLED ?? 'true').toLowerCase() !== 'false',
  NOTIFICATIONS_ENABLED: (process.env.EXPO_PUBLIC_NOTIFICATIONS_ENABLED ?? 'true').toLowerCase() !== 'false',
  BROKER_ENABLED: (process.env.EXPO_PUBLIC_BROKER_ENABLED ?? 'true').toLowerCase() !== 'false',
  PAYMENTS_ENABLED: (process.env.EXPO_PUBLIC_PAYMENTS_ENABLED ?? 'true').toLowerCase() !== 'false',
  LEARNING_ENABLED: (process.env.EXPO_PUBLIC_LEARNING_ENABLED ?? 'true').toLowerCase() !== 'false',
  THEME_SETTINGS_ENABLED: (process.env.EXPO_PUBLIC_THEME_SETTINGS_ENABLED ?? 'false').toLowerCase() !== 'false',
  // Crypto trading disabled for App Store compliance (regulatory requirements)
  CRYPTO_TRADING_ENABLED: (process.env.EXPO_PUBLIC_CRYPTO_TRADING_ENABLED ?? 'false').toLowerCase() !== 'false',
  CRYPTO_TRADING_MESSAGE: 'Cryptocurrency trading is currently not available. This feature will be available in the future once all regulatory requirements are met.',
};

// Production guardrails - hard fail if features are disabled in release
export function validateProductionFeatures() {
  if (isRelease) {
    const disabledFeatures = Object.entries(FEATURES)
      .filter(([_, enabled]) => !enabled)
      .map(([name]) => name);

    if (disabledFeatures.length > 0) {
      throw new Error(
        `🚨 PRODUCTION BUILD ERROR: Features disabled in release build: ${disabledFeatures.join(', ')}\n` +
        'All features must be enabled for production deployment.'
      );
    }
  }
}

// Log feature flags status
export function logFeatureFlags() {
  console.log('🚀 RICHESREACH - FEATURE FLAGS');
  console.log('=' .repeat(40));
  console.log(`Build: ${isRelease ? 'PRODUCTION' : 'DEVELOPMENT'}`);
  console.log('Features:');
  Object.entries(FEATURES).forEach(([name, enabled]) => {
    const status = enabled ? '🟢 ENABLED' : '🔴 DISABLED';
    console.log(`  ${name}: ${status}`);
  });
  console.log('=' .repeat(40));
}

// Initialize feature flags on app start
if (__DEV__) {
  logFeatureFlags();
} else {
  validateProductionFeatures();
}