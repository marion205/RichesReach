/**
 * Net Worth Screen — 2026 Premium Design
 * ========================================
 * Financial GPS: full wealth story in one premium view.
 *
 * Sections:
 *  - Dark navy hero with sparkline chart and animated big number
 *  - 30-day change chip + growth streak badge
 *  - Time range selector (1M / 3M / 6M / 1Y)
 *  - 2×2 change metrics grid (7D / 30D / 90D / 1Y)
 *  - Breakdown card (Portfolio / Savings / Debt)
 *  - Personal Records card (all-time high / low)
 *  - Headline sentence card (indigo tint, italic)
 *  - Loading skeleton + insufficient-data empty state
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  Animated,
  RefreshControl,
  StatusBar,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Feather } from '@expo/vector-icons';
import { useQuery } from '@apollo/client';
import { GET_NET_WORTH_HISTORY } from '../../../graphql/financialGps';

// ── Types ──────────────────────────────────────────────────────────────────────

interface HistoryPoint {
  capturedAt: string;
  netWorth: number;
  portfolioValue: number;
  savingsBalance: number;
  debt: number;
}

interface NetWorthData {
  userId: string;
  currentNetWorth: number;
  currentPortfolioValue: number;
  currentSavingsBalance: number;
  currentDebt: number;
  change7d: number | null;
  change30d: number | null;
  change90d: number | null;
  change1yr: number | null;
  changePct30d: number | null;
  allTimeHigh: number | null;
  allTimeHighDate: string | null;
  allTimeLow: number | null;
  allTimeLowDate: string | null;
  increaseStreakDays: number;
  snapshotCapturedToday: boolean;
  dataQuality: 'live' | 'estimated' | 'insufficient';
  headlineSentence: string | null;
  history: HistoryPoint[];
}

interface Props {
  navigation?: any;
  route?: any;
}

// ── Constants ──────────────────────────────────────────────────────────────────

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ── Design Tokens ──────────────────────────────────────────────────────────────

const D = {
  navy:          '#0B1426',
  navyMid:       '#0F1E35',
  navyLight:     '#162642',
  blue:          '#3B82F6',
  green:         '#10B981',
  red:           '#EF4444',
  amber:         '#F59E0B',
  indigo:        '#6366F1',
  white:         '#FFFFFF',
  textPrimary:   '#0F172A',
  textSecondary: '#64748B',
  textMuted:     '#94A3B8',
  card:          '#FFFFFF',
  cardBorder:    '#E2E8F0',
  bg:            '#F1F5F9',
  // Extended
  offWhite:      '#F8FAFC',
  greenFaint:    '#D1FAE5',
  redFaint:      '#FEE2E2',
  amberFaint:    '#FEF3C7',
  indigoFaint:   '#EEF2FF',
  blueFaint:     '#EFF6FF',
};

// ── Time Range Config ──────────────────────────────────────────────────────────

type TimeRange = '1M' | '3M' | '6M' | '1Y';

const TIME_RANGES: { label: TimeRange; days: number }[] = [
  { label: '1M', days: 30  },
  { label: '3M', days: 90  },
  { label: '6M', days: 180 },
  { label: '1Y', days: 365 },
];

// ── Helpers ────────────────────────────────────────────────────────────────────

const fmt = (n: number): string =>
  n >= 1_000_000
    ? '$' + (n / 1_000_000).toFixed(2) + 'M'
    : '$' + n.toLocaleString('en-US', { maximumFractionDigits: 0 });

const fmtDate = (iso: string | null): string => {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return iso;
  }
};

const fmtChange = (n: number | null): string => {
  if (n === null || n === undefined) return '—';
  const abs = Math.abs(n);
  const sign = n >= 0 ? '+' : '-';
  return sign + fmt(abs).replace('$', '') !== '—'
    ? sign + '$' + Math.abs(n).toLocaleString('en-US', { maximumFractionDigits: 0 })
    : '—';
};

// ── Main Component ─────────────────────────────────────────────────────────────

export default function NetWorthScreen({ navigation }: Props) {
  const [selectedRange, setSelectedRange] = useState<TimeRange>('3M');
  const [selectedDays, setSelectedDays] = useState(90);

  const { data, loading, error, refetch } = useQuery(GET_NET_WORTH_HISTORY, {
    variables: { days: selectedDays },
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  // Entrance animation
  const fadeAnim  = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;

  // Animated counter for big number
  const countAnim = useRef(new Animated.Value(0)).current;
  const [displayedValue, setDisplayedValue] = useState(0);

  const nw: NetWorthData | null = data?.netWorthHistory ?? null;

  // Trigger entrance once data arrives
  useEffect(() => {
    if (!loading && nw) {
      Animated.parallel([
        Animated.timing(fadeAnim,  { toValue: 1, duration: 500, useNativeDriver: true }),
        Animated.timing(slideAnim, { toValue: 0, duration: 500, useNativeDriver: true }),
      ]).start();

      // Animate counter from 0 to currentNetWorth
      countAnim.setValue(0);
      Animated.timing(countAnim, {
        toValue: nw.currentNetWorth,
        duration: 1200,
        useNativeDriver: false,
      }).start();
      countAnim.addListener(({ value }) => setDisplayedValue(Math.round(value)));
    }
    return () => countAnim.removeAllListeners();
  }, [loading, nw?.currentNetWorth]);

  const handleRangeSelect = useCallback((range: TimeRange, days: number) => {
    setSelectedRange(range);
    setSelectedDays(days);
    refetch({ days });
  }, [refetch]);

  const is30dUp = (nw?.change30d ?? 0) >= 0;
  const isInsufficientData = nw?.dataQuality === 'insufficient';

  // Sparkline: last 30 history points normalised to bar heights
  const historyPoints = (nw?.history ?? []).slice(-30);
  const sparkValues = historyPoints.map(h => h.netWorth);
  const sparkMin = sparkValues.length ? Math.min(...sparkValues) : 0;
  const sparkMax = sparkValues.length ? Math.max(...sparkValues) : 1;
  const sparkRange = sparkMax - sparkMin || 1;
  const sparkTrending = sparkValues.length >= 2
    ? sparkValues[sparkValues.length - 1] >= sparkValues[0]
    : true;
  const sparkColor = sparkTrending ? D.green : D.red;

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      {/* ── Hero Header ─────────────────────────────────────────────────── */}
      <LinearGradient
        colors={[D.navy, D.navyLight]}
        style={styles.hero}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <SafeAreaView edges={['top']} style={styles.heroSafe}>
          {/* Top row: back + eyebrow/title + quality badge */}
          <View style={styles.heroTop}>
            <Pressable
              onPress={() => navigation?.goBack()}
              style={({ pressed }) => [styles.backBtn, { opacity: pressed ? 0.6 : 1 }]}
              accessibilityLabel="Go back"
            >
              <Feather name="chevron-left" size={24} color={D.white} />
            </Pressable>

            <View style={styles.heroTitleBlock}>
              <Text style={styles.heroEyebrow}>NET WORTH</Text>
              <Text style={styles.heroTitle}>Your Wealth Story</Text>
            </View>

            {nw && (
              <View
                style={[
                  styles.qualityBadge,
                  {
                    backgroundColor:
                      nw.dataQuality === 'live'
                        ? 'rgba(16,185,129,0.18)'
                        : 'rgba(245,158,11,0.18)',
                    borderColor:
                      nw.dataQuality === 'live'
                        ? 'rgba(16,185,129,0.4)'
                        : 'rgba(245,158,11,0.4)',
                  },
                ]}
              >
                <View
                  style={[
                    styles.qualityDot,
                    {
                      backgroundColor:
                        nw.dataQuality === 'live' ? D.green : D.amber,
                    },
                  ]}
                />
                <Text
                  style={[
                    styles.qualityText,
                    {
                      color:
                        nw.dataQuality === 'live' ? D.green : D.amber,
                    },
                  ]}
                >
                  {nw.dataQuality === 'live' ? 'LIVE DATA' : 'ESTIMATED'}
                </Text>
              </View>
            )}
          </View>

          {/* ── Big Number ───────────────────────────────────────────────── */}
          {loading && !nw ? (
            <View style={styles.heroBigNumSkeleton} />
          ) : nw ? (
            <View style={styles.heroBigNumBlock}>
              <Text style={styles.heroBigNum}>{fmt(displayedValue)}</Text>

              {/* 30d change chip */}
              {nw.change30d !== null && (
                <View
                  style={[
                    styles.changeChip,
                    {
                      backgroundColor: is30dUp
                        ? 'rgba(16,185,129,0.18)'
                        : 'rgba(239,68,68,0.18)',
                    },
                  ]}
                >
                  <Feather
                    name={is30dUp ? 'arrow-up-right' : 'arrow-down-right'}
                    size={13}
                    color={is30dUp ? D.green : D.red}
                  />
                  <Text
                    style={[
                      styles.changeChipText,
                      { color: is30dUp ? D.green : D.red },
                    ]}
                  >
                    {fmtChange(nw.change30d)}
                    {nw.changePct30d !== null
                      ? ` (${nw.changePct30d >= 0 ? '+' : ''}${nw.changePct30d.toFixed(1)}%)`
                      : ''}
                  </Text>
                </View>
              )}

              {/* Streak badge */}
              {nw.increaseStreakDays >= 7 && (
                <View style={styles.streakBadge}>
                  <Text style={styles.streakText}>
                    {'\uD83D\uDD25'} {nw.increaseStreakDays}-day streak
                  </Text>
                </View>
              )}
            </View>
          ) : null}

          {/* ── Sparkline Chart ──────────────────────────────────────────── */}
          {sparkValues.length > 1 && (
            <View style={styles.sparkContainer}>
              {sparkValues.map((val, i) => {
                const heightPct = ((val - sparkMin) / sparkRange) * 100;
                const barHeight = Math.max(4, (heightPct / 100) * 48);
                const isLast = i === sparkValues.length - 1;
                return (
                  <View
                    key={i}
                    style={[
                      styles.sparkBar,
                      {
                        height: barHeight,
                        backgroundColor: isLast
                          ? sparkColor
                          : `${sparkColor}60`,
                        opacity: isLast ? 1 : 0.55 + (i / sparkValues.length) * 0.45,
                      },
                    ]}
                  />
                );
              })}
            </View>
          )}

          {/* Time range selector pinned to bottom of hero */}
          <View style={styles.timeRangeRow}>
            {TIME_RANGES.map(({ label, days }) => {
              const isActive = selectedRange === label;
              return (
                <Pressable
                  key={label}
                  onPress={() => handleRangeSelect(label, days)}
                  style={({ pressed }) => [
                    styles.rangeTab,
                    isActive && styles.rangeTabActive,
                    { opacity: pressed ? 0.75 : 1 },
                  ]}
                  accessibilityRole="tab"
                  accessibilityState={{ selected: isActive }}
                >
                  <Text
                    style={[
                      styles.rangeTabText,
                      isActive && styles.rangeTabTextActive,
                    ]}
                  >
                    {label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </SafeAreaView>
      </LinearGradient>

      {/* ── Scrollable Body ──────────────────────────────────────────────── */}
      <Animated.ScrollView
        style={{ flex: 1, opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={() => refetch({ days: selectedDays })}
            tintColor={D.blue}
          />
        }
      >
        {/* Loading skeleton */}
        {loading && !nw && <SkeletonBody />}

        {/* Insufficient data empty state */}
        {!loading && isInsufficientData && <InsufficientDataCard navigation={navigation} />}

        {/* Error state */}
        {!loading && error && !nw && (
          <View style={styles.errorCard}>
            <Feather name="alert-circle" size={28} color={D.red} />
            <Text style={styles.errorTitle}>Could not load data</Text>
            <Text style={styles.errorBody}>
              Pull down to retry, or check your connection.
            </Text>
          </View>
        )}

        {/* Main content — render when we have data (even if dataQuality !== 'insufficient') */}
        {nw && !isInsufficientData && (
          <>
            {/* 2×2 Change Metrics Grid */}
            <Text style={styles.sectionLabel}>PERFORMANCE</Text>
            <View style={styles.gridRow}>
              <ChangeCard label="7D" value={nw.change7d} />
              <ChangeCard label="30D" value={nw.change30d} />
            </View>
            <View style={styles.gridRow}>
              <ChangeCard label="90D" value={nw.change90d} />
              <ChangeCard label="1 YEAR" value={nw.change1yr} />
            </View>

            {/* Breakdown card */}
            <Text style={styles.sectionLabel}>BREAKDOWN TODAY</Text>
            <View style={styles.card}>
              <BreakdownRow
                icon="briefcase"
                label="Portfolio"
                amount={nw.currentPortfolioValue}
                color={D.blue}
                isDebt={false}
              />
              <View style={styles.divider} />
              <BreakdownRow
                icon="dollar-sign"
                label="Savings"
                amount={nw.currentSavingsBalance}
                color={D.green}
                isDebt={false}
              />
              <View style={styles.divider} />
              <BreakdownRow
                icon="credit-card"
                label="Debt"
                amount={nw.currentDebt}
                color={D.red}
                isDebt={true}
              />
            </View>

            {/* Personal Records card */}
            {(nw.allTimeHigh !== null || nw.allTimeLow !== null) && (
              <>
                <Text style={styles.sectionLabel}>PERSONAL RECORDS</Text>
                <View style={styles.card}>
                  {nw.allTimeHigh !== null && (
                    <View style={styles.recordRow}>
                      <View
                        style={[styles.recordIconWrap, { backgroundColor: D.greenFaint }]}
                      >
                        <Feather name="award" size={16} color={D.green} />
                      </View>
                      <View style={styles.recordContent}>
                        <Text style={styles.recordLabel}>All-Time High</Text>
                        <Text style={[styles.recordValue, { color: D.green }]}>
                          {fmt(nw.allTimeHigh)}
                        </Text>
                        <Text style={styles.recordDate}>
                          {fmtDate(nw.allTimeHighDate)}
                        </Text>
                      </View>
                    </View>
                  )}
                  {nw.allTimeHigh !== null && nw.allTimeLow !== null && (
                    <View style={styles.divider} />
                  )}
                  {nw.allTimeLow !== null && (
                    <View style={styles.recordRow}>
                      <View
                        style={[styles.recordIconWrap, { backgroundColor: D.redFaint }]}
                      >
                        <Feather name="alert-triangle" size={16} color={D.red} />
                      </View>
                      <View style={styles.recordContent}>
                        <Text style={styles.recordLabel}>All-Time Low</Text>
                        <Text style={[styles.recordValue, { color: D.red }]}>
                          {fmt(nw.allTimeLow)}
                        </Text>
                        <Text style={styles.recordDate}>
                          {fmtDate(nw.allTimeLowDate)}
                        </Text>
                      </View>
                    </View>
                  )}
                </View>
              </>
            )}

            {/* Headline sentence card */}
            {!!nw.headlineSentence && (
              <>
                <Text style={styles.sectionLabel}>INSIGHTS</Text>
                <View style={styles.headlineCard}>
                  <View style={styles.headlineAccent} />
                  <View style={styles.headlineInner}>
                    <View style={styles.headlineIconRow}>
                      <View style={styles.headlineIconWrap}>
                        <Feather name="zap" size={14} color={D.indigo} />
                      </View>
                      <Text style={styles.headlineEyebrow}>AI SUMMARY</Text>
                    </View>
                    <Text style={styles.headlineText}>"{nw.headlineSentence}"</Text>
                  </View>
                </View>
              </>
            )}

            <View style={{ height: 40 }} />
          </>
        )}
      </Animated.ScrollView>
    </View>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function ChangeCard({ label, value }: { label: string; value: number | null }) {
  const isNull = value === null || value === undefined;
  const isUp   = !isNull && value! >= 0;
  const color  = isNull ? D.textMuted : isUp ? D.green : D.red;
  const bg     = isNull ? D.bg : isUp ? D.greenFaint : D.redFaint;

  return (
    <View style={[styles.changeCard, { backgroundColor: D.card }]}>
      <Text style={styles.changeCardLabel}>{label}</Text>
      <View style={[styles.changeCardValueWrap, { backgroundColor: bg }]}>
        {!isNull && (
          <Feather
            name={isUp ? 'trending-up' : 'trending-down'}
            size={12}
            color={color}
            style={{ marginRight: 4 }}
          />
        )}
        <Text style={[styles.changeCardValue, { color }]}>
          {isNull ? '—' : fmtChange(value)}
        </Text>
      </View>
    </View>
  );
}

function BreakdownRow({
  icon,
  label,
  amount,
  color,
  isDebt,
}: {
  icon: keyof typeof Feather.glyphMap;
  label: string;
  amount: number;
  color: string;
  isDebt: boolean;
}) {
  return (
    <View style={styles.breakdownRow}>
      <View style={[styles.breakdownIconWrap, { backgroundColor: `${color}18` }]}>
        <Feather name={icon} size={16} color={color} />
      </View>
      <Text style={styles.breakdownLabel}>{label}</Text>
      <Text style={[styles.breakdownAmount, { color }]}>
        {isDebt ? `−${fmt(amount)}` : fmt(amount)}
      </Text>
    </View>
  );
}

function InsufficientDataCard({ navigation }: { navigation?: any }) {
  return (
    <View style={styles.emptyCard}>
      <LinearGradient
        colors={['#EEF2FF', '#F8FAFF']}
        style={styles.emptyGradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        {/* Illustration: concentric rings */}
        <View style={styles.emptyIllustration}>
          <View style={[styles.emptyRing, { width: 80, height: 80, borderColor: `${D.indigo}20` }]} />
          <View style={[styles.emptyRing, { width: 56, height: 56, borderColor: `${D.indigo}30` }]} />
          <View style={[styles.emptyRingCenter]}>
            <Feather name="trending-up" size={22} color={D.indigo} />
          </View>
        </View>

        <Text style={styles.emptyTitle}>Start Your Wealth Journey</Text>
        <Text style={styles.emptyBody}>
          Connect your accounts to start tracking your wealth journey and unlock
          powerful net worth insights.
        </Text>

        <Pressable
          onPress={() => navigation?.navigate('AccountManagement')}
          style={({ pressed }) => [
            styles.emptyCTA,
            { opacity: pressed ? 0.85 : 1 },
          ]}
        >
          <LinearGradient
            colors={[D.indigo, '#4F46E5']}
            style={styles.emptyCTAGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
          >
            <Feather name="link" size={15} color={D.white} />
            <Text style={styles.emptyCTAText}>Connect Accounts</Text>
          </LinearGradient>
        </Pressable>
      </LinearGradient>
    </View>
  );
}

function SkeletonBox({
  height,
  width,
  style,
}: {
  height: number;
  width?: number | string;
  style?: object;
}) {
  const pulse = useRef(new Animated.Value(0.4)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 0.9, duration: 700, useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0.4, duration: 700, useNativeDriver: true }),
      ])
    ).start();
    return () => pulse.stopAnimation();
  }, []);

  return (
    <Animated.View
      style={[
        {
          height,
          width: width ?? '100%',
          borderRadius: 8,
          backgroundColor: '#CBD5E1',
          opacity: pulse,
        },
        style,
      ]}
    />
  );
}

function SkeletonBody() {
  return (
    <View style={styles.skeletonBody}>
      {/* Metrics grid */}
      <SkeletonBox height={10} width={90} style={{ marginBottom: 12 }} />
      <View style={styles.gridRow}>
        <View style={[styles.changeCard, { justifyContent: 'space-between' }]}>
          <SkeletonBox height={12} width={30} />
          <SkeletonBox height={20} width={80} style={{ marginTop: 10 }} />
        </View>
        <View style={[styles.changeCard, { justifyContent: 'space-between' }]}>
          <SkeletonBox height={12} width={30} />
          <SkeletonBox height={20} width={80} style={{ marginTop: 10 }} />
        </View>
      </View>
      <View style={[styles.gridRow, { marginBottom: 20 }]}>
        <View style={[styles.changeCard, { justifyContent: 'space-between' }]}>
          <SkeletonBox height={12} width={30} />
          <SkeletonBox height={20} width={80} style={{ marginTop: 10 }} />
        </View>
        <View style={[styles.changeCard, { justifyContent: 'space-between' }]}>
          <SkeletonBox height={12} width={30} />
          <SkeletonBox height={20} width={80} style={{ marginTop: 10 }} />
        </View>
      </View>
      {/* Breakdown */}
      <SkeletonBox height={10} width={120} style={{ marginBottom: 12 }} />
      <View style={[styles.card, { gap: 16 }]}>
        <SkeletonBox height={18} />
        <SkeletonBox height={18} />
        <SkeletonBox height={18} />
      </View>
      {/* Records */}
      <SkeletonBox height={10} width={140} style={{ marginBottom: 12, marginTop: 6 }} />
      <View style={[styles.card, { gap: 16 }]}>
        <SkeletonBox height={18} />
        <SkeletonBox height={18} />
      </View>
    </View>
  );
}

// ── Styles ─────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: D.bg,
  },

  // ── Hero ──────────────────────────────────────────────────────────────────
  hero: {
    // height driven by content
  },
  heroSafe: {
    paddingHorizontal: 20,
    paddingBottom: 0,
  },
  heroTop: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    marginBottom: 10,
    gap: 10,
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.1)',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  heroTitleBlock: {
    flex: 1,
  },
  heroEyebrow: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.8,
    color: 'rgba(255,255,255,0.5)',
    marginBottom: 3,
  },
  heroTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: D.white,
    letterSpacing: -0.5,
  },
  qualityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 99,
    borderWidth: 1,
    flexShrink: 0,
  },
  qualityDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  qualityText: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.8,
  },

  // ── Big Number ────────────────────────────────────────────────────────────
  heroBigNumSkeleton: {
    height: 56,
    width: 220,
    borderRadius: 10,
    backgroundColor: 'rgba(255,255,255,0.12)',
    marginBottom: 16,
  },
  heroBigNumBlock: {
    marginBottom: 8,
    alignItems: 'flex-start',
    gap: 8,
  },
  heroBigNum: {
    fontSize: 44,
    fontWeight: '800',
    color: D.white,
    letterSpacing: -1.5,
    // Subtle glow via text shadow
    textShadowColor: 'rgba(59,130,246,0.35)',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 18,
  },
  changeChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 99,
  },
  changeChipText: {
    fontSize: 13,
    fontWeight: '700',
  },
  streakBadge: {
    backgroundColor: 'rgba(245,158,11,0.2)',
    borderRadius: 99,
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderWidth: 1,
    borderColor: 'rgba(245,158,11,0.35)',
  },
  streakText: {
    fontSize: 12,
    fontWeight: '600',
    color: D.amber,
  },

  // ── Sparkline ─────────────────────────────────────────────────────────────
  sparkContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    height: 48,
    gap: 2,
    marginBottom: 10,
    paddingHorizontal: 2,
  },
  sparkBar: {
    flex: 1,
    borderRadius: 2,
    minHeight: 4,
  },

  // ── Time Range ────────────────────────────────────────────────────────────
  timeRangeRow: {
    flexDirection: 'row',
    gap: 6,
    paddingBottom: 14,
    paddingTop: 2,
  },
  rangeTab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 7,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.18)',
  },
  rangeTabActive: {
    backgroundColor: D.white,
    borderColor: D.white,
  },
  rangeTabText: {
    fontSize: 12,
    fontWeight: '600',
    color: 'rgba(255,255,255,0.55)',
  },
  rangeTabTextActive: {
    color: D.navy,
  },

  // ── Scroll body ───────────────────────────────────────────────────────────
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 14,
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.3,
    color: D.textMuted,
    marginBottom: 10,
    marginLeft: 2,
  },

  // ── Change cards grid ─────────────────────────────────────────────────────
  gridRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  changeCard: {
    flex: 1,
    backgroundColor: D.card,
    borderRadius: 16,
    padding: 16,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 10,
    elevation: 3,
  },
  changeCardLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.8,
    color: D.textMuted,
    marginBottom: 10,
  },
  changeCardValueWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 99,
  },
  changeCardValue: {
    fontSize: 14,
    fontWeight: '700',
  },

  // ── Shared card shell ─────────────────────────────────────────────────────
  card: {
    backgroundColor: D.card,
    borderRadius: 16,
    padding: 18,
    marginBottom: 14,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 10,
    elevation: 3,
  },
  divider: {
    height: StyleSheet.hairlineWidth,
    backgroundColor: D.cardBorder,
    marginVertical: 14,
  },

  // ── Breakdown ─────────────────────────────────────────────────────────────
  breakdownRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  breakdownIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  breakdownLabel: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: D.textPrimary,
  },
  breakdownAmount: {
    fontSize: 15,
    fontWeight: '700',
    letterSpacing: -0.3,
  },

  // ── Records ───────────────────────────────────────────────────────────────
  recordRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  recordIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  recordContent: {
    flex: 1,
  },
  recordLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: D.textMuted,
    letterSpacing: 0.3,
    marginBottom: 2,
  },
  recordValue: {
    fontSize: 18,
    fontWeight: '800',
    letterSpacing: -0.4,
  },
  recordDate: {
    fontSize: 12,
    color: D.textSecondary,
    marginTop: 2,
  },

  // ── Headline card ─────────────────────────────────────────────────────────
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
    flexShrink: 0,
  },
  headlineInner: {
    flex: 1,
    padding: 16,
  },
  headlineIconRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 10,
  },
  headlineIconWrap: {
    width: 24,
    height: 24,
    borderRadius: 8,
    backgroundColor: `${D.indigo}20`,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headlineEyebrow: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    color: D.indigo,
  },
  headlineText: {
    fontSize: 14,
    lineHeight: 21,
    color: '#312E81',
    fontStyle: 'italic',
    fontWeight: '500',
  },

  // ── Error state ───────────────────────────────────────────────────────────
  errorCard: {
    alignItems: 'center',
    paddingVertical: 48,
    gap: 10,
  },
  errorTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: D.textPrimary,
  },
  errorBody: {
    fontSize: 14,
    color: D.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
  },

  // ── Empty / Insufficient state ────────────────────────────────────────────
  emptyCard: {
    borderRadius: 20,
    overflow: 'hidden',
    marginBottom: 20,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08,
    shadowRadius: 14,
    elevation: 4,
  },
  emptyGradient: {
    padding: 32,
    alignItems: 'center',
  },
  emptyIllustration: {
    width: 80,
    height: 80,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  emptyRing: {
    position: 'absolute',
    borderRadius: 999,
    borderWidth: 1.5,
  },
  emptyRingCenter: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: `${D.indigo}18`,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: D.textPrimary,
    marginBottom: 10,
    letterSpacing: -0.3,
  },
  emptyBody: {
    fontSize: 14,
    color: D.textSecondary,
    textAlign: 'center',
    lineHeight: 21,
    marginBottom: 24,
  },
  emptyCTA: {
    borderRadius: 14,
    overflow: 'hidden',
  },
  emptyCTAGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 24,
    paddingVertical: 14,
  },
  emptyCTAText: {
    fontSize: 15,
    fontWeight: '700',
    color: D.white,
  },

  // ── Skeleton ──────────────────────────────────────────────────────────────
  skeletonBody: {
    paddingTop: 4,
  },
});
