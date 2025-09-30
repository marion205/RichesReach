import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  RefreshControl,
  ActivityIndicator,
  Switch,
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import Toast from 'react-native-toast-message';
import {
  GET_RISK_SUMMARY,
  GET_ACTIVE_POSITIONS,
  CREATE_POSITION,
  CHECK_POSITION_EXITS,
  UPDATE_RISK_SETTINGS,
  RiskSummary,
  Position,
  CreatePositionResponse,
  CheckExitsResponse,
} from '../../../graphql/riskManagement';

interface RiskManagementScreenProps {
  navigateTo?: (screen: string) => void;
}

export default function RiskManagementScreen({ navigateTo }: RiskManagementScreenProps) {
  const [refreshing, setRefreshing] = useState(false);
  const [riskLevel, setRiskLevel] = useState('MODERATE');
  const [accountValue, setAccountValue] = useState('100000');

  const { data: riskData, loading: riskLoading, refetch: refetchRisk } = useQuery(GET_RISK_SUMMARY, {
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const { data: positionsData, loading: positionsLoading, refetch: refetchPositions } = useQuery(GET_ACTIVE_POSITIONS, {
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const [createPosition, { loading: creatingPosition }] = useMutation(CREATE_POSITION);
  const [checkExits, { loading: checkingExits }] = useMutation(CHECK_POSITION_EXITS);
  const [updateRiskSettings, { loading: updatingSettings }] = useMutation(UPDATE_RISK_SETTINGS);

  const riskSummary: RiskSummary | null = riskData?.riskSummary || null;
  const activePositions: Position[] = positionsData?.getActivePositions || [];

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([refetchRisk(), refetchPositions()]);
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleCreateTestPosition = async () => {
    try {
      const result = await createPosition({
        variables: {
          symbol: 'AAPL',
          side: 'LONG',
          price: 150.0,
          quantity: 0, // Let system calculate optimal size
          atr: 2.0,
          sector: 'Technology',
          confidence: 0.8,
        },
      });

      if (result.data?.createPosition?.success) {
        Toast.show({
          type: 'success',
          text1: 'Position Created',
          text2: `Created ${result.data.createPosition.position?.quantity} shares of ${result.data.createPosition.position?.symbol}`,
        });
        await refetchPositions();
        await refetchRisk();
      } else {
        Toast.show({
          type: 'error',
          text1: 'Position Creation Failed',
          text2: result.data?.createPosition?.message || 'Unknown error',
        });
      }
    } catch (error: any) {
      Toast.show({
        type: 'error',
        text1: 'Error',
        text2: error.message,
      });
    }
  };

  const handleCheckExits = async () => {
    try {
      // Mock current prices for testing
      const currentPrices = {
        'AAPL': 152.0,
        'MSFT': 380.0,
        'GOOGL': 2800.0,
      };

      const result = await checkExits({
        variables: { currentPrices },
      });

      if (result.data?.checkPositionExits?.success) {
        const exitedCount = result.data.checkPositionExits.exited_positions.length;
        if (exitedCount > 0) {
          Toast.show({
            type: 'info',
            text1: 'Positions Exited',
            text2: `${exitedCount} positions were closed`,
          });
        } else {
          Toast.show({
            type: 'info',
            text1: 'No Exits',
            text2: 'No positions met exit conditions',
          });
        }
        await refetchPositions();
        await refetchRisk();
      }
    } catch (error: any) {
      Toast.show({
        type: 'error',
        text1: 'Error',
        text2: error.message,
      });
    }
  };

  const handleUpdateRiskSettings = async () => {
    try {
      const result = await updateRiskSettings({
        variables: {
          accountValue: parseFloat(accountValue),
          riskLevel: riskLevel,
        },
      });

      if (result.data?.updateRiskSettings?.success) {
        Toast.show({
          type: 'success',
          text1: 'Settings Updated',
          text2: 'Risk settings have been updated',
        });
        await refetchRisk();
      }
    } catch (error: any) {
      Toast.show({
        type: 'error',
        text1: 'Error',
        text2: error.message,
      });
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  if (riskLoading || positionsLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading risk data...</Text>
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
              <Text style={styles.title}>Risk Management</Text>
              <Text style={styles.subtitle}>Position Limits & Stop Losses</Text>
            </View>
          </View>
        </View>
      </View>

      {/* Risk Summary Section */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Risk Summary</Text>
          <TouchableOpacity
            style={styles.infoButton}
            onPress={() => Alert.alert(
              'Risk Summary',
              'Shows your current risk exposure and limits:\n\n• Account Value: Your total trading capital\n• Daily P&L: Today\'s profit/loss\n• Active Positions: Number of open trades\n• Total Exposure: Capital at risk\n• Risk Level: Your current risk tolerance setting'
            )}
          >
            <Text style={styles.infoButtonText}>ℹ️</Text>
          </TouchableOpacity>
        </View>
        {riskSummary ? (
          <View style={styles.summaryCard}>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Account Value:</Text>
              <Text style={styles.summaryValue}>{formatCurrency(riskSummary.accountValue)}</Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Daily P&L:</Text>
              <Text style={[
                styles.summaryValue,
                { color: riskSummary.dailyPnl >= 0 ? '#4CAF50' : '#F44336' }
              ]}>
                {formatCurrency(riskSummary.dailyPnl)} ({formatPercentage(riskSummary.dailyPnlPct)})
              </Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Active Positions:</Text>
              <Text style={styles.summaryValue}>{riskSummary.activePositions}</Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Total Exposure:</Text>
              <Text style={styles.summaryValue}>
                {formatCurrency(riskSummary.totalExposure)} ({formatPercentage(riskSummary.exposurePct)})
              </Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Risk Level:</Text>
              <Text style={styles.summaryValue}>{riskSummary.riskLevel}</Text>
            </View>
          </View>
        ) : (
          <Text style={styles.errorText}>Failed to load risk summary</Text>
        )}
      </View>

      {/* Risk Settings Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Risk Settings</Text>
        <View style={styles.settingsCard}>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>Account Value:</Text>
            <Text style={styles.settingValue}>{formatCurrency(parseFloat(accountValue))}</Text>
          </View>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>Risk Level:</Text>
            <Text style={styles.settingValue}>{riskLevel}</Text>
          </View>
          {riskSummary && (
            <>
              <View style={styles.settingRow}>
                <Text style={styles.settingLabel}>Max Position Size:</Text>
                <Text style={styles.settingValue}>{formatPercentage(riskSummary.riskLimits.maxPositionSize)}</Text>
              </View>
              <View style={styles.settingRow}>
                <Text style={styles.settingLabel}>Max Daily Loss:</Text>
                <Text style={styles.settingValue}>{formatPercentage(riskSummary.riskLimits.maxDailyLoss)}</Text>
              </View>
              <View style={styles.settingRow}>
                <Text style={styles.settingLabel}>Max Concurrent Trades:</Text>
                <Text style={styles.settingValue}>{riskSummary.riskLimits.maxConcurrentTrades}</Text>
              </View>
            </>
          )}
        </View>
      </View>

      {/* Active Positions Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Active Positions ({activePositions.length})</Text>
        {activePositions.length > 0 ? (
          activePositions.map((position, index) => (
            <View key={index} style={styles.positionCard}>
              <View style={styles.positionHeader}>
                <Text style={styles.positionSymbol}>{position.symbol}</Text>
                <Text style={[
                  styles.positionSide,
                  { color: position.side === 'LONG' ? '#4CAF50' : '#F44336' }
                ]}>
                  {position.side}
                </Text>
              </View>
              <View style={styles.positionDetails}>
                <Text style={styles.positionDetail}>
                  Entry: {formatCurrency(position.entryPrice)} × {position.quantity}
                </Text>
                <Text style={styles.positionDetail}>
                  Stop Loss: {formatCurrency(position.stopLossPrice)}
                </Text>
                <Text style={styles.positionDetail}>
                  Take Profit: {formatCurrency(position.takeProfitPrice)}
                </Text>
                <Text style={styles.positionDetail}>
                  Time Remaining: {position.timeRemainingMinutes} min
                </Text>
              </View>
            </View>
          ))
        ) : (
          <Text style={styles.noDataText}>No active positions</Text>
        )}
      </View>

      {/* Action Buttons */}
      <View style={styles.actionSection}>
        <TouchableOpacity
          style={[styles.actionButton, creatingPosition && styles.actionButtonDisabled]}
          onPress={handleCreateTestPosition}
          disabled={creatingPosition}
        >
          {creatingPosition ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.actionButtonText}>Create Test Position</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, checkingExits && styles.actionButtonDisabled]}
          onPress={handleCheckExits}
          disabled={checkingExits}
        >
          {checkingExits ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.actionButtonText}>Check Exits</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, updatingSettings && styles.actionButtonDisabled]}
          onPress={handleUpdateRiskSettings}
          disabled={updatingSettings}
        >
          {updatingSettings ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.actionButtonText}>Update Settings</Text>
          )}
        </TouchableOpacity>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  section: {
    margin: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
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
  summaryCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  summaryLabel: {
    fontSize: 16,
    color: '#666',
  },
  summaryValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  settingsCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  settingLabel: {
    fontSize: 16,
    color: '#666',
  },
  settingValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  positionCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  positionSymbol: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  positionSide: {
    fontSize: 16,
    fontWeight: '600',
  },
  positionDetails: {
    marginTop: 8,
  },
  positionDetail: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  noDataText: {
    textAlign: 'center',
    fontSize: 16,
    color: '#666',
    fontStyle: 'italic',
    marginTop: 20,
  },
  errorText: {
    textAlign: 'center',
    fontSize: 16,
    color: '#F44336',
    marginTop: 20,
  },
  actionSection: {
    margin: 16,
    gap: 12,
  },
  actionButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionButtonDisabled: {
    backgroundColor: '#ccc',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
