/**
 * LifeDecisionScreen — 2026 Premium Design
 * =========================================
 * "What if I buy a $60K car?" simulator.
 * Shows the long-term wealth impact of financial decisions.
 *
 * Sections:
 *  - Dark navy hero with decision type selector
 *  - Input form: amount, description, monthly cost (optional)
 *  - Results card: opportunity cost, net worth delta, recommendation
 *  - Year-by-year comparison bar chart
 *  - Headline sentence
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  TextInput,
  Animated,
  StatusBar,
  Dimensions,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Feather from '@expo/vector-icons/Feather';
import { useNavigation } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLazyQuery, gql } from '@apollo/client';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ── GraphQL Query ─────────────────────────────────────────────────────────────

const SIMULATE_DECISION = gql`
  query SimulateDecision(
    $decisionType: String
    $amount: Float!
    $description: String
    $monthlyCost: Float
    $horizonYears: Int
  ) {
    simulateDecision(
      decisionType: $decisionType
      amount: $amount
      description: $description
      monthlyCost: $monthlyCost
      horizonYears: $horizonYears
    ) {
      userId
      decisionType
      description
      amount
      monthlyCost
      opportunityCost10yr
      netWorthDelta10yr
      monthlySurplusImpact
      breakEvenYears
      currentNetWorth
      investableSurplusMonthly
      returnRate
      projectionYears
      headlineSentence
      recommendation
      dataQuality
      yearByYear {
        year
        netWorthWith
        netWorthWithout
        delta
      }
    }
  }
`;

// ── Design Tokens ─────────────────────────────────────────────────────────────

const D = {
  navy:          '#0B1426',
  navyMid:       '#0F1E35',
  navyLight:     '#162642',
  blue:          '#3B82F6',
  green:         '#10B981',
  red:           '#EF4444',
  amber:         '#F59E0B',
  indigo:        '#6366F1',
  purple:        '#7C3AED',
  white:         '#FFFFFF',
  textPrimary:   '#0F172A',
  textSecondary: '#64748B',
  textMuted:     '#94A3B8',
  card:          '#FFFFFF',
  bg:            '#F1F5F9',
  greenFaint:    '#D1FAE5',
  redFaint:      '#FEE2E2',
  indigoFaint:   '#EEF2FF',
  amberFaint:    '#FEF3C7',
};

// ── Decision type config ──────────────────────────────────────────────────────

type DecisionType = 'purchase' | 'monthly' | 'debt' | 'investment';

const DECISION_TYPES: { key: DecisionType; label: string; icon: keyof typeof Feather.glyphMap; example: string }[] = [
  { key: 'purchase', label: 'One-Time', icon: 'shopping-bag', example: 'Car, gadget, furniture' },
  { key: 'monthly', label: 'Monthly', icon: 'repeat', example: 'Subscription, lease' },
  { key: 'debt', label: 'Financed', icon: 'credit-card', example: 'Loan, mortgage' },
  { key: 'investment', label: 'Investment', icon: 'home', example: 'Property, rental' },
];

// ── Formatting ────────────────────────────────────────────────────────────────

const fmt = (n: number) => '$' + Math.abs(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
const fmtSigned = (n: number) => (n >= 0 ? '+' : '−') + fmt(Math.abs(n));

// ── Main Screen ───────────────────────────────────────────────────────────────

export default function LifeDecisionScreen() {
  const navigation = useNavigation<any>();
  const insets = useSafeAreaInsets();

  const [decisionType, setDecisionType] = useState<DecisionType>('purchase');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [monthlyCost, setMonthlyCost] = useState('');

  const [simulate, { data, loading, error }] = useLazyQuery(SIMULATE_DECISION, {
    fetchPolicy: 'network-only',
  });

  const result = data?.simulateDecision;
  const hasResult = !loading && result;

  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (hasResult) {
      Animated.timing(fadeAnim, { toValue: 1, duration: 400, useNativeDriver: true }).start();
    } else {
      fadeAnim.setValue(0);
    }
  }, [hasResult, fadeAnim]);

  const onSimulate = () => {
    const amountNum = parseFloat(amount.replace(/[^0-9.]/g, ''));
    if (isNaN(amountNum) || amountNum <= 0) return;

    const monthlyNum = parseFloat(monthlyCost.replace(/[^0-9.]/g, '')) || 0;

    simulate({
      variables: {
        decisionType,
        amount: amountNum,
        description: description || `${decisionType} of ${fmt(amountNum)}`,
        monthlyCost: monthlyNum,
        horizonYears: 10,
      },
    });
  };

  const deltaColor = (result?.netWorthDelta10yr ?? 0) >= 0 ? D.green : D.red;
  const deltaFaint = (result?.netWorthDelta10yr ?? 0) >= 0 ? D.greenFaint : D.redFaint;

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <StatusBar barStyle="light-content" />

      {/* ── Hero Header ──────────────────────────────────────────────────── */}
      <LinearGradient
        colors={['#0B1426', '#1A1A2E']}
        style={[styles.hero, { paddingTop: insets.top + 8 }]}
      >
        <View style={styles.heroTop}>
          <Pressable
            onPress={() => navigation.goBack()}
            style={({ pressed }) => [styles.backBtn, { opacity: pressed ? 0.6 : 1 }]}
          >
            <Feather name="chevron-left" size={26} color={D.white} />
          </Pressable>
          <View style={{ flex: 1 }}>
            <Text style={styles.heroEyebrow}>FINANCIAL GPS</Text>
            <Text style={styles.heroTitle}>Life Decision</Text>
          </View>
          <View style={styles.heroIconBadge}>
            <Feather name="git-branch" size={22} color={D.amber} />
          </View>
        </View>

        {/* Decision type pills */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.typePills}
        >
          {DECISION_TYPES.map(dt => {
            const active = decisionType === dt.key;
            return (
              <Pressable
                key={dt.key}
                style={[styles.typePill, active && styles.typePillActive]}
                onPress={() => setDecisionType(dt.key)}
              >
                <Feather name={dt.icon} size={14} color={active ? D.white : D.textMuted} />
                <Text style={[styles.typePillText, active && styles.typePillTextActive]}>
                  {dt.label}
                </Text>
              </Pressable>
            );
          })}
        </ScrollView>
      </LinearGradient>

      {/* ── Scrollable Body ─────────────────────────────────────────────── */}
      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        {/* Input form card */}
        <View style={styles.card}>
          <Text style={styles.inputLabel}>What are you considering?</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. Tesla Model 3"
            placeholderTextColor={D.textMuted}
            value={description}
            onChangeText={setDescription}
          />

          <Text style={styles.inputLabel}>Total Amount ($)</Text>
          <TextInput
            style={styles.input}
            placeholder="60,000"
            placeholderTextColor={D.textMuted}
            keyboardType="numeric"
            value={amount}
            onChangeText={setAmount}
          />

          {(decisionType === 'monthly' || decisionType === 'debt') && (
            <>
              <Text style={styles.inputLabel}>Monthly Cost ($)</Text>
              <TextInput
                style={styles.input}
                placeholder="500"
                placeholderTextColor={D.textMuted}
                keyboardType="numeric"
                value={monthlyCost}
                onChangeText={setMonthlyCost}
              />
            </>
          )}

          <Pressable
            style={({ pressed }) => [styles.simulateBtn, { opacity: pressed ? 0.85 : 1 }]}
            onPress={onSimulate}
            disabled={loading}
          >
            {loading ? (
              <Text style={styles.simulateBtnText}>Calculating…</Text>
            ) : (
              <>
                <Feather name="play" size={16} color={D.white} />
                <Text style={styles.simulateBtnText}>Simulate Impact</Text>
              </>
            )}
          </Pressable>
        </View>

        {/* Error state */}
        {error && (
          <View style={[styles.card, { borderColor: D.red, borderWidth: 1 }]}>
            <Text style={{ color: D.red, fontWeight: '600' }}>Could not simulate. Try again.</Text>
          </View>
        )}

        {/* Results */}
        {hasResult && (
          <Animated.View style={{ opacity: fadeAnim }}>
            {/* Headline */}
            {result.headlineSentence && (
              <View style={styles.headlineCard}>
                <View style={styles.headlineAccent} />
                <Text style={styles.headlineText}>{result.headlineSentence}</Text>
              </View>
            )}

            {/* Key metrics */}
            <View style={styles.metricsRow}>
              <View style={[styles.metricCard, { backgroundColor: D.redFaint, borderColor: '#FECACA' }]}>
                <Text style={[styles.metricAmount, { color: D.red }]}>
                  {fmt(result.opportunityCost10yr ?? 0)}
                </Text>
                <Text style={styles.metricLabel}>Opportunity Cost (10yr)</Text>
              </View>
              <View style={[styles.metricCard, { backgroundColor: deltaFaint, borderColor: deltaColor + '44' }]}>
                <Text style={[styles.metricAmount, { color: deltaColor }]}>
                  {fmtSigned(result.netWorthDelta10yr ?? 0)}
                </Text>
                <Text style={styles.metricLabel}>Net Worth Delta</Text>
              </View>
            </View>

            {/* Monthly surplus impact */}
            {result.monthlySurplusImpact != null && (
              <View style={styles.card}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                  <Feather name="trending-down" size={18} color={D.amber} />
                  <Text style={styles.metricLabel}>Monthly Surplus Impact</Text>
                </View>
                <Text style={[styles.metricAmount, { color: D.amber, fontSize: 24 }]}>
                  {fmtSigned(result.monthlySurplusImpact)}/mo
                </Text>
                <Text style={styles.insightText}>
                  This is how much less you'll have to invest each month.
                </Text>
              </View>
            )}

            {/* Recommendation */}
            {result.recommendation && (
              <View style={[styles.card, { backgroundColor: D.indigoFaint, borderWidth: 1, borderColor: D.indigo + '33' }]}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <Feather name="compass" size={16} color={D.indigo} />
                  <Text style={[styles.metricLabel, { color: D.indigo, fontWeight: '700' }]}>Recommendation</Text>
                </View>
                <Text style={[styles.insightText, { color: D.textPrimary }]}>{result.recommendation}</Text>
              </View>
            )}

            {/* Year-by-year comparison */}
            {result.yearByYear?.length > 0 && (
              <View style={styles.card}>
                <Text style={styles.sectionHeader}>10-YEAR PROJECTION</Text>
                <View style={styles.chartLegend}>
                  <View style={styles.legendItem}>
                    <View style={[styles.legendDot, { backgroundColor: D.green }]} />
                    <Text style={styles.legendText}>Without decision</Text>
                  </View>
                  <View style={styles.legendItem}>
                    <View style={[styles.legendDot, { backgroundColor: D.red }]} />
                    <Text style={styles.legendText}>With decision</Text>
                  </View>
                </View>
                {result.yearByYear.map((y: any, idx: number) => {
                  const maxNW = Math.max(y.netWorthWith, y.netWorthWithout, 1);
                  const withPct = Math.min((y.netWorthWith / maxNW) * 100, 100);
                  const withoutPct = Math.min((y.netWorthWithout / maxNW) * 100, 100);
                  return (
                    <View key={idx} style={styles.chartRow}>
                      <Text style={styles.chartYear}>Y{y.year}</Text>
                      <View style={styles.chartBars}>
                        <View style={[styles.chartBar, { width: `${withoutPct}%`, backgroundColor: D.green }]} />
                        <View style={[styles.chartBar, { width: `${withPct}%`, backgroundColor: D.red, marginTop: 4 }]} />
                      </View>
                      <Text style={[styles.chartDelta, { color: y.delta >= 0 ? D.green : D.red }]}>
                        {fmtSigned(y.delta)}
                      </Text>
                    </View>
                  );
                })}
              </View>
            )}

            <View style={{ height: 32 }} />
          </Animated.View>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: D.bg },

  hero: { paddingHorizontal: 20, paddingBottom: 12 },
  heroTop: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 10 },
  backBtn: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.1)',
    alignItems: 'center', justifyContent: 'center',
  },
  heroEyebrow: { fontSize: 10, fontWeight: '700', color: 'rgba(255,255,255,0.6)', letterSpacing: 1.6, marginBottom: 3 },
  heroTitle: { fontSize: 24, fontWeight: '800', color: D.white, letterSpacing: -0.5 },
  heroIconBadge: {
    width: 48, height: 48, borderRadius: 24,
    backgroundColor: 'rgba(245,158,11,0.18)', borderWidth: 1, borderColor: 'rgba(245,158,11,0.35)',
    alignItems: 'center', justifyContent: 'center',
  },

  typePills: { gap: 10 },
  typePill: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 99,
    backgroundColor: 'rgba(255,255,255,0.08)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.12)',
  },
  typePillActive: { backgroundColor: D.amber, borderColor: D.amber },
  typePillText: { fontSize: 13, fontWeight: '600', color: D.textMuted },
  typePillTextActive: { color: D.white },

  scrollContent: { paddingHorizontal: 16, paddingTop: 14 },

  card: {
    backgroundColor: D.card, borderRadius: 20, padding: 18, marginBottom: 14,
    shadowColor: '#0F172A', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.07, shadowRadius: 12, elevation: 3,
  },

  inputLabel: { fontSize: 13, fontWeight: '600', color: D.textSecondary, marginBottom: 6 },
  input: {
    backgroundColor: D.bg, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12,
    fontSize: 16, color: D.textPrimary, marginBottom: 14,
  },

  simulateBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    backgroundColor: D.indigo, borderRadius: 12, paddingVertical: 14, marginTop: 4,
  },
  simulateBtnText: { fontSize: 16, fontWeight: '700', color: D.white },

  headlineCard: {
    backgroundColor: D.card, borderRadius: 16, marginBottom: 14, overflow: 'hidden',
    borderWidth: 1, borderColor: D.indigo + '22',
  },
  headlineAccent: { position: 'absolute', left: 0, top: 0, bottom: 0, width: 4, backgroundColor: D.indigo },
  headlineText: { padding: 16, paddingLeft: 20, fontSize: 15, fontWeight: '500', color: D.textPrimary, fontStyle: 'italic', lineHeight: 22 },

  metricsRow: { flexDirection: 'row', gap: 10, marginBottom: 14 },
  metricCard: { flex: 1, borderRadius: 16, borderWidth: 1, padding: 16, alignItems: 'center', gap: 4 },
  metricAmount: { fontSize: 22, fontWeight: '800', letterSpacing: -0.5 },
  metricLabel: { fontSize: 11, fontWeight: '600', color: D.textSecondary, letterSpacing: 0.3, textAlign: 'center' },

  insightText: { fontSize: 14, color: D.textSecondary, lineHeight: 20 },

  sectionHeader: { fontSize: 10, fontWeight: '700', letterSpacing: 1.2, color: D.textMuted, marginBottom: 12 },

  chartLegend: { flexDirection: 'row', gap: 16, marginBottom: 14 },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  legendDot: { width: 10, height: 10, borderRadius: 5 },
  legendText: { fontSize: 11, color: D.textSecondary },

  chartRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 10, gap: 8 },
  chartYear: { width: 28, fontSize: 11, fontWeight: '600', color: D.textMuted },
  chartBars: { flex: 1 },
  chartBar: { height: 8, borderRadius: 4 },
  chartDelta: { width: 70, fontSize: 11, fontWeight: '700', textAlign: 'right' },
});
