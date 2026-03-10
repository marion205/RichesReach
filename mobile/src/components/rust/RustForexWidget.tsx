import React, { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  TextInput,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { API_RUST_BASE } from '../../config/api';
import QuantTerminalWidget from './QuantTerminalWidget';
import logger from '../../utils/logger';

const IS_DEMO = process.env.EXPO_PUBLIC_DEMO_MODE === 'true';

// REST API response type (matches Rust backend)
interface ForexAnalysisResponse {
  pair: string;
  bid: number;
  ask: number;
  spread_bps: number;
  atr_14: number;
  trend: string;
  support: number;
  resistance: number;
  timestamp: string;
}

function getDemoForexAnalysis(pairToFetch: string): ForexAnalysisResponse {
  const now = new Date().toISOString();
  const bid = 1.08452;
  const ask = 1.08468;
  return {
    pair: pairToFetch,
    bid,
    ask,
    spread_bps: 1.6,
    atr_14: 0.0082,
    trend: 'BULLISH',
    support: 1.078,
    resistance: 1.092,
    timestamp: now,
  };
}

const DEMO_RL_PAYLOAD = {
  recommended_strategies: [
    { strategy_name: 'fx_momentum', weight: 0.42, score: 0.42 },
    { strategy_name: 'fx_orb', weight: 0.35, score: 0.35 },
    { strategy_name: 'fx_mean_reversion', weight: 0.23, score: 0.23 },
  ],
};

const DEMO_ORACLE_PAYLOAD = {
  alpha_score: 6.8,
  conviction: 'WEAK BUY',
  one_sentence: 'EUR/USD shows a mild bullish bias with calm volatility — small long exposure fits current regime.',
  regime_headline: 'Trend Up, Vol Calm',
  ml_confidence: 0.72,
  explanation: 'Model favors a small long based on trend and volatility regime.',
  position_sizing: { quantity: 0.02, stop_loss: 1.078, risk_usd: 50 },
  risk_guard: { approved: true, scale: 1, reason: 'Within risk limits.' },
};

const DEMO_BACKTEST_PAYLOAD = { sharpe_ratio: 1.24, win_rate: 0.58, total_return: 12.4 };
const DEMO_FUSION_PAYLOAD = {
  fusion_recommendation: { action: 'Cross-asset view supports a small long in EUR/USD; equities risk-on.', confidence: 0.65 },
  action: 'Cross-asset view supports a small long in EUR/USD; equities risk-on.',
  confidence: 0.65,
};

interface RustForexWidgetProps {
  defaultPair?: string;
  size?: 'large' | 'compact';
}

type TrendLabel = 'Up' | 'Down' | 'Sideways';
type VolLabel = 'Calm' | 'Normal' | 'Wild';
type ExecLabel = 'Tight' | 'Normal' | 'Wide';

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}
function safeNum(n: any): number | null {
  if (n === null || n === undefined) return null;
  const v = Number(n);
  return Number.isFinite(v) ? v : null;
}
function fmt5(n?: number | null) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return n.toFixed(5);
}
function fmt2(n?: number | null) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return n.toFixed(2);
}
function trendToLabel(trend: string | null | undefined): TrendLabel {
  if (!trend) return 'Sideways';
  if (trend === 'BULLISH') return 'Up';
  if (trend === 'BEARISH') return 'Down';
  return 'Sideways';
}
function trendColor(label: TrendLabel) {
  if (label === 'Up') return '#10B981';
  if (label === 'Down') return '#EF4444';
  return '#6B7280';
}
function volatilityLabel(volFraction: number | null): { label: VolLabel; color: string } {
  const v = volFraction ?? 0;
  if (v < 0.006) return { label: 'Calm', color: '#10B981' };
  if (v < 0.015) return { label: 'Normal', color: '#F59E0B' };
  return { label: 'Wild', color: '#EF4444' };
}
function executionLabel(spread: number | null, mid: number | null): { label: ExecLabel; color: string; bps: number | null } {
  if (!spread || !mid || mid <= 0) return { label: 'Normal', color: '#6B7280', bps: null };
  const bps = (spread / mid) * 10000;
  if (bps <= 1.2) return { label: 'Tight', color: '#10B981', bps };
  if (bps <= 3.0) return { label: 'Normal', color: '#F59E0B', bps };
  return { label: 'Wide', color: '#EF4444', bps };
}

type LoadState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; message: string; raw?: any }
  | { status: 'ready'; payload: any; ms?: number };

function convictionColor(conv: string) {
  const c = (conv || '').toUpperCase();
  if (c.includes('STRONG')) return '#10B981';
  if (c === 'BUY' || c.includes('WEAK BUY')) return '#22C55E';
  if (c.includes('NEUTRAL')) return '#6B7280';
  if (c.includes('DUMP') || c.includes('SELL')) return '#EF4444';
  return '#6B7280';
}

// ─── Decision Engine ──────────────────────────────────────────────────────────

interface DecisionResult {
  verdict: 'Take It' | 'Take It Small' | 'Wait for Confirmation' | 'Avoid This Setup';
  verdictColor: string;
  verdictBg: string;
  accentBorder: boolean;
  evidence: string[];       // always exactly 3 items
  invalidation: string;
  confidencePct: number;
  riskTier: 'conservative' | 'normal' | 'aggressive';
  riskOneLiner: string;     // e.g. "Small size only", "Normal size"
  plainEnglish: string;
  hasOracleData: boolean;
}

function deriveDecision(
  computed: {
    tLabel: TrendLabel;
    vLabel: VolLabel;
    exLabel: ExecLabel;
    confidence: number;
    support: number | null;
    resistance: number | null;
    mid: number | null;
    pairPretty: string;
  },
  oraclePayload?: any,
  regimePayload?: any,
): DecisionResult {
  const { tLabel, vLabel, exLabel, confidence, support, mid, pairPretty } = computed;

  // Oracle fields (only when available)
  const alphaScore   = oraclePayload ? safeNum(oraclePayload.alpha_score) : null;
  const conviction   = oraclePayload ? String(oraclePayload.conviction ?? '').toUpperCase() : '';
  const oneSentence  = oraclePayload ? String(oraclePayload.one_sentence ?? '') : '';
  const riskGuard    = oraclePayload?.risk_guard ?? null;
  const hasOracleData = !!oraclePayload;

  // Regime fields (from /v1/regime/simple — available on load, before oracle)
  const regimeHeadlineAuto = regimePayload ? String(regimePayload.headline ?? regimePayload.regime_headline ?? '') : '';
  const regimeAction       = regimePayload ? String(regimePayload.action ?? regimePayload.regime_action ?? '') : '';

  // ── 1. Verdict from market signals ──────────────────────────────────────────
  const isAvoid =
    exLabel === 'Wide' ||
    (vLabel === 'Wild' && tLabel === 'Sideways') ||
    conviction.includes('DUMP') ||
    conviction.includes('SELL');

  const isTakeItSmall =
    !isAvoid && (
      vLabel === 'Wild' ||
      (exLabel === 'Normal' && vLabel !== 'Calm') ||
      conviction.includes('WEAK BUY') ||
      conviction.includes('NEUTRAL')
    );

  const isWait = !isAvoid && !isTakeItSmall && tLabel === 'Sideways';

  let verdict: DecisionResult['verdict'];
  if (isAvoid) {
    verdict = 'Avoid This Setup';
  } else if (isTakeItSmall) {
    verdict = 'Take It Small';
  } else if (isWait) {
    verdict = 'Wait for Confirmation';
  } else {
    verdict = 'Take It';
  }

  // ── 2. Oracle promotion / demotion ──────────────────────────────────────────
  if (alphaScore !== null) {
    if (alphaScore > 6 && verdict !== 'Avoid This Setup') verdict = 'Take It';
    if (alphaScore < 3) verdict = 'Avoid This Setup';
  }
  // Risk guard veto
  if (riskGuard && riskGuard.approved === false) {
    if (verdict === 'Take It') verdict = 'Take It Small';
  }

  // ── 3. Verdict colour ────────────────────────────────────────────────────────
  const verdictColorMap: Record<DecisionResult['verdict'], { color: string; bg: string }> = {
    'Take It':               { color: '#FFFFFF', bg: '#00cc99' },
    'Take It Small':         { color: '#FFFFFF', bg: '#F59E0B' },
    'Wait for Confirmation': { color: '#FFFFFF', bg: '#F59E0B' },
    'Avoid This Setup':      { color: '#FFFFFF', bg: '#EF4444' },
  };
  const { color: verdictColor, bg: verdictBg } = verdictColorMap[verdict];
  const accentBorder = verdict === 'Take It';

  // ── 4. Evidence pool ─────────────────────────────────────────────────────────
  const pool: string[] = [];

  // Trend — always first
  if (tLabel === 'Up')        pool.push('Trend is up');
  else if (tLabel === 'Down') pool.push('Trend is down');
  else                        pool.push('Price is moving sideways');

  // Oracle one_sentence takes priority; fall back to regime headline (auto-loaded) or oracle regime_headline
  if (oneSentence && oneSentence.length > 10)             pool.push(oneSentence);
  else if (regimeHeadlineAuto && regimeHeadlineAuto.length > 5) pool.push(regimeHeadlineAuto);
  else if (oraclePayload?.regime_headline)                 pool.push(String(oraclePayload.regime_headline));

  // Volatility
  if (vLabel === 'Calm')      pool.push('Volatility is calm');
  else if (vLabel === 'Wild') pool.push('Volatility is elevated');
  else                        pool.push('Volatility is normal');

  // Execution cost
  if (exLabel === 'Tight')    pool.push('Tight spread — low execution cost');
  else if (exLabel === 'Wide') pool.push('Wide spread — entry cost is high');
  else                        pool.push('Spread is normal');

  // Price vs. support
  if (support !== null && mid !== null && mid > 0) {
    const pct = Math.abs((mid - support) / mid) * 100;
    if (pct < 0.5) pool.push(`Support at ${fmt5(support)} holding`);
  }

  // De-dupe, cap at 3, pad
  const evidence = [...new Set(pool)].slice(0, 3);
  while (evidence.length < 3) evidence.push('Awaiting more data');

  // ── 5. Invalidation ──────────────────────────────────────────────────────────
  let invalidation: string;
  if (riskGuard && riskGuard.approved === false && riskGuard.reason) {
    invalidation = String(riskGuard.reason);
  } else if (support !== null) {
    invalidation = `Break below support at ${fmt5(support)}`;
  } else if (vLabel === 'Normal') {
    invalidation = 'Spike in volatility to Wild';
  } else if (exLabel === 'Normal') {
    invalidation = 'Spread widening further';
  } else {
    invalidation = 'Significant trend reversal';
  }

  // ── 6. Risk tier ─────────────────────────────────────────────────────────────
  let riskTier: DecisionResult['riskTier'];
  if (verdict === 'Take It') {
    riskTier = confidence >= 75 ? 'aggressive' : 'normal';
  } else {
    riskTier = 'conservative';
  }

  // ── 7. Risk one-liner (for "Should You Take This Trade?" card) ─────────────────
  const riskOneLiner =
    riskTier === 'conservative' ? 'Small size only' :
    riskTier === 'normal' ? 'Reduced size' : 'Normal size';

  // ── 8. Plain English ─────────────────────────────────────────────────────────
  let plainEnglish: string;
  if (oneSentence && oneSentence.length > 10) {
    // Oracle has fired — richest context
    plainEnglish = oneSentence;
  } else if (regimeAction && regimeAction.length > 5) {
    // Regime auto-loaded — gives a macro action string before oracle fires
    const volNote = vLabel === 'Wild' ? ' Volatility is elevated — size down.' : '';
    plainEnglish = `${regimeAction}${volNote}`;
  } else {
    const direction = tLabel === 'Up' ? 'long' : tLabel === 'Down' ? 'short' : 'either direction';
    const volNote   = vLabel === 'Wild' ? ' Volatility is elevated — size down.' : '';
    if (verdict === 'Take It') {
      plainEnglish = `${pairPretty} looks favorable for a ${direction}.${volNote}`;
    } else if (verdict === 'Take It Small') {
      plainEnglish = `${pairPretty} has potential but conditions are mixed. Consider a smaller position.${volNote}`;
    } else if (verdict === 'Wait for Confirmation') {
      plainEnglish = `${pairPretty} is range-bound. Wait for a clear directional move before entering.`;
    } else {
      plainEnglish = `Conditions don't favour entering ${pairPretty} right now. Review the risk factors above.`;
    }
  }

  return {
    verdict, verdictColor, verdictBg, accentBorder,
    evidence, invalidation, confidencePct: confidence,
    riskTier, riskOneLiner, plainEnglish, hasOracleData,
  };
}

// ──────────────────────────────────────────────────────────────────────────────

async function postJson(path: string, body: any) {
  if (!API_RUST_BASE) {
    const err: any = new Error('Rust API server not configured. Please set EXPO_PUBLIC_RUST_API_URL.');
    err.raw = { error: 'Missing API_RUST_BASE configuration' };
    throw err;
  }
  
  const t0 = Date.now();
  let res: Response;
  let json: any = {};
  
  // Create AbortController for timeout (AbortSignal.timeout is not available in React Native)
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
  
  try {
    res = await fetch(`${API_RUST_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    clearTimeout(timeoutId); // Clear timeout if request succeeds
    json = await res.json().catch(() => ({}));
  } catch (fetchError: any) {
    clearTimeout(timeoutId); // Clear timeout on error
    const ms = Date.now() - t0;
    // Handle network errors (connection refused, timeout, etc.)
    if (fetchError.name === 'AbortError' || fetchError.name === 'TimeoutError' || fetchError.message?.includes('aborted')) {
      const err: any = new Error('Request timed out. The Rust API server may be slow or unavailable.');
      err.raw = { error: 'timeout', message: fetchError.message };
      err.ms = ms;
      throw err;
    }
    if (fetchError.message?.includes('Network request failed') || fetchError.message?.includes('Failed to connect')) {
      const err: any = new Error(`Cannot connect to Rust API server at ${API_RUST_BASE}. Please ensure the server is running.`);
      err.raw = { error: 'connection_failed', message: fetchError.message };
      err.ms = ms;
      throw err;
    }
    // Re-throw other errors
    const err: any = new Error(fetchError.message || 'Network request failed');
    err.raw = { error: 'unknown', message: fetchError.message };
    err.ms = ms;
    throw err;
  }
  
  const ms = Date.now() - t0;

  if (!res.ok) {
    const msg =
      (typeof json?.error === 'string' && json.error) ||
      (typeof json?.message === 'string' && json.message) ||
      `Request failed (${res.status})`;
    const err: any = new Error(msg);
    err.raw = json;
    err.ms = ms;
    throw err;
  }
  return { json, ms };
}

async function getJson(path: string) {
  if (!API_RUST_BASE) throw new Error('Missing API_RUST_BASE');
  const t0 = Date.now();
  const res = await fetch(`${API_RUST_BASE}${path}`);
  const json = await res.json().catch(() => ({}));
  const ms = Date.now() - t0;

  if (!res.ok) {
    const msg =
      (typeof json?.error === 'string' && json.error) ||
      (typeof json?.message === 'string' && json.message) ||
      `Request failed (${res.status})`;
    const err: any = new Error(msg);
    err.raw = json;
    err.ms = ms;
    throw err;
  }
  return { json, ms };
}

export default function RustForexWidget({ defaultPair = 'EURUSD', size = 'large' }: RustForexWidgetProps) {
  const isCompact = size === 'compact';

  const [pair, setPair] = useState(defaultPair);
  const [inputValue, setInputValue] = useState(defaultPair);

  const [showExplain, setShowExplain] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [showDecision, setShowDecision] = useState(true);

  // Alpha Oracle
  const [showOracle, setShowOracle] = useState(false);
  const [equity, setEquity] = useState('25000');
  const [openPositions, setOpenPositions] = useState('0');
  const [oracle, setOracle] = useState<LoadState>({ status: 'idle' });

  // Backtest (Prove it)
  const [showBacktest, setShowBacktest] = useState(false);
  const [strategy, setStrategy] = useState('fx_orb');
  const [backtest, setBacktest] = useState<LoadState>({ status: 'idle' });
  const [score, setScore] = useState<LoadState>({ status: 'idle' });

  // Cross-asset fusion
  const [showFusion, setShowFusion] = useState(false);
  const [fusion, setFusion] = useState<LoadState>({ status: 'idle' });

  // RL
  const [showRL, setShowRL] = useState(false);
  const [userId, setUserId] = useState('demo_user');
  const [rlRec, setRlRec] = useState<LoadState>({ status: 'idle' });
  const [rlUpdate, setRlUpdate] = useState<LoadState>({ status: 'idle' });

  useEffect(() => {
    if (Platform.OS === 'android') {
      // @ts-ignore
      if (UIManager.setLayoutAnimationEnabledExperimental) {
        // @ts-ignore
        UIManager.setLayoutAnimationEnabledExperimental(true);
      }
    }
  }, []);

  // Regime simple (auto-loaded on mount)
  const [regime, setRegime] = useState<LoadState>({ status: 'idle' });

  const [analysis, setAnalysis] = useState<ForexAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchForexAnalysis = async (pairToFetch: string) => {
    if (!pairToFetch) return;

    setLoading(true);
    setError(null);

    if (IS_DEMO && !API_RUST_BASE) {
      setAnalysis(getDemoForexAnalysis(pairToFetch));
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_RUST_BASE}/v1/forex/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pair: pairToFetch }),
      });

      if (!response.ok) {
        if (IS_DEMO) {
          setAnalysis(getDemoForexAnalysis(pairToFetch));
          setLoading(false);
          return;
        }
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.text();
          if (errorData) {
            try {
              const parsed = JSON.parse(errorData);
              errorMessage = parsed.error || parsed.message || errorMessage;
            } catch {
              errorMessage = errorData || errorMessage;
            }
          }
        } catch {
          // Ignore parsing errors
        }
        if (response.status === 500) {
          errorMessage = 'Forex data service unavailable. Market data provider may not have forex data configured.';
        } else if (response.status === 400) {
          errorMessage = `Invalid forex pair: ${pairToFetch}`;
        }
        throw new Error(errorMessage);
      }

      const data: ForexAnalysisResponse = await response.json();
      setAnalysis(data);
    } catch (err: any) {
      logger.error('Forex analysis error:', err);
      if (IS_DEMO) {
        setAnalysis(getDemoForexAnalysis(pairToFetch));
      } else {
        setError(err);
        setAnalysis(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchRegimeSimple = async () => {
    if (!API_RUST_BASE) return;
    setRegime({ status: 'loading' });
    try {
      const { json } = await getJson('/v1/regime/simple');
      setRegime({ status: 'ready', payload: json });
    } catch {
      // Regime is best-effort — silent failure is fine, the card still works from signals
      setRegime({ status: 'idle' });
    }
  };

  useEffect(() => {
    if (pair) {
      fetchForexAnalysis(pair);
    }
  }, [pair]);

  // Fetch regime once on mount (pair-agnostic macro context)
  useEffect(() => {
    fetchRegimeSimple();
  }, []);

  const handleSearch = () => {
    const trimmed = inputValue.trim().toUpperCase();
    if (!trimmed) return;
    setPair(trimmed);

    // reset advanced panels when switching symbol
    setOracle({ status: 'idle' });
    setBacktest({ status: 'idle' });
    setScore({ status: 'idle' });
    setFusion({ status: 'idle' });
    setRlRec({ status: 'idle' });
    setRlUpdate({ status: 'idle' });
  };

  const computed = useMemo(() => {
    const bid = safeNum(analysis?.bid);
    const ask = safeNum(analysis?.ask);
    // Convert spread_bps to decimal spread
    const spread = analysis?.spread_bps ? analysis.spread_bps / 10000 : null;
    const vol = safeNum(analysis?.atr_14);
    const support = safeNum(analysis?.support);
    const resistance = safeNum(analysis?.resistance);
    const corr = null; // Not available in REST response

    const mid = bid && ask ? (bid + ask) / 2 : null;

    const tLabel = trendToLabel(analysis?.trend);
    const tColor = trendColor(tLabel);

    const v = volatilityLabel(vol);
    const ex = executionLabel(spread, mid);

    let confidence = 55;
    if (tLabel !== 'Sideways') confidence += 10;
    if (v.label === 'Calm') confidence += 10;
    if (v.label === 'Wild') confidence -= 10;
    if (ex.label === 'Tight') confidence += 10;
    if (ex.label === 'Wide') confidence -= 10;
    if (corr !== null && Math.abs(corr) > 0.8) confidence -= 6;
    confidence = clamp(confidence, 20, 92);

    const pairPretty = analysis?.pair ? `${analysis.pair.slice(0, 3)}/${analysis.pair.slice(3)}` : 'This pair';
    const trendPhrase = tLabel === 'Up' ? 'trending up' : tLabel === 'Down' ? 'trending down' : 'moving sideways';
    const volPhrase = v.label === 'Calm' ? 'calm' : v.label === 'Normal' ? 'steady' : 'wild';

    const headline = `${pairPretty} is ${volPhrase} and ${trendPhrase}.`;
    const subline = `Volatility ${v.label} • Trend ${tLabel} • Execution ${ex.label}`;

    const explainBullets = [
      tLabel === 'Up'
        ? 'Price has been pushing higher more than it pulls back.'
        : tLabel === 'Down'
          ? 'Price has been pushing lower more than it bounces.'
          : 'Price is chopping — both sides are getting tested.',
      v.label === 'Calm'
        ? 'Moves are smaller and smoother today.'
        : v.label === 'Wild'
          ? 'Moves are bigger and faster today.'
          : 'Moves are normal for this pair.',
      ex.label === 'Tight'
        ? 'Execution cost is low (tight spread).'
        : ex.label === 'Wide'
          ? 'Execution cost is higher (wide spread).'
          : 'Execution cost is normal.',
    ];

    return {
      bid,
      ask,
      mid,
      spread,
      vol,
      support,
      resistance,
      corr,
      tLabel,
      tColor,
      vLabel: v.label,
      vColor: v.color,
      exLabel: ex.label,
      exColor: ex.color,
      exBps: ex.bps,
      confidence,
      headline,
      subline,
      explainBullets,
      pairPretty,
    };
  }, [analysis]);

  const decision = useMemo(
    () => deriveDecision(
      computed,
      oracle.status === 'ready' ? oracle.payload : undefined,
      regime.status === 'ready' ? regime.payload : undefined,
    ),
    [computed, oracle, regime],
  );

  // ---- Actions: Alpha Oracle / Backtest / Fusion / RL ----

  async function askAlphaOracle() {
    const entry = computed.mid ?? computed.bid ?? computed.ask;
    const eq = safeNum(equity);
    const open = Math.max(0, parseInt(openPositions || '0', 10));

    if (!entry && !IS_DEMO) return setOracle({ status: 'error', message: 'No price available yet.' });
    if ((!eq || eq <= 0) && !IS_DEMO) return setOracle({ status: 'error', message: 'Equity must be a positive number.' });

    setOracle({ status: 'loading' });
    if (IS_DEMO) {
      setTimeout(() => setOracle({ status: 'ready', payload: DEMO_ORACLE_PAYLOAD, ms: 85 }), 400);
      return;
    }
    try {
      const { json, ms } = await postJson('/v1/alpha/signal', {
        symbol: pair,
        equity: eq,
        entry_price: entry,
        open_positions: [],
        features: {
          price_usd: entry,
          volatility: computed.vol ?? 0,
        },
      });
      setOracle({ status: 'ready', payload: json, ms });
    } catch (e: any) {
      setOracle({ status: 'error', message: e?.message || 'Network error', raw: e?.raw });
    }
  }

  async function runBacktest() {
    setBacktest({ status: 'loading' });
    if (IS_DEMO) {
      setTimeout(() => setBacktest({ status: 'ready', payload: DEMO_BACKTEST_PAYLOAD, ms: 120 }), 500);
      return;
    }
    try {
      const { json, ms } = await postJson('/v1/backtest/run', {
        strategy_name: strategy,
        symbol: pair,
        signals: [],
        config: null,
      });
      setBacktest({ status: 'ready', payload: json, ms });
    } catch (e: any) {
      setBacktest({ status: 'error', message: e?.message || 'Backtest error', raw: e?.raw });
    }
  }

  async function fetchBacktestScore() {
    setScore({ status: 'loading' });
    if (IS_DEMO) {
      setTimeout(() => setScore({ status: 'ready', payload: { score: 78, strategy_score: 78 }, ms: 45 }), 200);
      return;
    }
    try {
      const { json, ms } = await getJson(`/v1/backtest/score/${encodeURIComponent(strategy)}/${encodeURIComponent(pair)}`);
      setScore({ status: 'ready', payload: json, ms });
    } catch (e: any) {
      setScore({ status: 'error', message: e?.message || 'Score error', raw: e?.raw });
    }
  }

  async function runFusion() {
    setFusion({ status: 'loading' });
    if (IS_DEMO) {
      setTimeout(() => setFusion({ status: 'ready', payload: DEMO_FUSION_PAYLOAD, ms: 95 }), 350);
      return;
    }
    try {
      const { json, ms } = await postJson('/v1/cross-asset/signal', {
        primary_asset: pair,
      });
      setFusion({ status: 'ready', payload: json, ms });
    } catch (e: any) {
      setFusion({ status: 'error', message: e?.message || 'Fusion error', raw: e?.raw });
    }
  }

  async function rlRecommend() {
    setRlRec({ status: 'loading' });
    if (IS_DEMO) {
      setTimeout(() => {
        setRlRec({ status: 'ready', payload: DEMO_RL_PAYLOAD, ms: 68 });
      }, 300);
      return;
    }
    try {
      const { json, ms } = await postJson('/v1/rl/recommend', {
        user_id: userId,
        context: {
          regime_mood: computed.tLabel === 'Up' ? 'Greed' : computed.tLabel === 'Down' ? 'Fear' : 'Neutral',
          iv_regime: computed.vLabel === 'Calm' ? 'Low' : computed.vLabel === 'Wild' ? 'High' : 'Medium',
          dte_bucket: '30-60',
          account_size_tier: 'Medium',
        },
        available_strategies: ['fx_orb', 'fx_momentum', 'fx_mean_reversion'],
      });
      setRlRec({ status: 'ready', payload: json, ms });
    } catch (e: any) {
      setRlRec({ status: 'error', message: e?.message || 'RL recommend error', raw: e?.raw });
    }
  }

  async function rlSendReward(reward: number) {
    setRlUpdate({ status: 'loading' });
    try {
      const { json, ms } = await postJson('/v1/rl/update', {
        reward: {
          action: {
            user_id: userId,
            strategy_name: strategy,
            symbol: pair,
            context: {
              regime_mood: computed.tLabel === 'Up' ? 'Greed' : computed.tLabel === 'Down' ? 'Fear' : 'Neutral',
              iv_regime: computed.vLabel === 'Calm' ? 'Low' : computed.vLabel === 'Wild' ? 'High' : 'Medium',
              dte_bucket: '30-60',
              account_size_tier: 'Medium',
            },
            timestamp: new Date().toISOString(),
          },
          reward: reward > 0 ? 0.1 : -0.1, // Normalize to -1 to 1 range
          outcome: reward > 0 ? 'Win' : 'Loss',
          timestamp: new Date().toISOString(),
        },
      });
      setRlUpdate({ status: 'ready', payload: json, ms });
    } catch (e: any) {
      setRlUpdate({ status: 'error', message: e?.message || 'RL update error', raw: e?.raw });
    }
  }

  // ---- States ----

  if (loading && !analysis) {
    return (
      <View style={[styles.container, isCompact && styles.containerCompact]}>
        <View style={styles.skeletonRow}>
          <ActivityIndicator size="small" color="#00cc99" />
          <Text style={styles.skeletonText}>Fetching live data…</Text>
        </View>
      </View>
    );
  }
  if (error && !analysis) {
    return (
      <View style={[styles.container, isCompact && styles.containerCompact]}>
        <View style={styles.inlineHeader}>
          <Icon name="alert-triangle" size={16} color="#EF4444" />
          <Text style={styles.inlineHeaderText}>Can't load forex data</Text>
        </View>
        {!isCompact && (
          <>
            <Text style={styles.muted}>{error?.message || 'Check your connection and try again.'}</Text>
            <Text style={[styles.muted, { marginTop: 8, fontSize: 11 }]}>
              Note: Forex data requires a configured market data provider with FX support.
            </Text>
          </>
        )}
      </View>
    );
  }
  if (!analysis) {
    return (
      <View style={[styles.container, isCompact && styles.containerCompact]}>
        <Text style={styles.muted}>No data yet.</Text>
      </View>
    );
  }

  // Compact mode — clean price + signal strip
  if (isCompact) {
    return (
      <View style={styles.compactWrap}>
        <View style={styles.compactPrices}>
          <View style={styles.compactPriceItem}>
            <Text style={styles.compactLabel}>BID</Text>
            <Text style={styles.compactValue}>{fmt5(computed.bid)}</Text>
          </View>
          <View style={styles.compactDivider} />
          <View style={styles.compactPriceItem}>
            <Text style={styles.compactLabel}>ASK</Text>
            <Text style={styles.compactValue}>{fmt5(computed.ask)}</Text>
          </View>
        </View>
        <View style={styles.compactSignalRow}>
          <View style={[styles.compactSignalChip, { backgroundColor: computed.tColor + '18', borderColor: computed.tColor + '40' }]}>
            <View style={[styles.compactSignalDot, { backgroundColor: computed.tColor }]} />
            <Text style={[styles.compactSignalText, { color: computed.tColor }]}>{computed.tLabel}</Text>
          </View>
          <Text style={styles.compactVolText}>{computed.vLabel}</Text>
        </View>
      </View>
    );
  }

  // Alpha Oracle response (root-level)
  const oracleResp = oracle.status === 'ready' ? oracle.payload : null;
  const alphaScore = oracleResp ? safeNum(oracleResp.alpha_score) : null;
  const conviction = oracleResp ? String(oracleResp.conviction ?? '') : '';
  const oneSentence = oracleResp ? String(oracleResp.one_sentence ?? '') : '';
  const regimeHeadline = oracleResp ? String(oracleResp.regime_headline ?? '') : '';
  const mlConfidence = oracleResp ? safeNum(oracleResp.ml_confidence) : null;
  const mlExpl = oracleResp ? String(oracleResp.explanation ?? '') : '';

  const qty = oracleResp ? safeNum(oracleResp?.position_sizing?.quantity) : null;
  const stop = oracleResp ? safeNum(oracleResp?.position_sizing?.stop_loss) : null;
  const riskUsd = oracleResp ? safeNum(oracleResp?.position_sizing?.risk_usd) : null;

  const approved = oracleResp ? oracleResp?.risk_guard?.approved : null;
  const scale = oracleResp ? safeNum(oracleResp?.risk_guard?.scale) : null;
  const reason = oracleResp ? String(oracleResp?.risk_guard?.reason ?? '') : '';

  const alphaColor = convictionColor(conviction);
  const alphaBarPct = alphaScore !== null ? clamp((alphaScore / 10) * 100, 0, 100) : 0;

  // Backtest parsing (unknown shape) — show key fields if present, else raw JSON.
  const backtestResp = backtest.status === 'ready' ? backtest.payload : null;
  const btSharpe = backtestResp ? safeNum(backtestResp.sharpe ?? backtestResp.sharpe_ratio) : null;
  const btWin = backtestResp ? safeNum(backtestResp.win_rate ?? backtestResp.winRate) : null;
  const btReturn = backtestResp ? safeNum(backtestResp.total_return ?? backtestResp.totalReturn ?? backtestResp.total_return_pct) : null;

  // Score response could be number or object
  const scoreResp = score.status === 'ready' ? score.payload : null;
  const scoreVal =
    scoreResp === null ? null :
    typeof scoreResp === 'number' ? scoreResp :
    safeNum(scoreResp.score ?? scoreResp.value ?? scoreResp.overall_score ?? scoreResp.strategy_score);

  // Fusion parsing (unknown shape)
  const fusionResp = fusion.status === 'ready' ? fusion.payload : null;
  const fusionSentence = fusionResp ? String(fusionResp.fusion_recommendation?.action ?? fusionResp.action ?? fusionResp.message ?? '') : '';
  const fusionScore = fusionResp ? safeNum(fusionResp.fusion_recommendation?.confidence ?? fusionResp.confidence ?? fusionResp.score) : null;

  // RL recommend parsing (unknown shape)
  const rlResp = rlRec.status === 'ready' ? rlRec.payload : null;
  const rlItems: Array<{ strategy?: string; weight?: number; score?: number; strategy_name?: string }> =
    Array.isArray(rlResp?.recommended_strategies) ? rlResp.recommended_strategies :
    Array.isArray(rlResp?.recommendations) ? rlResp.recommendations :
    Array.isArray(rlResp) ? rlResp :
    [];

  return (
    <View style={styles.container}>
      {/* Header row */}
      <View style={styles.topHeader}>
        <View style={styles.topHeaderLeft}>
          <View style={[styles.trendIndicator, { backgroundColor: computed.tColor }]} />
          <Text style={styles.topTitle}>Today's Read</Text>
        </View>
        <TouchableOpacity onPress={() => fetchForexAnalysis(pair)} style={styles.refreshBtn} activeOpacity={0.8}>
          <Icon name="refresh-ccw" size={15} color="#6B7280" />
        </TouchableOpacity>
      </View>

      {/* Headline */}
      <Text style={styles.heroLine}>{computed.headline}</Text>

      {/* Search */}
      <View style={styles.searchContainer}>
        <View style={styles.searchRow}>
          <Icon name="search" size={15} color="#AEAEB2" style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search pair (e.g. GBPUSD)"
            placeholderTextColor="#AEAEB2"
            value={inputValue}
            onChangeText={setInputValue}
            autoCapitalize="characters"
            autoCorrect={false}
            returnKeyType="search"
            onSubmitEditing={handleSearch}
          />
          <TouchableOpacity style={styles.searchButton} onPress={handleSearch} activeOpacity={0.85}>
            <Text style={styles.searchButtonText}>Go</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Mid price + Bid/Ask */}
      <View style={styles.pricesBlock}>
        <View style={styles.midPriceRow}>
          <Text style={styles.midLabel}>MID</Text>
          <Text style={styles.midValue}>{computed.mid !== null ? fmt5(computed.mid) : '—'}</Text>
          <View style={[styles.trendChip, { backgroundColor: computed.tColor + '18', borderColor: computed.tColor + '40' }]}>
            <Text style={[styles.trendChipText, { color: computed.tColor }]}>{computed.tLabel}</Text>
          </View>
        </View>
        <View style={styles.bidAskRow}>
          <View style={styles.bidAskItem}>
            <Text style={styles.bidAskLabel}>BID</Text>
            <Text style={styles.bidAskValue}>{fmt5(computed.bid)}</Text>
          </View>
          <View style={styles.bidAskSep} />
          <View style={styles.bidAskItem}>
            <Text style={styles.bidAskLabel}>ASK</Text>
            <Text style={styles.bidAskValue}>{fmt5(computed.ask)}</Text>
          </View>
          <View style={styles.bidAskSep} />
          <View style={styles.bidAskItem}>
            <Text style={styles.bidAskLabel}>SPREAD</Text>
            <Text style={styles.bidAskValue}>{computed.spread !== null ? computed.spread.toFixed(5) : '—'}</Text>
          </View>
        </View>
      </View>

      {/* Signal chips — horizontal scroll so full text shows (no ellipsis) */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.signalRowContent}
        style={styles.signalRowScroll}
      >
        <View style={[styles.signalChip, { backgroundColor: computed.tColor + '14', borderColor: computed.tColor + '35' }]}>
          <Icon name={computed.tLabel === 'Up' ? 'trending-up' : computed.tLabel === 'Down' ? 'trending-down' : 'minus'} size={13} color={computed.tColor} />
          <Text style={[styles.signalChipLabel, { color: computed.tColor }]}>Trend</Text>
          <Text style={[styles.signalChipValue, { color: computed.tColor }]}>{computed.tLabel}</Text>
        </View>
        <View style={[styles.signalChip, { backgroundColor: computed.vColor + '14', borderColor: computed.vColor + '35' }]}>
          <Icon name="activity" size={13} color={computed.vColor} />
          <Text style={[styles.signalChipLabel, { color: computed.vColor }]}>Vol</Text>
          <Text style={[styles.signalChipValue, { color: computed.vColor }]}>{computed.vLabel}</Text>
        </View>
        <View style={[styles.signalChip, { backgroundColor: computed.exColor + '14', borderColor: computed.exColor + '35' }]}>
          <Icon name="zap" size={13} color={computed.exColor} />
          <Text style={[styles.signalChipLabel, { color: computed.exColor }]}>Exec</Text>
          <Text style={[styles.signalChipValue, { color: computed.exColor }]}>{computed.exLabel}</Text>
        </View>
      </ScrollView>

      {/* ═══════════ DECISION CARD ═══════════ */}
      <View style={styles.decisionCard}>
        {/* Teal accent bar — absolute-positioned to avoid iOS overflow:hidden clip */}
        {decision.accentBorder && (
          <View style={styles.decisionAccentBar} />
        )}

        {/* Card header — always visible, toggles body */}
        <TouchableOpacity
          activeOpacity={0.9}
          onPress={() => {
            LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
            setShowDecision(v => !v);
          }}
          style={styles.decisionHeader}
        >
          <Text style={styles.decisionTitle}>Should You Take This Trade?</Text>
          <Icon name={showDecision ? 'chevron-up' : 'chevron-down'} size={16} color="#6B7280" />
        </TouchableOpacity>

        {/* Collapsible body — unified decision: Action, Confidence, Why, Risk, Invalidation, Simple view */}
        {showDecision && (
          <>
            {/* 1. Simple view (one sentence that ties it together) */}
            <View style={styles.decisionWhyWrap}>
              <Text style={styles.simpleViewLabel}>Simple view</Text>
              <Text style={styles.simpleViewText}>{decision.plainEnglish}</Text>
            </View>

            {/* 2. Action + Confidence row — aligned, tight spacing */}
            <View style={styles.actionConfidenceRow}>
              <View style={[styles.verdictChipInRow, { backgroundColor: decision.verdictBg }]}>
                <Text style={[styles.verdictChipText, { color: decision.verdictColor }]} numberOfLines={2}>
                  {decision.verdict}
                </Text>
              </View>
              <View style={styles.confidencePill}>
                <Text style={styles.confidencePillLabel}>Confidence</Text>
                <Text style={styles.confidencePillValue}>{decision.confidencePct}%</Text>
              </View>
            </View>

            {/* 3. Why — evidence bullets + cross-asset when fusion has run */}
            <View style={styles.evidenceBox}>
              {decision.evidence.map((e, i) => (
                <View key={`ev-${i}`} style={styles.bulletRow}>
                  <View style={[styles.bulletDot, e === 'Awaiting more data' && { backgroundColor: '#AEAEB2' }]} />
                  <Text style={[styles.bulletText, e === 'Awaiting more data' && { color: '#AEAEB2' }]}>{e}</Text>
                </View>
              ))}
              {fusion.status === 'ready' && fusionSentence ? (
                <View style={styles.bulletRow}>
                  <View style={styles.bulletDot} />
                  <Text style={styles.bulletText}>Cross-asset: {fusionSentence}</Text>
                </View>
              ) : null}
            </View>

            {/* 4. Risk one-liner */}
            <View style={styles.riskOneLinerRow}>
              <Text style={styles.riskOneLinerLabel}>Risk: </Text>
              <Text style={styles.riskOneLinerValue}>{decision.riskOneLiner}</Text>
            </View>

            {/* 5. Invalidation */}
            <View style={styles.invalidationRow}>
              <Icon name="alert-triangle" size={13} color="#F59E0B" />
              <Text style={styles.invalidationText}>
                <Text style={styles.invalidationLabel}>Invalidation: </Text>
                {decision.invalidation}
              </Text>
            </View>

            {/* 6. Risk grid — when Alpha Oracle has fired */}
            {oracle.status === 'ready' && (
              <View style={styles.decisionRiskWrap}>
                <View style={[styles.grid3, { marginTop: 0 }]}>
                  <View style={styles.cell}>
                    <Text style={styles.cellLabel}>CONFIDENCE</Text>
                    <Text style={styles.cellValue}>{decision.confidencePct}%</Text>
                  </View>
                  <View style={styles.cell}>
                    <Text style={styles.cellLabel}>SIZING</Text>
                    <Text style={styles.cellValue}>
                      {decision.riskTier === 'aggressive' ? 'Normal' : decision.riskTier === 'normal' ? 'Reduced' : 'Small'}
                    </Text>
                  </View>
                  <View style={styles.cell}>
                    <Text style={styles.cellLabel}>MAX RISK</Text>
                    <Text style={styles.cellValue}>
                      {decision.riskTier === 'conservative' ? 'Low' : decision.riskTier === 'normal' ? 'Medium' : 'Standard'}
                    </Text>
                  </View>
                </View>
              </View>
            )}

            {/* 7. Oracle hint when oracle hasn't been called */}
            {oracle.status === 'idle' && (
              <Text style={styles.decisionOracleHint}>
                {regime.status === 'ready'
                  ? 'Macro regime loaded. Tap Alpha Oracle for position sizing.'
                  : 'Tap Alpha Oracle below for a deeper analysis.'}
              </Text>
            )}

            <Text style={[styles.disclaimer, { marginHorizontal: 16 }]}>Educational insights — not financial advice.</Text>
          </>
        )}
      </View>
      {/* ═══════════ END DECISION CARD ═══════════ */}

      {/* Alpha Oracle */}
      <TouchableOpacity
        activeOpacity={0.9}
        onPress={() => { LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut); setShowOracle(v => !v); }}
        style={[styles.toggle, styles.toggleAccent]}
      >
        <View style={styles.toggleLeft}>
          <View style={styles.toggleIconWrap}>
            <Icon name="zap" size={14} color="#00cc99" />
          </View>
          <Text style={styles.toggleText}>Alpha Oracle</Text>
          <View style={styles.miniBadge}><Text style={styles.miniBadgeText}>1 tap</Text></View>
        </View>
        <Icon name={showOracle ? 'chevron-up' : 'chevron-down'} size={17} color="#6B7280" />
      </TouchableOpacity>

      {showOracle && (
        <View style={styles.panel}>
          <Text style={styles.panelHint}>One sentence. One move. Risk checked.</Text>

          <View style={styles.inputRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.smallLabel}>Equity</Text>
              <View style={styles.moneyInputRow}>
                <Text style={styles.moneyPrefix}>$</Text>
                <TextInput value={equity} onChangeText={setEquity} keyboardType="numeric" style={styles.moneyInput} placeholder="25000" />
              </View>
            </View>
            <View style={{ width: 110 }}>
              <Text style={styles.smallLabel}>Open pos</Text>
              <TextInput value={openPositions} onChangeText={setOpenPositions} keyboardType="numeric" style={styles.input} placeholder="0" />
            </View>
          </View>

          <TouchableOpacity onPress={askAlphaOracle} activeOpacity={0.88} style={styles.primaryBtn}>
            {oracle.status === 'loading' ? (
              <>
                <ActivityIndicator size="small" color="#FFFFFF" />
                <Text style={[styles.primaryBtnText, { marginLeft: 10 }]}>Asking…</Text>
              </>
            ) : (
              <>
                <Icon name="sparkles" size={16} color="#FFFFFF" />
                <Text style={styles.primaryBtnText}>Ask Alpha Oracle</Text>
              </>
            )}
          </TouchableOpacity>

          {oracle.status === 'error' && (
            <TouchableOpacity 
              style={styles.errorBox}
              onPress={askAlphaOracle}
              activeOpacity={0.7}
            >
              <Icon name="alert-circle" size={16} color="#EF4444" />
              <Text style={styles.errorText}>{oracle.message}</Text>
              <Text style={[styles.errorText, { fontSize: 11, marginTop: 4, opacity: 0.8 }]}>
                Tap to retry
              </Text>
            </TouchableOpacity>
          )}

          {oracle.status === 'ready' && (
            <View style={{ marginTop: 12 }}>
              <Text style={styles.bigSentence}>{oneSentence || 'Oracle response received.'}</Text>

              <View style={styles.scoreRow}>
                <View>
                  <Text style={styles.smallLabel}>Alpha score</Text>
                  <Text style={styles.scoreValue}>
                    {alphaScore !== null ? alphaScore.toFixed(1) : '—'}
                    <Text style={styles.scoreOutOf}> / 10</Text>
                  </Text>
                </View>
                <View style={[styles.convictionPill, { backgroundColor: alphaColor + '22' }]}>
                  <Text style={[styles.convictionText, { color: alphaColor }]}>{(conviction || 'NEUTRAL').toUpperCase()}</Text>
                </View>
              </View>

              <View style={styles.barTrack}>
                <View style={[styles.barFill, { width: `${alphaBarPct}%` }]} />
              </View>

              <View style={styles.grid3}>
                <View style={styles.cell}>
                  <Text style={styles.cellLabel}>Qty</Text>
                  <Text style={styles.cellValue}>{qty !== null ? qty.toFixed(4) : '—'}</Text>
                </View>
                <View style={styles.cell}>
                  <Text style={styles.cellLabel}>Stop</Text>
                  <Text style={styles.cellValue}>{stop !== null ? stop.toFixed(5) : '—'}</Text>
                </View>
                <View style={styles.cell}>
                  <Text style={styles.cellLabel}>Risk</Text>
                  <Text style={styles.cellValue}>{riskUsd !== null ? `$${riskUsd.toFixed(2)}` : '—'}</Text>
                </View>
              </View>

              <View style={styles.guardRow}>
                <View style={[styles.guardDot, { backgroundColor: approved === true ? '#10B981' : approved === false ? '#EF4444' : '#6B7280' }]} />
                <Text style={styles.guardText}>
                  {approved === true ? 'RiskGuard: approved' : approved === false ? 'RiskGuard: scaled/blocked' : 'RiskGuard: —'}
                  {scale !== null ? ` • scale ${scale.toFixed(2)}x` : ''}
                </Text>
              </View>
              {!!reason && <Text style={styles.guardReason}>{reason}</Text>}

              {/* WHY (Jobs-grade: 3 bullets max) */}
              <View style={styles.whyBox}>
                {!!regimeHeadline && <Text style={styles.whyLine}>• Macro: {regimeHeadline}</Text>}
                {!!mlExpl && <Text style={styles.whyLine}>• Micro: {mlExpl}{mlConfidence !== null ? ` (${(mlConfidence * 100).toFixed(0)}%)` : ''}</Text>}
                <Text style={styles.whyLine}>• Risk: {approved === true ? 'Guardrails OK' : approved === false ? 'Guardrails reduced exposure' : '—'}</Text>
              </View>

              {/* RL feedback: trains the meta-layer without making it scary */}
              <View style={styles.feedbackRow}>
                <TouchableOpacity style={styles.feedbackBtn} onPress={() => rlSendReward(+1)} activeOpacity={0.85}>
                  <Icon name="thumbs-up" size={16} color="#0B0B0F" />
                  <Text style={styles.feedbackText}>Helpful</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.feedbackBtn} onPress={() => rlSendReward(-1)} activeOpacity={0.85}>
                  <Icon name="thumbs-down" size={16} color="#0B0B0F" />
                  <Text style={styles.feedbackText}>Not helpful</Text>
                </TouchableOpacity>
              </View>

              <Text style={styles.disclaimer}>Educational insights — not financial advice.</Text>
            </View>
          )}
        </View>
      )}

      {/* Backtest: Prove it */}
      <TouchableOpacity
        activeOpacity={0.9}
        onPress={() => { LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut); setShowBacktest(v => !v); }}
        style={styles.toggle}
      >
        <View style={styles.toggleLeft}>
          <View style={[styles.toggleIconWrap, styles.toggleIconWrapSecondary]}>
            <Icon name="check-circle" size={14} color="#6366F1" />
          </View>
          <Text style={styles.toggleText}>Prove it</Text>
          <View style={styles.miniBadgeLight}><Text style={styles.miniBadgeLightText}>backtest</Text></View>
        </View>
        <Icon name={showBacktest ? 'chevron-up' : 'chevron-down'} size={17} color="#6B7280" />
      </TouchableOpacity>

      {showBacktest && (
        <View style={styles.panel}>
          <Text style={styles.panelHint}>Trust comes from receipts.</Text>

          <Text style={styles.smallLabel}>Strategy</Text>
          <TextInput value={strategy} onChangeText={setStrategy} style={styles.input} placeholder="fx_orb" />

          <View style={styles.twoBtnRow}>
            <TouchableOpacity onPress={runBacktest} style={styles.secondaryBtn} activeOpacity={0.85}>
              {backtest.status === 'loading' ? <ActivityIndicator size="small" color="#0B0B0F" /> : <Icon name="play" size={16} color="#0B0B0F" />}
              <Text style={styles.secondaryBtnText}>Run backtest</Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={fetchBacktestScore} style={styles.secondaryBtn} activeOpacity={0.85}>
              {score.status === 'loading' ? <ActivityIndicator size="small" color="#0B0B0F" /> : <Icon name="bar-chart-2" size={16} color="#0B0B0F" />}
              <Text style={styles.secondaryBtnText}>Get score</Text>
            </TouchableOpacity>
          </View>

          {score.status === 'ready' && (
            <View style={styles.scoreBox}>
              <Text style={styles.smallLabel}>Strategy score</Text>
              <Text style={styles.scoreBig}>{scoreVal !== null ? scoreVal.toFixed(2) : JSON.stringify(scoreResp)}</Text>
              {score.ms ? <Text style={styles.mutedTiny}>Fetched in {score.ms}ms</Text> : null}
            </View>
          )}

          {backtest.status === 'ready' && (
            <View style={styles.btBox}>
              <View style={styles.grid3}>
                <View style={styles.cell}>
                  <Text style={styles.cellLabel}>Sharpe</Text>
                  <Text style={styles.cellValue}>{btSharpe !== null ? btSharpe.toFixed(2) : '—'}</Text>
                </View>
                <View style={styles.cell}>
                  <Text style={styles.cellLabel}>Win rate</Text>
                  <Text style={styles.cellValue}>{btWin !== null ? `${(btWin * 100).toFixed(0)}%` : '—'}</Text>
                </View>
                <View style={styles.cell}>
                  <Text style={styles.cellLabel}>Return</Text>
                  <Text style={styles.cellValue}>{btReturn !== null ? `${(btReturn * 100).toFixed(0)}%` : '—'}</Text>
                </View>
              </View>

              <TouchableOpacity
                onPress={() => { LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut); setShowDetails(v => !v); }}
                style={styles.detailsToggle}
                activeOpacity={0.85}
              >
                <Text style={styles.detailsToggleText}>{showDetails ? 'Hide raw' : 'Show raw'}</Text>
                <Icon name={showDetails ? 'minus' : 'plus'} size={16} color="#111827" />
              </TouchableOpacity>

              {showDetails && (
                <Text style={styles.mono}>
                  {JSON.stringify(backtestResp, null, 2)}
                </Text>
              )}

              {backtest.ms ? <Text style={styles.mutedTiny}>Backtest in {backtest.ms}ms</Text> : null}
            </View>
          )}

          {backtest.status === 'error' && (
            <View style={styles.errorBox}>
              <Icon name="alert-circle" size={16} color="#EF4444" />
              <Text style={styles.errorText}>{backtest.message}</Text>
            </View>
          )}
        </View>
      )}

      {/* Cross-asset fusion */}
      <TouchableOpacity
        activeOpacity={0.9}
        onPress={() => { LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut); setShowFusion(v => !v); }}
        style={styles.toggle}
      >
        <View style={styles.toggleLeft}>
          <View style={[styles.toggleIconWrap, styles.toggleIconWrapSecondary]}>
            <Icon name="shuffle" size={14} color="#6366F1" />
          </View>
          <Text style={styles.toggleText}>Across markets</Text>
          <View style={styles.miniBadgeLight}><Text style={styles.miniBadgeLightText}>fusion</Text></View>
        </View>
        <Icon name={showFusion ? 'chevron-up' : 'chevron-down'} size={17} color="#6B7280" />
      </TouchableOpacity>

      {showFusion && (
        <View style={styles.panel}>
          <Text style={styles.panelHint}>See if the bigger world agrees.</Text>

          <TouchableOpacity onPress={runFusion} style={styles.secondaryBtnFull} activeOpacity={0.85}>
            {fusion.status === 'loading' ? <ActivityIndicator size="small" color="#0B0B0F" /> : <Icon name="activity" size={16} color="#0B0B0F" />}
            <Text style={styles.secondaryBtnText}>Generate fusion signal</Text>
          </TouchableOpacity>

          {fusion.status === 'ready' && (
            <View style={styles.fusionBox}>
              <Text style={styles.bigSentence}>
                {fusionSentence || 'Fusion signal received.'}
              </Text>
              <View style={styles.guardRow}>
                <View style={[styles.guardDot, { backgroundColor: '#0B0B0F' }]} />
                <Text style={styles.guardText}>
                  {fusionScore !== null ? `Fusion score: ${fusionScore.toFixed(2)}` : 'Fusion score: —'}
                </Text>
              </View>
              {fusion.ms ? <Text style={styles.mutedTiny}>Computed in {fusion.ms}ms</Text> : null}
              <Text style={styles.disclaimer}>Educational insights — not financial advice.</Text>
            </View>
          )}

          {fusion.status === 'error' && (
            <View style={styles.errorBox}>
              <Icon name="alert-circle" size={16} color="#EF4444" />
              <Text style={styles.errorText}>{fusion.message}</Text>
            </View>
          )}
        </View>
      )}

      {/* RL: personalize */}
      <TouchableOpacity
        activeOpacity={0.9}
        onPress={() => { LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut); setShowRL(v => !v); }}
        style={styles.toggle}
      >
        <View style={styles.toggleLeft}>
          <View style={[styles.toggleIconWrap, styles.toggleIconWrapSecondary]}>
            <Icon name="cpu" size={14} color="#6366F1" />
          </View>
          <Text style={styles.toggleText}>Personalize</Text>
          <View style={styles.miniBadgeLight}><Text style={styles.miniBadgeLightText}>RL</Text></View>
        </View>
        <Icon name={showRL ? 'chevron-up' : 'chevron-down'} size={17} color="#6B7280" />
      </TouchableOpacity>

      {showRL && (
        <View style={styles.panel}>
          <Text style={styles.panelHint}>Learns what works for you — in your market context.</Text>

          <Text style={styles.smallLabel}>User</Text>
          <TextInput value={userId} onChangeText={setUserId} style={styles.input} placeholder="demo_user" />

          <TouchableOpacity onPress={rlRecommend} style={styles.secondaryBtnFull} activeOpacity={0.85}>
            {rlRec.status === 'loading' ? <ActivityIndicator size="small" color="#0B0B0F" /> : <Icon name="star" size={16} color="#0B0B0F" />}
            <Text style={styles.secondaryBtnText}>Get recommendations</Text>
          </TouchableOpacity>

          {rlRec.status === 'ready' && (
            <View style={styles.rlBox}>
              <Text style={styles.smallLabel}>Top picks</Text>
              {rlItems.length === 0 ? (
                <Text style={styles.muted}>No recommendations returned.</Text>
              ) : (
                rlItems.slice(0, 3).map((it, idx) => (
                  <View key={`${idx}-${it.strategy_name ?? it.strategy ?? idx}`} style={styles.rlRow}>
                    <Text style={styles.rlStrategy}>{it.strategy_name ?? it.strategy ?? '—'}</Text>
                    <Text style={styles.rlScore}>{safeNum(it.weight ?? it.score)?.toFixed(2) ?? '—'}</Text>
                  </View>
                ))
              )}
              {rlRec.ms ? <Text style={styles.mutedTiny}>Computed in {rlRec.ms}ms</Text> : null}
            </View>
          )}

          {rlUpdate.status === 'loading' && (
            <Text style={styles.mutedTiny}>Saving feedback…</Text>
          )}
          {rlUpdate.status === 'error' && (
            <View style={styles.errorBox}>
              <Icon name="alert-circle" size={16} color="#EF4444" />
              <Text style={styles.errorText}>{rlUpdate.message}</Text>
            </View>
          )}
        </View>
      )}

      {/* Explain */}
      <TouchableOpacity
        activeOpacity={0.9}
        onPress={() => { LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut); setShowExplain(v => !v); }}
        style={styles.toggle}
      >
        <View style={styles.toggleLeft}>
          <View style={[styles.toggleIconWrap, styles.toggleIconWrapSecondary]}>
            <Icon name="info" size={14} color="#6366F1" />
          </View>
          <Text style={styles.toggleText}>Explain it simply</Text>
        </View>
        <Icon name={showExplain ? 'chevron-up' : 'chevron-down'} size={17} color="#6B7280" />
      </TouchableOpacity>

      {showExplain && (
        <View style={styles.panel}>
          {computed.explainBullets.map((b, idx) => (
            <View key={`${idx}-${b}`} style={styles.bulletRow}>
              <View style={styles.bulletDot} />
              <Text style={styles.bulletText}>{b}</Text>
            </View>
          ))}
          <Text style={styles.disclaimer}>Educational insights — not financial advice.</Text>
        </View>
      )}

      {/* Phase 3: Quant Terminal */}
      <QuantTerminalWidget
        symbol={pair}
        strategyName="forex_trend_following"
        userId={userId}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  // Base container
  container: { backgroundColor: '#FFFFFF', borderRadius: 0, padding: 0 },
  containerCompact: { padding: 0, borderWidth: 0, backgroundColor: 'transparent' },

  // Loading / Error states
  skeletonRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12, gap: 10 },
  skeletonText: { color: '#6B7280', fontWeight: '600', fontSize: 13 },
  inlineHeader: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  inlineHeaderText: { fontSize: 14, fontWeight: '700', color: '#1C1C1E' },
  muted: { marginTop: 6, color: '#8E8E93', fontWeight: '500', fontSize: 13 },
  mutedTiny: { marginTop: 8, color: '#AEAEB2', fontWeight: '600', fontSize: 11 },

  // Compact mode
  compactWrap: { gap: 8 },
  compactPrices: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  compactPriceItem: { flex: 1 },
  compactDivider: { width: 1, height: 28, backgroundColor: '#EBEBF0' },
  compactLabel: { fontSize: 9, color: '#AEAEB2', fontWeight: '700', letterSpacing: 0.5, marginBottom: 2 },
  compactValue: { fontSize: 13, fontWeight: '800', color: '#0B0B0F' },
  compactSignalRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  compactSignalChip: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    paddingHorizontal: 8, paddingVertical: 4, borderRadius: 999, borderWidth: 1,
  },
  compactSignalDot: { width: 5, height: 5, borderRadius: 2.5 },
  compactSignalText: { fontSize: 11, fontWeight: '700' },
  compactVolText: { fontSize: 11, fontWeight: '600', color: '#AEAEB2' },

  // Large widget header
  topHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 },
  topHeaderLeft: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  trendIndicator: { width: 8, height: 8, borderRadius: 4 },
  topTitle: { fontSize: 13, fontWeight: '700', color: '#6B7280', letterSpacing: 0.2 },
  refreshBtn: {
    width: 32, height: 32, borderRadius: 10, backgroundColor: '#F8F9FB',
    borderWidth: 1, borderColor: '#EBEBF0', alignItems: 'center', justifyContent: 'center',
  },

  // Headline
  heroLine: { fontSize: 17, fontWeight: '800', color: '#0B0B0F', letterSpacing: -0.3, lineHeight: 24, marginBottom: 14 },

  // Search
  searchContainer: { marginBottom: 16 },
  searchRow: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: '#F8F9FB', borderWidth: 1, borderColor: '#EBEBF0',
    borderRadius: 14, paddingHorizontal: 12, height: 44, gap: 8,
  },
  searchIcon: {},
  searchInput: {
    flex: 1, height: 44, fontSize: 14, fontWeight: '600', color: '#0B0B0F',
  },
  searchButton: {
    backgroundColor: '#0B0B0F', borderRadius: 10, paddingHorizontal: 12,
    height: 30, justifyContent: 'center', alignItems: 'center',
  },
  searchButtonText: { color: '#FFFFFF', fontSize: 12, fontWeight: '700' },

  // Prices block
  pricesBlock: {
    backgroundColor: '#F8F9FB', borderRadius: 16, borderWidth: 1, borderColor: '#EBEBF0',
    paddingVertical: 14, paddingHorizontal: 16, marginBottom: 12,
  },
  midPriceRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 12 },
  midLabel: { fontSize: 10, fontWeight: '800', color: '#AEAEB2', letterSpacing: 0.6 },
  midValue: { fontSize: 24, fontWeight: '800', color: '#0B0B0F', letterSpacing: -0.5, flex: 1 },
  trendChip: {
    paddingHorizontal: 10, paddingVertical: 5, borderRadius: 999, borderWidth: 1,
  },
  trendChipText: { fontSize: 12, fontWeight: '700' },
  bidAskRow: { flexDirection: 'row', alignItems: 'center' },
  bidAskItem: { flex: 1 },
  bidAskSep: { width: 1, height: 28, backgroundColor: '#EBEBF0', marginHorizontal: 8 },
  bidAskLabel: { fontSize: 9, fontWeight: '800', color: '#AEAEB2', letterSpacing: 0.6, marginBottom: 3 },
  bidAskValue: { fontSize: 13, fontWeight: '700', color: '#3A3A3C' },

  // Signal chips — horizontal scroll so full labels (Trend Sideways, Vol Calm, Exec Normal) show
  signalRowScroll: { marginBottom: 16 },
  signalRowContent: {
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 16,
    paddingRight: 24,
  },
  signalChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 14,
    borderWidth: 1,
  },
  signalChipLabel: { fontSize: 10, fontWeight: '800', letterSpacing: 0.2 },
  signalChipValue: { fontSize: 12, fontWeight: '800' },

  // Accordion toggles
  toggle: {
    marginBottom: 8,
    backgroundColor: '#F8F9FB',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#EBEBF0',
    paddingVertical: 13,
    paddingHorizontal: 14,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  toggleAccent: {
    backgroundColor: '#00cc9908',
    borderColor: '#00cc9925',
  },
  toggleLeft: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  toggleIconWrap: {
    width: 28, height: 28, borderRadius: 8,
    backgroundColor: '#00cc9915', alignItems: 'center', justifyContent: 'center',
  },
  toggleIconWrapSecondary: {
    backgroundColor: '#6366F110',
  },
  toggleText: { fontSize: 13, fontWeight: '700', color: '#0B0B0F' },

  miniBadge: {
    backgroundColor: '#00cc99', paddingHorizontal: 8, paddingVertical: 3,
    borderRadius: 999, marginLeft: 4,
  },
  miniBadgeText: { color: '#FFFFFF', fontSize: 9, fontWeight: '800', letterSpacing: 0.3 },
  miniBadgeLight: {
    backgroundColor: '#F0F0F5', paddingHorizontal: 8, paddingVertical: 3,
    borderRadius: 999, marginLeft: 4,
  },
  miniBadgeLightText: { color: '#6B7280', fontSize: 9, fontWeight: '700' },

  // Panel (expanded accordion content)
  panel: {
    marginBottom: 8, backgroundColor: '#FFFFFF', borderRadius: 14, padding: 14,
    borderWidth: 1, borderColor: '#EBEBF0',
  },
  panelHint: { fontSize: 12, color: '#6B7280', fontWeight: '600', lineHeight: 18, marginBottom: 4 },

  inputRow: { marginTop: 12, flexDirection: 'row', gap: 10, alignItems: 'flex-end' },
  smallLabel: { fontSize: 11, color: '#6B7280', fontWeight: '700', marginBottom: 5, letterSpacing: 0.2 },

  input: {
    height: 42, backgroundColor: '#F8F9FB', borderWidth: 1, borderColor: '#EBEBF0',
    borderRadius: 12, paddingHorizontal: 12, fontSize: 13, fontWeight: '700', color: '#0B0B0F',
  },
  moneyInputRow: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#F8F9FB',
    borderWidth: 1, borderColor: '#EBEBF0', borderRadius: 12, paddingHorizontal: 12, height: 42, gap: 6,
  },
  moneyPrefix: { fontSize: 13, fontWeight: '700', color: '#6B7280' },
  moneyInput: { flex: 1, height: 42, fontSize: 13, fontWeight: '700', color: '#0B0B0F' },

  // Buttons
  primaryBtn: {
    marginTop: 12, height: 46, borderRadius: 14, backgroundColor: '#00cc99',
    alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 8,
  },
  primaryBtnText: { color: '#FFFFFF', fontWeight: '800', fontSize: 13 },

  twoBtnRow: { marginTop: 12, flexDirection: 'row', gap: 10 },
  secondaryBtn: {
    flex: 1, height: 44, borderRadius: 12, backgroundColor: '#F8F9FB',
    borderWidth: 1, borderColor: '#EBEBF0', alignItems: 'center',
    justifyContent: 'center', flexDirection: 'row', gap: 8,
  },
  secondaryBtnFull: {
    marginTop: 12, height: 44, borderRadius: 12, backgroundColor: '#F8F9FB',
    borderWidth: 1, borderColor: '#EBEBF0', alignItems: 'center',
    justifyContent: 'center', flexDirection: 'row', gap: 8,
  },
  secondaryBtnText: { fontWeight: '700', color: '#0B0B0F', fontSize: 13 },

  errorBox: {
    marginTop: 12, flexDirection: 'row', alignItems: 'flex-start', gap: 8,
    backgroundColor: '#FEF2F2', borderWidth: 1, borderColor: '#FEE2E2',
    padding: 12, borderRadius: 12,
  },
  errorText: { flex: 1, color: '#B91C1C', fontWeight: '700', fontSize: 12, lineHeight: 18 },

  bigSentence: { fontSize: 15, fontWeight: '700', color: '#0B0B0F', lineHeight: 22 },

  scoreRow: { marginTop: 12, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 10 },
  scoreValue: { marginTop: 2, fontSize: 20, fontWeight: '800', color: '#0B0B0F' },
  scoreOutOf: { fontSize: 12, fontWeight: '700', color: '#8E8E93' },

  convictionPill: { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 999 },
  convictionText: { fontSize: 11, fontWeight: '800', letterSpacing: 0.5 },

  barTrack: { marginTop: 10, height: 6, backgroundColor: '#EBEBF0', borderRadius: 999, overflow: 'hidden' },
  barFill: { height: 6, backgroundColor: '#00cc99', borderRadius: 999 },

  grid3: { marginTop: 12, flexDirection: 'row', gap: 8 },
  cell: {
    flex: 1, backgroundColor: '#F8F9FB', borderWidth: 1, borderColor: '#EBEBF0',
    borderRadius: 12, paddingVertical: 10, paddingHorizontal: 10,
  },
  cellLabel: { fontSize: 10, color: '#8E8E93', fontWeight: '700', letterSpacing: 0.3 },
  cellValue: { marginTop: 4, fontSize: 13, color: '#0B0B0F', fontWeight: '800' },

  guardRow: { marginTop: 12, flexDirection: 'row', alignItems: 'center', gap: 8 },
  guardDot: { width: 8, height: 8, borderRadius: 4 },
  guardText: { color: '#6B7280', fontWeight: '600', fontSize: 12 },
  guardReason: { marginTop: 5, color: '#8E8E93', fontWeight: '600', fontSize: 12, lineHeight: 18 },

  whyBox: {
    marginTop: 12, backgroundColor: '#F8F9FB', borderWidth: 1, borderColor: '#EBEBF0',
    borderRadius: 12, padding: 12,
  },
  whyLine: { fontSize: 12, color: '#3A3A3C', fontWeight: '600', lineHeight: 20 },

  feedbackRow: { marginTop: 12, flexDirection: 'row', gap: 10 },
  feedbackBtn: {
    flex: 1, height: 42, borderRadius: 12, backgroundColor: '#F8F9FB', borderWidth: 1,
    borderColor: '#EBEBF0', alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 8,
  },
  feedbackText: { fontWeight: '700', color: '#3A3A3C', fontSize: 13 },

  scoreBox: {
    marginTop: 12, backgroundColor: '#F8F9FB', borderRadius: 12,
    borderWidth: 1, borderColor: '#EBEBF0', padding: 12,
  },
  scoreBig: { marginTop: 4, fontSize: 24, fontWeight: '800', color: '#0B0B0F' },

  btBox: { marginTop: 12 },
  detailsToggle: {
    marginTop: 10, paddingVertical: 10, paddingHorizontal: 10, borderRadius: 10,
    backgroundColor: '#F8F9FB', borderWidth: 1, borderColor: '#EBEBF0',
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
  },
  detailsToggleText: { fontSize: 12, fontWeight: '700', color: '#6B7280' },

  mono: {
    marginTop: 10, fontSize: 11, fontWeight: '600', color: '#3A3A3C',
    fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace' }),
  },

  fusionBox: { marginTop: 12 },
  rlBox: { marginTop: 12 },
  rlRow: {
    marginTop: 8, backgroundColor: '#F8F9FB', borderWidth: 1, borderColor: '#EBEBF0',
    borderRadius: 12, paddingVertical: 10, paddingHorizontal: 12,
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
  },
  rlStrategy: { fontWeight: '700', color: '#0B0B0F', fontSize: 13 },
  rlScore: { fontWeight: '700', color: '#6B7280', fontSize: 13 },

  bulletRow: { flexDirection: 'row', gap: 10, marginBottom: 8, alignItems: 'flex-start', marginTop: 8 },
  bulletDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#00cc99', marginTop: 7 },
  bulletText: { flex: 1, fontSize: 13, color: '#3A3A3C', fontWeight: '500', lineHeight: 20 },

  disclaimer: { marginTop: 12, fontSize: 11, color: '#AEAEB2', fontWeight: '500', textAlign: 'center' },

  // ── Decision Card ─────────────────────────────────────────────────────────
  decisionCard: {
    position: 'relative',
    marginBottom: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#EBEBF0',
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
  },
  // Teal accent bar — absolute, avoids iOS overflow:hidden + borderLeftWidth clip issue
  decisionAccentBar: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 4,
    backgroundColor: '#00cc99',
    zIndex: 1,
  },
  decisionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  decisionTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#0B0B0F',
    letterSpacing: 0.1,
  },

  // Verdict pill (standalone)
  verdictChip: {
    marginHorizontal: 16,
    marginBottom: 14,
    borderRadius: 12,
    paddingVertical: 13,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // Verdict pill inside Action+Confidence row (no margin, flex, same height as confidence)
  verdictChipInRow: {
    flex: 1,
    minHeight: 56,
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  verdictChipText: {
    fontSize: 15,
    fontWeight: '800',
    letterSpacing: 0.2,
    textAlign: 'center',
  },

  // Evidence bullets
  evidenceBox: {
    paddingHorizontal: 16,
    marginBottom: 10,
  },

  // Invalidation amber row
  invalidationRow: {
    marginHorizontal: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    backgroundColor: '#FFFBEB',
    borderWidth: 1,
    borderColor: '#FDE68A',
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  invalidationText: {
    flex: 1,
    fontSize: 12,
    fontWeight: '600',
    color: '#92400E',
    lineHeight: 18,
  },
  invalidationLabel: {
    fontWeight: '800',
    color: '#92400E',
  },

  // Risk grid wrapper (applies horizontal padding inside the card)
  decisionRiskWrap: {
    paddingHorizontal: 16,
    marginBottom: 12,
  },

  // Plain-English box wrapper + Simple view (first in expanded body)
  decisionWhyWrap: {
    paddingHorizontal: 16,
    paddingTop: 6,
    marginBottom: 12,
  },
  simpleViewLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#6B7280',
    marginBottom: 4,
    letterSpacing: 0.2,
  },
  simpleViewText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0B0B0F',
    lineHeight: 20,
  },
  actionConfidenceRow: {
    flexDirection: 'row',
    alignItems: 'stretch',
    paddingHorizontal: 16,
    marginBottom: 14,
    gap: 8,
  },
  confidencePill: {
    backgroundColor: '#F3F4F6',
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 12,
    minWidth: 80,
    justifyContent: 'center',
    alignItems: 'center',
  },
  confidencePillLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: '#6B7280',
    letterSpacing: 0.2,
  },
  confidencePillValue: {
    fontSize: 18,
    fontWeight: '800',
    color: '#0B0B0F',
  },
  riskOneLinerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginBottom: 10,
  },
  riskOneLinerLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#6B7280',
  },
  riskOneLinerValue: {
    fontSize: 13,
    fontWeight: '600',
    color: '#0B0B0F',
  },

  // Oracle hint
  decisionOracleHint: {
    marginHorizontal: 16,
    marginTop: 6,
    marginBottom: 4,
    fontSize: 11,
    fontWeight: '600',
    color: '#00cc99',
    textAlign: 'center',
  },
});
