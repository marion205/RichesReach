/**
 * Referral Program Card Component
 * $REACH token rewards for referrals
 */

import React, { useState, useEffect } from 'react';
import logger from '../../utils/logger';
import { View, Text, StyleSheet, TouchableOpacity, Share, Alert } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import * as Clipboard from 'expo-clipboard';
import * as Haptics from 'expo-haptics';

interface ReferralStats {
  totalReferrals: number;
  activeReferrals: number;
  totalEarned: number; // $REACH tokens
  pendingRewards: number;
  referralCode: string;
  referralLink: string;
}

export default function ReferralProgramCard() {
  const [stats, setStats] = useState<ReferralStats>({
    totalReferrals: 0,
    activeReferrals: 0,
    totalEarned: 0,
    pendingRewards: 0,
    referralCode: 'REACH2025',
    referralLink: 'https://richesreach.ai/ref/REACH2025',
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadReferralStats();
  }, []);

  const loadReferralStats = async () => {
    // In production, fetch from backend/GraphQL
    // For now, using mock data
    setStats({
      totalReferrals: 12,
      activeReferrals: 8,
      totalEarned: 1250,
      pendingRewards: 450,
      referralCode: 'REACH2025',
      referralLink: 'https://richesreach.ai/ref/REACH2025',
    });
  };

  const handleShare = async () => {
    try {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      
      const result = await Share.share({
        message: `Join RichesReach and get $25 in $REACH tokens! Use my referral code: ${stats.referralCode}\n\n${stats.referralLink}`,
        title: 'RichesReach Referral',
      });

      if (result.action === Share.sharedAction) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
    } catch (error) {
      logger.error('Failed to share:', error);
    }
  };

  const handleCopyLink = async () => {
    try {
      await Clipboard.setStringAsync(stats.referralLink);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      Alert.alert('Copied!', 'Referral link copied to clipboard');
    } catch (error) {
      Alert.alert('Error', 'Failed to copy link');
    }
  };

  const handleCopyCode = async () => {
    try {
      await Clipboard.setStringAsync(stats.referralCode);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      Alert.alert('Copied!', 'Referral code copied to clipboard');
    } catch (error) {
      Alert.alert('Error', 'Failed to copy code');
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="gift" size={20} color="#667eea" />
        <Text style={styles.title}>Referral Program</Text>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>$REACH Rewards</Text>
        </View>
      </View>

      <Text style={styles.description}>
        Earn $REACH tokens for every friend you refer. They get $25, you get $25!
      </Text>

      {/* Stats */}
      <View style={styles.stats}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{stats.totalReferrals}</Text>
          <Text style={styles.statLabel}>Total Referrals</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{stats.activeReferrals}</Text>
          <Text style={styles.statLabel}>Active</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: '#34C759' }]}>
            {stats.totalEarned.toLocaleString()}
          </Text>
          <Text style={styles.statLabel}>$REACH Earned</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: '#FF9F0A' }]}>
            {stats.pendingRewards.toLocaleString()}
          </Text>
          <Text style={styles.statLabel}>Pending</Text>
        </View>
      </View>

      {/* Referral Code */}
      <View style={styles.codeContainer}>
        <View style={styles.codeSection}>
          <Text style={styles.codeLabel}>Your Referral Code</Text>
          <View style={styles.codeRow}>
            <Text style={styles.codeValue}>{stats.referralCode}</Text>
            <TouchableOpacity style={styles.copyButton} onPress={handleCopyCode}>
              <Icon name="copy" size={16} color="#667eea" />
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.linkSection}>
          <Text style={styles.linkLabel}>Referral Link</Text>
          <View style={styles.linkRow}>
            <Text style={styles.linkValue} numberOfLines={1} ellipsizeMode="middle">
              {stats.referralLink}
            </Text>
            <TouchableOpacity style={styles.copyButton} onPress={handleCopyLink}>
              <Icon name="copy" size={16} color="#667eea" />
            </TouchableOpacity>
          </View>
        </View>
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        <TouchableOpacity style={styles.shareButton} onPress={handleShare}>
          <Icon name="share-2" size={18} color="#FFFFFF" />
          <Text style={styles.shareButtonText}>Share Referral</Text>
        </TouchableOpacity>
      </View>

      {/* Rewards Info */}
      <View style={styles.rewardsInfo}>
        <Icon name="info" size={14} color="#666" />
        <Text style={styles.rewardsInfoText}>
          Rewards are paid in $REACH tokens when your referral completes their first trade or deposits $100+
        </Text>
      </View>
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
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1a1a1a',
    marginLeft: 8,
    flex: 1,
  },
  badge: {
    backgroundColor: '#667eea15',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  badgeText: {
    color: '#667eea',
    fontSize: 11,
    fontWeight: '600',
  },
  description: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 16,
  },
  stats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 16,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#E5E5EA',
    marginBottom: 16,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 11,
    color: '#666',
    textAlign: 'center',
  },
  codeContainer: {
    marginBottom: 16,
  },
  codeSection: {
    marginBottom: 12,
  },
  codeLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 6,
  },
  codeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  codeValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1a1a1a',
    fontFamily: 'monospace',
    flex: 1,
  },
  linkSection: {
    marginBottom: 12,
  },
  linkLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 6,
  },
  linkRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  linkValue: {
    fontSize: 12,
    color: '#1a1a1a',
    flex: 1,
  },
  copyButton: {
    padding: 4,
    marginLeft: 8,
  },
  actions: {
    marginBottom: 12,
  },
  shareButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#667eea',
    padding: 14,
    borderRadius: 8,
    gap: 8,
  },
  shareButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  rewardsInfo: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#F9FAFB',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  rewardsInfoText: {
    fontSize: 12,
    color: '#666',
    lineHeight: 18,
    flex: 1,
  },
});

