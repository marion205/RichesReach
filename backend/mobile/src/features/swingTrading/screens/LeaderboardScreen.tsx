import React, { useState, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  SafeAreaView,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

/* ----------------------------- GraphQL ----------------------------- */
const GET_LEADERBOARD = gql`
  query GetLeaderboard($category: String, $limit: Int) {
    leaderboard(category: $category, limit: $limit) {
      rank
      category
      user {
        id
        username
        name
      }
      traderScore {
        overallScore
        accuracyScore
        consistencyScore
        disciplineScore
        totalSignals
        validatedSignals
        winRate
      }
    }
  }
`;

/* ------------------------------ Types ------------------------------ */
interface User {
  id: string;
  username: string;
  name: string | null;
}

interface TraderScore {
  overallScore: number;
  accuracyScore: number;
  consistencyScore: number;
  disciplineScore: number;
  totalSignals: number;
  validatedSignals: number;
  winRate: number;
}

interface LeaderboardEntry {
  rank: number;
  category: string;
  user: User;
  traderScore: TraderScore;
}

interface LeaderboardScreenProps {
  navigateTo?: (screen: string) => void;
}

/* ------------------------------ Helpers ------------------------------ */
const C = {
  bg: '#F9FAFB',
  card: '#FFFFFF',
  line: '#E5E7EB',
  text: '#111827',
  sub: '#6B7280',
  primary: '#3B82F6',
  green: '#10B981',
  red: '#EF4444',
  amber: '#F59E0B',
  gold: '#F59E0B',
  silver: '#9CA3AF',
  bronze: '#CD7F32',
};

const pct = (v?: number | null) =>
  typeof v === 'number' && isFinite(v) ? `${(v * 100).toFixed(1)}%` : 'N/A';

const getRankColor = (rank: number) => {
  if (rank === 1) return C.gold;
  if (rank === 2) return C.silver;
  if (rank === 3) return C.bronze;
  return C.sub;
};

const getRankIcon = (rank: number) => {
  if (rank === 1) return 'award';
  if (rank === 2) return 'award';
  if (rank === 3) return 'award';
  return 'user';
};

/* ----------------------------- Component ----------------------------- */
const LeaderboardScreen: React.FC<LeaderboardScreenProps> = ({ navigateTo }) => {
  const [category, setCategory] = useState<'overall' | 'accuracy' | 'consistency'>('overall');
  const [refreshing, setRefreshing] = useState(false);

  const {
    data,
    loading,
    error,
    refetch,
    networkStatus,
  } = useQuery<{ leaderboard: LeaderboardEntry[] }>(GET_LEADERBOARD, {
    variables: { category, limit: 50 },
    errorPolicy: 'all',
    notifyOnNetworkStatusChange: true,
  });

  const leaderboard = useMemo(() => data?.leaderboard ?? [], [data]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refetch({ category, limit: 50 });
    } finally {
      setRefreshing(false);
    }
  }, [refetch, category]);

  const categoryMeta = useMemo(() => ({
    overall: { title: 'Overall', icon: 'trending-up', color: C.primary },
    accuracy: { title: 'Accuracy', icon: 'target', color: C.green },
    consistency: { title: 'Consistency', icon: 'repeat', color: C.amber },
  }), []);

  const renderHeader = useCallback(() => (
    <View style={styles.header}>
      <View style={styles.headerTop}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigateTo?.('swing-trading-test')}
        >
          <Icon name="arrow-left" size={24} color="#6B7280" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Leaderboard</Text>
        <View style={styles.headerRight} />
      </View>

      <View style={styles.categoryTabs}>
        {(['overall', 'accuracy', 'consistency'] as const).map((cat) => (
          <TouchableOpacity
            key={cat}
            style={[
              styles.categoryTab,
              category === cat && { backgroundColor: categoryMeta[cat].color },
            ]}
            onPress={() => setCategory(cat)}
          >
            <Icon
              name={categoryMeta[cat].icon}
              size={16}
              color={category === cat ? '#FFFFFF' : C.sub}
            />
            <Text
              style={[
                styles.categoryTabText,
                category === cat && { color: '#FFFFFF' },
              ]}
            >
              {categoryMeta[cat].title}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.statsBar}>
        <Text style={styles.statsText}>
          Top {leaderboard.length} traders • {categoryMeta[category].title} ranking
        </Text>
      </View>
    </View>
  ), [navigateTo, category, categoryMeta, leaderboard.length]);

  const renderLeaderboardItem = useCallback(({ item }: { item: LeaderboardEntry }) => {
    const isTopThree = item.rank <= 3;
    const rankColor = getRankColor(item.rank);
    const rankIcon = getRankIcon(item.rank);

    return (
      <View style={[styles.leaderboardItem, isTopThree && styles.topThreeItem]}>
        <View style={styles.rankSection}>
          <View style={[styles.rankBadge, { backgroundColor: rankColor }]}>
            <Icon name={rankIcon} size={16} color="#FFFFFF" />
          </View>
          <Text style={[styles.rankNumber, { color: rankColor }]}>#{item.rank}</Text>
        </View>

        <View style={styles.userSection}>
          <Text style={styles.username}>
            {item.user.name || item.user.username}
          </Text>
          <Text style={styles.userHandle}>@{item.user.username}</Text>
        </View>

        <View style={styles.scoreSection}>
          <View style={styles.scoreRow}>
            <Text style={styles.scoreLabel}>Score</Text>
            <Text style={[styles.scoreValue, { color: C.primary }]}>
              {pct(item.traderScore.overallScore)}
            </Text>
          </View>
          <View style={styles.scoreRow}>
            <Text style={styles.scoreLabel}>Win Rate</Text>
            <Text style={[styles.scoreValue, { color: C.green }]}>
              {pct(item.traderScore.winRate)}
            </Text>
          </View>
        </View>

        <View style={styles.statsSection}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{item.traderScore.totalSignals}</Text>
            <Text style={styles.statLabel}>Signals</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{item.traderScore.validatedSignals}</Text>
            <Text style={styles.statLabel}>Validated</Text>
          </View>
        </View>
      </View>
    );
  }, []);

  const renderEmptyState = useCallback(() => (
    <View style={styles.emptyState}>
      <Icon name="users" size={48} color={C.sub} />
      <Text style={styles.emptyTitle}>No Leaderboard Data</Text>
      <Text style={styles.emptyDescription}>
        Leaderboard will populate as traders start using swing trading features
      </Text>
    </View>
  ), []);

  if (loading && !leaderboard.length) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={C.primary} />
          <Text style={styles.loadingText}>Loading leaderboard...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={48} color={C.red} />
          <Text style={styles.errorTitle}>Error Loading Leaderboard</Text>
          <Text style={styles.errorDescription}>{error.message}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={onRefresh}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={leaderboard}
        keyExtractor={(item) => `${item.user.id}-${item.category}`}
        renderItem={renderLeaderboardItem}
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={renderEmptyState}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing || networkStatus === 4}
            onRefresh={onRefresh}
          />
        }
        removeClippedSubviews
        windowSize={10}
        initialNumToRender={10}
        maxToRenderPerBatch={10}
        testID="leaderboard-list"
      />
    </SafeAreaView>
  );
};

/* ------------------------------ Styles ------------------------------ */
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: C.bg,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: C.sub,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: C.text,
    marginTop: 12,
    textAlign: 'center',
  },
  errorDescription: {
    fontSize: 14,
    color: C.sub,
    marginTop: 8,
    textAlign: 'center',
    lineHeight: 20,
  },
  retryButton: {
    backgroundColor: C.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 16,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    backgroundColor: C.card,
    borderBottomWidth: 1,
    borderBottomColor: C.line,
    paddingBottom: 16,
  },
  headerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: C.text,
  },
  headerRight: {
    width: 40,
  },
  categoryTabs: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  categoryTab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    marginRight: 8,
  },
  categoryTabText: {
    fontSize: 14,
    fontWeight: '600',
    color: C.sub,
    marginLeft: 6,
  },
  statsBar: {
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  statsText: {
    fontSize: 12,
    color: C.sub,
  },
  listContent: {
    paddingHorizontal: 16,
    paddingBottom: 24,
  },
  leaderboardItem: {
    backgroundColor: C.card,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
  },
  topThreeItem: {
    borderWidth: 2,
    borderColor: C.gold,
    shadowOpacity: 0.12,
  },
  rankSection: {
    alignItems: 'center',
    marginRight: 16,
  },
  rankBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 4,
  },
  rankNumber: {
    fontSize: 12,
    fontWeight: '700',
  },
  userSection: {
    flex: 1,
    marginRight: 16,
  },
  username: {
    fontSize: 16,
    fontWeight: '600',
    color: C.text,
  },
  userHandle: {
    fontSize: 12,
    color: C.sub,
    marginTop: 2,
  },
  scoreSection: {
    alignItems: 'flex-end',
    marginRight: 16,
  },
  scoreRow: {
    alignItems: 'center',
    marginBottom: 4,
  },
  scoreLabel: {
    fontSize: 10,
    color: C.sub,
    textTransform: 'uppercase',
  },
  scoreValue: {
    fontSize: 14,
    fontWeight: '700',
  },
  statsSection: {
    alignItems: 'center',
  },
  statItem: {
    alignItems: 'center',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 12,
    fontWeight: '600',
    color: C.text,
  },
  statLabel: {
    fontSize: 10,
    color: C.sub,
    textTransform: 'uppercase',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 48,
    paddingHorizontal: 32,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: C.text,
    marginTop: 16,
    textAlign: 'center',
  },
  emptyDescription: {
    fontSize: 14,
    color: C.sub,
    marginTop: 8,
    textAlign: 'center',
    lineHeight: 20,
  },
});

export default LeaderboardScreen;
