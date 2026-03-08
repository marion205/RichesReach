/**
 * "What would change this score?" card with multi-state workflow (Not started → Requested → Received → Reviewed).
 */

import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import Feather from '@expo/vector-icons/Feather';
import { COLORS, SPACING, RADIUS } from '../../theme/privateMarketsTheme';
import type { DiligenceItemStatus } from '../../types/privateMarketsTypes';

const STATUS_ORDER: DiligenceItemStatus[] = ['not_started', 'requested', 'received', 'reviewed'];
const STATUS_LABELS: Record<DiligenceItemStatus, string> = {
  not_started: 'Not started',
  requested: 'Requested',
  received: 'Received',
  reviewed: 'Reviewed',
};

export interface DiligenceChecklistSectionProps {
  lines: string[];
  statusByLine: Record<string, DiligenceItemStatus>;
  onStatusChange: (line: string, status: DiligenceItemStatus) => void;
  onRequestFromGP: (line: string) => void;
}

export function DiligenceChecklistSection({
  lines,
  statusByLine,
  onStatusChange,
  onRequestFromGP,
}: DiligenceChecklistSectionProps) {
  if (!lines.length) return null;
  return (
    <View style={styles.card}>
      <Text style={styles.subtitle}>What would change this score?</Text>
      <Text style={styles.hint}>Track your diligence workflow</Text>
      {lines.map((line, i) => {
        const status = statusByLine[line] ?? 'not_started';
        const canRequest = status === 'not_started' || status === 'requested';
        return (
          <View key={i} style={styles.itemBlock}>
            <Text style={[styles.lineText, status === 'reviewed' && styles.lineTextReviewed]}>{line}</Text>
            <View style={styles.pillsRow}>
              {STATUS_ORDER.map((s) => (
                <Pressable
                  key={s}
                  style={({ pressed }) => [
                    styles.pill,
                    status === s && styles.pillActive,
                    pressed && styles.pillPressed,
                  ]}
                  onPress={() => onStatusChange(line, s)}
                  accessibilityLabel={`Set status to ${STATUS_LABELS[s]}`}
                  accessibilityRole="button"
                >
                  <Text style={[styles.pillText, status === s && styles.pillTextActive]} numberOfLines={1}>
                    {STATUS_LABELS[s]}
                  </Text>
                </Pressable>
              ))}
            </View>
            {canRequest && (
              <Pressable
                style={({ pressed }) => [styles.requestBtn, pressed && styles.requestBtnPressed]}
                onPress={() => onRequestFromGP(line)}
                accessibilityLabel="Request from issuer or GP"
                accessibilityRole="button"
              >
                <Feather name="send" size={14} color={COLORS.primary} />
                <Text style={styles.requestBtnText}>Request from issuer/GP</Text>
              </Pressable>
            )}
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    marginBottom: SPACING.lg,
    backgroundColor: COLORS.bgCard,
    borderRadius: RADIUS.lg,
    padding: SPACING.xl,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  subtitle: { fontSize: 15, fontWeight: '700', color: COLORS.primary, marginBottom: SPACING.sm },
  hint: { fontSize: 12, color: '#64748B', marginBottom: 10 },
  itemBlock: { marginBottom: 16, paddingBottom: 12, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#E2E8F0' },
  lineText: { fontSize: 13, color: COLORS.textSecondary, lineHeight: 18, marginBottom: 8 },
  lineTextReviewed: { color: '#94A3B8', textDecorationLine: 'line-through' },
  pillsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 8 },
  pill: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: RADIUS.sm, borderWidth: 1, borderColor: '#E2E8F0', backgroundColor: '#F8FAFC' },
  pillActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  pillPressed: { opacity: 0.8 },
  pillText: { fontSize: 11, fontWeight: '600', color: '#64748B' },
  pillTextActive: { color: '#FFF' },
  requestBtn: { flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start', gap: 6, paddingVertical: 6, paddingHorizontal: 10, borderRadius: RADIUS.sm, backgroundColor: 'rgba(59, 130, 246, 0.1)' },
  requestBtnPressed: { opacity: 0.8 },
  requestBtnText: { fontSize: 12, fontWeight: '600', color: COLORS.primary },
});
