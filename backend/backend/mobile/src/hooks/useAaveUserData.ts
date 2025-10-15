import { useEffect, useMemo, useRef, useState } from 'react';

export type AAVEUserData = {
  totalCollateralBase: string;     // bigint string
  totalDebtBase: string;           // bigint string
  availableBorrowsBase: string;    // bigint string
  currentLiquidationThreshold: number; // bps (e.g., 8000 = 80%)
  ltv: number;                         // bps
  healthFactor: string;                // ray string (1e18 scale), "0" if no debt
};

export function formatRayToFloat(rayStr: string): number | null {
  if (!rayStr) return null;
  try {
    const b = BigInt(rayStr);
    if (b === 0n) return null; // no debt -> undefined HF
    // divide by 1e18 to get human number
    const intPart = Number(b / 10n**18n);
    const fracPart = Number(b % 10n**18n) / 1e18;
    return intPart + fracPart;
  } catch { return null; }
}

export function bpsToPct(bps?: number): number | null {
  if (bps === undefined || bps === null) return null;
  return Math.round((bps / 100) * 100) / 100; // 2 decimals
}

type State = {
  data?: AAVEUserData;
  loading: boolean;
  error?: string;
};

export function useAAVEUserData(opts: {
  address?: string | null;
  backendBaseUrl: string; // e.g., https://api.yourapp.com
  refreshMs?: number;     // default 8s
}) {
  const { address, backendBaseUrl, refreshMs = 8000 } = opts;
  const [state, setState] = useState<State>({ loading: !!address });
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchOnce = async () => {
    if (!address) return;
    setState(s => ({ ...s, loading: !s.data }));
    try {
      const r = await fetch(`${backendBaseUrl}/defi/aave-user-data/?address=${address}`);
      const j = await r.json();
      if (!r.ok || j.error) throw new Error(j.error || `HTTP ${r.status}`);
      setState({ loading: false, data: j });
    } catch (e: any) {
      setState({ loading: false, error: e?.message || 'Failed to load' });
    }
  };

  useEffect(() => {
    if (!address) return;
    fetchOnce();
    timer.current && clearInterval(timer.current);
    timer.current = setInterval(fetchOnce, refreshMs);
    return () => { if (timer.current) clearInterval(timer.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [address, backendBaseUrl, refreshMs]);

  const derived = useMemo(() => {
    if (!state.data) return {};
    const hf = formatRayToFloat(state.data.healthFactor);
    const ltvPct = bpsToPct(state.data.ltv);
    const liqPct = bpsToPct(state.data.currentLiquidationThreshold);
    return { hf, ltvPct, liqPct };
  }, [state.data]);

  return { ...state, ...derived, reload: fetchOnce };
}
