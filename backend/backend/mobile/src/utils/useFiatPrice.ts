// Lightweight fiat price helper + hook with simple cache & fallbacks.

import { useEffect, useRef, useState } from 'react';

type SymbolLike = 'USDC' | 'USDT' | 'WETH' | string;

type CacheEntry = { price: number; ts: number };
const PRICE_CACHE = new Map<SymbolLike, CacheEntry>();

function now() { return Date.now(); }

async function fetchBackendPrices(backendBaseUrl: string, symbols: SymbolLike[]): Promise<Record<string, number>> {
  const qs = encodeURIComponent(symbols.join(','));
  const url = `${backendBaseUrl.replace(/\/$/, '')}/prices?symbols=${qs}`;
  const res = await fetch(url, { method: 'GET' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json(); // expect { "USDC":1, "WETH":2500, ... }
}

function fallbackPrice(sym: SymbolLike): number | undefined {
  if (sym === 'USDC' || sym === 'USDT') return 1.0;
  if (sym === 'WETH') return 2500; // safe placeholder; replace anytime
  return undefined;
}

export async function getFiatPrice(opts: {
  symbol: SymbolLike;
  backendBaseUrl?: string;  // if provided, we try this first
  ttlMs?: number;           // cache TTL (default 20s)
}): Promise<number> {
  const { symbol, backendBaseUrl, ttlMs = 20_000 } = opts;
  const cached = PRICE_CACHE.get(symbol);
  if (cached && (now() - cached.ts) < ttlMs) return cached.price;

  // 1) Try backend if available
  if (backendBaseUrl) {
    try {
      const obj = await fetchBackendPrices(backendBaseUrl, [symbol]);
      const price = Number(obj?.[symbol]);
      if (Number.isFinite(price) && price > 0) {
        PRICE_CACHE.set(symbol, { price, ts: now() });
        return price;
      }
    } catch { /* fall through */ }
  }

  // 2) Fallback to last cached (even if expired)
  if (cached && Number.isFinite(cached.price)) {
    return cached.price;
  }

  // 3) Graceful final fallback
  const fb = fallbackPrice(symbol);
  if (fb !== undefined) {
    PRICE_CACHE.set(symbol, { price: fb, ts: now() });
    return fb;
  }

  // 4) If totally unknown, throw
  throw new Error(`No price available for ${symbol}`);
}

export function useFiatPrice(opts: {
  symbol: SymbolLike;
  backendBaseUrl?: string;
  pollMs?: number;      // default 30s
  ttlMs?: number;       // default 20s (cache)
}) {
  const { symbol, backendBaseUrl, pollMs = 30_000, ttlMs = 20_000 } = opts;
  const [state, setState] = useState<{ price?: number; loading: boolean; error?: string }>({ loading: true });
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchOnce = async () => {
    setState(s => ({ ...s, loading: !s.price })); // spinner only if empty
    try {
      const p = await getFiatPrice({ symbol, backendBaseUrl, ttlMs });
      setState({ loading: false, price: p });
    } catch (e: any) {
      setState(s => ({ ...s, loading: false, error: e?.message ?? 'Failed to load price' }));
    }
  };

  useEffect(() => {
    timer.current && clearInterval(timer.current);
    fetchOnce();
    timer.current = setInterval(fetchOnce, pollMs);
    return () => { timer.current && clearInterval(timer.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol, backendBaseUrl, pollMs, ttlMs]);

  const toFiat = (humanAmount: string | number) => {
    const amt = typeof humanAmount === 'string' ? Number(humanAmount) : humanAmount;
    if (!state.price || !Number.isFinite(amt)) return undefined;
    return amt * state.price;
  };

  return { ...state, reload: fetchOnce, toFiat };
}
