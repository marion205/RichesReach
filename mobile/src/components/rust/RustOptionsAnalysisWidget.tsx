import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { useQuery, gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const GET_RUST_OPTIONS_ANALYSIS = gql`
  query GetRustOptionsAnalysis($symbol: String!) {
    rustOptionsAnalysis(symbol: $symbol) {
      symbol
      underlyingPrice
      volatilitySurface {
        atmVol
        skew
        termStructure
      }
      greeks {
        delta
        gamma
        theta
        vega
        rho
      }
      recommendedStrikes {
        strike
        expiration
        optionType
        greeks {
          delta
          gamma
          theta
          vega
          rho
        }
        expectedReturn
        riskScore
      }
      putCallRatio
      impliedVolatilityRank
      timestamp
    }
  }
`;

interface RustOptionsAnalysisWidgetProps {
  symbol: string;
}

export default function RustOptionsAnalysisWidget({ symbol }: RustOptionsAnalysisWidgetProps) {
  const { data, loading, error } = useQuery(GET_RUST_OPTIONS_ANALYSIS, {
    variables: { symbol },
    skip: !symbol,
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="small" color="#007AFF" />
        <Text style={styles.loadingText}>Loading Rust analysis...</Text>
      </View>
    );
  }

  if (error || !data?.rustOptionsAnalysis) {
    return null; // Fail silently
  }

  const analysis = data.rustOptionsAnalysis;
  const volSurface = analysis.volatilitySurface || {};
  const greeks = analysis.greeks || {};

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="zap" size={16} color="#007AFF" />
        <Text style={styles.title}>Rust Engine Analysis</Text>
      </View>

      {/* Volatility Surface */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Volatility Surface</Text>
        <View style={styles.row}>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>ATM Vol</Text>
            <Text style={styles.metricValue}>{(volSurface.atmVol * 100).toFixed(1)}%</Text>
          </View>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Skew</Text>
            <Text style={styles.metricValue}>{(volSurface.skew * 100).toFixed(2)}%</Text>
          </View>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>IV Rank</Text>
            <Text style={styles.metricValue}>{analysis.impliedVolatilityRank?.toFixed(0) || 'N/A'}</Text>
          </View>
        </View>
      </View>

      {/* Greeks */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Greeks (ATM)</Text>
        <View style={styles.greeksGrid}>
          <View style={styles.greekItem}>
            <Text style={styles.greekLabel}>Δ Delta</Text>
            <Text style={styles.greekValue}>{greeks.delta?.toFixed(3) || 'N/A'}</Text>
          </View>
          <View style={styles.greekItem}>
            <Text style={styles.greekLabel}>Γ Gamma</Text>
            <Text style={styles.greekValue}>{greeks.gamma?.toFixed(3) || 'N/A'}</Text>
          </View>
          <View style={styles.greekItem}>
            <Text style={styles.greekLabel}>Θ Theta</Text>
            <Text style={styles.greekValue}>{greeks.theta?.toFixed(3) || 'N/A'}</Text>
          </View>
          <View style={styles.greekItem}>
            <Text style={styles.greekLabel}>ν Vega</Text>
            <Text style={styles.greekValue}>{greeks.vega?.toFixed(3) || 'N/A'}</Text>
          </View>
          <View style={styles.greekItem}>
            <Text style={styles.greekLabel}>ρ Rho</Text>
            <Text style={styles.greekValue}>{greeks.rho?.toFixed(3) || 'N/A'}</Text>
          </View>
        </View>
      </View>

      {/* Put/Call Ratio */}
      <View style={styles.section}>
        <View style={styles.row}>
          <Text style={styles.sectionTitle}>Put/Call Ratio</Text>
          <Text style={styles.pcrValue}>{analysis.putCallRatio?.toFixed(2) || 'N/A'}</Text>
        </View>
      </View>
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
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metric: {
    flex: 1,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  greeksGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  greekItem: {
    width: '18%',
    alignItems: 'center',
    marginBottom: 8,
  },
  greekLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginBottom: 4,
  },
  greekValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  pcrValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#007AFF',
  },
  loadingText: {
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 8,
  },
});

