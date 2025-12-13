import React, { useState, useEffect, useMemo } from 'react';
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
import { useQuery, gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import { API_RUST_BASE } from '../../config/api';

const GET_RUST_OPTIONS_ANALYSIS = gql`
  query GetRustOptionsAnalysis($symbol: String!) {
    rustOptionsAnalysis(symbol: $symbol) {
      symbol
      underlyingPrice
      volatilitySurface {
        atmVol
        skew
        termStructure
      }
      greeks {
        delta
        gamma
        theta
        vega
        rho
      }
      recommendedStrikes {
        strike
        expiration
        optionType
        greeks {
          delta
          gamma
          theta
          vega
          rho
        }
        expectedReturn
        riskScore
      }
      putCallRatio
      impliedVolatilityRank
      timestamp
    }
  }
`;

interface RustOptionsAnalysisWidgetProps {
  symbol: string;
}

type LoadState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; message: string; raw?: any }
  | { status: 'ready'; payload: any; ms?: number };

function safeNum(n: any): number | null {
  if (n === null || n === undefined) return null;
  const v = Number(n);
  return Number.isFinite(v) ? v : null;
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
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

export default function RustOptionsAnalysisWidget({ symbol }: RustOptionsAnalysisWidgetProps) {
  const [showExplain, setShowExplain] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  // Phase 2: Backtest
  const [showBacktest, setShowBacktest] = useState(false);
  const [strategy, setStrategy] = useState('options_iron_condor');
  const [backtest, setBacktest] = useState<LoadState>({ status: 'idle' });
  const [score, setScore] = useState<LoadState>({ status: 'idle' });

  // Phase 2: Cross-asset fusion
  const [showFusion, setShowFusion] = useState(false);
  const [fusion, setFusion] = useState<LoadState>({ status: 'idle' });

  // Phase 2: RL
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

  const { data, loading, error, refetch } = useQuery(GET_RUST_OPTIONS_ANALYSIS, {
    variables: { symbol },
    skip: !symbol,
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const analysis = data?.rustOptionsAnalysis;
  const volSurface = analysis?.volatilitySurface || {};
  const greeks = analysis?.greeks || {};

  // Compute IV regime from IV rank
  const ivRank = safeNum(analysis?.impliedVolatilityRank);
  const ivRegime = ivRank !== null
    ? ivRank < 30 ? 'Low' : ivRank < 70 ? 'Medium' : 'High'
    : 'Medium';

  // Compute trend from put/call ratio
  const pcr = safeNum(analysis?.putCallRatio);
  const trend = pcr !== null
    ? pcr > 1.2 ? 'BEARISH' : pcr < 0.8 ? 'BULLISH' : 'NEUTRAL'
    : 'NEUTRAL';

  // Phase 2 Actions
  async function runBacktest() {
    setBacktest({ status: 'loading' });
    try {
      const { json, ms } = await postJson('/v1/backtest/run', {
        strategy_name: strategy,
        symbol: symbol,
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
      const { json, ms } = await getJson(`/v1/backtest/score/${encodeURIComponent(strategy)}/${encodeURIComponent(symbol)}`);
      setScore({ status: 'ready', payload: json, ms });
    } catch (e: any) {
      setScore({ status: 'error', message: e?.message || 'Score error', raw: e?.raw });
    }
  }

  async function runFusion() {
    setFusion({ status: 'loading' });
    try {
      const { json, ms } = await postJson('/v1/cross-asset/signal', {
        primary_asset: symbol,
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
          regime_mood: trend === 'BULLISH' ? 'Greed' : trend === 'BEARISH' ? 'Fear' : 'Neutral',
          iv_regime: ivRegime,
          dte_bucket: '30-60',
          account_size_tier: 'Medium',
        },
        available_strategies: ['options_iron_condor', 'options_straddle', 'options_butterfly', 'options_credit_spread'],
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
            symbol: symbol,
            context: {
              regime_mood: trend === 'BULLISH' ? 'Greed' : trend === 'BEARISH' ? 'Fear' : 'Neutral',
              iv_regime: ivRegime,
              dte_bucket: '30-60',
              account_size_tier: 'Medium',
            },
            timestamp: new Date().toISOString(),
          },
          reward: reward > 0 ? 0.1 : -0.1,
          outcome: reward > 0 ? 'Win' : 'Loss',
          timestamp: new Date().toISOString(),
        },
      });
      setRlUpdate({ status: 'ready', payload: json, ms });
    } catch (e: any) {
      setRlUpdate({ status: 'error', message: e?.message || 'RL update error', raw: e?.raw });
    }
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="small" color="#0B0B0F" />
        <Text style={styles.loadingText}>Loading Rust analysis...</Text>
      </View>
    );
  }

  if (error || !analysis) {
    return null; // Fail silently
  }

  // Backtest parsing
  const backtestResp = backtest.status === 'ready' ? backtest.payload : null;
  const btSharpe = backtestResp ? safeNum(backtestResp.sharpe ?? backtestResp.sharpe_ratio) : null;
  const btWin = backtestResp ? safeNum(backtestResp.win_rate ?? backtestResp.winRate) : null;
  const btReturn = backtestResp ? safeNum(backtestResp.total_return ?? backtestResp.totalReturn ?? backtestResp.total_return_pct) : null;

  // Score response
  const scoreResp = score.status === 'ready' ? score.payload : null;
  const scoreVal =
    scoreResp === null ? null :
    typeof scoreResp === 'number' ? scoreResp :
    safeNum(scoreResp.score ?? scoreResp.value ?? scoreResp.overall_score ?? scoreResp.strategy_score);

  // Fusion parsing
  const fusionResp = fusion.status === 'ready' ? fusion.payload : null;
  const fusionSentence = fusionResp ? String(fusionResp.fusion_recommendation?.action ?? fusionResp.action ?? fusionResp.message ?? '') : '';
  const fusionScore = fusionResp ? safeNum(fusionResp.fusion_recommendation?.confidence ?? fusionResp.confidence ?? fusionResp.score) : null;

  // RL recommend parsing
  const rlResp = rlRec.status === 'ready' ? rlRec.payload : null;
  const rlItems: Array<{ strategy?: string; weight?: number; score?: number; strategy_name?: string }> =
    Array.isArray(rlResp?.recommended_strategies) ? rlResp.recommended_strategies :
    Array.isArray(rlResp?.recommendations) ? rlResp.recommendations :
    Array.isArray(rlResp) ? rlResp :
    [];

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="zap" size={16} color="#0B0B0F" />
        <Text style={styles.title}>Options Analysis</Text>
        <TouchableOpacity onPress={() => refetch({ symbol })} style={styles.refreshBtn} activeOpacity={0.8}>
          <Icon name="refresh-ccw" size={14} color="#0B0B0F" />
        </TouchableOpacity>
      </View>

      {/* Volatility Surface */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Volatility Surface</Text>
        <View style={styles.row}>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>ATM Vol</Text>
            <Text style={styles.metricValue}>{((volSurface.atmVol || 0) * 100).toFixed(1)}%</Text>
          </View>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Skew</Text>
            <Text style={styles.metricValue}>{((volSurface.skew || 0) * 100).toFixed(2)}%</Text>
          </View>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>IV Rank</Text>
            <Text style={styles.metricValue}>{ivRank !== null ? ivRank.toFixed(0) : 'N/A'}</Text>
          </View>
        </View>
      </View>

      {/* Greeks */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Greeks (ATM)</Text>
        <View style={styles.greeksGrid}>
          <View style={styles.greekItem}>
            <Text style={styles.greekLabel}>Δ Delta</Text>
            <Text style={styles.greekValue}>{greeks.delta?.toFixed(3) || 'N/A'}</Text>
          </View>
          <View style={styles.greekItem}>
            <Text style={styles.greekLabel}>Γ Gamma</Text>
            <Text style={styles.greekValue}>{greeks.gamma?.toFixed(3) || 'N/A'}</Text>
          </View>
          <View style={styles.greekItem}>
            <Text style={styles.greekLabel}>Θ Theta</Text>
            <Text style={styles.greekValue}>{greeks.theta?.toFixed(3) || 'N/A'}</Text>
          </View>
          <View style={styles.greekItem}>
            <Text style={styles.greekLabel}>ν Vega</Text>
            <Text style={styles.greekValue}>{greeks.vega?.toFixed(3) || 'N/A'}</Text>
          </View>
          <View style={styles.greekItem}>
            <Text style={styles.greekLabel}>ρ Rho</Text>
            <Text style={styles.greekValue}>{greeks.rho?.toFixed(3) || 'N/A'}</Text>
          </View>
        </View>
      </View>

      {/* Put/Call Ratio */}
      <View style={styles.section}>
        <View style={styles.row}>
          <Text style={styles.sectionTitle}>Put/Call Ratio</Text>
          <Text style={styles.pcrValue}>{pcr !== null ? pcr.toFixed(2) : 'N/A'}</Text>
        </View>
      </View>

      {/* Phase 2: Backtest - Prove it */}
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
          <TextInput value={strategy} onChangeText={setStrategy} style={styles.input} placeholder="options_iron_condor" />

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

      {/* Phase 2: Cross-asset fusion */}
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

      {/* Phase 2: RL - personalize */}
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
          <View style={styles.bulletRow}>
            <View style={styles.bulletDot} />
            <Text style={styles.bulletText}>
              IV Rank {ivRank !== null ? `${ivRank.toFixed(0)}%` : 'N/A'}: {ivRegime === 'Low' ? 'Low volatility — good for selling premium' : ivRegime === 'High' ? 'High volatility — good for buying protection' : 'Moderate volatility — balanced strategies'}
            </Text>
          </View>
          <View style={styles.bulletRow}>
            <View style={styles.bulletDot} />
            <Text style={styles.bulletText}>
              Put/Call Ratio {pcr !== null ? pcr.toFixed(2) : 'N/A'}: {pcr !== null && pcr > 1.2 ? 'Bearish sentiment — more puts than calls' : pcr !== null && pcr < 0.8 ? 'Bullish sentiment — more calls than puts' : 'Neutral sentiment'}
            </Text>
          </View>
          <View style={styles.bulletRow}>
            <View style={styles.bulletDot} />
            <Text style={styles.bulletText}>
              Greeks show how your position moves with price (delta), time (theta), volatility (vega), and interest rates (rho).
            </Text>
          </View>
          <Text style={styles.disclaimer}>Educational insights — not financial advice.</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#F1F1F4',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    justifyContent: 'space-between',
  },
  title: {
    fontSize: 16,
    fontWeight: '900',
    color: '#0B0B0F',
    marginLeft: 8,
    flex: 1,
  },
  refreshBtn: {
    width: 32,
    height: 32,
    borderRadius: 12,
    backgroundColor: '#FAFAFB',
    borderWidth: 1,
    borderColor: '#F1F1F4',
    alignItems: 'center',
    justifyContent: 'center',
  },
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '900',
    color: '#0B0B0F',
    marginBottom: 8,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metric: {
    flex: 1,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#71717A',
    fontWeight: '700',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '900',
    color: '#0B0B0F',
  },
  greeksGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  greekItem: {
    width: '18%',
    alignItems: 'center',
    marginBottom: 8,
  },
  greekLabel: {
    fontSize: 11,
    color: '#71717A',
    fontWeight: '700',
    marginBottom: 4,
  },
  greekValue: {
    fontSize: 14,
    fontWeight: '900',
    color: '#0B0B0F',
  },
  pcrValue: {
    fontSize: 18,
    fontWeight: '900',
    color: '#0B0B0F',
  },
  loadingText: {
    fontSize: 12,
    color: '#71717A',
    marginLeft: 8,
    fontWeight: '700',
  },
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
  toggleLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  toggleText: {
    fontSize: 13,
    fontWeight: '900',
    color: '#0B0B0F',
  },
  miniBadgeLight: {
    backgroundColor: '#EDEDF2',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 999,
    marginLeft: 6,
  },
  miniBadgeLightText: {
    color: '#0B0B0F',
    fontSize: 10,
    fontWeight: '900',
  },
  panel: {
    marginTop: 10,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: '#F1F1F4',
  },
  panelHint: {
    fontSize: 12,
    color: '#52525B',
    fontWeight: '800',
    lineHeight: 18,
  },
  smallLabel: {
    fontSize: 11,
    color: '#71717A',
    fontWeight: '900',
    marginBottom: 6,
    marginTop: 12,
  },
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
  twoBtnRow: {
    marginTop: 12,
    flexDirection: 'row',
    gap: 10,
  },
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
  secondaryBtnText: {
    fontWeight: '900',
    color: '#0B0B0F',
    fontSize: 13,
  },
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
  errorText: {
    flex: 1,
    color: '#B91C1C',
    fontWeight: '800',
    fontSize: 12,
  },
  scoreBox: {
    marginTop: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#F1F1F4',
    padding: 12,
  },
  scoreBig: {
    marginTop: 4,
    fontSize: 22,
    fontWeight: '900',
    color: '#0B0B0F',
  },
  btBox: {
    marginTop: 12,
  },
  grid3: {
    marginTop: 12,
    flexDirection: 'row',
    gap: 10,
  },
  cell: {
    flex: 1,
    backgroundColor: '#FAFAFB',
    borderWidth: 1,
    borderColor: '#F1F1F4',
    borderRadius: 14,
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  cellLabel: {
    fontSize: 10,
    color: '#71717A',
    fontWeight: '900',
  },
  cellValue: {
    marginTop: 4,
    fontSize: 12,
    color: '#0B0B0F',
    fontWeight: '900',
  },
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
  detailsToggleText: {
    fontSize: 12,
    fontWeight: '900',
    color: '#111827',
  },
  mono: {
    marginTop: 10,
    fontSize: 11,
    fontWeight: '700',
    color: '#111827',
    fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace' }),
  },
  mutedTiny: {
    marginTop: 8,
    color: '#A1A1AA',
    fontWeight: '700',
    fontSize: 11,
  },
  fusionBox: {
    marginTop: 12,
  },
  bigSentence: {
    fontSize: 14,
    fontWeight: '900',
    color: '#0B0B0F',
    lineHeight: 20,
  },
  guardRow: {
    marginTop: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  guardDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  guardText: {
    color: '#52525B',
    fontWeight: '800',
    fontSize: 12,
  },
  rlBox: {
    marginTop: 12,
  },
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
  rlStrategy: {
    fontWeight: '900',
    color: '#0B0B0F',
  },
  rlScore: {
    fontWeight: '900',
    color: '#52525B',
  },
  muted: {
    marginTop: 6,
    color: '#71717A',
    fontWeight: '600',
  },
  bulletRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 10,
    alignItems: 'flex-start',
    marginTop: 8,
  },
  bulletDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#0B0B0F',
    marginTop: 6,
  },
  bulletText: {
    flex: 1,
    fontSize: 12,
    color: '#52525B',
    fontWeight: '700',
    lineHeight: 18,
  },
  disclaimer: {
    marginTop: 12,
    fontSize: 11,
    color: '#A1A1AA',
    fontWeight: '700',
    textAlign: 'center',
  },
});
