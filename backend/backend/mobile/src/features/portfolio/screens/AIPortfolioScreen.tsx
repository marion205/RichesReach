import React, { useCallback, useEffect, useMemo, useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  SafeAreaView,
  RefreshControl,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  FlatList,
} from 'react-native';

// 🔥 FILE LOADED INDICATOR - If you see this, the updated code is being used
console.log('🔥 FILE LOADED: AIPortfolioScreen.tsx with updated validation logic');
import Icon from 'react-native-vector-icons/Feather';
import { useMutation, useQuery, gql, useApolloClient } from '@apollo/client';
import AsyncStorage from '@react-native-async-storage/async-storage';
import TradingButton from '../../../components/forms/TradingButton';
import { StableNumberInput } from '../../../components/StableNumberInput';

/* -------------------------------- THEME ---------------------------------- */
const COLORS = {
  bg: '#F2F2F7',
  card: '#FFFFFF',
  border: '#E2E8F0',
  text: '#1F2937',
  subtext: '#6B7280',
  primary: '#00cc99',
  warning: '#F59E0B',
  danger: '#EF4444',
  success: '#10B981',
  muted: '#F3F4F6',
  pill: '#F9FAFB',
};

const SPACING = 16;

/* ------------------------------ GRAPHQL ----------------------------------- */
const GET_USER_PROFILE = gql`
  query GetUserProfile {
    me {
      id
      name
      email
      incomeProfile {
        incomeBracket
        age
        investmentGoals
        riskTolerance
        investmentHorizon
      }
    }
  }
`;

const GET_AI_RECOMMENDATIONS = gql`
  query GetAIRecommendations {
    aiRecommendations {
      portfolioAnalysis {
        totalValue
        numHoldings
        sectorBreakdown
        riskScore
        diversificationScore
        expectedImpact {
          evPct
          evAbs
          per10k
        }
        risk {
          volatilityEstimate
          maxDrawdownPct
        }
        assetAllocation {
          stocks
          bonds
          cash
        }
      }
      buyRecommendations {
        symbol
        companyName
        recommendation
        confidence
        reasoning
        targetPrice
        currentPrice
        expectedReturn    # decimal like 0.05 = 5%
        allocation        # percentage allocation like 25.3
      }
      sellRecommendations {
        symbol
        reasoning
      }
      rebalanceSuggestions {
        action
        currentAllocation
        suggestedAllocation
        reasoning
        priority
      }
      riskAssessment {
        overallRisk
        volatilityEstimate   # percent value if backend provides (e.g., 12.8)
        recommendations
      }
      marketOutlook {
        overallSentiment
        confidence
        keyFactors
      }
    }
  }
`;

const GET_QUANT_SCREENER = gql`
  query GetQuantScreener {
    advancedStockScreening {
      symbol
      sector
      peRatio
      dividendYield
      volatility
      debtRatio
      mlScore
      score
    }
  }
`;

const CREATE_INCOME_PROFILE = gql`
  mutation CreateIncomeProfile(
    $incomeBracket: String!
    $age: Int!
    $investmentGoals: [String!]!
    $riskTolerance: String!
    $investmentHorizon: String!
  ) {
    createIncomeProfile(
      incomeBracket: $incomeBracket
      age: $age
      investmentGoals: $investmentGoals
      riskTolerance: $riskTolerance
      investmentHorizon: $investmentHorizon
    ) {
      success
      message
    }
  }
`;

const GENERATE_AI_RECOMMENDATIONS = gql`
  mutation GenerateAIRecommendations {
    generateAiRecommendations {
      success
      message
      recommendations {
        id
        riskProfile
        portfolioAllocation
        recommendedStocks
        expectedPortfolioReturn
        riskAssessment
      }
    }
  }
`;

/* -------------------------------- TYPES ----------------------------------- */
interface AIPortfolioScreenProps {
  navigateTo?: (screen: string) => void;
}

/* ------------------------------ UTILITIES --------------------------------- */
type RT = 'Conservative' | 'Moderate' | 'Aggressive' | '';

const allocationFromRisk: Record<RT, { stocks: string; bonds: string; etfs: string; cash: string }> = {
  Conservative: { stocks: '30%', bonds: '50%', etfs: '15%', cash: '5%' },
  Moderate:     { stocks: '60%', bonds: '30%', etfs: '8%',  cash: '2%' },
  Aggressive:   { stocks: '80%', bonds: '15%', etfs: '3%',  cash: '2%' },
  '':           { stocks: '—',   bonds: '—',   etfs: '—',    cash: '—' },
};

const fallbackVolByRT: Record<RT, number> = {
  Conservative: 8.2,
  Moderate: 12.8,
  Aggressive: 18.5,
  '': 12.8,
};

const fallbackMddByRT: Record<RT, string> = {
  Conservative: '15.0%',
  Moderate: '32.0%',
  Aggressive: 'N/A',
  '': 'N/A',
};

const fmtPct = (v?: number | null) => {
  if (v == null || Number.isNaN(Number(v))) return 'N/A';
  return `${Number(v).toFixed(1)}%`;
};

const fmtMoney = (v?: number | null) => {
  if (v == null || Number.isNaN(Number(v))) return 'N/A';
  return `$${Number(v).toLocaleString()}`;
};

/**
 * Prefer backend volatility if available (ai.riskAssessment.volatilityEstimate).
 * If backend returns e.g. 12.8 (meaning 12.8%), we display "12.8%".
 * Otherwise, we fall back to riskTolerance-based defaults.
 */
const getVolatility = (
  ai: any | undefined,
  riskTolerance: RT
): string => {
  const backendVol = ai?.riskAssessment?.volatilityEstimate;
  if (backendVol != null && !Number.isNaN(Number(backendVol))) {
    return fmtPct(Number(backendVol));
  }
  return fmtPct(fallbackVolByRT[riskTolerance]);
};

/**
 * We don’t have drawdown in the query; use a clean fallback map by risk tolerance.
 */
const getMaxDrawdown = (riskTolerance: RT): string => {
  return fallbackMddByRT[riskTolerance];
};

/**
 * Expected Value (EV) of applying the NEW recommendations.
 * Uses confidence-weighted expectedReturn from buyRecommendations.
 * - If portfolio total value is known: EV$ = totalValue * weightedAvgReturn
 * - If not: show EV per $10k invested.
 */
const computeExpectedImpact = (ai: any, totalValue?: number | null) => {
  const recs: Array<{ expectedReturn?: number | null; confidence?: number | null }> =
    ai?.buyRecommendations || [];

  if (!recs.length) {
    return { evPct: null, evAbs: null, per10k: null };
  }

  let weightSum = 0;
  let weightedReturn = 0;

  for (const r of recs) {
    const er = Number(r?.expectedReturn ?? 0);   // e.g., 0.05 = 5%
    let w = Number(r?.confidence ?? 0.5);        // default 0.5 if missing
    if (w < 0) w = 0;
    if (w > 1) w = 1;
    weightedReturn += er * w;
    weightSum += w;
  }

  const evPct = weightSum > 0 ? (weightedReturn / weightSum) : null; // decimal (e.g., 0.04)
  const evAbs = totalValue != null && evPct != null ? totalValue * evPct : null;
  const per10k = evPct != null ? 10000 * evPct : null;

  return { evPct, evAbs, per10k };
};

const getRiskColor = (riskLevel: string) => {
  switch ((riskLevel || '').toLowerCase()) {
    case 'low':
      return COLORS.success;
    case 'medium':
      return COLORS.warning;
    case 'high':
      return COLORS.danger;
    default:
      return COLORS.subtext;
  }
};

/* ------------------------------ QUANTITATIVE UTILITIES ----------------------- */

type ProfileLite = {
  riskTolerance: RT;
  investmentHorizon?: string;
  investmentGoals?: string[];
};

type FactorWeights = {
  value: number; quality: number; momentum: number; lowVol: number; yield: number;
};

type ScreenerRow = {
  symbol: string; sector?: string; peRatio?: number; dividendYield?: number;
  volatility?: number; debtRatio?: number; mlScore?: number; score?: number;
};

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

function profileToPolicy(p: ProfileLite) {
  const risk = p.riskTolerance || 'Moderate';
  const volTarget = { Conservative: 0.08, Moderate: 0.13, Aggressive: 0.18 }[risk];
  const nameCap = { Conservative: 0.04, Moderate: 0.06, Aggressive: 0.08 }[risk];
  const sectorCap = { Conservative: 0.25, Moderate: 0.30, Aggressive: 0.35 }[risk];

  const horizon = (p.investmentHorizon || '').toLowerCase();
  const shortH = horizon.includes('1-3') || horizon.includes('3-5');
  const turnoverBudget = shortH ? 0.80 : 0.35; // portion of book you'll allow to turn per rebalance

  return { volTarget, nameCap, sectorCap, turnoverBudget };
}

function profileToFactorTilts(p: ProfileLite): FactorWeights {
  // base weights sum to ~1
  let w: FactorWeights = { value: 0.22, quality: 0.22, momentum: 0.22, lowVol: 0.18, yield: 0.16 };

  // risk tolerance nudges
  if (p.riskTolerance === 'Conservative') { w.lowVol += 0.10; w.yield += 0.05; w.momentum -= 0.10; }
  if (p.riskTolerance === 'Aggressive')   { w.momentum += 0.12; w.value += 0.05; w.lowVol -= 0.10; }

  // goals nudges
  const goals = (p.investmentGoals || []).map(g => g.toLowerCase());
  if (goals.some(g => /passive income|dividend/.test(g))) { w.yield += 0.12; w.lowVol += 0.05; }
  if (goals.some(g => /wealth|growth/.test(g)))            { w.momentum += 0.08; w.quality += 0.05; }
  if (goals.some(g => /retire|retirement/.test(g)))        { w.lowVol += 0.06; w.quality += 0.04; }

  // horizon tilt (shorter horizon → a bit more momentum)
  const hz = (p.investmentHorizon || '').toLowerCase();
  if (hz.includes('1-3') || hz.includes('3-5')) { w.momentum += 0.05; }

  // normalize
  const sum = Object.values(w).reduce((a, b) => a + b, 0);
  for (const k in w) (w as any)[k] = (w as any)[k] / sum;
  return w;
}

function toFactors(rows: ScreenerRow[]) {
  // Proxies:
  //  - value     ~ 1/PE
  //  - quality   ~ -debtRatio
  //  - momentum  ~ mlScore
  //  - lowVol    ~ -volatility
  //  - yield     ~ dividendYield
  const raw = rows.map(r => ({
    symbol: r.symbol,
    value: r.peRatio != null ? 1 / Math.max(r.peRatio, 1e-6) : null,
    quality: r.debtRatio != null ? -r.debtRatio : null,
    momentum: r.mlScore ?? r.score ?? null,
    lowVol: r.volatility != null ? -r.volatility : null,
    yield: r.dividendYield ?? null,
    sector: r.sector || 'Other',
  }));

  // z-score by sector to avoid naive sector bets
  const bySector: Record<string, any[]> = {};
  raw.forEach(x => { (bySector[x.sector] ||= []).push(x); });

  const zmap: Record<string, any> = {};
  for (const s of Object.keys(bySector)) {
    const bucket = bySector[s];
    const keys: (keyof FactorWeights)[] = ['value','quality','momentum','lowVol','yield'];
    const stats: Record<string,{m:number;sd:number}> = {};
    for (const k of keys) {
      const arr = bucket.map(b => b[k]).filter(v => v != null) as number[];
      const m = arr.length ? arr.reduce((a,b)=>a+b,0)/arr.length : 0;
      const sd = Math.sqrt(Math.max(1e-9, arr.reduce((a,b)=>a+(b-m)**2,0)/(arr.length||1)));
      stats[k] = { m, sd };
    }
    for (const b of bucket) {
      const z: any = { symbol: b.symbol, sector: s };
      for (const k of keys) {
        const {m,sd} = stats[k];
        const v = (b as any)[k];
        z[k] = v==null ? 0 : (v - m)/sd; // missing → neutral
      }
      zmap[z.symbol] = z;
    }
  }
  return zmap as Record<string, {symbol:string; sector:string} & FactorWeights>;
}

function blendScores(
  rec: any,
  z: Partial<FactorWeights> | undefined,
  w: FactorWeights,
  horizon: string | undefined
) {
  const factorScore =
    (z?.value ?? 0)*w.value +
    (z?.quality ?? 0)*w.quality +
    (z?.momentum ?? 0)*w.momentum +
    (z?.lowVol ?? 0)*w.lowVol +
    (z?.yield ?? 0)*w.yield;

  // normalize AI signal ~ expectedReturn * confidence
  const ai = (Number(rec?.expectedReturn ?? 0) * Number(rec?.confidence ?? 0));
  // relative weight: longer horizon → more factor, shorter → more "AI"
  const shortH = (horizon || '').match(/^(1-3|3-5)/i);
  const alpha = shortH ? 0.45 : 0.65; // weight on factorScore
  return alpha * factorScore + (1 - alpha) * ai;
}

/* ------------------------------ INCOME-AWARE POLICY ----------------------- */

type Policy = {
  volTarget?: number;         // annualized (e.g., 0.12 = 12%)
  nameCap: number;            // per-name max weight
  sectorCap: number;          // per-sector max weight
  turnoverBudget?: number;    // ||w - w_prev||_1
  cashFloorPct: number;       // min cash to keep
  perTradeMaxPct: number;     // of portfolio
  positionMinPct: number;     // avoid dust
  preferETFs: boolean;
  sectorOverrides?: Record<string, number>;
  excludeHighVol?: number;    // exclude names with ann. vol > x
  minMarketCap?: number;      // USD
};

function derivePolicyFromProfile(profile: {
  incomeBracket?: string;
  riskTolerance?: RT;
  investmentHorizon?: string; // '1-3 years' | '3-5 years' | '5-10 years' | '10+ years'
  investmentGoals?: string[];
}, totalValue?: number | null): Policy {
  const income = (profile.incomeBracket || '').toLowerCase();
  const rt = (profile.riskTolerance || 'Moderate') as RT;
  const horizon = (profile.investmentHorizon || '').toLowerCase();
  const goals = profile.investmentGoals || [];

  // Base by income bracket
  let volTarget = 0.12, cashFloor = 0.08, nameCap = 0.06, sectorCap = 0.30,
      perTradeMax = 0.03, posMin = 0.005, preferETFs = false,
      excludeHighVol = 0.55, minMC = 2e9, turnoverBudget = 0.35;

  if (income.includes('under $30')) {        // lowest bracket
    volTarget = 0.09; cashFloor = 0.12; nameCap = 0.04; sectorCap = 0.25;
    perTradeMax = 0.02; posMin = 0.0075; preferETFs = true;
    excludeHighVol = 0.45; minMC = 5e9; turnoverBudget = 0.25;
  } else if (income.includes('$30,000 - $50,000')) {
    volTarget = 0.105; cashFloor = 0.10; nameCap = 0.05; sectorCap = 0.28;
    perTradeMax = 0.025; posMin = 0.006; preferETFs = true;
    excludeHighVol = 0.50; minMC = 3e9; turnoverBudget = 0.30;
  } else if (income.includes('$50,000 - $75,000')) {
    volTarget = 0.12; cashFloor = 0.08; nameCap = 0.06; sectorCap = 0.30;
  } else if (income.includes('$75,000 - $100,000')) {
    volTarget = 0.135; cashFloor = 0.06; nameCap = 0.08; sectorCap = 0.32;
  } else if (income.includes('$100,000 - $150,000')) {
    volTarget = 0.15; cashFloor = 0.05; nameCap = 0.10; sectorCap = 0.34;
  } else if (income.includes('over $150,000')) {
    volTarget = 0.17; cashFloor = 0.04; nameCap = 0.12; sectorCap = 0.36;
  }

  // Adjust by *risk tolerance*
  const bump = rt === 'Aggressive' ? 1.2 : rt === 'Conservative' ? 0.8 : 1.0;
  volTarget = volTarget * bump;

  // Adjust by *horizon*
  if (horizon.includes('1-3')) { volTarget *= 0.85; cashFloor += 0.02; }
  if (horizon.includes('10+')) { volTarget *= 1.1;  cashFloor -= 0.01; }

  // Goal-based sector tilts (soft caps via overrides)
  const overrides: Record<string, number> = {};
  if (goals.includes('Wealth Building')) overrides['Technology'] = Math.min(0.35, sectorCap + 0.05);
  if (goals.includes('Passive Income'))  overrides['Utilities'] = Math.min(0.25, sectorCap - 0.05);
  if (goals.includes('Emergency Fund'))  cashFloor = Math.max(cashFloor, 0.15);

  // Very small accounts: avoid tiny positions
  if ((totalValue ?? 0) < 3000) {
    preferETFs = true;
    nameCap = Math.min(nameCap, 0.10);
    posMin = Math.max(posMin, 0.02); // keep the number of lines small
  }

  return {
    volTarget,
    nameCap,
    sectorCap,
    turnoverBudget,
    cashFloorPct: Math.max(0, Math.min(0.25, cashFloor)),
    perTradeMaxPct: perTradeMax,
    positionMinPct: posMin,
    preferETFs,
    sectorOverrides: Object.keys(overrides).length ? overrides : undefined,
    excludeHighVol,
    minMarketCap: minMC,
  };
}

/* ------------------------------ OPTIMIZER INTEGRATION ----------------------- */

async function optimizeWeights(
  personalizedRecs: any[],
  policy: { volTarget?: number; nameCap: number; sectorCap: number; turnoverBudget?: number; sectorOverrides?: Record<string, number> },
  zBySymbol: Record<string, { sector?: string; lowVol?: number }>,
  prevWeights?: Record<string, number>,
) {
  // Build request payload (use your blended score)
  const tickers = personalizedRecs.map((r) => ({
    symbol: r.symbol,
    score: Number(r._personalizedScore ?? 0),
    sector: zBySymbol[r.symbol]?.sector || 'Other',
    vol: undefined, // optional: if you have per-name vol, pass it here
  }));

  const body = {
    tickers,
    policy,
    prevWeights: prevWeights || {},
  };

  const res = await fetch(`${process.env.EXPO_PUBLIC_API_URL || 'http://54.162.138.209:8000'}/optimize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Optimizer returned ${res.status}`);
  return res.json();
}

/* ------------------------------ ANALYSIS METHODOLOGY ----------------------- */

type MethodologyStep = {
  key: string;
  title: string;
  icon: string;          // Feather icon name
  color: string;         // main accent
  tint: string;          // soft background tint
  summary: string;
  weight: number;        // 0..1
  tags: string[];
};

const METHODOLOGY_STEPS: MethodologyStep[] = [
  {
    key: 'technical',
    title: 'Technical Signals',
    icon: 'bar-chart-2',
    color: '#6366F1',
    tint: '#EEF2FF',
    summary: 'Trend, momentum, and breadth to time entries/exits.',
    weight: 0.35,
    tags: ['MA Crossovers', 'RSI/MACD', 'Breakouts', 'Volume Thrust'],
  },
  {
    key: 'fundamental',
    title: 'Fundamental Quality',
    icon: 'trending-up',
    color: '#10B981',
    tint: '#ECFDF5',
    summary: 'Growth, margins, and valuation vs. sector peers.',
    weight: 0.30,
    tags: ['EPS Growth', 'FCF Margin', 'Debt/Equity', 'EV/EBITDA'],
  },
  {
    key: 'risk',
    title: 'Risk & Regime',
    icon: 'alert-triangle',
    color: '#F59E0B',
    tint: '#FFFBEB',
    summary: 'Volatility, drawdown, and macro/sector regime.',
    weight: 0.20,
    tags: ['Volatility', 'Max Drawdown', 'Beta', 'Correlation'],
  },
  {
    key: 'portfolio',
    title: 'Portfolio Fit & Optimization',
    icon: 'crosshair',
    color: '#EF4444',
    tint: '#FEF2F2',
    summary: 'Position sizing & constraints to improve diversification.',
    weight: 0.15,
    tags: ['Sizing', 'Sector Caps', 'Turnover Limit', 'Risk Parity'],
  },
];

const AnalysisMethodology = ({ ai }: { ai?: any }) => {
  const [open, setOpen] = useState<string | null>(null);

  // Optional: if backend provides weights, map them here and override
  // const dynamicWeights = ai?.methodologyWeights ?? null;

  return (
    <View style={styles.methodologySection}>
      <Text style={styles.sectionTitle}>Analysis Methodology</Text>

      {METHODOLOGY_STEPS.map(step => (
        <TouchableOpacity
          key={step.key}
          activeOpacity={0.9}
          onPress={() => setOpen(prev => (prev === step.key ? null : step.key))}
          style={[styles.methodologyCard, { borderLeftColor: step.color, backgroundColor: step.tint }]}
        >
          {/* Header */}
          <View style={styles.methodologyHeader}>
            <View style={styles.methodologyHeaderLeft}>
              <View style={[styles.methodologyIconWrap, { backgroundColor: step.color }]}>
                <Icon name={step.icon} size={14} color="#fff" />
              </View>
              <Text style={styles.methodologyTitle}>{step.title}</Text>
            </View>

            <View style={styles.weightBadge}>
              <Text style={styles.weightBadgeText}>{Math.round(step.weight * 100)}%</Text>
            </View>
          </View>

          {/* Weight bar */}
          <View style={styles.weightTrack}>
            <View style={[styles.weightFill, { width: `${Math.min(100, Math.max(0, step.weight * 100))}%`, backgroundColor: step.color }]} />
          </View>

          {/* Summary */}
          <Text style={styles.methodologySummary}>{step.summary}</Text>

          {/* Expandable body */}
          {open === step.key && (
            <View style={styles.methodologyBody}>
              <View style={styles.tagsRow}>
                {step.tags.map((t, i) => (
                  <View key={i} style={styles.pillTag}>
                    <Text style={styles.pillTagText}>{t}</Text>
                  </View>
                ))}
              </View>

              {/* Optional footnote per section */}
              {step.key === 'portfolio' && (
                <Text style={styles.methodologyFootnote}>
                  Uses conservative turnover and sector caps; never recommends leverage or short options in non-hedging contexts.
                </Text>
              )}
            </View>
          )}
        </TouchableOpacity>
      ))}

      {/* Data sources row */}
      <View style={styles.dataSourcesCard}>
        <Text style={styles.dataSourcesTitle}>Data Inputs</Text>
        <View style={styles.tagsRow}>
          {['Price', 'Volume', 'Fundamentals', 'Options Flow', 'News/Sentiment'].map((src, i) => (
            <View key={i} style={[styles.pillTag, { backgroundColor: COLORS.subtext }]}>
              <Text style={[styles.pillTagText, { color: COLORS.bg }]}>{src}</Text>
            </View>
          ))}
        </View>
        <Text style={styles.dataSourcesNote}>
          Signals are combined with a Bayesian/ensemble approach; outputs are sanity-checked against your risk profile and portfolio constraints.
        </Text>
      </View>
    </View>
  );
};

/* ------------------------------ MEMOIZED COMPONENTS ----------------------- */
const FactorBadge = ({ label }: { label: string }) => (
  <View style={{ paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, backgroundColor: COLORS.muted, marginRight: 6, marginTop: 6 }}>
    <Text style={{ fontSize: 11, color: COLORS.subtext }}>{label}</Text>
  </View>
);

const CashSafetyWarning = ({ policy, totalValue, paused }: { policy: Policy; totalValue?: number; paused?: boolean }) => {
  const cashFloor = policy.cashFloorPct;
  const currentCash = 0.05; // This would come from actual portfolio data
  const isLowCash = currentCash < cashFloor;
  
  if (!isLowCash && !paused) return null;
  
  return (
    <View style={[styles.cashWarning, paused && { backgroundColor: '#FEF2F2', borderLeftColor: '#EF4444' }]}>
      <Icon name="alert-triangle" size={16} color={paused ? "#EF4444" : "#F59E0B"} />
      <Text style={[styles.cashWarningText, paused && { color: '#991B1B' }]}>
        {paused 
          ? `Emergency Cash Required: ${(cashFloor * 100).toFixed(0)}% minimum (Equity purchases paused)`
          : `Cash Safety Buffer: Keep ${(cashFloor * 100).toFixed(0)}% cash minimum`
        }
      </Text>
    </View>
  );
};

const StockCard = React.memo(({ item, showPersonalized, optResult }: { item: any; showPersonalized: boolean; optResult?: {weights?: Record<string, number>; vol?: number} | null }) => {
  // Safety check for undefined item
  if (!item) {
    console.warn('StockCard: item is undefined');
    return null;
  }
  
  const f = item._factors as (FactorWeights & { sector?: string }) | undefined;

  // show top 2 positive z-scores as badges
  const topFactors = f ? Object.entries({ value:f.value, quality:f.quality, momentum:f.momentum, lowVol:f.lowVol, yield:f.yield })
    .sort((a,b)=> (b[1]||0) - (a[1]||0))
    .slice(0,2)
    .map(([k]) => k) : [];

  return (
  <View style={styles.stockCard}>
    <View style={styles.stockHeader}>
      <View style={styles.stockInfo}>
        <Text style={styles.stockSymbol}>{item.symbol}</Text>
        <Text style={styles.companyName}>{item.companyName}</Text>
      </View>
      <View style={styles.stockMetrics}>
        <Text style={styles.allocationText}>
          {item.allocation && Array.isArray(item.allocation) && item.allocation.length > 0 
            ? `${item.allocation[0].percentage}%` 
            : '—'}
        </Text>
        <Text style={styles.expectedReturn}>
                        {item.expectedReturn != null ? `${(Number(item.expectedReturn) * 100).toFixed(1)}%` : 'N/A'}
        </Text>
      </View>
    </View>
    
    {/* Additional data fields */}
    <View style={styles.stockDetails}>
      {item.currentPrice && <Text style={styles.stockDetailText}>Current: ${item.currentPrice.toFixed(2)}</Text>}
      {item.targetPrice &&  <Text style={styles.stockDetailText}>Target: ${item.targetPrice.toFixed(2)}</Text>}
      {item.confidence &&    <Text style={styles.stockDetailText}>Conf: {Math.round(item.confidence * 100)}%</Text>}
      {f?.sector &&         <Text style={styles.stockDetailText}>Sector: {f.sector}</Text>}
      {optResult?.weights?.[item.symbol] != null && (
        <Text style={[styles.stockDetailText, { color: COLORS.primary, fontWeight: '600' }]}>
          Suggested: {(optResult.weights[item.symbol]*100).toFixed(1)}%
        </Text>
      )}
    </View>

                  {/* quant factor badges */}
                  {topFactors.length > 0 && (
                    <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
                      {topFactors.map(t => <FactorBadge key={t} label={t.toUpperCase()} />)}
                    </View>
                  )}

                  {/* Factor exposures chips (coming from factorContrib) */}
                  {item.factorContrib && (
                    <View style={{flexDirection:'row', flexWrap:'wrap', gap:6, marginTop:6}}>
                      {Object.entries(item.factorContrib).map(([k,v]: any) => (
                        <View key={k} style={[styles.tag, {backgroundColor:'#6366F1'}]}>
                          <Text style={styles.tagText}>{`${k}: ${Number(v).toFixed(1)}σ`}</Text>
                        </View>
                      ))}
                    </View>
                  )}

                  {/* Transaction cost preview */}
                  {item.tcPreview != null && (
                    <Text style={[styles.stockDetailText, {marginTop:6}]}>
                      Est. TC: {(Number(item.tcPreview)*100).toFixed(2)}%
        </Text>
      )}

                  {/* Why this size */}
                  {item.whyThisSize && (
                    <Text style={[styles.reasoning, {marginTop:6, fontStyle:'italic'}]}>
                      {item.whyThisSize}
        </Text>
      )}
    
    {!!item.reasoning && <Text style={styles.reasoning}>{item.reasoning}</Text>}
    <View style={styles.stockTags}>
      {!!item.recommendation && (
        <View style={[styles.tag, { backgroundColor: COLORS.success }]}>
          <Text style={styles.tagText}>{item.recommendation}</Text>
        </View>
      )}
      <View style={[styles.tag, { backgroundColor: '#6366F1' }]}>
        <Text style={styles.tagText}>{showPersonalized ? 'Personalized' : 'Quantitative'}</Text>
      </View>
    </View>
    
    {/* Trading Buttons */}
    <View style={styles.tradingButtons}>
      <TradingButton
        symbol={item.symbol}
        currentPrice={item.currentPrice}
        side="buy"
        style={styles.tradingButton}
        onOrderPlaced={(order) => {
          console.log('Buy order placed:', order);
        }}
      />
      <TradingButton
        symbol={item.symbol}
        currentPrice={item.currentPrice}
        side="sell"
        style={styles.tradingButton}
        onOrderPlaced={(order) => {
          console.log('Sell order placed:', order);
        }}
      />
    </View>
  </View>
  );
});

type ListHeaderProps = {
  hasProfile: boolean;
  user?: {
    incomeProfile?: {
      incomeBracket?: string;
      age?: number;
      riskTolerance?: string;
    };
  };
  showProfileForm: boolean;
  setShowProfileForm: (v: boolean) => void;
  Form: React.ComponentType;
  recommendationsLoading: boolean;
  ai?: any;
  recommendationsError?: any;
  refetchRecommendations: (opts?: any) => Promise<any>;
  Recommendations: React.ComponentType;
  hideStockPicks?: boolean;
  isGeneratingRecommendations?: boolean;
  handleGenerateRecommendations?: () => void;
};

const ListHeader = React.memo((props: ListHeaderProps) => {
  const {
    hasProfile,
    user,
    showProfileForm,
    setShowProfileForm,
    Form,
    recommendationsLoading,
    ai,
    recommendationsError,
    refetchRecommendations,
    Recommendations,
    hideStockPicks = false,
    isGeneratingRecommendations = false,
    handleGenerateRecommendations = () => {}
  } = props;

  // dev-only debug
  if (__DEV__) console.log('hideStockPicks:', hideStockPicks);

  return (
    <View>
      {/* Profile status + CTA */}
      <View style={styles.profileStatus}>
        {hasProfile ? (
          <View style={styles.profileComplete}>
            <Icon name="check" size={24} color={COLORS.success} />
            <Text style={styles.profileCompleteText}>Profile Complete</Text>
            <Text style={styles.profileDetails}>
              {user?.incomeProfile?.incomeBracket} • {user?.incomeProfile?.age} yrs • {user?.incomeProfile?.riskTolerance}
            </Text>
          </View>
        ) : (
          <View style={styles.profileIncomplete}>
            <Icon name="alert-circle" size={24} color={COLORS.warning} />
            <Text style={styles.profileIncompleteText}>Complete Your Profile</Text>
            <Text style={styles.profileIncompleteSubtext}>
              Create your financial profile to get personalized AI recommendations.
            </Text>
            <TouchableOpacity style={styles.createProfileButton} onPress={() => setShowProfileForm(true)}>
              <Text style={styles.createProfileButtonText}>Create Profile</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      {showProfileForm && <Form />}

      {hasProfile ? (
        recommendationsLoading && !ai ? (
          <View style={[styles.recommendationsContainer, { alignItems: 'center' }]}>
            <ActivityIndicator size="small" color={COLORS.primary} />
            <Text style={[styles.loadingText, { marginTop: 8 }]}>Loading AI recommendations…</Text>
          </View>
        ) : recommendationsError ? (
          <View style={[styles.recommendationsContainer, { alignItems: 'center' }]}>
            <Icon name="alert-triangle" size={20} color={COLORS.danger} />
            <Text style={[styles.loadingText, { marginTop: 8 }]}>Couldn't load recommendations.</Text>
            <TouchableOpacity
              style={[styles.saveButton, { marginTop: 12 }]}
              onPress={() => refetchRecommendations({ fetchPolicy: 'network-only' })}
            >
              <Text style={styles.saveButtonText}>Retry</Text>
            </TouchableOpacity>
          </View>
        ) : !hideStockPicks ? (
          <Recommendations />
        ) : ai ? (
          <View style={styles.recommendationsContainer}>
            <View style={styles.recommendationHeader}>
              <Text style={styles.recommendationTitle}>Quantitative AI Portfolio Analysis</Text>
              <TouchableOpacity
                style={[styles.regenerateButton, isGeneratingRecommendations && { opacity: 0.7 }]}
                onPress={handleGenerateRecommendations}
                disabled={isGeneratingRecommendations}
              >
                <Icon name="refresh-cw" size={16} color={COLORS.primary} />
                <Text style={styles.regenerateButtonText}>
                  {isGeneratingRecommendations ? 'Regenerating...' : 'Regenerate'}
                </Text>
              </TouchableOpacity>
            </View>
            
            {/* Portfolio Analysis Sections */}
            {ai.portfolioAnalysis && (
              <>
                {/* Portfolio Summary */}
                <View style={styles.portfolioSummary}>
                  <View style={styles.summaryItem}>
                    <Text style={styles.summaryLabel}>Total Value</Text>
                    <Text style={styles.summaryValue}>
                      {ai.portfolioAnalysis.totalValue ? `$${ai.portfolioAnalysis.totalValue.toLocaleString()}` : 'N/A'}
                    </Text>
                  </View>
                  <View style={styles.summaryItem}>
                    <Text style={styles.summaryLabel}>Holdings</Text>
                    <Text style={styles.summaryValue}>{ai.portfolioAnalysis.numHoldings ?? 'N/A'}</Text>
                  </View>
                  <View style={styles.summaryItem}>
                    <Text style={styles.summaryLabel}>Risk Score</Text>
                    <Text style={styles.summaryValue}>{ai.portfolioAnalysis.riskScore ?? 'N/A'}</Text>
                  </View>
                </View>

                {/* Expected Impact */}
                <View style={styles.expectedImpactCard}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <Icon name="activity" size={18} color={COLORS.primary} />
                    <Text style={styles.sectionTitle}>Expected Impact</Text>
                  </View>
                  <Text style={styles.expectedLine}>
                    EV Return: <Text style={styles.boldText}>
                      {ai.portfolioAnalysis.expectedImpact?.evPct != null 
                        ? `${(ai.portfolioAnalysis.expectedImpact.evPct * 100).toFixed(1)}%` 
                        : 'N/A'}
                    </Text>
                  </Text>
                  {ai.portfolioAnalysis.totalValue ? (
                    <Text style={styles.expectedLine}>
                      EV Change: <Text style={styles.boldText}>
                        {ai.portfolioAnalysis.expectedImpact?.evAbs != null 
                          ? `$${ai.portfolioAnalysis.expectedImpact.evAbs.toLocaleString()}` 
                          : 'N/A'}
                      </Text> (this period)
                    </Text>
                  ) : (
                    <Text style={styles.expectedLine}>
                      EV per $10k: <Text style={styles.boldText}>
                        {ai.portfolioAnalysis.expectedImpact?.per10k != null 
                          ? `$${ai.portfolioAnalysis.expectedImpact.per10k.toLocaleString()}` 
                          : 'N/A'}
                      </Text>
                    </Text>
                  )}
                  <Text style={styles.expectedHint}>
                    Based on confidence-weighted expected returns from current buy recommendations.
                  </Text>
                </View>

                {/* Risk Analysis */}
                <View style={styles.riskMetricsSection}>
                  <Text style={styles.sectionTitle}>Risk Analysis</Text>
                  <View style={styles.riskMetricsGrid}>
                    <View style={styles.riskMetricItem}>
                      <Icon name="trending-up" size={20} color={COLORS.danger} />
                      <Text style={styles.riskMetricLabel}>Volatility</Text>
                      <Text style={styles.riskMetricValue}>
                        {ai.portfolioAnalysis.risk?.volatilityEstimate 
                          ? `${ai.portfolioAnalysis.risk.volatilityEstimate}%` 
                          : 'N/A'}
                      </Text>
                    </View>
                    <View style={styles.riskMetricItem}>
                      <Icon name="trending-down" size={20} color={COLORS.warning} />
                      <Text style={styles.riskMetricLabel}>Max Drawdown</Text>
                      <Text style={styles.riskMetricValue}>
                        {ai.portfolioAnalysis.risk?.maxDrawdownPct 
                          ? `${ai.portfolioAnalysis.risk.maxDrawdownPct}%` 
                          : 'N/A'}
                      </Text>
                    </View>
                  </View>
                </View>

                {/* Asset Allocation */}
                <View style={styles.allocationSection}>
                  <Text style={styles.sectionTitle}>Asset Allocation</Text>
                  <View style={styles.allocationGrid}>
                    <View style={styles.allocationItem}>
                      <View style={[styles.allocationBar, { backgroundColor: COLORS.primary }]} />
                      <Text style={styles.allocationLabel}>Stocks</Text>
                      <Text style={styles.allocationValue}>
                        {ai.portfolioAnalysis.assetAllocation?.stocks 
                          ? `${ai.portfolioAnalysis.assetAllocation.stocks}%` 
                          : 'N/A'}
                      </Text>
                    </View>
                    <View style={styles.allocationItem}>
                      <View style={[styles.allocationBar, { backgroundColor: COLORS.success }]} />
                      <Text style={styles.allocationLabel}>Bonds</Text>
                      <Text style={styles.allocationValue}>
                        {ai.portfolioAnalysis.assetAllocation?.bonds 
                          ? `${ai.portfolioAnalysis.assetAllocation.bonds}%` 
                          : 'N/A'}
                      </Text>
                    </View>
                    <View style={styles.allocationItem}>
                      <View style={[styles.allocationBar, { backgroundColor: COLORS.muted }]} />
                      <Text style={styles.allocationLabel}>Cash</Text>
                      <Text style={styles.allocationValue}>
                        {ai.portfolioAnalysis.assetAllocation?.cash 
                          ? `${ai.portfolioAnalysis.assetAllocation.cash}%` 
                          : 'N/A'}
                      </Text>
                    </View>
                  </View>
                </View>
              </>
            )}
          </View>
        ) : null
      ) : null}
    </View>
  );
});

ListHeader.displayName = 'ListHeader';

/* ------------------------------ COMPONENT --------------------------------- */
export default function AIPortfolioScreen({ navigateTo }: AIPortfolioScreenProps) {
  const safeNavigateTo = navigateTo || (() => {});

  // UI state
  const [showProfileForm, setShowProfileForm] = useState(false);
  const [isGeneratingRecommendations, setIsGeneratingRecommendations] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // form state
  const [incomeBracket, setIncomeBracket] = useState('');
  const [age, setAge] = useState('');
  const [selectedGoals, setSelectedGoals] = useState<string[]>([]);
  const [riskTolerance, setRiskTolerance] = useState<RT>('');
  const [investmentHorizon, setInvestmentHorizon] = useState('');

  // queries
  const {
    data: userData,
    loading: userLoading,
    error: userError,
    refetch: refetchUser,
  } = useQuery(GET_USER_PROFILE, {
    fetchPolicy: 'cache-first',
    nextFetchPolicy: 'cache-first',
    notifyOnNetworkStatusChange: true,
  });

  const user = userData?.me;
  // Check if profile exists AND has meaningful data (not just empty strings)
  const hasProfile = !!user?.incomeProfile && 
    user.incomeProfile.age && 
    user.incomeProfile.incomeBracket && 
    user.incomeProfile.investmentHorizon && 
    user.incomeProfile.riskTolerance && 
    user.incomeProfile.investmentGoals?.length > 0;
  
  // Debug logging for profile validation
  console.log('🔍 Profile Debug:', {
    hasIncomeProfile: !!user?.incomeProfile,
    age: user?.incomeProfile?.age,
    incomeBracket: user?.incomeProfile?.incomeBracket,
    investmentHorizon: user?.incomeProfile?.investmentHorizon,
    riskTolerance: user?.incomeProfile?.riskTolerance,
    investmentGoals: user?.incomeProfile?.investmentGoals,
    hasProfile: hasProfile
  });
  

  const {
    data: recommendationsData,
    loading: recommendationsLoading,
    error: recommendationsError,
    refetch: refetchRecommendations,
    networkStatus,
  } = useQuery(GET_AI_RECOMMENDATIONS, {
    fetchPolicy: 'network-only',          // ✅ Always fetch fresh data
    skip: !hasProfile,                    // ✅ don't fetch until profile exists
    notifyOnNetworkStatusChange: true,
  });

  // Quant screener for factor analysis
  const { data: screenerData } = useQuery(GET_QUANT_SCREENER, {
    fetchPolicy: 'cache-first',
    skip: false, // Don't skip - we need this data for personalized recommendations
  });

  // mutations
  const [createIncomeProfile, { loading: creatingProfile }] = useMutation(CREATE_INCOME_PROFILE);
  const [generateAIRecommendations] = useMutation(GENERATE_AI_RECOMMENDATIONS);
  const client = useApolloClient();

  const rt = (user?.incomeProfile?.riskTolerance as RT) || '';

  const ai = recommendationsData?.aiRecommendations;
  const totalValue = ai?.portfolioAnalysis?.totalValue as number | undefined;
  
  // Profile-based policy and factor tilts
  const profileLite: ProfileLite = useMemo(() => ({
    riskTolerance: rt,
    investmentHorizon: user?.incomeProfile?.investmentHorizon,
    investmentGoals: user?.incomeProfile?.investmentGoals as string[] | undefined,
  }), [rt, user?.incomeProfile?.investmentHorizon, user?.incomeProfile?.investmentGoals]);

  // Income-aware policy (replaces the simple profileToPolicy)
  const policy = useMemo(
    () => derivePolicyFromProfile(
      {
        incomeBracket: user?.incomeProfile?.incomeBracket,
        riskTolerance: user?.incomeProfile?.riskTolerance as RT,
        investmentHorizon: user?.incomeProfile?.investmentHorizon,
        investmentGoals: user?.incomeProfile?.investmentGoals || [],
      },
      ai?.portfolioAnalysis?.totalValue
    ),
    [user?.incomeProfile, ai?.portfolioAnalysis?.totalValue]
  );
  
  const factorTilts = useMemo(() => profileToFactorTilts(profileLite), [profileLite]);

  const zBySymbol = useMemo(() => {
    const rows = (screenerData?.advancedStockScreening ?? []) as ScreenerRow[];
    return toFactors(rows);
  }, [screenerData]);

  const personalizedRecs = useMemo(() => {
    // Apply suitability filters based on income-derived policy
    const universe = (ai?.buyRecommendations || [])
      .filter((s: any) => !policy.minMarketCap || (s.marketCap ?? 0) >= policy.minMarketCap)
      .filter((s: any) => !policy.excludeHighVol || (s.annVol ?? 0.0) <= policy.excludeHighVol);
    
    const base = universe.map((r: any) => {
      const z = zBySymbol[r.symbol];
      const score = blendScores(r, z, factorTilts, profileLite.investmentHorizon);
      return { ...r, _personalizedScore: score, _factors: z };
    });
    // stable sort by score desc
    const result = base.sort((a: any, b: any) => (b._personalizedScore ?? 0) - (a._personalizedScore ?? 0));
    
    
    return result;
  }, [ai?.buyRecommendations, zBySymbol, factorTilts, profileLite.investmentHorizon, policy]);

  // UI state for personalized vs raw AI toggle
  const [showPersonalized, setShowPersonalized] = useState(false); // Start with raw AI
  
  // Update to personalized when data is available
  useEffect(() => {
    if (personalizedRecs.length > 0 && !showPersonalized) {
      setShowPersonalized(true);
    }
  }, [personalizedRecs.length, showPersonalized]);
  
  // Optimization state
  const [optimizing, setOptimizing] = useState(false);
  const [optResult, setOptResult] = useState<{weights?: Record<string, number>; vol?: number} | null>(null);

  // Check if equity purchases are paused due to emergency cash requirements
  // This pattern ensures all trading-related UI is properly gated when policy requires emergency cash
  const paused = ai?.riskAssessment?.recommendations?.some((r: string) => /emergency cash/i.test(r));
  


  const riskAlloc = useMemo(() => allocationFromRisk[rt], [rt]);
  const { evPct, evAbs, per10k } = useMemo(() => computeExpectedImpact(ai, totalValue), [ai, totalValue]);

  /* ------------------------------- HANDLERS ------------------------------- */
  const handleGoalToggle = useCallback((goal: string) => {
    setSelectedGoals((prev) => (prev.includes(goal) ? prev.filter((g) => g !== goal) : [...prev, goal]));
  }, []);

  const handleCreateProfile = useCallback(async () => {
    if (!incomeBracket || !age || selectedGoals.length === 0 || !riskTolerance || !investmentHorizon) {
      Alert.alert('Missing Information', 'Please fill in all fields.');
      return;
    }
    const parsedAge = parseInt(age, 10);
    if (Number.isNaN(parsedAge) || parsedAge < 18 || parsedAge > 120) {
      Alert.alert('Invalid Age', 'Please enter a valid age between 18 and 120.');
      return;
    }

    try {
      const { data, errors } = await createIncomeProfile({
        variables: {
          incomeBracket,
          age: parsedAge,
          investmentGoals: selectedGoals,
          riskTolerance,
          investmentHorizon,
        },
      });

      if (errors && errors.length > 0) {
        console.error('GraphQL errors:', errors);
        Alert.alert('Error', `GraphQL Error: ${errors[0].message}`);
        return;
      }

      if (data?.createIncomeProfile?.success) {
        Alert.alert('Success', 'Income profile saved.');
        setShowProfileForm(false);
        await refetchUser();
        await handleGenerateRecommendations();
      } else {
        Alert.alert('Error', data?.createIncomeProfile?.message || 'Failed to create profile');
      }
    } catch (err) {
      console.error('ERROR: create profile', err);
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      Alert.alert('Error', `Failed to create profile: ${errorMessage}`);
    }
  }, [age, incomeBracket, investmentHorizon, riskTolerance, selectedGoals, createIncomeProfile, refetchUser]);


  const handleGenerateRecommendations = useCallback(async () => {
    console.log('🔥🔥🔥 NEW CODE RUNNING - Updated validation logic active!');
    console.log('🔄 REGENERATE BUTTON PRESSED - Starting AI Portfolio Recommendations Generation');
    console.log('📊 Current user profile (local state):', { age, incomeBracket, investmentHorizon, riskTolerance, selectedGoals });
    console.log('📊 Current user profile (GraphQL data):', {
      age: user?.incomeProfile?.age,
      incomeBracket: user?.incomeProfile?.incomeBracket,
      investmentHorizon: user?.incomeProfile?.investmentHorizon,
      riskTolerance: user?.incomeProfile?.riskTolerance,
      investmentGoals: user?.incomeProfile?.investmentGoals
    });
    console.log('🔍 hasProfile value:', hasProfile);
    
    // Check if profile is complete before proceeding
    if (!hasProfile) {
      console.log('❌ Profile incomplete - cannot generate recommendations');
      Alert.alert(
        'Profile Required', 
        'Please complete your financial profile first to generate AI recommendations.',
        [{ text: 'OK', onPress: () => setShowProfileForm(true) }]
      );
      return;
    }
    
    console.log('✅ Profile complete - proceeding with generation');
    
    setIsGeneratingRecommendations(true);
    try {
      console.log('🚀 Calling generateAIRecommendations GraphQL mutation...');
      const res = await generateAIRecommendations();
      
      console.log('📥 GraphQL Response received:', {
        success: res.data?.generateAiRecommendations?.success,
        message: res.data?.generateAiRecommendations?.message,
        hasData: !!res.data?.generateAiRecommendations?.recommendations,
        errors: res.errors
      });
      
      const ok = res.data?.generateAiRecommendations?.success;
      
      if (!ok) {
        const message = res.data?.generateAiRecommendations?.message || 'Failed to generate recommendations';
        console.log('❌ Generation failed:', message);
        Alert.alert('Error', message);
        return;
      }
      
      console.log('✅ Generation successful! Clearing cache and refreshing data...');
      
      // Clear Apollo Client cache for aiRecommendations
      client.cache.evict({ fieldName: 'aiRecommendations' });
      client.cache.gc();
      
      // Force refresh with cache bypass
      await refetchRecommendations({ 
        fetchPolicy: 'network-only',
        notifyOnNetworkStatusChange: true 
      });
      
      console.log('🔄 Data refresh completed');
    } catch (err) {
      console.error('💥 ERROR in handleGenerateRecommendations:', err);
      console.error('💥 Error details:', {
        message: err?.message,
        stack: err?.stack,
        name: err?.name
      });
      Alert.alert('Error', 'Failed to generate recommendations. Please try again.');
    } finally {
      console.log('🏁 Generation process completed, setting loading to false');
      setIsGeneratingRecommendations(false);
    }
  }, [generateAIRecommendations, refetchRecommendations, client, hasProfile, setShowProfileForm]);

  // Refresh data when component mounts or profile changes
  useEffect(() => {
    if (hasProfile) {
      refetchRecommendations({ fetchPolicy: 'network-only' });
    }
  }, [hasProfile, refetchRecommendations]);

  const onRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      // Clear Apollo Client cache for aiRecommendations
      client.cache.evict({ fieldName: 'aiRecommendations' });
      client.cache.gc();
      
      await Promise.all([
        refetchUser({ fetchPolicy: 'network-only' }),
        refetchRecommendations({ fetchPolicy: 'network-only' }),
      ]);
    } finally {
      setIsRefreshing(false);
    }
  }, [refetchUser, refetchRecommendations, client]);

  useEffect(() => {
    if (!showProfileForm && user?.incomeProfile) {
      const t = setTimeout(() => {
        refetchRecommendations({ fetchPolicy: 'network-only' });
      }, 300);
      return () => clearTimeout(t);
    }
  }, [showProfileForm, user?.incomeProfile, refetchRecommendations]);

  /* ----------------------------- RENDER PIECES ---------------------------- */
  const Form = () => (
    <View style={styles.formContainer}>
      <Text style={styles.formTitle}>Create Your Financial Profile</Text>

      {/* Income */}
      <View style={styles.formGroup}>
        <Text style={styles.label}>Annual Income</Text>
        <View style={styles.optionsGrid}>
          {['Under $30,000','$30,000 - $50,000','$50,000 - $75,000','$75,000 - $100,000','$100,000 - $150,000','Over $150,000']
            .map((bracket) => (
            <TouchableOpacity
              key={bracket}
              style={[styles.optionButton, incomeBracket === bracket && styles.selectedOption]}
              onPress={() => setIncomeBracket(bracket)}
              activeOpacity={0.9}
            >
              <Text style={[styles.optionText, incomeBracket === bracket && styles.selectedOptionText]}>{bracket}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Age */}
      <View style={styles.formGroup}>
        <Text style={styles.label}>Age</Text>
        <StableNumberInput
          value={age}
          onSubmitValue={(n) => {
            // Validate when user submits or blurs
            if (n === null || n < 18) {
              setAge('18');
            } else {
              setAge(String(n));
            }
          }}
          style={styles.input}
          placeholder="Enter your age (minimum 18)"
          maxLength={3}
        />
      </View>

      {/* Goals */}
      <View style={styles.formGroup}>
        <Text style={styles.label}>Investment Goals (Select all that apply)</Text>
        <View style={styles.optionsGrid}>
          {['Retirement Savings','Buy a Home','Emergency Fund','Wealth Building','Passive Income','Tax Benefits','College Fund','Travel Fund'].map((goal) => {
            const selected = selectedGoals.includes(goal);
            return (
              <TouchableOpacity
                key={goal}
                style={[styles.optionButton, selected && styles.selectedOption]}
                onPress={() => handleGoalToggle(goal)}
                activeOpacity={0.9}
              >
                <Text style={[styles.optionText, selected && styles.selectedOptionText]}>{goal}</Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Risk */}
      <View style={styles.formGroup}>
        <Text style={styles.label}>Risk Tolerance</Text>
        <View style={styles.optionsGrid}>
          {(['Conservative','Moderate','Aggressive'] as RT[]).map((r) => (
            <TouchableOpacity
              key={r}
              style={[styles.optionButton, riskTolerance === r && styles.selectedOption]}
              onPress={() => setRiskTolerance(r)}
              activeOpacity={0.9}
            >
              <Text style={[styles.optionText, riskTolerance === r && styles.selectedOptionText]}>{r}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Horizon */}
      <View style={styles.formGroup}>
        <Text style={styles.label}>Investment Time Horizon</Text>
        <View style={styles.optionsGrid}>
          {['1-3 years','3-5 years','5-10 years','10+ years'].map((opt) => (
            <TouchableOpacity
              key={opt}
              style={[styles.optionButton, investmentHorizon === opt && styles.selectedOption]}
              onPress={() => setInvestmentHorizon(opt)}
              activeOpacity={0.9}
            >
              <Text style={[styles.optionText, investmentHorizon === opt && styles.selectedOptionText]}>{opt}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Actions */}
      <View style={styles.formActions}>
        <TouchableOpacity
          style={styles.cancelButton}
          onPress={() => setShowProfileForm(false)}
          disabled={creatingProfile}
        >
          <Text style={styles.cancelButtonText}>Cancel</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.saveButton, creatingProfile && { opacity: 0.7 }]}
          onPress={handleCreateProfile}
          disabled={creatingProfile}
        >
          <Text style={styles.saveButtonText}>{creatingProfile ? 'Saving…' : 'Save Profile'}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const EmptyRecs = () => (
    <View style={styles.emptyState}>
      <Icon name="cpu" size={64} color="#9CA3AF" />
      <Text style={styles.emptyTitle}>No AI Recommendations Yet</Text>
      <Text style={styles.emptySubtitle}>
        Generate personalized quantitative AI portfolio recommendations based on your financial profile.
      </Text>
      <TouchableOpacity
        style={styles.generateButton}
        onPress={handleGenerateRecommendations}
        disabled={isGeneratingRecommendations}
      >
        <Text style={styles.generateButtonText}>
          {isGeneratingRecommendations ? 'Generating…' : 'Generate Quantitative AI Recommendations'}
        </Text>
      </TouchableOpacity>
    </View>
  );

  const SummaryCards = () => (
    <>
      {/* Portfolio Summary */}
      <View style={styles.portfolioSummary}>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryLabel}>Total Value</Text>
          <Text style={styles.summaryValue}>
            {totalValue != null ? fmtMoney(totalValue) : 'N/A'}
          </Text>
        </View>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryLabel}>Holdings</Text>
          <Text style={styles.summaryValue}>{ai?.portfolioAnalysis?.numHoldings ?? 'N/A'}</Text>
        </View>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryLabel}>Risk Score</Text>
          <Text style={styles.summaryValue}>{ai?.portfolioAnalysis?.riskScore ?? 'N/A'}</Text>
        </View>
      </View>

      {/* Expected Impact (from new recommendations) */}
      <View style={styles.expectedImpactCard}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <Icon name="activity" size={18} color={COLORS.primary} />
          <Text style={styles.sectionTitle}>Expected Impact (from new data)</Text>
        </View>
        <Text style={styles.expectedLine}>
          EV Return: <Text style={styles.boldText}>{evPct != null ? fmtPct(evPct * 100) : 'N/A'}</Text>
        </Text>
        {totalValue != null ? (
          <Text style={styles.expectedLine}>
            EV Change: <Text style={styles.boldText}>{evAbs != null ? fmtMoney(evAbs) : 'N/A'}</Text> (this period)
          </Text>
        ) : (
          <Text style={styles.expectedLine}>
            EV per $10k: <Text style={styles.boldText}>{per10k != null ? fmtMoney(per10k) : 'N/A'}</Text>
          </Text>
        )}
        <Text style={styles.expectedHint}>
          Based on confidence-weighted expected returns from current buy recommendations.
        </Text>
      </View>

      {/* Risk metrics */}
      <View style={styles.riskMetricsSection}>
        <Text style={styles.sectionTitle}>Risk Analysis</Text>
        <View style={styles.riskMetricsGrid}>
          <View style={styles.riskMetricItem}>
            <Icon name="trending-up" size={20} color={COLORS.danger} />
            <Text style={styles.riskMetricLabel}>Volatility</Text>
            <Text style={styles.riskMetricValue}>{getVolatility(ai, rt)}</Text>
            <TouchableOpacity
              style={styles.infoButtonBottomRight}
              onPress={() =>
                Alert.alert(
                  'Volatility',
                  'How much your portfolio fluctuates. We prefer backend risk metrics; otherwise we show a profile-based estimate.'
                )
              }
            >
              <Icon name="info" size={14} color={COLORS.subtext} />
            </TouchableOpacity>
          </View>

          <View style={styles.riskMetricItem}>
            <Icon name="alert-circle" size={20} color={COLORS.warning} />
            <Text style={styles.riskMetricLabel}>Max Drawdown</Text>
            <Text style={styles.riskMetricValue}>{getMaxDrawdown(rt)}</Text>
            <TouchableOpacity
              style={styles.infoButtonBottomRight}
              onPress={() =>
                Alert.alert(
                  'Max Drawdown',
                  'Worst peak-to-trough decline. Using profile-based estimate until backend provides this metric.'
                )
              }
            >
              <Icon name="info" size={14} color={COLORS.subtext} />
            </TouchableOpacity>
          </View>

          <View style={styles.riskMetricItem}>
            <Icon name="lock" size={20} color={COLORS.success} />
            <Text style={styles.riskMetricLabel}>Risk Level</Text>
            <Text style={styles.riskMetricValue}>{rt || 'N/A'}</Text>
            <TouchableOpacity
              style={styles.infoButtonBottomRight}
              onPress={() =>
                Alert.alert(
                  'Risk Level',
                  'Your tolerance drives the stock/bond mix. Conservative = stability; Aggressive = higher upside and risk.'
                )
              }
            >
              <Icon name="info" size={14} color={COLORS.subtext} />
            </TouchableOpacity>
          </View>
        </View>
      </View>

      {/* Allocation */}
      <View style={styles.allocationSection}>
        <Text style={styles.sectionTitle}>Asset Allocation</Text>
        <View style={styles.allocationGrid}>
          {(['stocks', 'bonds', 'etfs', 'cash'] as const).map((k) => (
            <View key={k} style={styles.allocationItem}>
              <Text style={styles.allocationLabel}>{k[0].toUpperCase() + k.slice(1)}</Text>
              <Text style={styles.allocationValue}>{riskAlloc[k]}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* Sector breakdown */}
      <View style={styles.sectorSection}>
        <Text style={styles.sectionTitle}>Portfolio Allocation</Text>
        <View style={styles.sectorGrid}>
          {(['Technology', 'Healthcare', 'Financials'] as const).map((sector) => (
            <View key={sector} style={styles.sectorItem}>
              <Text style={styles.sectorLabel}>{sector}</Text>
              <Text style={styles.sectorValue}>
                {ai?.portfolioAnalysis?.sectorBreakdown?.[sector] ?? 0}%
              </Text>
            </View>
          ))}
        </View>
      </View>
    </>
  );

  const Recommendations = () => {
    if (!ai) return <EmptyRecs />;

    return (
      <View style={styles.recommendationsContainer}>
        <View style={styles.recommendationHeader}>
          <Text style={styles.recommendationTitle}>Quantitative AI Portfolio Analysis</Text>
          <TouchableOpacity
            style={[styles.regenerateButton, isGeneratingRecommendations && { opacity: 0.7 }]}
            onPress={handleGenerateRecommendations}
            disabled={isGeneratingRecommendations}
          >
            <Icon name="refresh-cw" size={16} color={COLORS.primary} />
            <Text style={styles.regenerateButtonText}>
              {isGeneratingRecommendations ? 'Regenerating...' : 'Regenerate'}
            </Text>
          </TouchableOpacity>
        </View>

        <SummaryCards />

        {/* Stock Picks - only show if not hidden */}
        <View style={styles.stocksSection}>
          <View style={styles.recommendationHeader}>
            <Text style={styles.sectionTitle}>Quantitative AI Portfolio Analysis</Text>
            <View style={styles.buttonRow}>
              <TouchableOpacity
                style={[styles.regenerateButton, (isGeneratingRecommendations || paused) && { opacity: 0.7 }]}
                onPress={handleGenerateRecommendations}
                disabled={isGeneratingRecommendations || paused}
              >
                <Icon name="refresh-cw" size={16} color={COLORS.primary} />
                <Text style={styles.regenerateButtonText}>
                  {isGeneratingRecommendations ? 'Regenerating...' : paused ? 'Paused (Build Emergency Cash)' : 'Regenerate'}
                </Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.regenerateButton, (optimizing || paused) && { opacity: 0.7 }]}
                onPress={async () => {
                  try {
                    setOptimizing(true);
                    const result = await optimizeWeights(personalizedRecs, {
                      volTarget: policy.volTarget,        // from profile
                      nameCap: policy.nameCap,            // e.g. 0.06
                      sectorCap: policy.sectorCap,        // e.g. 0.30
                      turnoverBudget: policy.turnoverBudget, // optional
                    }, zBySymbol);
                    const wmap = Object.fromEntries(result.weights.map((w:any)=>[w.symbol, w.weight]));
                    setOptResult({weights: wmap, vol: result.portfolioVol});
                  } catch (e) {
                    Alert.alert("Optimization failed", `${e}`);
                  } finally {
                    setOptimizing(false);
                  }
                }}
                disabled={optimizing || paused}
              >
                <Icon name="sliders" size={16} color={COLORS.primary} />
                <Text style={styles.regenerateButtonText}>
                  {optimizing ? "Optimizing..." : paused ? "Paused (Build Emergency Cash)" : "Optimize Weights"}
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Cash safety warning */}
          <CashSafetyWarning policy={policy} totalValue={totalValue} paused={paused} />

          {/* Policy banner for emergency cash */}
          {ai?.riskAssessment?.recommendations?.some((r: string) =>
            r.toLowerCase().includes('emergency cash')
          ) && (
            <View style={{backgroundColor: '#FEF3C7', borderColor:'#F59E0B', borderWidth:1, padding:12, borderRadius:8, marginBottom:12}}>
              <Text style={{color:'#92400E', fontWeight:'700'}}>Action needed</Text>
              <Text style={{color:'#78350F', marginTop:4}}>
                Build your emergency cash first. Equity buy suggestions are paused by your policy.
              </Text>
            </View>
          )}

          {/* model toggle */}
          <View style={{ flexDirection: 'row', justifyContent: 'center', marginBottom: 12, gap: 8 }}>
            <TouchableOpacity
              onPress={() => setShowPersonalized(true)}
              style={[styles.pillToggle, showPersonalized && styles.pillActive, paused && { opacity: 0.5 }]}
              disabled={paused}
            >
              <Text style={[styles.pillText, showPersonalized && styles.pillTextActive]}>Personalized</Text>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => setShowPersonalized(false)}
              style={[styles.pillToggle, !showPersonalized && styles.pillActive, paused && { opacity: 0.5 }]}
              disabled={paused}
            >
              <Text style={[styles.pillText, !showPersonalized && styles.pillTextActive]}>Raw AI</Text>
            </TouchableOpacity>
          </View>

          <FlatList
            data={(showPersonalized ? personalizedRecs : ai.buyRecommendations) || []}
            keyExtractor={(it: any, idx: number) => {
              const symbol = it?.symbol || `unknown-${idx}`;
              return `${symbol}-${idx}`;
            }}
            renderItem={({ item }) => <StockCard item={item} showPersonalized={showPersonalized} optResult={optResult} />}
            scrollEnabled={false}
            ListEmptyComponent={
              <View style={{ padding: 20, alignItems: 'center' }}>
                {paused ? (
                  <>
                    <Icon name="alert-triangle" size={48} color="#F59E0B" style={{ marginBottom: 12 }} />
                    <Text style={{ color: '#92400E', fontSize: 16, fontWeight: '600', textAlign: 'center', marginBottom: 8 }}>
                      Equity Purchases Paused
                    </Text>
                    <Text style={{ color: COLORS.subtext, textAlign: 'center', lineHeight: 20 }}>
                      Build your emergency cash buffer first. Once you have sufficient cash reserves, 
                      equity recommendations will be available.
                    </Text>
                  </>
                ) : (
              <Text style={{ color: COLORS.subtext, textAlign: 'center' }}>No buy recommendations yet.</Text>
                )}
              </View>
            }
          />
          
          {/* Portfolio volatility display */}
          {optResult?.vol != null && (
            <Text style={{ color: COLORS.subtext, textAlign: 'center', marginTop: 6 }}>
              Optimized portfolio vol: {(optResult.vol*100).toFixed(1)}% (target {Math.round((policy.volTarget || 0.12)*100)}%)
            </Text>
          )}
        </View>

        {/* Methodology - always show at the bottom */}
        <View style={styles.methodologySection}>
          <Text style={styles.sectionTitle}>Methodology (Income-Aware Quant)</Text>

            <View style={styles.methodologyItem}>
            <Text style={styles.methodologyLabel}>Income → Risk Capacity</Text>
            <Text style={{ color: COLORS.text, marginTop: 4 }}>
              Your income shapes safety rails: cash buffer {(policy.cashFloorPct*100).toFixed(0)}%, 
              max position {(policy.nameCap*100).toFixed(0)}%, sector cap {(policy.sectorCap*100).toFixed(0)}%, 
              vol target {Math.round((policy.volTarget || 0.12)*100)}%. We never use income to predict returns.
            </Text>
            </View>

            <View style={styles.methodologyItem}>
            <Text style={styles.methodologyLabel}>Factor Tilts</Text>
            <Text style={{ color: COLORS.text, marginTop: 4 }}>
              Your goals adjust factor weights: Value/Quality/Momentum/Low-Vol/Yield → 
              {` ${Object.entries(factorTilts).map(([k,v])=>`${k}:${Math.round(v*100)}%`).join('  ')}`}
            </Text>
            </View>

            <View style={styles.methodologyItem}>
            <Text style={styles.methodologyLabel}>Signals & Ranking</Text>
            <Text style={{ color: COLORS.text, marginTop: 4 }}>
              We z-score factor proxies by sector (to avoid naive sector bets) and blend them with the AI signal
              (expected return × confidence). Shorter horizons weight the AI more; longer horizons weight factors more.
            </Text>
            </View>

            <View style={styles.methodologyItem}>
            <Text style={styles.methodologyLabel}>Convex Optimization</Text>
            <Text style={{ color: COLORS.text, marginTop: 4 }}>
              We solve maximize(score - λ·variance) subject to your income-derived constraints: 
              position limits, sector caps, volatility targeting, and turnover budgeting.
            </Text>
          </View>
        </View>
      </View>
    );
  };

  /* --------------------------- TOP-LEVEL RENDER --------------------------- */
  if (userLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={COLORS.primary} />
          <Text style={styles.loadingText}>Loading your profile…</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (userError) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Icon name="alert-triangle" size={24} color={COLORS.danger} />
          <Text style={styles.loadingText}>Couldn’t load your profile.</Text>
          <TouchableOpacity style={[styles.saveButton, { marginTop: 12 }]} onPress={() => refetchUser()}>
            <Text style={styles.saveButtonText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerTitleContainer}>
          <Icon name="trending-up" size={24} color={COLORS.primary} style={styles.headerIcon} />
          <Text style={styles.headerTitle}>AI Portfolio Advisor</Text>
        </View>

        <TouchableOpacity
          style={[styles.profileButton, showProfileForm && styles.profileButtonActive]}
          onPress={() => setShowProfileForm((s) => !s)}
          activeOpacity={0.7}
        >
          <View style={styles.profileButtonContent}>
            <Icon name={showProfileForm ? 'x' : 'user'} size={20} color={showProfileForm ? COLORS.danger : COLORS.primary} />
            <Text style={[styles.profileButtonText, showProfileForm && styles.profileButtonTextActive]}>
              {showProfileForm ? 'Close Form' : 'Edit Profile'}
            </Text>
          </View>
          {!showProfileForm && (
            <View style={styles.profileButtonHint}>
              <Icon name="chevron-down" size={12} color={COLORS.primary} />
              <Text style={styles.profileButtonHintText} numberOfLines={2}>
                Tap to edit your financial profile
              </Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        {showProfileForm || (!hasProfile && !ai?.buyRecommendations?.length) ? (
          // Use ScrollView when form is open, no profile, or no recommendations to ensure proper scrolling
          <ScrollView
            style={styles.content}
            contentContainerStyle={{ flexGrow: 1 }}
            refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={onRefresh} />}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={true}
          >
            <ListHeader 
              hasProfile={hasProfile}
              user={user}
              showProfileForm={showProfileForm}
              setShowProfileForm={setShowProfileForm}
              Form={Form}
              recommendationsLoading={recommendationsLoading}
              ai={ai}
              recommendationsError={recommendationsError}
              refetchRecommendations={refetchRecommendations}
              Recommendations={Recommendations}
              isGeneratingRecommendations={isGeneratingRecommendations}
              handleGenerateRecommendations={handleGenerateRecommendations}
            />
          </ScrollView>
        ) : (
          // Use FlatList only when we have actual stock recommendations to display
          <FlatList
            key={`flatlist-${ai?.buyRecommendations?.length || 0}-${Date.now()}`}
            style={{ flex: 1 }}
            data={(showPersonalized ? personalizedRecs : ai?.buyRecommendations) || []}
            keyExtractor={(it: any, idx: number) => {
              const symbol = it?.symbol || `unknown-${idx}`;
              return `${symbol}-${idx}`;
            }}
            renderItem={({ item }: { item: any; index: number }) => (
              <StockCard item={item} showPersonalized={showPersonalized} optResult={optResult} />
            )}
            ListHeaderComponent={
              <ListHeader 
                hasProfile={hasProfile}
                user={user}
                showProfileForm={showProfileForm}
                setShowProfileForm={setShowProfileForm}
                Form={Form}
                recommendationsLoading={recommendationsLoading}
                ai={ai}
                recommendationsError={recommendationsError}
                refetchRecommendations={refetchRecommendations}
                Recommendations={Recommendations}
                hideStockPicks={true} // Hide stock picks in header since they're rendered as FlatList items
                isGeneratingRecommendations={isGeneratingRecommendations}
                handleGenerateRecommendations={handleGenerateRecommendations}
              />
            }
            ListFooterComponent={
              // Add Analysis Methodology as footer to ensure it's always last
              <AnalysisMethodology ai={ai} />
            }
            ListEmptyComponent={
              hasProfile
                ? (!recommendationsLoading ? <Text style={{ color: COLORS.subtext, textAlign: 'center' }}>No buy recommendations yet.</Text> : null)
                : null
            }
            refreshing={isRefreshing || networkStatus === 4}
            onRefresh={onRefresh}
            contentContainerStyle={styles.content}
            keyboardShouldPersistTaps="handled"
            // perf tuning
            initialNumToRender={8}
            maxToRenderPerBatch={10}
            updateCellsBatchingPeriod={50}
            windowSize={5}
            removeClippedSubviews
          />
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

/* -------------------------------- STYLES ---------------------------------- */
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg },

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING,
    paddingVertical: 15,
    backgroundColor: COLORS.card,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    gap: 8,
  },
  headerTitleContainer: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    flex: 1, 
    marginRight: 8,
    minWidth: 0, // Allow text to shrink
  },
  headerIcon: { marginRight: 8 },
  headerTitle: { 
    fontSize: 24, 
    fontWeight: 'bold', 
    color: COLORS.text,
    flex: 1,
    flexWrap: 'wrap',
  },

  profileButton: {
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 20,
    backgroundColor: COLORS.muted,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    minWidth: 100,
    maxWidth: 120,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
    flexShrink: 0, // Prevent button from shrinking
  },
  profileButtonActive: { backgroundColor: '#FEF2F2', borderColor: COLORS.danger, transform: [{ scale: 1.05 }] },
  profileButtonContent: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, width: '100%', marginBottom: 2 },
  profileButtonText: { 
    fontSize: 11, 
    fontWeight: '600', 
    color: COLORS.primary, 
    textAlign: 'center',
    flexShrink: 1,
  },
  profileButtonTextActive: { 
    color: COLORS.danger,
    fontSize: 10, // Smaller text when form is open
  },
  profileButtonHint: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 3, marginTop: 3, width: '100%' },
  profileButtonHintText: { fontSize: 9, color: COLORS.subtext, fontStyle: 'italic', textAlign: 'center', flexShrink: 1 },

  content: { padding: SPACING },

  /* Profile status */
  profileStatus: { backgroundColor: COLORS.card, borderRadius: 12, padding: SPACING, marginBottom: SPACING },
  profileComplete: { alignItems: 'center' },
  profileCompleteText: { fontSize: 18, fontWeight: 'bold', color: COLORS.success, marginTop: 8, marginBottom: 4 },
  profileDetails: { fontSize: 14, color: COLORS.subtext, textAlign: 'center' },
  profileIncomplete: { alignItems: 'center' },
  profileIncompleteText: { fontSize: 18, fontWeight: 'bold', color: COLORS.warning, marginTop: 8, marginBottom: 4 },
  profileIncompleteSubtext: { fontSize: 14, color: COLORS.subtext, textAlign: 'center', marginBottom: 16 },
  createProfileButton: { backgroundColor: COLORS.primary, paddingHorizontal: 24, paddingVertical: 12, borderRadius: 8 },
  createProfileButtonText: { color: '#fff', fontSize: 16, fontWeight: '600' },

  /* Form */
  formContainer: { backgroundColor: COLORS.card, borderRadius: 12, padding: SPACING, marginBottom: SPACING },
  formTitle: { fontSize: 20, fontWeight: 'bold', color: COLORS.text, marginBottom: 20, textAlign: 'center' },
  formGroup: { marginBottom: 20 },
  label: { fontSize: 16, fontWeight: '600', color: '#374151', marginBottom: 8 },
  input: { borderWidth: 1, borderColor: '#D1D5DB', borderRadius: 8, padding: 12, fontSize: 16, backgroundColor: '#fff' },
  optionsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  optionButton: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, backgroundColor: COLORS.muted, borderWidth: 1, borderColor: '#E5E7EB' },
  optionText: { fontSize: 14, color: '#374151' },
  selectedOption: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  selectedOptionText: { color: '#fff', fontWeight: '600' },
  formActions: { flexDirection: 'row', gap: 12, marginTop: 20 },
  cancelButton: { flex: 1, paddingVertical: 12, paddingHorizontal: 20, borderRadius: 8, backgroundColor: COLORS.muted, alignItems: 'center' },
  cancelButtonText: { color: '#374151', fontSize: 16, fontWeight: '600' },
  saveButton: { flex: 1, paddingVertical: 12, paddingHorizontal: 20, borderRadius: 8, backgroundColor: COLORS.primary, alignItems: 'center' },
  saveButtonText: { color: '#fff', fontSize: 16, fontWeight: '600' },

  /* Empty */
  emptyState: { alignItems: 'center', padding: 40, backgroundColor: COLORS.card, borderRadius: 12 },
  emptyTitle: { fontSize: 20, fontWeight: 'bold', color: COLORS.text, marginTop: 16, marginBottom: 8 },
  emptySubtitle: { fontSize: 16, color: COLORS.subtext, textAlign: 'center', marginBottom: 24, lineHeight: 24 },
  generateButton: { backgroundColor: COLORS.primary, paddingHorizontal: 32, paddingVertical: 16, borderRadius: 8 },
  generateButtonText: { color: '#fff', fontSize: 16, fontWeight: '600' },

  /* Recs container */
  recommendationsContainer: { backgroundColor: COLORS.card, borderRadius: 12, padding: SPACING },
  recommendationHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, gap: 12, paddingLeft: 0 },
  recommendationTitle: { fontSize: 20, fontWeight: 'bold', color: COLORS.text, flex: 1, marginRight: 12 },
  regenerateButton: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    gap: 6, 
    paddingHorizontal: 12, 
    paddingVertical: 8, 
    backgroundColor: COLORS.muted, 
    borderRadius: 20, 
    borderWidth: 1, 
    borderColor: COLORS.primary 
  },
  regenerateButtonText: { fontSize: 12, fontWeight: '600', color: COLORS.primary },

  portfolioSummary: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  summaryItem: { alignItems: 'center', flex: 1 },
  summaryLabel: { fontSize: 12, color: COLORS.subtext, marginBottom: 4 },
  summaryValue: { fontSize: 18, fontWeight: 'bold', color: COLORS.primary },

  expectedImpactCard: { backgroundColor: COLORS.pill, borderRadius: 8, padding: 14, marginBottom: 12 },
  expectedLine: { color: COLORS.text, marginBottom: 4 },
  boldText: { fontWeight: '700', color: COLORS.text },
  expectedHint: { color: COLORS.subtext, fontSize: 12, marginTop: 2 },

  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: COLORS.text, marginVertical: 8 },

  allocationSection: { marginBottom: 24, marginTop: 4 },
  allocationGrid: { flexDirection: 'row', justifyContent: 'space-between', gap: 10 },
  allocationItem: { flex: 1, alignItems: 'center', padding: 16, backgroundColor: COLORS.pill, borderRadius: 8 },
  allocationBar: { width: 20, height: 4, borderRadius: 2, marginBottom: 8 },
  allocationLabel: { fontSize: 12, color: COLORS.subtext, marginBottom: 4 },
  allocationValue: { fontSize: 18, fontWeight: 'bold', color: COLORS.primary },

  stocksSection: { marginBottom: 20 },
  stockCard: { backgroundColor: COLORS.pill, borderRadius: 8, padding: 16, marginBottom: 12 },
  stockHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 },
  stockInfo: { flex: 1 },
  stockSymbol: { fontSize: 18, fontWeight: 'bold', color: COLORS.primary },
  companyName: { fontSize: 14, color: COLORS.subtext, marginTop: 2 },
  stockMetrics: { alignItems: 'flex-end' },
  allocationText: { fontSize: 16, fontWeight: 'bold', color: COLORS.text },
  expectedReturn: { fontSize: 12, color: COLORS.subtext, marginTop: 2 },
  stockDetails: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginTop: 8, marginBottom: 8 },
  stockDetailText: { fontSize: 12, color: COLORS.subtext, backgroundColor: COLORS.muted, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6 },
  reasoning: { fontSize: 14, color: '#374151', lineHeight: 20, marginBottom: 12 },
  stockTags: { flexDirection: 'row', gap: 8 },
  tag: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12 },
  tagText: { fontSize: 12, color: '#fff', fontWeight: '600' },
  
  tradingButtons: { 
    flexDirection: 'row', 
    gap: 8, 
    marginTop: 12,
    justifyContent: 'space-between'
  },
  tradingButton: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
  },

  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: COLORS.bg },
  loadingText: { fontSize: 16, color: COLORS.subtext, marginTop: 8 },

  riskMetricsSection: { marginBottom: 24 },
  riskMetricsGrid: { flexDirection: 'row', justifyContent: 'space-around', gap: 10 },
  riskMetricItem: {
    alignItems: 'center',
    padding: 16,
    paddingBottom: 24,
    backgroundColor: COLORS.pill,
    borderRadius: 8,
    flex: 1,
    position: 'relative',
  },
  riskMetricLabel: { fontSize: 12, color: COLORS.subtext, marginTop: 8 },
  riskMetricValue: { fontSize: 18, fontWeight: 'bold', color: COLORS.primary, marginTop: 4, marginBottom: 8 },
  infoButtonBottomRight: {
    position: 'absolute',
    bottom: 6,
    right: 6,
    padding: 3,
    borderRadius: 10,
    backgroundColor: COLORS.muted,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    zIndex: 1,
  },

  sectorSection: { marginBottom: 24 },
  sectorGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-around', gap: 10 },
  sectorItem: { alignItems: 'center', padding: 16, backgroundColor: COLORS.pill, borderRadius: 8, flex: 1 },
  sectorLabel: { fontSize: 12, color: COLORS.subtext, marginBottom: 4 },
  sectorValue: { fontSize: 18, fontWeight: 'bold', color: COLORS.primary },

  methodologySection: { marginTop: 24 },
  methodologyItem: { marginBottom: 16, padding: 12, backgroundColor: COLORS.card, borderRadius: 8, borderWidth: 1, borderColor: COLORS.border },
  methodologyLabel: { fontSize: 14, fontWeight: '700', color: COLORS.text, marginBottom: 4 },
  
  // New methodology styles
  methodologyCard: {
    borderLeftWidth: 4,
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
  },
  methodologyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  methodologyHeaderLeft: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  methodologyIconWrap: {
    width: 24, height: 24, borderRadius: 12,
    alignItems: 'center', justifyContent: 'center',
  },
  methodologyTitle: { fontSize: 16, fontWeight: '700', color: COLORS.text },
  weightBadge: {
    paddingHorizontal: 8, paddingVertical: 4, borderRadius: 10,
    backgroundColor: '#fff', borderWidth: 1, borderColor: COLORS.border,
  },
  weightBadgeText: { fontSize: 12, fontWeight: '700', color: COLORS.text },

  weightTrack: {
    height: 6, backgroundColor: '#E5E7EB', borderRadius: 3,
    overflow: 'hidden', marginBottom: 8,
  },
  weightFill: { height: '100%', borderRadius: 3 },

  methodologySummary: { color: COLORS.subtext, fontSize: 13, lineHeight: 18, marginBottom: 8 },
  methodologyBody: { marginTop: 4 },
  tagsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  pillTag: { backgroundColor: '#111827', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 16 },
  pillTagText: { color: '#fff', fontSize: 12, fontWeight: '600' },
  methodologyFootnote: { marginTop: 10, fontSize: 12, color: COLORS.subtext, lineHeight: 18 },

  dataSourcesCard: {
    backgroundColor: COLORS.card,
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginTop: 8,
  },
  dataSourcesTitle: { fontSize: 14, fontWeight: '700', color: COLORS.text, marginBottom: 8 },
  dataSourcesNote: { marginTop: 8, fontSize: 12, color: COLORS.subtext, lineHeight: 18 },

  // Toggle styles
  pillToggle: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, borderWidth: 1, borderColor: COLORS.primary, backgroundColor: COLORS.card },
  pillActive: { backgroundColor: COLORS.primary },
  pillText: { fontSize: 12, fontWeight: '600', color: COLORS.primary },
  pillTextActive: { color: '#fff' },
  
  // Button row styles
  buttonRow: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  
  // Cash safety warning styles
  cashWarning: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#F59E0B',
  },
  cashWarningText: {
    color: '#92400E',
    fontSize: 13,
    fontWeight: '600',
    marginLeft: 6,
  },
});