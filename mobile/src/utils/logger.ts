/**
 * Logger Utility
 * Wraps console methods with __DEV__ checks to prevent production logs
 * Defensive implementation that never throws
 */

// Safely check if we're in dev mode
const isDev = typeof __DEV__ !== 'undefined' ? __DEV__ : true;

// Ensure console methods exist
const safeConsole = {
  log: typeof console !== 'undefined' && console.log ? console.log.bind(console) : () => {},
  warn: typeof console !== 'undefined' && console.warn ? console.warn.bind(console) : () => {},
  error: typeof console !== 'undefined' && console.error ? console.error.bind(console) : () => {},
  info: typeof console !== 'undefined' && console.info ? console.info.bind(console) : () => {},
  debug: typeof console !== 'undefined' && console.debug ? console.debug.bind(console) : () => {},
  group: typeof console !== 'undefined' && console.group ? console.group.bind(console) : () => {},
  groupEnd: typeof console !== 'undefined' && console.groupEnd ? console.groupEnd.bind(console) : () => {},
};

export const logger = {
  /**
   * Log debug information (only in development)
   */
  log: (...args: any[]): void => {
    try {
      if (isDev) {
        safeConsole.log(...args);
      }
    } catch (e) {
      // Silently fail - logger should never throw
    }
  },

  /**
   * Log warnings (only in development)
   */
  warn: (...args: any[]): void => {
    try {
      if (isDev) {
        safeConsole.warn(...args);
      }
    } catch (e) {
      // Silently fail - logger should never throw
    }
  },

  /**
   * Log errors (always logged, even in production)
   */
  error: (...args: any[]): void => {
    try {
      safeConsole.error(...args);
      // In production, you might want to send to error tracking service
      // if (Sentry) Sentry.captureException(new Error(args.join(' ')));
    } catch (e) {
      // Silently fail - logger should never throw
    }
  },

  /**
   * Log info messages (only in development)
   */
  info: (...args: any[]): void => {
    try {
      if (isDev) {
        safeConsole.info(...args);
      }
    } catch (e) {
      // Silently fail - logger should never throw
    }
  },

  /**
   * Log debug messages (only in development)
   */
  debug: (...args: any[]): void => {
    try {
      if (isDev) {
        safeConsole.debug(...args);
      }
    } catch (e) {
      // Silently fail - logger should never throw
    }
  },

  /**
   * Group related logs (only in development)
   */
  group: (label: string): void => {
    try {
      if (isDev) {
        safeConsole.group(label);
      }
    } catch (e) {
      // Silently fail - logger should never throw
    }
  },

  /**
   * End log group (only in development)
   */
  groupEnd: (): void => {
    try {
      if (isDev) {
        safeConsole.groupEnd();
      }
    } catch (e) {
      // Silently fail - logger should never throw
    }
  },
};

export default logger;

