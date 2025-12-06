import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { RAHASignal } from '../hooks/useRAHASignals';

interface RAHASignalOverlayProps {
  signals: RAHASignal[];
  onSignalPress?: (signal: RAHASignal) => void;
  showOnChart?: boolean;
}

export default function RAHASignalOverlay({
  signals,
  onSignalPress,
  showOnChart = false,
}: RAHASignalOverlayProps) {
  if (!signals || signals.length === 0) {
    return null;
  }

  const getSignalColor = (signalType: string) => {
    if (signalType.includes('LONG')) return '#10B981';
    if (signalType.includes('SHORT')) return '#EF4444';
    return '#6B7280';
  };

  const getSignalIcon = (signalType: string) => {
    if (signalType.includes('LONG')) return 'arrow-up';
    if (signalType.includes('SHORT')) return 'arrow-down';
    return 'minus';
  };

  const formatPrice = (price: number) => {
    return `$${price.toFixed(2)}`;
  };

  if (showOnChart) {
    // Render as chart markers (for future chart integration)
    return (
      <View style={styles.chartOverlay}>
        {signals.map((signal) => (
          <View
            key={signal.id}
            style={[
              styles.chartMarker,
              { borderColor: getSignalColor(signal.signalType) },
            ]}
          >
            <Icon
              name={getSignalIcon(signal.signalType)}
              size={12}
              color={getSignalColor(signal.signalType)}
            />
          </View>
        ))}
      </View>
    );
  }

  // Render as list
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="zap" size={16} color="#3B82F6" />
        <Text style={styles.headerText}>RAHA Signals ({signals.length})</Text>
      </View>

      {signals.map((signal) => {
        const signalColor = getSignalColor(signal.signalType);
        const confidenceColor =
          signal.confidenceScore >= 0.7
            ? '#10B981'
            : signal.confidenceScore >= 0.5
            ? '#F59E0B'
            : '#EF4444';

        return (
          <TouchableOpacity
            key={signal.id}
            style={[styles.signalCard, { borderLeftColor: signalColor }]}
            onPress={() => onSignalPress?.(signal)}
            activeOpacity={0.7}
          >
            <View style={styles.signalHeader}>
              <View style={styles.signalTypeContainer}>
                <Icon
                  name={getSignalIcon(signal.signalType)}
                  size={16}
                  color={signalColor}
                />
                <Text style={[styles.signalType, { color: signalColor }]}>
                  {signal.signalType.replace('_', ' ')}
                </Text>
              </View>
              <View style={[styles.confidenceBadge, { backgroundColor: confidenceColor + '20' }]}>
                <Text style={[styles.confidenceText, { color: confidenceColor }]}>
                  {(signal.confidenceScore * 100).toFixed(0)}%
                </Text>
              </View>
            </View>

            <View style={styles.signalDetails}>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Symbol:</Text>
                <Text style={styles.detailValue}>{signal.symbol}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Price:</Text>
                <Text style={styles.detailValue}>{formatPrice(signal.price)}</Text>
              </View>
              {signal.stopLoss && (
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Stop Loss:</Text>
                  <Text style={[styles.detailValue, { color: '#EF4444' }]}>
                    {formatPrice(signal.stopLoss)}
                  </Text>
                </View>
              )}
              {signal.takeProfit && (
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Take Profit:</Text>
                  <Text style={[styles.detailValue, { color: '#10B981' }]}>
                    {formatPrice(signal.takeProfit)}
                  </Text>
                </View>
              )}
            </View>

            {signal.strategyVersion && (
              <View style={styles.strategyBadge}>
                <Icon name="layers" size={12} color="#6B7280" />
                <Text style={styles.strategyText}>
                  {signal.strategyVersion.strategy.name}
                </Text>
              </View>
            )}

            {signal.meta?.regime && (
              <View style={styles.metaBadge}>
                <Icon name="activity" size={12} color="#6B7280" />
                <Text style={styles.metaText}>
                  Regime: {signal.meta.regime}
                </Text>
              </View>
            )}
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 8,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    paddingHorizontal: 4,
  },
  headerText: {
    marginLeft: 6,
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  signalCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  signalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  signalTypeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  signalType: {
    marginLeft: 6,
    fontSize: 14,
    fontWeight: '600',
  },
  confidenceBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  confidenceText: {
    fontSize: 12,
    fontWeight: '600',
  },
  signalDetails: {
    marginBottom: 8,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  detailLabel: {
    fontSize: 12,
    color: '#6B7280',
  },
  detailValue: {
    fontSize: 12,
    fontWeight: '600',
    color: '#111827',
  },
  strategyBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  strategyText: {
    marginLeft: 4,
    fontSize: 11,
    color: '#6B7280',
  },
  metaBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  metaText: {
    marginLeft: 4,
    fontSize: 11,
    color: '#6B7280',
    fontStyle: 'italic',
  },
  chartOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  chartMarker: {
    position: 'absolute',
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    backgroundColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
});

