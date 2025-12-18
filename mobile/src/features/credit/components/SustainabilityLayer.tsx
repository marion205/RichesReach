/**
 * Sustainability Layer - Impact Tracking
 * Tracks environmental impact from credit-building actions
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Modal, Alert } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { SustainabilityTracking } from '../types/CreditTypes';

interface SustainabilityLayerProps {
  tracking: SustainabilityTracking;
  onViewDetails?: () => void;
}

export const SustainabilityLayer: React.FC<SustainabilityLayerProps> = ({
  tracking,
  onViewDetails,
}) => {
  const [showInfoModal, setShowInfoModal] = useState(false);
  
  const formatNumber = (num: number) => {
    if (num >= 1000) return `${(num / 1000).toFixed(1)}k`;
    return num.toString();
  };

  const showExplanation = () => {
    Alert.alert(
      'What is Credit Impact?',
      `Every time you take action to build your credit—like paying bills on time, reducing utilization, or setting up autopay—you're not just improving your score. You're also making a positive impact on the planet.

🌱 How it works:
• Complete credit-building actions
• We partner with organizations like Tree-Nation to plant trees
• Track your environmental impact in real-time
• See your total trees planted and CO₂ offset

💚 Why it matters:
Building credit can feel abstract. Credit Impact makes it tangible by connecting your financial progress to real environmental benefits. Every action counts—for your score and for the planet.

Your impact grows with every credit action you complete!`,
      [{ text: 'Got it!', style: 'default' }]
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.titleSection}>
          <Text style={styles.title}>Credit Impact</Text>
          <Text style={styles.subtitle}>
            Building credit while building a better planet
          </Text>
        </View>
        <View style={styles.headerRight}>
          <TouchableOpacity 
            style={styles.infoButton}
            onPress={showExplanation}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Icon name="help-circle" size={18} color="#007AFF" />
          </TouchableOpacity>
          <View style={styles.impactBadge}>
            <Icon name="sun" size={20} color="#34C759" />
          </View>
        </View>
      </View>

      {/* Total Impact */}
      <View style={styles.totalImpactBox}>
        <View style={styles.impactRow}>
          <View style={styles.impactItem}>
            <Icon name="sun" size={28} color="#34C759" />
            <Text style={styles.impactValue}>{formatNumber(tracking.totalImpact.treesPlanted)}</Text>
            <Text style={styles.impactLabel}>Trees Planted</Text>
          </View>
          <View style={styles.impactDivider} />
          <View style={styles.impactItem}>
            <Icon name="cloud" size={28} color="#5AC8FA" />
            <Text style={styles.impactValue}>{tracking.totalImpact.co2Offset.toFixed(1)}</Text>
            <Text style={styles.impactLabel}>kg CO₂ Offset</Text>
          </View>
        </View>
      </View>

      {/* Weekly Impact */}
      <View style={styles.weeklyBox}>
        <Text style={styles.weeklyTitle}>This Week</Text>
        <View style={styles.weeklyStats}>
          <View style={styles.weeklyStat}>
            <Text style={styles.weeklyValue}>{tracking.weeklyImpact.treesPlanted}</Text>
            <Text style={styles.weeklyLabel}>Trees</Text>
          </View>
          <View style={styles.weeklyStat}>
            <Text style={styles.weeklyValue}>{tracking.weeklyImpact.co2Offset.toFixed(1)}</Text>
            <Text style={styles.weeklyLabel}>kg CO₂</Text>
          </View>
          <View style={styles.weeklyStat}>
            <Text style={styles.weeklyValue}>{tracking.weeklyImpact.actionsCompleted}</Text>
            <Text style={styles.weeklyLabel}>Actions</Text>
          </View>
        </View>
      </View>

      {/* Goals */}
      {tracking.goals.length > 0 && (
        <View style={styles.goalsBox}>
          <Text style={styles.sectionTitle}>Impact Goals</Text>
          {tracking.goals.map((goal) => {
            const progress = (goal.current / goal.target) * 100;
            return (
              <View key={goal.id} style={styles.goalCard}>
                <View style={styles.goalHeader}>
                  <Text style={styles.goalName}>{goal.name}</Text>
                  <Text style={styles.goalProgress}>
                    {goal.current} / {goal.target} {goal.unit === 'trees' ? 'trees' : 'kg'}
                  </Text>
                </View>
                <View style={styles.goalBar}>
                  <View 
                    style={[
                      styles.goalFill,
                      { width: `${Math.min(progress, 100)}%` }
                    ]} 
                  />
                </View>
                <Text style={styles.goalPercent}>{Math.round(progress)}% complete</Text>
              </View>
            );
          })}
        </View>
      )}

      {/* Milestones */}
      {tracking.totalImpact.milestones.length > 0 && (
        <View style={styles.milestonesBox}>
          <Text style={styles.sectionTitle}>Recent Milestones</Text>
          {tracking.totalImpact.milestones.slice(0, 3).map((milestone) => (
            <View key={milestone.id} style={styles.milestoneCard}>
              <Icon name="award" size={16} color="#FFD700" />
              <View style={styles.milestoneContent}>
                <Text style={styles.milestoneName}>{milestone.name}</Text>
                <Text style={styles.milestoneDate}>
                  {new Date(milestone.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </Text>
              </View>
              <Text style={styles.milestoneImpact}>
                +{milestone.impact} {milestone.impact > 1 ? 'trees' : 'tree'}
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* Partner Integrations */}
      {tracking.partnerIntegrations.length > 0 && (
        <View style={styles.partnersBox}>
          <Text style={styles.sectionTitle}>Partner Contributions</Text>
          {tracking.partnerIntegrations.map((partner, index) => (
            <View key={index} style={styles.partnerCard}>
              <View style={styles.partnerIcon}>
                <Icon 
                  name={partner.type === 'tree_planting' ? 'sun' : 
                        partner.type === 'carbon_offset' ? 'cloud' : 'sun'} 
                  size={18} 
                  color="#34C759" 
                />
              </View>
              <View style={styles.partnerContent}>
                <Text style={styles.partnerName}>{partner.name}</Text>
                <Text style={styles.partnerType}>
                  {partner.type === 'tree_planting' ? 'Tree Planting' :
                   partner.type === 'carbon_offset' ? 'Carbon Offset' : 'Renewable Energy'}
                </Text>
              </View>
              <Text style={styles.partnerContribution}>
                {partner.contribution} {partner.type === 'tree_planting' ? 'trees' : 'kg CO₂'}
              </Text>
            </View>
          ))}
        </View>
      )}

      {onViewDetails && (
        <TouchableOpacity style={styles.detailsButton} onPress={onViewDetails}>
          <Text style={styles.detailsButtonText}>View Full Impact Report</Text>
          <Icon name="arrow-right" size={16} color="#007AFF" />
        </TouchableOpacity>
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
    marginBottom: 20,
  },
  titleSection: {
    flex: 1,
    marginRight: 12,
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
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  infoButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#E3F2FD',
    alignItems: 'center',
    justifyContent: 'center',
  },
  impactBadge: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#ECFDF5',
    alignItems: 'center',
    justifyContent: 'center',
  },
  totalImpactBox: {
    backgroundColor: '#ECFDF5',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
  },
  impactRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  impactItem: {
    alignItems: 'center',
    flex: 1,
  },
  impactValue: {
    fontSize: 32,
    fontWeight: '700',
    color: '#1C1C1E',
    marginTop: 8,
    marginBottom: 4,
  },
  impactLabel: {
    fontSize: 14,
    color: '#8E8E93',
  },
  impactDivider: {
    width: 1,
    height: 60,
    backgroundColor: '#D1FAE5',
  },
  weeklyBox: {
    backgroundColor: '#F8F9FA',
    borderRadius: 10,
    padding: 16,
    marginBottom: 16,
  },
  weeklyTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  weeklyStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  weeklyStat: {
    alignItems: 'center',
  },
  weeklyValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#34C759',
    marginBottom: 4,
  },
  weeklyLabel: {
    fontSize: 12,
    color: '#8E8E93',
  },
  goalsBox: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  goalCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 10,
    padding: 16,
    marginBottom: 12,
  },
  goalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  goalName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  goalProgress: {
    fontSize: 13,
    color: '#8E8E93',
  },
  goalBar: {
    height: 8,
    backgroundColor: '#E5E5EA',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 6,
  },
  goalFill: {
    height: '100%',
    backgroundColor: '#34C759',
    borderRadius: 4,
  },
  goalPercent: {
    fontSize: 12,
    color: '#8E8E93',
  },
  milestonesBox: {
    marginBottom: 16,
  },
  milestoneCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#F8F9FA',
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
  },
  milestoneContent: {
    flex: 1,
  },
  milestoneName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 2,
  },
  milestoneDate: {
    fontSize: 12,
    color: '#8E8E93',
  },
  milestoneImpact: {
    fontSize: 14,
    fontWeight: '700',
    color: '#34C759',
  },
  partnersBox: {
    marginBottom: 16,
  },
  partnerCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#F8F9FA',
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
  },
  partnerIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#ECFDF5',
    alignItems: 'center',
    justifyContent: 'center',
  },
  partnerContent: {
    flex: 1,
  },
  partnerName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 2,
  },
  partnerType: {
    fontSize: 12,
    color: '#8E8E93',
  },
  partnerContribution: {
    fontSize: 13,
    fontWeight: '700',
    color: '#34C759',
  },
  detailsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 16,
    backgroundColor: '#E3F2FD',
    borderRadius: 10,
    marginTop: 8,
  },
  detailsButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
});

