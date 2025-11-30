import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { useQuery } from '@apollo/client';
import { GET_IV_SURFACE_FORECAST } from '../../graphql/optionsQueries';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

const { width } = Dimensions.get('window');

interface IVChangePoint {
  strike: number;
  expiration: string;
  currentIv: number;
  predictedIv1hr: number;
  predictedIv24hr: number;
  ivChange1hrPct: number;
  ivChange24hrPct: number;
  confidence: number;
}

interface IVSurfaceForecast {
  symbol: string;
  currentIv: string;  // JSON string
  predictedIv1hr: string;  // JSON string
  predictedIv24hr: string;  // JSON string
  confidence: number;
  regime: string;
  ivChangeHeatmap: IVChangePoint[];
  timestamp: string;
}

interface IVSurfaceForecastProps {
  symbol: string;
}

export const IVSurfaceForecast: React.FC<IVSurfaceForecastProps> = ({ symbol }) => {
  const [timeHorizon, setTimeHorizon] = useState<'1hr' | '24hr'>('1hr');

  const { data, loading, error, refetch } = useQuery(GET_IV_SURFACE_FORECAST, {
    variables: { symbol },
    pollInterval: 120000, // Update every 2 minutes (reduced to avoid rate limits)
    fetchPolicy: 'cache-and-network',
  });

  if (loading && !data) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Forecasting IV surface...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <Icon name="alert-circle" size={24} color="#ef4444" />
        <Text style={styles.errorText}>Failed to load IV forecast</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const forecast: IVSurfaceForecast | undefined = data?.ivSurfaceForecast;

  if (!forecast || !forecast.ivChangeHeatmap || forecast.ivChangeHeatmap.length === 0) {
    return (
      <View style={styles.container}>
        <Text style={styles.emptyText}>No IV forecast available</Text>
      </View>
    );
  }

  // Get IV change based on time horizon
  const getIVChange = (point: IVChangePoint): number => {
    return timeHorizon === '1hr' ? point.ivChange1hrPct : point.ivChange24hrPct;
  };

  const getPredictedIV = (point: IVChangePoint): number => {
    return timeHorizon === '1hr' ? point.predictedIv1hr : point.predictedIv24hr;
  };

  // Get color based on IV change
  const getIVChangeColor = (change: number): string => {
    if (change > 10) return '#EF4444'; // Red - IV expanding significantly
    if (change > 5) return '#F59E0B';  // Orange - IV expanding
    if (change > 0) return '#FCD34D';  // Yellow - IV slightly expanding
    if (change > -5) return '#6EE7B7'; // Light green - IV slightly contracting
    if (change > -10) return '#34D399'; // Green - IV contracting
    return '#10B981'; // Dark green - IV crushing
  };

  // Group by expiration
  const byExpiration: Record<string, IVChangePoint[]> = {};
  forecast.ivChangeHeatmap.forEach(point => {
    if (!byExpiration[point.expiration]) {
      byExpiration[point.expiration] = [];
    }
    byExpiration[point.expiration].push(point);
  });

  const expirations = Object.keys(byExpiration).sort();

  // Calculate min/max for color scaling
  const allChanges = forecast.ivChangeHeatmap.map(p => getIVChange(p));
  const minChange = Math.min(...allChanges);
  const maxChange = Math.max(...allChanges);
  const range = maxChange - minChange || 1;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>IV Surface Forecast</Text>
          <Text style={styles.subtitle}>
            Predicts IV changes {timeHorizon === '1hr' ? '1 hour' : '24 hours'} ahead
          </Text>
        </View>
        <View style={styles.regimeBadge}>
          <Text style={styles.regimeText}>{forecast.regime.toUpperCase()}</Text>
        </View>
      </View>

      {/* Time Horizon Selector */}
      <View style={styles.timeHorizonSelector}>
        {(['1hr', '24hr'] as const).map(horizon => (
          <TouchableOpacity
            key={horizon}
            style={[
              styles.timeButton,
              timeHorizon === horizon && styles.timeButtonActive,
            ]}
            onPress={() => setTimeHorizon(horizon)}
          >
            <Text
              style={[
                styles.timeButtonText,
                timeHorizon === horizon && styles.timeButtonTextActive,
              ]}
            >
              {horizon === '1hr' ? '1 Hour' : '24 Hours'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Confidence & Regime Info */}
      <View style={styles.infoRow}>
        <View style={styles.infoItem}>
          <Text style={styles.infoLabel}>Confidence</Text>
          <Text style={styles.infoValue}>{forecast.confidence.toFixed(0)}%</Text>
        </View>
        <View style={styles.infoItem}>
          <Text style={styles.infoLabel}>Regime</Text>
          <Text style={styles.infoValue}>{forecast.regime}</Text>
        </View>
      </View>

      {/* Heatmap by Expiration */}
      <ScrollView style={styles.heatmapContainer} horizontal showsHorizontalScrollIndicator={false}>
        {expirations.map(expiration => {
          const points = byExpiration[expiration].sort((a, b) => a.strike - b.strike);
          
          return (
            <View key={expiration} style={styles.expirationColumn}>
              <Text style={styles.expirationHeader}>{expiration}</Text>
              {points.map((point, index) => {
                const ivChange = getIVChange(point);
                const color = getIVChangeColor(ivChange);
                const intensity = Math.abs(ivChange) / Math.max(Math.abs(maxChange), Math.abs(minChange), 1);
                
                return (
                  <TouchableOpacity
                    key={`${point.strike}-${index}`}
                    style={[
                      styles.heatmapCell,
                      {
                        backgroundColor: color,
                        opacity: 0.6 + (intensity * 0.4), // More intense for larger changes
                      },
                    ]}
                  >
                    <Text style={styles.heatmapStrike}>${point.strike.toFixed(0)}</Text>
                    <Text style={styles.heatmapChange}>
                      {ivChange > 0 ? '+' : ''}
                      {ivChange.toFixed(1)}%
                    </Text>
                    <Text style={styles.heatmapIV}>
                      {getPredictedIV(point).toFixed(2)}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          );
        })}
      </ScrollView>

      {/* Legend */}
      <View style={styles.legend}>
        <Text style={styles.legendTitle}>IV Change</Text>
        <View style={styles.legendItems}>
          <View style={styles.legendItem}>
            <View style={[styles.legendColor, { backgroundColor: '#EF4444' }]} />
            <Text style={styles.legendText}>+10%+ (Expanding)</Text>
          </View>
          <View style={styles.legendItem}>
            <View style={[styles.legendColor, { backgroundColor: '#FCD34D' }]} />
            <Text style={styles.legendText}>0-5% (Slight)</Text>
          </View>
          <View style={styles.legendItem}>
            <View style={[styles.legendColor, { backgroundColor: '#10B981' }]} />
            <Text style={styles.legendText}>-10%- (Crushing)</Text>
          </View>
        </View>
      </View>

      {/* Key Insights */}
      <View style={styles.insightsContainer}>
        <Text style={styles.insightsTitle}>Key Insights</Text>
        {forecast.regime === 'earnings' && (
          <View style={styles.insightItem}>
            <Icon name="alert-circle" size={16} color="#F59E0B" />
            <Text style={styles.insightText}>
              Earnings detected: IV likely to expand before, crush after
            </Text>
          </View>
        )}
        {forecast.regime === 'fomc' && (
          <View style={styles.insightItem}>
            <Icon name="alert-circle" size={16} color="#3B82F6" />
            <Text style={styles.insightText}>
              FOMC meeting: Expect IV expansion around announcement
            </Text>
          </View>
        )}
        {forecast.confidence > 80 && (
          <View style={styles.insightItem}>
            <Icon name="check-circle" size={16} color="#10B981" />
            <Text style={styles.insightText}>
              High confidence forecast ({forecast.confidence.toFixed(0)}%)
            </Text>
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginVertical: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    color: '#111827',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
  },
  regimeBadge: {
    backgroundColor: '#3B82F6',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 12,
  },
  regimeText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  loadingText: {
    marginTop: 8,
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
  },
  errorText: {
    marginTop: 8,
    fontSize: 14,
    color: '#EF4444',
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 12,
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#007AFF',
    borderRadius: 8,
    alignSelf: 'center',
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  emptyText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 32,
  },
  timeHorizonSelector: {
    flexDirection: 'row',
    marginBottom: 16,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    padding: 4,
  },
  timeButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 6,
  },
  timeButtonActive: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  timeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
  timeButtonTextActive: {
    color: '#007AFF',
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 20,
    paddingVertical: 12,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
  },
  infoItem: {
    alignItems: 'center',
  },
  infoLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  infoValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  heatmapContainer: {
    marginBottom: 20,
  },
  expirationColumn: {
    marginRight: 12,
    minWidth: 100,
  },
  expirationHeader: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
    textAlign: 'center',
  },
  heatmapCell: {
    padding: 8,
    marginBottom: 4,
    borderRadius: 6,
    alignItems: 'center',
    minHeight: 70,
    justifyContent: 'center',
  },
  heatmapStrike: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 2,
  },
  heatmapChange: {
    fontSize: 11,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 2,
  },
  heatmapIV: {
    fontSize: 10,
    color: '#FFFFFF',
    opacity: 0.9,
  },
  legend: {
    marginBottom: 16,
    padding: 12,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
  },
  legendTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  legendItems: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  legendColor: {
    width: 16,
    height: 16,
    borderRadius: 4,
    marginRight: 6,
  },
  legendText: {
    fontSize: 11,
    color: '#6B7280',
  },
  insightsContainer: {
    padding: 12,
    backgroundColor: '#F0F7FF',
    borderRadius: 8,
  },
  insightsTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  insightItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  insightText: {
    flex: 1,
    marginLeft: 8,
    fontSize: 12,
    color: '#374151',
    lineHeight: 18,
  },
});

