import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import { 
  GET_ML_SYSTEM_STATUS, 
  TRAIN_MODELS, 
  GET_BANDIT_STRATEGY,
  UPDATE_BANDIT_REWARD 
} from '../../../graphql/mlLearning';

interface MLSystemStatus {
  outcome_tracking: {
    total_outcomes: number;
    recent_outcomes: number;
  };
  models: {
    safe_model: string | null;
    aggressive_model: string | null;
  };
  bandit: {
    [strategy: string]: {
      win_rate: number;
      confidence: number;
      alpha: number;
      beta: number;
    };
  };
  last_training: {
    SAFE: string | null;
    AGGRESSIVE: string | null;
  };
  ml_available: boolean;
}

interface MLSystemScreenProps {
  navigateTo?: (screen: string) => void;
}

export default function MLSystemScreen({ navigateTo }: MLSystemScreenProps) {
  const [refreshing, setRefreshing] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);

  const { data, loading, error, refetch } = useQuery(GET_ML_SYSTEM_STATUS, {
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const [trainModels, { loading: trainingLoading }] = useMutation(TRAIN_MODELS);
  const [getBanditStrategy, { loading: banditLoading }] = useMutation(GET_BANDIT_STRATEGY);
  const [updateBanditReward] = useMutation(UPDATE_BANDIT_REWARD);

  const mlStatus: MLSystemStatus | null = data?.mlSystemStatus || null;

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await refetch();
    } catch (err) {
      console.error('Error refreshing ML system status:', err);
    } finally {
      setRefreshing(false);
    }
  };

  const handleTrainModels = async () => {
    Alert.alert(
      'Train Models',
      'This will retrain both SAFE and AGGRESSIVE models with recent data. Continue?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Train',
          onPress: async () => {
            try {
              const result = await trainModels({
                variables: { modes: ['SAFE', 'AGGRESSIVE'] }
              });
              
              if (result.data?.trainModels?.success) {
                Alert.alert('Success', 'Models trained successfully!');
                await refetch();
              } else {
                const message = result.data?.trainModels?.message || 'Failed to train models';
                Alert.alert('Info', message);
                await refetch();
              }
            } catch (err) {
              console.error('Error training models:', err);
              Alert.alert('Error', 'Failed to train models');
            }
          },
        },
      ]
    );
  };

  const handleGetBanditStrategy = async () => {
    try {
      const result = await getBanditStrategy({
        variables: { context: {} }
      });
      
      if (result.data?.banditStrategy?.selected_strategy) {
        setSelectedStrategy(result.data.banditStrategy.selected_strategy);
        Alert.alert(
          'Strategy Selected',
          `Selected strategy: ${result.data.banditStrategy.selected_strategy}`
        );
      } else {
        Alert.alert('Info', 'Using fallback strategy selection (ML libraries not available)');
      }
    } catch (err) {
      console.error('Error getting bandit strategy:', err);
      Alert.alert('Error', 'Failed to get strategy');
    }
  };

  const handleUpdateReward = (strategy: string, success: boolean) => {
    const reward = success ? 1.0 : 0.0;
    
    Alert.alert(
      'Update Reward',
      `Mark ${strategy} strategy as ${success ? 'successful' : 'failed'}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Update',
          onPress: async () => {
            try {
              await updateBanditReward({
                variables: { strategy, reward }
              });
              Alert.alert('Success', `Updated ${strategy} reward`);
              await refetch();
            } catch (err) {
              console.error('Error updating reward:', err);
              Alert.alert('Error', 'Failed to update reward');
            }
          },
        },
      ]
    );
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return 'Invalid date';
    }
  };

  const getWinRateColor = (winRate: number) => {
    if (winRate >= 0.6) return '#4CAF50';
    if (winRate >= 0.4) return '#FF9800';
    return '#F44336';
  };

  if (loading && !mlStatus) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#2196F3" />
        <Text style={styles.loadingText}>Loading ML system status...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>Error loading ML system: {error.message}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={onRefresh}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <View style={styles.headerLeft}>
            {navigateTo && (
              <TouchableOpacity
                style={styles.backButton}
                onPress={() => navigateTo('day-trading')}
              >
                <Text style={styles.backButtonText}>← Back</Text>
              </TouchableOpacity>
            )}
            <View style={styles.headerText}>
              <Text style={styles.title}>ML Learning System</Text>
              <Text style={styles.subtitle}>Machine Learning & Strategy Optimization</Text>
            </View>
          </View>
        </View>
      </View>

      {/* System Status */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>System Status</Text>
          <TouchableOpacity
            style={styles.infoButton}
            onPress={() => Alert.alert(
              'ML System Status',
              'Shows the current state of the machine learning system:\n\n• ML Available: Whether ML libraries are loaded\n• Total Outcomes: All trading outcomes tracked\n• Recent Outcomes: Outcomes from last 7 days\n• Model Status: Current model performance metrics'
            )}
          >
            <Text style={styles.infoButtonText}>ℹ️</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.statusRow}>
          <Text style={styles.statusLabel}>ML Available:</Text>
          <Text style={[styles.statusValue, { color: mlStatus?.ml_available ? '#4CAF50' : '#F44336' }]}>
            {mlStatus?.ml_available ? 'Yes' : 'No'}
          </Text>
        </View>
        <View style={styles.statusRow}>
          <Text style={styles.statusLabel}>Total Outcomes:</Text>
          <Text style={styles.statusValue}>{mlStatus?.outcome_tracking.total_outcomes || 0}</Text>
        </View>
        <View style={styles.statusRow}>
          <Text style={styles.statusLabel}>Recent Outcomes (7d):</Text>
          <Text style={styles.statusValue}>{mlStatus?.outcome_tracking.recent_outcomes || 0}</Text>
        </View>
      </View>

      {/* Model Status */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Model Status</Text>
        <View style={styles.modelRow}>
          <Text style={styles.modelLabel}>SAFE Model:</Text>
          <Text style={styles.modelValue}>
            {mlStatus?.models.safe_model ? 'Active' : 'Not Available'}
          </Text>
        </View>
        <View style={styles.modelRow}>
          <Text style={styles.modelLabel}>AGGRESSIVE Model:</Text>
          <Text style={styles.modelValue}>
            {mlStatus?.models.aggressive_model ? 'Active' : 'Not Available'}
          </Text>
        </View>
        <View style={styles.modelRow}>
          <Text style={styles.modelLabel}>Last Training (SAFE):</Text>
          <Text style={styles.modelValue}>
            {formatDate(mlStatus?.last_training.SAFE)}
          </Text>
        </View>
        <View style={styles.modelRow}>
          <Text style={styles.modelLabel}>Last Training (AGGRESSIVE):</Text>
          <Text style={styles.modelValue}>
            {formatDate(mlStatus?.last_training.AGGRESSIVE)}
          </Text>
        </View>
      </View>

      {/* Strategy Performance */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Strategy Performance</Text>
        {mlStatus?.bandit && Object.entries(mlStatus.bandit).map(([strategy, performance]) => (
          <View key={strategy} style={styles.strategyRow}>
            <View style={styles.strategyInfo}>
              <Text style={styles.strategyName}>{strategy.replace('_', ' ').toUpperCase()}</Text>
              <Text style={[styles.winRate, { color: getWinRateColor(performance.win_rate) }]}>
                {(performance.win_rate * 100).toFixed(1)}%
              </Text>
            </View>
            <View style={styles.strategyActions}>
              <TouchableOpacity
                style={[styles.rewardButton, styles.successButton]}
                onPress={() => handleUpdateReward(strategy, true)}
              >
                <Text style={styles.rewardButtonText}>✓</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.rewardButton, styles.failureButton]}
                onPress={() => handleUpdateReward(strategy, false)}
              >
                <Text style={styles.rewardButtonText}>✗</Text>
              </TouchableOpacity>
            </View>
          </View>
        ))}
      </View>

      {/* Actions */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Actions</Text>
        
        <TouchableOpacity
          style={[styles.actionButton, trainingLoading && styles.actionButtonDisabled]}
          onPress={handleTrainModels}
          disabled={trainingLoading}
        >
          {trainingLoading ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.actionButtonText}>Train Models</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, banditLoading && styles.actionButtonDisabled]}
          onPress={handleGetBanditStrategy}
          disabled={banditLoading}
        >
          {banditLoading ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.actionButtonText}>Get Strategy</Text>
          )}
        </TouchableOpacity>

        {selectedStrategy && (
          <View style={styles.selectedStrategy}>
            <Text style={styles.selectedStrategyText}>
              Selected: {selectedStrategy.replace('_', ' ').toUpperCase()}
            </Text>
          </View>
        )}
      </View>

      {/* Info */}
      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>How It Works</Text>
        <Text style={styles.infoText}>
          • The ML system tracks trading outcomes to improve predictions{'\n'}
          • Models are retrained automatically when enough new data is available{'\n'}
          • The bandit system learns which strategies work best in different market conditions{'\n'}
          • Update rewards to help the system learn from your trading results
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  backButton: {
    marginRight: 12,
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  backButtonText: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: '600',
  },
  headerText: {
    flex: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginTop: 4,
  },
  card: {
    backgroundColor: '#fff',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  infoButton: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  infoButtonText: {
    fontSize: 16,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  statusLabel: {
    fontSize: 14,
    color: '#666',
  },
  statusValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  modelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  modelLabel: {
    fontSize: 14,
    color: '#666',
  },
  modelValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  strategyRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  strategyInfo: {
    flex: 1,
  },
  strategyName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  winRate: {
    fontSize: 12,
    fontWeight: '600',
    marginTop: 2,
  },
  strategyActions: {
    flexDirection: 'row',
    gap: 8,
  },
  rewardButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  successButton: {
    backgroundColor: '#4CAF50',
  },
  failureButton: {
    backgroundColor: '#F44336',
  },
  rewardButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  actionButton: {
    backgroundColor: '#2196F3',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 12,
  },
  actionButtonDisabled: {
    backgroundColor: '#ccc',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  selectedStrategy: {
    backgroundColor: '#e3f2fd',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  selectedStrategyText: {
    fontSize: 14,
    color: '#1976d2',
    textAlign: 'center',
    fontWeight: '600',
  },
  infoCard: {
    backgroundColor: '#fff3cd',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#ffc107',
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#856404',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#856404',
    lineHeight: 20,
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 16,
  },
  errorText: {
    fontSize: 16,
    color: '#f44336',
    textAlign: 'center',
    marginTop: 50,
    marginHorizontal: 20,
  },
  retryButton: {
    marginTop: 20,
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: '#2196F3',
    borderRadius: 8,
    alignSelf: 'center',
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
