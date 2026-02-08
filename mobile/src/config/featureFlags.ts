/**
 * Production Feature Flags for React Native App
 * Ensures no mock data in production builds
 */
import { Platform } from 'react-native';
import logger from '../utils/logger';

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
  // DeFi Fortress - yield farming, lending, and DeFi education
  DEFI_FORTRESS_ENABLED: (process.env.EXPO_PUBLIC_DEFI_FORTRESS_ENABLED ?? 'true').toLowerCase() !== 'false',
  // DeFi Mainnet — real funds on Ethereum, Polygon, Arbitrum, Base
  // Defaults to false: must be explicitly enabled when ready for production
  DEFI_MAINNET_ENABLED: (process.env.EXPO_PUBLIC_DEFI_MAINNET_ENABLED ?? 'false').toLowerCase() !== 'false',
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
  logger.log('🚀 RICHESREACH - FEATURE FLAGS');
  logger.log('=' .repeat(40));
  logger.log(`Build: ${isRelease ? 'PRODUCTION' : 'DEVELOPMENT'}`);
  logger.log('Features:');
  Object.entries(FEATURES).forEach(([name, enabled]) => {
    const status = enabled ? '🟢 ENABLED' : '🔴 DISABLED';
    logger.log(`  ${name}: ${status}`);
  });
  logger.log('=' .repeat(40));
}

// Initialize feature flags on app start
if (__DEV__) {
  logFeatureFlags();
} else {
  validateProductionFeatures();
}