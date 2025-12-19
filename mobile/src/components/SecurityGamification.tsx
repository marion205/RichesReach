/**
 * Security Gamification Component
 * Badges, streaks, achievements, and leaderboards
 */
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useQuery } from '@apollo/client';
import { LinearGradient } from 'expo-linear-gradient';
import Icon from 'react-native-vector-icons/Feather';
import { SECURITY_INSIGHTS, ZERO_TRUST_SUMMARY } from '../graphql/queries_corrected';
import { useAuth } from '../contexts/AuthContext';

interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  earned: boolean;
  earnedDate?: string;
}

interface Achievement {
  id: string;
  name: string;
  description: string;
  progress: number;
  maxProgress: number;
  icon: string;
}

interface Streak {
  type: 'security' | 'login' | 'biometric';
  current: number;
  longest: number;
  lastDate: string;
}

export const SecurityGamification: React.FC = () => {
  const { user } = useAuth();
  const [badges, setBadges] = useState<Badge[]>([]);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [streaks, setStreaks] = useState<Streak[]>([]);
  
  const { data: insightsData } = useQuery(SECURITY_INSIGHTS, {
    skip: !user?.id,
  });
  
  const { data: zeroTrustData } = useQuery(ZERO_TRUST_SUMMARY, {
    skip: !user?.id,
  });

  useEffect(() => {
    if (insightsData && zeroTrustData) {
      // Calculate badges
      const calculatedBadges: Badge[] = [
        {
          id: 'security_champion',
          name: 'Security Champion',
          description: 'Achieve security score of 80+',
          icon: 'shield',
          color: '#4CAF50',
          earned: (insightsData.securityScore?.score || 0) >= 80,
        },
        {
          id: 'fortress_master',
          name: 'Fortress Master',
          description: 'No unresolved security events for 30 days',
          icon: 'lock',
          color: '#2196F3',
          earned: (insightsData.securityEvents?.length || 0) === 0,
        },
        {
          id: 'zero_trust_hero',
          name: 'Zero Trust Hero',
          description: 'Maintain average trust score of 80+',
          icon: 'check-circle',
          color: '#9C27B0',
          earned: (zeroTrustData.zeroTrustSummary?.averageTrustScore || 0) >= 80,
        },
        {
          id: 'biometric_master',
          name: 'Biometric Master',
          description: 'Enable all biometric authentication methods',
          icon: 'fingerprint',
          color: '#FF9800',
          earned: false, // Would check biometric settings
        },
        {
          id: 'device_defender',
          name: 'Device Defender',
          description: 'Register and verify 3+ trusted devices',
          icon: 'smartphone',
          color: '#F44336',
          earned: (zeroTrustData.zeroTrustSummary?.devices || 0) >= 3,
        },
        {
          id: 'compliance_king',
          name: 'Compliance King',
          description: 'All compliance checks passed',
          icon: 'file-check',
          color: '#00BCD4',
          earned: false, // Would check compliance status
        },
      ];
      
      setBadges(calculatedBadges);

      // Calculate achievements (progress-based)
      const calculatedAchievements: Achievement[] = [
        {
          id: 'security_score_100',
          name: 'Perfect Security',
          description: 'Reach security score of 100',
          progress: insightsData.securityScore?.score || 0,
          maxProgress: 100,
          icon: 'star',
        },
        {
          id: 'trusted_devices_5',
          name: 'Device Collector',
          description: 'Register 5 trusted devices',
          progress: zeroTrustData.zeroTrustSummary?.devices || 0,
          maxProgress: 5,
          icon: 'smartphone',
        },
        {
          id: 'security_streak_30',
          name: '30-Day Streak',
          description: 'Maintain security streak for 30 days',
          progress: 0, // Would calculate from historical data
          maxProgress: 30,
          icon: 'calendar',
        },
      ];
      
      setAchievements(calculatedAchievements);

      // Calculate streaks
      const calculatedStreaks: Streak[] = [
        {
          type: 'security',
          current: 0, // Would calculate from historical data
          longest: 0,
          lastDate: new Date().toISOString(),
        },
        {
          type: 'login',
          current: 0,
          longest: 0,
          lastDate: new Date().toISOString(),
        },
        {
          type: 'biometric',
          current: 0,
          longest: 0,
          lastDate: new Date().toISOString(),
        },
      ];
      
      setStreaks(calculatedStreaks);
    }
  }, [insightsData, zeroTrustData]);

  const earnedBadges = badges.filter(b => b.earned);
  const unearnedBadges = badges.filter(b => !b.earned);

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Stats Overview */}
      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{earnedBadges.length}</Text>
          <Text style={styles.statLabel}>Badges Earned</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{achievements.length}</Text>
          <Text style={styles.statLabel}>Achievements</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{streaks[0]?.current || 0}</Text>
          <Text style={styles.statLabel}>Day Streak</Text>
        </View>
      </View>

      {/* Earned Badges */}
      {earnedBadges.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🏆 Earned Badges</Text>
          <View style={styles.badgesGrid}>
            {earnedBadges.map((badge) => (
              <View key={badge.id} style={styles.badgeCard}>
                <LinearGradient
                  colors={[badge.color, `${badge.color}CC`]}
                  style={styles.badgeIcon}
                >
                  <Icon name={badge.icon} size={32} color="#FFF" />
                </LinearGradient>
                <Text style={styles.badgeName}>{badge.name}</Text>
                <Text style={styles.badgeDescription}>{badge.description}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Unearned Badges */}
      {unearnedBadges.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🔒 Locked Badges</Text>
          <View style={styles.badgesGrid}>
            {unearnedBadges.map((badge) => (
              <View key={badge.id} style={[styles.badgeCard, styles.badgeLocked]}>
                <View style={[styles.badgeIcon, styles.badgeIconLocked]}>
                  <Icon name={badge.icon} size={32} color="#999" />
                  <View style={styles.lockOverlay}>
                    <Icon name="lock" size={16} color="#FFF" />
                  </View>
                </View>
                <Text style={[styles.badgeName, styles.badgeNameLocked]}>{badge.name}</Text>
                <Text style={styles.badgeDescription}>{badge.description}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Achievements */}
      {achievements.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📈 Achievements</Text>
          {achievements.map((achievement) => {
            const progress = (achievement.progress / achievement.maxProgress) * 100;
            return (
              <View key={achievement.id} style={styles.achievementCard}>
                <View style={styles.achievementHeader}>
                  <Icon name={achievement.icon} size={24} color="#4A90E2" />
                  <View style={styles.achievementInfo}>
                    <Text style={styles.achievementName}>{achievement.name}</Text>
                    <Text style={styles.achievementDescription}>{achievement.description}</Text>
                  </View>
                </View>
                <View style={styles.progressContainer}>
                  <View style={styles.progressBar}>
                    <View
                      style={[
                        styles.progressFill,
                        { width: `${Math.min(progress, 100)}%` },
                      ]}
                    />
                  </View>
                  <Text style={styles.progressText}>
                    {achievement.progress} / {achievement.maxProgress}
                  </Text>
                </View>
              </View>
            );
          })}
        </View>
      )}

      {/* Streaks */}
      {streaks.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🔥 Streaks</Text>
          {streaks.map((streak, index) => (
            <View key={index} style={styles.streakCard}>
              <View style={styles.streakHeader}>
                <Icon
                  name={streak.type === 'security' ? 'shield' : streak.type === 'login' ? 'log-in' : 'fingerprint'}
                  size={24}
                  color="#FF6B6B"
                />
                <Text style={styles.streakType}>
                  {streak.type.charAt(0).toUpperCase() + streak.type.slice(1)} Streak
                </Text>
              </View>
              <View style={styles.streakStats}>
                <View style={styles.streakStat}>
                  <Text style={styles.streakValue}>{streak.current}</Text>
                  <Text style={styles.streakLabel}>Current</Text>
                </View>
                <View style={styles.streakStat}>
                  <Text style={styles.streakValue}>{streak.longest}</Text>
                  <Text style={styles.streakLabel}>Longest</Text>
                </View>
              </View>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
    paddingTop: 16,
  },
  statsContainer: {
    flexDirection: 'row',
    margin: 16,
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#FFF',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  statValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#4A90E2',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  section: {
    marginHorizontal: 16,
    marginBottom: 16,
    backgroundColor: '#FFF',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
    color: '#333',
  },
  badgesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  badgeCard: {
    width: '48%',
    backgroundColor: '#F9F9F9',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  badgeLocked: {
    opacity: 0.6,
  },
  badgeIcon: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  badgeIconLocked: {
    backgroundColor: '#E0E0E0',
    position: 'relative',
  },
  lockOverlay: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    backgroundColor: '#999',
    borderRadius: 12,
    width: 24,
    height: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    textAlign: 'center',
    marginBottom: 4,
  },
  badgeNameLocked: {
    color: '#999',
  },
  badgeDescription: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  achievementCard: {
    backgroundColor: '#F9F9F9',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  achievementHeader: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  achievementInfo: {
    flex: 1,
    marginLeft: 12,
  },
  achievementName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  achievementDescription: {
    fontSize: 12,
    color: '#666',
  },
  progressContainer: {
    marginTop: 8,
  },
  progressBar: {
    height: 8,
    backgroundColor: '#E0E0E0',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 4,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#4A90E2',
    borderRadius: 4,
  },
  progressText: {
    fontSize: 12,
    color: '#666',
    textAlign: 'right',
  },
  streakCard: {
    backgroundColor: '#F9F9F9',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  streakHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  streakType: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginLeft: 12,
  },
  streakStats: {
    flexDirection: 'row',
    gap: 24,
  },
  streakStat: {
    alignItems: 'center',
  },
  streakValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FF6B6B',
  },
  streakLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
});

