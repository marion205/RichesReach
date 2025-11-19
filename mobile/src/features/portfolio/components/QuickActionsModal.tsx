/**
 * QuickActionsModal
 * Quick action menu triggered by double tap on Constellation Orb
 */

import React from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Feather';
import { MoneySnapshot } from '../services/MoneySnapshotService';

interface QuickAction {
  id: string;
  title: string;
  icon: string;
  color: string;
  onPress: () => void;
}

interface QuickActionsModalProps {
  visible: boolean;
  onClose: () => void;
  snapshot: MoneySnapshot;
  onNavigate?: (screen: string) => void;
}

export const QuickActionsModal: React.FC<QuickActionsModalProps> = ({
  visible,
  onClose,
  snapshot,
  onNavigate,
}) => {
  const actions: QuickAction[] = [
    {
      id: 'add-funds',
      title: 'Add Funds',
      icon: 'plus-circle',
      color: '#34C759',
      onPress: () => {
        onNavigate?.('trading');
        onClose();
      },
    },
    {
      id: 'transfer',
      title: 'Transfer Money',
      icon: 'arrow-left-right',
      color: '#007AFF',
      onPress: () => {
        onNavigate?.('portfolio-management');
        onClose();
      },
    },
    {
      id: 'analyze',
      title: 'Analyze Portfolio',
      icon: 'bar-chart-2',
      color: '#FF9500',
      onPress: () => {
        onNavigate?.('premium-analytics');
        onClose();
      },
    },
    {
      id: 'goals',
      title: 'Set Goals',
      icon: 'target',
      color: '#AF52DE',
      onPress: () => {
        // Future enhancement: Navigate to investment goals screen
        onClose();
      },
    },
    {
      id: 'insights',
      title: 'View Insights',
      icon: 'lightbulb',
      color: '#FF3B30',
      onPress: () => {
        onNavigate?.('oracle-insights');
        onClose();
      },
    },
    {
      id: 'export',
      title: 'Export Data',
      icon: 'download',
      color: '#8E8E93',
      onPress: () => {
        // Future enhancement: Export portfolio data as PDF/CSV
        onClose();
      },
    },
  ];

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`;
    if (amount >= 1000) return `$${(amount / 1000).toFixed(1)}K`;
    return `$${amount.toFixed(0)}`;
  };

  return (
    <Modal
      visible={visible}
      animationType="fade"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
          <View style={styles.header}>
            <Text style={styles.title}>Quick Actions</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Icon name="x" size={24} color="#8E8E93" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            {/* Quick Stats */}
            <View style={styles.statsCard}>
              <View style={styles.statItem}>
                <Text style={styles.statLabel}>Net Worth</Text>
                <Text style={styles.statValue}>
                  {formatCurrency(snapshot?.netWorth ?? 0)}
                </Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statLabel}>Cash Flow</Text>
                <Text style={[styles.statValue, { color: (snapshot?.cashflow?.delta ?? 0) >= 0 ? '#34C759' : '#FF3B30' }]}>
                  {formatCurrency(Math.abs(snapshot?.cashflow?.delta ?? 0))}
                </Text>
              </View>
            </View>

            {/* Action Grid */}
            <View style={styles.actionsGrid}>
              {actions.map((action) => (
                <TouchableOpacity
                  key={action.id}
                  style={[styles.actionCard, { borderLeftColor: action.color }]}
                  onPress={action.onPress}
                  activeOpacity={0.7}
                >
                  <View style={[styles.actionIcon, { backgroundColor: `${action.color}20` }]}>
                    <Icon name={action.icon as any} size={24} color={action.color} />
                  </View>
                  <Text style={styles.actionTitle}>{action.title}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </ScrollView>
        </SafeAreaView>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  container: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '80%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  closeButton: {
    padding: 4,
  },
  content: {
    padding: 20,
  },
  statsCard: {
    flexDirection: 'row',
    backgroundColor: '#F8F9FA',
    borderRadius: 16,
    padding: 16,
    marginBottom: 24,
    gap: 16,
  },
  statItem: {
    flex: 1,
  },
  statLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  actionCard: {
    width: '48%',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  actionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
});

export default QuickActionsModal;

