// Defensive ErrorUtils shim so early callers never crash.
// If RN already initialized it, we leave it alone.

declare global {
  // loose typing on purpose
  // eslint-disable-next-line no-var
  var ErrorUtils:
    | {
        getGlobalHandler: () => (err: any, isFatal?: boolean) => void;
        setGlobalHandler: (h: (err: any, isFatal?: boolean) => void) => void;
      }
    | undefined;
}

(() => {
  const g: any = globalThis as any;

  // Already set up by InitializeCore? Bail.
  if (g.ErrorUtils && typeof g.ErrorUtils.getGlobalHandler === 'function') return;

  let handler =
    (error: any, isFatal?: boolean) => {
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
})();

