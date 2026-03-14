/**
 * MillionairePathScreen — Visual Wealth Journey
 * =============================================
 * The "Hero Metric" visualization from the blueprint.
 * Shows days until millionaire with a mountain path graphic.
 */

import React, { useRef, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  Animated,
  StatusBar,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Feather } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import Svg, { Path, Circle, Defs, LinearGradient as SvgGradient, Stop, G, Text as SvgText } from 'react-native-svg';
import MillionairePathService, { TimelineProjection } from '../../../services/MillionairePathService';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ── Design Tokens ────────────────────────────────────────────────────────────

const D = {
  navy:          '#0B1426',
  navyMid:       '#0F1E35',
  navyLight:     '#162642',
  white:         '#FFFFFF',
  green:         '#10B981',
  greenFaint:    '#D1FAE5',
  indigo:        '#6366F1',
  indigoFaint:   '#EEF2FF',
  amber:         '#F59E0B',
  amberFaint:    '#FEF3C7',
  gold:          '#EAB308',
  textPrimary:   '#0F172A',
  textSecondary: '#64748B',
  textMuted:     '#94A3B8',
  card:          '#FFFFFF',
  bg:            '#F1F5F9',
};

// ── Demo Data ────────────────────────────────────────────────────────────────

const DEMO_PATH = {
  currentValue: 47832,
  monthlyContribution: 850,
  goalAmount: 1000000,
  daysRemaining: 4210,
  progressPercent: 4.78,
  yearsRemaining: 11.5,
  estimatedDate: 'August 2037',
  recentAcceleration: 142, // days saved from recent actions
};

// ── Mountain Path Component ──────────────────────────────────────────────────

function MountainPath({ progress }: { progress: number }) {
  const pathProgress = useRef(new Animated.Value(0)).current;
  const avatarAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(pathProgress, {
        toValue: 1,
        duration: 2000,
        useNativeDriver: false,
      }),
      Animated.timing(avatarAnim, {
        toValue: progress / 100,
        duration: 2000,
        useNativeDriver: false,
      }),
    ]).start();
  }, [progress]);

  const width = SCREEN_WIDTH - 32;
  const height = 180;

  // Mountain path coordinates
  const pathD = `M 20 ${height - 20} 
                 Q 60 ${height - 40} 100 ${height - 60}
                 T 180 ${height - 90}
                 T 260 ${height - 110}
                 T ${width - 40} 40`;

  return (
    <View style={styles.mountainContainer}>
      <Svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        <Defs>
          <SvgGradient id="pathGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <Stop offset="0%" stopColor={D.indigo} stopOpacity="0.3" />
            <Stop offset={`${progress}%`} stopColor={D.green} stopOpacity="1" />
            <Stop offset={`${progress}%`} stopColor={D.textMuted} stopOpacity="0.3" />
            <Stop offset="100%" stopColor={D.textMuted} stopOpacity="0.2" />
          </SvgGradient>
        </Defs>
        
        {/* Background path */}
        <Path
          d={pathD}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="4"
          strokeLinecap="round"
        />
        
        {/* Progress path */}
        <Path
          d={pathD}
          fill="none"
          stroke="url(#pathGradient)"
          strokeWidth="4"
          strokeLinecap="round"
        />
        
        {/* Milestone markers */}
        <G>
          {/* 25% marker */}
          <Circle cx="100" cy={height - 60} r="6" fill={progress >= 25 ? D.green : 'rgba(255,255,255,0.2)'} />
          <SvgText x="100" y={height - 75} fill="rgba(255,255,255,0.6)" fontSize="10" textAnchor="middle">$250K</SvgText>
          
          {/* 50% marker */}
          <Circle cx="180" cy={height - 90} r="6" fill={progress >= 50 ? D.green : 'rgba(255,255,255,0.2)'} />
          <SvgText x="180" y={height - 105} fill="rgba(255,255,255,0.6)" fontSize="10" textAnchor="middle">$500K</SvgText>
          
          {/* 75% marker */}
          <Circle cx="260" cy={height - 110} r="6" fill={progress >= 75 ? D.green : 'rgba(255,255,255,0.2)'} />
          <SvgText x="260" y={height - 125} fill="rgba(255,255,255,0.6)" fontSize="10" textAnchor="middle">$750K</SvgText>
          
          {/* Summit */}
          <Circle cx={width - 40} cy="40" r="10" fill={D.gold} />
          <SvgText x={width - 40} y="25" fill={D.gold} fontSize="11" fontWeight="bold" textAnchor="middle">$1M</SvgText>
        </G>
        
        {/* Start point */}
        <Circle cx="20" cy={height - 20} r="8" fill={D.indigo} />
        
        {/* Current position avatar */}
        <Circle 
          cx={20 + (progress / 100) * (width - 60)} 
          cy={height - 20 - (progress / 100) * (height - 60)} 
          r="12" 
          fill={D.green} 
          stroke={D.white}
          strokeWidth="2"
        />
      </Svg>
      
      {/* Flag at summit */}
      <View style={styles.summitFlag}>
        <Text style={{ fontSize: 24 }}>🏔️</Text>
      </View>
    </View>
  );
}

// ── Milestone Card ───────────────────────────────────────────────────────────

function MilestoneCard({
  projection,
  index,
}: {
  projection: TimelineProjection;
  index: number;
}) {
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 300,
      delay: index * 50,
      useNativeDriver: true,
    }).start();
  }, []);

  const isMilestone = !!projection.milestone;

  return (
    <Animated.View style={[styles.milestoneCard, isMilestone && styles.milestoneCardHighlight, { opacity: fadeAnim }]}>
      <View style={styles.milestoneYear}>
        <Text style={styles.milestoneYearText}>{projection.year}</Text>
        <Text style={styles.milestoneAgeText}>Age {projection.age}</Text>
      </View>
      <View style={styles.milestoneContent}>
        <Text style={styles.milestoneValue}>
          ${(projection.projectedValue / 1000).toFixed(0)}K
        </Text>
        {isMilestone && (
          <Text style={styles.milestoneBadge}>{projection.milestone}</Text>
        )}
      </View>
      <View style={styles.milestoneBreakdown}>
        <Text style={styles.breakdownText}>
          +${(projection.growthTotal / 1000).toFixed(0)}K growth
        </Text>
      </View>
    </Animated.View>
  );
}

// ── Action Impact Card ───────────────────────────────────────────────────────

function ActionImpactCard({
  title,
  amount,
  impact,
  icon,
  color,
  onPress,
}: {
  title: string;
  amount: string;
  impact: string;
  icon: string;
  color: string;
  onPress?: () => void;
}) {
  return (
    <Pressable style={[styles.actionCard, { borderLeftColor: color }]} onPress={onPress}>
      <View style={[styles.actionIcon, { backgroundColor: color + '20' }]}>
        <Feather name={icon as any} size={18} color={color} />
      </View>
      <View style={styles.actionContent}>
        <Text style={styles.actionTitle}>{title}</Text>
        <Text style={styles.actionAmount}>{amount}</Text>
      </View>
      <View style={styles.actionImpact}>
        <Feather name="zap" size={12} color={D.green} />
        <Text style={styles.actionImpactText}>{impact}</Text>
      </View>
    </Pressable>
  );
}

// ── Main Component ───────────────────────────────────────────────────────────

export default function MillionairePathScreen() {
  const navigation = useNavigation<any>();
  const [projections, setProjections] = useState<TimelineProjection[]>([]);
  const heroCountAnim = useRef(new Animated.Value(0)).current;
  const [displayDays, setDisplayDays] = useState(0);

  useEffect(() => {
    // Generate projections
    const proj = MillionairePathService.generateProjection(
      DEMO_PATH.currentValue,
      DEMO_PATH.monthlyContribution,
      35,
      DEMO_PATH.goalAmount,
      20
    );
    setProjections(proj);

    // Count-up animation
    Animated.timing(heroCountAnim, {
      toValue: DEMO_PATH.daysRemaining,
      duration: 2000,
      useNativeDriver: false,
    }).start();

    const listener = heroCountAnim.addListener(({ value }) => {
      setDisplayDays(Math.round(value));
    });

    return () => heroCountAnim.removeListener(listener);
  }, []);

  const formatDays = (days: number) => {
    const years = Math.floor(days / 365);
    const months = Math.floor((days % 365) / 30);
    return `${years}y ${months}m`;
  };

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />
      
      {/* Hero Section */}
      <LinearGradient
        colors={[D.navy, '#0A1628', '#0A2518']}
        style={styles.hero}
      >
        <SafeAreaView edges={['top']} style={styles.heroSafe}>
          <View style={styles.heroTop}>
            <Pressable onPress={() => navigation.goBack()} style={styles.backBtn}>
              <Feather name="chevron-left" size={24} color={D.white} />
            </Pressable>
            <View style={styles.heroTitleWrap}>
              <Text style={styles.heroEyebrow}>YOUR MILLIONAIRE PATH</Text>
              <Text style={styles.heroTitle}>Journey to $1M</Text>
            </View>
            <Pressable style={styles.shareBtn}>
              <Feather name="share-2" size={20} color={D.white} />
            </Pressable>
          </View>
          
          {/* Hero Metric */}
          <View style={styles.heroMetric}>
            <Text style={styles.metricLabel}>Days Until Millionaire</Text>
            <View style={styles.metricRow}>
              <Text style={styles.metricValue}>{displayDays.toLocaleString()}</Text>
              <View style={styles.accelerationBadge}>
                <Feather name="trending-up" size={12} color={D.green} />
                <Text style={styles.accelerationText}>
                  -{DEMO_PATH.recentAcceleration} days
                </Text>
              </View>
            </View>
            <Text style={styles.metricSubtext}>
              That's {formatDays(displayDays)} • Est. {DEMO_PATH.estimatedDate}
            </Text>
          </View>
          
          {/* Mountain Path Visualization */}
          <MountainPath progress={DEMO_PATH.progressPercent} />
          
          {/* Progress Stats */}
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>${(DEMO_PATH.currentValue / 1000).toFixed(0)}K</Text>
              <Text style={styles.statLabel}>Current</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={styles.statValue}>${DEMO_PATH.monthlyContribution}</Text>
              <Text style={styles.statLabel}>Monthly</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={[styles.statValue, { color: D.green }]}>{DEMO_PATH.progressPercent}%</Text>
              <Text style={styles.statLabel}>Progress</Text>
            </View>
          </View>
        </SafeAreaView>
      </LinearGradient>
      
      {/* Content */}
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Accelerate Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Accelerate Your Path</Text>
            <View style={styles.sectionBadge}>
              <Feather name="zap" size={12} color={D.green} />
              <Text style={styles.sectionBadgeText}>Quick Wins</Text>
            </View>
          </View>
          
          <ActionImpactCard
            title="Stop $127/mo in leaks"
            amount="4 subscriptions found"
            impact="142 days closer"
            icon="shield"
            color={D.indigo}
            onPress={() => navigation.navigate('LeakRedirect')}
          />
          <ActionImpactCard
            title="Increase to $1,000/mo"
            amount="+$150/mo contribution"
            impact="8 months sooner"
            icon="trending-up"
            color={D.green}
            onPress={() => navigation.navigate('Reallocate')}
          />
          <ActionImpactCard
            title="Capture employer match"
            amount="$1,300/year free money"
            impact="2 years sooner"
            icon="gift"
            color={D.amber}
            onPress={() => navigation.navigate('FinancialHealth')}
          />
        </View>
        
        {/* Year by Year */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Year-by-Year Projection</Text>
          <Text style={styles.sectionSubtitle}>
            At 7% average annual return
          </Text>
          
          {projections.slice(0, 10).map((proj, index) => (
            <MilestoneCard key={proj.year} projection={proj} index={index} />
          ))}
        </View>
        
        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

// ── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: D.bg,
  },
  
  // Hero
  hero: {},
  heroSafe: {
    paddingHorizontal: 16,
    paddingBottom: 24,
  },
  heroTop: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    marginBottom: 20,
    gap: 12,
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  shareBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  heroTitleWrap: {
    flex: 1,
  },
  heroEyebrow: {
    fontSize: 9,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.5)',
    letterSpacing: 1.5,
    marginBottom: 2,
  },
  heroTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: D.white,
  },
  
  // Hero Metric
  heroMetric: {
    alignItems: 'center',
    marginBottom: 20,
  },
  metricLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.6)',
    marginBottom: 8,
  },
  metricRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  metricValue: {
    fontSize: 52,
    fontWeight: '800',
    color: D.white,
    letterSpacing: -2,
  },
  accelerationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(16,185,129,0.2)',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
  },
  accelerationText: {
    fontSize: 13,
    fontWeight: '700',
    color: D.green,
  },
  metricSubtext: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.5)',
    marginTop: 8,
  },
  
  // Mountain
  mountainContainer: {
    marginBottom: 20,
    position: 'relative',
  },
  summitFlag: {
    position: 'absolute',
    right: 24,
    top: 0,
  },
  
  // Stats
  statsRow: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 16,
    padding: 16,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 20,
    fontWeight: '700',
    color: D.white,
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.5)',
  },
  statDivider: {
    width: 1,
    backgroundColor: 'rgba(255,255,255,0.1)',
    marginHorizontal: 8,
  },
  
  // Scroll
  scroll: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  
  // Section
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: D.textPrimary,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: D.textSecondary,
    marginBottom: 12,
  },
  sectionBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: D.greenFaint,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  sectionBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: D.green,
  },
  
  // Action Card
  actionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: D.card,
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    borderLeftWidth: 4,
  },
  actionIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  actionContent: {
    flex: 1,
  },
  actionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: D.textPrimary,
    marginBottom: 2,
  },
  actionAmount: {
    fontSize: 12,
    color: D.textSecondary,
  },
  actionImpact: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: D.greenFaint,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  actionImpactText: {
    fontSize: 11,
    fontWeight: '600',
    color: D.green,
  },
  
  // Milestone Card
  milestoneCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: D.card,
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
  },
  milestoneCardHighlight: {
    borderWidth: 1.5,
    borderColor: D.gold,
    backgroundColor: '#FFFBEB',
  },
  milestoneYear: {
    width: 60,
    marginRight: 12,
  },
  milestoneYearText: {
    fontSize: 15,
    fontWeight: '700',
    color: D.textPrimary,
  },
  milestoneAgeText: {
    fontSize: 11,
    color: D.textMuted,
  },
  milestoneContent: {
    flex: 1,
  },
  milestoneValue: {
    fontSize: 18,
    fontWeight: '700',
    color: D.textPrimary,
  },
  milestoneBadge: {
    fontSize: 12,
    fontWeight: '600',
    color: D.gold,
    marginTop: 2,
  },
  milestoneBreakdown: {},
  breakdownText: {
    fontSize: 11,
    color: D.green,
  },
});
