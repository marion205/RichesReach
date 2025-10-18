import React, { memo } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useQuery } from '@apollo/client';
import { AI_YIELD_OPTIMIZER_QUERY } from '../graphql/queries_actual_schema';

interface AIOptimizerProps {
  userId?: string;
}

const AIOptimizer: React.FC<AIOptimizerProps> = memo(({ userId }) => {
  const { data, loading, error } = useQuery(AI_YIELD_OPTIMIZER_QUERY, {
    variables: { userRiskTolerance: 0.5 },
    fetchPolicy: 'cache-first',
    errorPolicy: 'all',
    notifyOnNetworkStatusChange: false,
  });

  if (loading) {
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>AI optimizing your portfolio...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>AI optimization temporarily unavailable</Text>
      </View>
    );
  }

  const result = data?.aiYieldOptimizer;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>AI-Powered Portfolio</Text>
      {result && (
        <View style={styles.resultContainer}>
          <Text style={styles.expectedApy}>
            Expected APY: {(result.expectedApy * 100).toFixed(1)}%
          </Text>
          <Text style={styles.riskLevel}>
            Risk Level: {(result.totalRisk * 100).toFixed(0)}%
          </Text>
          {result.pools && result.pools.length > 0 && (
            <View style={styles.poolsContainer}>
              <Text style={styles.poolsTitle}>Recommended Pools:</Text>
              {result.pools.slice(0, 3).map((pool: any, index: number) => (
                <Text key={index} style={styles.poolItem}>
                  • {pool.protocol}: {pool.apy.toFixed(1)}% APY
                </Text>
              ))}
            </View>
          )}
        </View>
      )}
    </View>
  );
});

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#f8f9fa',
    borderTopWidth: 1,
    borderTopColor: '#e9ecef',
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
    textAlign: 'center',
  },
  loadingText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  errorText: {
    fontSize: 14,
    color: '#EF4444',
    textAlign: 'center',
  },
  resultContainer: {
    backgroundColor: 'white',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  expectedApy: {
    fontSize: 16,
    fontWeight: '600',
    color: '#10B981',
    marginBottom: 4,
  },
  riskLevel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  poolsContainer: {
    marginTop: 8,
  },
  poolsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  poolItem: {
    fontSize: 12,
    color: '#666',
    marginLeft: 8,
  },
});

export default AIOptimizer;
