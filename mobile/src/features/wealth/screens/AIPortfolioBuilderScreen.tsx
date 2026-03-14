/**
 * AIPortfolioBuilderScreen — Your Personalized Investment Plan
 * ==============================================================
 * The AI constructs a portfolio allocation based on:
 *  - Freed money amount
 *  - Risk tolerance (user preference + financial situation)
 *  - Existing portfolio composition
 *  - Time horizon and financial health
 *
 * Shows:
 *  - Risk profile with rationale
 *  - Allocation pie chart / bars with exact $ amounts
 *  - Primary ETF for each slice
 *  - Combined projections (10/20/30 year)
 *  - Wealth milestones timeline
 *
 * 2026 Premium Design Language
 */

import React, { useRef, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  RefreshControl,
  Animated,
  StatusBar,
  Dimensions,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Feather from '@expo/vector-icons/Feather';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery, gql } from '@apollo/client';
import Svg, { Circle, G } from 'react-native-svg';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ── GraphQL Query ─────────────────────────────────────────────────────────────

const BUILD_PORTFOLIO = gql`
  query BuildPortfolio($monthlyAmount: Float!, $riskPreference: String) {
    buildPortfolio(monthlyAmount: $monthlyAmount, riskPreference: $riskPreference) {
      userId
      monthlyAmount
      annualAmount
      riskProfile
      riskRationale
      allocations {
        strategyId
        strategyName
        percentage
        monthlyAmount
        annualAmount
        color
        icon
        primaryEtf
        primaryEtfName
        rationale
      }
      projected10yr
      projected20yr
      projected30yr
      expectedReturnRate
      milestones {
        years
        value
        label
      }
      headline
      portfolioAdjustments
      warnings
      dataQuality
    }
  }
`;

// ── Design Tokens ─────────────────────────────────────────────────────────────

const D = {
  navy:          '#0B1426',
  navyMid:       '#0F1E35',
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
  cardBorder:    '#E2E8F0',
  bg:            '#F1F5F9',
  greenFaint:    '#D1FAE5',
  blueFaint:     '#EFF6FF',
  indigoFaint:   '#EEF2FF',
  amberFaint:    '#FEF3C7',
  purpleFaint:   '#F3E8FF',
  redFaint:      '#FEE2E2',
};

// ── Formatting ────────────────────────────────────────────────────────────────

const fmt = (n: number) => '$' + Math.abs(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
const fmtK = (n: number) => {
  if (n >= 1000000) return '$' + (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return '$' + (n / 1000).toFixed(0) + 'K';
  return fmt(n);
};

// ── Skeleton ──────────────────────────────────────────────────────────────────

function SkeletonLine({ width, height = 14, style }: { width: number | string; height?: number; style?: object }) {
  const shimmer = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, { toValue: 1, duration: 850, useNativeDriver: true }),
        Animated.timing(shimmer, { toValue: 0, duration: 850, useNativeDriver: true }),
      ])
    ).start();
  }, [shimmer]);
  const opacity = shimmer.interpolate({ inputRange: [0, 1], outputRange: [0.25, 0.55] });
  return <Animated.View style={[{ width, height, borderRadius: 6, backgroundColor: D.textMuted, opacity }, style]} />;
}

function LoadingSkeleton() {
  return (
    <View style={{ paddingHorizontal: 16, paddingTop: 24, gap: 16 }}>
      <View style={[styles.card, { padding: 20, alignItems: 'center' }]}>
        <SkeletonLine width={140} height={140} style={{ borderRadius: 70 }} />
        <SkeletonLine width="60%" height={18} style={{ marginTop: 20 }} />
      </View>
      {[1, 2, 3].map(i => (
        <View key={i} style={[styles.card, { padding: 16, flexDirection: 'row', gap: 12 }]}>
          <SkeletonLine width={48} height={48} style={{ borderRadius: 12 }} />
          <View style={{ flex: 1, gap: 6 }}>
            <SkeletonLine width="70%" height={16} />
            <SkeletonLine width="40%" height={12} />
          </View>
          <SkeletonLine width={60} height={24} style={{ borderRadius: 8 }} />
        </View>
      ))}
    </View>
  );
}

// ── Allocation Donut Chart ────────────────────────────────────────────────────

interface Allocation {
  strategyId: string;
  strategyName: string;
  percentage: number;
  monthlyAmount: number;
  annualAmount: number;
  color: string;
  icon: string;
  primaryEtf: string;
  primaryEtfName: string;
  rationale: string;
}

function AllocationDonut({ allocations, size = 160 }: { allocations: Allocation[]; size?: number }) {
  const strokeWidth = 24;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;
  
  let offset = 0;
  
  return (
    <View style={{ alignItems: 'center' }}>
      <Svg width={size} height={size}>
        <G rotation="-90" origin={`${center}, ${center}`}>
          {allocations.map((alloc, idx) => {
            const strokeDasharray = (alloc.percentage / 100) * circumference;
            const strokeDashoffset = -offset;
            offset += strokeDasharray;
            
            return (
              <Circle
                key={alloc.strategyId}
                cx={center}
                cy={center}
                r={radius}
                stroke={alloc.color}
                strokeWidth={strokeWidth}
                fill="transparent"
                strokeDasharray={`${strokeDasharray} ${circumference}`}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
              />
            );
          })}
        </G>
      </Svg>
      <View style={styles.donutCenter}>
        <Text style={styles.donutCenterLabel}>AI Built</Text>
        <Text style={styles.donutCenterValue}>Portfolio</Text>
      </View>
    </View>
  );
}

// ── Allocation Bar ────────────────────────────────────────────────────────────

function AllocationBar({ allocation, onPress }: { allocation: Allocation; onPress?: () => void }) {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const iconName = (allocation.icon || 'trending-up') as keyof typeof Feather.glyphMap;
  
  const onPressIn = () => Animated.spring(scaleAnim, { toValue: 0.98, useNativeDriver: true, speed: 50 }).start();
  const onPressOut = () => Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 50 }).start();
  
  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
      <Pressable
        onPressIn={onPressIn}
        onPressOut={onPressOut}
        onPress={onPress}
        style={styles.allocationCard}
      >
        {/* Left accent */}
        <View style={[styles.allocationAccent, { backgroundColor: allocation.color }]} />
        
        <View style={styles.allocationContent}>
          {/* Icon + Info */}
          <View style={[styles.allocationIconWrap, { backgroundColor: allocation.color + '22' }]}>
            <Feather name={iconName} size={20} color={allocation.color} />
          </View>
          
          <View style={{ flex: 1, marginLeft: 12 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <Text style={styles.allocationName}>{allocation.strategyName}</Text>
              <View style={[styles.pctBadge, { backgroundColor: allocation.color + '22' }]}>
                <Text style={[styles.pctBadgeText, { color: allocation.color }]}>
                  {allocation.percentage}%
                </Text>
              </View>
            </View>
            
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 4 }}>
              <View style={styles.etfChip}>
                <Text style={styles.etfChipText}>{allocation.primaryEtf}</Text>
              </View>
              <Text style={styles.allocationEtfName} numberOfLines={1}>
                {allocation.primaryEtfName}
              </Text>
            </View>
            
            <Text style={styles.allocationRationale} numberOfLines={2}>
              {allocation.rationale}
            </Text>
          </View>
          
          {/* Amount */}
          <View style={styles.allocationAmountWrap}>
            <Text style={styles.allocationAmount}>{fmt(allocation.monthlyAmount)}</Text>
            <Text style={styles.allocationAmountLabel}>/month</Text>
          </View>
        </View>
      </Pressable>
    </Animated.View>
  );
}

// ── Milestone Timeline ────────────────────────────────────────────────────────

interface Milestone {
  years: number;
  value: number;
  label: string;
}

function MilestoneTimeline({ milestones }: { milestones: Milestone[] }) {
  if (!milestones || milestones.length === 0) return null;
  
  return (
    <View style={styles.timelineCard}>
      <View style={styles.timelineHeader}>
        <Feather name="flag" size={16} color={D.indigo} />
        <Text style={styles.timelineTitle}>YOUR WEALTH MILESTONES</Text>
      </View>
      
      <View style={styles.timelineLine} />
      
      {milestones.map((milestone, idx) => (
        <View key={idx} style={styles.timelineItem}>
          <View style={styles.timelineDot} />
          <View style={styles.timelineContent}>
            <Text style={styles.timelineYears}>{milestone.years} years</Text>
            <Text style={styles.timelineValue}>{fmtK(milestone.value)}</Text>
            <Text style={styles.timelineLabel}>{milestone.label}</Text>
          </View>
        </View>
      ))}
    </View>
  );
}

// ── Risk Profile Badge ────────────────────────────────────────────────────────

function RiskProfileBadge({ profile, rationale }: { profile: string; rationale: string }) {
  const colorMap: Record<string, string> = {
    conservative: D.blue,
    moderate: D.green,
    aggressive: D.purple,
  };
  const iconMap: Record<string, string> = {
    conservative: 'shield',
    moderate: 'target',
    aggressive: 'zap',
  };
  
  const color = colorMap[profile] || D.green;
  const iconName = (iconMap[profile] || 'target') as keyof typeof Feather.glyphMap;
  
  return (
    <View style={[styles.riskCard, { borderColor: color + '33' }]}>
      <View style={[styles.riskIconWrap, { backgroundColor: color + '22' }]}>
        <Feather name={iconName} size={18} color={color} />
      </View>
      <View style={{ flex: 1 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <Text style={styles.riskLabel}>Risk Profile</Text>
          <View style={[styles.riskBadge, { backgroundColor: color }]}>
            <Text style={styles.riskBadgeText}>{profile.toUpperCase()}</Text>
          </View>
        </View>
        <Text style={styles.riskRationale}>{rationale}</Text>
      </View>
    </View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────

export default function AIPortfolioBuilderScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const insets = useSafeAreaInsets();
  
  const monthlyAmount = route.params?.monthlyAmount ?? 100;
  const riskPreference = route.params?.riskPreference ?? null;
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;
  
  const { data, loading, error, refetch } = useQuery(BUILD_PORTFOLIO, {
    variables: { monthlyAmount, riskPreference },
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });
  
  const result = data?.buildPortfolio;
  const allocations: Allocation[] = result?.allocations ?? [];
  
  useEffect(() => {
    if (!loading) {
      Animated.parallel([
        Animated.timing(fadeAnim, { toValue: 1, duration: 500, useNativeDriver: true }),
        Animated.timing(slideAnim, { toValue: 0, duration: 500, useNativeDriver: true }),
      ]).start();
    }
  }, [loading, fadeAnim, slideAnim]);
  
  const [refreshing, setRefreshing] = useState(false);
  const onRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };
  
  const handleApplyPlan = () => {
    console.log('[AIPortfolioBuilder] handleApplyPlan called, allocations:', allocations.length);
    
    // Show confirmation with plan details
    Alert.alert(
      'Plan Activated! 🎉',
      `Your ${result?.riskProfile || 'balanced'} portfolio plan is ready.\n\n` +
      `• ${allocations.length} asset allocations\n` +
      `• ${fmt(monthlyAmount)}/month investing\n` +
      `• Target: ${fmtK(result?.projected30yr || 0)} in 30 years\n\n` +
      'Go to Invest Hub to start buying your ETFs.',
      [
        {
          text: 'Stay Here',
          style: 'cancel',
        },
        {
          text: 'Go to Invest',
          onPress: () => {
            try {
              // Try navigating to Invest tab/hub
              navigation.navigate('Invest' as never);
            } catch {
              try {
                navigation.navigate('InvestHub' as never);
              } catch {
                navigation.goBack();
              }
            }
          },
        },
      ]
    );
  };
  
  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />
      
      {/* ── Hero Header ──────────────────────────────────────────────────── */}
      <LinearGradient
        colors={['#0B1426', '#1A0B26']}
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
            <Text style={styles.heroEyebrow}>AI PORTFOLIO BUILDER</Text>
            <Text style={styles.heroTitle}>Your Investment Plan</Text>
          </View>
          <View style={styles.heroIconBadge}>
            <Feather name="pie-chart" size={22} color={D.purple} />
          </View>
        </View>
        
        {/* Amount card */}
        <View style={styles.heroCard}>
          <View>
            <Text style={styles.heroAmountLabel}>Investing</Text>
            <Text style={styles.heroAmount}>
              {fmt(monthlyAmount)}
              <Text style={styles.heroAmountUnit}>/month</Text>
            </Text>
          </View>
          {result && (
            <View style={styles.heroProjection}>
              <Text style={styles.heroProjectionLabel}>30-year projection</Text>
              <Text style={styles.heroProjectionValue}>{fmtK(result.projected30yr)}</Text>
              <Text style={styles.heroProjectionRate}>
                @ {((result.expectedReturnRate || 0.075) * 100).toFixed(1)}% return
              </Text>
            </View>
          )}
        </View>
      </LinearGradient>
      
      {/* ── Scrollable Body ─────────────────────────────────────────────── */}
      <Animated.ScrollView
        style={{ flex: 1, opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={D.purple} />}
      >
        {loading && <LoadingSkeleton />}
        
        {!loading && error && (
          <View style={styles.center}>
            <View style={styles.errorIconWrap}>
              <Feather name="wifi-off" size={26} color={D.red} />
            </View>
            <Text style={styles.emptyTitle}>Could not build portfolio</Text>
            <Text style={styles.centerText}>Pull down to retry.</Text>
          </View>
        )}
        
        {!loading && !error && result && (
          <>
            {/* Risk Profile */}
            <RiskProfileBadge 
              profile={result.riskProfile} 
              rationale={result.riskRationale} 
            />
            
            {/* Portfolio Adjustments */}
            {result.portfolioAdjustments?.length > 0 && (
              <View style={styles.adjustmentsCard}>
                <Feather name="sliders" size={14} color={D.indigo} />
                <Text style={styles.adjustmentsText}>
                  {result.portfolioAdjustments.join(' • ')}
                </Text>
              </View>
            )}
            
            {/* Warnings */}
            {result.warnings?.length > 0 && (
              <View style={styles.warningsCard}>
                <Feather name="alert-triangle" size={14} color={D.amber} />
                <Text style={styles.warningsText}>
                  {result.warnings.join(' • ')}
                </Text>
              </View>
            )}
            
            {/* Donut Chart */}
            <View style={styles.chartCard}>
              <AllocationDonut allocations={allocations} size={180} />
              
              {/* Legend */}
              <View style={styles.legend}>
                {allocations.map(alloc => (
                  <View key={alloc.strategyId} style={styles.legendItem}>
                    <View style={[styles.legendDot, { backgroundColor: alloc.color }]} />
                    <Text style={styles.legendLabel}>{alloc.percentage}%</Text>
                    <Text style={styles.legendName} numberOfLines={1}>{alloc.strategyName}</Text>
                  </View>
                ))}
              </View>
            </View>
            
            {/* Section header */}
            <Text style={styles.sectionHeader}>YOUR ALLOCATION</Text>
            
            {/* Allocation bars */}
            {allocations.map(alloc => (
              <AllocationBar key={alloc.strategyId} allocation={alloc} />
            ))}
            
            {/* Projections Row */}
            <View style={styles.projectionsCard}>
              <Text style={styles.projectionsTitle}>PROJECTED GROWTH</Text>
              <View style={styles.projectionsRow}>
                <View style={styles.projectionItem}>
                  <Text style={styles.projectionLabel}>10 Years</Text>
                  <Text style={styles.projectionValue}>{fmtK(result.projected10yr)}</Text>
                </View>
                <View style={styles.projectionDivider} />
                <View style={styles.projectionItem}>
                  <Text style={styles.projectionLabel}>20 Years</Text>
                  <Text style={styles.projectionValue}>{fmtK(result.projected20yr)}</Text>
                </View>
                <View style={styles.projectionDivider} />
                <View style={styles.projectionItem}>
                  <Text style={styles.projectionLabel}>30 Years</Text>
                  <Text style={[styles.projectionValue, { color: D.green }]}>{fmtK(result.projected30yr)}</Text>
                </View>
              </View>
            </View>
            
            {/* Milestones */}
            <MilestoneTimeline milestones={result.milestones} />
            
            {/* Apply Plan CTA */}
            <Pressable
              onPress={() => {
                console.log('[AIPortfolioBuilder] Start This Plan pressed');
                handleApplyPlan();
              }}
              style={({ pressed }) => [
                styles.applyCta,
                { opacity: pressed ? 0.85 : 1, transform: [{ scale: pressed ? 0.98 : 1 }] },
              ]}
            >
              <LinearGradient
                colors={['#7C3AED', '#6366F1']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.applyCtaGradient}
                pointerEvents="none"
              >
                <Feather name="check-circle" size={22} color={D.white} />
                <View style={{ flex: 1, marginLeft: 14 }} pointerEvents="none">
                  <Text style={styles.applyCtaTitle}>Start This Plan</Text>
                  <Text style={styles.applyCtaSubtitle}>
                    Explore assets and begin investing
                  </Text>
                </View>
                <Feather name="arrow-right" size={22} color={D.white} />
              </LinearGradient>
            </Pressable>
            
            {/* Disclaimer */}
            <View style={styles.disclaimer}>
              <Feather name="info" size={14} color={D.textMuted} />
              <Text style={styles.disclaimerText}>
                This is an AI-generated allocation based on your financial profile. 
                Not financial advice. Past performance does not guarantee future results.
              </Text>
            </View>
            
            <View style={{ height: 32 }} />
          </>
        )}
      </Animated.ScrollView>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: D.bg },
  
  // Hero
  hero: { paddingHorizontal: 20, paddingBottom: 14 },
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
    backgroundColor: 'rgba(124,58,237,0.18)', borderWidth: 1, borderColor: 'rgba(124,58,237,0.35)',
    alignItems: 'center', justifyContent: 'center',
  },
  
  heroCard: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: 16,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.12)',
    padding: 16,
  },
  heroAmountLabel: { fontSize: 11, fontWeight: '600', color: 'rgba(255,255,255,0.5)', letterSpacing: 0.5 },
  heroAmount: { fontSize: 28, fontWeight: '800', color: D.white, letterSpacing: -1 },
  heroAmountUnit: { fontSize: 14, fontWeight: '600', color: 'rgba(255,255,255,0.6)' },
  heroProjection: { alignItems: 'flex-end' },
  heroProjectionLabel: { fontSize: 10, color: 'rgba(255,255,255,0.5)' },
  heroProjectionValue: { fontSize: 24, fontWeight: '800', color: D.purple, marginTop: 2 },
  heroProjectionRate: { fontSize: 10, color: 'rgba(255,255,255,0.4)', marginTop: 2 },
  
  scrollContent: { paddingHorizontal: 16, paddingTop: 14 },
  
  // Cards
  card: {
    backgroundColor: D.card, borderRadius: 20, marginBottom: 14,
    shadowColor: '#0F172A', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.07, shadowRadius: 12, elevation: 3,
  },
  
  // Risk Profile
  riskCard: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 12,
    backgroundColor: D.card, borderRadius: 16, padding: 16, marginBottom: 12,
    borderWidth: 1,
  },
  riskIconWrap: { width: 40, height: 40, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  riskLabel: { fontSize: 11, fontWeight: '600', color: D.textMuted, letterSpacing: 0.3 },
  riskBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  riskBadgeText: { fontSize: 10, fontWeight: '800', color: D.white, letterSpacing: 0.8 },
  riskRationale: { fontSize: 13, color: D.textSecondary, lineHeight: 18, marginTop: 4 },
  
  // Adjustments
  adjustmentsCard: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    backgroundColor: D.indigoFaint, borderRadius: 10, padding: 12, marginBottom: 12,
    borderWidth: 1, borderColor: D.indigo + '22',
  },
  adjustmentsText: { flex: 1, fontSize: 12, color: D.indigo, fontWeight: '500' },
  
  // Warnings
  warningsCard: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    backgroundColor: D.amberFaint, borderRadius: 10, padding: 12, marginBottom: 12,
    borderWidth: 1, borderColor: D.amber + '33',
  },
  warningsText: { flex: 1, fontSize: 12, color: '#92400E', fontWeight: '500' },
  
  // Chart card
  chartCard: {
    backgroundColor: D.card, borderRadius: 20, padding: 24, marginBottom: 16,
    alignItems: 'center',
    shadowColor: '#0F172A', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.07, shadowRadius: 12, elevation: 3,
  },
  
  // Donut center
  donutCenter: {
    position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
    alignItems: 'center', justifyContent: 'center',
  },
  donutCenterLabel: { fontSize: 12, color: D.textMuted, fontWeight: '600' },
  donutCenterValue: { fontSize: 16, color: D.textPrimary, fontWeight: '800', marginTop: 2 },
  
  // Legend
  legend: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', gap: 8, marginTop: 20 },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 4 },
  legendDot: { width: 8, height: 8, borderRadius: 4 },
  legendLabel: { fontSize: 11, fontWeight: '700', color: D.textPrimary },
  legendName: { fontSize: 11, color: D.textMuted, maxWidth: 80 },
  
  // Section header
  sectionHeader: { fontSize: 10, fontWeight: '700', letterSpacing: 1.2, color: D.textMuted, marginBottom: 12, marginLeft: 2 },
  
  // Allocation card
  allocationCard: {
    backgroundColor: D.card, borderRadius: 16, marginBottom: 10, overflow: 'hidden',
    shadowColor: '#0F172A', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.05, shadowRadius: 8, elevation: 2,
  },
  allocationAccent: { position: 'absolute', left: 0, top: 0, bottom: 0, width: 4 },
  allocationContent: { flexDirection: 'row', alignItems: 'center', padding: 14, paddingLeft: 18 },
  allocationIconWrap: { width: 44, height: 44, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  allocationName: { fontSize: 14, fontWeight: '700', color: D.textPrimary },
  pctBadge: { paddingHorizontal: 7, paddingVertical: 2, borderRadius: 6 },
  pctBadgeText: { fontSize: 11, fontWeight: '800' },
  etfChip: { backgroundColor: D.bg, borderRadius: 4, paddingHorizontal: 6, paddingVertical: 2 },
  etfChipText: { fontSize: 10, fontWeight: '700', color: D.textPrimary },
  allocationEtfName: { fontSize: 11, color: D.textMuted, flex: 1 },
  allocationRationale: { fontSize: 11, color: D.textSecondary, lineHeight: 15, marginTop: 6 },
  allocationAmountWrap: { alignItems: 'flex-end', marginLeft: 8 },
  allocationAmount: { fontSize: 16, fontWeight: '800', color: D.textPrimary },
  allocationAmountLabel: { fontSize: 10, color: D.textMuted },
  
  // Projections
  projectionsCard: {
    backgroundColor: D.card, borderRadius: 16, padding: 18, marginTop: 8, marginBottom: 16,
    shadowColor: '#0F172A', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.05, shadowRadius: 8, elevation: 2,
  },
  projectionsTitle: { fontSize: 10, fontWeight: '700', letterSpacing: 1.2, color: D.textMuted, marginBottom: 14, textAlign: 'center' },
  projectionsRow: { flexDirection: 'row', alignItems: 'center' },
  projectionItem: { flex: 1, alignItems: 'center' },
  projectionLabel: { fontSize: 11, fontWeight: '600', color: D.textMuted },
  projectionValue: { fontSize: 20, fontWeight: '800', color: D.textPrimary, marginTop: 4 },
  projectionDivider: { width: 1, height: 36, backgroundColor: D.cardBorder },
  
  // Timeline
  timelineCard: {
    backgroundColor: D.card, borderRadius: 16, padding: 18, marginBottom: 16,
    shadowColor: '#0F172A', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.05, shadowRadius: 8, elevation: 2,
  },
  timelineHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16 },
  timelineTitle: { fontSize: 10, fontWeight: '700', letterSpacing: 1.2, color: D.indigo },
  timelineLine: { position: 'absolute', left: 26, top: 50, bottom: 18, width: 2, backgroundColor: D.indigoFaint },
  timelineItem: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 16, paddingLeft: 4 },
  timelineDot: { width: 12, height: 12, borderRadius: 6, backgroundColor: D.indigo, borderWidth: 2, borderColor: D.indigoFaint, marginTop: 4 },
  timelineContent: { marginLeft: 14 },
  timelineYears: { fontSize: 12, fontWeight: '700', color: D.indigo },
  timelineValue: { fontSize: 18, fontWeight: '800', color: D.textPrimary, marginTop: 2 },
  timelineLabel: { fontSize: 12, color: D.textSecondary, marginTop: 2 },
  
  // Apply CTA
  applyCta: { marginTop: 8, marginBottom: 12, borderRadius: 16, overflow: 'hidden' },
  applyCtaGradient: {
    flexDirection: 'row', alignItems: 'center', padding: 18, borderRadius: 16,
    shadowColor: D.purple, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 12, elevation: 4,
    minHeight: 70,
  },
  applyCtaTitle: { fontSize: 17, fontWeight: '800', color: D.white },
  applyCtaSubtitle: { fontSize: 12, color: 'rgba(255,255,255,0.8)', marginTop: 2 },
  
  // Disclaimer
  disclaimer: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, paddingHorizontal: 4, marginTop: 8 },
  disclaimerText: { flex: 1, fontSize: 11, color: D.textMuted, lineHeight: 16 },
  
  // States
  center: { alignItems: 'center', paddingVertical: 64, gap: 10, paddingHorizontal: 32 },
  centerText: { fontSize: 14, color: D.textSecondary, textAlign: 'center', lineHeight: 20 },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: D.textPrimary },
  errorIconWrap: { width: 64, height: 64, borderRadius: 32, backgroundColor: D.redFaint, alignItems: 'center', justifyContent: 'center', marginBottom: 4 },
});
