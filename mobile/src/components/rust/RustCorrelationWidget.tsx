import React, { useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, TouchableOpacity, TextInput } from 'react-native';
import { useQuery, gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const GET_RUST_CORRELATION_ANALYSIS = gql`
  query GetRustCorrelationAnalysis($primary: String!, $secondary: String) {
    rustCorrelationAnalysis(primary: $primary, secondary: $secondary) {
      primarySymbol
      secondarySymbol
      correlation1d
      correlation7d
      correlation30d
      btcDominance
      spyCorrelation
      globalRegime
      localContext
      timestamp
    }
  }
`;

interface RustCorrelationWidgetProps {
  primarySymbol: string;
  defaultSecondary?: string;
}

export default function RustCorrelationWidget({ 
  primarySymbol, 
  defaultSecondary = 'SPY' 
}: RustCorrelationWidgetProps) {
  const [secondarySymbol, setSecondarySymbol] = useState(defaultSecondary);
  const [inputValue, setInputValue] = useState(defaultSecondary);

  const { data, loading, error, refetch } = useQuery(GET_RUST_CORRELATION_ANALYSIS, {
    variables: { primary: primarySymbol, secondary: secondarySymbol },
    skip: !primarySymbol,
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const handleSearch = () => {
    if (inputValue.trim()) {
      setSecondarySymbol(inputValue.trim().toUpperCase());
      refetch({ primary: primarySymbol, secondary: inputValue.trim().toUpperCase() });
    }
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="small" color="#007AFF" />
        <Text style={styles.loadingText}>Loading correlation...</Text>
      </View>
    );
  }

  if (error || !data?.rustCorrelationAnalysis) {
    return null;
  }

  const analysis = data.rustCorrelationAnalysis;

  const getRegimeColor = (regime: string) => {
    switch (regime) {
      case 'EQUITY_RISK_ON': return '#10B981';
      case 'EQUITY_RISK_OFF': return '#EF4444';
      case 'CRYPTO_ALT_SEASON': return '#8B5CF6';
      case 'CRYPTO_BTC_DOMINANCE': return '#F59E0B';
      case 'NEUTRAL': return '#6B7280';
      default: return '#6B7280';
    }
  };
  
  const formatRegimeLabel = (globalRegime: string, localContext: string) => {
    const regimeMap: Record<string, string> = {
      'EQUITY_RISK_ON': 'Risk-On',
      'EQUITY_RISK_OFF': 'Risk-Off',
      'CRYPTO_ALT_SEASON': 'Alt Season',
      'CRYPTO_BTC_DOMINANCE': 'BTC Dominance',
      'NEUTRAL': 'Neutral',
    };
    
    const contextMap: Record<string, string> = {
      'IDIOSYNCRATIC_BREAKOUT': 'Breakout',
      'CHOPPY_MEAN_REVERT': 'Choppy',
      'NORMAL': '',
    };
    
    const regimeLabel = regimeMap[globalRegime] || globalRegime;
    const contextLabel = contextMap[localContext] || '';
    
    return contextLabel ? `${regimeLabel} · ${contextLabel}` : regimeLabel;
  };

  const getCorrelationColor = (corr: number) => {
    if (corr > 0.7) return '#10B981';
    if (corr > 0.3) return '#F59E0B';
    if (corr > -0.3) return '#6B7280';
    return '#EF4444';
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="link" size={16} color="#007AFF" />
        <Text style={styles.title}>Cross-Asset Correlation</Text>
      </View>

      {/* Symbol Input */}
      <View style={styles.searchContainer}>
        <Text style={styles.searchLabel}>Compare with:</Text>
        <View style={styles.searchRow}>
          <TextInput
            style={styles.searchInput}
            placeholder="Symbol (e.g., SPY)"
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

      {/* Correlation Values */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>
          {analysis.primarySymbol} vs {analysis.secondarySymbol}
        </Text>
        <View style={styles.correlationGrid}>
          <View style={styles.correlationItem}>
            <Text style={styles.correlationLabel}>1 Day</Text>
            <Text style={[
              styles.correlationValue,
              { color: getCorrelationColor(analysis.correlation1d) }
            ]}>
              {(analysis.correlation1d * 100).toFixed(0)}%
            </Text>
          </View>
          <View style={styles.correlationItem}>
            <Text style={styles.correlationLabel}>7 Days</Text>
            <Text style={[
              styles.correlationValue,
              { color: getCorrelationColor(analysis.correlation7d) }
            ]}>
              {(analysis.correlation7d * 100).toFixed(0)}%
            </Text>
          </View>
          <View style={styles.correlationItem}>
            <Text style={styles.correlationLabel}>30 Days</Text>
            <Text style={[
              styles.correlationValue,
              { color: getCorrelationColor(analysis.correlation30d) }
            ]}>
              {(analysis.correlation30d * 100).toFixed(0)}%
            </Text>
          </View>
        </View>
      </View>

      {/* BTC Dominance (if crypto) */}
      {analysis.btcDominance !== null && analysis.btcDominance !== undefined && (
        <View style={styles.section}>
          <View style={styles.row}>
            <Text style={styles.sectionTitle}>BTC Dominance</Text>
            <Text style={styles.btcValue}>{analysis.btcDominance.toFixed(1)}%</Text>
          </View>
        </View>
      )}

      {/* Market Regime */}
      {analysis.globalRegime && (
        <View style={styles.section}>
          <View style={styles.row}>
            <Text style={styles.sectionTitle}>Market Regime</Text>
            <View style={[
              styles.regimeBadge,
              { backgroundColor: getRegimeColor(analysis.globalRegime) + '20' }
            ]}>
              <Text style={[
                styles.regimeText,
                { color: getRegimeColor(analysis.globalRegime) }
              ]}>
                {formatRegimeLabel(analysis.globalRegime, analysis.localContext || 'NORMAL')}
              </Text>
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
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  correlationGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  correlationItem: {
    flex: 1,
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: 12,
    borderRadius: 8,
    marginHorizontal: 4,
  },
  correlationLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginBottom: 4,
  },
  correlationValue: {
    fontSize: 18,
    fontWeight: '700',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  btcValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F59E0B',
  },
  regimeBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  regimeText: {
    fontSize: 12,
    fontWeight: '600',
  },
  loadingText: {
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 8,
  },
});

