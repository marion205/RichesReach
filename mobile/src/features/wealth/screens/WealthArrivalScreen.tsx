/**
 * Wealth Arrival Screen — 2026 Premium Design
 * ============================================
 * Hero screen of the Financial GPS feature suite.
 * Shows when the user will reach their target net worth
 * with multi-scenario projections, milestones, and a
 * custom bar-chart visualisation built entirely from Views.
 *
 * Design language matches OpportunityDiscoveryScreen exactly:
 *  - Dark navy → deep-purple hero gradient
 *  - Glass-morphism arrival hero card
 *  - 3-scenario toggle pills
 *  - Animated View-based bar chart
 *  - Staggered milestone timeline
 *  - Skeleton shimmer loading states
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  Animated,
  Dimensions,
  StatusBar,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Feather from '@expo/vector-icons/Feather';
import { useNavigation } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@apollo/client';

import { GET_WEALTH_ARRIVAL } from '../../../graphql/financialGps';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ── Design tokens ─────────────────────────────────────────────────────────────

const D = {
  navy:          '#0B1426',
  navyMid:       '#0F1E35',
  navyLight:     '#162642',
  blue:          '#3B82F6',
  blueLight:     '#60A5FA',
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
  cardBorder:    '#E2E8F0',
  bg:            '#F1F5F9',
  // Faint tints
  greenFaint:    '#D1FAE5',
  blueFaint:     '#EFF6FF',
  indigoFaint:   '#EEF2FF',
  amberFaint:    '#FEF3C7',
  offWhite:      '#F8FAFC',
};

// ── Constants ─────────────────────────────────────────────────────────────────

type Scenario = 'Conservative' | 'Moderate' | 'Aggressive';

const TARGET_AMOUNTS = [100_000, 250_000, 500_000, 1_000_000, 2_000_000, 5_000_000, 10_000_000];

const SCENARIO_CONFIG: Record<Scenario, { color: string; faint: string; label: string }> = {
  Conservative: { color: D.blue,   faint: D.blueFaint,   label: 'Conservative' },
  Moderate:     { color: D.green,  faint: D.greenFaint,  label: 'Moderate' },
  Aggressive:   { color: D.amber,  faint: D.amberFaint,  label: 'Aggressive' },
};

const CHART_HEIGHT = 140;
const BAR_MAX_HEIGHT = 110;

// ── Helpers ───────────────────────────────────────────────────────────────────

const fmtShort = (n: number): string => {
  if (n >= 1_000_000) return '$' + (n / 1_000_000).toFixed(n % 1_000_000 === 0 ? 0 : 1) + 'M';
  if (n >= 1_000)     return '$' + (n / 1_000).toFixed(0) + 'K';
  return '$' + n.toFixed(0);
};

const fmtTargetLabel = (n: number): string => {
  if (n >= 1_000_000) return '$' + (n / 1_000_000).toFixed(0) + 'M';
  if (n >= 1_000)     return '$' + (n / 1_000).toFixed(0) + 'K';
  return '$' + n.toFixed(0);
};

const currentYear = new Date().getFullYear();

// ── Main Component ────────────────────────────────────────────────────────────

export default function WealthArrivalScreen() {
  const navigation = useNavigation<any>();
  const insets     = useSafeAreaInsets();

  const [targetNetWorth, setTargetNetWorth] = useState(1_000_000);
  const [activeScenario, setActiveScenario] = useState<Scenario>('Moderate');

  const { data, loading } = useQuery(GET_WEALTH_ARRIVAL, {
    variables: { targetNetWorth },
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  // Entrance animations
  const fadeAnim  = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;

  // Bar chart animation
  const chartAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!loading) {
      Animated.parallel([
        Animated.timing(fadeAnim,  { toValue: 1, duration: 500, useNativeDriver: true }),
        Animated.timing(slideAnim, { toValue: 0, duration: 500, useNativeDriver: true }),
      ]).start();
      // Animate chart bars growing up
      chartAnim.setValue(0);
      Animated.timing(chartAnim, { toValue: 1, duration: 700, delay: 200, useNativeDriver: false }).start();
    }
  }, [loading, activeScenario, targetNetWorth]);

  // Re-animate chart on scenario change
  useEffect(() => {
    chartAnim.setValue(0);
    Animated.timing(chartAnim, { toValue: 1, duration: 600, useNativeDriver: false }).start();
  }, [activeScenario]);

  const wa = data?.wealthArrival;

  // Resolve active scenario data
  const activeScenarioData = wa?.scenarios?.find(
    (s: any) => s.scenario === activeScenario
  ) ?? wa?.primary;

  const primaryData = wa?.primary;

  const cycleTarget = (dir: 1 | -1) => {
    const idx = TARGET_AMOUNTS.indexOf(targetNetWorth);
    const next = idx + dir;
    if (next >= 0 && next < TARGET_AMOUNTS.length) {
      setTargetNetWorth(TARGET_AMOUNTS[next]);
    }
  };

  const scenarioColor = SCENARIO_CONFIG[activeScenario].color;

  // Compute arrival year for each scenario (for the pills in the hero card)
  const getArrivalYear = (scenarioName: Scenario) => {
    const s = wa?.scenarios?.find((sc: any) => sc.scenario === scenarioName);
    const years = s?.wealthArrivalYears ?? null;
    if (years == null) return '—';
    return String(currentYear + Math.round(years));
  };

  const primaryYears = activeScenarioData?.wealthArrivalYears;
  const arrivalYear  = primaryYears != null ? currentYear + Math.round(primaryYears) : null;
  const yearsAway    = primaryYears != null ? Math.round(primaryYears) : null;

  // ── Skeleton ────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <View style={styles.root}>
        <StatusBar barStyle="light-content" />
        <LinearGradient
          colors={['#0B1426', '#1E1B4B']}
          style={[styles.hero, { paddingTop: insets.top + 8 }]}
        >
          <View style={styles.heroTop}>
            <Pressable onPress={() => navigation.goBack()} style={{ marginRight: 12 }}>
              <Feather name="chevron-left" size={26} color={D.white} />
            </Pressable>
            <View style={{ flex: 1 }}>
              <Text style={styles.heroEyebrow}>WEALTH ARRIVAL</Text>
              <Text style={styles.heroTitle}>Your Wealth Journey</Text>
            </View>
          </View>
          <View style={styles.glassCard}>
            <ActivityIndicator size="large" color={D.white} />
            <Text style={{ color: 'rgba(255,255,255,0.6)', marginTop: 12, fontSize: 13 }}>
              Calculating your arrival…
            </Text>
          </View>
        </LinearGradient>
        <ScrollView contentContainerStyle={styles.listContent} showsVerticalScrollIndicator={false}>
          <SkeletonBlock height={64} />
          <SkeletonBlock height={140} />
          <SkeletonBlock height={100} />
          <SkeletonBlock height={200} />
          <SkeletonBlock height={160} />
        </ScrollView>
      </View>
    );
  }

  // ── Insufficient data state ─────────────────────────────────────────────────

  if (!wa || wa.dataQuality === 'insufficient') {
    return (
      <View style={styles.root}>
        <StatusBar barStyle="light-content" />
        <LinearGradient
          colors={['#0B1426', '#1E1B4B']}
          style={[styles.hero, { paddingTop: insets.top + 8 }]}
        >
          <View style={styles.heroTop}>
            <Pressable onPress={() => navigation.goBack()} style={{ marginRight: 12 }}>
              <Feather name="chevron-left" size={26} color={D.white} />
            </Pressable>
            <View style={{ flex: 1 }}>
              <Text style={styles.heroEyebrow}>WEALTH ARRIVAL</Text>
              <Text style={styles.heroTitle}>Your Wealth Journey</Text>
            </View>
          </View>
        </LinearGradient>
        <View style={styles.emptyStateWrap}>
          <View style={styles.emptyIconCircle}>
            <Feather name="map" size={32} color={D.indigo} />
          </View>
          <Text style={styles.emptyTitle}>Connect Your Accounts</Text>
          <Text style={styles.emptyBody}>
            Connect your financial accounts to see your personalised Wealth Arrival date — powered by your real income, savings, and net worth data.
          </Text>
          <Pressable
            style={styles.connectCta}
            onPress={() => navigation.navigate('BankAccounts')}
          >
            <LinearGradient colors={[D.indigo, D.purple]} style={styles.connectCtaGrad}>
              <Feather name="link" size={16} color={D.white} />
              <Text style={styles.connectCtaText}>Connect Accounts</Text>
            </LinearGradient>
          </Pressable>
        </View>
      </View>
    );
  }

  // ── Main render ─────────────────────────────────────────────────────────────

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      {/* ── Hero Header ─────────────────────────────────────────────────── */}
      <LinearGradient
        colors={['#0B1426', '#1E1B4B']}
        style={[styles.hero, { paddingTop: insets.top + 8 }]}
      >
        {/* Top row */}
        <View style={styles.heroTop}>
          <Pressable
            onPress={() => navigation.goBack()}
            style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }, { marginRight: 12 }]}
            accessibilityLabel="Go back"
          >
            <Feather name="chevron-left" size={26} color={D.white} />
          </Pressable>
          <View style={{ flex: 1 }}>
            <Text style={styles.heroEyebrow}>WEALTH ARRIVAL</Text>
            <Text style={styles.heroTitle}>Your Wealth Journey</Text>
          </View>
          {/* Target pill + adjuster */}
          <View style={styles.targetPillWrap}>
            <Pressable
              onPress={() => cycleTarget(-1)}
              style={({ pressed }) => [styles.targetAdj, { opacity: pressed ? 0.6 : 1 }]}
              hitSlop={8}
            >
              <Feather name="minus" size={12} color={D.white} />
            </Pressable>
            <View style={styles.targetPill}>
              <Text style={styles.targetPillEmoji}>🏁</Text>
              <Text style={styles.targetPillText}>Target: {fmtTargetLabel(targetNetWorth)}</Text>
            </View>
            <Pressable
              onPress={() => cycleTarget(1)}
              style={({ pressed }) => [styles.targetAdj, { opacity: pressed ? 0.6 : 1 }]}
              hitSlop={8}
            >
              <Feather name="plus" size={12} color={D.white} />
            </Pressable>
          </View>
        </View>

        {/* Glass-morphism Arrival Card */}
        <View style={styles.glassCard}>
          <Text style={styles.glassEyebrow}>YOU'LL ARRIVE</Text>

          <View style={styles.glassYearRow}>
            <Text style={styles.glassYear}>
              {arrivalYear != null ? String(arrivalYear) : '—'}
            </Text>
            {yearsAway != null && (
              <Text style={styles.glassYearSub}>
                in {yearsAway} {yearsAway === 1 ? 'year' : 'years'}
              </Text>
            )}
          </View>

          {/* Scenario arrival pills */}
          <View style={styles.scenarioPillsRow}>
            {(['Conservative', 'Moderate', 'Aggressive'] as Scenario[]).map((sc) => {
              const isActive = sc === activeScenario;
              const cfg = SCENARIO_CONFIG[sc];
              const yr = getArrivalYear(sc);
              return (
                <Pressable
                  key={sc}
                  onPress={() => setActiveScenario(sc)}
                  style={[
                    styles.scenarioYrPill,
                    isActive && { backgroundColor: cfg.color },
                  ]}
                >
                  <Text style={[
                    styles.scenarioYrLabel,
                    isActive && { color: D.white, fontWeight: '700' },
                  ]}>
                    {sc.slice(0, 3).toUpperCase()}
                  </Text>
                  <Text style={[
                    styles.scenarioYrValue,
                    isActive && { color: D.white },
                  ]}>
                    {yr}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>
      </LinearGradient>

      {/* ── Scrollable Content ──────────────────────────────────────────── */}
      <Animated.ScrollView
        style={{ opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
      >

        {/* ── Scenario Toggle ─────────────────────────────────────────────── */}
        <View style={styles.scenarioToggleRow}>
          {(['Conservative', 'Moderate', 'Aggressive'] as Scenario[]).map((sc) => {
            const isActive = sc === activeScenario;
            const cfg = SCENARIO_CONFIG[sc];
            return (
              <Pressable
                key={sc}
                onPress={() => setActiveScenario(sc)}
                style={({ pressed }) => [
                  styles.scenarioTogglePill,
                  isActive && { backgroundColor: cfg.color },
                  pressed && { opacity: 0.8 },
                ]}
              >
                <Text style={[
                  styles.scenarioToggleText,
                  isActive && { color: D.white, fontWeight: '700' },
                ]}>
                  {cfg.label}
                </Text>
              </Pressable>
            );
          })}
        </View>

        {/* ── Bar Chart Projection ────────────────────────────────────────── */}
        {activeScenarioData?.yearByYear?.length > 0 && (
          <BarChart
            yearByYear={activeScenarioData.yearByYear}
            currentNetWorth={wa.currentNetWorth ?? 0}
            targetNetWorth={targetNetWorth}
            accentColor={scenarioColor}
            chartAnim={chartAnim}
          />
        )}

        {/* ── Key Metrics Strip ───────────────────────────────────────────── */}
        <View style={styles.metricsStrip}>
          <MetricMini
            label="Annual Contrib."
            value={fmtShort(wa.annualContribution ?? 0)}
            color={D.green}
            icon="arrow-up-circle"
          />
          <MetricMini
            label="Savings Rate"
            value={(wa.savingsRatePct ?? 0).toFixed(1) + '%'}
            color={D.blue}
            icon="percent"
          />
          <MetricMini
            label="Final Net Worth"
            value={fmtShort(activeScenarioData?.finalNetWorth ?? 0)}
            color={D.indigo}
            icon="trending-up"
          />
          <MetricMini
            label="Annual Return"
            value={(activeScenarioData?.annualReturn ?? 0).toFixed(1) + '%'}
            color={D.amber}
            icon="activity"
          />
        </View>

        {/* ── Headline Card ────────────────────────────────────────────────── */}
        {wa.headlineSentence ? (
          <View style={styles.headlineCard}>
            <View style={styles.headlineAccent} />
            <View style={styles.headlineInner}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <Feather name="zap" size={14} color={D.indigo} />
                <Text style={styles.headlineEyebrow}>YOUR WEALTH HEADLINE</Text>
              </View>
              <Text style={styles.headlineText}>"{wa.headlineSentence}"</Text>
            </View>
          </View>
        ) : null}

        {/* ── Milestones Timeline ──────────────────────────────────────────── */}
        {primaryData?.milestones?.length > 0 && (
          <MilestonesSection milestones={primaryData.milestones} accentColor={scenarioColor} />
        )}

        {/* ── Income & Contributions Card ──────────────────────────────────── */}
        <IncomeCard
          monthlyIncome={wa.estimatedMonthlyIncome ?? 0}
          surplus={wa.investableSurplusMonthly ?? 0}
          annualContrib={wa.annualContribution ?? 0}
          savingsRate={wa.savingsRatePct ?? 0}
          accentColor={scenarioColor}
        />

        <View style={{ height: 40 }} />
      </Animated.ScrollView>
    </View>
  );
}

// ── Bar Chart Component ───────────────────────────────────────────────────────

interface BarChartProps {
  yearByYear: Array<{ year: number; netWorth: number }>;
  currentNetWorth: number;
  targetNetWorth: number;
  accentColor: string;
  chartAnim: Animated.Value;
}

function BarChart({ yearByYear, currentNetWorth, targetNetWorth, accentColor, chartAnim }: BarChartProps) {
  // Sample to max 30 bars for readability
  const maxBars = 30;
  const step    = Math.max(1, Math.ceil(yearByYear.length / maxBars));
  const bars    = yearByYear.filter((_, i) => i % step === 0);

  const maxNW   = Math.max(...bars.map((b) => b.netWorth), targetNetWorth, currentNetWorth, 1);

  const barWidth = Math.max(4, Math.floor((SCREEN_WIDTH - 64) / bars.length) - 2);

  const baselineH = (currentNetWorth / maxNW) * BAR_MAX_HEIGHT;
  const targetH   = (targetNetWorth  / maxNW) * BAR_MAX_HEIGHT;

  return (
    <View style={styles.chartCard}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <Feather name="bar-chart-2" size={14} color={accentColor} />
        <Text style={styles.chartTitle}>Net Worth Projection</Text>
      </View>
      <Text style={styles.chartSubtitle}>
        {bars[0]?.year} – {bars[bars.length - 1]?.year}
      </Text>

      <View style={[styles.chartArea, { height: CHART_HEIGHT }]}>
        {/* Baseline (current NW) dotted line */}
        <View
          style={[
            styles.chartBaseline,
            { bottom: baselineH + 10, borderColor: 'rgba(148,163,184,0.5)' },
          ]}
          pointerEvents="none"
        />

        {/* Target dashed golden line */}
        <View
          style={[
            styles.chartTarget,
            { bottom: targetH + 10, borderColor: D.amber },
          ]}
          pointerEvents="none"
        />

        {/* Target label */}
        <Text
          style={[
            styles.chartTargetLabel,
            { bottom: targetH + 14, color: D.amber },
          ]}
        >
          {fmtShort(targetNetWorth)}
        </Text>

        {/* Bars */}
        <View style={styles.chartBarsRow}>
          {bars.map((bar, i) => {
            const proportion = bar.netWorth / maxNW;
            const maxH = proportion * BAR_MAX_HEIGHT;
            const opacity = 0.4 + (i / bars.length) * 0.6;
            const isTarget = bar.netWorth >= targetNetWorth;

            return (
              <View key={bar.year} style={styles.chartBarWrap}>
                <Animated.View
                  style={[
                    styles.chartBar,
                    {
                      width: barWidth,
                      height: chartAnim.interpolate({
                        inputRange: [0, 1],
                        outputRange: [0, maxH],
                      }),
                      backgroundColor: isTarget ? D.amber : accentColor,
                      opacity,
                      borderTopLeftRadius: 2,
                      borderTopRightRadius: 2,
                    },
                  ]}
                />
                {i % 5 === 0 && (
                  <Text style={styles.chartYearLabel}>
                    {String(bar.year).slice(2)}
                  </Text>
                )}
              </View>
            );
          })}
        </View>
      </View>

      {/* Legend */}
      <View style={styles.chartLegend}>
        <View style={styles.chartLegendItem}>
          <View style={[styles.chartLegendDot, { backgroundColor: accentColor }]} />
          <Text style={styles.chartLegendText}>Net Worth</Text>
        </View>
        <View style={styles.chartLegendItem}>
          <View style={[styles.chartLegendDot, { backgroundColor: D.amber }]} />
          <Text style={styles.chartLegendText}>Target</Text>
        </View>
        <View style={styles.chartLegendItem}>
          <View style={[styles.chartLegendDash, { borderColor: 'rgba(148,163,184,0.7)' }]} />
          <Text style={styles.chartLegendText}>Current NW</Text>
        </View>
      </View>
    </View>
  );
}

// ── Metric Mini Card ──────────────────────────────────────────────────────────

interface MetricMiniProps {
  label: string;
  value: string;
  color: string;
  icon: keyof typeof Feather.glyphMap;
}

function MetricMini({ label, value, color, icon }: MetricMiniProps) {
  return (
    <View style={[styles.metricMini, { borderTopColor: color }]}>
      <Feather name={icon} size={13} color={color} style={{ marginBottom: 6 }} />
      <Text style={[styles.metricMiniValue, { color }]}>{value}</Text>
      <Text style={styles.metricMiniLabel}>{label}</Text>
    </View>
  );
}

// ── Milestones Section ────────────────────────────────────────────────────────

interface Milestone {
  targetAmount: number;
  yearsAway: number;
  arrivalYear: number;
  alreadyAchieved: boolean;
  label?: string;
}

function MilestonesSection({ milestones, accentColor }: { milestones: Milestone[]; accentColor: string }) {
  const visible = milestones.slice(0, 8);

  return (
    <View style={styles.card}>
      <View style={[styles.cardAccentLine, { backgroundColor: accentColor }]} />
      <View style={styles.cardInner}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <Feather name="flag" size={14} color={accentColor} />
          <Text style={styles.sectionTitle}>Milestones</Text>
        </View>
        {visible.map((m, i) => (
          <MilestoneRow key={i} milestone={m} index={i} accentColor={accentColor} />
        ))}
      </View>
    </View>
  );
}

function MilestoneRow({
  milestone: m,
  index,
  accentColor,
}: {
  milestone: Milestone;
  index: number;
  accentColor: string;
}) {
  const slideAnim = useRef(new Animated.Value(20)).current;
  const fadeAnim  = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim,  { toValue: 1, duration: 350, delay: index * 60, useNativeDriver: true }),
      Animated.timing(slideAnim, { toValue: 0, duration: 350, delay: index * 60, useNativeDriver: true }),
    ]).start();
  }, []);

  const dotColor = m.alreadyAchieved ? D.green : accentColor;

  return (
    <Animated.View
      style={[
        styles.milestoneRow,
        { opacity: fadeAnim, transform: [{ translateX: slideAnim }] },
      ]}
    >
      {/* Connector line */}
      {index > 0 && <View style={[styles.milestoneConnector, { backgroundColor: dotColor }]} />}

      {/* Dot */}
      <View style={[styles.milestoneDot, { backgroundColor: dotColor }]}>
        {m.alreadyAchieved && (
          <Feather name="check" size={9} color={D.white} />
        )}
      </View>

      {/* Content */}
      <View style={styles.milestoneContent}>
        <Text style={styles.milestoneAmount}>{fmtShort(m.targetAmount)}</Text>
        {m.label ? <Text style={styles.milestoneLabel}>{m.label}</Text> : null}
      </View>

      {/* Right side */}
      <View style={{ alignItems: 'flex-end', gap: 4 }}>
        {m.alreadyAchieved ? (
          <View style={styles.achievedBadge}>
            <Text style={styles.achievedBadgeText}>✓ Achieved</Text>
          </View>
        ) : (
          <View style={[styles.yearPill, { backgroundColor: `${accentColor}18` }]}>
            <Text style={[styles.yearPillText, { color: accentColor }]}>
              {m.arrivalYear}
            </Text>
          </View>
        )}
        {!m.alreadyAchieved && m.yearsAway != null && (
          <Text style={styles.yearsAwayText}>in {Math.round(m.yearsAway)}y</Text>
        )}
      </View>
    </Animated.View>
  );
}

// ── Income & Contributions Card ───────────────────────────────────────────────

interface IncomeCardProps {
  monthlyIncome: number;
  surplus: number;
  annualContrib: number;
  savingsRate: number;
  accentColor: string;
}

function IncomeCard({ monthlyIncome, surplus, annualContrib, savingsRate, accentColor }: IncomeCardProps) {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const onPressIn  = () => Animated.spring(scaleAnim, { toValue: 0.975, useNativeDriver: true, speed: 50 }).start();
  const onPressOut = () => Animated.spring(scaleAnim, { toValue: 1,     useNativeDriver: true, speed: 50 }).start();

  const safeRate = Math.min(Math.max(savingsRate, 0), 100);

  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
      <Pressable onPressIn={onPressIn} onPressOut={onPressOut} style={styles.card}>
        <View style={[styles.cardAccentLine, { backgroundColor: D.green }]} />
        <View style={styles.cardInner}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Feather name="dollar-sign" size={14} color={D.green} />
            <Text style={styles.sectionTitle}>Income & Contributions</Text>
          </View>

          <View style={styles.incomeRow}>
            <IncomeItem label="Monthly Income"       value={fmtShort(monthlyIncome)}   color={D.textPrimary} />
            <IncomeItem label="Investable Surplus"   value={fmtShort(surplus)}          color={D.green} />
            <IncomeItem label="Annual Contribution"  value={fmtShort(annualContrib)}    color={D.indigo} />
          </View>

          {/* Savings rate bar */}
          <View style={{ marginTop: 16 }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 }}>
              <Text style={styles.incomeBarLabel}>Savings Rate</Text>
              <Text style={[styles.incomeBarPct, { color: accentColor }]}>
                {safeRate.toFixed(1)}%
              </Text>
            </View>
            <View style={styles.incomeBarTrack}>
              <View
                style={[
                  styles.incomeBarFill,
                  {
                    width: `${safeRate}%` as any,
                    backgroundColor: accentColor,
                  },
                ]}
              />
            </View>
            <Text style={styles.incomeBarHint}>
              {safeRate < 10
                ? 'Increasing contributions will accelerate your arrival date.'
                : safeRate < 20
                ? 'Good momentum — small increases compound significantly over time.'
                : 'Excellent savings discipline powering your wealth engine.'}
            </Text>
          </View>
        </View>
      </Pressable>
    </Animated.View>
  );
}

function IncomeItem({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <View style={styles.incomeItem}>
      <Text style={[styles.incomeValue, { color }]}>{value}</Text>
      <Text style={styles.incomeLabel}>{label}</Text>
    </View>
  );
}

// ── Skeleton Shimmer ──────────────────────────────────────────────────────────

function SkeletonBlock({ height }: { height: number }) {
  const shimmer = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, { toValue: 1, duration: 900, useNativeDriver: true }),
        Animated.timing(shimmer, { toValue: 0, duration: 900, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  return (
    <Animated.View
      style={[
        styles.skeletonBlock,
        {
          height,
          opacity: shimmer.interpolate({ inputRange: [0, 1], outputRange: [0.4, 0.8] }),
        },
      ]}
    />
  );
}

// ── Styles ─────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: D.bg },

  // Hero
  hero: {
    paddingHorizontal: 20,
    paddingBottom: 24,
  },
  heroTop: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 20,
    paddingTop: 4,
  },
  heroEyebrow: {
    fontSize: 10,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.45)',
    letterSpacing: 1.8,
    marginBottom: 4,
  },
  heroTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: D.white,
    letterSpacing: -0.5,
  },

  // Target pill
  targetPillWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginLeft: 8,
    marginTop: 6,
  },
  targetAdj: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: 'rgba(255,255,255,0.12)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  targetPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: 'rgba(255,255,255,0.12)',
    borderRadius: 99,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: 'rgba(255,255,255,0.2)',
  },
  targetPillEmoji: { fontSize: 12 },
  targetPillText: {
    fontSize: 12,
    fontWeight: '700',
    color: D.white,
    letterSpacing: 0.3,
  },

  // Glass card (arrival hero)
  glassCard: {
    backgroundColor: 'rgba(255,255,255,0.09)',
    borderRadius: 20,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: 'rgba(255,255,255,0.18)',
    padding: 20,
    alignItems: 'center',
  },
  glassEyebrow: {
    fontSize: 10,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.5)',
    letterSpacing: 2,
    marginBottom: 6,
  },
  glassYearRow: {
    alignItems: 'center',
    marginBottom: 16,
  },
  glassYear: {
    fontSize: 64,
    fontWeight: '800',
    color: D.white,
    letterSpacing: -2,
    lineHeight: 68,
  },
  glassYearSub: {
    fontSize: 16,
    fontWeight: '500',
    color: 'rgba(255,255,255,0.55)',
    marginTop: 2,
  },
  scenarioPillsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  scenarioYrPill: {
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 12,
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: 'rgba(255,255,255,0.15)',
    minWidth: 72,
  },
  scenarioYrLabel: {
    fontSize: 9,
    fontWeight: '600',
    color: 'rgba(255,255,255,0.5)',
    letterSpacing: 1.2,
    marginBottom: 3,
  },
  scenarioYrValue: {
    fontSize: 15,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.85)',
  },

  // Scenario toggle
  scenarioToggleRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  scenarioTogglePill: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: D.card,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: D.cardBorder,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
  },
  scenarioToggleText: {
    fontSize: 13,
    fontWeight: '500',
    color: D.textSecondary,
  },

  // Chart
  chartCard: {
    backgroundColor: D.card,
    borderRadius: 16,
    padding: 16,
    marginBottom: 14,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 12,
    elevation: 3,
  },
  chartTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: D.textPrimary,
  },
  chartSubtitle: {
    fontSize: 11,
    color: D.textMuted,
    marginBottom: 12,
    marginLeft: 22,
  },
  chartArea: {
    position: 'relative',
    overflow: 'hidden',
  },
  chartBarsRow: {
    position: 'absolute',
    bottom: 22,
    left: 0,
    right: 0,
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 1,
    paddingHorizontal: 4,
  },
  chartBarWrap: {
    alignItems: 'center',
    justifyContent: 'flex-end',
  },
  chartBar: {
    borderRadius: 2,
  },
  chartYearLabel: {
    fontSize: 8,
    color: D.textMuted,
    marginTop: 3,
    fontWeight: '500',
  },
  chartBaseline: {
    position: 'absolute',
    left: 4,
    right: 4,
    height: 0,
    borderTopWidth: 1,
    borderStyle: 'dotted',
  },
  chartTarget: {
    position: 'absolute',
    left: 4,
    right: 4,
    height: 0,
    borderTopWidth: 1.5,
    borderStyle: 'dashed',
  },
  chartTargetLabel: {
    position: 'absolute',
    right: 8,
    fontSize: 9,
    fontWeight: '700',
  },
  chartLegend: {
    flexDirection: 'row',
    gap: 14,
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: D.cardBorder,
  },
  chartLegendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  chartLegendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  chartLegendDash: {
    width: 14,
    height: 0,
    borderTopWidth: 1.5,
    borderStyle: 'dotted',
  },
  chartLegendText: {
    fontSize: 11,
    color: D.textSecondary,
    fontWeight: '500',
  },

  // Metrics strip
  metricsStrip: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 14,
  },
  metricMini: {
    flex: 1,
    backgroundColor: D.card,
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
    borderTopWidth: 3,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
  },
  metricMiniValue: {
    fontSize: 14,
    fontWeight: '800',
    letterSpacing: -0.3,
  },
  metricMiniLabel: {
    fontSize: 9,
    fontWeight: '500',
    color: D.textMuted,
    textAlign: 'center',
    marginTop: 3,
    letterSpacing: 0.2,
  },

  // Headline card
  headlineCard: {
    backgroundColor: D.indigoFaint,
    borderRadius: 16,
    marginBottom: 14,
    flexDirection: 'row',
    overflow: 'hidden',
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 2,
  },
  headlineAccent: {
    width: 4,
    backgroundColor: D.indigo,
  },
  headlineInner: {
    flex: 1,
    padding: 16,
  },
  headlineEyebrow: {
    fontSize: 9,
    fontWeight: '700',
    color: D.indigo,
    letterSpacing: 1.5,
  },
  headlineText: {
    fontSize: 14,
    fontStyle: 'italic',
    color: '#312E81',
    lineHeight: 21,
    fontWeight: '500',
  },

  // Card base
  card: {
    backgroundColor: D.card,
    borderRadius: 16,
    marginBottom: 14,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 12,
    elevation: 3,
    overflow: 'hidden',
  },
  cardAccentLine: {
    height: 3,
    width: '100%',
  },
  cardInner: {
    padding: 18,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: D.textPrimary,
  },

  // Milestone rows
  milestoneRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
    position: 'relative',
  },
  milestoneConnector: {
    position: 'absolute',
    left: 8,
    top: -14,
    width: 1.5,
    height: 14,
    opacity: 0.25,
  },
  milestoneDot: {
    width: 18,
    height: 18,
    borderRadius: 9,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    flexShrink: 0,
  },
  milestoneContent: { flex: 1 },
  milestoneAmount: {
    fontSize: 15,
    fontWeight: '700',
    color: D.textPrimary,
  },
  milestoneLabel: {
    fontSize: 11,
    color: D.textSecondary,
    marginTop: 1,
  },
  achievedBadge: {
    backgroundColor: D.greenFaint,
    borderRadius: 99,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  achievedBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: D.green,
  },
  yearPill: {
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  yearPillText: {
    fontSize: 12,
    fontWeight: '700',
  },
  yearsAwayText: {
    fontSize: 10,
    color: D.textMuted,
    fontWeight: '500',
  },

  // Income card
  incomeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  incomeItem: { alignItems: 'center', flex: 1 },
  incomeValue: {
    fontSize: 15,
    fontWeight: '800',
    letterSpacing: -0.3,
  },
  incomeLabel: {
    fontSize: 10,
    color: D.textMuted,
    fontWeight: '500',
    marginTop: 3,
    textAlign: 'center',
  },
  incomeBarLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: D.textSecondary,
  },
  incomeBarPct: {
    fontSize: 13,
    fontWeight: '800',
  },
  incomeBarTrack: {
    height: 8,
    backgroundColor: D.bg,
    borderRadius: 4,
    overflow: 'hidden',
  },
  incomeBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  incomeBarHint: {
    fontSize: 11,
    color: D.textMuted,
    marginTop: 6,
    lineHeight: 16,
  },

  // List container
  listContent: {
    paddingHorizontal: 16,
    paddingTop: 16,
  },

  // Empty state
  emptyStateWrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  emptyIconCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: D.indigoFaint,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: D.textPrimary,
    marginBottom: 10,
    textAlign: 'center',
  },
  emptyBody: {
    fontSize: 14,
    color: D.textSecondary,
    textAlign: 'center',
    lineHeight: 21,
    marginBottom: 28,
  },
  connectCta: {
    borderRadius: 14,
    overflow: 'hidden',
    shadowColor: D.indigo,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 5,
  },
  connectCtaGrad: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 28,
    paddingVertical: 14,
  },
  connectCtaText: {
    fontSize: 15,
    fontWeight: '700',
    color: D.white,
  },

  // Skeleton
  skeletonBlock: {
    backgroundColor: D.cardBorder,
    borderRadius: 16,
    marginBottom: 14,
  },
});
