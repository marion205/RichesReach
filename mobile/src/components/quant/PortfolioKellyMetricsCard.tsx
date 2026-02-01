/**
 * Portfolio Kelly Metrics Card
 * Displays aggregate Kelly Criterion metrics across all portfolio positions
 */
import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { useQuery, gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const PORTFOLIO_KELLY_METRICS_QUERY = gql`
  query PortfolioKellyMetrics {
    portfolioKellyMetrics {
      totalPortfolioValue
      aggregateKellyFraction
      aggregateRecommendedFraction
      portfolioMaxDrawdownRisk
      weightedWinRate
      positionCount
      totalPositions
    }
  }
`;

interface PortfolioKellyMetricsCardProps {
  style?: any;
}

export default function PortfolioKellyMetricsCard({ style }: PortfolioKellyMetricsCardProps) {
  const { data, loading, error } = useQuery(PORTFOLIO_KELLY_METRICS_QUERY, {
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  // Log errors for debugging
  if (error) {
    console.error('[PortfolioKellyMetricsCard] GraphQL Error:', error);
    if (error.graphQLErrors) {
      error.graphQLErrors.forEach((err, idx) => {
        console.error(`[PortfolioKellyMetricsCard] GraphQL Error ${idx}:`, err.message, err);
      });
    }
    if (error.networkError) {
      console.error('[PortfolioKellyMetricsCard] Network Error:', error.networkError);
    }
  }

  const metrics = data?.portfolioKellyMetrics;

  if (loading) {
    return (
      <View style={[styles.container, style]}>
        <View style={styles.header}>
          <Icon name="trending-up" size={20} color="#1D4ED8" />
          <Text style={styles.title}>Portfolio Risk Metrics</Text>
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color="#1D4ED8" />
          <Text style={styles.loadingText}>Calculating metrics...</Text>
        </View>
      </View>
    );
  }

  if (error || !metrics) {
    return (
      <View style={[styles.container, style]}>
        <View style={styles.header}>
          <Icon name="trending-up" size={20} color="#1D4ED8" />
          <Text style={styles.title}>Portfolio Risk Metrics</Text>
        </View>
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={16} color="#EF4444" />
          <Text style={styles.errorText}>Unable to load metrics</Text>
        </View>
      </View>
    );
  }

  const hasData = metrics.positionCount > 0;
  const hasPositions = (metrics.totalPositions || 0) > 0;
  const portfolioValue = metrics.totalPortfolioValue || 0;
  const kellyOptimal = (metrics.aggregateKellyFraction || 0) * 100;
  const kellyRecommended = (metrics.aggregateRecommendedFraction || 0) * 100;
  const maxDrawdown = (metrics.portfolioMaxDrawdownRisk || 0) * 100;
  const winRate = (metrics.weightedWinRate || 0) * 100;

  return (
    <View style={[styles.container, style]}>
      <View style={styles.header}>
        <Icon name="trending-up" size={20} color="#1D4ED8" />
        <Text style={styles.title}>Portfolio Risk Metrics</Text>
        {hasData && (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>
              {metrics.positionCount}/{metrics.totalPositions}
            </Text>
          </View>
        )}
      </View>

      {!hasData ? (
        <View style={styles.emptyContainer}>
          <Icon name="bar-chart-2" size={32} color="#9CA3AF" />
          <Text style={styles.emptyText}>
            {hasPositions 
              ? "Calculating metrics..." 
              : "No position data available"}
          </Text>
          <Text style={styles.emptySubtext}>
            {hasPositions
              ? `Processing ${metrics.totalPositions} position${metrics.totalPositions !== 1 ? 's' : ''}...`
              : "Add positions to see portfolio-level risk metrics"}
          </Text>
        </View>
      ) : (
        <View style={styles.content}>
          {/* Portfolio Value */}
          <View style={styles.metricRow}>
            <Text style={styles.metricLabel}>Portfolio Value</Text>
            <Text style={styles.metricValue}>
              ${portfolioValue.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </Text>
          </View>

          {/* Kelly Metrics */}
          <View style={styles.kellySection}>
            <View style={styles.kellyRow}>
              <View style={styles.kellyItem}>
                <Text style={styles.kellyLabel}>KELLY OPTIMAL</Text>
                <Text style={styles.kellyValue}>{kellyOptimal.toFixed(2)}%</Text>
              </View>
              <View style={styles.kellyItem}>
                <Text style={styles.kellyLabel}>RECOMMENDED</Text>
                <Text style={styles.kellyValue}>{kellyRecommended.toFixed(2)}%</Text>
              </View>
            </View>
          </View>

          {/* Risk Metrics */}
          <View style={styles.riskSection}>
            <View style={styles.riskRow}>
              <View style={styles.riskItem}>
                <Icon name="alert-triangle" size={16} color="#F59E0B" />
                <View style={styles.riskItemContent}>
                  <Text style={styles.riskLabel}>Max Drawdown</Text>
                  <Text style={styles.riskValue}>{maxDrawdown.toFixed(2)}%</Text>
                </View>
              </View>
              <View style={styles.riskItem}>
                <Icon name="target" size={16} color="#10B981" />
                <View style={styles.riskItemContent}>
                  <Text style={styles.riskLabel}>Win Rate</Text>
                  <Text style={styles.riskValue}>{winRate.toFixed(1)}%</Text>
                </View>
              </View>
            </View>
          </View>

          {/* Info Footer */}
          <View style={styles.footer}>
            <Icon name="info" size={12} color="#6B7280" />
            <Text style={styles.footerText}>
              Weighted averages across {metrics.positionCount} positions
            </Text>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    flex: 1,
  },
  badge: {
    backgroundColor: '#EFF6FF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1D4ED8',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 24,
    gap: 8,
  },
  loadingText: {
    fontSize: 14,
    color: '#6B7280',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 24,
    gap: 8,
  },
  errorText: {
    fontSize: 14,
    color: '#EF4444',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginTop: 12,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
    textAlign: 'center',
  },
  content: {
    gap: 16,
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  metricLabel: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  metricValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  kellySection: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
  },
  kellyRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    gap: 16,
  },
  kellyItem: {
    flex: 1,
    alignItems: 'center',
  },
  kellyLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#6B7280',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  kellyValue: {
    fontSize: 24,
    fontWeight: '800',
    color: '#1D4ED8',
  },
  riskSection: {
    marginTop: 8,
  },
  riskRow: {
    flexDirection: 'row',
    gap: 16,
  },
  riskItem: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  riskItemContent: {
    flex: 1,
  },
  riskLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  riskValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 8,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  footerText: {
    fontSize: 11,
    color: '#6B7280',
  },
});

