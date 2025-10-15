/**
 * Telemetry Utility - Front-end Observability
 * Structured logging for UX events and performance tracking
 */

export const logUX = (event: string, props?: Record<string, any>) => {
  // Wire to Sentry / Segment / custom endpoint
  if (__DEV__) console.log(`[telemetry] ${event}`, props ?? {});
};
