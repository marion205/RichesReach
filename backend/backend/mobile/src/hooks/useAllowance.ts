// Minimal, dependency-light allowance hook
// - Auto-polls every `pollMs` (default 8s)
// - Returns { allowanceHuman, allowanceWei, loading, error, reload }
// - Works with ethers v5/v6 or any provider exposing `call({ to, data })`

import { useEffect, useMemo, useRef, useState } from 'react';

type Hex = `0x${string}`;
type ProviderLike = {
  call: (tx: { to: string; data: Hex }) => Promise<Hex>;
};

const ERC20_ALLOWANCE_SIG = '0xdd62ed3e'; // allowance(address,address)
const ERC20_DECIMALS_SIG = '0x313ce567';  // decimals()

// simple hex pad left
const pad32 = (hex: string) => hex.replace(/^0x/, '').padStart(64, '0');
const encodeAddress = (addr: string) => pad32(addr.toLowerCase().replace(/^0x/, ''));

// formatUnits without ethers
function formatUnits(value: bigint, decimals: number): string {
  const neg = value < 0n;
  let s = (neg ? -value : value).toString();
  if (decimals === 0) return (neg ? '-' : '') + s;

  while (s.length <= decimals) s = '0' + s;
  const i = s.length - decimals;
  const int = s.slice(0, i);
  let frac = s.slice(i).replace(/0+$/, '');
  return (neg ? '-' : '') + int + (frac ? '.' + frac : '');
}

async function readDecimals(provider: ProviderLike, token: string): Promise<number> {
  const data = (ERC20_DECIMALS_SIG as Hex);
  const out = await provider.call({ to: token, data });
  // return last byte as decimals (ABI returns uint8 packed in 32 bytes)
  return parseInt(out.slice(-2), 16) || 18;
}

async function readAllowanceWei(
  provider: ProviderLike,
  token: string,
  owner: string,
  spender: string
): Promise<bigint> {
  const data = (ERC20_ALLOWANCE_SIG + encodeAddress(owner) + encodeAddress(spender)) as Hex;
  const out = await provider.call({ to: token, data });
  return BigInt(out);
}

export function useAllowance(opts: {
  provider: ProviderLike | null | undefined;
  tokenAddress?: string;   // ERC-20 contract
  owner?: string;          // wallet address
  spender?: string;        // AAVE Pool/Router
  decimals?: number;       // optional override
  pollMs?: number;         // default 8000
}) {
  const { provider, tokenAddress, owner, spender, decimals, pollMs = 8000 } = opts;
  const [state, setState] = useState<{
    loading: boolean; error?: string; allowanceWei?: bigint; allowanceHuman?: string; decimals?: number;
  }>({ loading: !!(provider && tokenAddress && owner && spender) });

  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchOnce = async () => {
    if (!provider || !tokenAddress || !owner || !spender) return;
    setState(s => ({ ...s, loading: !s.allowanceWei })); // show spinner only on first load
    try {
      const dec = decimals ?? await readDecimals(provider, tokenAddress);
      const wei = await readAllowanceWei(provider, tokenAddress, owner, spender);
      const human = formatUnits(wei, dec);
      setState({ loading: false, allowanceWei: wei, allowanceHuman: human, decimals: dec });
    } catch (e: any) {
      setState({ loading: false, error: e?.message ?? 'Failed to read allowance' });
    }
  };

  useEffect(() => {
    // start fresh on deps change
    timer.current && clearInterval(timer.current);
    fetchOnce();
    if (provider && tokenAddress && owner && spender) {
      timer.current = setInterval(fetchOnce, pollMs);
    }
    return () => { timer.current && clearInterval(timer.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [provider, tokenAddress, owner, spender, pollMs, decimals]);

  return {
    ...state,
    reload: fetchOnce,
  };
}
