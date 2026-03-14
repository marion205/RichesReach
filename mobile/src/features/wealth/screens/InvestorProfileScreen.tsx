/**
 * InvestorProfileScreen — Behavioral Identity Dashboard
 * =======================================================
 * Shows the user's investor archetype, bias detection panel,
 * and Next Best Actions.
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
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Feather } from '@expo/vector-icons';
import { useNavigation, useRoute } from '@react-navigation/native';
import BiasDetectionService, { BiasAnalysis } from '../services/BiasDetectionService';

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
  red:           '#EF4444',
  redFaint:      '#FEE2E2',
  textPrimary:   '#0F172A',
  textSecondary: '#64748B',
  textMuted:     '#94A3B8',
  card:          '#FFFFFF',
  bg:            '#F1F5F9',
  border:        '#E2E8F0',
};

// ── Archetype Data ───────────────────────────────────────────────────────────

interface ArchetypeInfo {
  key: string;
  title: string;
  emoji: string;
  description: string;
  focus: string;
  color: string;
  coachingTone: string;
  strategy: string;
}

const ARCHETYPES: Record<string, ArchetypeInfo> = {
  cautious_protector: {
    key: 'cautious_protector',
    title: 'The Cautious Protector',
    emoji: '🛡️',
    description: 'You prioritize security and steady progress over aggressive growth.',
    focus: 'Security, risk mitigation, and protecting what you have',
    color: D.green,
    coachingTone: 'The Guardian',
    strategy: 'Income & Stability',
  },
  steady_builder: {
    key: 'steady_builder',
    title: 'The Steady Builder',
    emoji: '🏗️',
    description: 'You believe in systems and automation. You trust compounding over time.',
    focus: 'Efficiency, systems, and the math of time',
    color: D.indigo,
    coachingTone: 'The Architect',
    strategy: 'Simple Path Core (VTI/VOO)',
  },
  opportunity_hunter: {
    key: 'opportunity_hunter',
    title: 'The Opportunity Hunter',
    emoji: '🎯',
    description: 'You\'re energized by finding the next big opportunity.',
    focus: 'Growth, edge, and strategic positioning',
    color: D.amber,
    coachingTone: 'The Scout',
    strategy: 'Growth & Innovation',
  },
  reactive_trader: {
    key: 'reactive_trader',
    title: 'The Reactive Trader',
    emoji: '⚡',
    description: 'You\'re emotionally connected to your investments.',
    focus: 'Stability through structure and guardrails',
    color: D.red,
    coachingTone: 'The Stabilizer',
    strategy: 'High-automation, low-visibility',
  },
};

// ── Demo Data ────────────────────────────────────────────────────────────────

const DEMO_DIMENSIONS = {
  riskTolerance: 65,
  locusOfControl: 70,
  lossAversion: 40,
  sophistication: 55,
};

const DEMO_BIASES = [
  {
    type: 'concentration',
    label: 'Concentration',
    score: 55,
    color: D.amber,
    icon: 'target' as const,
    message: '42% of portfolio in top 3 holdings. Consider broader diversification.',
  },
  {
    type: 'familiarity',
    label: 'Familiarity',
    score: 48,
    color: D.indigo,
    icon: 'heart' as const,
    message: 'Heavy in familiar tech names. Great companies, but explore beyond.',
  },
  {
    type: 'recency',
    label: 'Recency',
    score: 25,
    color: D.green,
    icon: 'trending-up' as const,
    message: 'Low recency bias. You\'re not chasing recent winners.',
  },
];

const DEMO_ACTIONS = [
  {
    id: 'leak',
    type: 'cancel_leak',
    priority: 1,
    headline: 'Stop $127/mo in leaks',
    description: 'We found 4 subscriptions draining your wealth.',
    impact: 'Worth $63,450 in 20 years',
    screen: 'LeakDetector',
    color: D.red,
    icon: 'alert-circle' as const,
  },
  {
    id: 'emergency',
    type: 'build_emergency_fund',
    priority: 2,
    headline: 'Build your fortress to 3 months',
    description: 'You have 1.9 months of expenses saved.',
    impact: 'Need $5,040 more',
    screen: 'FinancialHealth',
    color: D.amber,
    icon: 'shield' as const,
  },
  {
    id: 'match',
    type: 'capture_match',
    priority: 3,
    headline: 'Capture $1,300/year in free money',
    description: 'Your employer match is the best investment you\'ll ever make.',
    impact: '100% guaranteed return',
    screen: 'FinancialHealth',
    color: D.green,
    icon: 'gift' as const,
  },
];

// ── Bias Gauge Component ─────────────────────────────────────────────────────

interface BiasData {
  type: string;
  label: string;
  score: number;
  color: string;
  icon: string;
  message: string;
  isActive?: boolean;
}

function BiasGauge({
  bias,
  index,
}: {
  bias: BiasData;
  index: number;
}) {
  const widthAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 400,
        delay: index * 100,
        useNativeDriver: true,
      }),
      Animated.timing(widthAnim, {
        toValue: bias.score,
        duration: 800,
        delay: index * 100 + 200,
        useNativeDriver: false,
      }),
    ]).start();
  }, []);

  const getScoreLabel = (score: number) => {
    if (score < 30) return 'Low';
    if (score < 60) return 'Moderate';
    return 'High';
  };

  return (
    <Animated.View style={[styles.biasCard, { opacity: fadeAnim }, bias.isActive && styles.biasCardActive]}>
      <View style={styles.biasHeader}>
        <View style={[styles.biasIcon, { backgroundColor: bias.color + '20' }]}>
          <Feather name={bias.icon as any} size={16} color={bias.color} />
        </View>
        <Text style={styles.biasLabel}>{bias.label}</Text>
        {bias.isActive && (
          <View style={[styles.activeBadge, { backgroundColor: bias.color }]}>
            <Feather name="alert-circle" size={10} color={D.white} />
            <Text style={styles.activeBadgeText}>Active</Text>
          </View>
        )}
        <View style={[styles.biasScoreBadge, { backgroundColor: bias.color + '20' }]}>
          <Text style={[styles.biasScoreText, { color: bias.color }]}>
            {getScoreLabel(bias.score)}
          </Text>
        </View>
      </View>
      
      <View style={styles.biasBarContainer}>
        <Animated.View
          style={[
            styles.biasBar,
            {
              backgroundColor: bias.color,
              width: widthAnim.interpolate({
                inputRange: [0, 100],
                outputRange: ['0%', '100%'],
              }),
            },
          ]}
        />
      </View>
      
      <Text style={styles.biasMessage}>{bias.message}</Text>
    </Animated.View>
  );
}

// ── Action Card Component ────────────────────────────────────────────────────

function ActionCard({
  action,
  index,
  onPress,
}: {
  action: typeof DEMO_ACTIONS[0];
  index: number;
  onPress: () => void;
}) {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 400,
        delay: index * 80,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 400,
        delay: index * 80,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const onPressIn = () => {
    Animated.spring(scaleAnim, { toValue: 0.97, useNativeDriver: true, speed: 50 }).start();
  };
  const onPressOut = () => {
    Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 50 }).start();
  };

  return (
    <Animated.View
      style={{
        transform: [{ scale: scaleAnim }, { translateY: slideAnim }],
        opacity: fadeAnim,
      }}
    >
      <Pressable
        onPress={onPress}
        onPressIn={onPressIn}
        onPressOut={onPressOut}
        style={styles.actionCard}
      >
        <View style={[styles.actionPriority, { backgroundColor: action.color }]}>
          <Text style={styles.actionPriorityText}>{action.priority}</Text>
        </View>
        <View style={[styles.actionIcon, { backgroundColor: action.color + '15' }]}>
          <Feather name={action.icon} size={20} color={action.color} />
        </View>
        <View style={styles.actionContent}>
          <Text style={styles.actionHeadline}>{action.headline}</Text>
          <Text style={styles.actionDescription}>{action.description}</Text>
          <Text style={[styles.actionImpact, { color: action.color }]}>{action.impact}</Text>
        </View>
        <Feather name="chevron-right" size={20} color={D.textMuted} />
      </Pressable>
    </Animated.View>
  );
}

// ── Dimension Bar Component ──────────────────────────────────────────────────

function DimensionBar({
  label,
  value,
  color,
  delay,
}: {
  label: string;
  value: number;
  color: string;
  delay: number;
}) {
  const widthAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(widthAnim, {
      toValue: value,
      duration: 800,
      delay,
      useNativeDriver: false,
    }).start();
  }, []);

  return (
    <View style={styles.dimensionRow}>
      <Text style={styles.dimensionLabel}>{label}</Text>
      <View style={styles.dimensionBarOuter}>
        <Animated.View
          style={[
            styles.dimensionBarInner,
            {
              backgroundColor: color,
              width: widthAnim.interpolate({
                inputRange: [0, 100],
                outputRange: ['0%', '100%'],
              }),
            },
          ]}
        />
      </View>
      <Text style={styles.dimensionValue}>{value}</Text>
    </View>
  );
}

// ── Main Component ───────────────────────────────────────────────────────────

export default function InvestorProfileScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  
  const archetypeKey = route.params?.archetype || 'steady_builder';
  const archetype = ARCHETYPES[archetypeKey] || ARCHETYPES.steady_builder;

  const [biasAnalysis, setBiasAnalysis] = useState<BiasAnalysis | null>(null);
  const [loadingBiases, setLoadingBiases] = useState(true);

  // Load real bias data from portfolio
  useEffect(() => {
    let cancelled = false;
    async function loadBiases() {
      try {
        const analysis = await BiasDetectionService.analyzePortfolio();
        if (!cancelled) {
          setBiasAnalysis(analysis);
        }
      } catch (error) {
        console.warn('Failed to load bias analysis:', error);
      } finally {
        if (!cancelled) {
          setLoadingBiases(false);
        }
      }
    }
    loadBiases();
    return () => { cancelled = true; };
  }, []);

  // Transform real bias analysis into display format, or use demo data
  const biases = biasAnalysis ? [
    {
      type: 'concentration',
      label: 'Concentration',
      score: biasAnalysis.concentrationBias.score,
      color: biasAnalysis.concentrationBias.isActive ? D.amber : D.green,
      icon: 'target' as const,
      message: biasAnalysis.concentrationBias.coaching,
      isActive: biasAnalysis.concentrationBias.isActive,
    },
    {
      type: 'familiarity',
      label: 'Familiarity',
      score: biasAnalysis.familiarityBias.score,
      color: biasAnalysis.familiarityBias.isActive ? D.indigo : D.green,
      icon: 'heart' as const,
      message: biasAnalysis.familiarityBias.coaching,
      isActive: biasAnalysis.familiarityBias.isActive,
    },
    {
      type: 'recency',
      label: 'Recency',
      score: biasAnalysis.recencyBias.score,
      color: biasAnalysis.recencyBias.isActive ? D.amber : D.green,
      icon: 'trending-up' as const,
      message: biasAnalysis.recencyBias.coaching,
      isActive: biasAnalysis.recencyBias.isActive,
    },
    {
      type: 'loss_aversion',
      label: 'Loss Aversion',
      score: biasAnalysis.lossAversion.score,
      color: biasAnalysis.lossAversion.isActive ? D.red : D.green,
      icon: 'shield-off' as const,
      message: biasAnalysis.lossAversion.coaching,
      isActive: biasAnalysis.lossAversion.isActive,
    },
  ] : DEMO_BIASES;

  const handleActionPress = (screen: string) => {
    navigation.navigate(screen);
  };

  const handleRetakeQuiz = () => {
    navigation.navigate('InvestorQuiz');
  };

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />
      
      {/* Hero Header */}
      <LinearGradient colors={[D.navy, D.navyMid]} style={styles.hero}>
        <SafeAreaView edges={['top']} style={styles.heroSafe}>
          <View style={styles.heroTop}>
            <Pressable onPress={() => navigation.goBack()} style={styles.backBtn}>
              <Feather name="chevron-left" size={24} color={D.white} />
            </Pressable>
            <View style={styles.heroTitleWrap}>
              <Text style={styles.heroEyebrow}>YOUR INVESTOR IDENTITY</Text>
              <Text style={styles.heroTitle}>{archetype.title}</Text>
            </View>
            <View style={[styles.archetypeEmoji, { backgroundColor: archetype.color + '30' }]}>
              <Text style={{ fontSize: 24 }}>{archetype.emoji}</Text>
            </View>
          </View>
          
          <Text style={styles.heroDescription}>{archetype.description}</Text>
          
          <View style={styles.heroTags}>
            <View style={[styles.heroTag, { backgroundColor: 'rgba(255,255,255,0.1)' }]}>
              <Feather name="user" size={12} color={D.white} />
              <Text style={styles.heroTagText}>{archetype.coachingTone}</Text>
            </View>
            <View style={[styles.heroTag, { backgroundColor: 'rgba(255,255,255,0.1)' }]}>
              <Feather name="pie-chart" size={12} color={D.white} />
              <Text style={styles.heroTagText}>{archetype.strategy}</Text>
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
        {/* Dimensions Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your Dimensions</Text>
          <View style={styles.dimensionsCard}>
            <DimensionBar
              label="Risk Tolerance"
              value={DEMO_DIMENSIONS.riskTolerance}
              color={D.green}
              delay={0}
            />
            <DimensionBar
              label="Locus of Control"
              value={DEMO_DIMENSIONS.locusOfControl}
              color={D.indigo}
              delay={100}
            />
            <DimensionBar
              label="Loss Aversion"
              value={100 - DEMO_DIMENSIONS.lossAversion}
              color={D.amber}
              delay={200}
            />
            <DimensionBar
              label="Sophistication"
              value={DEMO_DIMENSIONS.sophistication}
              color={D.green}
              delay={300}
            />
          </View>
        </View>
        
        {/* Bias Detection Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Bias Detection</Text>
            <View style={styles.sectionBadge}>
              <Feather name="eye" size={12} color={D.textSecondary} />
              <Text style={styles.sectionBadgeText}>Live Analysis</Text>
            </View>
          </View>
          <Text style={styles.sectionSubtitle}>
            Based on your quiz answers and portfolio behavior
          </Text>
          
          {loadingBiases ? (
            <View style={{ alignItems: 'center', paddingVertical: 20 }}>
              <ActivityIndicator size="small" color={D.indigo} />
              <Text style={{ color: D.textMuted, marginTop: 8, fontSize: 12 }}>
                Analyzing your portfolio...
              </Text>
            </View>
          ) : (
            biases.map((bias, index) => (
              <BiasGauge key={bias.type} bias={bias} index={index} />
            ))
          )}
        </View>
        
        {/* Next Best Actions Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Next Best Actions</Text>
            <View style={[styles.sectionBadge, { backgroundColor: D.greenFaint }]}>
              <Feather name="zap" size={12} color={D.green} />
              <Text style={[styles.sectionBadgeText, { color: D.green }]}>Prioritized</Text>
            </View>
          </View>
          <Text style={styles.sectionSubtitle}>
            Based on your financial state and goals
          </Text>
          
          {DEMO_ACTIONS.map((action, index) => (
            <ActionCard
              key={action.id}
              action={action}
              index={index}
              onPress={() => handleActionPress(action.screen)}
            />
          ))}
        </View>
        
        {/* Retake Quiz */}
        <Pressable style={styles.retakeButton} onPress={handleRetakeQuiz}>
          <Feather name="refresh-cw" size={16} color={D.textSecondary} />
          <Text style={styles.retakeButtonText}>Retake Quiz</Text>
        </Pressable>
        
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
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  heroTop: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    marginBottom: 12,
    gap: 12,
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
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
    fontSize: 20,
    fontWeight: '800',
    color: D.white,
    letterSpacing: -0.3,
  },
  archetypeEmoji: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  heroDescription: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.7)',
    lineHeight: 21,
    marginBottom: 14,
  },
  heroTags: {
    flexDirection: 'row',
    gap: 8,
  },
  heroTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  heroTagText: {
    fontSize: 12,
    fontWeight: '600',
    color: D.white,
  },
  
  // Scroll
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 20,
  },
  
  // Section
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: D.textPrimary,
    marginBottom: 4,
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
    backgroundColor: D.bg,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  sectionBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: D.textSecondary,
  },
  
  // Dimensions
  dimensionsCard: {
    backgroundColor: D.card,
    borderRadius: 16,
    padding: 16,
    gap: 14,
  },
  dimensionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  dimensionLabel: {
    width: 100,
    fontSize: 12,
    color: D.textSecondary,
  },
  dimensionBarOuter: {
    flex: 1,
    height: 8,
    backgroundColor: D.border,
    borderRadius: 4,
    overflow: 'hidden',
  },
  dimensionBarInner: {
    height: '100%',
    borderRadius: 4,
  },
  dimensionValue: {
    width: 28,
    fontSize: 13,
    fontWeight: '700',
    color: D.textPrimary,
    textAlign: 'right',
  },
  
  // Bias
  biasCard: {
    backgroundColor: D.card,
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
  },
  biasCardActive: {
    borderWidth: 1.5,
    borderColor: D.amber,
    shadowColor: D.amber,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
  },
  activeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    marginLeft: 'auto',
  },
  activeBadgeText: {
    fontSize: 9,
    fontWeight: '700',
    color: D.white,
  },
  biasHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 10,
  },
  biasIcon: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  biasLabel: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
    color: D.textPrimary,
  },
  biasScoreBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  biasScoreText: {
    fontSize: 11,
    fontWeight: '700',
  },
  biasBarContainer: {
    height: 6,
    backgroundColor: D.border,
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 10,
  },
  biasBar: {
    height: '100%',
    borderRadius: 3,
  },
  biasMessage: {
    fontSize: 13,
    color: D.textSecondary,
    lineHeight: 19,
  },
  
  // Actions
  actionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: D.card,
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    gap: 12,
  },
  actionPriority: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionPriorityText: {
    fontSize: 12,
    fontWeight: '800',
    color: D.white,
  },
  actionIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionContent: {
    flex: 1,
  },
  actionHeadline: {
    fontSize: 14,
    fontWeight: '700',
    color: D.textPrimary,
    marginBottom: 2,
  },
  actionDescription: {
    fontSize: 12,
    color: D.textSecondary,
    marginBottom: 4,
  },
  actionImpact: {
    fontSize: 11,
    fontWeight: '600',
  },
  
  // Retake
  retakeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    borderWidth: 1,
    borderColor: D.border,
    borderRadius: 12,
    backgroundColor: D.card,
  },
  retakeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: D.textSecondary,
  },
});
