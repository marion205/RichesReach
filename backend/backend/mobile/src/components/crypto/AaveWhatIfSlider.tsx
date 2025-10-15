// AAVE What-if stress test slider (HF + LTV)
// - Inputs: collateralUsd, debtUsd (or loanUsd), ltv (0..1), liqThreshold (0..1)
// - Outputs via onStressChange: { shock, hf, ltvPct, capUsd, headroomUsd, tier }
// NOTE: If you use Expo and have @react-native-community/slider, switch the import

import React, { useState, useEffect, useMemo } from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
// If you already use the RN core Slider, keep your import. Otherwise prefer community slider:
import Slider from '@react-native-community/slider';
import { fmtUsd, fmtPercent } from '../../shared/utils/format';

type Tier = 'SAFE' | 'WARN' | 'TOP_UP' | 'AT_RISK' | 'LIQUIDATE';

export interface AAVEStressResult {
  shock: number;
  hf: number;              // Health Factor under stress
  ltvPct: number;          // LTV under stress (%)
  capUsd: number;          // Borrow cap = stressedCollat * ltv
  headroomUsd: number;     // cap - debt
  collateralValue: number; // stressed collateral
  debtUsd: number;         // fixed debt input
  tier: Tier;
}

interface Props {
  collateralUsd: number;
  // Back-compat with your old API:
  debtUsd?: number;
  loanUsd?: number;
  // AAVE reserve params (0..1). Defaults are sane if not provided.
  ltv?: number;               // e.g. 0.7
  liqThreshold?: number;      // e.g. 0.8
  onStressChange: (r: AAVEStressResult) => void;
  style?: any;
}

const tierFromHF = (hf: number): Tier => {
  if (!isFinite(hf) || hf > 1.5) return 'SAFE';
  if (hf > 1.2) return 'WARN';
  if (hf > 1.05) return 'TOP_UP';
  if (hf > 1.0) return 'AT_RISK';
  return 'LIQUIDATE';
};

const tierColor = (t: Tier) =>
  ({ SAFE:'#10B981', WARN:'#F59E0B', TOP_UP:'#EF4444', AT_RISK:'#DC2626', LIQUIDATE:'#7C2D12' }[t] || '#6B7280');

const tierMsg = (t: Tier, hf: number) => {
  const txt = hf === Infinity ? '∞' : hf.toFixed(2);
  switch (t) {
    case 'SAFE': return `Healthy — HF ${txt}`;
    case 'WARN': return `Monitor — HF ${txt}`;
    case 'TOP_UP': return `Consider adding collateral — HF ${txt}`;
    case 'AT_RISK': return `Immediate action — HF ${txt}`;
    default: return `Liquidation risk — HF ${txt}`;
  }
};

const AAVEWhatIfSlider: React.FC<Props> = ({
  collateralUsd,
  debtUsd,
  loanUsd,
  ltv = 0.7,
  liqThreshold = 0.8,
  onStressChange,
  style,
}) => {
  const [shock, setShock] = useState(0);
  const debt = useMemo(() => Math.max(0, Number(debtUsd ?? loanUsd ?? 0)), [debtUsd, loanUsd]);

  const [state, setState] = useState<AAVEStressResult>({
    shock: 0,
    hf: Infinity,
    ltvPct: 0,
    capUsd: collateralUsd * ltv,
    headroomUsd: collateralUsd * ltv - debt,
    collateralValue: collateralUsd,
    debtUsd: debt,
    tier: 'SAFE',
  });

  useEffect(() => {
    const stressedColl = Math.max(0.01, collateralUsd * (1 + shock));
    const capUsd = stressedColl * ltv;
    const ltvPct = debt > 0 ? (debt / stressedColl) * 100 : 0;
    const hf = debt > 0 ? (stressedColl * liqThreshold) / debt : Infinity;
    const headroomUsd = Math.max(0, capUsd - debt);
    const tier = tierFromHF(hf);

    const next: AAVEStressResult = {
      shock,
      hf,
      ltvPct,
      capUsd,
      headroomUsd,
      collateralValue: stressedColl,
      debtUsd: debt,
      tier,
    };
    setState(next);
    onStressChange(next);
  }, [shock, collateralUsd, debt, ltv, liqThreshold, onStressChange]);

  return (
    <View style={[styles.container, style]}>
      <Text style={styles.title}>Stress Test (AAVE)</Text>

      <View style={styles.sliderContainer}>
        <Text style={styles.label}>Market Shock: {fmtPercent(shock * 100)}</Text>
        <Slider
          style={styles.slider}
          minimumValue={-0.5}
          maximumValue={0.2}
          step={0.01}
          value={shock}
          onValueChange={setShock}
          minimumTrackTintColor={tierColor(state.tier)}
          maximumTrackTintColor="#E5E7EB"
          thumbTintColor={Platform.OS === 'android' ? '#007AFF' : undefined}
        />
        <View style={styles.rangeLabels}>
          <Text style={styles.rangeLabel}>-50%</Text>
          <Text style={styles.rangeLabel}>0%</Text>
          <Text style={styles.rangeLabel}>+20%</Text>
        </View>
      </View>

      <View style={[styles.resultCard, { borderLeftColor: tierColor(state.tier) }]}>
        <View style={styles.resultHeader}>
          <Text style={styles.resultTitle}>Stress Results</Text>
          <View style={[styles.tierBadge, { backgroundColor: tierColor(state.tier) }]}>
            <Text style={styles.tierText}>{state.tier}</Text>
          </View>
        </View>

        <View style={styles.metricsGrid}>
          <Metric label="Collateral" value={fmtUsd(state.collateralValue)} />
          <Metric label="Debt" value={fmtUsd(state.debtUsd)} />
          <Metric label="LTV" value={`${state.ltvPct.toFixed(1)}%`} valueStyle={{ color: tierColor(state.tier) }} />
          <Metric label="Health Factor" value={isFinite(state.hf) ? state.hf.toFixed(2) : '∞'} valueStyle={{ color: tierColor(state.tier) }} />
          <Metric label="Borrow Cap" value={fmtUsd(state.capUsd)} />
          <Metric label="Headroom" value={fmtUsd(state.headroomUsd)} />
        </View>

        <Text style={[styles.message, { color: tierColor(state.tier) }]}>
          {tierMsg(state.tier, state.hf)}
        </Text>
      </View>
    </View>
  );
};

const Metric = ({ label, value, valueStyle }: { label: string; value: string; valueStyle?: any }) => (
  <View style={styles.metric}>
    <Text style={styles.metricLabel}>{label}</Text>
    <Text style={[styles.metricValue, valueStyle]}>{value}</Text>
  </View>
);

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  title: { fontSize: 18, fontWeight: '700', color: '#111827', marginBottom: 16 },
  sliderContainer: { marginBottom: 20 },
  label: { fontSize: 16, fontWeight: '600', color: '#111827', marginBottom: 8 },
  slider: { width: '100%', height: 40 },
  rangeLabels: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 },
  rangeLabel: { fontSize: 12, color: '#6B7280' },

  resultCard: { backgroundColor: '#F9FAFB', borderRadius: 8, padding: 16, borderLeftWidth: 4 },
  resultHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  resultTitle: { fontSize: 16, fontWeight: '600', color: '#111827' },
  tierBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12 },
  tierText: { fontSize: 12, fontWeight: '700', color: '#FFFFFF' },

  metricsGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', marginBottom: 12 },
  metric: { width: '48%', marginBottom: 10 },
  metricLabel: { fontSize: 12, color: '#6B7280', marginBottom: 2 },
  metricValue: { fontSize: 16, fontWeight: '700', color: '#111827' },

  message: { fontSize: 14, fontWeight: '500', textAlign: 'center' },
});

export default AAVEWhatIfSlider;
