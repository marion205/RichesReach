// 1) Our hard polyfill safety net (must be FIRST to prevent crashes)
import './polyfills/errorutils.js';

// 2) Force RN core (sets up global.ErrorUtils, etc.)
// This may already set ErrorUtils, but our polyfill ensures it exists first
import 'react-native/Libraries/Core/InitializeCore';

// Quick verification - should print true in Metro logs very early
console.log('[boot]', 'ErrorUtils ready?', !!global.ErrorUtils?.getGlobalHandler);

// Suppress React Native warnings FIRST (before any imports)
import { LogBox, ErrorUtils } from 'react-native';

// Suppress known warnings and errors
LogBox.ignoreLogs([
  'SafeAreaView has been deprecated',
  'NetInfo not available',
  'Store reset while query was in flight',
  'Network request failed',
  'Network request timed out',
  'Text strings must be rendered within a <Text> component',
  'Console Error',
  'React Native\'s New Architecture', // Suppress New Architecture warning
  'runtime not ready', // Suppress HostFunction errors
  'Exception in HostFunction', // Suppress HostFunction errors
  '[runtime not ready]', // Suppress HostFunction errors (with brackets)
]);

// Suppress console.error for HostFunction errors (they're expected in Expo Go)
const originalError = console.error;
console.error = (...args) => {
  const message = args.join(' ');
  if (
    message.includes('runtime not ready') ||
    message.includes('Exception in HostFunction') ||
    message.includes('[runtime not ready]') ||
    message.includes('HostFunction')
  ) {
    // Silently ignore - these are expected in Expo Go
    return;
  }
  originalError.apply(console, args);
};

// Suppress global error handler for HostFunction errors
// Guard against ErrorUtils being undefined (shouldn't happen with polyfill, but safety first)
const originalGlobalHandler = global.ErrorUtils?.getGlobalHandler?.() || (() => {});
if (global.ErrorUtils) {
  global.ErrorUtils.setGlobalHandler((error, isFatal) => {
  const errorMessage = error?.message || error?.toString() || '';
  if (
    errorMessage.includes('runtime not ready') ||
    errorMessage.includes('Exception in HostFunction') ||
    errorMessage.includes('HostFunction')
  ) {
    // Silently ignore - these are expected in Expo Go
    return;
  }
    // Call original handler for other errors
    if (originalGlobalHandler) {
      originalGlobalHandler(error, isFatal);
    }
  });
}

LogBox.ignoreAllLogs(true);

import 'react-native-gesture-handler';
import { registerRootComponent } from 'expo';
import App from './src/App';

registerRootComponent(App);
