import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useQuery } from '@apollo/client';
import { GET_EDGE_PREDICTIONS } from '../../graphql/optionsQueries';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

interface EdgePrediction {
  strike: number;
  expiration: string;
  optionType: string;
  currentEdge: number;
  predictedEdge15min: number;
  predictedEdge1hr: number;
  predictedEdge1day: number;
  confidence: number;
  explanation: string;
  edgeChangeDollars: number;
  currentPremium: number;
  predictedPremium15min: number;
  predictedPremium1hr: number;
}

interface EdgePredictorHeatmapProps {
  symbol: string;
}

export const EdgePredictorHeatmap: React.FC<EdgePredictorHeatmapProps> = ({ symbol }) => {
  const [timeHorizon, setTimeHorizon] = useState<'15min' | '1hr' | '1day'>('1hr');
  const [selectedExpiration, setSelectedExpiration] = useState<string | null>(null);

  const { data, loading, error, refetch } = useQuery(GET_EDGE_PREDICTIONS, {
    variables: { symbol },
    pollInterval: 60000, // Update every 60 seconds (reduced to avoid rate limits)
    fetchPolicy: 'cache-and-network',
  });

  if (loading && !data) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Analyzing edge predictions...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <Icon name="alert-circle" size={24} color="#ef4444" />
        <Text style={styles.errorText}>Failed to load edge predictions</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const predictions: EdgePrediction[] = data?.edgePredictions || [];

  if (predictions.length === 0) {
    return (
      <View style={styles.container}>
        <Text style={styles.emptyText}>No edge predictions available</Text>
      </View>
    );
  }

  // Group by expiration
  const byExpiration: Record<string, EdgePrediction[]> = {};
  predictions.forEach(pred => {
    if (!byExpiration[pred.expiration]) {
      byExpiration[pred.expiration] = [];
    }
    byExpiration[pred.expiration].push(pred);
  });

  const expirations = Object.keys(byExpiration).sort();

  // Get selected predictions
  const selectedPredictions = selectedExpiration
    ? byExpiration[selectedExpiration] || []
    : predictions;

  // Get edge value based on time horizon
  const getEdgeValue = (pred: EdgePrediction): number => {
    switch (timeHorizon) {
      case '15min':
        return pred.predictedEdge15min;
      case '1hr':
        return pred.predictedEdge1hr;
      case '1day':
        return pred.predictedEdge1day;
      default:
        return pred.predictedEdge1hr;
    }
  };

  // Get color based on edge value
  const getEdgeColor = (edge: number): string => {
    if (edge > 10) return '#10B981'; // Green - high positive edge
    if (edge > 5) return '#34D399'; // Light green
    if (edge > 0) return '#6EE7B7'; // Very light green
    if (edge > -5) return '#FCD34D'; // Yellow
    if (edge > -10) return '#F59E0B'; // Orange
    return '#EF4444'; // Red - negative edge
  };

  // Sort by edge value (highest first)
  const sortedPredictions = [...selectedPredictions].sort(
    (a, b) => getEdgeValue(b) - getEdgeValue(a)
  );

  // Top 20 predictions
  const topPredictions = sortedPredictions.slice(0, 20);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Edge Predictor</Text>
        <Text style={styles.subtitle}>Expected edge changes in next hour</Text>
      </View>

      {/* Time Horizon Selector */}
      <View style={styles.timeHorizonSelector}>
        {(['15min', '1hr', '1day'] as const).map(horizon => (
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
              {horizon === '15min' ? '15m' : horizon === '1hr' ? '1h' : '1d'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Expiration Filter */}
      {expirations.length > 1 && (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.expirationFilter}
        >
          <TouchableOpacity
            style={[
              styles.expirationButton,
              !selectedExpiration && styles.expirationButtonActive,
            ]}
            onPress={() => setSelectedExpiration(null)}
          >
            <Text
              style={[
                styles.expirationButtonText,
                !selectedExpiration && styles.expirationButtonTextActive,
              ]}
            >
              All
            </Text>
          </TouchableOpacity>
          {expirations.map(exp => (
            <TouchableOpacity
              key={exp}
              style={[
                styles.expirationButton,
                selectedExpiration === exp && styles.expirationButtonActive,
              ]}
              onPress={() => setSelectedExpiration(exp)}
            >
              <Text
                style={[
                  styles.expirationButtonText,
                  selectedExpiration === exp && styles.expirationButtonTextActive,
                ]}
              >
                {exp}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}

      {/* Predictions List */}
      <ScrollView style={styles.predictionsList}>
        {topPredictions.map((pred, index) => {
          const edgeValue = getEdgeValue(pred);
          const edgeColor = getEdgeColor(edgeValue);

          return (
            <View key={`${pred.strike}-${pred.expiration}-${pred.optionType}`} style={styles.predictionCard}>
              <View style={styles.predictionHeader}>
                <View style={styles.predictionInfo}>
                  <Text style={styles.predictionStrike}>
                    ${pred.strike.toFixed(2)} {pred.optionType.toUpperCase()}
                  </Text>
                  <Text style={styles.predictionExpiration}>{pred.expiration}</Text>
                </View>
                <View
                  style={[
                    styles.edgeBadge,
                    { backgroundColor: edgeColor },
                  ]}
                >
                  <Text style={styles.edgeBadgeText}>
                    {edgeValue > 0 ? '+' : ''}
                    {edgeValue.toFixed(1)}%
                  </Text>
                </View>
              </View>

              <View style={styles.predictionDetails}>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Confidence:</Text>
                  <Text style={styles.detailValue}>{pred.confidence.toFixed(0)}%</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Expected $ Change:</Text>
                  <Text
                    style={[
                      styles.detailValue,
                      pred.edgeChangeDollars > 0 ? styles.positiveValue : styles.negativeValue,
                    ]}
                  >
                    {pred.edgeChangeDollars > 0 ? '+' : ''}
                    ${pred.edgeChangeDollars.toFixed(2)}
                  </Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Current Premium:</Text>
                  <Text style={styles.detailValue}>${pred.currentPremium.toFixed(2)}</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Predicted Premium:</Text>
                  <Text style={styles.detailValue}>
                    ${(timeHorizon === '15min' 
                      ? pred.predictedPremium15min 
                      : pred.predictedPremium1hr).toFixed(2)}
                  </Text>
                </View>
              </View>

              {pred.explanation && (
                <View style={styles.explanationContainer}>
                  <Icon name="information" size={16} color="#6B7280" />
                  <Text style={styles.explanationText}>{pred.explanation}</Text>
                </View>
              )}
            </View>
          );
        })}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    padding: 16,
  },
  header: {
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
    paddingVertical: 8,
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
  expirationFilter: {
    marginBottom: 16,
  },
  expirationButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    marginRight: 8,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
  },
  expirationButtonActive: {
    backgroundColor: '#007AFF',
  },
  expirationButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
  expirationButtonTextActive: {
    color: '#FFFFFF',
  },
  predictionsList: {
    flex: 1,
  },
  predictionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  predictionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  predictionInfo: {
    flex: 1,
  },
  predictionStrike: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  predictionExpiration: {
    fontSize: 12,
    color: '#6B7280',
  },
  edgeBadge: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
  },
  edgeBadgeText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  predictionDetails: {
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  detailLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  positiveValue: {
    color: '#10B981',
  },
  negativeValue: {
    color: '#EF4444',
  },
  explanationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  explanationText: {
    flex: 1,
    marginLeft: 8,
    fontSize: 12,
    color: '#6B7280',
    fontStyle: 'italic',
  },
});

