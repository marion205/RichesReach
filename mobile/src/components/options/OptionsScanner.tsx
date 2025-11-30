import React, { useState, useMemo } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useQuery, gql } from '@apollo/client';

const SCAN_OPTIONS = gql`
  query ScanOptions($filters: JSONString) {
    scanOptions(filters: $filters) {
      symbol
      contractSymbol
      strike
      expiration
      optionType
      bid
      ask
      volume
      impliedVolatility
      delta
      theta
      score
      opportunity
    }
  }
`;

interface OptionsScannerProps {
  onSelect?: (option: any) => void;
}

export default function OptionsScanner({ onSelect }: OptionsScannerProps) {
  const [activeFilter, setActiveFilter] = useState<'highIV' | 'lowIV' | 'highDelta' | 'highVolume' | 'nearMoney'>('highIV');
  const [scanning, setScanning] = useState(false);

  // Simple, Jobs-style filters - just the essentials
  const filters = useMemo(() => {
    const base = {
      minVolume: 100,
      maxDaysToExp: 45,
    };

    switch (activeFilter) {
      case 'highIV':
        return { ...base, minIV: 0.3, sortBy: 'iv' };
      case 'lowIV':
        return { ...base, maxIV: 0.2, sortBy: 'iv' };
      case 'highDelta':
        return { ...base, minDelta: 0.6, sortBy: 'delta' };
      case 'highVolume':
        return { ...base, minVolume: 5000, sortBy: 'volume' };
      case 'nearMoney':
        return { ...base, maxStrikeOffset: 0.05, sortBy: 'strike' };
      default:
        return base;
    };
  }, [activeFilter]);

  const { data, loading, error } = useQuery(SCAN_OPTIONS, {
    variables: { filters: JSON.stringify(filters) },
    skip: !scanning,
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const scanResults = data?.scanOptions || [];

  // Mock results for demo (would use real data in production)
  const mockResults = useMemo(() => {
    if (!scanning) return [];
    
    const symbols = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'AMZN'];
    return symbols.slice(0, 5).map((symbol, i) => ({
      symbol,
      contractSymbol: `${symbol}240119C00150000`,
      strike: 150 + (i * 5),
      expiration: '2024-01-19',
      optionType: 'call',
      bid: 2.40 + (i * 0.1),
      ask: 2.50 + (i * 0.1),
      volume: 5000 + (i * 1000),
      impliedVolatility: 0.25 + (i * 0.05),
      delta: 0.5 + (i * 0.1),
      theta: -0.05,
      score: 85 - (i * 5),
      opportunity: activeFilter === 'highIV' ? 'High volatility play' : 
                   activeFilter === 'lowIV' ? 'Low volatility entry' :
                   activeFilter === 'highDelta' ? 'Strong directional move' :
                   activeFilter === 'highVolume' ? 'High liquidity' : 'Near-the-money',
    }));
  }, [scanning, activeFilter]);

  const results = scanResults.length > 0 ? scanResults : mockResults;

  const filterLabels = {
    highIV: 'High IV',
    lowIV: 'Low IV',
    highDelta: 'High Delta',
    highVolume: 'High Volume',
    nearMoney: 'Near Money',
  };

  const filterDescriptions = {
    highIV: 'Find high volatility opportunities',
    lowIV: 'Find low volatility entries',
    highDelta: 'Strong directional moves',
    highVolume: 'High liquidity trades',
    nearMoney: 'At-the-money options',
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="search" size={18} color="#007AFF" />
        <Text style={styles.title}>Find Opportunities</Text>
      </View>

      <Text style={styles.subtitle}>
        {filterDescriptions[activeFilter]}
      </Text>

      {/* Simple Filter Pills - Jobs Style */}
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        style={styles.filterContainer}
        contentContainerStyle={styles.filterContent}
      >
        {Object.entries(filterLabels).map(([key, label]) => (
          <TouchableOpacity
            key={key}
            style={[styles.filterPill, activeFilter === key && styles.filterPillActive]}
            onPress={() => {
              setActiveFilter(key as any);
              setScanning(false);
            }}
          >
            <Text style={[styles.filterText, activeFilter === key && styles.filterTextActive]}>
              {label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Scan Button - Big, Beautiful, Jobs Style */}
      <TouchableOpacity
        style={[styles.scanButton, scanning && styles.scanButtonActive]}
        onPress={() => setScanning(true)}
        disabled={scanning}
      >
        {scanning ? (
          <>
            <ActivityIndicator size="small" color="#FFFFFF" />
            <Text style={styles.scanButtonText}>Scanning...</Text>
          </>
        ) : (
          <>
            <Icon name="zap" size={20} color="#FFFFFF" />
            <Text style={styles.scanButtonText}>Scan Market</Text>
          </>
        )}
      </TouchableOpacity>

      {/* Results - Clean, Simple List */}
      {scanning && (
        <ScrollView style={styles.resultsContainer} showsVerticalScrollIndicator={false}>
          {loading ? (
            <View style={styles.loadingState}>
              <ActivityIndicator size="large" color="#007AFF" />
              <Text style={styles.loadingText}>Finding opportunities...</Text>
            </View>
          ) : results.length > 0 ? (
            results.map((option: any, index: number) => (
              <TouchableOpacity
                key={index}
                style={styles.resultCard}
                onPress={() => onSelect?.(option)}
              >
                <View style={styles.resultHeader}>
                  <View>
                    <Text style={styles.resultSymbol}>{option.symbol}</Text>
                    <Text style={styles.resultDetails}>
                      ${option.strike} {option.optionType} • {option.expiration}
                    </Text>
                  </View>
                  <View style={styles.scoreBadge}>
                    <Text style={styles.scoreText}>{option.score}</Text>
                  </View>
                </View>
                
                <View style={styles.resultMetrics}>
                  <View style={styles.metric}>
                    <Text style={styles.metricLabel}>Bid/Ask</Text>
                    <Text style={styles.metricValue}>
                      ${option.bid.toFixed(2)} / ${option.ask.toFixed(2)}
                    </Text>
                  </View>
                  <View style={styles.metric}>
                    <Text style={styles.metricLabel}>IV</Text>
                    <Text style={styles.metricValue}>
                      {(option.impliedVolatility * 100).toFixed(1)}%
                    </Text>
                  </View>
                  <View style={styles.metric}>
                    <Text style={styles.metricLabel}>Volume</Text>
                    <Text style={styles.metricValue}>{option.volume.toLocaleString()}</Text>
                  </View>
                </View>

                <Text style={styles.opportunityText}>{option.opportunity}</Text>
              </TouchableOpacity>
            ))
          ) : (
            <View style={styles.emptyState}>
              <Icon name="search" size={48} color="#D1D5DB" />
              <Text style={styles.emptyText}>No opportunities found</Text>
              <Text style={styles.emptySubtext}>Try adjusting your filters</Text>
            </View>
          )}
        </ScrollView>
      )}

      {!scanning && (
        <View style={styles.placeholderState}>
          <Icon name="zap" size={64} color="#E5E7EB" />
          <Text style={styles.placeholderText}>Tap "Scan Market" to find opportunities</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginLeft: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 16,
    marginLeft: 26,
  },
  filterContainer: {
    marginBottom: 20,
  },
  filterContent: {
    gap: 8,
  },
  filterPill: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    marginRight: 8,
  },
  filterPillActive: {
    backgroundColor: '#007AFF',
  },
  filterText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
  filterTextActive: {
    color: '#FFFFFF',
  },
  scanButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
    marginBottom: 20,
  },
  scanButtonActive: {
    opacity: 0.7,
  },
  scanButtonText: {
    fontSize: 17,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  resultsContainer: {
    maxHeight: 400,
  },
  loadingState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 12,
  },
  resultCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  resultSymbol: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  resultDetails: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 4,
  },
  scoreBadge: {
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  scoreText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#059669',
  },
  resultMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  metric: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  opportunityText: {
    fontSize: 13,
    color: '#007AFF',
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#9CA3AF',
    marginTop: 8,
  },
  placeholderState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  placeholderText: {
    fontSize: 15,
    color: '#9CA3AF',
    marginTop: 16,
    textAlign: 'center',
  },
});


