import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
  Alert,
} from 'react-native';
import { useQuery } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import { GET_CRYPTO_RECOMMENDATIONS } from '../../graphql/cryptoQueries';

interface CryptoRecommendation {
  symbol: string;
  score: number;
  probability: number;
  confidenceLevel: string;
  priceUsd: number;
  volatilityTier: string;
  liquidity24hUsd: number;
  rationale: string;
}

interface CryptoRecommendationsCardProps {
  onRecommendationPress?: (symbol: string) => void;
  maxRecommendations?: number;
}

const CryptoRecommendationsCard: React.FC<CryptoRecommendationsCardProps> = ({
  onRecommendationPress,
  maxRecommendations = 5,
}) => {
  const [refreshing, setRefreshing] = useState(false);

  const { data, loading, error, refetch } = useQuery(GET_CRYPTO_RECOMMENDATIONS, {
    variables: {
      constraints: {
        maxSymbols: maxRecommendations,
        minProbability: 0.55,
        minLiquidityUsd24h: 5000000,
        allowedTiers: ['LOW', 'MEDIUM', 'HIGH'],
        excludeSymbols: [],
      },
    },
    pollInterval: 300000, // 5 minutes
  });

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refetch();
    } catch (error) {
      console.error('Error refreshing recommendations:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleRecommendationPress = (symbol: string) => {
    if (onRecommendationPress) {
      onRecommendationPress(symbol);
    } else {
      Alert.alert('Recommendation', `View details for ${symbol}`);
    }
  };

  const getConfidenceColor = (level: string) => {
    switch (level.toUpperCase()) {
      case 'HIGH': return '#10B981';
      case 'MEDIUM': return '#F59E0B';
      case 'LOW': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const getVolatilityColor = (tier: string) => {
    switch (tier.toUpperCase()) {
      case 'LOW': return '#10B981';
      case 'MEDIUM': return '#F59E0B';
      case 'HIGH': return '#EF4444';
      case 'EXTREME': return '#DC2626';
      default: return '#6B7280';
    }
  };

  const formatLiquidity = (liquidity: number) => {
    if (liquidity >= 1000000000) {
      return `$${(liquidity / 1000000000).toFixed(1)}B`;
    } else if (liquidity >= 1000000) {
      return `$${(liquidity / 1000000).toFixed(1)}M`;
    } else if (liquidity >= 1000) {
      return `$${(liquidity / 1000).toFixed(1)}K`;
    }
    return `$${liquidity.toFixed(0)}`;
  };

  if (loading && !data) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>AI Coin Recommendations</Text>
          <ActivityIndicator size="small" color="#007AFF" />
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Analyzing market opportunities...</Text>
        </View>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>AI Coin Recommendations</Text>
          <TouchableOpacity onPress={handleRefresh} style={styles.refreshButton}>
            <Icon name="refresh-cw" size={20} color="#007AFF" />
          </TouchableOpacity>
        </View>
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={48} color="#EF4444" />
          <Text style={styles.errorTitle}>Failed to Load Recommendations</Text>
          <Text style={styles.errorText}>
            {error.message || 'Unable to fetch AI recommendations. Please try again.'}
          </Text>
          <TouchableOpacity onPress={handleRefresh} style={styles.retryButton}>
            <Icon name="refresh-cw" size={16} color="#007AFF" />
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  const recommendations = data?.cryptoRecommendations?.recommendations || [];

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>AI Coin Recommendations</Text>
        <TouchableOpacity 
          onPress={handleRefresh} 
          style={styles.refreshButton}
          disabled={refreshing}
        >
          <Icon 
            name={refreshing ? "loader" : "refresh-cw"} 
            size={20} 
            color="#007AFF" 
            style={refreshing ? styles.spinning : undefined}
          />
        </TouchableOpacity>
      </View>

      {recommendations.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Icon name="trending-up" size={48} color="#6B7280" />
          <Text style={styles.emptyTitle}>No Recommendations Available</Text>
          <Text style={styles.emptyText}>
            {data?.cryptoRecommendations?.message || 'No coins meet the current criteria for recommendations.'}
          </Text>
        </View>
      ) : (
        <ScrollView 
          style={styles.recommendationsList}
          showsVerticalScrollIndicator={false}
        >
          {recommendations.map((rec: CryptoRecommendation, index: number) => (
            <TouchableOpacity
              key={`${rec.symbol}-${index}`}
              style={styles.recommendationCard}
              onPress={() => handleRecommendationPress(rec.symbol)}
            >
              <View style={styles.recommendationHeader}>
                <View style={styles.symbolContainer}>
                  <Text style={styles.symbol}>{rec.symbol}</Text>
                  <View style={[
                    styles.volatilityBadge,
                    { backgroundColor: getVolatilityColor(rec.volatilityTier) }
                  ]}>
                    <Text style={styles.volatilityText}>{rec.volatilityTier}</Text>
                  </View>
                </View>
                <View style={styles.scoreContainer}>
                  <Text style={styles.score}>{rec.score.toFixed(0)}</Text>
                  <Text style={styles.scoreLabel}>Score</Text>
                </View>
              </View>

              <View style={styles.recommendationBody}>
                <View style={styles.metricsRow}>
                  <View style={styles.metric}>
                    <Text style={styles.metricLabel}>Probability</Text>
                    <Text style={styles.metricValue}>
                      {(rec.probability * 100).toFixed(1)}%
                    </Text>
                  </View>
                  <View style={styles.metric}>
                    <Text style={styles.metricLabel}>Price</Text>
                    <Text style={styles.metricValue}>
                      ${rec.priceUsd.toFixed(2)}
                    </Text>
                  </View>
                  <View style={styles.metric}>
                    <Text style={styles.metricLabel}>Liquidity</Text>
                    <Text style={styles.metricValue}>
                      {formatLiquidity(rec.liquidity24hUsd)}
                    </Text>
                  </View>
                </View>

                <View style={styles.confidenceContainer}>
                  <View style={[
                    styles.confidenceBadge,
                    { backgroundColor: getConfidenceColor(rec.confidenceLevel) }
                  ]}>
                    <Icon name="zap" size={12} color="white" />
                    <Text style={styles.confidenceText}>{rec.confidenceLevel}</Text>
                  </View>
                </View>

                <Text style={styles.rationale} numberOfLines={2}>
                  {rec.rationale}
                </Text>
              </View>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
  },
  refreshButton: {
    padding: 8,
  },
  spinning: {
    transform: [{ rotate: '360deg' }],
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6B7280',
  },
  errorContainer: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  errorTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#EF4444',
    marginTop: 12,
    marginBottom: 8,
  },
  errorText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
    marginTop: 12,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: '#9CA3AF',
    textAlign: 'center',
  },
  recommendationsList: {
    maxHeight: 400,
  },
  recommendationCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  recommendationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  symbolContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  symbol: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
  },
  volatilityBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  volatilityText: {
    fontSize: 10,
    fontWeight: '600',
    color: 'white',
  },
  scoreContainer: {
    alignItems: 'center',
  },
  score: {
    fontSize: 18,
    fontWeight: '700',
    color: '#059669',
  },
  scoreLabel: {
    fontSize: 10,
    color: '#6B7280',
  },
  recommendationBody: {
    gap: 8,
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metric: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 10,
    color: '#6B7280',
    marginBottom: 2,
  },
  metricValue: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1F2937',
  },
  confidenceContainer: {
    alignSelf: 'flex-start',
  },
  confidenceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  confidenceText: {
    fontSize: 10,
    fontWeight: '600',
    color: 'white',
  },
  rationale: {
    fontSize: 12,
    color: '#6B7280',
    lineHeight: 16,
  },
});

export default CryptoRecommendationsCard;
