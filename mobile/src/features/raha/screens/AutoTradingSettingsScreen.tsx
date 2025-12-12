/**
 * Auto-Trading Settings Screen
 * Configure RAHA auto-trading settings for automatic signal execution
 */
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  TextInput,
  SafeAreaView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useQuery, useMutation } from '@apollo/client';
import { GET_AUTO_TRADING_SETTINGS, UPDATE_AUTO_TRADING_SETTINGS } from '../../../graphql/raha';
import logger from '../../../utils/logger';
import type {
  ExtendedQuery,
  ExtendedMutation,
  AutoTradingSettingsType,
} from '../../../generated/graphql';
import Slider from '@react-native-community/slider';

interface AutoTradingSettingsScreenProps {
  navigateTo?: (screen: string, params?: any) => void;
  onBack?: () => void;
}

export default function AutoTradingSettingsScreen({
  navigateTo,
  onBack,
}: AutoTradingSettingsScreenProps) {
  // ✅ Typed queries and mutations (now using generated types!)
  type AutoTradingSettingsQuery = Pick<ExtendedQuery, 'autoTradingSettings'>;
  type UpdateAutoTradingSettingsMutation = Pick<ExtendedMutation, 'updateAutoTradingSettings'>;
  
  const { data, loading, error, refetch } = useQuery<AutoTradingSettingsQuery>(GET_AUTO_TRADING_SETTINGS);
  const [updateSettings, { loading: updating }] = useMutation<UpdateAutoTradingSettingsMutation>(UPDATE_AUTO_TRADING_SETTINGS, {
    onCompleted: () => {
      Alert.alert('Success', 'Auto-trading settings updated!');
      refetch();
    },
    onError: err => {
      logger.error('Error updating auto-trading settings:', err);
      Alert.alert('Error', 'Failed to update settings. Please try again.');
    },
  });

  const settings = data?.autoTradingSettings;

  // Local state for form
  const [enabled, setEnabled] = useState(settings?.enabled ?? false);
  const [minConfidence, setMinConfidence] = useState(
    parseFloat(settings?.minConfidenceThreshold) || 0.75
  );
  const [positionSizingMethod, setPositionSizingMethod] = useState<
    'FIXED' | 'PERCENTAGE' | 'RISK_BASED'
  >(settings?.positionSizingMethod ?? 'PERCENTAGE');
  const [fixedPositionSize, setFixedPositionSize] = useState(
    parseFloat(settings?.fixedPositionSize) || 1000
  );
  const [positionSizePercent, setPositionSizePercent] = useState(
    parseFloat(settings?.positionSizePercent) || 2.0
  );
  const [riskPerTradePercent, setRiskPerTradePercent] = useState(
    parseFloat(settings?.riskPerTradePercent) || 1.0
  );
  const [maxPositionSizePercent, setMaxPositionSizePercent] = useState(
    parseFloat(settings?.maxPositionSizePercent) || 10.0
  );
  const [maxDailyLossPercent, setMaxDailyLossPercent] = useState(
    parseFloat(settings?.maxDailyLossPercent) || 5.0
  );
  const [maxConcurrentPositions, setMaxConcurrentPositions] = useState(
    parseInt(settings?.maxConcurrentPositions) || 5
  );
  const [onlyMarketHours, setOnlyMarketHours] = useState(settings?.onlyTradeMarketHours ?? true);
  const [allowedSymbols, setAllowedSymbols] = useState(settings?.allowedSymbols?.join(', ') ?? '');
  const [blockedSymbols, setBlockedSymbols] = useState(settings?.blockedSymbols?.join(', ') ?? '');

  // Update local state when data loads
  useEffect(() => {
    if (settings) {
      setEnabled(settings.enabled ?? false);
      setMinConfidence(parseFloat(settings.minConfidenceThreshold) || 0.75);
      setPositionSizingMethod(settings.positionSizingMethod ?? 'PERCENTAGE');
      setFixedPositionSize(parseFloat(settings.fixedPositionSize) || 1000);
      setPositionSizePercent(parseFloat(settings.positionSizePercent) || 2.0);
      setRiskPerTradePercent(parseFloat(settings.riskPerTradePercent) || 1.0);
      setMaxPositionSizePercent(parseFloat(settings.maxPositionSizePercent) || 10.0);
      setMaxDailyLossPercent(parseFloat(settings.maxDailyLossPercent) || 5.0);
      setMaxConcurrentPositions(parseInt(settings.maxConcurrentPositions) || 5);
      setOnlyMarketHours(settings.onlyTradeMarketHours ?? true);
      setAllowedSymbols(settings.allowedSymbols?.join(', ') ?? '');
      setBlockedSymbols(settings.blockedSymbols?.join(', ') ?? '');
    }
  }, [settings]);

  const handleSave = async () => {
    try {
      await updateSettings({
        variables: {
          enabled,
          minConfidenceThreshold: minConfidence ? parseFloat(minConfidence.toFixed(2)) : 0.75,
          positionSizingMethod,
          fixedPositionSize: fixedPositionSize ? parseFloat(fixedPositionSize.toFixed(2)) : 1000,
          positionSizePercent: positionSizePercent
            ? parseFloat(positionSizePercent.toFixed(2))
            : 2.0,
          riskPerTradePercent: riskPerTradePercent
            ? parseFloat(riskPerTradePercent.toFixed(2))
            : 1.0,
          maxPositionSizePercent: maxPositionSizePercent
            ? parseFloat(maxPositionSizePercent.toFixed(2))
            : 10.0,
          maxDailyLossPercent: maxDailyLossPercent
            ? parseFloat(maxDailyLossPercent.toFixed(2))
            : 5.0,
          maxConcurrentPositions: maxConcurrentPositions
            ? parseInt(maxConcurrentPositions.toString())
            : 5,
          onlyTradeMarketHours: onlyMarketHours,
          allowedSymbols: allowedSymbols
            .split(',')
            .map(s => s.trim().toUpperCase())
            .filter(Boolean),
          blockedSymbols: blockedSymbols
            .split(',')
            .map(s => s.trim().toUpperCase())
            .filter(Boolean),
        },
      });
    } catch (error) {
      logger.error('Error saving auto-trading settings:', error);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#1D4ED8" />
        <Text style={styles.loadingText}>Loading settings...</Text>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={styles.errorContainer}>
        <Text style={styles.errorText}>Error loading settings: {error.message}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={onBack}>
            <Icon name="arrow-left" size={24} color="#111827" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Auto-Trading Settings</Text>
          <View style={{ width: 24 }} />
        </View>

        {/* Warning Banner */}
        <View style={styles.warningBanner}>
          <Icon name="alert-triangle" size={20} color="#F59E0B" />
          <Text style={styles.warningText}>
            Auto-trading executes real trades with real money. Ensure you understand the risks and
            have completed broker account setup.
          </Text>
        </View>

        {/* Main Toggle */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Auto-Trading</Text>
          <View style={styles.preferenceItem}>
            <View style={styles.preferenceLabelContainer}>
              <Text style={styles.preferenceLabel}>Enable Auto-Trading</Text>
              <Text style={styles.preferenceDescription}>
                Automatically execute RAHA signals when confidence threshold is met
              </Text>
            </View>
            <Switch onValueChange={setEnabled} value={enabled} />
          </View>
        </View>

        {enabled && (
          <>
            {/* Confidence Threshold */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Signal Filters</Text>
              <View style={styles.preferenceItem}>
                <Text style={styles.preferenceLabel}>
                  Min. Confidence Threshold ({Math.round(minConfidence * 100)}%)
                </Text>
                <Slider
                  style={styles.slider}
                  minimumValue={0.5}
                  maximumValue={0.95}
                  step={0.05}
                  value={minConfidence}
                  onValueChange={setMinConfidence}
                  minimumTrackTintColor="#1D4ED8"
                  maximumTrackTintColor="#D1D5DB"
                  thumbTintColor="#1D4ED8"
                />
              </View>
            </View>

            {/* Position Sizing */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Position Sizing</Text>
              <View style={styles.preferenceItem}>
                <Text style={styles.preferenceLabel}>Sizing Method</Text>
                <View style={styles.methodButtons}>
                  <TouchableOpacity
                    style={[
                      styles.methodButton,
                      positionSizingMethod === 'FIXED' && styles.methodButtonActive,
                    ]}
                    onPress={() => setPositionSizingMethod('FIXED')}
                  >
                    <Text
                      style={[
                        styles.methodButtonText,
                        positionSizingMethod === 'FIXED' && styles.methodButtonTextActive,
                      ]}
                    >
                      Fixed $
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[
                      styles.methodButton,
                      positionSizingMethod === 'PERCENTAGE' && styles.methodButtonActive,
                    ]}
                    onPress={() => setPositionSizingMethod('PERCENTAGE')}
                  >
                    <Text
                      style={[
                        styles.methodButtonText,
                        positionSizingMethod === 'PERCENTAGE' && styles.methodButtonTextActive,
                      ]}
                    >
                      % Equity
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[
                      styles.methodButton,
                      positionSizingMethod === 'RISK_BASED' && styles.methodButtonActive,
                    ]}
                    onPress={() => setPositionSizingMethod('RISK_BASED')}
                  >
                    <Text
                      style={[
                        styles.methodButtonText,
                        positionSizingMethod === 'RISK_BASED' && styles.methodButtonTextActive,
                      ]}
                    >
                      Risk-Based
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>

              {positionSizingMethod === 'FIXED' && (
                <View style={styles.preferenceItem}>
                  <Text style={styles.preferenceLabel}>Fixed Position Size ($)</Text>
                  <TextInput
                    style={styles.textInput}
                    value={fixedPositionSize.toString()}
                    onChangeText={text => setFixedPositionSize(parseFloat(text) || 0)}
                    keyboardType="numeric"
                    placeholder="1000"
                  />
                </View>
              )}

              {positionSizingMethod === 'PERCENTAGE' && (
                <View style={styles.preferenceItem}>
                  <Text style={styles.preferenceLabel}>
                    Position Size ({positionSizePercent ? positionSizePercent.toFixed(1) : '2.0'}%
                    of equity)
                  </Text>
                  <Slider
                    style={styles.slider}
                    minimumValue={0.5}
                    maximumValue={10}
                    step={0.5}
                    value={positionSizePercent || 2.0}
                    onValueChange={setPositionSizePercent}
                    minimumTrackTintColor="#1D4ED8"
                    maximumTrackTintColor="#D1D5DB"
                    thumbTintColor="#1D4ED8"
                  />
                </View>
              )}

              {positionSizingMethod === 'RISK_BASED' && (
                <>
                  <View style={styles.preferenceItem}>
                    <Text style={styles.preferenceLabel}>
                      Risk Per Trade ({riskPerTradePercent ? riskPerTradePercent.toFixed(1) : '1.0'}
                      % of equity)
                    </Text>
                    <Slider
                      style={styles.slider}
                      minimumValue={0.5}
                      maximumValue={5}
                      step={0.5}
                      value={riskPerTradePercent || 1.0}
                      onValueChange={setRiskPerTradePercent}
                      minimumTrackTintColor="#1D4ED8"
                      maximumTrackTintColor="#D1D5DB"
                      thumbTintColor="#1D4ED8"
                    />
                  </View>
                  <View style={styles.preferenceItem}>
                    <Text style={styles.preferenceLabel}>
                      Max Position Size (
                      {maxPositionSizePercent ? maxPositionSizePercent.toFixed(1) : '10.0'}% of
                      equity)
                    </Text>
                    <Slider
                      style={styles.slider}
                      minimumValue={5}
                      maximumValue={25}
                      step={1}
                      value={maxPositionSizePercent || 10.0}
                      onValueChange={setMaxPositionSizePercent}
                      minimumTrackTintColor="#1D4ED8"
                      maximumTrackTintColor="#D1D5DB"
                      thumbTintColor="#1D4ED8"
                    />
                  </View>
                </>
              )}
            </View>

            {/* Risk Limits */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Risk Limits</Text>
              <View style={styles.preferenceItem}>
                <Text style={styles.preferenceLabel}>
                  Max Daily Loss ({maxDailyLossPercent ? maxDailyLossPercent.toFixed(1) : '5.0'}
                  %)
                </Text>
                <Text style={styles.preferenceDescription}>
                  Stop auto-trading if daily loss exceeds this percentage (0 = disabled)
                </Text>
                <Slider
                  style={styles.slider}
                  minimumValue={0}
                  maximumValue={10}
                  step={0.5}
                  value={maxDailyLossPercent || 5.0}
                  onValueChange={setMaxDailyLossPercent}
                  minimumTrackTintColor="#1D4ED8"
                  maximumTrackTintColor="#D1D5DB"
                  thumbTintColor="#1D4ED8"
                />
              </View>
              <View style={styles.preferenceItem}>
                <Text style={styles.preferenceLabel}>Max Concurrent Positions</Text>
                <TextInput
                  style={styles.textInput}
                  value={maxConcurrentPositions.toString()}
                  onChangeText={text => setMaxConcurrentPositions(parseInt(text) || 0)}
                  keyboardType="numeric"
                  placeholder="5"
                />
              </View>
            </View>

            {/* Trading Hours */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Trading Hours</Text>
              <View style={styles.preferenceItem}>
                <Text style={styles.preferenceLabel}>Only Trade Market Hours</Text>
                <Text style={styles.preferenceDescription}>
                  Only execute trades during market hours (9:30 AM - 4:00 PM ET)
                </Text>
                <Switch onValueChange={setOnlyMarketHours} value={onlyMarketHours} />
              </View>
            </View>

            {/* Symbol Filters */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Symbol Filters</Text>
              <View style={styles.preferenceItem}>
                <Text style={styles.preferenceLabel}>Allowed Symbols (comma-separated)</Text>
                <Text style={styles.preferenceDescription}>
                  Only trade these symbols (leave empty for all)
                </Text>
                <TextInput
                  style={styles.textInput}
                  value={allowedSymbols}
                  onChangeText={setAllowedSymbols}
                  placeholder="e.g., AAPL, MSFT, NVDA"
                  placeholderTextColor="#9CA3AF"
                  autoCapitalize="characters"
                />
              </View>
              <View style={styles.preferenceItem}>
                <Text style={styles.preferenceLabel}>Blocked Symbols (comma-separated)</Text>
                <Text style={styles.preferenceDescription}>Never trade these symbols</Text>
                <TextInput
                  style={styles.textInput}
                  value={blockedSymbols}
                  onChangeText={setBlockedSymbols}
                  placeholder="e.g., TSLA, GME"
                  placeholderTextColor="#9CA3AF"
                  autoCapitalize="characters"
                />
              </View>
            </View>
          </>
        )}

        {/* Save Button */}
        <TouchableOpacity
          style={[styles.saveButton, updating && styles.saveButtonDisabled]}
          onPress={handleSave}
          disabled={updating}
        >
          {updating ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={styles.saveButtonText}>Save Settings</Text>
          )}
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#6B7280',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    padding: 20,
  },
  errorText: {
    fontSize: 16,
    color: '#EF4444',
    textAlign: 'center',
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#1D4ED8',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    paddingBottom: 32,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  warningBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    padding: 16,
    margin: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FCD34D',
  },
  warningText: {
    flex: 1,
    marginLeft: 12,
    fontSize: 14,
    color: '#92400E',
    lineHeight: 20,
  },
  section: {
    backgroundColor: '#FFFFFF',
    marginTop: 16,
    marginHorizontal: 16,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  preferenceItem: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  preferenceLabelContainer: {
    flex: 1,
  },
  preferenceLabel: {
    fontSize: 16,
    color: '#374151',
    fontWeight: '500',
    marginBottom: 4,
  },
  preferenceDescription: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  slider: {
    flex: 1,
    height: 40,
    marginTop: 8,
  },
  textInput: {
    flex: 1,
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 16,
    color: '#111827',
  },
  methodButtons: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  methodButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
  },
  methodButtonActive: {
    backgroundColor: '#1D4ED8',
    borderColor: '#1D4ED8',
  },
  methodButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  methodButtonTextActive: {
    color: '#FFFFFF',
  },
  saveButton: {
    backgroundColor: '#1D4ED8',
    paddingVertical: 14,
    marginHorizontal: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 24,
    shadowColor: '#1D4ED8',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 5,
    elevation: 5,
  },
  saveButtonDisabled: {
    backgroundColor: '#9CA3AF',
  },
  saveButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
});
