import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { LinearGradient } from 'expo-linear-gradient';

interface RecommendedStrike {
  strike: number;
  expiration: string;
  optionType: string;
  greeks?: {
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
    rho: number;
  };
  expectedReturn?: number;
  riskScore?: number;
}

interface OptionsNextMoveCardProps {
  symbol: string;
  underlyingPrice: number;
  recommendation: RecommendedStrike;
  onReview: () => void;
  onWhyThis?: () => void;
  onViewFullChain?: () => void;
}

export default function OptionsNextMoveCard({
  symbol,
  underlyingPrice,
  recommendation,
  onReview,
  onWhyThis,
  onViewFullChain,
}: OptionsNextMoveCardProps) {
  // Calculate days to expiration
  const daysToExp = (() => {
    try {
      const expDate = new Date(recommendation.expiration);
      const today = new Date();
      const diff = Math.ceil((expDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
      return diff > 0 ? diff : 0;
    } catch {
      return 0;
    }
  })();

  // Calculate win probability from expected return (simplified)
  const winProbability = recommendation.expectedReturn
    ? Math.min(95, Math.max(5, Math.round(recommendation.expectedReturn * 100)))
    : 64;

  // Estimate max loss (premium paid for calls, strike - premium for puts)
  const isCall = recommendation.optionType.toLowerCase() === 'call';
  const estimatedPremium = isCall
    ? Math.max(0.5, (Math.abs(recommendation.strike - underlyingPrice) * 0.1))
    : Math.max(0.5, (Math.abs(underlyingPrice - recommendation.strike) * 0.1));
  const maxLoss = estimatedPremium * 100; // Per contract, assume 1 contract

  // Format expiration date
  const formatExpiration = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  // Get confidence level
  const getConfidence = () => {
    if (recommendation.riskScore !== undefined) {
      if (recommendation.riskScore < 0.3) return 'High';
      if (recommendation.riskScore < 0.6) return 'Medium';
      return 'Low';
    }
    return 'High';
  };

  const confidence = getConfidence();

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.titleRow}>
            <Text style={styles.cardTitle}>Top Trade</Text>
            <View style={[styles.confidenceBadge, confidence === 'High' && styles.confidenceHigh]}>
              <Text style={styles.confidenceText}>AI Confidence: {confidence}</Text>
            </View>
          </View>
          <Text style={styles.cardSubtitle}>Based on your risk and this market</Text>
        </View>
      </View>

      {/* Main Trade Line */}
      <View style={styles.tradeLine}>
        <Text style={styles.tradeText}>
          {recommendation.optionType === 'call' ? 'Buy' : 'Buy'} 1 × {symbol} ${recommendation.strike.toFixed(2)}{' '}
          {recommendation.optionType === 'call' ? 'Call' : 'Put'}
        </Text>
        <Text style={styles.expirationText}>expires in {daysToExp} days</Text>
      </View>

      {/* Three Key Numbers */}
      <View style={styles.metricsRow}>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Win chance</Text>
          <Text style={styles.metricValue}>{winProbability}%</Text>
        </View>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Max loss</Text>
          <Text style={styles.metricValue}>${maxLoss.toFixed(0)}</Text>
        </View>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Timeframe</Text>
          <Text style={styles.metricValue}>~{daysToExp} days</Text>
        </View>
      </View>

      {/* Action Buttons */}
      <View style={styles.actionsRow}>
        <TouchableOpacity style={styles.secondaryButton} onPress={onWhyThis}>
          <Text style={styles.secondaryButtonText}>Why this trade?</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.primaryButton} onPress={onReview}>
          <Text style={styles.primaryButtonText}>Review & Place Trade</Text>
        </TouchableOpacity>
      </View>

      {/* View Full Chain Link */}
      <TouchableOpacity
        style={styles.fullChainLink}
        onPress={onViewFullChain}
        accessibilityLabel="View full options chain"
        accessibilityHint="Scroll to see all available options contracts"
        accessibilityRole="button"
      >
        <Text style={styles.fullChainText}>View full chain</Text>
        <Icon name="chevron-right" size={14} color="#6B7280" />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  header: {
    marginBottom: 16,
  },
  headerLeft: {
    flex: 1,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
    gap: 8,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  cardSubtitle: {
    fontSize: 13,
    color: '#6B7280',
  },
  confidenceBadge: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
  },
  confidenceHigh: {
    backgroundColor: '#D1FAE5',
  },
  confidenceText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#059669',
  },
  tradeLine: {
    marginBottom: 20,
  },
  tradeText: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  expirationText: {
    fontSize: 14,
    color: '#6B7280',
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  metric: {
    flex: 1,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 6,
  },
  metricValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  secondaryButton: {
    flex: 1,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#E5E7EB',
    alignItems: 'center',
  },
  secondaryButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#374151',
  },
  primaryButton: {
    flex: 2,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: '#007AFF',
    alignItems: 'center',
  },
  primaryButtonText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  fullChainLink: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 8,
  },
  fullChainText: {
    fontSize: 13,
    color: '#6B7280',
    marginRight: 4,
  },
});

