// Defensive ErrorUtils shim so early callers never crash.
// MUST run synchronously at module load time (no IIFE delay)
// If RN already initialized it, we leave it alone.

const g = globalThis || global || window;

// Check if ErrorUtils exists and has getGlobalHandler (safe check)
const hasErrorUtils = g.ErrorUtils && typeof g.ErrorUtils.getGlobalHandler === 'function';

// Only set up polyfill if ErrorUtils doesn't exist or is incomplete
if (!hasErrorUtils) {
  let handler = (error, isFatal) => {
    // minimal no-op handler so early callers don't crash
    // (keep console so early errors aren't swallowed)
    // eslint-disable-next-line no-console
    console.error('[polyfill] Unhandled error:', error, { isFatal });
  };

  g.ErrorUtils = {
    getGlobalHandler: () => handler,
    setGlobalHandler: (h) => {
      if (typeof h === 'function') handler = h;
    },
  };
}

