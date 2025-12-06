import React, { useMemo } from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

const { width } = Dimensions.get('window');

interface PNLCandleProps {
  realizedPNL?: number;
  unrealizedPNL?: number;
  riskMultiple?: number; // R-multiple
  confidenceScore?: number;
  expectedPNL?: number; // Projected/ghost candle P&L
  expectancy?: number; // Expected value per candle
  showGhost?: boolean; // Show projected future candle
}

export default function PNLCandle({
  realizedPNL = 0,
  unrealizedPNL = 0,
  riskMultiple = 0,
  confidenceScore = 0.5,
  expectedPNL = 0,
  expectancy = 0,
  showGhost = false,
}: PNLCandleProps) {
  const totalPNL = realizedPNL + unrealizedPNL;

  const pnlColor = useMemo(() => {
    if (totalPNL > 0) return '#10B981'; // Green
    if (totalPNL < 0) return '#EF4444'; // Red
    return '#6B7280'; // Gray
  }, [totalPNL]);

  const confidenceColor = useMemo(() => {
    if (confidenceScore >= 0.7) return '#10B981';
    if (confidenceScore >= 0.5) return '#F59E0B';
    return '#EF4444';
  }, [confidenceScore]);

  const rMultipleColor = useMemo(() => {
    if (riskMultiple >= 1) return '#10B981';
    if (riskMultiple >= 0) return '#F59E0B';
    return '#EF4444';
  }, [riskMultiple]);

  const formatCurrency = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}$${Math.abs(value).toFixed(2)}`;
  };

  const formatRMultiple = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}R`;
  };

  return (
    <View style={styles.container}>
      {/* Main P&L Candle */}
      <View style={[styles.candle, { borderColor: pnlColor }]}>
        <View style={styles.candleHeader}>
          <Text style={styles.candleTitle}>P&L Candle</Text>
          <View style={[styles.confidenceBadge, { backgroundColor: confidenceColor + '20' }]}>
            <Icon name="target" size={12} color={confidenceColor} />
            <Text style={[styles.confidenceText, { color: confidenceColor }]}>
              {(confidenceScore * 100).toFixed(0)}%
            </Text>
          </View>
        </View>

        {/* Realized P&L */}
        {realizedPNL !== 0 && (
          <View style={styles.pnlRow}>
            <View style={styles.pnlLabel}>
              <Icon name="check-circle" size={14} color="#6B7280" />
              <Text style={styles.pnlLabelText}>Realized</Text>
            </View>
            <Text style={[styles.pnlValue, { color: realizedPNL >= 0 ? '#10B981' : '#EF4444' }]}>
              {formatCurrency(realizedPNL)}
            </Text>
          </View>
        )}

        {/* Unrealized P&L */}
        {unrealizedPNL !== 0 && (
          <View style={styles.pnlRow}>
            <View style={styles.pnlLabel}>
              <Icon name="clock" size={14} color="#6B7280" />
              <Text style={styles.pnlLabelText}>Unrealized</Text>
            </View>
            <Text style={[styles.pnlValue, { color: unrealizedPNL >= 0 ? '#10B981' : '#EF4444' }]}>
              {formatCurrency(unrealizedPNL)}
            </Text>
          </View>
        )}

        {/* Total P&L */}
        <View style={[styles.pnlRow, styles.totalRow]}>
          <Text style={styles.totalLabel}>Total P&L</Text>
          <Text style={[styles.totalValue, { color: pnlColor }]}>
            {formatCurrency(totalPNL)}
          </Text>
        </View>

        {/* R-Multiple */}
        {riskMultiple !== 0 && (
          <View style={styles.metricRow}>
            <View style={styles.metricLabel}>
              <Icon name="trending-up" size={14} color="#6B7280" />
              <Text style={styles.metricLabelText}>R-Multiple</Text>
            </View>
            <Text style={[styles.metricValue, { color: rMultipleColor }]}>
              {formatRMultiple(riskMultiple)}
            </Text>
          </View>
        )}

        {/* Expectancy */}
        {expectancy !== 0 && (
          <View style={styles.metricRow}>
            <View style={styles.metricLabel}>
              <Icon name="bar-chart-2" size={14} color="#6B7280" />
              <Text style={styles.metricLabelText}>Expectancy</Text>
            </View>
            <Text style={[styles.metricValue, { color: expectancy >= 0 ? '#10B981' : '#EF4444' }]}>
              {formatRMultiple(expectancy)}
            </Text>
          </View>
        )}
      </View>

      {/* Ghost Candle (Projected P&L) */}
      {showGhost && expectedPNL !== 0 && (
        <View style={[styles.ghostCandle, { borderColor: expectedPNL >= 0 ? '#10B981' : '#EF4444' }]}>
          <View style={styles.ghostHeader}>
            <Icon name="eye" size={14} color="#6B7280" />
            <Text style={styles.ghostTitle}>Projected P&L</Text>
          </View>
          <Text style={[styles.ghostValue, { color: expectedPNL >= 0 ? '#10B981' : '#EF4444' }]}>
            {formatCurrency(expectedPNL)}
          </Text>
          <Text style={styles.ghostSubtext}>
            Expected value based on strategy history
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 8,
  },
  candle: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  candleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  candleTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  confidenceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  confidenceText: {
    marginLeft: 4,
    fontSize: 12,
    fontWeight: '600',
  },
  pnlRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  pnlLabel: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  pnlLabelText: {
    marginLeft: 6,
    fontSize: 14,
    color: '#6B7280',
  },
  pnlValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  totalRow: {
    marginTop: 8,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  totalLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  totalValue: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  metricLabel: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  metricLabelText: {
    marginLeft: 6,
    fontSize: 12,
    color: '#6B7280',
  },
  metricValue: {
    fontSize: 14,
    fontWeight: '600',
  },
  ghostCandle: {
    marginTop: 12,
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderStyle: 'dashed',
    opacity: 0.7,
  },
  ghostHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  ghostTitle: {
    marginLeft: 6,
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
  },
  ghostValue: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  ghostSubtext: {
    fontSize: 11,
    color: '#9CA3AF',
    fontStyle: 'italic',
  },
});

