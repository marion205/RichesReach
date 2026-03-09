/**
 * Goal Plan — destination after tapping a goal CTA from Ask (millionaire, retirement, house, emergency fund, concentration).
 * Shows current invested, suggested monthly, timeline, and "Start this plan". Levers: target, monthly, target age.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import { useRoute } from '@react-navigation/native';
import RealTimePortfolioService from '../services/RealTimePortfolioService';
import { saveSavedGoal } from '../../../services/savedGoalService';
import {
  type GoalType,
  MIN_TARGET,
  MAX_TARGET,
  DEFAULT_RATE,
  formatGoalTarget,
  yearsToTargetAge,
  monthlyPmtToReach,
  yearsToGoal,
  getDefaultTarget,
  getGoalTitle,
  getGoalSubtitle,
} from '../lib/goalPlanUtils';

const IS_DEMO = process.env.EXPO_PUBLIC_DEMO_MODE === 'true';
const DEMO_PORTFOLIO = 14303;

const GET_USER_PROFILE = gql`
  query GetUserProfileForGoal {
    me {
      id
      name
      incomeProfile {
        age
        incomeBracket
      }
    }
  }
`;

interface GoalPlanScreenProps {
  navigateTo?: (screen: string, params?: Record<string, unknown>) => void;
}

type GoalPlanRouteParams = { target?: number; goalType?: GoalType };

export default function GoalPlanScreen({ navigateTo }: GoalPlanScreenProps) {
  const insets = useSafeAreaInsets();
  const route = useRoute();
  const params = route.params as GoalPlanRouteParams | undefined;
  const goalType = params?.goalType ?? 'millionaire';
  const defaultTarget = getDefaultTarget(goalType);
  const initialTarget = params?.target;
  const [targetInputString, setTargetInputString] = useState<string>(
    initialTarget != null && initialTarget >= MIN_TARGET && initialTarget <= MAX_TARGET && initialTarget !== defaultTarget
      ? String(initialTarget)
      : ''
  );
  const targetAmount = useMemo(() => {
    if (targetInputString.trim() === '' || targetInputString === '0') return defaultTarget;
    const n = parseInt(targetInputString.replace(/\D/g, ''), 10);
    return Number.isNaN(n) ? defaultTarget : Math.min(MAX_TARGET, n);
  }, [targetInputString, defaultTarget]);
  const [currentInvested, setCurrentInvested] = useState<number>(IS_DEMO ? DEMO_PORTFOLIO : 0);
  const [portfolioLoading, setPortfolioLoading] = useState(true);
  const [monthlyOverride, setMonthlyOverride] = useState<number | null>(null);
  const [targetAgeOverride, setTargetAgeOverride] = useState<number | null>(null);
  const targetClamped = useMemo(
    () => Math.max(MIN_TARGET, Math.min(MAX_TARGET, targetAmount)),
    [targetAmount]
  );

  const { data: profileData } = useQuery(GET_USER_PROFILE, {
    errorPolicy: 'ignore',
    fetchPolicy: 'cache-first',
  });

  const age = profileData?.me?.incomeProfile?.age ?? (IS_DEMO ? 32 : null);
  const targetAge = targetAgeOverride ?? 65;
  const yearsLeft = useMemo(
    () => yearsToTargetAge(age ?? 32, targetAge) ?? 33,
    [age, targetAge]
  );

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const data = await RealTimePortfolioService.getPortfolioData();
        if (mounted && data?.totalValue != null) setCurrentInvested(data.totalValue);
        else if (mounted && IS_DEMO) setCurrentInvested(DEMO_PORTFOLIO);
      } catch (_) {
        if (mounted && IS_DEMO) setCurrentInvested(DEMO_PORTFOLIO);
      } finally {
        if (mounted) setPortfolioLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const suggestedMonthly = useMemo(
    () => monthlyPmtToReach(targetClamped, yearsLeft, DEFAULT_RATE, currentInvested),
    [targetClamped, yearsLeft, currentInvested]
  );

  const monthly = monthlyOverride ?? suggestedMonthly;
  const yearsToReach = useMemo(
    () => yearsToGoal(targetClamped, monthly, DEFAULT_RATE, currentInvested),
    [targetClamped, monthly, currentInvested]
  );

  const userId = profileData?.me?.id ?? '1';

  const handleStartPlan = useCallback(async () => {
    const plan = {
      goalType,
      target: targetClamped,
      currentInvested,
      monthlyContribution: monthly,
      yearsToReach,
      targetAge,
    };
    await saveSavedGoal(userId, plan);
    if (navigateTo) {
      navigateTo('portfolio', { newGoal: plan });
    }
  }, [navigateTo, userId, goalType, targetClamped, currentInvested, monthly, yearsToReach, targetAge]);

  if (portfolioLoading) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <ActivityIndicator size="large" color="#00cc99" style={styles.loader} />
        <Text style={styles.loadingText}>Loading your plan…</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={[styles.container, { paddingTop: insets.top }]}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <Text style={styles.title}>{getGoalTitle(goalType, targetClamped)}</Text>
      <Text style={styles.subtitle}>{getGoalSubtitle(goalType)}</Text>

      <View style={styles.card}>
        <Row label="Target" value={formatGoalTarget(targetClamped)} />
        <Row label="Current invested" value={`$${currentInvested.toLocaleString()}`} />
        <Row label="Suggested monthly contribution" value={`$${suggestedMonthly.toLocaleString()}`} />
        <Row label="Target timeline" value={`${yearsToReach} years`} />
      </View>

      <View style={styles.levers}>
        <Text style={styles.leverTitle}>Adjust your plan</Text>
        <View style={styles.leverRow}>
          <Text style={styles.leverLabel}>Target amount ($)</Text>
          <TextInput
            style={styles.input}
            keyboardType="number-pad"
            placeholder={String(defaultTarget)}
            value={targetInputString}
            onChangeText={(t) => setTargetInputString(t.replace(/\D/g, ''))}
          />
        </View>
        <View style={styles.leverRow}>
          <Text style={styles.leverLabel}>Monthly contribution ($)</Text>
          <TextInput
            style={styles.input}
            keyboardType="number-pad"
            placeholder={String(suggestedMonthly)}
            defaultValue={monthlyOverride != null ? String(monthlyOverride) : ''}
            onChangeText={(t) => {
              const n = parseInt(t.replace(/\D/g, ''), 10);
              setMonthlyOverride(Number.isNaN(n) || t.trim() === '' ? null : n);
            }}
          />
        </View>
        <View style={styles.leverRow}>
          <Text style={styles.leverLabel}>Reach goal by age</Text>
          <TextInput
            style={styles.input}
            keyboardType="number-pad"
            placeholder={String(targetAge)}
            defaultValue={targetAgeOverride != null ? String(targetAgeOverride) : ''}
            onChangeText={(t) => {
              const n = parseInt(t.replace(/\D/g, ''), 10);
              setTargetAgeOverride(Number.isNaN(n) || t.trim() === '' ? null : n);
            }}
          />
        </View>
        {(monthlyOverride != null || targetAgeOverride != null || targetInputString.trim() !== '') && (
          <Text style={styles.recalcHint}>
            At ${monthly.toLocaleString()}/month you reach {formatGoalTarget(targetClamped)} in {yearsToReach} years.
          </Text>
        )}
      </View>

      <TouchableOpacity style={styles.cta} onPress={handleStartPlan} activeOpacity={0.85}>
        <Text style={styles.ctaText}>Start this plan</Text>
        <Icon name="arrow-right" size={20} color="#fff" />
      </TouchableOpacity>
    </ScrollView>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={styles.rowValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  content: { padding: 20, paddingBottom: 40 },
  loader: { marginTop: 80 },
  loadingText: { marginTop: 12, fontSize: 16, color: '#666', textAlign: 'center' },
  title: { fontSize: 24, fontWeight: '700', color: '#111', marginBottom: 4 },
  subtitle: { fontSize: 15, color: '#666', marginBottom: 24 },
  card: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#e5e5e5' },
  rowLabel: { fontSize: 15, color: '#666' },
  rowValue: { fontSize: 16, fontWeight: '600', color: '#111' },
  levers: { marginBottom: 24 },
  leverTitle: { fontSize: 17, fontWeight: '600', color: '#111', marginBottom: 12 },
  leverRow: { marginBottom: 12 },
  leverLabel: { fontSize: 14, color: '#666', marginBottom: 4 },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    color: '#111',
  },
  recalcHint: { marginTop: 8, fontSize: 14, color: '#00cc99', fontWeight: '500' },
  cta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#00cc99',
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
  },
  ctaText: { fontSize: 17, fontWeight: '600', color: '#fff' },
});
