/**
 * VolatilityNotificationCard
 * ==========================
 * Displays market volatility in a positive, actionable way.
 * "Market growth today just paid for your groceries this week"
 */

import React, { useRef, useEffect } from 'react';
import { View, Text, StyleSheet, Pressable, Animated } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { VolatilityNotification } from '../services/VolatilityCoachingService';

interface VolatilityNotificationCardProps {
  notification: VolatilityNotification;
  onPress?: () => void;
  onDismiss?: () => void;
}

const D = {
  green:         '#10B981',
  greenFaint:    '#D1FAE5',
  amber:         '#F59E0B',
  amberFaint:    '#FEF3C7',
  navy:          '#0B1426',
  white:         '#FFFFFF',
  textPrimary:   '#0F172A',
  textSecondary: '#64748B',
  textMuted:     '#94A3B8',
  card:          '#FFFFFF',
};

export default function VolatilityNotificationCard({
  notification,
  onPress,
  onDismiss,
}: VolatilityNotificationCardProps) {
  const slideAnim = useRef(new Animated.Value(-100)).current;
  const opacityAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(slideAnim, {
        toValue: 0,
        tension: 40,
        friction: 10,
        useNativeDriver: true,
      }),
      Animated.timing(opacityAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const handleDismiss = () => {
    Animated.parallel([
      Animated.timing(slideAnim, {
        toValue: -100,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(opacityAnim, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start(() => {
      onDismiss?.();
    });
  };

  const isPositive = notification.type === 'positive';
  const color = isPositive ? D.green : D.amber;
  const bgColor = isPositive ? D.greenFaint : D.amberFaint;
  const icon = isPositive ? 'trending-up' : 'shield';

  return (
    <Animated.View
      style={[
        styles.container,
        {
          transform: [{ translateY: slideAnim }],
          opacity: opacityAnim,
        },
      ]}
    >
      <Pressable
        style={[styles.card, { backgroundColor: bgColor, borderLeftColor: color }]}
        onPress={onPress}
      >
        {/* Icon */}
        <View style={[styles.iconWrap, { backgroundColor: color + '20' }]}>
          <Feather name={icon} size={20} color={color} />
        </View>

        {/* Content */}
        <View style={styles.content}>
          <Text style={styles.headline}>{notification.headline}</Text>
          <Text style={styles.body}>{notification.body}</Text>
          
          {/* Impact Row */}
          <View style={styles.impactRow}>
            {notification.impact.daysCloser && notification.impact.daysCloser > 0 && (
              <View style={[styles.impactBadge, { backgroundColor: color + '20' }]}>
                <Feather name="zap" size={10} color={color} />
                <Text style={[styles.impactText, { color }]}>
                  {notification.impact.daysCloser} days closer
                </Text>
              </View>
            )}
            <View style={[styles.impactBadge, { backgroundColor: color + '20' }]}>
              <Text style={[styles.impactText, { color }]}>
                {isPositive ? '+' : ''}${Math.abs(notification.impact.dollarAmount).toLocaleString()}
              </Text>
            </View>
          </View>

          {/* CTA */}
          {notification.ctaText && (
            <View style={styles.ctaRow}>
              <Text style={[styles.ctaText, { color }]}>{notification.ctaText}</Text>
              <Feather name="arrow-right" size={14} color={color} />
            </View>
          )}
        </View>

        {/* Dismiss Button */}
        <Pressable style={styles.dismissBtn} onPress={handleDismiss}>
          <Feather name="x" size={16} color={D.textMuted} />
        </Pressable>
      </Pressable>
    </Animated.View>
  );
}

// Compact inline version
export function VolatilityBadge({
  dollarChange,
  percentChange,
  onPress,
}: {
  dollarChange: number;
  percentChange: number;
  onPress?: () => void;
}) {
  const isPositive = dollarChange >= 0;
  const color = isPositive ? D.green : D.amber;

  return (
    <Pressable
      style={[styles.badge, { backgroundColor: color + '15', borderColor: color + '30' }]}
      onPress={onPress}
    >
      <Feather
        name={isPositive ? 'trending-up' : 'trending-down'}
        size={14}
        color={color}
      />
      <Text style={[styles.badgeAmount, { color }]}>
        {isPositive ? '+' : ''}${Math.abs(dollarChange).toLocaleString()}
      </Text>
      <Text style={[styles.badgePercent, { color: color + '99' }]}>
        ({isPositive ? '+' : ''}{percentChange.toFixed(2)}%)
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  card: {
    flexDirection: 'row',
    borderRadius: 16,
    padding: 16,
    borderLeftWidth: 4,
  },
  iconWrap: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  content: {
    flex: 1,
  },
  headline: {
    fontSize: 16,
    fontWeight: '700',
    color: D.textPrimary,
    marginBottom: 4,
  },
  body: {
    fontSize: 13,
    color: D.textSecondary,
    lineHeight: 20,
    marginBottom: 10,
  },
  impactRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 10,
  },
  impactBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  impactText: {
    fontSize: 11,
    fontWeight: '600',
  },
  ctaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  ctaText: {
    fontSize: 13,
    fontWeight: '600',
  },
  dismissBtn: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(255,255,255,0.8)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  
  // Badge
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    borderWidth: 1,
  },
  badgeAmount: {
    fontSize: 14,
    fontWeight: '700',
  },
  badgePercent: {
    fontSize: 12,
    fontWeight: '500',
  },
});
