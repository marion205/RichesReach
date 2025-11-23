/**
 * Portfolio Leaderboard Screen
 * Shows top performing portfolios ranked by returns
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
import { useNavigation } from '@react-navigation/native';

const GET_PORTFOLIO_LEADERBOARD = gql`
  query GetPortfolioLeaderboard($timeframe: String, $limit: Int) {
    portfolioLeaderboard(timeframe: $timeframe, limit: $limit) {
      userId
      userName
      userEmail
      totalReturnPct
      totalValue
      rank
      holdingsCount
      bestPerformer
      worstPerformer
    }
  }
`;

type LeaderboardEntry = {
  userId: number;
  userName: string;
  userEmail: string;
  totalReturnPct: number;
  totalValue: number;
  rank: number;
  holdingsCount: number;
  bestPerformer: string | null;
  worstPerformer: string | null;
};

export default function PortfolioLeaderboardScreen() {
  const navigation = useNavigation();
  const [timeframe, setTimeframe] = useState<'daily' | 'weekly' | 'monthly' | 'all_time'>('all_time');
  const [refreshing, setRefreshing] = useState(false);

  const { data, loading, error, refetch } = useQuery(GET_PORTFOLIO_LEADERBOARD, {
    variables: { timeframe, limit: 50 },
    fetchPolicy: 'cache-and-network',
  });

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    refetch().finally(() => setRefreshing(false));
  }, [refetch]);

  const entries: LeaderboardEntry[] = data?.portfolioLeaderboard || [];

  const getRankIcon = (rank: number) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  };

  const getReturnColor = (returnPct: number) => {
    if (returnPct > 0) return '#10B981';
    if (returnPct < 0) return '#EF4444';
    return '#6B7280';
  };

  return (
    <View style={styles.container}>
      {/* Timeframe Selector */}
      <View style={styles.timeframeContainer}>
        {(['daily', 'weekly', 'monthly', 'all_time'] as const).map((tf) => (
          <TouchableOpacity
            key={tf}
            style={[styles.timeframeButton, timeframe === tf && styles.timeframeButtonActive]}
            onPress={() => setTimeframe(tf)}
          >
            <Text style={[styles.timeframeText, timeframe === tf && styles.timeframeTextActive]}>
              {tf === 'all_time' ? 'All Time' : tf.charAt(0).toUpperCase() + tf.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading && !data && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
        </View>
      )}

      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>Error loading leaderboard</Text>
        </View>
      )}

      <ScrollView
        style={styles.scrollView}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {entries.map((entry) => (
          <TouchableOpacity
            key={entry.userId}
            style={styles.entryCard}
            onPress={() => {
              // Navigate to user profile or portfolio
            }}
          >
            <View style={styles.rankContainer}>
              <Text style={styles.rankText}>{getRankIcon(entry.rank)}</Text>
            </View>

            <View style={styles.entryContent}>
              <View style={styles.entryHeader}>
                <Text style={styles.userName}>{entry.userName}</Text>
                <Text style={[styles.returnText, { color: getReturnColor(entry.totalReturnPct) }]}>
                  {entry.totalReturnPct > 0 ? '+' : ''}{entry.totalReturnPct.toFixed(2)}%
                </Text>
              </View>

              <View style={styles.entryDetails}>
                <Text style={styles.detailText}>
                  ${entry.totalValue.toLocaleString()} • {entry.holdingsCount} holdings
                </Text>
                {entry.bestPerformer && (
                  <Text style={styles.performerText}>
                    Best: {entry.bestPerformer}
                  </Text>
                )}
              </View>
            </View>

            <Ionicons name="chevron-forward" size={20} color="#9CA3AF" />
          </TouchableOpacity>
        ))}

        {entries.length === 0 && !loading && (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No leaderboard data available</Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  timeframeContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  timeframeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
  },
  timeframeButtonActive: {
    backgroundColor: '#007AFF',
  },
  timeframeText: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  timeframeTextActive: {
    color: '#FFFFFF',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorContainer: {
    padding: 20,
    alignItems: 'center',
  },
  errorText: {
    color: '#EF4444',
    fontSize: 16,
  },
  scrollView: {
    flex: 1,
  },
  entryCard: {
    flexDirection: 'row',
    alignItems: 'center',
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
  rankContainer: {
    width: 40,
    alignItems: 'center',
  },
  rankText: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  entryContent: {
    flex: 1,
    marginLeft: 12,
  },
  entryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  userName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  returnText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  entryDetails: {
    marginTop: 4,
  },
  detailText: {
    fontSize: 14,
    color: '#6B7280',
  },
  performerText: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 2,
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#9CA3AF',
  },
});

