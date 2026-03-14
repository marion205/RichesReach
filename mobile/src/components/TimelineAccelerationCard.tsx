/**
 * TimelineAccelerationCard
 * ========================
 * Shows the impact of an action on the millionaire timeline.
 * This is the "Variable Reward" that makes users feel great about saving.
 */

import React, { useRef, useEffect } from 'react';
import { View, Text, StyleSheet, Animated, Pressable } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

interface TimelineAccelerationCardProps {
  monthlyAmount: number;
  futureValue: number;
  daysCloser: number;
  actionType: 'leak_redirect' | 'contribution_increase' | 'debt_payoff' | 'match_capture';
  onViewTimeline?: () => void;
}

const D = {
  green:         '#10B981',
  greenFaint:    '#D1FAE5',
  navy:          '#0B1426',
  white:         '#FFFFFF',
  textPrimary:   '#0F172A',
  textSecondary: '#64748B',
  textMuted:     '#94A3B8',
};

const ACTION_CONFIG = {
  leak_redirect: { icon: 'shield', color: '#6366F1', label: 'Leak Redirected' },
  contribution_increase: { icon: 'trending-up', color: '#10B981', label: 'Contribution Increased' },
  debt_payoff: { icon: 'check-circle', color: '#EF4444', label: 'Debt Eliminated' },
  match_capture: { icon: 'gift', color: '#F59E0B', label: 'Free Money Captured' },
};

export default function TimelineAccelerationCard({
  monthlyAmount,
  futureValue,
  daysCloser,
  actionType,
  onViewTimeline,
}: TimelineAccelerationCardProps) {
  const scaleAnim = useRef(new Animated.Value(0.8)).current;
  const opacityAnim = useRef(new Animated.Value(0)).current;
  const countAnim = useRef(new Animated.Value(0)).current;
  const [displayDays, setDisplayDays] = React.useState(0);

  const config = ACTION_CONFIG[actionType];

  useEffect(() => {
    // Entrance animation
    Animated.parallel([
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 50,
        friction: 8,
        useNativeDriver: true,
      }),
      Animated.timing(opacityAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();

    // Count-up animation for days
    Animated.timing(countAnim, {
      toValue: daysCloser,
      duration: 1500,
      useNativeDriver: false,
    }).start();

    const listener = countAnim.addListener(({ value }) => {
      setDisplayDays(Math.round(value));
    });

    return () => {
      countAnim.removeListener(listener);
    };
  }, [daysCloser]);

  const formatFutureValue = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return `$${value.toFixed(0)}`;
  };

  const formatDays = (days: number) => {
    if (days >= 365) {
      const years = Math.floor(days / 365);
      const months = Math.round((days % 365) / 30);
      return months > 0 ? `${years}y ${months}mo` : `${years} year${years > 1 ? 's' : ''}`;
    }
    if (days >= 30) {
      const months = Math.round(days / 30);
      return `${months} month${months > 1 ? 's' : ''}`;
    }
    return `${days} day${days !== 1 ? 's' : ''}`;
  };

  return (
    <Animated.View
      style={[
        styles.container,
        {
          opacity: opacityAnim,
          transform: [{ scale: scaleAnim }],
        },
      ]}
    >
      <LinearGradient
        colors={[D.navy, '#0A2518']}
        style={styles.card}
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={[styles.iconWrap, { backgroundColor: config.color + '30' }]}>
            <Feather name={config.icon as any} size={20} color={config.color} />
          </View>
          <View style={styles.headerText}>
            <Text style={styles.actionLabel}>{config.label}</Text>
            <Text style={styles.monthlyAmount}>${monthlyAmount}/mo redirected</Text>
          </View>
          <View style={styles.checkBadge}>
            <Feather name="check" size={16} color={D.white} />
          </View>
        </View>

        {/* Impact Metrics */}
        <View style={styles.metricsRow}>
          <View style={styles.metric}>
            <Text style={styles.metricValue}>{formatDays(displayDays)}</Text>
            <Text style={styles.metricLabel}>closer to goal</Text>
          </View>
          <View style={styles.metricDivider} />
          <View style={styles.metric}>
            <Text style={styles.metricValue}>{formatFutureValue(futureValue)}</Text>
            <Text style={styles.metricLabel}>in 20 years</Text>
          </View>
        </View>

        {/* Progress Animation */}
        <View style={styles.progressSection}>
          <View style={styles.progressLine}>
            <View style={styles.progressDot} />
            <View style={styles.progressTrack}>
              <Animated.View 
                style={[
                  styles.progressFill,
                  { width: `${Math.min(100, (displayDays / daysCloser) * 100)}%` }
                ]} 
              />
            </View>
            <View style={[styles.progressDot, { backgroundColor: D.green }]}>
              <Feather name="flag" size={10} color={D.white} />
            </View>
          </View>
          <View style={styles.progressLabels}>
            <Text style={styles.progressLabelNow}>Now</Text>
            <Text style={[styles.progressLabelGoal, { color: D.green }]}>Millionaire</Text>
          </View>
        </View>

        {/* CTA */}
        {onViewTimeline && (
          <Pressable style={styles.ctaButton} onPress={onViewTimeline}>
            <Text style={styles.ctaText}>View Your Timeline</Text>
            <Feather name="arrow-right" size={16} color={D.green} />
          </Pressable>
        )}
      </LinearGradient>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 16,
    marginHorizontal: 16,
  },
  card: {
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(16,185,129,0.3)',
  },
  
  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  iconWrap: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  headerText: {
    flex: 1,
  },
  actionLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: D.white,
    marginBottom: 2,
  },
  monthlyAmount: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.6)',
  },
  checkBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: D.green,
    alignItems: 'center',
    justifyContent: 'center',
  },

  // Metrics
  metricsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 14,
    padding: 16,
    marginBottom: 20,
  },
  metric: {
    flex: 1,
    alignItems: 'center',
  },
  metricValue: {
    fontSize: 28,
    fontWeight: '800',
    color: D.green,
    marginBottom: 4,
  },
  metricLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.6)',
  },
  metricDivider: {
    width: 1,
    height: 40,
    backgroundColor: 'rgba(255,255,255,0.1)',
    marginHorizontal: 16,
  },

  // Progress
  progressSection: {
    marginBottom: 16,
  },
  progressLine: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  progressDot: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: 'rgba(255,255,255,0.3)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  progressTrack: {
    flex: 1,
    height: 4,
    backgroundColor: 'rgba(255,255,255,0.1)',
    marginHorizontal: 8,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: D.green,
    borderRadius: 2,
  },
  progressLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  progressLabelNow: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.5)',
  },
  progressLabelGoal: {
    fontSize: 11,
    fontWeight: '600',
  },

  // CTA
  ctaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: 'rgba(16,185,129,0.15)',
    paddingVertical: 12,
    borderRadius: 12,
  },
  ctaText: {
    fontSize: 14,
    fontWeight: '600',
    color: D.green,
  },
});
