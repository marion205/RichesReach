import React, { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
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

async function postJson(path: string, body: any) {
  if (!API_RUST_BASE) throw new Error('Missing API_RUST_BASE');
  const t0 = Date.now();
  const res = await fetch(`${API_RUST_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
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

  const [analysis, setAnalysis] = useState<ForexAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchForexAnalysis = async (pairToFetch: string) => {
    if (!pairToFetch) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_RUST_BASE}/v1/forex/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pair: pairToFetch }),
      });
      
      if (!response.ok) {
        // Try to get error message from response
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
        
        // Provide user-friendly error messages
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
      console.error('Forex analysis error:', err);
      setError(err);
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (pair) {
      fetchForexAnalysis(pair);
    }
  }, [pair]);

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

  // ---- Actions: Alpha Oracle / Backtest / Fusion / RL ----

  async function askAlphaOracle() {
    const entry = computed.mid ?? computed.bid ?? computed.ask;
    const eq = safeNum(equity);
    const open = Math.max(0, parseInt(openPositions || '0', 10));

    if (!entry) return setOracle({ status: 'error', message: 'No price available yet.' });
    if (!eq || eq <= 0) return setOracle({ status: 'error', message: 'Equity must be a positive number.' });

    setOracle({ status: 'loading' });

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
    try {
      const { json, ms } = await postJson('/v1/backtest/run', {
        strategy_name: strategy,
        symbol: pair,
        signals: [], // In production, this would come from historical data
        config: null,
      });
      setBacktest({ status: 'ready', payload: json, ms });
    } catch (e: any) {
      setBacktest({ status: 'error', message: e?.message || 'Backtest error', raw: e?.raw });
    }
  }

  async function fetchBacktestScore() {
    setScore({ status: 'loading' });
    try {
      const { json, ms } = await getJson(`/v1/backtest/score/${encodeURIComponent(strategy)}/${encodeURIComponent(pair)}`);
      setScore({ status: 'ready', payload: json, ms });
    } catch (e: any) {
      setScore({ status: 'error', message: e?.message || 'Score error', raw: e?.raw });
    }
  }

  async function runFusion() {
    setFusion({ status: 'loading' });
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
          <ActivityIndicator size="small" color="#0B0B0F" />
          <Text style={styles.skeletonText}>Updating…</Text>
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

  // Compact mode stays simple
  if (isCompact) {
    return (
      <View style={styles.compactWrap}>
        <View style={styles.compactTop}>
          <View style={[styles.dot, { backgroundColor: computed.tColor }]} />
          <Text style={styles.compactPair}>{computed.pairPretty}</Text>
        </View>

        <View style={styles.compactPrices}>
          <View style={styles.compactPriceItem}>
            <Text style={styles.compactLabel}>Bid</Text>
            <Text style={styles.compactValue}>{fmt5(computed.bid)}</Text>
          </View>
          <View style={styles.compactPriceItem}>
            <Text style={styles.compactLabel}>Ask</Text>
            <Text style={styles.compactValue}>{fmt5(computed.ask)}</Text>
          </View>
        </View>

        <View style={styles.compactFooter}>
          <Text style={styles.compactFooterText}>
            {computed.vLabel} • {computed.exLabel}
          </Text>
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
      {/* Header */}
      <View style={styles.topHeader}>
        <View style={styles.topHeaderLeft}>
          <View style={[styles.dot, { backgroundColor: computed.tColor }]} />
          <Text style={styles.topTitle}>Today's Read</Text>
        </View>

        <TouchableOpacity onPress={() => fetchForexAnalysis(pair)} style={styles.refreshBtn} activeOpacity={0.8}>
          <Icon name="refresh-ccw" size={16} color="#0B0B0F" />
        </TouchableOpacity>
      </View>

      <Text style={styles.heroLine}>{computed.headline}</Text>
      <Text style={styles.heroSubline}>{computed.subline}</Text>

      {/* Search */}
      <View style={styles.searchContainer}>
        <Text style={styles.searchLabel}>Currency pair</Text>
        <View style={styles.searchRow}>
          <TextInput
            style={styles.searchInput}
            placeholder="EURUSD"
            value={inputValue}
            onChangeText={setInputValue}
            autoCapitalize="characters"
            autoCorrect={false}
            returnKeyType="search"
            onSubmitEditing={handleSearch}
          />
          <TouchableOpacity style={styles.searchButton} onPress={handleSearch} activeOpacity={0.85}>
            <Icon name="search" size={16} color="#FFFFFF" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Prices */}
      <View style={styles.prices}>
        <View style={styles.priceCard}>
          <Text style={styles.priceLabel}>Bid</Text>
          <Text style={styles.priceValue}>{fmt5(computed.bid)}</Text>
        </View>
        <View style={styles.priceCard}>
          <Text style={styles.priceLabel}>Ask</Text>
          <Text style={styles.priceValue}>{fmt5(computed.ask)}</Text>
        </View>
        <View style={styles.priceCard}>
          <Text style={styles.priceLabel}>Spread</Text>
          <Text style={styles.priceValue}>{computed.spread !== null ? computed.spread.toFixed(5) : '—'}</Text>
        </View>
      </View>

      {/* 3 lights */}
      <View style={styles.lightsRow}>
        <View style={styles.lightCard}>
          <Text style={styles.lightTitle}>Trend</Text>
          <View style={[styles.pill, { backgroundColor: computed.tColor + '22' }]}>
            <Text style={[styles.pillText, { color: computed.tColor }]} numberOfLines={1} adjustsFontSizeToFit>{computed.tLabel}</Text>
          </View>
        </View>
        <View style={styles.lightCard}>
          <Text style={styles.lightTitle}>Volatility</Text>
          <View style={[styles.pill, { backgroundColor: computed.vColor + '22' }]}>
            <Text style={[styles.pillText, { color: computed.vColor }]} numberOfLines={1} adjustsFontSizeToFit>{computed.vLabel}</Text>
          </View>
        </View>
        <View style={styles.lightCard}>
          <Text style={styles.lightTitle}>Execution</Text>
          <View style={[styles.pill, { backgroundColor: computed.exColor + '22' }]}>
            <Text style={[styles.pillText, { color: computed.exColor }]} numberOfLines={1} adjustsFontSizeToFit>{computed.exLabel}</Text>
          </View>
        </View>
      </View>

      {/* Alpha Oracle */}
      <TouchableOpacity
        activeOpacity={0.9}
        onPress={() => { LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut); setShowOracle(v => !v); }}
        style={styles.toggle}
      >
        <View style={styles.toggleLeft}>
          <Icon name="zap" size={16} color="#0B0B0F" />
          <Text style={styles.toggleText}>Alpha Oracle</Text>
          <View style={styles.miniBadge}><Text style={styles.miniBadgeText}>1 tap</Text></View>
        </View>
        <Icon name={showOracle ? 'chevron-up' : 'chevron-down'} size={18} color="#0B0B0F" />
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
            <View style={styles.errorBox}>
              <Icon name="alert-circle" size={16} color="#EF4444" />
              <Text style={styles.errorText}>{oracle.message}</Text>
            </View>
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
          <Icon name="check-circle" size={16} color="#0B0B0F" />
          <Text style={styles.toggleText}>Prove it</Text>
          <View style={styles.miniBadgeLight}><Text style={styles.miniBadgeLightText}>backtest</Text></View>
        </View>
        <Icon name={showBacktest ? 'chevron-up' : 'chevron-down'} size={18} color="#0B0B0F" />
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
          <Icon name="shuffle" size={16} color="#0B0B0F" />
          <Text style={styles.toggleText}>Across markets</Text>
          <View style={styles.miniBadgeLight}><Text style={styles.miniBadgeLightText}>fusion</Text></View>
        </View>
        <Icon name={showFusion ? 'chevron-up' : 'chevron-down'} size={18} color="#0B0B0F" />
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
          <Icon name="cpu" size={16} color="#0B0B0F" />
          <Text style={styles.toggleText}>Personalize</Text>
          <View style={styles.miniBadgeLight}><Text style={styles.miniBadgeLightText}>RL</Text></View>
        </View>
        <Icon name={showRL ? 'chevron-up' : 'chevron-down'} size={18} color="#0B0B0F" />
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
          <Icon name="info" size={16} color="#0B0B0F" />
          <Text style={styles.toggleText}>Explain it simply</Text>
        </View>
        <Icon name={showExplain ? 'chevron-up' : 'chevron-down'} size={18} color="#0B0B0F" />
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
  container: { backgroundColor: '#FFFFFF', borderRadius: 18, padding: 16, borderWidth: 1, borderColor: '#F1F1F4' },
  containerCompact: { padding: 0, borderWidth: 0, backgroundColor: 'transparent' },

  skeletonRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10 },
  skeletonText: { marginLeft: 10, color: '#52525B', fontWeight: '600' },
  inlineHeader: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  inlineHeaderText: { fontSize: 14, fontWeight: '800', color: '#111827' },
  muted: { marginTop: 6, color: '#71717A', fontWeight: '600' },
  mutedTiny: { marginTop: 8, color: '#A1A1AA', fontWeight: '700', fontSize: 11 },

  compactWrap: { backgroundColor: '#FFFFFF', borderRadius: 14, padding: 10, borderWidth: 1, borderColor: '#F2F2F6' },
  compactTop: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  compactPair: { fontSize: 13, fontWeight: '900', color: '#0B0B0F' },
  compactPrices: { flexDirection: 'row', justifyContent: 'space-between', gap: 8 },
  compactPriceItem: {
    flex: 1, backgroundColor: '#FAFAFB', borderRadius: 12, paddingVertical: 8, paddingHorizontal: 10,
    borderWidth: 1, borderColor: '#F1F1F4',
  },
  compactLabel: { fontSize: 10, color: '#71717A', fontWeight: '700' },
  compactValue: { marginTop: 2, fontSize: 13, fontWeight: '900', color: '#0B0B0F' },
  compactFooter: { marginTop: 8, alignItems: 'center' },
  compactFooterText: { fontSize: 11, color: '#71717A', fontWeight: '700' },

  topHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  topHeaderLeft: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  topTitle: { fontSize: 14, fontWeight: '900', color: '#0B0B0F' },
  refreshBtn: {
    width: 36, height: 36, borderRadius: 12, backgroundColor: '#FAFAFB',
    borderWidth: 1, borderColor: '#F1F1F4', alignItems: 'center', justifyContent: 'center',
  },

  dot: { width: 10, height: 10, borderRadius: 5 },

  heroLine: { marginTop: 10, fontSize: 18, fontWeight: '900', color: '#0B0B0F', letterSpacing: -0.2 },
  heroSubline: { marginTop: 6, fontSize: 13, color: '#71717A', fontWeight: '700' },

  searchContainer: { marginTop: 14 },
  searchLabel: { fontSize: 12, color: '#71717A', fontWeight: '700', marginBottom: 8 },
  searchRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  searchInput: {
    flex: 1, height: 44, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#E5E7EB',
    borderRadius: 14, paddingHorizontal: 14, fontSize: 14, fontWeight: '700', color: '#0B0B0F',
  },
  searchButton: { width: 44, height: 44, backgroundColor: '#0B0B0F', borderRadius: 14, justifyContent: 'center', alignItems: 'center' },

  prices: { marginTop: 14, flexDirection: 'row', gap: 10 },
  priceCard: {
    flex: 1, backgroundColor: '#FAFAFB', borderRadius: 14, paddingVertical: 12, paddingHorizontal: 12,
    borderWidth: 1, borderColor: '#F1F1F4',
  },
  priceLabel: { fontSize: 11, color: '#71717A', fontWeight: '800' },
  priceValue: { marginTop: 5, fontSize: 15, fontWeight: '900', color: '#0B0B0F' },

  lightsRow: { marginTop: 12, flexDirection: 'row', gap: 10 },
  lightCard: { flex: 1, backgroundColor: '#FFFFFF', borderRadius: 14, padding: 12, borderWidth: 1, borderColor: '#F1F1F4' },
  lightTitle: { fontSize: 11, color: '#71717A', fontWeight: '900', marginBottom: 8 },
  pill: { alignSelf: 'flex-start', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999 },
  pillText: { fontSize: 13, fontWeight: '900' },

  toggle: {
    marginTop: 12,
    backgroundColor: '#FAFAFB',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#F1F1F4',
    paddingVertical: 12,
    paddingHorizontal: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  toggleLeft: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  toggleText: { fontSize: 13, fontWeight: '900', color: '#0B0B0F' },

  miniBadge: { backgroundColor: '#0B0B0F', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 999, marginLeft: 6 },
  miniBadgeText: { color: '#FFFFFF', fontSize: 10, fontWeight: '900' },
  miniBadgeLight: { backgroundColor: '#EDEDF2', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 999, marginLeft: 6 },
  miniBadgeLightText: { color: '#0B0B0F', fontSize: 10, fontWeight: '900' },

  panel: { marginTop: 10, backgroundColor: '#FFFFFF', borderRadius: 16, padding: 14, borderWidth: 1, borderColor: '#F1F1F4' },
  panelHint: { fontSize: 12, color: '#52525B', fontWeight: '800', lineHeight: 18 },

  inputRow: { marginTop: 12, flexDirection: 'row', gap: 10, alignItems: 'flex-end' },
  smallLabel: { fontSize: 11, color: '#71717A', fontWeight: '900', marginBottom: 6 },

  input: {
    height: 44,
    backgroundColor: '#FAFAFB',
    borderWidth: 1,
    borderColor: '#F1F1F4',
    borderRadius: 14,
    paddingHorizontal: 12,
    fontSize: 13,
    fontWeight: '900',
    color: '#0B0B0F',
  },
  moneyInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FAFAFB',
    borderWidth: 1,
    borderColor: '#F1F1F4',
    borderRadius: 14,
    paddingHorizontal: 12,
    height: 44,
    gap: 8,
  },
  moneyPrefix: { fontSize: 13, fontWeight: '900', color: '#0B0B0F' },
  moneyInput: { flex: 1, height: 44, fontSize: 13, fontWeight: '900', color: '#0B0B0F' },

  primaryBtn: {
    marginTop: 12,
    height: 46,
    borderRadius: 14,
    backgroundColor: '#0B0B0F',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },
  primaryBtnText: { marginLeft: 10, color: '#FFFFFF', fontWeight: '900', fontSize: 13 },

  twoBtnRow: { marginTop: 12, flexDirection: 'row', gap: 10 },
  secondaryBtn: {
    flex: 1,
    height: 46,
    borderRadius: 14,
    backgroundColor: '#FAFAFB',
    borderWidth: 1,
    borderColor: '#F1F1F4',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  secondaryBtnFull: {
    marginTop: 12,
    height: 46,
    borderRadius: 14,
    backgroundColor: '#FAFAFB',
    borderWidth: 1,
    borderColor: '#F1F1F4',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  secondaryBtnText: { fontWeight: '900', color: '#0B0B0F', fontSize: 13 },

  errorBox: {
    marginTop: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FEE2E2',
    padding: 10,
    borderRadius: 14,
  },
  errorText: { flex: 1, color: '#B91C1C', fontWeight: '800', fontSize: 12 },

  bigSentence: { fontSize: 14, fontWeight: '900', color: '#0B0B0F', lineHeight: 20 },

  scoreRow: { marginTop: 12, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 10 },
  scoreValue: { marginTop: 2, fontSize: 18, fontWeight: '900', color: '#0B0B0F' },
  scoreOutOf: { fontSize: 12, fontWeight: '900', color: '#71717A' },

  convictionPill: { paddingHorizontal: 10, paddingVertical: 7, borderRadius: 999 },
  convictionText: { fontSize: 11, fontWeight: '900', letterSpacing: 0.5 },

  barTrack: { marginTop: 10, height: 10, backgroundColor: '#F1F1F4', borderRadius: 999, overflow: 'hidden' },
  barFill: { height: 10, backgroundColor: '#0B0B0F', borderRadius: 999 },

  grid3: { marginTop: 12, flexDirection: 'row', gap: 10 },
  cell: {
    flex: 1,
    backgroundColor: '#FAFAFB',
    borderWidth: 1,
    borderColor: '#F1F1F4',
    borderRadius: 14,
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  cellLabel: { fontSize: 10, color: '#71717A', fontWeight: '900' },
  cellValue: { marginTop: 4, fontSize: 12, color: '#0B0B0F', fontWeight: '900' },

  guardRow: { marginTop: 12, flexDirection: 'row', alignItems: 'center', gap: 8 },
  guardDot: { width: 10, height: 10, borderRadius: 5 },
  guardText: { color: '#52525B', fontWeight: '800', fontSize: 12 },
  guardReason: { marginTop: 6, color: '#71717A', fontWeight: '800', fontSize: 12, lineHeight: 18 },

  whyBox: {
    marginTop: 12,
    backgroundColor: '#FAFAFB',
    borderWidth: 1,
    borderColor: '#F1F1F4',
    borderRadius: 14,
    padding: 10,
  },
  whyLine: { fontSize: 12, color: '#52525B', fontWeight: '800', lineHeight: 18 },

  feedbackRow: { marginTop: 12, flexDirection: 'row', gap: 10 },
  feedbackBtn: {
    flex: 1,
    height: 44,
    borderRadius: 14,
    backgroundColor: '#FAFAFB',
    borderWidth: 1,
    borderColor: '#F1F1F4',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  feedbackText: { fontWeight: '900', color: '#0B0B0F', fontSize: 13 },

  scoreBox: {
    marginTop: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#F1F1F4',
    padding: 12,
  },
  scoreBig: { marginTop: 4, fontSize: 22, fontWeight: '900', color: '#0B0B0F' },

  btBox: { marginTop: 12 },
  detailsToggle: {
    marginTop: 12,
    paddingVertical: 10,
    paddingHorizontal: 10,
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#F1F1F4',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailsToggleText: { fontSize: 12, fontWeight: '900', color: '#111827' },

  mono: {
    marginTop: 10,
    fontSize: 11,
    fontWeight: '700',
    color: '#111827',
    fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace' }),
  },

  fusionBox: { marginTop: 12 },
  rlBox: { marginTop: 12 },
  rlRow: {
    marginTop: 10,
    backgroundColor: '#FAFAFB',
    borderWidth: 1,
    borderColor: '#F1F1F4',
    borderRadius: 14,
    paddingVertical: 10,
    paddingHorizontal: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  rlStrategy: { fontWeight: '900', color: '#0B0B0F' },
  rlScore: { fontWeight: '900', color: '#52525B' },

  bulletRow: { flexDirection: 'row', gap: 10, marginBottom: 10, alignItems: 'flex-start', marginTop: 8 },
  bulletDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#0B0B0F', marginTop: 6 },
  bulletText: { flex: 1, fontSize: 12, color: '#52525B', fontWeight: '700', lineHeight: 18 },

  disclaimer: { marginTop: 12, fontSize: 11, color: '#A1A1AA', fontWeight: '700', textAlign: 'center' },
});
