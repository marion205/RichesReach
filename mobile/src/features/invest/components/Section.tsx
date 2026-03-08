/**
 * Reusable section block: optional title + optional card wrapper.
 * Uses theme tokens for consistency.
 */

import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import { COLORS, SPACING, RADIUS } from '../theme/privateMarketsTheme';

interface SectionProps {
  title?: string;
  card?: boolean;
  children: React.ReactNode;
  style?: ViewStyle;
  cardStyle?: ViewStyle;
}

export function Section({ title, card, children, style, cardStyle }: SectionProps) {
  const content = card ? (
    <View style={[styles.card, cardStyle]}>{children}</View>
  ) : (
    <>{children}</>
  );
  return (
    <View style={[styles.section, style]}>
      {title ? <Text style={styles.title}>{title}</Text> : null}
      {content}
    </View>
  );
}

const styles = StyleSheet.create({
  section: { marginBottom: 36 },
  title: {
    fontSize: 14,
    fontWeight: '700',
    color: '#64748B',
    marginBottom: SPACING.md,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  card: {
    backgroundColor: COLORS.bgCard,
    borderRadius: RADIUS.lg,
    padding: SPACING.xl,
    borderWidth: 1,
    borderColor: COLORS.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
});
