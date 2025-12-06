/**
 * Risk Monitor Card Component
 * Real-time monitoring of DeFi positions with alerts
 */

import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import RiskEngineService, { PositionRisk, RiskAlert } from '../../services/RiskEngineService';
import * as Notifications from 'expo-notifications';

interface RiskMonitorCardProps {
  onPositionClick?: (positionId: string) => void;
}

export default function RiskMonitorCard({ onPositionClick }: RiskMonitorCardProps) {
  const [positions, setPositions] = useState<PositionRisk[]>([]);
  const [summary, setSummary] = useState({
    totalPositions: 0,
    safe: 0,
    warning: 0,
    critical: 0,
    liquidated: 0,
    totalValue: 0,
  });
  const [monitoring, setMonitoring] = useState(false);

  useEffect(() => {
    // Setup notification handler
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }),
    });

    // Register for alerts
    const handleAlert = (alert: RiskAlert) => {
      handleRiskAlert(alert);
    };

    RiskEngineService.onAlert(handleAlert);

    // Load initial positions
    loadPositions();

    return () => {
      RiskEngineService.offAlert(handleAlert);
    };
  }, []);

  const loadPositions = () => {
    const allPositions = RiskEngineService.getPositions();
    setPositions(allPositions);
    setSummary(RiskEngineService.getRiskSummary());
  };

  const handleRiskAlert = async (alert: RiskAlert) => {
    // Show in-app alert
    if (alert.severity === 'critical' || alert.severity === 'high') {
      Alert.alert(
        alert.type.replace('_', ' ').toUpperCase(),
        alert.message,
        alert.actionRequired
          ? [
              { text: 'View Position', onPress: () => onPositionClick?.(alert.positionId) },
              { text: 'Dismiss' },
            ]
          : [{ text: 'OK' }]
      );
    }

    // Send push notification
    await Notifications.scheduleNotificationAsync({
      content: {
        title: alert.type.replace('_', ' ').toUpperCase(),
        body: alert.message,
        sound: true,
        priority: alert.severity === 'critical' ? 'max' : 'high',
      },
      trigger: null, // Immediate
    });
  };

  const startMonitoring = () => {
    RiskEngineService.startMonitoring(30000); // Check every 30 seconds
    setMonitoring(true);
  };

  const stopMonitoring = () => {
    RiskEngineService.stopMonitoring();
    setMonitoring(false);
  };

  const getRiskColor = (riskLevel: string): string => {
    switch (riskLevel) {
      case 'safe':
        return '#34C759';
      case 'warning':
        return '#FF9F0A';
      case 'critical':
        return '#FF3B30';
      case 'liquidated':
        return '#8E8E93';
      default:
        return '#8E8E93';
    }
  };

  const getRiskIcon = (riskLevel: string): string => {
    switch (riskLevel) {
      case 'safe':
        return 'check-circle';
      case 'warning':
        return 'alert-triangle';
      case 'critical':
        return 'alert-circle';
      case 'liquidated':
        return 'x-circle';
      default:
        return 'help-circle';
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Icon name="shield" size={20} color="#667eea" />
          <Text style={styles.title}>Risk Monitor</Text>
        </View>
        <TouchableOpacity
          style={[styles.monitorButton, monitoring && styles.monitorButtonActive]}
          onPress={monitoring ? stopMonitoring : startMonitoring}
        >
          <View style={[styles.monitorDot, monitoring && styles.monitorDotActive]} />
          <Text style={styles.monitorButtonText}>
            {monitoring ? 'Monitoring' : 'Start Monitor'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Risk Summary */}
      <View style={styles.summary}>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryValue}>{summary.totalPositions}</Text>
          <Text style={styles.summaryLabel}>Positions</Text>
        </View>
        <View style={styles.summaryItem}>
          <Text style={[styles.summaryValue, { color: '#34C759' }]}>{summary.safe}</Text>
          <Text style={styles.summaryLabel}>Safe</Text>
        </View>
        <View style={styles.summaryItem}>
          <Text style={[styles.summaryValue, { color: '#FF9F0A' }]}>{summary.warning}</Text>
          <Text style={styles.summaryLabel}>Warning</Text>
        </View>
        <View style={styles.summaryItem}>
          <Text style={[styles.summaryValue, { color: '#FF3B30' }]}>{summary.critical}</Text>
          <Text style={styles.summaryLabel}>Critical</Text>
        </View>
      </View>

      {/* Positions List */}
      {positions.length > 0 ? (
        <ScrollView style={styles.positionsList} showsVerticalScrollIndicator={false}>
          {positions.map((position) => (
            <TouchableOpacity
              key={position.positionId}
              style={styles.positionCard}
              onPress={() => onPositionClick?.(position.positionId)}
            >
              <View style={styles.positionHeader}>
                <View style={styles.positionInfo}>
                  <Text style={styles.positionProtocol}>{position.protocol}</Text>
                  <Text style={styles.positionAsset}>{position.asset}</Text>
                </View>
                <View style={[styles.riskBadge, { backgroundColor: getRiskColor(position.riskLevel) }]}>
                  <Icon name={getRiskIcon(position.riskLevel)} size={12} color="#FFFFFF" />
                  <Text style={styles.riskBadgeText}>{position.riskLevel.toUpperCase()}</Text>
                </View>
              </View>

              <View style={styles.positionStats}>
                <View style={styles.stat}>
                  <Text style={styles.statLabel}>Health Factor</Text>
                  <Text style={[styles.statValue, { color: getRiskColor(position.riskLevel) }]}>
                    {position.healthFactor.toFixed(2)}
                  </Text>
                </View>
                <View style={styles.stat}>
                  <Text style={styles.statLabel}>Value</Text>
                  <Text style={styles.statValue}>${position.currentValue.toFixed(2)}</Text>
                </View>
              </View>

              {position.estimatedLiquidationPrice && (
                <View style={styles.liquidationWarning}>
                  <Icon name="alert-triangle" size={12} color="#FF3B30" />
                  <Text style={styles.liquidationText}>
                    Liquidation at ${position.estimatedLiquidationPrice.toFixed(2)}
                  </Text>
                </View>
              )}
            </TouchableOpacity>
          ))}
        </ScrollView>
      ) : (
        <View style={styles.emptyState}>
          <Icon name="shield-off" size={48} color="#8E8E93" />
          <Text style={styles.emptyText}>No positions being monitored</Text>
          <Text style={styles.emptySubtext}>
            Add DeFi positions to start monitoring for liquidation risk
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    maxHeight: 500,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1a1a1a',
    marginLeft: 8,
  },
  monitorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F2F2F7',
  },
  monitorButtonActive: {
    backgroundColor: '#34C75915',
  },
  monitorDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#8E8E93',
    marginRight: 6,
  },
  monitorDotActive: {
    backgroundColor: '#34C759',
  },
  monitorButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  summary: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
    marginBottom: 16,
  },
  summaryItem: {
    alignItems: 'center',
  },
  summaryValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  summaryLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  positionsList: {
    maxHeight: 300,
  },
  positionCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  positionInfo: {
    flex: 1,
  },
  positionProtocol: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  positionAsset: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  riskBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    gap: 4,
  },
  riskBadgeText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '600',
  },
  positionStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 8,
  },
  stat: {
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 11,
    color: '#666',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  liquidationWarning: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FF3B3015',
    padding: 8,
    borderRadius: 6,
    marginTop: 8,
    gap: 6,
  },
  liquidationText: {
    fontSize: 11,
    color: '#FF3B30',
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    padding: 32,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginTop: 12,
  },
  emptySubtext: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
    textAlign: 'center',
  },
});

