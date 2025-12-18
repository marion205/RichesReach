/**
 * Ecosystem Perks - Real-World Rewards Integration
 * Unlock discounts, access, and perks based on credit actions
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { EcosystemIntegration, CreditPerk } from '../types/CreditTypes';

interface EcosystemPerksProps {
  integration: EcosystemIntegration;
  onRedeemPerk: (perkId: string) => void;
}

export const EcosystemPerks: React.FC<EcosystemPerksProps> = ({
  integration,
  onRedeemPerk,
}) => {
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'discount': return 'tag';
      case 'access': return 'key';
      case 'cashback': return 'dollar-sign';
      case 'event': return 'calendar';
      case 'service': return 'star';
      default: return 'gift';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'discount': return '#34C759';
      case 'access': return '#007AFF';
      case 'cashback': return '#FFD700';
      case 'event': return '#FF9500';
      case 'service': return '#AF52DE';
      default: return '#8E8E93';
    }
  };

  const unlockedPerks = integration.perks.filter(p => integration.unlockedPerks.includes(p.id));
  const availablePerks = integration.perks.filter(p => integration.availablePerks.includes(p.id));
  const lockedPerks = integration.perks.filter(
    p => !integration.unlockedPerks.includes(p.id) && !integration.availablePerks.includes(p.id)
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Credit Perks</Text>
          <Text style={styles.subtitle}>
            Unlock rewards as you build credit
          </Text>
        </View>
        <View style={styles.savingsBox}>
          <Text style={styles.savingsLabel}>Total Saved</Text>
          <Text style={styles.savingsAmount}>${integration.totalSavings.toFixed(0)}</Text>
        </View>
      </View>

      {/* Unlocked Perks */}
      {unlockedPerks.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Unlocked Perks</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {unlockedPerks.map((perk) => (
              <TouchableOpacity
                key={perk.id}
                style={styles.perkCard}
                onPress={() => onRedeemPerk(perk.id)}
                activeOpacity={0.7}
              >
                <View style={[styles.perkIcon, { backgroundColor: getCategoryColor(perk.category) + '20' }]}>
                  <Icon name={getCategoryIcon(perk.category)} size={24} color={getCategoryColor(perk.category)} />
                </View>
                <Text style={styles.perkName}>{perk.name}</Text>
                <Text style={styles.perkDescription} numberOfLines={2}>
                  {perk.description}
                </Text>
                {perk.discount && (
                  <Text style={[styles.perkValue, { color: getCategoryColor(perk.category) }]}>
                    {perk.discount}% OFF
                  </Text>
                )}
                {perk.cashback && (
                  <Text style={[styles.perkValue, { color: getCategoryColor(perk.category) }]}>
                    {perk.cashback}% Cashback
                  </Text>
                )}
                <TouchableOpacity style={styles.redeemButton}>
                  <Text style={styles.redeemText}>Redeem</Text>
                </TouchableOpacity>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Available Perks (can unlock) */}
      {availablePerks.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Available to Unlock</Text>
          {availablePerks.map((perk) => (
            <View key={perk.id} style={styles.availableCard}>
              <View style={styles.availableLeft}>
                <View style={[styles.availableIcon, { backgroundColor: getCategoryColor(perk.category) + '20' }]}>
                  <Icon name={getCategoryIcon(perk.category)} size={20} color={getCategoryColor(perk.category)} />
                </View>
                <View style={styles.availableContent}>
                  <Text style={styles.availableName}>{perk.name}</Text>
                  <Text style={styles.availableDescription}>{perk.description}</Text>
                  <View style={styles.requirementBox}>
                    <Icon name="target" size={12} color="#8E8E93" />
                    <Text style={styles.requirementText}>
                      {perk.unlockRequirement.type === 'utilization_target' && 
                        `Keep utilization under ${perk.unlockRequirement.value}%`}
                      {perk.unlockRequirement.type === 'score_threshold' && 
                        `Reach ${perk.unlockRequirement.value} credit score`}
                      {perk.unlockRequirement.type === 'action_completion' && 
                        `Complete ${perk.unlockRequirement.value} actions`}
                      {perk.unlockRequirement.type === 'streak' && 
                        `Maintain ${perk.unlockRequirement.value} week streak`}
                    </Text>
                  </View>
                </View>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Locked Perks */}
      {lockedPerks.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Coming Soon</Text>
          {lockedPerks.map((perk) => (
            <View key={perk.id} style={styles.lockedCard}>
              <Icon name="lock" size={16} color="#8E8E93" />
              <Text style={styles.lockedName}>{perk.name}</Text>
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
    alignItems: 'flex-start',
    marginBottom: 20,
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
  savingsBox: {
    alignItems: 'flex-end',
  },
  savingsLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
  },
  savingsAmount: {
    fontSize: 24,
    fontWeight: '700',
    color: '#34C759',
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  perkCard: {
    width: 160,
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    marginRight: 12,
    alignItems: 'center',
  },
  perkIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  perkName: {
    fontSize: 15,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 6,
    textAlign: 'center',
  },
  perkDescription: {
    fontSize: 12,
    color: '#8E8E93',
    textAlign: 'center',
    marginBottom: 8,
    minHeight: 32,
  },
  perkValue: {
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 12,
  },
  redeemButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    width: '100%',
    alignItems: 'center',
  },
  redeemText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  availableCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 10,
    padding: 16,
    marginBottom: 12,
  },
  availableLeft: {
    flexDirection: 'row',
    gap: 12,
  },
  availableIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  availableContent: {
    flex: 1,
  },
  availableName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  availableDescription: {
    fontSize: 13,
    color: '#8E8E93',
    marginBottom: 8,
  },
  requirementBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FFFFFF',
    padding: 8,
    borderRadius: 6,
  },
  requirementText: {
    fontSize: 12,
    color: '#8E8E93',
    flex: 1,
  },
  lockedCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 12,
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    marginBottom: 8,
    opacity: 0.6,
  },
  lockedName: {
    fontSize: 14,
    color: '#8E8E93',
  },
});

