/**
 * Statement-Date Utilization Planner
 * Shows per-card paydown recommendations optimized for statement close dates
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { StatementDatePlan } from '../types/CreditTypes';

interface StatementDatePlannerProps {
  plans: StatementDatePlan[];
  onCardPress?: (plan: StatementDatePlan) => void;
}

export const StatementDatePlanner: React.FC<StatementDatePlannerProps> = ({
  plans,
  onCardPress,
}) => {
  if (plans.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Icon name="credit-card" size={32} color="#8E8E93" />
        <Text style={styles.emptyText}>No credit cards linked</Text>
        <Text style={styles.emptySubtext}>
          Link a card to see statement-date optimization plans
        </Text>
      </View>
    );
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getDaysUntilClose = (days: number) => {
    if (days === 0) return 'Today';
    if (days === 1) return 'Tomorrow';
    if (days < 7) return `${days} days`;
    if (days < 30) return `${Math.floor(days / 7)} weeks`;
    return `${Math.floor(days / 30)} months`;
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Statement-Date Planner</Text>
          <Text style={styles.subtitle}>
            Pay before statement closes to optimize reported utilization
          </Text>
        </View>
        <Icon name="calendar" size={24} color="#007AFF" />
      </View>

      {plans.map((plan) => {
        const isUrgent = plan.daysUntilClose <= 3;
        const utilizationPercent = Math.round(plan.currentUtilization * 100);
        const targetPercent = Math.round(plan.targetUtilization * 100);

        return (
          <TouchableOpacity
            key={plan.cardId}
            style={[styles.card, isUrgent && styles.cardUrgent]}
            onPress={() => onCardPress?.(plan)}
            activeOpacity={0.7}
          >
            <View style={styles.cardHeader}>
              <Text style={styles.cardName}>{plan.cardName}</Text>
              {isUrgent && (
                <View style={styles.urgentBadge}>
                  <Text style={styles.urgentText}>Urgent</Text>
                </View>
              )}
            </View>

            <View style={styles.cardContent}>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Current Utilization</Text>
                <Text style={[styles.metricValue, utilizationPercent > 30 && styles.metricValueHigh]}>
                  {utilizationPercent}%
                </Text>
              </View>

              <View style={styles.recommendationBox}>
                <View style={styles.recommendationHeader}>
                  <Icon name="target" size={16} color="#007AFF" />
                  <Text style={styles.recommendationTitle}>Recommended Action</Text>
                </View>
                <Text style={styles.recommendationAmount}>
                  Pay ${plan.recommendedPaydown.toFixed(0)} by {formatDate(plan.statementCloseDate)}
                </Text>
                <Text style={styles.recommendationResult}>
                  → Reports at {targetPercent}% utilization
                </Text>
                {plan.projectedScoreGain > 0 && (
                  <Text style={styles.scoreGain}>
                    +{plan.projectedScoreGain} points potential
                  </Text>
                )}
              </View>

              <View style={styles.timingRow}>
                <View style={styles.timingItem}>
                  <Icon name="clock" size={14} color="#8E8E93" />
                  <Text style={styles.timingText}>
                    Statement closes in {getDaysUntilClose(plan.daysUntilClose)}
                  </Text>
                </View>
                <View style={styles.timingItem}>
                  <Icon name="calendar" size={14} color="#8E8E93" />
                  <Text style={styles.timingText}>
                    Due {formatDate(plan.paymentDueDate)}
                  </Text>
                </View>
              </View>
            </View>
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 13,
    color: '#8E8E93',
    lineHeight: 18,
  },
  emptyContainer: {
    padding: 32,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginTop: 12,
    marginBottom: 4,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
  },
  card: {
    backgroundColor: '#F8F9FA',
    borderRadius: 10,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  cardUrgent: {
    borderColor: '#FF9500',
    borderWidth: 2,
    backgroundColor: '#FFF8E1',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  cardName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  urgentBadge: {
    backgroundColor: '#FF9500',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  urgentText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FFFFFF',
    textTransform: 'uppercase',
  },
  cardContent: {
    gap: 12,
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 14,
    color: '#8E8E93',
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#34C759',
  },
  metricValueHigh: {
    color: '#FF3B30',
  },
  recommendationBox: {
    backgroundColor: '#E3F2FD',
    borderRadius: 8,
    padding: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#007AFF',
  },
  recommendationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  recommendationTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#007AFF',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  recommendationAmount: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  recommendationResult: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
    marginBottom: 4,
  },
  scoreGain: {
    fontSize: 12,
    color: '#34C759',
    fontWeight: '600',
    marginTop: 4,
  },
  timingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  timingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  timingText: {
    fontSize: 12,
    color: '#8E8E93',
  },
});

