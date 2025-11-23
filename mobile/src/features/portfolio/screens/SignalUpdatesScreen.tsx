/**
 * Signal Updates Screen
 * Real-time multi-signal fusion updates for stocks
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useQuery, gql } from '@apollo/client';
import { Ionicons } from '@expo/vector-icons';
import { useRoute, useNavigation } from '@react-navigation/native';

const GET_SIGNAL_UPDATES = gql`
  query GetSignalUpdates($symbol: String!, $lookbackHours: Int) {
    signalUpdates(symbol: $symbol, lookbackHours: $lookbackHours) {
      symbol
      timestamp
      fusionScore
      recommendation
      consumerStrength
      signals
      alerts {
        type
        severity
        message
        timestamp
      }
    }
  }
`;

const GET_PORTFOLIO_SIGNALS = gql`
  query GetPortfolioSignals($threshold: Float) {
    portfolioSignals(threshold: $threshold) {
      portfolioSignals
      strongBuyCount
      strongSellCount
      overallSentiment
      totalPositions
    }
  }
`;

type RouteParams = {
  symbol?: string;
  mode?: 'single' | 'portfolio';
};

export default function SignalUpdatesScreen() {
  const route = useRoute();
  const navigation = useNavigation();
  const { symbol, mode = 'single' } = (route.params as RouteParams) || {};
  const [refreshing, setRefreshing] = useState(false);

  const { data: signalData, loading: signalLoading, error: signalError, refetch: refetchSignal } = useQuery(
    GET_SIGNAL_UPDATES,
    {
      variables: { symbol, lookbackHours: 24 },
      skip: !symbol || mode === 'portfolio',
      fetchPolicy: 'cache-and-network',
      errorPolicy: 'all', // Continue even if there are errors
      notifyOnNetworkStatusChange: false,
    }
  );

  const { data: portfolioData, loading: portfolioLoading, refetch: refetchPortfolio } = useQuery(
    GET_PORTFOLIO_SIGNALS,
    {
      variables: { threshold: 60.0 },
      skip: mode !== 'portfolio',
      fetchPolicy: 'cache-and-network',
    }
  );

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    if (mode === 'portfolio') {
      refetchPortfolio().finally(() => setRefreshing(false));
    } else {
      refetchSignal().finally(() => setRefreshing(false));
    }
  }, [mode, refetchPortfolio, refetchSignal]);

  const loading = mode === 'portfolio' ? portfolioLoading : signalLoading;

  const getScoreColor = (score: number | undefined | null) => {
    const safeScore = score ?? 50.0;
    if (safeScore >= 70) return '#10B981';
    if (safeScore >= 50) return '#F59E0B';
    return '#EF4444';
  };

  const getRecommendationColor = (rec: string) => {
    if (rec === 'BUY') return '#10B981';
    if (rec === 'SELL') return '#EF4444';
    return '#6B7280';
  };

  const getSeverityColor = (severity: string) => {
    if (severity === 'high') return '#EF4444';
    if (severity === 'medium') return '#F59E0B';
    return '#6B7280';
  };

  // Show loading only for initial load, not on refresh
  if (loading && !signalData && !portfolioData && !refreshing) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading signals...</Text>
      </View>
    );
  }

  // Show error state with fallback data
  if (signalError && !signalData && mode !== 'portfolio') {
    return (
      <View style={styles.container}>
        <View style={styles.errorCard}>
          <Ionicons name="alert-circle" size={24} color="#EF4444" />
          <Text style={styles.errorText}>
            Unable to load real-time signals. Showing default analysis.
          </Text>
        </View>
        {/* Show fallback data */}
        <View style={styles.fusionCard}>
          <Text style={styles.fusionTitle}>Multi-Signal Fusion Score</Text>
          <View style={styles.fusionScoreContainer}>
            <Text style={[styles.fusionScore, { color: '#6B7280' }]}>50.0</Text>
            <Text style={styles.fusionScoreLabel}>/ 100</Text>
          </View>
          <View style={[styles.recommendationBadge, { backgroundColor: '#6B7280' }]}>
            <Text style={styles.recommendationText}>HOLD</Text>
          </View>
          <Text style={styles.fallbackText}>
            Signal data temporarily unavailable. Please try again later.
          </Text>
        </View>
      </View>
    );
  }

  if (mode === 'portfolio') {
    const portfolioSignals = portfolioData?.portfolioSignals;
    const signals = portfolioSignals?.portfolioSignals
      ? portfolioSignals.portfolioSignals.map((s: string) => JSON.parse(s))
      : [];

    return (
      <ScrollView
        style={styles.container}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {/* Portfolio Summary */}
        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>Portfolio Signals</Text>
          <View style={styles.summaryStats}>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{portfolioSignals?.strongBuyCount || 0}</Text>
              <Text style={styles.statLabel}>Strong Buys</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={[styles.statValue, { color: '#EF4444' }]}>
                {portfolioSignals?.strongSellCount || 0}
              </Text>
              <Text style={styles.statLabel}>Strong Sells</Text>
            </View>
            <View style={styles.statItem}>
              <Text
                style={[
                  styles.statValue,
                  {
                    color:
                      portfolioSignals?.overallSentiment === 'bullish'
                        ? '#10B981'
                        : portfolioSignals?.overallSentiment === 'bearish'
                        ? '#EF4444'
                        : '#6B7280',
                  },
                ]}
              >
                {portfolioSignals?.overallSentiment || 'neutral'}
              </Text>
              <Text style={styles.statLabel}>Sentiment</Text>
            </View>
          </View>
        </View>

        {/* Individual Signals */}
        {signals.map((signal: any, idx: number) => (
          <View key={idx} style={styles.signalCard}>
            <View style={styles.signalHeader}>
              <Text style={styles.signalSymbol}>{signal.symbol}</Text>
              <View
                style={[
                  styles.scoreBadge,
                  { backgroundColor: getScoreColor(signal.fusionScore ?? 50.0) },
                ]}
              >
                <Text style={styles.scoreText}>
                  {(signal.fusionScore ?? 50.0).toFixed(1)}
                </Text>
              </View>
            </View>
            <View style={styles.signalBody}>
              <View
                style={[
                  styles.recommendationBadge,
                  { backgroundColor: getRecommendationColor(signal.recommendation) },
                ]}
              >
                <Text style={styles.recommendationText}>{signal.recommendation}</Text>
              </View>
              {signal.alerts && signal.alerts.length > 0 && (
                <View style={styles.alertsContainer}>
                  {signal.alerts.map((alert: any, alertIdx: number) => (
                    <View key={alertIdx} style={styles.alertItem}>
                      <View
                        style={[
                          styles.alertDot,
                          { backgroundColor: getSeverityColor(alert.severity) },
                        ]}
                      />
                      <Text style={styles.alertText}>{alert.message}</Text>
                    </View>
                  ))}
                </View>
              )}
            </View>
          </View>
        ))}
      </ScrollView>
    );
  }

  // Single stock signal view
  // Gracefully handle null/undefined signalUpdates
  const signal = signalData?.signalUpdates ?? null;

  if (!signal) {
    return (
      <ScrollView
        style={styles.container}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        <View style={styles.emptyContainer}>
          <Ionicons name="pulse-outline" size={48} color="#6B7280" />
          <Text style={styles.emptyText}>
            No AI signal updates yet. We'll notify you when something changes.
          </Text>
          <Text style={styles.emptySubtext}>
            Signal data temporarily unavailable. Please try again later.
          </Text>
        </View>
      </ScrollView>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* Fusion Score */}
      <View style={styles.fusionCard}>
        <Text style={styles.fusionTitle}>Multi-Signal Fusion Score</Text>
        <View style={styles.fusionScoreContainer}>
          <Text style={[styles.fusionScore, { color: getScoreColor(signal.fusionScore ?? 50.0) }]}>
            {(signal.fusionScore ?? 50.0).toFixed(1)}
          </Text>
          <Text style={styles.fusionScoreLabel}>/ 100</Text>
        </View>
        <View
          style={[
            styles.recommendationBadge,
            { backgroundColor: getRecommendationColor(signal.recommendation) },
          ]}
        >
          <Text style={styles.recommendationText}>{signal.recommendation}</Text>
        </View>
      </View>

      {/* Individual Signals */}
      {signal.signals && (() => {
        // Parse signals if it's a JSON string
        let signalsData: any = {};
        try {
          if (typeof signal.signals === 'string') {
            signalsData = JSON.parse(signal.signals);
          } else {
            signalsData = signal.signals;
          }
        } catch (e) {
          console.warn('Error parsing signals:', e);
          signalsData = {};
        }
        
        if (!signalsData || Object.keys(signalsData).length === 0) {
          return null;
        }
        
        return (
          <View style={styles.signalsSection}>
            <Text style={styles.sectionTitle}>Signal Breakdown</Text>
            {Object.entries(signalsData).map(([key, value]: [string, any]) => (
              <View key={key} style={styles.signalItem}>
                <View style={styles.signalItemHeader}>
                  <Text style={styles.signalItemName}>{key.toUpperCase()}</Text>
                  <Text style={[styles.signalItemScore, { color: getScoreColor(value?.score ?? 50.0) }]}>
                    {(value?.score ?? 50.0).toFixed(1)}
                  </Text>
                </View>
                <View style={styles.signalItemDetails}>
                  <Text style={styles.signalItemTrend}>Trend: {value?.trend ?? 'stable'}</Text>
                  <Text style={styles.signalItemStrength}>Strength: {value?.strength ?? 'moderate'}</Text>
                </View>
              </View>
            ))}
          </View>
        );
      })()}

      {/* Alerts */}
      {signal.alerts && signal.alerts.length > 0 && (
        <View style={styles.alertsSection}>
          <Text style={styles.sectionTitle}>Alerts</Text>
          {signal.alerts.map((alert: any, idx: number) => (
            <View key={idx} style={styles.alertCard}>
              <View style={styles.alertHeader}>
                <View
                  style={[
                    styles.alertDot,
                    { backgroundColor: getSeverityColor(alert.severity) },
                  ]}
                />
                <Text style={styles.alertType}>{alert.type}</Text>
                <Text style={styles.alertSeverity}>{alert.severity}</Text>
              </View>
              <Text style={styles.alertMessage}>{alert.message}</Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6B7280',
  },
  errorCard: {
    backgroundColor: '#FEF2F2',
    padding: 16,
    margin: 16,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#FEE2E2',
  },
  errorText: {
    flex: 1,
    marginLeft: 12,
    fontSize: 14,
    color: '#DC2626',
  },
  fallbackText: {
    marginTop: 12,
    fontSize: 12,
    color: '#9CA3AF',
    textAlign: 'center',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 16,
    color: '#9CA3AF',
  },
  summaryCard: {
    backgroundColor: '#FFFFFF',
    padding: 20,
    margin: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  summaryTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 16,
  },
  summaryStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#10B981',
  },
  statLabel: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  signalCard: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    marginHorizontal: 16,
    marginTop: 12,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  signalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  signalSymbol: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
  },
  scoreBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  scoreText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: 'bold',
  },
  signalBody: {
    marginTop: 8,
  },
  recommendationBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    marginBottom: 8,
  },
  recommendationText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  alertsContainer: {
    marginTop: 8,
  },
  alertItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  alertDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  alertText: {
    fontSize: 14,
    color: '#374151',
    flex: 1,
  },
  fusionCard: {
    backgroundColor: '#FFFFFF',
    padding: 24,
    margin: 16,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  fusionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 16,
  },
  fusionScoreContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 16,
  },
  fusionScore: {
    fontSize: 48,
    fontWeight: 'bold',
  },
  fusionScoreLabel: {
    fontSize: 24,
    color: '#9CA3AF',
    marginLeft: 4,
  },
  signalsSection: {
    backgroundColor: '#FFFFFF',
    padding: 20,
    margin: 16,
    marginTop: 0,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 16,
  },
  signalItem: {
    padding: 16,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    marginBottom: 12,
  },
  signalItemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  signalItemName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  signalItemScore: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  signalItemDetails: {
    flexDirection: 'row',
    marginTop: 4,
  },
  signalItemTrend: {
    fontSize: 14,
    color: '#6B7280',
    marginRight: 16,
  },
  signalItemStrength: {
    fontSize: 14,
    color: '#6B7280',
  },
  alertsSection: {
    backgroundColor: '#FFFFFF',
    padding: 20,
    margin: 16,
    marginTop: 0,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  alertCard: {
    padding: 16,
    backgroundColor: '#FEF2F2',
    borderRadius: 8,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#EF4444',
  },
  alertHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  alertType: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
    marginLeft: 8,
    flex: 1,
  },
  alertSeverity: {
    fontSize: 12,
    color: '#6B7280',
    textTransform: 'uppercase',
  },
  alertMessage: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
  },
});

