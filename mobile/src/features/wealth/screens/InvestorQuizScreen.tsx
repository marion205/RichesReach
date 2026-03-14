/**
 * InvestorQuizScreen — Behavioral Identity Quiz
 * ===============================================
 * 10-question quiz to determine the user's investor archetype.
 * Based on Pompian's Behavioral Finance framework.
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  Animated,
  Dimensions,
  StatusBar,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Feather } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import Slider from '@react-native-community/slider';

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
  amber:         '#F59E0B',
  textPrimary:   '#0F172A',
  textSecondary: '#64748B',
  textMuted:     '#94A3B8',
  card:          '#FFFFFF',
  bg:            '#F1F5F9',
  border:        '#E2E8F0',
};

// ── Quiz Questions ───────────────────────────────────────────────────────────

interface QuizOption {
  id: string;
  text: string;
}

interface QuizQuestion {
  id: string;
  text: string;
  subtext?: string;
  type: 'single_choice' | 'slider';
  options?: QuizOption[];
  sliderMin?: number;
  sliderMax?: number;
  sliderLabels?: string[];
}

const QUESTIONS: QuizQuestion[] = [
  {
    id: 'q1_market_drop',
    text: 'A stock you own drops 15% in one week. What\'s your gut reaction?',
    subtext: 'Be honest — what would you actually do?',
    type: 'single_choice',
    options: [
      { id: 'a', text: 'Sell immediately to protect what\'s left' },
      { id: 'b', text: 'Do nothing and wait for recovery' },
      { id: 'c', text: 'Buy more at the "discount"' },
      { id: 'd', text: 'Research why it dropped before deciding' },
    ],
  },
  {
    id: 'q2_wealth_view',
    text: 'Which statement best describes your view on wealth?',
    type: 'single_choice',
    options: [
      { id: 'a', text: 'I want to ensure I never backslide into financial stress' },
      { id: 'b', text: 'I want my money to work as hard as I do' },
      { id: 'c', text: 'I want to find opportunities before others do' },
      { id: 'd', text: 'I just want simple, automatic growth' },
    ],
  },
  {
    id: 'q3_luck_vs_skill',
    text: 'How much of financial success is your decisions vs. luck?',
    subtext: 'Slide toward which factor you believe matters more.',
    type: 'slider',
    sliderMin: 0,
    sliderMax: 10,
    sliderLabels: ['Mostly Luck', '50/50', 'Mostly My Decisions'],
  },
  {
    id: 'q4_horizon',
    text: 'What\'s your primary investment time horizon?',
    type: 'single_choice',
    options: [
      { id: 'a', text: 'Less than 2 years' },
      { id: 'b', text: '2-5 years' },
      { id: 'c', text: '5-15 years' },
      { id: 'd', text: '15+ years (retirement)' },
    ],
  },
  {
    id: 'q5_volatility',
    text: 'Your portfolio is down 25% from last month. How do you feel?',
    type: 'single_choice',
    options: [
      { id: 'a', text: 'Sick to my stomach — I\'d lose sleep' },
      { id: 'b', text: 'Uncomfortable, but I know it\'s part of investing' },
      { id: 'c', text: 'Fine — I\'ve seen this before' },
      { id: 'd', text: 'Excited — time to buy more!' },
    ],
  },
  {
    id: 'q6_knowledge',
    text: 'How would you describe your investment knowledge?',
    type: 'single_choice',
    options: [
      { id: 'a', text: 'Beginner — I know basics like stocks and savings' },
      { id: 'b', text: 'Intermediate — ETFs, diversification, compounding' },
      { id: 'c', text: 'Advanced — tax strategies, options, alternatives' },
      { id: 'd', text: 'Expert — I could teach a course' },
    ],
  },
  {
    id: 'q7_decision_style',
    text: 'When making a big financial decision, you typically:',
    type: 'single_choice',
    options: [
      { id: 'a', text: 'Ask trusted friends/family for advice' },
      { id: 'b', text: 'Research extensively before acting' },
      { id: 'c', text: 'Trust your gut and move quickly' },
      { id: 'd', text: 'Wait for someone else to go first' },
    ],
  },
  {
    id: 'q8_concentration',
    text: 'If you had $100,000 to invest, you\'d prefer to:',
    type: 'single_choice',
    options: [
      { id: 'a', text: 'Put it all in one high-conviction stock' },
      { id: 'b', text: 'Split between 3-5 stocks you know well' },
      { id: 'c', text: 'Buy a diversified index fund' },
      { id: 'd', text: 'Keep most in cash/bonds' },
    ],
  },
  {
    id: 'q9_news_reaction',
    text: 'When you see scary financial news:',
    type: 'single_choice',
    options: [
      { id: 'a', text: 'I want to check my portfolio and maybe sell' },
      { id: 'b', text: 'I feel anxious but stay the course' },
      { id: 'c', text: 'I ignore it — news is mostly noise' },
      { id: 'd', text: 'I see it as a buying opportunity' },
    ],
  },
  {
    id: 'q10_risk_slider',
    text: 'How much short-term loss could you handle for long-term gains?',
    subtext: 'At what point would you panic?',
    type: 'slider',
    sliderMin: 5,
    sliderMax: 50,
    sliderLabels: ['5%', '25%', '50%'],
  },
];

// ── Archetype Results ────────────────────────────────────────────────────────

interface ArchetypeResult {
  key: string;
  title: string;
  emoji: string;
  description: string;
  focus: string;
  color: string;
}

const ARCHETYPES: Record<string, ArchetypeResult> = {
  cautious_protector: {
    key: 'cautious_protector',
    title: 'The Cautious Protector',
    emoji: '🛡️',
    description: 'You prioritize security and steady progress over aggressive growth.',
    focus: 'Security, risk mitigation, and protecting what you have',
    color: D.green,
  },
  steady_builder: {
    key: 'steady_builder',
    title: 'The Steady Builder',
    emoji: '🏗️',
    description: 'You believe in systems and automation. You trust compounding over time.',
    focus: 'Efficiency, systems, and the math of time',
    color: D.indigo,
  },
  opportunity_hunter: {
    key: 'opportunity_hunter',
    title: 'The Opportunity Hunter',
    emoji: '🎯',
    description: 'You\'re energized by finding the next big opportunity.',
    focus: 'Growth, edge, and strategic positioning',
    color: D.amber,
  },
  reactive_trader: {
    key: 'reactive_trader',
    title: 'The Reactive Trader',
    emoji: '⚡',
    description: 'You\'re emotionally connected to your investments.',
    focus: 'Stability through structure and guardrails',
    color: '#EF4444',
  },
};

// ── Option Card Component ────────────────────────────────────────────────────

function OptionCard({
  option,
  selected,
  onPress,
  index,
}: {
  option: QuizOption;
  selected: boolean;
  onPress: () => void;
  index: number;
}) {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 300,
        delay: index * 60,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 300,
        delay: index * 60,
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
        style={[
          styles.optionCard,
          selected && styles.optionCardSelected,
        ]}
      >
        <View style={[styles.optionRadio, selected && styles.optionRadioSelected]}>
          {selected && <View style={styles.optionRadioInner} />}
        </View>
        <Text style={[styles.optionText, selected && styles.optionTextSelected]}>
          {option.text}
        </Text>
      </Pressable>
    </Animated.View>
  );
}

// ── Main Component ───────────────────────────────────────────────────────────

export default function InvestorQuizScreen() {
  const navigation = useNavigation<any>();
  const scrollRef = useRef<ScrollView>(null);
  
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [sliderValues, setSliderValues] = useState<Record<string, number>>({
    q3_luck_vs_skill: 5,
    q10_risk_slider: 25,
  });
  const [showResult, setShowResult] = useState(false);
  const [archetype, setArchetype] = useState<ArchetypeResult | null>(null);
  
  const progressAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(progressAnim, {
      toValue: (currentQuestion + 1) / QUESTIONS.length,
      duration: 300,
      useNativeDriver: false,
    }).start();
  }, [currentQuestion]);

  const question = QUESTIONS[currentQuestion];
  const progress = (currentQuestion + 1) / QUESTIONS.length;
  const canProceed = question.type === 'slider' || answers[question.id];

  const handleOptionSelect = useCallback((optionId: string) => {
    setAnswers(prev => ({ ...prev, [question.id]: optionId }));
  }, [question.id]);

  const handleSliderChange = useCallback((value: number) => {
    setSliderValues(prev => ({ ...prev, [question.id]: value }));
    setAnswers(prev => ({ ...prev, [question.id]: value.toString() }));
  }, [question.id]);

  const calculateArchetype = (): string => {
    // Simplified scoring for frontend
    // In production, this would call the backend API
    
    let riskScore = 50;
    let lossAversionScore = 50;
    let locusScore = 50;
    
    // Q1: Market drop reaction
    const q1 = answers['q1_market_drop'];
    if (q1 === 'a') { riskScore -= 20; lossAversionScore += 30; }
    if (q1 === 'c') { riskScore += 25; lossAversionScore -= 20; }
    if (q1 === 'd') { locusScore += 15; }
    
    // Q2: Wealth view
    const q2 = answers['q2_wealth_view'];
    if (q2 === 'a') { lossAversionScore += 20; }
    if (q2 === 'c') { riskScore += 25; locusScore += 25; }
    
    // Q3: Luck vs skill (slider)
    const q3 = sliderValues['q3_luck_vs_skill'];
    locusScore += (q3 - 5) * 10;
    
    // Q5: Volatility comfort
    const q5 = answers['q5_volatility'];
    if (q5 === 'a') { riskScore -= 25; lossAversionScore += 30; }
    if (q5 === 'd') { riskScore += 30; lossAversionScore -= 20; }
    
    // Q9: News reaction
    const q9 = answers['q9_news_reaction'];
    if (q9 === 'a') { lossAversionScore += 25; }
    if (q9 === 'd') { riskScore += 25; }
    
    // Q10: Risk tolerance (slider)
    const q10 = sliderValues['q10_risk_slider'];
    riskScore += (q10 - 25) * 2;
    
    // Determine archetype
    if (lossAversionScore > 60 && riskScore < 45) {
      return 'cautious_protector';
    }
    if (riskScore > 60 && locusScore > 55 && lossAversionScore < 50) {
      return 'opportunity_hunter';
    }
    if (lossAversionScore > 55 && locusScore > 50 && riskScore < 55) {
      return 'reactive_trader';
    }
    return 'steady_builder';
  };

  const handleNext = () => {
    if (currentQuestion < QUESTIONS.length - 1) {
      setCurrentQuestion(prev => prev + 1);
      scrollRef.current?.scrollTo({ y: 0, animated: true });
    } else {
      // Calculate result
      const result = calculateArchetype();
      setArchetype(ARCHETYPES[result]);
      setShowResult(true);
    }
  };

  const handleBack = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(prev => prev - 1);
      scrollRef.current?.scrollTo({ y: 0, animated: true });
    } else {
      navigation.goBack();
    }
  };

  const handleFinish = () => {
    // Navigate to profile screen with result
    navigation.navigate('InvestorProfile', { archetype: archetype?.key });
  };

  // ── Result Screen ──────────────────────────────────────────────────────────

  if (showResult && archetype) {
    return (
      <View style={styles.root}>
        <StatusBar barStyle="light-content" />
        <LinearGradient colors={[D.navy, D.navyMid]} style={styles.resultContainer}>
          <SafeAreaView style={styles.resultSafe}>
            <View style={styles.resultContent}>
              <Text style={styles.resultEmoji}>{archetype.emoji}</Text>
              <Text style={styles.resultTitle}>{archetype.title}</Text>
              <Text style={styles.resultDescription}>{archetype.description}</Text>
              
              <View style={styles.resultFocusCard}>
                <Text style={styles.resultFocusLabel}>YOUR FOCUS</Text>
                <Text style={styles.resultFocusText}>{archetype.focus}</Text>
              </View>
              
              <Pressable
                style={({ pressed }) => [
                  styles.resultButton,
                  { backgroundColor: archetype.color, opacity: pressed ? 0.9 : 1 },
                ]}
                onPress={handleFinish}
              >
                <Text style={styles.resultButtonText}>See Your Profile</Text>
                <Feather name="arrow-right" size={20} color={D.white} />
              </Pressable>
            </View>
          </SafeAreaView>
        </LinearGradient>
      </View>
    );
  }

  // ── Quiz Screen ────────────────────────────────────────────────────────────

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />
      
      {/* Header */}
      <LinearGradient colors={[D.navy, D.navyMid]} style={styles.header}>
        <SafeAreaView edges={['top']} style={styles.headerSafe}>
          <View style={styles.headerTop}>
            <Pressable onPress={handleBack} style={styles.backBtn}>
              <Feather name="chevron-left" size={24} color={D.white} />
            </Pressable>
            <View style={styles.headerTitleWrap}>
              <Text style={styles.headerEyebrow}>BEHAVIORAL IDENTITY</Text>
              <Text style={styles.headerTitle}>Discover Your Type</Text>
            </View>
            <View style={styles.headerProgress}>
              <Text style={styles.headerProgressText}>
                {currentQuestion + 1}/{QUESTIONS.length}
              </Text>
            </View>
          </View>
          
          {/* Progress Bar */}
          <View style={styles.progressBar}>
            <Animated.View
              style={[
                styles.progressFill,
                {
                  width: progressAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: ['0%', '100%'],
                  }),
                },
              ]}
            />
          </View>
        </SafeAreaView>
      </LinearGradient>
      
      {/* Question Content */}
      <ScrollView
        ref={scrollRef}
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.questionText}>{question.text}</Text>
        {question.subtext && (
          <Text style={styles.questionSubtext}>{question.subtext}</Text>
        )}
        
        {question.type === 'single_choice' && question.options && (
          <View style={styles.optionsContainer}>
            {question.options.map((option, index) => (
              <OptionCard
                key={option.id}
                option={option}
                selected={answers[question.id] === option.id}
                onPress={() => handleOptionSelect(option.id)}
                index={index}
              />
            ))}
          </View>
        )}
        
        {question.type === 'slider' && (
          <View style={styles.sliderContainer}>
            <Slider
              style={styles.slider}
              minimumValue={question.sliderMin || 0}
              maximumValue={question.sliderMax || 10}
              step={1}
              value={sliderValues[question.id] || (question.sliderMin! + question.sliderMax!) / 2}
              onValueChange={handleSliderChange}
              minimumTrackTintColor={D.green}
              maximumTrackTintColor={D.border}
              thumbTintColor={D.green}
            />
            <View style={styles.sliderLabels}>
              {question.sliderLabels?.map((label, i) => (
                <Text
                  key={i}
                  style={[
                    styles.sliderLabel,
                    i === 0 && { textAlign: 'left' },
                    i === question.sliderLabels!.length - 1 && { textAlign: 'right' },
                  ]}
                >
                  {label}
                </Text>
              ))}
            </View>
            <View style={styles.sliderValueBadge}>
              <Text style={styles.sliderValueText}>
                {question.id === 'q10_risk_slider'
                  ? `${sliderValues[question.id] || 25}% drop`
                  : sliderValues[question.id] || 5}
              </Text>
            </View>
          </View>
        )}
      </ScrollView>
      
      {/* Next Button */}
      <SafeAreaView edges={['bottom']} style={styles.footer}>
        <Pressable
          style={[styles.nextButton, !canProceed && styles.nextButtonDisabled]}
          onPress={handleNext}
          disabled={!canProceed}
        >
          <Text style={styles.nextButtonText}>
            {currentQuestion === QUESTIONS.length - 1 ? 'See Results' : 'Continue'}
          </Text>
          <Feather
            name={currentQuestion === QUESTIONS.length - 1 ? 'check' : 'arrow-right'}
            size={20}
            color={D.white}
          />
        </Pressable>
      </SafeAreaView>
    </View>
  );
}

// ── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: D.bg,
  },
  
  // Header
  header: {},
  headerSafe: {
    paddingHorizontal: 20,
    paddingBottom: 16,
  },
  headerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    marginBottom: 14,
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
  headerTitleWrap: {
    flex: 1,
  },
  headerEyebrow: {
    fontSize: 9,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.5)',
    letterSpacing: 1.5,
    marginBottom: 2,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: D.white,
    letterSpacing: -0.3,
  },
  headerProgress: {
    backgroundColor: 'rgba(255,255,255,0.15)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  headerProgressText: {
    fontSize: 13,
    fontWeight: '700',
    color: D.white,
  },
  
  // Progress bar
  progressBar: {
    height: 4,
    backgroundColor: 'rgba(255,255,255,0.15)',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: D.green,
    borderRadius: 2,
  },
  
  // Scroll
  scroll: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  
  // Question
  questionText: {
    fontSize: 22,
    fontWeight: '700',
    color: D.textPrimary,
    lineHeight: 30,
    marginBottom: 8,
  },
  questionSubtext: {
    fontSize: 14,
    color: D.textSecondary,
    marginBottom: 24,
  },
  
  // Options
  optionsContainer: {
    marginTop: 8,
    gap: 10,
  },
  optionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: D.card,
    borderRadius: 14,
    padding: 16,
    borderWidth: 2,
    borderColor: D.border,
    gap: 12,
  },
  optionCardSelected: {
    borderColor: D.green,
    backgroundColor: D.greenFaint,
  },
  optionRadio: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 2,
    borderColor: D.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  optionRadioSelected: {
    borderColor: D.green,
  },
  optionRadioInner: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: D.green,
  },
  optionText: {
    flex: 1,
    fontSize: 15,
    color: D.textPrimary,
    lineHeight: 21,
  },
  optionTextSelected: {
    fontWeight: '600',
  },
  
  // Slider
  sliderContainer: {
    marginTop: 32,
    paddingHorizontal: 8,
  },
  slider: {
    width: '100%',
    height: 40,
  },
  sliderLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  sliderLabel: {
    flex: 1,
    fontSize: 12,
    color: D.textSecondary,
    textAlign: 'center',
  },
  sliderValueBadge: {
    alignSelf: 'center',
    marginTop: 20,
    backgroundColor: D.green,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
  },
  sliderValueText: {
    fontSize: 16,
    fontWeight: '700',
    color: D.white,
  },
  
  // Footer
  footer: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 8,
    backgroundColor: D.bg,
    borderTopWidth: 1,
    borderTopColor: D.border,
  },
  nextButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: D.green,
    paddingVertical: 16,
    borderRadius: 14,
    gap: 8,
  },
  nextButtonDisabled: {
    backgroundColor: D.textMuted,
  },
  nextButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: D.white,
  },
  
  // Result screen
  resultContainer: {
    flex: 1,
  },
  resultSafe: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  resultContent: {
    alignItems: 'center',
  },
  resultEmoji: {
    fontSize: 80,
    marginBottom: 20,
  },
  resultTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: D.white,
    textAlign: 'center',
    marginBottom: 12,
  },
  resultDescription: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.75)',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  resultFocusCard: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 16,
    padding: 20,
    width: '100%',
    marginBottom: 32,
  },
  resultFocusLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.5)',
    letterSpacing: 1.5,
    marginBottom: 8,
  },
  resultFocusText: {
    fontSize: 16,
    color: D.white,
    fontWeight: '600',
    lineHeight: 24,
  },
  resultButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 14,
    gap: 8,
    width: '100%',
  },
  resultButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: D.white,
  },
});
