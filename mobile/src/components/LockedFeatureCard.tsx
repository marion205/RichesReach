/**
 * LockedFeatureCard
 * =================
 * Shows a locked feature with its unlock requirements.
 * Used to tease upcoming features and motivate progression.
 */

import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import FeatureUnlockService, { MaturityStage } from '../services/FeatureUnlockService';

interface LockedFeatureCardProps {
  featureId: string;
  featureName: string;
  description: string;
  icon: string;
  unlockStage: MaturityStage;
  onPress?: () => void;
  compact?: boolean;
}

const D = {
  navy:          '#0B1426',
  white:         '#FFFFFF',
  textPrimary:   '#0F172A',
  textSecondary: '#64748B',
  textMuted:     '#94A3B8',
  card:          '#FFFFFF',
  border:        '#E2E8F0',
};

export default function LockedFeatureCard({
  featureId,
  featureName,
  description,
  icon,
  unlockStage,
  onPress,
  compact = false,
}: LockedFeatureCardProps) {
  const stageInfo = FeatureUnlockService.getStageInfo(unlockStage);

  if (compact) {
    return (
      <Pressable style={styles.compactCard} onPress={onPress}>
        <View style={styles.compactIconWrap}>
          <Feather name={icon as any} size={16} color={D.textMuted} />
          <View style={styles.lockBadge}>
            <Feather name="lock" size={8} color={D.white} />
          </View>
        </View>
        <View style={styles.compactContent}>
          <Text style={styles.compactTitle}>{featureName}</Text>
          <View style={styles.unlockRow}>
            <Text style={{ fontSize: 12 }}>{stageInfo.emoji}</Text>
            <Text style={[styles.unlockText, { color: stageInfo.color }]}>
              Unlock at {stageInfo.title}
            </Text>
          </View>
        </View>
      </Pressable>
    );
  }

  return (
    <Pressable style={styles.card} onPress={onPress}>
      <LinearGradient
        colors={['rgba(148,163,184,0.1)', 'rgba(148,163,184,0.05)']}
        style={styles.gradient}
      >
        <View style={styles.iconWrap}>
          <Feather name={icon as any} size={24} color={D.textMuted} />
          <View style={styles.lockBadgeLarge}>
            <Feather name="lock" size={12} color={D.white} />
          </View>
        </View>
        
        <View style={styles.content}>
          <Text style={styles.title}>{featureName}</Text>
          <Text style={styles.description}>{description}</Text>
          
          <View style={[styles.unlockBadge, { backgroundColor: stageInfo.color + '20' }]}>
            <Text style={{ fontSize: 14 }}>{stageInfo.emoji}</Text>
            <Text style={[styles.unlockBadgeText, { color: stageInfo.color }]}>
              Unlock at {stageInfo.title} level
            </Text>
          </View>
        </View>
        
        <Feather name="chevron-right" size={18} color={D.textMuted} />
      </LinearGradient>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 14,
    marginBottom: 10,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: D.border,
    borderStyle: 'dashed',
  },
  gradient: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
  },
  iconWrap: {
    width: 50,
    height: 50,
    borderRadius: 14,
    backgroundColor: 'rgba(148,163,184,0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  lockBadgeLarge: {
    position: 'absolute',
    bottom: -4,
    right: -4,
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: D.textMuted,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: D.card,
  },
  content: {
    flex: 1,
  },
  title: {
    fontSize: 15,
    fontWeight: '600',
    color: D.textSecondary,
    marginBottom: 2,
  },
  description: {
    fontSize: 12,
    color: D.textMuted,
    marginBottom: 8,
  },
  unlockBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  unlockBadgeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  
  // Compact
  compactCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(148,163,184,0.08)',
    borderRadius: 10,
    padding: 10,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: D.border,
    borderStyle: 'dashed',
  },
  compactIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: 'rgba(148,163,184,0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  lockBadge: {
    position: 'absolute',
    bottom: -3,
    right: -3,
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: D.textMuted,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: D.card,
  },
  compactContent: {
    flex: 1,
  },
  compactTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: D.textMuted,
    marginBottom: 2,
  },
  unlockRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  unlockText: {
    fontSize: 11,
    fontWeight: '500',
  },
});
