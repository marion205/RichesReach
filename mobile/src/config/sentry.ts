/**
 * Sentry Configuration for RichesReach Mobile App
 * Error tracking and performance monitoring
 */
import Constants from 'expo-constants';

// Lazy import Sentry to avoid HostFunction errors in Expo Go
let Sentry: any = null;
try {
  Sentry = require('@sentry/react-native');
} catch (e) {
  // Sentry not available - will skip initialization
}

// Initialize Sentry if DSN is provided
// Check in order: expo extra config, environment variables, or empty
// Note: In Expo Go, Constants.expoConfig might not be available
const SENTRY_DSN = 
  (Constants.expoConfig?.extra?.sentryDsn as string | undefined) ||
  (Constants.manifest?.extra?.sentryDsn as string | undefined) ||
  process.env.SENTRY_DSN || 
  process.env.EXPO_PUBLIC_SENTRY_DSN || 
  '';

// Only initialize if DSN is available and not in Expo Go (Sentry doesn't work in Expo Go)
// Use executionEnvironment for proper detection
const isExpoGo = Constants.executionEnvironment === 'storeClient';

if (SENTRY_DSN && !isExpoGo && Sentry) {
  try {
    // Delay Sentry initialization to ensure ErrorUtils polyfill is loaded
    // Use setImmediate to ensure it runs after the polyfill
    setImmediate(() => {
      try {
        Sentry.init({
          dsn: SENTRY_DSN,
          environment: Constants.expoConfig?.extra?.environment || process.env.ENVIRONMENT || process.env.EXPO_PUBLIC_ENVIRONMENT || 'production',
          release: Constants.expoConfig?.extra?.releaseVersion || process.env.RELEASE_VERSION || process.env.EXPO_PUBLIC_RELEASE_VERSION || '1.0.0',
          tracesSampleRate: parseFloat(process.env.SENTRY_TRACES_SAMPLE_RATE || process.env.EXPO_PUBLIC_SENTRY_TRACES_SAMPLE_RATE || '0.1'),
          profilesSampleRate: parseFloat(process.env.SENTRY_PROFILES_SAMPLE_RATE || process.env.EXPO_PUBLIC_SENTRY_PROFILES_SAMPLE_RATE || '0.1'),
          enableAutoSessionTracking: true,
          enableNativeCrashHandling: true,
          beforeSend(event, hint) {
            // Filter sensitive data
            if (event.request) {
              // Filter sensitive headers
              if (event.request.headers) {
                const sensitiveHeaders = ['authorization', 'x-api-key', 'cookie'];
                sensitiveHeaders.forEach(header => {
                  if (header in event.request.headers) {
                    event.request.headers[header] = '[FILTERED]';
                  }
                });
              }
              
              // Filter sensitive data
              if (event.request.data) {
                const sensitiveKeys = ['password', 'token', 'api_key', 'secret'];
                if (typeof event.request.data === 'object') {
                  sensitiveKeys.forEach(key => {
                    if (key in event.request.data) {
                      event.request.data[key] = '[FILTERED]';
                    }
                  });
                }
              }
            }
            
            return event;
          },
        });
        
        console.log('✅ Sentry initialized for error tracking');
      } catch (initError) {
        // Silently fail - Sentry initialization errors shouldn't break the app
        console.warn('Sentry initialization failed:', initError);
      }
    });
  } catch (error) {
    // Silently fail - Sentry initialization errors shouldn't break the app
    console.warn('Sentry setup failed:', error);
  }
} else if (isExpoGo) {
  // Silent in Expo Go - Sentry doesn't work there anyway
  // console.log('ℹ️ Sentry not available in Expo Go - use development build for error tracking');
} else {
  console.log('⚠️ Sentry DSN not configured - error tracking disabled');
}

export default Sentry;

