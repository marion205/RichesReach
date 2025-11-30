import React, { useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, TouchableOpacity, TextInput } from 'react-native';
import { useQuery, gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const GET_RUST_FOREX_ANALYSIS = gql`
  query GetRustForexAnalysis($pair: String!) {
    rustForexAnalysis(pair: $pair) {
      pair
      bid
      ask
      spread
      pipValue
      volatility
      trend
      supportLevel
      resistanceLevel
      correlation24h
      timestamp
    }
  }
`;

interface RustForexWidgetProps {
  defaultPair?: string;
  size?: 'large' | 'compact';
}

export default function RustForexWidget({ defaultPair = 'EURUSD', size = 'large' }: RustForexWidgetProps) {
  const [pair, setPair] = useState(defaultPair);
  const [inputValue, setInputValue] = useState(defaultPair);

  const { data, loading, error, refetch } = useQuery(GET_RUST_FOREX_ANALYSIS, {
    variables: { pair },
    skip: !pair,
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const handleSearch = () => {
    if (inputValue.trim()) {
      const newPair = inputValue.trim().toUpperCase();
      setPair(newPair);
      refetch({ pair: newPair });
    }
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="small" color="#007AFF" />
        <Text style={styles.loadingText}>Loading forex data...</Text>
      </View>
    );
  }

  if (error) {
    // Show error state instead of hiding
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Icon name="globe" size={16} color="#007AFF" />
          <Text style={styles.title}>Forex Analysis</Text>
        </View>
        <Text style={styles.errorText}>Unable to load forex data. Check connection.</Text>
      </View>
    );
  }

  if (!data?.rustForexAnalysis) {
    // Show empty state instead of hiding - so user knows widget is there
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Icon name="globe" size={16} color="#007AFF" />
          <Text style={styles.title}>Forex Analysis</Text>
        </View>
        <Text style={styles.loadingText}>Loading forex data...</Text>
      </View>
    );
  }

  const analysis = data.rustForexAnalysis;

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'BULLISH': return '#10B981';
      case 'BEARISH': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const isCompact = size === 'compact';
  
  return (
    <View style={[styles.container, isCompact && styles.containerCompact]}>
      {!isCompact && (
        <View style={styles.header}>
          <Icon name="globe" size={16} color="#007AFF" />
          <Text style={styles.title}>Forex Analysis</Text>
        </View>
      )}

      {/* Pair Input - Hidden in compact mode */}
      {!isCompact && (
        <View style={styles.searchContainer}>
          <Text style={styles.searchLabel}>Currency Pair:</Text>
          <View style={styles.searchRow}>
            <TextInput
              style={styles.searchInput}
              placeholder="EURUSD"
              value={inputValue}
              onChangeText={setInputValue}
              autoCapitalize="characters"
              autoCorrect={false}
            />
            <TouchableOpacity style={styles.searchButton} onPress={handleSearch}>
              <Icon name="search" size={16} color="#007AFF" />
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Price Info */}
      <View style={[styles.section, isCompact && styles.sectionCompact]}>
        {!isCompact && <Text style={styles.sectionTitle}>{analysis.pair}</Text>}
        <View style={styles.priceRow}>
          <View style={[styles.priceItem, isCompact && styles.priceItemCompact]}>
            <Text style={[styles.priceLabel, isCompact && styles.priceLabelCompact]}>Bid</Text>
            <Text style={[styles.priceValue, isCompact && styles.priceValueCompact]}>{analysis.bid?.toFixed(5) || 'N/A'}</Text>
          </View>
          <View style={[styles.priceItem, isCompact && styles.priceItemCompact]}>
            <Text style={[styles.priceLabel, isCompact && styles.priceLabelCompact]}>Ask</Text>
            <Text style={[styles.priceValue, isCompact && styles.priceValueCompact]}>{analysis.ask?.toFixed(5) || 'N/A'}</Text>
          </View>
          {!isCompact && (
            <View style={styles.priceItem}>
              <Text style={styles.priceLabel}>Spread</Text>
              <Text style={styles.priceValue}>{analysis.spread?.toFixed(5) || 'N/A'}</Text>
            </View>
          )}
        </View>
      </View>

      {/* Market Data - Hidden in compact mode */}
      {!isCompact && (
        <View style={styles.section}>
          <View style={styles.row}>
            <Text style={styles.sectionTitle}>Trend</Text>
            <View style={[
              styles.trendBadge,
              { backgroundColor: getTrendColor(analysis.trend) + '20' }
            ]}>
              <Text style={[
                styles.trendText,
                { color: getTrendColor(analysis.trend) }
              ]}>
                {analysis.trend}
              </Text>
            </View>
          </View>
          <View style={styles.metricsGrid}>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Volatility</Text>
              <Text style={styles.metricValue}>{(analysis.volatility * 100).toFixed(2)}%</Text>
            </View>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Pip Value</Text>
              <Text style={styles.metricValue}>${analysis.pipValue?.toFixed(2) || 'N/A'}</Text>
            </View>
          </View>
        </View>
      )}

      {/* Support/Resistance - Hidden in compact mode */}
      {!isCompact && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Key Levels</Text>
          <View style={styles.levelsRow}>
            <View style={styles.levelItem}>
              <Text style={styles.levelLabel}>Support</Text>
              <Text style={styles.levelValue}>{analysis.supportLevel?.toFixed(5) || 'N/A'}</Text>
            </View>
            <View style={styles.levelItem}>
              <Text style={styles.levelLabel}>Resistance</Text>
              <Text style={styles.levelValue}>{analysis.resistanceLevel?.toFixed(5) || 'N/A'}</Text>
            </View>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  containerCompact: {
    padding: 0,
    marginBottom: 0,
    backgroundColor: 'transparent',
    borderWidth: 0,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginLeft: 8,
  },
  searchContainer: {
    marginBottom: 16,
  },
  searchLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 8,
  },
  searchRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  searchInput: {
    flex: 1,
    height: 40,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 14,
    marginRight: 8,
  },
  searchButton: {
    width: 40,
    height: 40,
    backgroundColor: '#007AFF',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  section: {
    marginBottom: 16,
  },
  sectionCompact: {
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  priceItem: {
    flex: 1,
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: 12,
    borderRadius: 8,
    marginHorizontal: 4,
  },
  priceItemCompact: {
    padding: 8,
    marginHorizontal: 2,
  },
  priceLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginBottom: 4,
  },
  priceLabelCompact: {
    fontSize: 10,
    marginBottom: 2,
  },
  priceValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  priceValueCompact: {
    fontSize: 14,
    fontWeight: '800',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  trendBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  trendText: {
    fontSize: 12,
    fontWeight: '600',
  },
  metricsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metric: {
    flex: 1,
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: 12,
    borderRadius: 8,
    marginHorizontal: 4,
  },
  metricLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  levelsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  levelItem: {
    flex: 1,
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: 12,
    borderRadius: 8,
    marginHorizontal: 4,
  },
  levelLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginBottom: 4,
  },
  levelValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  loadingText: {
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 8,
  },
  errorText: {
    fontSize: 12,
    color: '#EF4444',
    textAlign: 'center',
    padding: 8,
  },
});

