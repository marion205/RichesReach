import React, { useMemo } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useOptionsPositions } from '../../hooks/useOptionsPositions';
import { useAlpacaAccount } from '../../features/stocks/hooks/useAlpacaAccount';

export default function PortfolioRiskManager() {
  const { alpacaAccount } = useAlpacaAccount(1);
  const { positions: optionsPositions } = useOptionsPositions(alpacaAccount?.id || null);

  // Calculate portfolio-level Greeks
  const portfolioGreeks = useMemo(() => {
    let totalDelta = 0;
    let totalGamma = 0;
    let totalTheta = 0;
    let totalVega = 0;
    let totalRho = 0;
    let totalNotional = 0;
    let totalCost = 0;
    let totalUnrealizedPL = 0;

    optionsPositions.forEach((pos: any) => {
      const qty = pos.qty || 0;
      const currentPrice = pos.currentPrice || pos.avgEntryPrice || 0;
      const entryPrice = pos.avgEntryPrice || 0;
      
      // Simplified Greeks calculation (would use actual options pricing model in production)
      const isCall = pos.optionType === 'call';
      const strike = pos.strike || 0;
      const underlyingPrice = currentPrice; // Would get from market data
      
      // Simplified delta (would use Black-Scholes in production)
      const moneyness = isCall 
        ? (underlyingPrice - strike) / strike
        : (strike - underlyingPrice) / strike;
      const delta = isCall 
        ? Math.max(0, Math.min(1, 0.5 + moneyness * 0.5))
        : Math.max(-1, Math.min(0, -0.5 + moneyness * 0.5));
      
      // Simplified Greeks (would calculate properly in production)
      const positionDelta = delta * qty * 100;
      const positionGamma = 0.01 * qty * 100; // Simplified
      const positionTheta = -0.05 * qty * 100; // Time decay
      const positionVega = 0.1 * qty * 100; // Volatility sensitivity
      const positionRho = 0.02 * qty * 100; // Interest rate sensitivity

      totalDelta += positionDelta;
      totalGamma += positionGamma;
      totalTheta += positionTheta;
      totalVega += positionVega;
      totalRho += positionRho;
      
      totalNotional += Math.abs(qty * 100 * currentPrice);
      totalCost += Math.abs(qty * 100 * entryPrice);
      totalUnrealizedPL += (pos.unrealizedPl || pos.unrealizedPL || 0) * qty;
    });

    // Calculate portfolio risk metrics
    const portfolioDelta = totalDelta;
    const portfolioGamma = totalGamma;
    const portfolioTheta = totalTheta;
    const portfolioVega = totalVega;
    const portfolioRho = totalRho;

    // Risk assessment
    const riskLevel = Math.abs(portfolioDelta) > 1000 ? 'High' : 
                     Math.abs(portfolioDelta) > 500 ? 'Medium' : 'Low';

    // Probability calculations (simplified)
    const probabilityOfProfit = portfolioDelta > 0 ? 55 : 45; // Simplified

    return {
      delta: portfolioDelta,
      gamma: portfolioGamma,
      theta: portfolioTheta,
      vega: portfolioVega,
      rho: portfolioRho,
      totalNotional,
      totalCost,
      totalUnrealizedPL,
      riskLevel,
      probabilityOfProfit,
      positionCount: optionsPositions.length,
    };
  }, [optionsPositions]);

  if (optionsPositions.length === 0) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Icon name="shield" size={18} color="#007AFF" />
          <Text style={styles.title}>Portfolio Risk Management</Text>
        </View>
        <View style={styles.emptyState}>
          <Icon name="info" size={24} color="#9CA3AF" />
          <Text style={styles.emptyText}>No options positions to analyze</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="shield" size={18} color="#007AFF" />
        <Text style={styles.title}>Portfolio Risk Management</Text>
        <View style={[styles.riskBadge, portfolioGreeks.riskLevel === 'High' && styles.riskBadgeHigh]}>
          <Text style={styles.riskBadgeText}>{portfolioGreeks.riskLevel} Risk</Text>
        </View>
      </View>

      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Portfolio Greeks */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Portfolio Greeks</Text>
          <View style={styles.greeksGrid}>
            <View style={styles.greekCard}>
              <Text style={styles.greekLabel}>Delta</Text>
              <Text style={[styles.greekValue, portfolioGreeks.delta > 0 ? styles.positive : styles.negative]}>
                {portfolioGreeks.delta > 0 ? '+' : ''}{portfolioGreeks.delta.toFixed(2)}
              </Text>
              <Text style={styles.greekDescription}>Price sensitivity</Text>
            </View>
            <View style={styles.greekCard}>
              <Text style={styles.greekLabel}>Gamma</Text>
              <Text style={styles.greekValue}>{portfolioGreeks.gamma.toFixed(2)}</Text>
              <Text style={styles.greekDescription}>Delta sensitivity</Text>
            </View>
            <View style={styles.greekCard}>
              <Text style={styles.greekLabel}>Theta</Text>
              <Text style={[styles.greekValue, styles.negative]}>
                {portfolioGreeks.theta.toFixed(2)}
              </Text>
              <Text style={styles.greekDescription}>Time decay (daily)</Text>
            </View>
            <View style={styles.greekCard}>
              <Text style={styles.greekLabel}>Vega</Text>
              <Text style={styles.greekValue}>{portfolioGreeks.vega.toFixed(2)}</Text>
              <Text style={styles.greekDescription}>Volatility sensitivity</Text>
            </View>
            <View style={styles.greekCard}>
              <Text style={styles.greekLabel}>Rho</Text>
              <Text style={styles.greekValue}>{portfolioGreeks.rho.toFixed(2)}</Text>
              <Text style={styles.greekDescription}>Interest rate sensitivity</Text>
            </View>
          </View>
        </View>

        {/* Portfolio Metrics */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Portfolio Metrics</Text>
          <View style={styles.metricsCard}>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Total Positions</Text>
              <Text style={styles.metricValue}>{portfolioGreeks.positionCount}</Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Total Notional</Text>
              <Text style={styles.metricValue}>${portfolioGreeks.totalNotional.toLocaleString()}</Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Total Cost</Text>
              <Text style={styles.metricValue}>${portfolioGreeks.totalCost.toLocaleString()}</Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Unrealized P&L</Text>
              <Text style={[
                styles.metricValue,
                portfolioGreeks.totalUnrealizedPL >= 0 ? styles.positive : styles.negative
              ]}>
                {portfolioGreeks.totalUnrealizedPL >= 0 ? '+' : ''}${portfolioGreeks.totalUnrealizedPL.toLocaleString()}
              </Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Probability of Profit</Text>
              <Text style={styles.metricValue}>{portfolioGreeks.probabilityOfProfit}%</Text>
            </View>
          </View>
        </View>

        {/* Risk Warnings */}
        {portfolioGreeks.riskLevel === 'High' && (
          <View style={styles.warningCard}>
            <Icon name="alert-triangle" size={20} color="#DC2626" />
            <Text style={styles.warningTitle}>High Risk Detected</Text>
            <Text style={styles.warningText}>
              Your portfolio has high delta exposure. Consider hedging or reducing position size.
            </Text>
          </View>
        )}

        {Math.abs(portfolioGreeks.theta) > 50 && (
          <View style={styles.warningCard}>
            <Icon name="clock" size={20} color="#F59E0B" />
            <Text style={styles.warningTitle}>High Time Decay</Text>
            <Text style={styles.warningText}>
              Your portfolio is losing ${Math.abs(portfolioGreeks.theta).toFixed(2)} per day to theta decay.
            </Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    maxHeight: 600,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginLeft: 8,
    flex: 1,
  },
  riskBadge: {
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  riskBadgeHigh: {
    backgroundColor: '#FEE2E2',
  },
  riskBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#059669',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 14,
    color: '#9CA3AF',
    marginTop: 8,
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  greeksGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  greekCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    alignItems: 'center',
  },
  greekLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 8,
    fontWeight: '600',
  },
  greekValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  greekDescription: {
    fontSize: 11,
    color: '#9CA3AF',
    textAlign: 'center',
  },
  positive: {
    color: '#059669',
  },
  negative: {
    color: '#DC2626',
  },
  metricsCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  metricLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  warningCard: {
    flexDirection: 'row',
    backgroundColor: '#FEF3C7',
    borderRadius: 12,
    padding: 16,
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#FDE68A',
    gap: 12,
  },
  warningTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#92400E',
    marginBottom: 4,
  },
  warningText: {
    fontSize: 14,
    color: '#78350F',
    flex: 1,
  },
});

