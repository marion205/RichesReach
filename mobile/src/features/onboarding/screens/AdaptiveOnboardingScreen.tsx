/**
 * AdaptiveOnboardingScreen — Maturity-Based Onboarding
 * =====================================================
 * Tailors the onboarding experience based on user's financial maturity stage.
 * 
 * Stages:
 * - Starter: Focus on leaks, credit, emergency fund
 * - Builder: Portfolio structure, automation, diversification
 * - Optimizer: Tax efficiency, concentration alerts, scenario modeling
 * - Advanced: Options, PE, DeFi, custom strategies
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  Animated,
  StatusBar,
  Dimensions,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Feather } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ── Design Tokens ────────────────────────────────────────────────────────────

const D = {
  navy:          '#0B1426',
  navyMid:       '#0F1E35',
  white:         '#FFFFFF',
  green:         '#10B981',
  greenFaint:    '#D1FAE5',
  indigo:        '#6366F1',
  indigoFaint:   '#EEF2FF',
  amber:         '#F59E0B',
  amberFaint:    '#FEF3C7',
  purple:        '#8B5CF6',
  purpleFaint:   '#F3E8FF',
  red:           '#EF4444',
  textPrimary:   '#0F172A',
  textSecondary: '#64748B',
  textMuted:     '#94A3B8',
  card:          '#FFFFFF',
  bg:            '#F1F5F9',
  border:        '#E2E8F0',
};

// ── Maturity Stage Configuration ─────────────────────────────────────────────

type MaturityStage = 'starter' | 'builder' | 'optimizer' | 'advanced';

interface StageConfig {
  key: MaturityStage;
  title: string;
  subtitle: string;
  emoji: string;
  color: string;
  faint: string;
  description: string;
  focusAreas: string[];
  features: Array<{
    icon: string;
    title: string;
    description: string;
    screen: string;
  }>;
  aiTone: string;
  unlocks: string[];
}

const STAGES: Record<MaturityStage, StageConfig> = {
  starter: {
    key: 'starter',
    title: 'Starter',
    subtitle: 'Building your foundation',
    emoji: '🌱',
    color: D.green,
    faint: D.greenFaint,
    description: 'You\'re at the beginning of your wealth journey. Let\'s focus on the fundamentals that will set you up for success.',
    focusAreas: ['Stop financial leaks', 'Build emergency fund', 'Understand your cash flow'],
    features: [
      { icon: 'search', title: 'Leak Detector', description: 'Find and stop money drains', screen: 'LeakDetector' },
      { icon: 'shield', title: 'Emergency Fund', description: 'Build your financial fortress', screen: 'FinancialHealth' },
      { icon: 'credit-card', title: 'Credit Health', description: 'Understand and improve your score', screen: 'credit' },
    ],
    aiTone: 'Encouraging Coach',
    unlocks: ['Leak Detector', 'Budget Tools', 'Credit Score', 'Emergency Fund Tracker'],
  },
  builder: {
    key: 'builder',
    title: 'Builder',
    subtitle: 'Growing your wealth',
    emoji: '🏗️',
    color: D.indigo,
    faint: D.indigoFaint,
    description: 'You have a foundation. Now it\'s time to put your money to work with systematic, automated investing.',
    focusAreas: ['Automate contributions', 'Build diversified portfolio', 'Track millionaire path'],
    features: [
      { icon: 'trending-up', title: 'AI Portfolio Builder', description: 'Personalized investment plan', screen: 'AIPortfolioBuilder' },
      { icon: 'flag', title: 'Wealth Arrival', description: 'Your millionaire timeline', screen: 'WealthArrival' },
      { icon: 'repeat', title: 'Auto-Invest', description: 'Set it and forget it', screen: 'Reallocate' },
    ],
    aiTone: 'Strategic Architect',
    unlocks: ['Portfolio Builder', 'Wealth Arrival', 'Auto-Invest', 'Diversification Analysis'],
  },
  optimizer: {
    key: 'optimizer',
    title: 'Optimizer',
    subtitle: 'Maximizing efficiency',
    emoji: '⚡',
    color: D.amber,
    faint: D.amberFaint,
    description: 'Your portfolio is growing. Let\'s optimize for tax efficiency, reduce concentration risk, and model scenarios.',
    focusAreas: ['Tax-loss harvesting', 'Concentration monitoring', 'Fee optimization'],
    features: [
      { icon: 'sliders', title: 'Tax Optimizer', description: 'Smart tax-loss harvesting', screen: 'portfolio' },
      { icon: 'alert-triangle', title: 'Bias Detection', description: 'Real-time portfolio analysis', screen: 'InvestorProfile' },
      { icon: 'bar-chart-2', title: 'Scenario Modeling', description: 'What-if analysis', screen: 'LifeDecision' },
    ],
    aiTone: 'Precise Analyst',
    unlocks: ['Tax Optimizer', 'Concentration Alerts', 'Fee Analysis', 'Scenario Modeling'],
  },
  advanced: {
    key: 'advanced',
    title: 'Advanced',
    subtitle: 'Sophisticated strategies',
    emoji: '🎯',
    color: D.purple,
    faint: D.purpleFaint,
    description: 'You\'re ready for advanced strategies. Access options, alternative investments, and custom intelligence.',
    focusAreas: ['Options strategies', 'Alternative investments', 'Custom portfolio overlays'],
    features: [
      { icon: 'layers', title: 'Options Lab', description: 'Covered calls, spreads, hedging', screen: 'options' },
      { icon: 'briefcase', title: 'Private Markets', description: 'PE and venture access', screen: 'private-markets' },
      { icon: 'cpu', title: 'Custom AI', description: 'Train your own models', screen: 'AIPortfolioBuilder' },
    ],
    aiTone: 'Sophisticated Partner',
    unlocks: ['Options Lab', 'Private Markets', 'DeFi Integration', 'Custom Strategies'],
  },
};

// ── Stage Selection Card ─────────────────────────────────────────────────────

function StageCard({
  stage,
  isSelected,
  onSelect,
  index,
}: {
  stage: StageConfig;
  isSelected: boolean;
  onSelect: () => void;
  index: number;
}) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 400,
        delay: index * 100,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 400,
        delay: index * 100,
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
        opacity: fadeAnim,
        transform: [{ translateY: slideAnim }, { scale: scaleAnim }],
      }}
    >
      <Pressable
        onPress={onSelect}
        onPressIn={onPressIn}
        onPressOut={onPressOut}
        style={[
          styles.stageCard,
          isSelected && { borderColor: stage.color, borderWidth: 2 },
        ]}
      >
        <View style={[styles.stageEmoji, { backgroundColor: stage.faint }]}>
          <Text style={{ fontSize: 28 }}>{stage.emoji}</Text>
        </View>
        <View style={styles.stageContent}>
          <Text style={styles.stageTitle}>{stage.title}</Text>
          <Text style={styles.stageSubtitle}>{stage.subtitle}</Text>
        </View>
        {isSelected && (
          <View style={[styles.checkBadge, { backgroundColor: stage.color }]}>
            <Feather name="check" size={14} color={D.white} />
          </View>
        )}
      </Pressable>
    </Animated.View>
  );
}

// ── Feature Card ─────────────────────────────────────────────────────────────

function FeatureCard({
  feature,
  color,
  index,
  onPress,
}: {
  feature: StageConfig['features'][0];
  color: string;
  index: number;
  onPress: () => void;
}) {
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 300,
      delay: index * 80,
      useNativeDriver: true,
    }).start();
  }, []);

  return (
    <Animated.View style={{ opacity: fadeAnim }}>
      <Pressable style={styles.featureCard} onPress={onPress}>
        <View style={[styles.featureIcon, { backgroundColor: color + '20' }]}>
          <Feather name={feature.icon as any} size={20} color={color} />
        </View>
        <View style={styles.featureContent}>
          <Text style={styles.featureTitle}>{feature.title}</Text>
          <Text style={styles.featureDescription}>{feature.description}</Text>
        </View>
        <Feather name="chevron-right" size={18} color={D.textMuted} />
      </Pressable>
    </Animated.View>
  );
}

// ── Main Component ───────────────────────────────────────────────────────────

export default function AdaptiveOnboardingScreen() {
  const navigation = useNavigation<any>();
  const [step, setStep] = useState<'select' | 'confirm'>('select');
  const [selectedStage, setSelectedStage] = useState<MaturityStage | null>(null);

  const stage = selectedStage ? STAGES[selectedStage] : null;

  const handleStageSelect = (stageKey: MaturityStage) => {
    setSelectedStage(stageKey);
  };

  const handleContinue = () => {
    if (selectedStage) {
      setStep('confirm');
    }
  };

  const handleComplete = () => {
    // Navigate to quiz then home
    navigation.reset({
      index: 0,
      routes: [{ name: 'InvestorQuiz' }],
    });
  };

  const handleFeaturePress = (screen: string) => {
    navigation.navigate(screen);
  };

  // Step 1: Stage Selection
  if (step === 'select') {
    return (
      <View style={styles.root}>
        <StatusBar barStyle="light-content" />
        <LinearGradient colors={[D.navy, D.navyMid]} style={styles.header}>
          <SafeAreaView edges={['top']}>
            <View style={styles.headerContent}>
              <Text style={styles.headerEyebrow}>PERSONALIZED EXPERIENCE</Text>
              <Text style={styles.headerTitle}>Where are you in your{'\n'}wealth journey?</Text>
              <Text style={styles.headerSubtitle}>
                This helps us tailor the app to your needs
              </Text>
            </View>
          </SafeAreaView>
        </LinearGradient>

        <ScrollView style={styles.content} contentContainerStyle={styles.contentInner}>
          {Object.values(STAGES).map((s, index) => (
            <StageCard
              key={s.key}
              stage={s}
              isSelected={selectedStage === s.key}
              onSelect={() => handleStageSelect(s.key)}
              index={index}
            />
          ))}
          <View style={{ height: 100 }} />
        </ScrollView>

        {selectedStage && (
          <View style={styles.footer}>
            <Pressable
              style={[styles.continueButton, { backgroundColor: STAGES[selectedStage].color }]}
              onPress={handleContinue}
            >
              <Text style={styles.continueButtonText}>Continue</Text>
              <Feather name="arrow-right" size={18} color={D.white} />
            </Pressable>
          </View>
        )}
      </View>
    );
  }

  // Step 2: Confirmation & Feature Preview
  if (step === 'confirm' && stage) {
    return (
      <View style={styles.root}>
        <StatusBar barStyle="light-content" />
        <LinearGradient colors={[D.navy, D.navyMid]} style={styles.heroSmall}>
          <SafeAreaView edges={['top']}>
            <View style={styles.heroSmallContent}>
              <Pressable onPress={() => setStep('select')} style={styles.backBtn}>
                <Feather name="chevron-left" size={24} color={D.white} />
              </Pressable>
              <View style={[styles.stageBadgeLarge, { backgroundColor: stage.faint }]}>
                <Text style={{ fontSize: 40 }}>{stage.emoji}</Text>
              </View>
              <Text style={styles.confirmTitle}>{stage.title}</Text>
              <Text style={styles.confirmSubtitle}>{stage.subtitle}</Text>
            </View>
          </SafeAreaView>
        </LinearGradient>

        <ScrollView style={styles.content} contentContainerStyle={styles.contentInner}>
          {/* Description */}
          <View style={styles.descriptionCard}>
            <Text style={styles.descriptionText}>{stage.description}</Text>
          </View>

          {/* Focus Areas */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>We'll Focus On</Text>
            <View style={styles.focusGrid}>
              {stage.focusAreas.map((area, i) => (
                <View key={i} style={[styles.focusPill, { backgroundColor: stage.faint }]}>
                  <Feather name="check-circle" size={14} color={stage.color} />
                  <Text style={[styles.focusPillText, { color: stage.color }]}>{area}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* Features Preview */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Your Key Features</Text>
            {stage.features.map((feature, index) => (
              <FeatureCard
                key={feature.title}
                feature={feature}
                color={stage.color}
                index={index}
                onPress={() => handleFeaturePress(feature.screen)}
              />
            ))}
          </View>

          {/* AI Tone */}
          <View style={styles.aiToneCard}>
            <View style={styles.aiToneIcon}>
              <Feather name="message-circle" size={20} color={stage.color} />
            </View>
            <View>
              <Text style={styles.aiToneLabel}>Your AI Coach</Text>
              <Text style={[styles.aiToneName, { color: stage.color }]}>{stage.aiTone}</Text>
            </View>
          </View>

          {/* Unlocks */}
          <View style={styles.unlocksCard}>
            <Text style={styles.unlocksTitle}>You'll Unlock</Text>
            <View style={styles.unlocksList}>
              {stage.unlocks.map((unlock, i) => (
                <View key={i} style={styles.unlockItem}>
                  <Feather name="unlock" size={12} color={D.green} />
                  <Text style={styles.unlockText}>{unlock}</Text>
                </View>
              ))}
            </View>
          </View>

          <View style={{ height: 100 }} />
        </ScrollView>

        <View style={styles.footer}>
          <Pressable
            style={[styles.continueButton, { backgroundColor: stage.color }]}
            onPress={handleComplete}
          >
            <Text style={styles.continueButtonText}>Start My Journey</Text>
            <Feather name="arrow-right" size={18} color={D.white} />
          </Pressable>
        </View>
      </View>
    );
  }

  return null;
}

// ── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: D.bg,
  },
  
  // Header
  header: {
    paddingBottom: 24,
  },
  headerContent: {
    paddingHorizontal: 24,
    paddingTop: 16,
  },
  headerEyebrow: {
    fontSize: 10,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.5)',
    letterSpacing: 1.5,
    marginBottom: 8,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: D.white,
    lineHeight: 36,
    marginBottom: 8,
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.6)',
  },
  
  // Hero Small
  heroSmall: {
    paddingBottom: 20,
  },
  heroSmallContent: {
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingTop: 8,
  },
  backBtn: {
    position: 'absolute',
    left: 16,
    top: 8,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  stageBadgeLarge: {
    width: 80,
    height: 80,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 32,
    marginBottom: 12,
  },
  confirmTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: D.white,
    marginBottom: 4,
  },
  confirmSubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.6)',
  },
  
  // Content
  content: {
    flex: 1,
  },
  contentInner: {
    padding: 16,
  },
  
  // Stage Card
  stageCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: D.card,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  stageEmoji: {
    width: 56,
    height: 56,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  stageContent: {
    flex: 1,
  },
  stageTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: D.textPrimary,
    marginBottom: 2,
  },
  stageSubtitle: {
    fontSize: 13,
    color: D.textSecondary,
  },
  checkBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  
  // Description
  descriptionCard: {
    backgroundColor: D.card,
    borderRadius: 14,
    padding: 16,
    marginBottom: 20,
  },
  descriptionText: {
    fontSize: 15,
    color: D.textSecondary,
    lineHeight: 24,
  },
  
  // Section
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: D.textPrimary,
    marginBottom: 12,
  },
  
  // Focus Grid
  focusGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  focusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
  },
  focusPillText: {
    fontSize: 13,
    fontWeight: '600',
  },
  
  // Feature Card
  featureCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: D.card,
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
  },
  featureIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  featureContent: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: D.textPrimary,
    marginBottom: 2,
  },
  featureDescription: {
    fontSize: 12,
    color: D.textSecondary,
  },
  
  // AI Tone
  aiToneCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: D.card,
    borderRadius: 14,
    padding: 16,
    marginBottom: 16,
    gap: 12,
  },
  aiToneIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: D.indigoFaint,
    alignItems: 'center',
    justifyContent: 'center',
  },
  aiToneLabel: {
    fontSize: 11,
    color: D.textMuted,
    marginBottom: 2,
  },
  aiToneName: {
    fontSize: 16,
    fontWeight: '700',
  },
  
  // Unlocks
  unlocksCard: {
    backgroundColor: D.card,
    borderRadius: 14,
    padding: 16,
  },
  unlocksTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: D.textPrimary,
    marginBottom: 12,
  },
  unlocksList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  unlockItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: D.greenFaint,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  unlockText: {
    fontSize: 12,
    color: D.green,
    fontWeight: '500',
  },
  
  // Footer
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 16,
    paddingBottom: 32,
    backgroundColor: D.bg,
  },
  continueButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 16,
    borderRadius: 14,
  },
  continueButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: D.white,
  },
});
