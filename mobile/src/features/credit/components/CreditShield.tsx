/**
 * Credit Shield - Preventive Safety Plan
 * Detects cashflow stress + due dates to prevent late payments
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { CreditShieldPlan } from '../types/CreditTypes';

interface CreditShieldProps {
  plan: CreditShieldPlan;
  onViewDetails?: () => void;
}

export const CreditShield: React.FC<CreditShieldProps> = ({
  plan,
  onViewDetails,
}) => {
  const getRiskColor = (risk: 'LOW' | 'MEDIUM' | 'HIGH') => {
    switch (risk) {
      case 'HIGH': return '#FF3B30';
      case 'MEDIUM': return '#FF9500';
      default: return '#34C759';
    }
  };

  const getRiskIcon = (risk: 'LOW' | 'MEDIUM' | 'HIGH') => {
    switch (risk) {
      case 'HIGH': return 'alert-triangle';
      case 'MEDIUM': return 'alert-circle';
      default: return 'shield';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getDaysUntilDue = (days: number) => {
    if (days === 0) return 'Due today';
    if (days === 1) return 'Due tomorrow';
    if (days < 7) return `Due in ${days} days`;
    if (days < 30) return `Due in ${Math.floor(days / 7)} weeks`;
    return `Due in ${Math.floor(days / 30)} months`;
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Icon 
            name={getRiskIcon(plan.riskLevel)} 
            size={24} 
            color={getRiskColor(plan.riskLevel)} 
          />
          <View style={styles.headerText}>
            <Text style={styles.title}>Credit Shield</Text>
            <Text style={[styles.riskLevel, { color: getRiskColor(plan.riskLevel) }]}>
              {plan.riskLevel} Risk
            </Text>
          </View>
        </View>
        {onViewDetails && (
          <TouchableOpacity onPress={onViewDetails}>
            <Text style={styles.viewDetailsText}>View Details</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Safety Buffer */}
      <View style={styles.bufferBox}>
        <View style={styles.bufferHeader}>
          <Icon name="dollar-sign" size={18} color="#007AFF" />
          <Text style={styles.bufferTitle}>Recommended Safety Buffer</Text>
        </View>
        <Text style={styles.bufferAmount}>
          ${plan.safetyBuffer.toFixed(0)}
        </Text>
        <Text style={styles.bufferNote}>
          Keep this amount available to cover minimum payments
        </Text>
      </View>

      {/* Upcoming Payments */}
      {plan.upcomingPayments.length > 0 && (
        <View style={styles.paymentsSection}>
          <Text style={styles.sectionTitle}>Upcoming Payments</Text>
          {plan.upcomingPayments.map((payment, index) => (
            <View key={index} style={styles.paymentCard}>
              <View style={styles.paymentHeader}>
                <Text style={styles.paymentCardName}>{payment.cardName}</Text>
                <View style={[styles.riskBadge, { backgroundColor: getRiskColor(payment.riskLevel) + '20' }]}>
                  <Text style={[styles.riskBadgeText, { color: getRiskColor(payment.riskLevel) }]}>
                    {payment.riskLevel}
                  </Text>
                </View>
              </View>
              <View style={styles.paymentDetails}>
                <View style={styles.paymentRow}>
                  <Icon name="calendar" size={14} color="#8E8E93" />
                  <Text style={styles.paymentText}>
                    {formatDate(payment.dueDate)} • {getDaysUntilDue(payment.daysUntilDue)}
                  </Text>
                </View>
                <View style={styles.paymentRow}>
                  <Icon name="dollar-sign" size={14} color="#8E8E93" />
                  <Text style={styles.paymentAmount}>
                    Minimum: ${payment.minimumPayment.toFixed(2)}
                  </Text>
                </View>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Total Minimum Payments */}
      <View style={styles.totalBox}>
        <Text style={styles.totalLabel}>Total Minimum Payments Due</Text>
        <Text style={styles.totalAmount}>
          ${plan.totalMinimumPayments.toFixed(2)}
        </Text>
      </View>

      {/* Recommendations */}
      {plan.recommendations.length > 0 && (
        <View style={styles.recommendationsSection}>
          <Text style={styles.sectionTitle}>Recommendations</Text>
          {plan.recommendations.map((rec, index) => (
            <View key={index} style={styles.recommendationItem}>
              <Icon name="check-circle" size={16} color="#34C759" />
              <Text style={styles.recommendationText}>{rec}</Text>
            </View>
          ))}
        </View>
      )}
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
    alignItems: 'center',
    marginBottom: 16,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  headerText: {
    gap: 2,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  riskLevel: {
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  viewDetailsText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
  bufferBox: {
    backgroundColor: '#E3F2FD',
    borderRadius: 10,
    padding: 16,
    marginBottom: 16,
    borderLeftWidth: 3,
    borderLeftColor: '#007AFF',
  },
  bufferHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  bufferTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#007AFF',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  bufferAmount: {
    fontSize: 32,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  bufferNote: {
    fontSize: 13,
    color: '#8E8E93',
  },
  paymentsSection: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  paymentCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  paymentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  paymentCardName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  riskBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  riskBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  paymentDetails: {
    gap: 6,
  },
  paymentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  paymentText: {
    fontSize: 13,
    color: '#8E8E93',
  },
  paymentAmount: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  totalBox: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#F8F9FA',
    borderRadius: 10,
    marginBottom: 16,
  },
  totalLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  totalAmount: {
    fontSize: 20,
    fontWeight: '700',
    color: '#007AFF',
  },
  recommendationsSection: {
    marginTop: 8,
  },
  recommendationItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    marginBottom: 10,
  },
  recommendationText: {
    flex: 1,
    fontSize: 14,
    color: '#1C1C1E',
    lineHeight: 20,
  },
});

