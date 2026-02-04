import { useState, useEffect, useCallback } from 'react';
import { API_HTTP } from '../config/api';

export interface DailyBriefProgressResult {
  streak: number | null;
  loading: boolean;
  refetch: () => Promise<void>;
}

/**
 * Fetches daily brief progress (streak) for the current user.
 * Safe: no fetch when token is missing; cleanup on unmount; mounted guard for setState.
 */
export function useDailyBriefProgress(token: string | null): DailyBriefProgressResult {
  const [streak, setStreak] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    if (!token) {
      setStreak(null);
      setLoading(false);
      return undefined;
    }
    setLoading(true);
    const run = async () => {
      try {
        const response = await fetch(`${API_HTTP}/api/daily-brief/progress`, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        if (active && response.ok) {
          const data = await response.json();
          setStreak(data.streak ?? 0);
        } else if (active) {
          setStreak(0);
        }
      } catch {
        if (active) setStreak(0);
      } finally {
        if (active) setLoading(false);
      }
    };
    run();
    return () => {
      active = false;
    };
  }, [token]);

  const refetch = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const response = await fetch(`${API_HTTP}/api/daily-brief/progress`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      if (response.ok) {
        const data = await response.json();
        setStreak(data.streak ?? 0);
      } else {
        setStreak(0);
      }
    } catch {
      setStreak(0);
    } finally {
      setLoading(false);
    }
  }, [token]);

  return { streak, loading, refetch };
}
