/**
 * Notification Preferences Screen
 * Configure RAHA push notification settings
 */
import React, { useState } from 'react';
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
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useQuery, useMutation, gql } from '@apollo/client';
// GraphQL queries/mutations for notification preferences - commented out as they don't exist yet
// import {
//   GET_NOTIFICATION_PREFERENCES,
//   UPDATE_NOTIFICATION_PREFERENCES,
// } from '../../../graphql/raha';
import logger from '../../../utils/logger';
import type {
  ExtendedQuery,
  ExtendedMutation,
} from '../../../generated/graphql';
import RAHANotificationService from '../../../services/RAHANotificationService';

interface NotificationPreferencesScreenProps {
  navigateTo?: (screen: string, params?: any) => void;
  onBack?: () => void;
}

export default function NotificationPreferencesScreen({
  navigateTo,
  onBack,
}: NotificationPreferencesScreenProps) {
  // ✅ Typed queries and mutations (now using generated types!)
  type NotificationPreferencesQuery = Pick<ExtendedQuery, 'notificationPreferences'>;
  type UpdateNotificationPreferencesMutation = Pick<ExtendedMutation, 'updateNotificationPreferences'>;
  
  // GraphQL queries/mutations commented out as they don't exist yet
  // Using placeholder queries/mutations
  const PLACEHOLDER_QUERY = gql`query { __typename }`;
  const PLACEHOLDER_MUTATION = gql`mutation { __typename }`;
  const { data, loading, refetch } = useQuery<NotificationPreferencesQuery>(PLACEHOLDER_QUERY, { skip: true });
  const [updatePreferences, { loading: updating }] = useMutation<UpdateNotificationPreferencesMutation>(PLACEHOLDER_MUTATION);

  // Initialize RAHA notification service when component mounts
  React.useEffect(() => {
    const initNotifications = async () => {
      try {
        await RAHANotificationService.initialize(updatePreferences);
      } catch (error) {
        logger.error('Error initializing RAHA notifications:', error);
      }
    };
    initNotifications();
  }, []);

  const prefs = data?.notificationPreferences;

  // Local state for form
  const [pushEnabled, setPushEnabled] = useState(prefs?.pushEnabled ?? true);
  const [signalEnabled, setSignalEnabled] = useState(prefs?.signalNotificationsEnabled ?? true);
  const [signalThreshold, setSignalThreshold] = useState(prefs?.signalConfidenceThreshold ?? 0.7);
  const [signalSymbols, setSignalSymbols] = useState(prefs?.signalSymbols?.join(', ') ?? '');
  const [backtestEnabled, setBacktestEnabled] = useState(
    prefs?.backtestNotificationsEnabled ?? true
  );
  const [backtestSuccessOnly, setBacktestSuccessOnly] = useState(
    prefs?.backtestSuccessOnly ?? false
  );
  const [quietHoursEnabled, setQuietHoursEnabled] = useState(prefs?.quietHoursEnabled ?? false);
  const [quietHoursStart, setQuietHoursStart] = useState(prefs?.quietHoursStart ?? '22:00');
  const [quietHoursEnd, setQuietHoursEnd] = useState(prefs?.quietHoursEnd ?? '08:00');

  // Update local state when data loads
  React.useEffect(() => {
    if (prefs) {
      setPushEnabled(prefs.pushEnabled ?? true);
      setSignalEnabled(prefs.signalNotificationsEnabled ?? true);
      setSignalThreshold(prefs.signalConfidenceThreshold ?? 0.7);
      setSignalSymbols(prefs.signalSymbols?.join(', ') ?? '');
      setBacktestEnabled(prefs.backtestNotificationsEnabled ?? true);
      setBacktestSuccessOnly(prefs.backtestSuccessOnly ?? false);
      setQuietHoursEnabled(prefs.quietHoursEnabled ?? false);
      setQuietHoursStart(prefs.quietHoursStart ?? '22:00');
      setQuietHoursEnd(prefs.quietHoursEnd ?? '08:00');
    }
  }, [prefs]);

  const handleSave = async () => {
    try {
      const symbolsArray = signalSymbols
        .split(',')
        .map(s => s.trim().toUpperCase())
        .filter(s => s.length > 0);

      await updatePreferences({
        variables: {
          pushEnabled,
          signalNotificationsEnabled: signalEnabled,
          signalConfidenceThreshold: signalThreshold,
          signalSymbols: symbolsArray.length > 0 ? symbolsArray : null,
          backtestNotificationsEnabled: backtestEnabled,
          backtestSuccessOnly,
          quietHoursEnabled,
          quietHoursStart: quietHoursEnabled ? quietHoursStart : null,
          quietHoursEnd: quietHoursEnabled ? quietHoursEnd : null,
        },
      });

      Alert.alert('Success', 'Notification preferences saved');
      refetch();
    } catch (error) {
      logger.error('Error saving preferences:', error);
      Alert.alert('Error', 'Failed to save preferences');
    }
  };

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else if (navigateTo) {
      navigateTo('pro-labs');
    } else if (typeof window !== 'undefined') {
      if ((window as any).__navigateToGlobal) {
        (window as any).__navigateToGlobal('pro-labs');
      }
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text>Loading preferences...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={handleBack}>
          <Icon name="arrow-left" size={24} color="#111827" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Notification Settings</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.content}>
        {/* Push Notifications */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Push Notifications</Text>
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Enable Push Notifications</Text>
              <Text style={styles.settingDescription}>Receive notifications on your device</Text>
            </View>
            <Switch
              value={pushEnabled}
              onValueChange={setPushEnabled}
              trackColor={{ false: '#D1D5DB', true: '#3B82F6' }}
            />
          </View>
        </View>

        {/* Signal Notifications */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Signal Notifications</Text>
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Signal Alerts</Text>
              <Text style={styles.settingDescription}>
                Get notified when high-confidence signals are generated
              </Text>
            </View>
            <Switch
              value={signalEnabled}
              onValueChange={setSignalEnabled}
              disabled={!pushEnabled}
              trackColor={{ false: '#D1D5DB', true: '#3B82F6' }}
            />
          </View>

          {signalEnabled && (
            <>
              <View style={styles.settingRow}>
                <View style={styles.settingInfo}>
                  <Text style={styles.settingLabel}>Confidence Threshold</Text>
                  <Text style={styles.settingDescription}>
                    Only notify for signals above this confidence (0.0 - 1.0)
                  </Text>
                </View>
                <TextInput
                  style={styles.numberInput}
                  value={signalThreshold.toString()}
                  onChangeText={text => {
                    const num = parseFloat(text);
                    if (!isNaN(num) && num >= 0 && num <= 1) {
                      setSignalThreshold(num);
                    }
                  }}
                  keyboardType="decimal-pad"
                  placeholder="0.70"
                />
              </View>

              <View style={styles.settingRow}>
                <View style={styles.settingInfo}>
                  <Text style={styles.settingLabel}>Symbols (Optional)</Text>
                  <Text style={styles.settingDescription}>
                    Comma-separated list (e.g., AAPL, TSLA). Leave empty for all symbols.
                  </Text>
                </View>
                <TextInput
                  style={styles.textInput}
                  value={signalSymbols}
                  onChangeText={setSignalSymbols}
                  placeholder="AAPL, TSLA, MSFT"
                  autoCapitalize="characters"
                />
              </View>
            </>
          )}
        </View>

        {/* Backtest Notifications */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Backtest Notifications</Text>
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Backtest Alerts</Text>
              <Text style={styles.settingDescription}>Get notified when backtests complete</Text>
            </View>
            <Switch
              value={backtestEnabled}
              onValueChange={setBacktestEnabled}
              disabled={!pushEnabled}
              trackColor={{ false: '#D1D5DB', true: '#3B82F6' }}
            />
          </View>

          {backtestEnabled && (
            <View style={styles.settingRow}>
              <View style={styles.settingInfo}>
                <Text style={styles.settingLabel}>Success Only</Text>
                <Text style={styles.settingDescription}>
                  Only notify for backtests with win rate &gt; 50%
                </Text>
              </View>
              <Switch
                value={backtestSuccessOnly}
                onValueChange={setBacktestSuccessOnly}
                trackColor={{ false: '#D1D5DB', true: '#3B82F6' }}
              />
            </View>
          )}
        </View>

        {/* Quiet Hours */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quiet Hours</Text>
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Enable Quiet Hours</Text>
              <Text style={styles.settingDescription}>
                Don't send notifications during these hours
              </Text>
            </View>
            <Switch
              value={quietHoursEnabled}
              onValueChange={setQuietHoursEnabled}
              disabled={!pushEnabled}
              trackColor={{ false: '#D1D5DB', true: '#3B82F6' }}
            />
          </View>

          {quietHoursEnabled && (
            <>
              <View style={styles.settingRow}>
                <View style={styles.settingInfo}>
                  <Text style={styles.settingLabel}>Start Time</Text>
                  <Text style={styles.settingDescription}>HH:MM format</Text>
                </View>
                <TextInput
                  style={styles.timeInput}
                  value={quietHoursStart}
                  onChangeText={setQuietHoursStart}
                  placeholder="22:00"
                />
              </View>

              <View style={styles.settingRow}>
                <View style={styles.settingInfo}>
                  <Text style={styles.settingLabel}>End Time</Text>
                  <Text style={styles.settingDescription}>HH:MM format</Text>
                </View>
                <TextInput
                  style={styles.timeInput}
                  value={quietHoursEnd}
                  onChangeText={setQuietHoursEnd}
                  placeholder="08:00"
                />
              </View>
            </>
          )}
        </View>

        <TouchableOpacity
          style={[styles.saveButton, updating && styles.saveButtonDisabled]}
          onPress={handleSave}
          disabled={updating}
        >
          <Text style={styles.saveButtonText}>{updating ? 'Saving...' : 'Save Preferences'}</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  settingInfo: {
    flex: 1,
    marginRight: 16,
  },
  settingLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#111827',
    marginBottom: 4,
  },
  settingDescription: {
    fontSize: 12,
    color: '#6B7280',
  },
  numberInput: {
    width: 80,
    height: 40,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 14,
    textAlign: 'center',
  },
  textInput: {
    flex: 1,
    height: 40,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 14,
  },
  timeInput: {
    width: 100,
    height: 40,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 14,
  },
  saveButton: {
    backgroundColor: '#3B82F6',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 24,
    marginBottom: 32,
  },
  saveButtonDisabled: {
    opacity: 0.5,
  },
  saveButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
