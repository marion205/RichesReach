import React, { useMemo } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import EducationalTooltip from './EducationalTooltip';
import { getTermExplanation } from '../data/financialTerms';

interface Holding {
  symbol: string;
  companyName: string;
  shares: number;
  currentPrice: number;
  totalValue: number;
  costBasis: number;
  returnAmount: number;
  returnPercent: number; // assumed % over same period for every holding
  sector?: string | null;
}

interface BasicRiskMetricsProps {
  holdings: Holding[];
  totalValue: number;
  totalReturn: number;
  totalReturnPercent: number;
  onNavigate?: (screen: string, data?: any) => void;
  hasPremiumAccess?: boolean;
}

const RISK_THRESHOLDS = {
  lowVol: 5,
  medVol: 15,
  goodDiversification: 70,
  okDiversification: 50,
  topHoldingWarn: 0.15,   // 15%+
  topSectorWarn: 0.35,    // 35%+
};

const BasicRiskMetrics: React.FC<BasicRiskMetricsProps> = ({
  holdings,
  totalValue,
  totalReturn,
  totalReturnPercent,
  onNavigate,
  hasPremiumAccess = false,
}) => {
  // ------- guards -------
  const sanitized = useMemo(() => (holdings || []).filter(h => h && h.totalValue > 0), [holdings]);
  const portfolioValue = Math.max(
    totalValue || sanitized.reduce((s, h) => s + (h.totalValue || 0), 0),
    0
  );
  const empty = sanitized.length === 0 || portfolioValue === 0;

  // ------- sector weights / HHI diversification -------
  const { sectorWeights, diversificationScore, topSectorWeight } = useMemo(() => {
    if (empty) return { sectorWeights: {}, diversificationScore: 0, topSectorWeight: 0 };

    const weights: Record<string, number> = {};
    sanitized.forEach(h => {
      const sector = (h.sector || 'Other').trim();
      const w = (h.totalValue || 0) / portfolioValue;
      if (!isFinite(w) || w <= 0) return;
      weights[sector] = (weights[sector] || 0) + w;
    });

    // Herfindahl–Hirschman Index (lower = more diversified)
    // HHI = sum(w_i^2); normalize to 0..100 score where 100 = perfectly diversified (many tiny weights)
    const hhi = Object.values(weights).reduce((s, w) => s + w * w, 0); // 1..(1/N)
    // Map: if single sector (hhi=1) -> 0; if evenly across 7 sectors (hhi≈1/7) -> ~85; across 10 -> ~90+
    const score = Math.max(0, Math.min(100, Math.round((1 - hhi) * 120)));

    const topW = Math.max(0, ...Object.values(weights));
    return { sectorWeights: weights, diversificationScore: score, topSectorWeight: topW };
  }, [empty, sanitized, portfolioValue]);

  // ------- value-weighted cross-sectional volatility (dispersion of holding returns) -------
  const { volatilityPct, topHoldingWeight } = useMemo(() => {
    if (empty) return { volatilityPct: 0, topHoldingWeight: 0 };

    // We only have each holding's period returnPercent (not daily). Use cross-sectional dispersion as a proxy.
    const weights = sanitized.map(h => (h.totalValue || 0) / portfolioValue);
    const rets = sanitized.map(h => Number(h.returnPercent) || 0);

    const mean = rets.reduce((s, r, i) => s + r * weights[i], 0);
    const variance =
      rets.reduce((s, r, i) => s + weights[i] * Math.pow(r - mean, 2), 0) /
      Math.max(1, weights.length);
    const vol = Math.sqrt(Math.max(0, variance));

    const topW = Math.max(0, ...weights);
    return { volatilityPct: Math.round(vol * 10) / 10, topHoldingWeight: topW };
  }, [empty, sanitized, portfolioValue]);

  // ------- levels & helpers -------
  const riskLevel =
    volatilityPct < RISK_THRESHOLDS.lowVol
      ? { level: 'Low', color: '#34C759', icon: 'shield' }
      : volatilityPct < RISK_THRESHOLDS.medVol
      ? { level: 'Medium', color: '#FF9500', icon: 'alert-triangle' }
      : { level: 'High', color: '#FF3B30', icon: 'alert-circle' };

  const diversificationLevel =
    diversificationScore >= 80
      ? { level: 'Excellent', color: '#34C759', icon: 'check-circle' }
      : diversificationScore >= RISK_THRESHOLDS.goodDiversification
      ? { level: 'Good', color: '#32D74B', icon: 'thumbs-up' }
      : diversificationScore >= RISK_THRESHOLDS.okDiversification
      ? { level: 'Fair', color: '#FF9500', icon: 'minus-circle' }
      : { level: 'Poor', color: '#FF3B30', icon: 'x-circle' };

  const holdingsCount = sanitized.length;
  const sectorCount = Object.keys(sectorWeights).length;

  // concentration flags
  const concentrationFlags: string[] = [];
  if (topHoldingWeight >= RISK_THRESHOLDS.topHoldingWarn) {
    concentrationFlags.push(`Top holding is ${(topHoldingWeight * 100).toFixed(0)}% of portfolio`);
  }
  if (topSectorWeight >= RISK_THRESHOLDS.topSectorWarn) {
    concentrationFlags.push(`Top sector is ${(topSectorWeight * 100).toFixed(0)}%`);
  }

  return (
    <View style={styles.container} accessibilityRole="summary">
      <View style={styles.header}>
        <View style={styles.titleContainer}>
          <Icon name="bar-chart-2" size={20} color="#007AFF" />
          <Text style={styles.title}>Risk & Diversification</Text>
        </View>
        <Text style={styles.subtitle} accessibilityLabel="Plan tier">
          Free Analysis
        </Text>
      </View>

      {/* Diversification */}
      <View style={styles.metricCard}>
        <EducationalTooltip
          term="Diversification"
          explanation={getTermExplanation('Diversification')}
          position="top"
        >
          <View style={styles.metricHeader}>
            <Icon name={diversificationLevel.icon} size={16} color={diversificationLevel.color} />
            <Text style={styles.metricTitle}>Diversification</Text>
          </View>
        </EducationalTooltip>

        <View style={styles.metricContent}>
          <Text style={[styles.metricValue, { color: diversificationLevel.color }]}>
            {diversificationScore}/100
          </Text>
          <Text style={[styles.metricLevel, { color: diversificationLevel.color }]}>
            {diversificationLevel.level}
          </Text>
        </View>

        <View
          style={styles.progressBar}
          accessibilityRole="progressbar"
          accessibilityValue={{ now: diversificationScore, min: 0, max: 100 }}
        >
          <View
            style={[
              styles.progressFill,
              { width: `${diversificationScore}%`, backgroundColor: diversificationLevel.color },
            ]}
          />
        </View>

        <Text style={styles.metricDescription}>
          {holdingsCount} holdings across {sectorCount} {sectorCount === 1 ? 'sector' : 'sectors'}
        </Text>

        {concentrationFlags.length > 0 && (
          <View style={styles.flagList}>
            {concentrationFlags.map((f, i) => (
              <View key={i} style={styles.flagItem}>
                <Icon name="alert-octagon" size={12} color="#FF3B30" />
                <Text style={styles.flagText}>{f}</Text>
              </View>
            ))}
          </View>
        )}
      </View>

      {/* Volatility */}
      <View style={styles.metricCard}>
        <EducationalTooltip
          term="Volatility"
          explanation={getTermExplanation('Volatility')}
          position="top"
        >
          <View style={styles.metricHeader}>
            <Icon name={riskLevel.icon} size={16} color={riskLevel.color} />
            <Text style={styles.metricTitle}>Volatility</Text>
          </View>
        </EducationalTooltip>

        <View style={styles.metricContent}>
          <Text style={[styles.metricValue, { color: riskLevel.color }]}>{volatilityPct}%</Text>
          <Text style={[styles.metricLevel, { color: riskLevel.color }]}>{riskLevel.level} Risk</Text>
        </View>

        {/* Position the indicator on a 0–50% scale to avoid going off track on noisy inputs */}
        <View style={styles.riskBar}>
          <View
            style={[
              styles.riskIndicator,
              {
                left: `${Math.min((volatilityPct / 50) * 100, 100)}%`,
                backgroundColor: riskLevel.color,
              },
            ]}
          />
        </View>

        <Text style={styles.metricDescription}>
          Measured as dispersion of holding returns (value-weighted)
        </Text>
      </View>

      {/* Premium CTA */}
      <TouchableOpacity
        testID="risk-upgrade-cta"
        style={styles.upgradePrompt}
        onPress={() => onNavigate?.(hasPremiumAccess ? 'premium-analytics' : 'subscription')}
        activeOpacity={0.7}
        accessibilityRole="button"
        accessibilityLabel={hasPremiumAccess ? 'Open premium analytics' : 'Unlock advanced analytics'}
      >
        <View style={styles.upgradeContent}>
          <Icon name="star" size={16} color="#FFD60A" />
          <Text style={styles.upgradeText}>
            {hasPremiumAccess ? 'Premium Analytics' : 'Unlock advanced analytics with Premium'}
          </Text>
        </View>
        <Icon name="chevron-right" size={16} color="#8E8E93" />
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { backgroundColor: '#FFFFFF', borderRadius: 16, padding: 16, marginVertical: 8,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 6, elevation: 3 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  titleContainer: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  title: { fontSize: 18, fontWeight: '700', color: '#1C1C1E' },
  subtitle: { fontSize: 12, color: '#8E8E93', backgroundColor: '#F2F2F7', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8 },

  metricsContainer: { gap: 16 },
  metricCard: { backgroundColor: '#F8F9FA', borderRadius: 12, padding: 16, marginBottom: 12 },
  metricHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  metricTitle: { fontSize: 14, fontWeight: '600', color: '#1C1C1E' },
  metricContent: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  metricValue: { fontSize: 24, fontWeight: '700' },
  metricLevel: { fontSize: 14, fontWeight: '600' },

  progressBar: { height: 6, backgroundColor: '#E5E5EA', borderRadius: 3, marginBottom: 8, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 3 },

  riskBar: { height: 6, backgroundColor: '#E5E5EA', borderRadius: 3, marginBottom: 8, position: 'relative' },
  riskIndicator: { position: 'absolute', top: -2, width: 10, height: 10, borderRadius: 5, borderWidth: 2, borderColor: '#FFFFFF' },

  metricDescription: { fontSize: 12, color: '#8E8E93', lineHeight: 16 },

  flagList: { marginTop: 6, gap: 4 },
  flagItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  flagText: { fontSize: 12, color: '#FF3B30' },

  upgradePrompt: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    backgroundColor: '#F2F2F7', borderRadius: 12, padding: 12, marginTop: 4 },
  upgradeContent: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  upgradeText: { fontSize: 14, fontWeight: '500', color: '#1C1C1E' },
});

export default BasicRiskMetrics;