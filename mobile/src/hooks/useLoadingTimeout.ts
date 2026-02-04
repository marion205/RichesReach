/**
 * useLoadingTimeout: prevents infinite spinners by detecting when a loading state
 * has been true longer than a given timeout. Optionally calls onTimeout (e.g. to
 * clear loading or show an alert). Cleans up the timer on unmount and when loading
 * becomes false.
 */
import { useState, useEffect, useRef } from 'react';

export interface UseLoadingTimeoutOptions {
  /** Time in ms after which loading is considered "timed out" (default 15000) */
  timeoutMs?: number;
  /** Called when the timeout fires; use to clear loading, show alert, etc. */
  onTimeout?: () => void;
}

export interface UseLoadingTimeoutResult {
  /** True once the timeout has fired while loading was still true */
  timedOut: boolean;
}

export function useLoadingTimeout(
  loading: boolean,
  options: UseLoadingTimeoutOptions = {}
): UseLoadingTimeoutResult {
  const { timeoutMs = 15000, onTimeout } = options;
  const [timedOut, setTimedOut] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onTimeoutRef = useRef(onTimeout);
  onTimeoutRef.current = onTimeout;

  useEffect(() => {
    if (loading) {
      setTimedOut(false);
      timerRef.current = setTimeout(() => {
        timerRef.current = null;
        setTimedOut(true);
        onTimeoutRef.current?.();
      }, timeoutMs);
      return () => {
        if (timerRef.current) {
          clearTimeout(timerRef.current);
          timerRef.current = null;
        }
      };
    }
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setTimedOut(false);
  }, [loading, timeoutMs]);

  return { timedOut };
}
