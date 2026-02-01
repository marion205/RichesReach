// features/stocks/components/ChanQuantSignalsCard.tsx
/**
 * Chan Quantitative Signals Card
 * Displays mean reversion, momentum, Kelly, and regime robustness signals
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { useQuery, gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import KellyDrawdownOrb from '../../../components/quant/KellyDrawdownOrb';

const CHAN_QUANT_SIGNALS_QUERY = gql`
  query ChanQuantSignals($symbol: String!) {
    chanQuantSignals(symbol: $symbol) {
      symbol
      meanReversion {
        deviationSigma
        reversionProbability
        expectedDrawdown
        timeframeDays
        confidence
        explanation
      }
      momentum {
        timingConfidence
        momentumDecayProbability
        trendPersistenceHalfLife
        momentumAlignment {
          daily
          weekly
          monthly
        }
        confidence
        explanation
      }
      kellyPositionSize {
        kellyFraction
        recommendedFraction
        maxDrawdownRisk
        winRate
        avgWin
        avgLoss
        explanation
      }
      regimeRobustness {
        robustnessScore
        regimesTested
        worstRegimePerformance
        bestRegimePerformance
        explanation
      }
    }
  }
`;

interface ChanQuantSignalsCardProps {
  symbol: string;
  onShowExplainer?: () => void;
}

export default function ChanQuantSignalsCard({ symbol, onShowExplainer }: ChanQuantSignalsCardProps) {
  const { data, loading, error } = useQuery(CHAN_QUANT_SIGNALS_QUERY, {
    variables: { symbol },
    skip: !symbol,
  });

  if (loading) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Quant Signals</Text>
          <Text style={styles.subtitle}>Based on Ernest P. Chan's methods</Text>
        </View>
        <Text style={styles.loadingText}>Loading quantitative signals...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Quant Signals</Text>
          <Text style={styles.subtitle}>Based on Ernest P. Chan's methods</Text>
        </View>
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={24} color="#EF4444" />
          <Text style={styles.errorText}>Unable to load quantitative signals</Text>
          <Text style={styles.errorSubtext}>{error.message || 'Please try again later'}</Text>
        </View>
      </View>
    );
  }

  if (!data?.chanQuantSignals) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Quant Signals</Text>
          <Text style={styles.subtitle}>Based on Ernest P. Chan's methods</Text>
        </View>
        <View style={styles.errorContainer}>
          <Icon name="info" size={24} color="#6B7280" />
          <Text style={styles.errorText}>No quantitative signals available</Text>
          <Text style={styles.errorSubtext}>Data may not be available for this symbol</Text>
        </View>
      </View>
    );
  }

  const signals = data.chanQuantSignals;

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Quant Signals</Text>
          <Text style={styles.subtitle}>Based on Ernest P. Chan's methods</Text>
        </View>
        {onShowExplainer && (
          <TouchableOpacity onPress={onShowExplainer} style={styles.infoButton}>
            <Icon name="info" size={20} color="#3B82F6" />
          </TouchableOpacity>
        )}
      </View>

      {/* Mean Reversion */}
      {signals.meanReversion && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Icon name="trending-down" size={20} color="#3B82F6" />
            <Text style={styles.sectionTitle}>Mean Reversion</Text>
            <View style={[styles.confidenceBadge, { backgroundColor: getConfidenceColor(signals.meanReversion.confidence) + '20' }]}>
              <Text style={[styles.confidenceText, { color: getConfidenceColor(signals.meanReversion.confidence) }]}>
                {signals.meanReversion.confidence.toUpperCase()}
              </Text>
            </View>
          </View>
          <View style={styles.metricsRow}>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Deviation</Text>
              <Text style={styles.metricValue}>{signals.meanReversion.deviationSigma.toFixed(2)}σ</Text>
            </View>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Reversion Prob</Text>
              <Text style={styles.metricValue}>{(signals.meanReversion.reversionProbability * 100).toFixed(1)}%</Text>
            </View>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Max Drawdown</Text>
              <Text style={styles.metricValue}>{(signals.meanReversion.expectedDrawdown * 100).toFixed(1)}%</Text>
            </View>
          </View>
          <Text style={styles.explanation}>{signals.meanReversion.explanation}</Text>
        </View>
      )}

      {/* Momentum */}
      {signals.momentum && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Icon name="trending-up" size={20} color="#10B981" />
            <Text style={styles.sectionTitle}>Momentum</Text>
            <View style={[styles.confidenceBadge, { backgroundColor: getConfidenceColor(signals.momentum.confidence) + '20' }]}>
              <Text style={[styles.confidenceText, { color: getConfidenceColor(signals.momentum.confidence) }]}>
                {signals.momentum.confidence.toUpperCase()}
              </Text>
            </View>
          </View>
          <View style={styles.momentumAlignment}>
            <View style={styles.alignmentItem}>
              <Text style={styles.alignmentLabel}>Daily</Text>
              <Icon 
                name={signals.momentum.momentumAlignment.daily ? "check-circle" : "x-circle"} 
                size={20} 
                color={signals.momentum.momentumAlignment.daily ? "#10B981" : "#EF4444"} 
              />
            </View>
            <View style={styles.alignmentItem}>
              <Text style={styles.alignmentLabel}>Weekly</Text>
              <Icon 
                name={signals.momentum.momentumAlignment.weekly ? "check-circle" : "x-circle"} 
                size={20} 
                color={signals.momentum.momentumAlignment.weekly ? "#10B981" : "#EF4444"} 
              />
            </View>
            <View style={styles.alignmentItem}>
              <Text style={styles.alignmentLabel}>Monthly</Text>
              <Icon 
                name={signals.momentum.momentumAlignment.monthly ? "check-circle" : "x-circle"} 
                size={20} 
                color={signals.momentum.momentumAlignment.monthly ? "#10B981" : "#EF4444"} 
              />
            </View>
          </View>
          <View style={styles.metricsRow}>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Timing Confidence</Text>
              <Text style={styles.metricValue}>{(signals.momentum.timingConfidence * 100).toFixed(0)}%</Text>
            </View>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Decay Prob (7d)</Text>
              <Text style={styles.metricValue}>{(signals.momentum.momentumDecayProbability * 100).toFixed(1)}%</Text>
            </View>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Half-Life</Text>
              <Text style={styles.metricValue}>{signals.momentum.trendPersistenceHalfLife.toFixed(0)}d</Text>
            </View>
          </View>
          <Text style={styles.explanation}>{signals.momentum.explanation}</Text>
        </View>
      )}

      {/* Kelly Position Size */}
      {signals.kellyPositionSize && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Icon name="target" size={20} color="#F59E0B" />
            <Text style={styles.sectionTitle}>Kelly Position Sizing</Text>
          </View>
          <KellyDrawdownOrb
            kellyFraction={signals.kellyPositionSize.kellyFraction}
            recommendedFraction={signals.kellyPositionSize.recommendedFraction}
            maxDrawdownRisk={signals.kellyPositionSize.maxDrawdownRisk}
            winRate={signals.kellyPositionSize.winRate}
            avgWin={signals.kellyPositionSize.avgWin}
            avgLoss={signals.kellyPositionSize.avgLoss}
            symbol={symbol}
            showDetails={true}
          />
          <Text style={styles.explanation}>{signals.kellyPositionSize.explanation}</Text>
        </View>
      )}

      {/* Regime Robustness */}
      {signals.regimeRobustness && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Icon name="shield" size={20} color="#8B5CF6" />
            <Text style={styles.sectionTitle}>Regime Robustness</Text>
            <View style={styles.robustnessScore}>
              <Text style={styles.robustnessValue}>{(signals.regimeRobustness.robustnessScore * 100).toFixed(0)}%</Text>
            </View>
          </View>
          <Text style={styles.regimesList}>
            Tested: {signals.regimeRobustness.regimesTested.join(', ')}
          </Text>
          <View style={styles.metricsRow}>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Worst Regime</Text>
              <Text style={styles.metricValue}>{signals.regimeRobustness.worstRegimePerformance.toFixed(2)}</Text>
            </View>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Best Regime</Text>
              <Text style={styles.metricValue}>{signals.regimeRobustness.bestRegimePerformance.toFixed(2)}</Text>
            </View>
          </View>
          <Text style={styles.explanation}>{signals.regimeRobustness.explanation}</Text>
        </View>
      )}
    </ScrollView>
  );
}

function getConfidenceColor(confidence: string): string {
  switch (confidence.toLowerCase()) {
    case 'high':
      return '#10B981';
    case 'medium':
      return '#F59E0B';
    case 'low':
      return '#EF4444';
    default:
      return '#6B7280';
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    color: '#111827',
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
    fontWeight: '500',
  },
  infoButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  section: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    flex: 1,
  },
  confidenceBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  confidenceText: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  metric: {
    flex: 1,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
    fontWeight: '500',
  },
  metricValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  momentumAlignment: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
    paddingVertical: 12,
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
  },
  alignmentItem: {
    alignItems: 'center',
    gap: 8,
  },
  alignmentLabel: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '500',
  },
  explanation: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
    marginTop: 8,
  },
  robustnessScore: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#8B5CF6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  robustnessValue: {
    fontSize: 20,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  regimesList: {
    fontSize: 13,
    color: '#6B7280',
    marginBottom: 12,
    fontWeight: '500',
  },
  loadingText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    padding: 20,
  },
  errorContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
    gap: 12,
  },
  errorText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    textAlign: 'center',
  },
  errorSubtext: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 4,
  },
});

