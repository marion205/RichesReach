/**
 * Prominent goal plan card for Portfolio — inline levers and live-updating timeline.
 * One card per goal type; adjustments persist and recalc instantly.
 */

import React, { useState, useMemo, useCallback } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import type { SavedGoalPlan } from '../../../services/savedGoalService';
import type { GoalType } from '../../../services/aiClient';
import {
  formatGoalTarget,
  getGoalTitle,
  getGoalSubtitle,
  yearsToGoal,
  monthlyPmtToReach,
  DEFAULT_RATE,
  MIN_TARGET,
  MAX_TARGET,
} from '../lib/goalPlanUtils';

interface GoalPlanCardProps {
  plan: SavedGoalPlan;
  currentInvested: number;
  userId: string;
  onSave: (userId: string, plan: SavedGoalPlan) => Promise<void>;
  onDismiss: () => void;
  onEditFull: (goalType: GoalType) => void;
}

export default function GoalPlanCard({ plan, currentInvested, userId, onSave, onDismiss, onEditFull }: GoalPlanCardProps) {
  const [targetInputString, setTargetInputString] = useState('');
  const targetAmount = (() => {
    const t = targetInputString.replace(/\D/g, '').trim();
    if (t === '' || t === '0') return plan.target;
    const n = parseInt(t, 10);
    return Number.isNaN(n) ? plan.target : Math.min(MAX_TARGET, n);
  })();
  const [monthlyOverride, setMonthlyOverride] = useState<number | null>(null);
  const targetClamped = Math.max(MIN_TARGET, Math.min(MAX_TARGET, targetAmount));
  const monthly = monthlyOverride ?? plan.monthlyContribution;
  const yearsToReach = useMemo(
    () => yearsToGoal(targetClamped, monthly, DEFAULT_RATE, currentInvested),
    [targetClamped, monthly, currentInvested]
  );
  const suggestedMonthly = useMemo(
    () => monthlyPmtToReach(targetClamped, yearsToReach, DEFAULT_RATE, currentInvested),
    [targetClamped, yearsToReach, currentInvested]
  );

  const persist = useCallback(() => {
    const updated: SavedGoalPlan = {
      ...plan,
      target: targetClamped,
      currentInvested,
      monthlyContribution: monthly,
      yearsToReach,
    };
    onSave(userId, updated);
  }, [plan, targetClamped, currentInvested, monthly, yearsToReach, userId, onSave]);

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.title}>{getGoalTitle(plan.goalType, targetClamped)}</Text>
          <Text style={styles.subtitle}>{getGoalSubtitle(plan.goalType)}</Text>
        </View>
        <TouchableOpacity onPress={onDismiss} hitSlop={12} style={styles.dismiss}>
          <Icon name="x" size={22} color="#64748B" />
        </TouchableOpacity>
      </View>

      <View style={styles.summary}>
        <Text style={styles.summaryLine}>
          Target <Text style={styles.summaryValue}>{formatGoalTarget(targetClamped)}</Text>
          {' · '}
          <Text style={styles.summaryValue}>${monthly.toLocaleString()}/mo</Text>
          {' · '}
          <Text style={styles.summaryValue}>{yearsToReach} years</Text>
        </Text>
        <Text style={styles.meta}>
          Current: ${currentInvested.toLocaleString()} · Reach by age {plan.targetAge}
        </Text>
      </View>

      <View style={styles.levers}>
        <View style={styles.leverRow}>
          <Text style={styles.leverLabel}>Target ($)</Text>
          <TextInput
            style={styles.input}
            keyboardType="number-pad"
            value={targetInputString}
            placeholder={String(plan.target)}
            onChangeText={(t) => setTargetInputString(t.replace(/\D/g, ''))}
            onBlur={persist}
          />
        </View>
        <View style={styles.leverRow}>
          <Text style={styles.leverLabel}>Monthly ($)</Text>
          <TextInput
            style={styles.input}
            keyboardType="number-pad"
            value={monthlyOverride != null ? String(monthlyOverride) : ''}
            placeholder={String(suggestedMonthly)}
            onChangeText={(t) => {
              const n = parseInt(t.replace(/\D/g, ''), 10);
              setMonthlyOverride(Number.isNaN(n) || t.trim() === '' ? null : n);
            }}
            onBlur={persist}
          />
        </View>
      </View>

      <Text style={styles.liveHint}>
        At ${monthly.toLocaleString()}/mo → {formatGoalTarget(targetClamped)} in {yearsToReach} years
      </Text>

      <TouchableOpacity style={styles.editFull} onPress={() => onEditFull(plan.goalType)} activeOpacity={0.8}>
        <Text style={styles.editFullText}>Edit full plan</Text>
        <Icon name="chevron-right" size={18} color="#00cc99" />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 4,
    borderLeftWidth: 4,
    borderLeftColor: '#00cc99',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  headerLeft: { flex: 1 },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#0f172a',
  },
  subtitle: {
    fontSize: 14,
    color: '#64748B',
    marginTop: 2,
  },
  dismiss: { padding: 4 },
  summary: { marginBottom: 16 },
  summaryLine: {
    fontSize: 16,
    color: '#334155',
  },
  summaryValue: {
    fontWeight: '600',
    color: '#0f172a',
  },
  meta: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 4,
  },
  levers: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 10,
  },
  leverRow: { flex: 1 },
  leverLabel: {
    fontSize: 12,
    color: '#64748B',
    marginBottom: 4,
  },
  input: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    color: '#0f172a',
    backgroundColor: '#f8fafc',
  },
  liveHint: {
    fontSize: 14,
    color: '#00cc99',
    fontWeight: '600',
    marginBottom: 12,
  },
  editFull: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
  },
  editFullText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#00cc99',
  },
});
