import React, { useState, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
  Alert,
  TextInput,
  Switch,
  Modal,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import {
  useStrategy,
  useUserStrategySettings,
  useEnableStrategy,
  useDisableStrategy,
} from '../hooks/useStrategies';
import { useRunBacktest, useUserBacktests } from '../hooks/useBacktest';

interface StrategyDetailScreenProps {
  strategyId?: string;
  navigateTo?: (screen: string, params?: any) => void;
  onBack?: () => void;
}

export default function StrategyDetailScreen({ strategyId: strategyIdProp, navigateTo, onBack }: StrategyDetailScreenProps = {}) {
  // Get strategyId from props or window params (for backwards compatibility)
  const strategyId = strategyIdProp || (typeof window !== 'undefined' && (window as any).__currentScreenParams?.strategyId);
  
  // Custom navigation helper (not using React Navigation)
  const handleBack = () => {
    if (onBack) {
      onBack();
    } else if (navigateTo) {
      navigateTo('pro-labs');
    } else if (typeof window !== 'undefined') {
      if ((window as any).__navigateToGlobal) {
        (window as any).__navigateToGlobal('pro-labs');
      } else if ((window as any).__setCurrentScreen) {
        (window as any).__setCurrentScreen('pro-labs');
      }
    }
  };
  
  const handleNavigateToBacktests = () => {
    if (navigateTo) {
      navigateTo('pro-labs', { view: 'backtests' });
    } else if (typeof window !== 'undefined') {
      if ((window as any).__navigateToGlobal) {
        (window as any).__navigateToGlobal('pro-labs', { view: 'backtests' });
      } else if ((window as any).__setCurrentScreen) {
        (window as any).__setCurrentScreen('pro-labs');
      }
    }
  };

  const { strategy, loading } = useStrategy(strategyId);
  const { settings: userSettings } = useUserStrategySettings();
  const { enableStrategy, loading: enabling } = useEnableStrategy();
  const { disableStrategy, loading: disabling } = useDisableStrategy();
  const { runBacktest, loading: backtesting } = useRunBacktest();
  const { backtests } = useUserBacktests();

  const [showParameters, setShowParameters] = useState(false);
  const [showBacktest, setShowBacktest] = useState(false);
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [autoTradeEnabled, setAutoTradeEnabled] = useState(false);

  const userSetting = useMemo(() => {
    return userSettings.find(
      s => s.strategyVersion.strategy.id === strategyId
    );
  }, [userSettings, strategyId]);

  const isEnabled = !!userSetting?.enabled;

  React.useEffect(() => {
    if (userSetting) {
      setParameters(userSetting.parameters || {});
      setAutoTradeEnabled(userSetting.autoTradeEnabled || false);
    } else if (strategy?.defaultVersion?.configSchema) {
      // Initialize with default values
      const defaults: Record<string, any> = {};
      const props = strategy.defaultVersion.configSchema.properties || {};
      Object.keys(props).forEach(key => {
        if (props[key].default !== undefined) {
          defaults[key] = props[key].default;
        }
      });
      setParameters(defaults);
    }
  }, [userSetting, strategy]);

  const handleEnable = useCallback(async () => {
    if (!strategy?.defaultVersion?.id) {
      Alert.alert('Error', 'Strategy version not found');
      return;
    }

    const result = await enableStrategy(strategy.defaultVersion.id, parameters);
    if (result.success) {
      Alert.alert('Success', 'Strategy enabled successfully');
    } else {
      Alert.alert('Error', result.message);
    }
  }, [strategy, parameters, enableStrategy]);

  const handleDisable = useCallback(async () => {
    if (!userSetting?.strategyVersion?.id) {
      Alert.alert('Error', 'Strategy not enabled');
      return;
    }

    const result = await disableStrategy(userSetting.strategyVersion.id);
    if (result.success) {
      Alert.alert('Success', 'Strategy disabled successfully');
    } else {
      Alert.alert('Error', result.message);
    }
  }, [userSetting, disableStrategy]);

  const handleRunBacktest = useCallback(async () => {
    if (!strategy?.defaultVersion?.id) {
      Alert.alert('Error', 'Strategy version not found');
      return;
    }

    // Default backtest parameters
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30); // 30 days

    const result = await runBacktest(
      strategy.defaultVersion.id,
      'SPY', // Default symbol
      '5m',
      startDate.toISOString().split('T')[0],
      endDate.toISOString().split('T')[0],
      parameters
    );

    if (result.success) {
      Alert.alert('Success', 'Backtest started. Check backtest results.');
      setShowBacktest(false);
    } else {
      Alert.alert('Error', result.message);
    }
  }, [strategy, parameters, runBacktest]);

  const renderParameterInput = useCallback((key: string, schema: any) => {
    const value = parameters[key] ?? schema.default ?? 0;
    const isNumber = schema.type === 'number';

    return (
      <View key={key} style={styles.parameterRow}>
        <View style={styles.parameterLabel}>
          <Text style={styles.parameterName}>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</Text>
          <Text style={styles.parameterDescription}>{schema.description || ''}</Text>
          {schema.minimum !== undefined && schema.maximum !== undefined && (
            <Text style={styles.parameterRange}>
              Range: {schema.minimum} - {schema.maximum}
            </Text>
          )}
        </View>
        <TextInput
          style={styles.parameterInput}
          value={String(value)}
          onChangeText={(text) => {
            const numValue = isNumber ? parseFloat(text) || 0 : text;
            setParameters({ ...parameters, [key]: numValue });
          }}
          keyboardType={isNumber ? 'numeric' : 'default'}
          placeholder={String(schema.default || '')}
        />
      </View>
    );
  }, [parameters]);

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3B82F6" />
          <Text style={styles.loadingText}>Loading strategy...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!strategy) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={48} color="#EF4444" />
          <Text style={styles.errorText}>Strategy not found</Text>
          <TouchableOpacity
            style={styles.backButton}
            onPress={handleBack}
          >
            <Text style={styles.backButtonText}>Go Back</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const configSchema = strategy.defaultVersion?.configSchema || { properties: {} };
  const parametersList = Object.entries(configSchema.properties || {});

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={handleBack}
          >
            <Icon name="arrow-left" size={24} color="#111827" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Strategy Details</Text>
          <View style={{ width: 24 }} />
        </View>

        {/* Strategy Info */}
        <View style={styles.strategyCard}>
          <Text style={styles.strategyName}>{strategy.name}</Text>
          <Text style={styles.strategyDescription}>{strategy.description}</Text>

          <View style={styles.strategyMeta}>
            <View style={styles.metaItem}>
              <Icon name="tag" size={16} color="#6B7280" />
              <Text style={styles.metaText}>{strategy.marketType}</Text>
            </View>
            <View style={styles.metaItem}>
              <Icon name="clock" size={16} color="#6B7280" />
              <Text style={styles.metaText}>
                {strategy.timeframeSupported.join(', ')}
              </Text>
            </View>
            <View style={styles.metaItem}>
              <Icon name="grid" size={16} color="#6B7280" />
              <Text style={styles.metaText}>{strategy.category}</Text>
            </View>
          </View>

          {strategy.influencerRef && (
            <View style={styles.influencerBadge}>
              <Icon name="user" size={16} color="#6B7280" />
              <Text style={styles.influencerText}>
                Inspired by {strategy.influencerRef.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </Text>
            </View>
          )}
        </View>

        {/* Enable/Disable Button */}
        <TouchableOpacity
          style={[
            styles.enableButton,
            isEnabled ? styles.enableButtonDisabled : styles.enableButtonEnabled,
          ]}
          onPress={isEnabled ? handleDisable : handleEnable}
          disabled={enabling || disabling}
        >
          {enabling || disabling ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <>
              <Icon
                name={isEnabled ? 'x-circle' : 'check-circle'}
                size={20}
                color="#FFFFFF"
              />
              <Text style={styles.enableButtonText}>
                {isEnabled ? 'Disable Strategy' : 'Enable Strategy'}
              </Text>
            </>
          )}
        </TouchableOpacity>

        {/* Parameters Section */}
        {parametersList.length > 0 && (
          <TouchableOpacity
            style={styles.section}
            onPress={() => setShowParameters(!showParameters)}
          >
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Parameters</Text>
              <Icon
                name={showParameters ? 'chevron-up' : 'chevron-down'}
                size={20}
                color="#6B7280"
              />
            </View>
          </TouchableOpacity>
        )}

        {showParameters && parametersList.length > 0 && (
          <View style={styles.parametersContainer}>
            {parametersList.map(([key, schema]: [string, any]) =>
              renderParameterInput(key, schema)
            )}
          </View>
        )}

        {/* Actions */}
        <View style={styles.actionsContainer}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => setShowBacktest(true)}
          >
            <Icon name="play-circle" size={20} color="#3B82F6" />
            <Text style={styles.actionButtonText}>Run Backtest</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            onPress={handleNavigateToBacktests}
          >
            <Icon name="bar-chart-2" size={20} color="#3B82F6" />
            <Text style={styles.actionButtonText}>View Backtests</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>

      {/* Backtest Modal */}
      <Modal
        visible={showBacktest}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowBacktest(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Run Backtest</Text>
              <TouchableOpacity onPress={() => setShowBacktest(false)}>
                <Icon name="x" size={24} color="#6B7280" />
              </TouchableOpacity>
            </View>

            <Text style={styles.modalText}>
              This will run a backtest using the current parameters. Results will be available in the backtests section.
            </Text>

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={[styles.modalButton, styles.modalButtonCancel]}
                onPress={() => setShowBacktest(false)}
              >
                <Text style={styles.modalButtonTextCancel}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.modalButtonConfirm]}
                onPress={handleRunBacktest}
                disabled={backtesting}
              >
                {backtesting ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Text style={styles.modalButtonTextConfirm}>Run</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
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
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    marginTop: 16,
    fontSize: 16,
    color: '#EF4444',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
  },
  backButton: {
    padding: 8,
  },
  strategyCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  strategyName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 8,
  },
  strategyDescription: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 16,
  },
  strategyMeta: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 12,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
    marginBottom: 8,
  },
  metaText: {
    marginLeft: 6,
    fontSize: 12,
    color: '#6B7280',
  },
  influencerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  influencerText: {
    marginLeft: 6,
    fontSize: 12,
    color: '#6B7280',
    fontStyle: 'italic',
  },
  enableButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
  },
  enableButtonEnabled: {
    backgroundColor: '#10B981',
  },
  enableButtonDisabled: {
    backgroundColor: '#EF4444',
  },
  enableButtonText: {
    marginLeft: 8,
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  section: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  parametersContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  parameterRow: {
    marginBottom: 16,
  },
  parameterLabel: {
    marginBottom: 8,
  },
  parameterName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  parameterDescription: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  parameterRange: {
    fontSize: 11,
    color: '#9CA3AF',
  },
  parameterInput: {
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#111827',
    backgroundColor: '#F9FAFB',
  },
  actionsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    marginHorizontal: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  actionButtonText: {
    marginLeft: 8,
    fontSize: 14,
    fontWeight: '600',
    color: '#3B82F6',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
  },
  modalText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 24,
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  modalButton: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginHorizontal: 6,
  },
  modalButtonCancel: {
    backgroundColor: '#F3F4F6',
  },
  modalButtonConfirm: {
    backgroundColor: '#3B82F6',
  },
  modalButtonTextCancel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
  },
  modalButtonTextConfirm: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});

