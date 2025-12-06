import React, { useState, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  SafeAreaView,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useStrategies, useUserStrategySettings, Strategy } from '../hooks/useStrategies';

const { width } = Dimensions.get('window');

interface StrategyStoreScreenProps {
  navigateTo?: (screen: string, params?: any) => void;
}

const CATEGORIES = [
  { key: 'all', label: 'All', icon: 'grid' },
  { key: 'MOMENTUM', label: 'Momentum', icon: 'trending-up' },
  { key: 'REVERSAL', label: 'Reversal', icon: 'refresh-cw' },
  { key: 'FUTURES', label: 'Futures', icon: 'bar-chart-2' },
  { key: 'FOREX', label: 'Forex', icon: 'globe' },
];

const MARKET_TYPES = [
  { key: 'all', label: 'All Markets' },
  { key: 'STOCKS', label: 'Stocks' },
  { key: 'FUTURES', label: 'Futures' },
  { key: 'FOREX', label: 'Forex' },
  { key: 'CRYPTO', label: 'Crypto' },
];

export default function StrategyStoreScreen({ navigateTo: navigateToProp }: StrategyStoreScreenProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedMarketType, setSelectedMarketType] = useState<string>('all');
  const [refreshing, setRefreshing] = useState(false);

  // Custom navigation helper (not using React Navigation)
  const navigateTo = navigateToProp || ((screen: string, params?: any) => {
    // Use custom navigation system
    if (typeof window !== 'undefined') {
      if ((window as any).__navigateToGlobal) {
        (window as any).__navigateToGlobal(screen, params);
      } else if ((window as any).__setCurrentScreen) {
        (window as any).__setCurrentScreen(screen);
      }
    }
  });

  const { strategies, loading, error, refetch } = useStrategies(
    selectedMarketType !== 'all' ? selectedMarketType : undefined,
    selectedCategory !== 'all' ? selectedCategory : undefined
  );

  const { settings: userSettings } = useUserStrategySettings();

  const enabledStrategyIds = useMemo(() => {
    return new Set(userSettings.map(s => s.strategyVersion.strategy.id));
  }, [userSettings]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refetch();
    } finally {
      setRefreshing(false);
    }
  }, [refetch]);

  const filteredStrategies = useMemo(() => {
    return strategies.filter(strategy => {
      if (selectedCategory !== 'all' && strategy.category !== selectedCategory) {
        return false;
      }
      if (selectedMarketType !== 'all' && strategy.marketType !== selectedMarketType) {
        return false;
      }
      return true;
    });
  }, [strategies, selectedCategory, selectedMarketType]);

  const getCategoryIcon = (category: string) => {
    const categoryMap: Record<string, string> = {
      'MOMENTUM': 'trending-up',
      'REVERSAL': 'refresh-cw',
      'FUTURES': 'bar-chart-2',
      'FOREX': 'globe',
      'SWING': 'activity',
      'CRYPTO': 'bitcoin',
    };
    return categoryMap[category] || 'grid';
  };

  const getCategoryColor = (category: string) => {
    const colorMap: Record<string, string> = {
      'MOMENTUM': '#10B981',
      'REVERSAL': '#F59E0B',
      'FUTURES': '#3B82F6',
      'FOREX': '#8B5CF6',
      'SWING': '#EC4899',
      'CRYPTO': '#F97316',
    };
    return colorMap[category] || '#6B7280';
  };

  const renderStrategyCard = useCallback(({ item }: { item: Strategy }) => {
    const isEnabled = enabledStrategyIds.has(item.id);
    const categoryColor = getCategoryColor(item.category);
    const categoryIcon = getCategoryIcon(item.category);

    return (
      <TouchableOpacity
        style={styles.strategyCard}
        onPress={() => navigateTo('raha-strategy-detail', { strategyId: item.id })}
        activeOpacity={0.7}
      >
        <View style={styles.strategyHeader}>
          <View style={[styles.categoryBadge, { backgroundColor: categoryColor + '20' }]}>
            <Icon name={categoryIcon} size={16} color={categoryColor} />
            <Text style={[styles.categoryText, { color: categoryColor }]}>
              {item.category}
            </Text>
          </View>
          {isEnabled && (
            <View style={styles.enabledBadge}>
              <Icon name="check-circle" size={16} color="#10B981" />
              <Text style={styles.enabledText}>Enabled</Text>
            </View>
          )}
        </View>

        <Text style={styles.strategyName}>{item.name}</Text>
        <Text style={styles.strategyDescription} numberOfLines={2}>
          {item.description}
        </Text>

        <View style={styles.strategyFooter}>
          <View style={styles.marketTypeContainer}>
            <Icon name="tag" size={12} color="#6B7280" />
            <Text style={styles.marketTypeText}>{item.marketType}</Text>
          </View>
          <View style={styles.timeframesContainer}>
            <Icon name="clock" size={12} color="#6B7280" />
            <Text style={styles.timeframesText}>
              {item.timeframeSupported.join(', ')}
            </Text>
          </View>
        </View>

        {item.influencerRef && (
          <View style={styles.influencerBadge}>
            <Icon name="user" size={12} color="#6B7280" />
            <Text style={styles.influencerText}>
              Inspired by {item.influencerRef.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </Text>
          </View>
        )}
      </TouchableOpacity>
    );
  }, [enabledStrategyIds, navigateTo]);

  const renderCategoryFilter = useCallback(({ item }: { item: typeof CATEGORIES[0] }) => {
    const isSelected = selectedCategory === item.key;
    return (
      <TouchableOpacity
        style={[styles.categoryFilter, isSelected && styles.categoryFilterSelected]}
        onPress={() => setSelectedCategory(item.key)}
      >
        <Icon
          name={item.icon}
          size={16}
          color={isSelected ? '#FFFFFF' : '#6B7280'}
        />
        <Text style={[styles.categoryFilterText, isSelected && styles.categoryFilterTextSelected]}>
          {item.label}
        </Text>
      </TouchableOpacity>
    );
  }, [selectedCategory]);

  if (loading && !refreshing) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3B82F6" />
          <Text style={styles.loadingText}>Loading strategies...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Strategy Store</Text>
        <Text style={styles.headerSubtitle}>
          Browse and enable trading strategies
        </Text>
      </View>

      {/* Category Filters */}
      <View style={styles.filtersContainer}>
        <FlatList
          data={CATEGORIES}
          renderItem={renderCategoryFilter}
          keyExtractor={(item) => item.key}
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.categoryFiltersList}
        />
      </View>

      {/* Market Type Filter */}
      <View style={styles.marketTypeFilters}>
        {MARKET_TYPES.map((type) => (
          <TouchableOpacity
            key={type.key}
            style={[
              styles.marketTypeFilter,
              selectedMarketType === type.key && styles.marketTypeFilterSelected,
            ]}
            onPress={() => setSelectedMarketType(type.key)}
          >
            <Text
              style={[
                styles.marketTypeFilterText,
                selectedMarketType === type.key && styles.marketTypeFilterTextSelected,
              ]}
            >
              {type.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Strategies List */}
      {error && (
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={24} color="#EF4444" />
          <Text style={styles.errorText}>
            Failed to load strategies. Pull to refresh.
          </Text>
          {__DEV__ && (
            <Text style={[styles.errorText, { fontSize: 12, marginTop: 8, fontFamily: 'monospace' }]}>
              {error.message || JSON.stringify(error)}
            </Text>
          )}
        </View>
      )}

      <FlatList
        data={filteredStrategies}
        renderItem={renderStrategyCard}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.strategiesList}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Icon name="inbox" size={48} color="#9CA3AF" />
            <Text style={styles.emptyText}>No strategies found</Text>
            <Text style={styles.emptySubtext}>
              Try adjusting your filters
            </Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    padding: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#6B7280',
  },
  filtersContainer: {
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  categoryFiltersList: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  categoryFilter: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
  },
  categoryFilterSelected: {
    backgroundColor: '#3B82F6',
  },
  categoryFilterText: {
    marginLeft: 6,
    fontSize: 14,
    fontWeight: '500',
    color: '#6B7280',
  },
  categoryFilterTextSelected: {
    color: '#FFFFFF',
  },
  marketTypeFilters: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  marketTypeFilter: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
    borderRadius: 16,
    backgroundColor: '#F3F4F6',
  },
  marketTypeFilterSelected: {
    backgroundColor: '#3B82F6',
  },
  marketTypeFilterText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#6B7280',
  },
  marketTypeFilterTextSelected: {
    color: '#FFFFFF',
  },
  strategiesList: {
    padding: 16,
  },
  strategyCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  strategyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  categoryBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  categoryText: {
    marginLeft: 4,
    fontSize: 12,
    fontWeight: '600',
  },
  enabledBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: '#10B98120',
  },
  enabledText: {
    marginLeft: 4,
    fontSize: 12,
    fontWeight: '600',
    color: '#10B981',
  },
  strategyName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 8,
  },
  strategyDescription: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 12,
  },
  strategyFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  marketTypeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  marketTypeText: {
    marginLeft: 4,
    fontSize: 12,
    color: '#6B7280',
  },
  timeframesContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  timeframesText: {
    marginLeft: 4,
    fontSize: 12,
    color: '#6B7280',
  },
  influencerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  influencerText: {
    marginLeft: 4,
    fontSize: 11,
    color: '#6B7280',
    fontStyle: 'italic',
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
  errorContainer: {
    padding: 20,
    alignItems: 'center',
    backgroundColor: '#FEF2F2',
    margin: 16,
    borderRadius: 12,
  },
  errorText: {
    marginTop: 8,
    fontSize: 14,
    color: '#EF4444',
    textAlign: 'center',
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    marginTop: 16,
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
  },
  emptySubtext: {
    marginTop: 4,
    fontSize: 14,
    color: '#9CA3AF',
  },
});

