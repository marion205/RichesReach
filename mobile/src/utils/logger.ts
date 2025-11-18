/**
 * Logger Utility
 * Wraps console methods with __DEV__ checks to prevent production logs
 */

const isDev = __DEV__;

export const logger = {
  /**
   * Log debug information (only in development)
   */
  log: (...args: any[]): void => {
    if (isDev) {
      console.log(...args);
    }
  },

  /**
   * Log warnings (only in development)
   */
  warn: (...args: any[]): void => {
    if (isDev) {
      console.warn(...args);
    }
  },

  /**
   * Log errors (always logged, even in production)
   */
  error: (...args: any[]): void => {
    console.error(...args);
    // In production, you might want to send to error tracking service
    // if (Sentry) Sentry.captureException(new Error(args.join(' ')));
  },

  /**
   * Log info messages (only in development)
   */
  info: (...args: any[]): void => {
    if (isDev) {
      console.info(...args);
    }
  },

  /**
   * Log debug messages (only in development)
   */
  debug: (...args: any[]): void => {
    if (isDev) {
      console.debug(...args);
    }
  },

  /**
   * Group related logs (only in development)
   */
  group: (label: string): void => {
    if (isDev) {
      console.group(label);
    }
  },

  /**
   * End log group (only in development)
   */
  groupEnd: (): void => {
    if (isDev) {
      console.groupEnd();
    }
  },
};

export default logger;

