import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
  Animated,
  Dimensions,
  ActivityIndicator,
  Easing,
} from 'react-native';
import { useMutation, useQuery } from '@apollo/client';
import { gql } from '@apollo/client';
import * as Speech from 'expo-speech';
import * as Haptics from 'expo-haptics';
import { useVoice } from '../../../contexts/VoiceContext';
import { LinearGradient } from 'expo-linear-gradient';
import MemeQuestScreen from '../../social/screens/MemeQuestScreen';
// import ConfettiCannon from 'react-native-confetti-cannon';

const { width, height } = Dimensions.get('window');

// Safe text rendering wrapper - prevents text rendering errors
const SafeText: React.FC<React.PropsWithChildren<{ style?: any }>> = ({ children, style }) => {
  if (typeof children === 'string' || typeof children === 'number') {
    return <Text style={style}>{children}</Text>;
  }
  return <>{children}</>;
};

// Simple Confetti Component - Fallback without external dependencies
const SimpleConfetti: React.FC<{ visible: boolean }> = ({ visible }) => {
  const confettiPieces = useRef(
    Array.from({ length: 50 }, (_, i) => ({
      id: i,
      animation: new Animated.Value(0),
      x: Math.random() * width,
      delay: Math.random() * 1000,
    }))
  ).current;

  useEffect(() => {
    if (visible) {
      confettiPieces.forEach((piece) => {
        Animated.sequence([
          Animated.delay(piece.delay),
          Animated.timing(piece.animation, {
            toValue: 1,
            duration: 2000,
            useNativeDriver: true,
          }),
        ]).start();
      });
    } else {
      confettiPieces.forEach((piece) => {
        piece.animation.setValue(0);
      });
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <View style={styles.confettiContainer}>
      {confettiPieces.map((piece) => (
        <Animated.View
          key={piece.id}
          style={[
            styles.confettiPiece,
            {
              left: piece.x,
              opacity: piece.animation,
              transform: [
                {
                  translateY: piece.animation.interpolate({
                    inputRange: [0, 1],
                    outputRange: [-50, height + 50],
                  }),
                },
                {
                  rotate: piece.animation.interpolate({
                    inputRange: [0, 1],
                    outputRange: ['0deg', '720deg'],
                  }),
                },
              ],
            },
          ]}
        >
          <Text style={styles.confettiEmoji}>
            {['🎉', '✨', '🌟', '💫', '🎊'][piece.id % 5]}
          </Text>
        </Animated.View>
      ))}
    </View>
  );
};

// Enhanced Lesson Card - Super playful with bouncy icons and sparkles
const LessonCard: React.FC<{
  lesson: any;
  index: number;
  onPress: () => void;
}> = ({ lesson, index, onPress }) => {
  const cardAnimation = useRef(new Animated.Value(0)).current;
  const pulseAnimation = useRef(new Animated.Value(1)).current;
  const wiggleAnimation = useRef(new Animated.Value(0)).current; // Playful wiggle on hover
  const pressAnimation = useRef(new Animated.Value(1)).current;
  const sparkleAnimation = useRef(new Animated.Value(0)).current; // Subtle sparkle effect
  
  useEffect(() => {
    // Ensure pulseAnimation is properly initialized before starting
    if (pulseAnimation && typeof pulseAnimation.setValue === 'function') {
      // Simple pulse animation without complex easing
      const pulseLoop = () => {
        Animated.sequence([
          Animated.timing(pulseAnimation, {
            toValue: 1.1,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnimation, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
        ]).start(() => pulseLoop());
      };
      pulseLoop();
    }
    
    // Playful staggered entrance: bounce + wiggle
    Animated.sequence([
      Animated.delay(index * 120),
      Animated.parallel([
        Animated.spring(cardAnimation, {
          toValue: 1,
          tension: 18,
          friction: 1.5,
          useNativeDriver: true,
        }),
        Animated.spring(wiggleAnimation, {
          toValue: 1,
          tension: 12,
          friction: 4,
          useNativeDriver: true,
        }),
      ]),
    ]).start();
    
    // Twinkling sparkle for extra playfulness
    Animated.loop(
      Animated.timing(sparkleAnimation, {
        toValue: 1,
        duration: 2000,
        useNativeDriver: true,
      })
    ).start();
  }, [index]);
  
  const handlePressIn = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); // Bouncy haptic
    Animated.parallel([
      Animated.spring(pressAnimation, {
        toValue: 0.94,
        tension: 25,
        useNativeDriver: true,
      }),
      Animated.spring(wiggleAnimation, {
        toValue: 1.05,
        tension: 15,
        useNativeDriver: true,
      }),
    ]).start();
  };
  
  const handlePressOut = () => {
    Animated.parallel([
      Animated.spring(pressAnimation, {
        toValue: 1,
        tension: 25,
        useNativeDriver: true,
      }),
      Animated.spring(wiggleAnimation, {
        toValue: 1,
        tension: 15,
        useNativeDriver: true,
      }),
    ]).start();
  };
  
  return (
    <Animated.View
      style={[
        styles.lessonCardWrapper,
        {
          opacity: cardAnimation,
          transform: [
            {
              translateY: cardAnimation.interpolate({
                inputRange: [0, 1],
                outputRange: [40, 0],
              }),
            },
            {
              scale: cardAnimation.interpolate({
                inputRange: [0, 1],
                outputRange: [0.85, 1],
              }),
            },
            {
              rotate: wiggleAnimation.interpolate({
                inputRange: [0, 1],
                outputRange: ['0deg', '360deg'], // Full spin on entrance!
              }),
            },
          ],
        },
      ]}
    >
      <Animated.View
        style={{
          transform: [{ scale: pressAnimation }],
        }}
      >
        <LinearGradient
          colors={[lesson.color, `${lesson.color}EE`, lesson.color]} // More dynamic gradient
          style={styles.lessonCardGradient}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
        >
          <TouchableOpacity
            style={styles.lessonCardTouchable}
            onPress={onPress}
            onPressIn={handlePressIn}
            onPressOut={handlePressOut}
            activeOpacity={0.85}
          >
            <View style={styles.lessonCardContent}>
              <Animated.View
                style={[
                  styles.lessonIconContainer,
                  {
                    transform: [{ scale: pulseAnimation || 1 }],
                  },
                ]}
              >
                <Text style={styles.lessonIcon}>{lesson.icon} ✨</Text>
              </Animated.View>
              <Text style={styles.lessonCardTitle}>{lesson.topic} 🎯</Text>
              <Text style={styles.lessonDifficulty}>{lesson.difficulty} Level</Text>
              <View style={styles.lessonReward}>
                <Text style={styles.lessonRewardText}>✨ {lesson.xpReward} XP ✨</Text>
              </View>
              {lesson.completed && (
                <View style={styles.completedBadge}>
                  <Text style={styles.completedBadgeText}>👑</Text>
                </View>
              )}
            </View>
          </TouchableOpacity>
        </LinearGradient>
      </Animated.View>
    </Animated.View>
  );
};

// GraphQL Queries and Mutations
const GET_TUTOR_PROGRESS = gql`
  query GetTutorProgress {
    tutorProgress {
      userId
      xp
      level
      streakDays
      badges
      abilityEstimate
      skillMastery {
        skill
        masteryLevel
        masteryPercentage
        status
      }
      hearts
      maxHearts
    }
  }
`;

const START_QUEST = gql`
  mutation StartQuest($difficulty: String!) {
    startQuest(difficulty: $difficulty) {
      id
      topic
      difficulty
      rewards {
        type
        amount
      }
      progress
      narration
      expiresAt
      questType
      timeLimitMinutes
      scenarios {
        id
        description
        type
        marketCondition
        expectedOutcome
      }
    }
  }
`;

const UPDATE_QUEST_PROGRESS = gql`
  mutation UpdateQuestProgress($questId: String!, $progress: Float!, $completedScenarios: Int!) {
    updateQuestProgress(questId: $questId, progress: $progress, completedScenarios: $completedScenarios) {
      questId
      progress
      completed
      rewardsEarned
      message
      nextQuestAvailable
      streakBonus
    }
  }
`;

const START_LESSON = gql`
  mutation StartLesson($topic: String!, $regime: String) {
    startLesson(topic: $topic, regime: $regime) {
      id
      title
      text
      voiceNarration
      quiz {
        id
        question
        options
        correct
        explanation
        voiceHint
      }
      xpEarned
      streak
      difficulty
      estimatedTimeMinutes
      skillsTargeted
    }
  }
`;

const SUBMIT_QUIZ = gql`
  mutation SubmitQuiz($lessonId: ID!, $answers: [Int!]!) {
    submitQuiz(lessonId: $lessonId, answers: $answers) {
      score
      xpBonus
      totalXp
      feedback
      badgesEarned
      nextRecommendation
      streakStatus
      levelProgress {
        currentLevel
        currentXp
        nextLevelXp
        progressPercentage
      }
    }
  }
`;

const GET_DAILY_QUEST = gql`
  query GetDailyQuest {
    dailyQuest {
      id
      title
      description
      questType
      difficulty
      xpReward
      timeLimitMinutes
      requiredSkills
      regimeContext
      voiceNarration
      completionCriteria {
        scenariosCompleted
        successRate
      }
    }
  }
`;

const START_LIVE_SIM = gql`
  mutation StartLiveSim($symbol: String!, $mode: String!) {
    startLiveSim(symbol: $symbol, mode: $mode) {
      id
      symbol
      mode
      initialBalance
      currentBalance
      learningObjectives
      voiceFeedbackEnabled
      regimeContext
      performanceMetrics {
        totalTrades
        winRate
        totalPnL
        returnPercentage
      }
    }
  }
`;

interface TutorScreenProps {
  navigation: any;
}

const TutorScreen: React.FC<TutorScreenProps> = ({ navigation }) => {
  // State management
  const [currentLesson, setCurrentLesson] = useState<any>(null);
  const [currentQuiz, setCurrentQuiz] = useState<any[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<number[]>([]);
  const [isListening, setIsListening] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [quizResults, setQuizResults] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'learn' | 'quest' | 'sim' | 'progress' | 'memequest'>('learn');
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [showConfetti, setShowConfetti] = useState(false);
  
  // Enhanced learning state
  const [currentStep, setCurrentStep] = useState(0);
  const [learningSteps, setLearningSteps] = useState<any[]>([]);
  const [showStepQuiz, setShowStepQuiz] = useState(false);
  const [stepQuizAnswer, setStepQuizAnswer] = useState<number | null>(null);
  
  // Quest state
  const [currentQuest, setCurrentQuest] = useState<any>(null);
  const [questProgress, setQuestProgress] = useState(0);
  const [questCompleted, setQuestCompleted] = useState(false);
  
  // Animations
  const progressAnimation = useRef(new Animated.Value(0)).current;
  const streakAnimation = useRef(new Animated.Value(0)).current;
  const xpAnimation = useRef(new Animated.Value(0)).current;
  const pulseAnimation = useRef(new Animated.Value(1)).current;
  
  // Voice context
  const { speak, parseCommand, isVoiceEnabled } = useVoice();
  
  // Voice helper function
  const speakWithToggle = (text: string, options?: any) => {
    if (voiceEnabled) {
      Speech.speak(text, options);
    }
  };
  
  // GraphQL hooks
  const { data: progressData, loading: progressLoading, refetch: refetchProgress } = useQuery(GET_TUTOR_PROGRESS);
  const { data: questData, loading: questLoading } = useQuery(GET_DAILY_QUEST);
  
  // Fallback mock data for when GraphQL queries fail
  const mockProgress = {
    tutorProgress: {
      userId: "demo-user-123",
      xp: 1250,
      level: 3,
      streakDays: 7,
      badges: ["First Steps", "Quiz Master", "Streak Keeper"],
      abilityEstimate: 0.75,
      skillMastery: [
        {
          skill: "options_trading",
          masteryLevel: "intermediate",
          masteryPercentage: 65,
          status: "learning",
          __typename: "SkillMastery"
        }
      ],
      hearts: 3,
      maxHearts: 5,
      __typename: "TutorProgress"
    }
  };
  
  const mockQuest = {
    dailyQuest: {
      id: "quest_001",
      title: "Options Spread Mastery",
      description: "Complete 3 options spread scenarios with 80% accuracy",
      questType: "simulation",
      difficulty: 3,
      xpReward: 150,
      timeLimitMinutes: 15,
      requiredSkills: ["options_trading", "risk_management"],
      regimeContext: "bull_market",
      voiceNarration: "Welcome to today's quest! You'll practice options spreads in a bull market scenario.",
      completionCriteria: {
        scenariosCompleted: 0,
        successRate: 0.0,
        __typename: "CompletionCriteria"
      },
      __typename: "DailyQuest"
    }
  };
  const [startLesson] = useMutation(START_LESSON);
  const [submitQuiz] = useMutation(SUBMIT_QUIZ);
  const [startLiveSim] = useMutation(START_LIVE_SIM);
  
  // Quest mutations
  const [startQuest] = useMutation(START_QUEST, {
    onCompleted: (data) => {
      console.log('StartQuest mutation completed:', data);
      if (data?.startQuest) {
        setCurrentQuest(data.startQuest);
        setQuestProgress(0);
        setQuestCompleted(false);
        
        // Voice narration for quest start
        speakWithToggle(data.startQuest.narration);
        
        // Haptic feedback
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        
        // Switch to quest tab
        setActiveTab('quest');
      }
    },
    onError: (error) => {
      console.error('Quest start failed:', error);
      Alert.alert('Quest Error', 'Failed to start quest. Please try again.');
    }
  });
  
  const [updateQuestProgress] = useMutation(UPDATE_QUEST_PROGRESS, {
    onCompleted: (data) => {
      if (data?.updateQuestProgress) {
        setQuestProgress(data.updateQuestProgress.progress);
        if (data.updateQuestProgress.completed) {
          setQuestCompleted(true);
          speakWithToggle(data.updateQuestProgress.message);
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        }
      }
    }
  });

  const progress = progressData?.tutorProgress || mockProgress.tutorProgress;
  const dailyQuest = questData?.dailyQuest || mockQuest.dailyQuest;

  useEffect(() => {
    if (progress) {
      // Animate progress bars
      Animated.timing(progressAnimation, {
        toValue: progress.level / 10,
        duration: 1000,
        useNativeDriver: false,
      }).start();
      
      Animated.timing(streakAnimation, {
        toValue: progress.streakDays / 30,
        duration: 1000,
        useNativeDriver: false,
      }).start();
      
      // Start pulse animation for voice button
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnimation, {
            toValue: 1.1,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnimation, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      ).start();
    }
  }, [progress]);

  const handleVoiceCommand = async (transcript: string) => {
    const command = parseCommand(transcript);
    
    switch (command.intent) {
      case 'start_lesson':
        await startNewLesson(command.topic || 'options');
        break;
      case 'submit_answer':
        if (currentQuiz.length > 0) {
          handleAnswerSubmit();
        }
        break;
      case 'next_question':
        handleNextQuestion();
        break;
      case 'repeat_question':
        speakCurrentQuestion();
        break;
      case 'explain_answer':
        explainCurrentAnswer();
        break;
      default:
        speakWithToggle("I didn't understand that command. Try saying 'start lesson' or 'next question'.");
    }
  };

  const createLearningSteps = (lesson: any) => {
    const steps = [];
    const text = lesson?.text || '';
    
    console.log('Creating learning steps for lesson:', lesson?.title);
    console.log('Lesson text length:', text?.length);
    console.log('Lesson text preview:', text?.substring(0, 200));
    console.log('Full lesson text:', text);
    
    // Ensure text is a string
    if (typeof text !== 'string') {
      console.log('WARNING: Lesson text is not a string:', typeof text);
      return [{
        type: 'explanation',
        title: 'Lesson Content',
        content: 'Loading lesson content...',
        icon: '📚',
        color: '#2196F3'
      }];
    }
    
    // Check if we're getting the right content
    if (!text || text.includes('Welcome to crypto basics! This comprehensive lesson covers all essential concepts')) {
      console.log('WARNING: Received generic welcome message instead of actual lesson content!');
      console.log('Full lesson object:', JSON.stringify(lesson, null, 2));
    }
    
    // Split text into paragraphs - try multiple methods
    let paragraphs = [];
    
    // First try splitting by double newlines
    if (text.includes('\n\n')) {
      paragraphs = text.split('\n\n').filter(p => p.trim());
    } 
    // Then try splitting by single newlines
    else if (text.includes('\n')) {
      paragraphs = text.split('\n').filter(p => p.trim());
    }
    // If no newlines, split by periods and create steps
    else {
      const sentences = text.split('.').filter(s => s.trim());
      paragraphs = sentences.map(s => s.trim() + '.');
    }
    
    console.log('Parsed paragraphs:', paragraphs);
    
    // If no paragraphs found, create a single step with the full text
    if (paragraphs.length === 0) {
      steps.push({
        type: 'explanation',
        title: 'Lesson Content',
        content: text || 'Loading lesson content...',
        icon: '📚',
        color: '#2196F3'
      });
    } else {
      paragraphs.forEach((paragraph, index) => {
        // Ensure paragraph is a string
        const safeParagraph = typeof paragraph === 'string' ? paragraph : 'Loading content...';
        
        // Create concept cards for key terms
        if (safeParagraph.includes('**') || safeParagraph.includes('⭐')) {
          steps.push({
            type: 'concept',
            title: `Key Concept ${index + 1}`,
            content: String(safeParagraph.replace(/\*\*(.*?)\*\*/g, '⭐$1⭐')),
            icon: '💡',
            color: '#FF9800'
          });
        } else if (safeParagraph.includes('Example') || safeParagraph.includes('example')) {
          steps.push({
            type: 'example',
            title: `Real Example ${index + 1}`,
            content: String(safeParagraph),
            icon: '📊',
            color: '#4CAF50'
          });
        } else {
          steps.push({
            type: 'explanation',
            title: `Step ${index + 1}`,
            content: String(safeParagraph),
            icon: '📚',
            color: '#2196F3'
          });
        }
      });
    }
    
    // Add interactive quiz steps
    if (lesson.quiz && Array.isArray(lesson.quiz) && lesson.quiz.length > 0) {
      lesson.quiz.forEach((quiz: any, index: number) => {
        steps.push({
          type: 'quiz',
          title: `Quick Check ${index + 1}`,
          question: String(typeof quiz.question === 'string' ? quiz.question : 'Loading question...'),
          options: Array.isArray(quiz.options) ? quiz.options.map(opt => String(opt)) : ['Loading options...'],
          correct: typeof quiz.correct === 'number' ? quiz.correct : 0,
          explanation: String(typeof quiz.explanation === 'string' ? quiz.explanation : 'Loading explanation...'),
          icon: '❓',
          color: '#9C27B0'
        });
      });
    }
    
    console.log('Created steps:', steps);
    return steps;
  };

  const startNewLesson = async (topic: string) => {
    try {
      console.log('Starting lesson with topic:', topic);
      console.log('API endpoint:', process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000');
      
      const { data } = await startLesson({
        variables: { topic, regime: 'BULL' }
      });
      
      console.log('Received lesson data:', data?.startLesson?.title);
      console.log('Lesson text preview:', data?.startLesson?.text?.substring(0, 100));
      
      if (data?.startLesson) {
        setCurrentLesson(data.startLesson);
        setCurrentQuiz(data.startLesson.quiz);
        setCurrentQuestionIndex(0);
        setSelectedAnswers([]);
        setShowResults(false);
        setShowConfetti(true); // Trigger confetti burst
        
        // Create interactive learning steps
        const steps = createLearningSteps(data.startLesson);
        setLearningSteps(steps);
        setCurrentStep(0);
        setShowStepQuiz(false);
        setStepQuizAnswer(null);
        
        // Playful voice with enthusiasm
        speakWithToggle(`Yay! Let's dive into ${topic}!`, { 
          rate: 0.9, // Slightly slower for emphasis
          voice: data.startLesson.voiceNarration 
        });
        
        // Multi-haptic burst for excitement
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        setTimeout(() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy), 200);
        
        // Animate XP gain
        Animated.timing(xpAnimation, {
          toValue: data.startLesson.xpEarned / 100,
          duration: 1500,
          useNativeDriver: false,
        }).start();
        
        setTimeout(() => setShowConfetti(false), 3000);
      }
    } catch (error) {
      console.error('Error starting lesson:', error);
      Alert.alert('Oops! 😅', 'Lesson start fizzled. Try again for bonus XP!');
    }
  };

  const handleStepQuizAnswer = (answerIndex: number) => {
    setStepQuizAnswer(answerIndex);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    
    const currentStepData = learningSteps?.[currentStep];
    if (currentStepData && answerIndex === currentStepData.correct) {
      speakWithToggle("Correct! 🎉 Great job!", { rate: 0.8 });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } else {
      speakWithToggle("Not quite! Let's try again! 💪", { rate: 0.8 });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    }
  };

  const nextStep = () => {
    if (currentStep < (learningSteps?.length || 0) - 1) {
      setCurrentStep(currentStep + 1);
      setShowStepQuiz(false);
      setStepQuizAnswer(null);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    } else {
      // Lesson completed
      setShowResults(true);
      speakWithToggle("Amazing! You've completed the lesson! 🏆", { rate: 0.8 });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    }
  };

  const previousStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
      setShowStepQuiz(false);
      setStepQuizAnswer(null);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
  };

  const renderLearningStep = () => {
    console.log('Rendering learning step:', currentStep, 'of', learningSteps?.length || 0);
    console.log('Learning steps:', learningSteps);
    
    if (!learningSteps?.[currentStep]) {
      console.log('No step found at index:', currentStep);
      return (
        <View style={styles.learningStepContainer}>
          <Text style={styles.stepContentText}>
            No learning content available. Please try again.
          </Text>
        </View>
      );
    }
    
    const step = learningSteps?.[currentStep];
    console.log('Current step:', step);
    
    // Safety check - ensure step has required properties
    if (!step || !step.icon || !step.title || !step.color) {
      console.log('Step missing required properties');
      return (
        <View style={styles.learningStepContainer}>
          <Text style={styles.stepContentText}>
            Invalid learning step. Please try again.
          </Text>
        </View>
      );
    }
    
    return (
      <View style={styles.learningStepContainer}>
        {/* Step Header */}
        <View style={styles.stepHeader}>
          <SafeText style={styles.stepIcon}>{step.icon}</SafeText>
          <SafeText style={styles.stepTitle}>{step.title}</SafeText>
          <SafeText style={styles.stepCounter}>
            {(currentStep || 0) + 1} of {learningSteps?.length || 0}
          </SafeText>
        </View>
        
        {/* Step Content */}
        <View style={[
          styles.stepContent, 
          { backgroundColor: `${step.color}20` }
        ]}>
          {step.type === 'quiz' ? (
            <View style={styles.stepQuizContainer}>
              <Text style={styles.stepQuizQuestion}>{step.question && typeof step.question === 'string' ? step.question : 'No question available'}</Text>
              <View style={styles.stepQuizOptions}>
                {step.options && Array.isArray(step.options) && step.options.map((option: string, index: number) => (
                  <TouchableOpacity
                    key={index}
                    style={[
                      styles.stepQuizOption,
                      stepQuizAnswer === index && styles.stepQuizOptionSelected
                    ]}
                    onPress={() => handleStepQuizAnswer(index)}
                  >
                    <Text style={styles.stepQuizOptionText}>{option && typeof option === 'string' ? option : 'No option'}</Text>
                  </TouchableOpacity>
                ))}
              </View>
              {stepQuizAnswer !== null && (
                <View style={styles.stepQuizExplanation}>
                  <Text style={styles.stepQuizExplanationText}>
                    {stepQuizAnswer === step.correct ? '✅ Correct!' : '❌ Try again!'}
                  </Text>
                  <Text style={styles.stepQuizExplanationDetail}>
                    {step.explanation && typeof step.explanation === 'string' ? step.explanation : 'No explanation available'}
                  </Text>
                </View>
              )}
            </View>
          ) : (
            <ScrollView style={styles.stepContentScroll} showsVerticalScrollIndicator={false}>
              <Text style={styles.stepContentText}>
                {step.content && typeof step.content === 'string' ? step.content
                  .replace(/\n\n/g, '\n\n') // Preserve paragraph breaks
                  .replace(/\n/g, '\n') // Preserve line breaks
                  .replace(/•/g, '• ') // Add space after bullet points
                  .replace(/⭐/g, ' ⭐ ') // Add spaces around stars
                  : 'Loading content...'}
              </Text>
            </ScrollView>
          )}
        </View>
        
        {/* Step Navigation */}
        <View style={styles.stepNavigation}>
          <TouchableOpacity
            style={[styles.stepNavButton, currentStep === 0 && styles.stepNavButtonDisabled]}
            onPress={previousStep}
            disabled={currentStep === 0}
          >
            <Text style={styles.stepNavButtonText}>← Previous</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.stepNavButton}
            onPress={nextStep}
          >
            <Text style={styles.stepNavButtonText}>
              {currentStep === (learningSteps?.length || 0) - 1 ? 'Finish 🎉' : 'Next →'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  const handleAnswerSelect = (answerIndex: number) => {
    const newAnswers = [...selectedAnswers];
    newAnswers[currentQuestionIndex] = answerIndex;
    setSelectedAnswers(newAnswers);
    
    // Haptic feedback
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    
    // Voice feedback
    speakWithToggle(`Selected option ${String.fromCharCode(65 + answerIndex)}`);
  };

  const handleNextQuestion = () => {
    if (currentQuestionIndex < currentQuiz.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      speakCurrentQuestion();
    } else {
      handleAnswerSubmit();
    }
  };

  const speakCurrentQuestion = () => {
    if (currentQuiz[currentQuestionIndex]) {
      const question = currentQuiz[currentQuestionIndex];
      const options = question.options.map((opt: string, index: number) => 
        `${String.fromCharCode(65 + index)}: ${opt}`
      ).join('. ');
      
      speakWithToggle(`${question.question}. ${options}`, {
        voice: question.voiceHint || 'Nova'
      });
    }
  };

  const explainCurrentAnswer = () => {
    if (currentQuiz[currentQuestionIndex]) {
      const question = currentQuiz[currentQuestionIndex];
      speakWithToggle(question.explanation, { voice: question.voiceHint || 'Nova' });
    }
  };

  // Quest completion handler - now presents actual trading scenarios
  const completeQuestScenario = () => {
    if (currentQuest) {
      const scenarioNumber = Math.floor(questProgress * 4) + 1;
      const scenarios = [
        {
          title: "📈 Crypto Trading Challenge",
          description: "You have $1,000 to invest. Bitcoin is at $45,000. Recent news suggests institutional adoption is increasing. What do you do?",
          options: [
            "Invest all $1,000 in Bitcoin now",
            "Invest $500 in Bitcoin, keep $500 for other opportunities", 
            "Wait for a dip below $40,000",
            "Invest in Ethereum instead at $3,000"
          ],
          correct: 1,
          explanation: "Diversification is key! Investing half now and keeping half for opportunities reduces risk while maintaining exposure to potential gains.",
          xpReward: 25
        },
        {
          title: "📊 Stock Market Decision",
          description: "Apple stock drops 5% after missing earnings expectations. You own 10 shares at $150 each. The company has strong fundamentals but short-term concerns. What's your move?",
          options: [
            "Sell immediately to cut losses",
            "Hold and wait for recovery",
            "Buy more shares at the lower price",
            "Set a stop-loss at $140"
          ],
          correct: 1,
          explanation: "Strong fundamentals suggest this is temporary. Holding allows you to benefit from the company's long-term value creation.",
          xpReward: 25
        },
        {
          title: "⚡ Risk Management Test",
          description: "Your portfolio is up 15% this month. You're considering taking profits or letting it ride. Your risk tolerance is moderate. What's your strategy?",
          options: [
            "Sell everything and take profits",
            "Sell 30% to lock in some gains",
            "Hold everything for more gains",
            "Rebalance to original allocation"
          ],
          correct: 3,
          explanation: "Rebalancing maintains your target risk level while locking in some gains. This prevents overexposure to recent winners.",
          xpReward: 25
        },
        {
          title: "🎯 Portfolio Diversification",
          description: "You have $5,000 to invest across different asset classes. Current allocation: 60% stocks, 30% bonds, 10% crypto. How would you allocate new funds?",
          options: [
            "Put it all in stocks for growth",
            "Maintain current proportions",
            "Increase crypto allocation to 20%",
            "Add international stocks (20%)"
          ],
          correct: 3,
          explanation: "Adding international exposure improves diversification and reduces concentration risk in domestic markets.",
          xpReward: 25
        }
      ];

      const currentScenario = scenarios[scenarioNumber - 1];
      
      if (currentScenario) {
        // Show scenario modal/dialog
        Alert.alert(
          currentScenario.title,
          currentScenario.description,
          [
            {
              text: currentScenario.options[0],
              onPress: () => handleScenarioAnswer(0, currentScenario, scenarioNumber)
            },
            {
              text: currentScenario.options[1], 
              onPress: () => handleScenarioAnswer(1, currentScenario, scenarioNumber)
            },
            {
              text: currentScenario.options[2],
              onPress: () => handleScenarioAnswer(2, currentScenario, scenarioNumber)
            },
            {
              text: currentScenario.options[3],
              onPress: () => handleScenarioAnswer(3, currentScenario, scenarioNumber)
            }
          ]
        );
      }
    }
  };

  const handleScenarioAnswer = (answerIndex: number, scenario: any, scenarioNumber: number) => {
    const isCorrect = answerIndex === scenario.correct;
    const newProgress = Math.min(questProgress + 0.25, 1.0);
    
    // Show feedback
    Alert.alert(
      isCorrect ? "🎉 Correct!" : "❌ Not quite right",
      scenario.explanation,
      [
        {
          text: "Continue",
          onPress: () => {
            // Update quest progress
            updateQuestProgress({ 
              variables: { 
                questId: currentQuest.id, 
                progress: newProgress,
                completedScenarios: scenarioNumber
              } 
            });
            
            // Add XP for correct answers
            if (isCorrect) {
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
              speakWithToggle(`Great job! You earned ${scenario.xpReward} XP for that correct answer!`);
            } else {
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
              speakWithToggle("Good try! Remember this lesson for next time.");
            }
            
            // Check if quest is complete
            if (newProgress >= 1.0) {
              setTimeout(() => {
                Alert.alert(
                  "🏆 Quest Complete!",
                  `Congratulations! You've completed the ${currentQuest.difficulty} quest and earned bonus rewards!`,
                  [
                    {
                      text: "Claim Rewards",
                      onPress: () => {
                        setQuestCompleted(true);
                        speakWithToggle("Fantastic work! You've mastered the trading scenarios!");
                      }
                    }
                  ]
                );
              }, 1000);
            }
          }
        }
      ]
    );
  };

  const handleAnswerSubmit = async () => {
    if (!currentLesson || selectedAnswers.length === 0) return;
    
    try {
      const { data } = await submitQuiz({
        variables: {
          lessonId: currentLesson.id,
          answers: selectedAnswers
        }
      });
      
      if (data?.submitQuiz) {
        setQuizResults(data.submitQuiz);
        setShowResults(true);
        
        // Voice feedback
        speakWithToggle(data.submitQuiz.feedback, { voice: 'Shimmer' });
        
        // Haptic feedback
        if (data.submitQuiz.score >= 80) {
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        } else {
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
        }
        
        // Refetch progress
        refetchProgress();
      }
    } catch (error) {
      console.error('Error submitting quiz:', error);
      Alert.alert('Error', 'Failed to submit quiz. Please try again.');
    }
  };

  const startSimulation = async (symbol: string) => {
    console.log('Starting live simulation for symbol:', symbol);
    try {
      const { data } = await startLiveSim({
        variables: { symbol, mode: 'paper' }
      });
      
      console.log('Live simulation data received:', data);
      
      if (data?.startLiveSim) {
        console.log('Navigating to trading screen with simulation data');
        // Navigate to trading screen with simulation data
        navigation.navigate('trading', { 
          simulationMode: true,
          session: data.startLiveSim 
        });
      }
    } catch (error) {
      console.error('Error starting simulation:', error);
      Alert.alert('Error', 'Failed to start simulation. Please try again.');
    }
  };

  const renderProgressSection = () => (
    <View style={styles.progressSection}>
      <Text style={styles.sectionTitle}>Your Learning Progress</Text>
      
      <View style={styles.progressCard}>
        <View style={styles.progressRow}>
          <Text style={styles.progressLabel}>Level {progress?.level || 1}</Text>
          <Text style={styles.progressValue}>{progress?.xp || 0} XP</Text>
        </View>
        
        <View style={styles.progressBarContainer}>
          <Animated.View 
            style={[
              styles.progressBar, 
              { width: '75%' }
            ]} 
          />
        </View>
        
        <View style={styles.streakRow}>
          <Text style={styles.streakLabel}>🔥 {progress?.streakDays || 0} Day Streak</Text>
          <Animated.View 
            style={[
              styles.streakBar, 
              { width: '80%' }
            ]} 
          />
        </View>
        
        <View style={styles.badgesContainer}>
          {progress?.badges?.slice(0, 3).map((badge: string, index: number) => (
            <View key={index} style={styles.badge}>
              <Text style={styles.badgeText}>{badge}</Text>
            </View>
          ))}
        </View>
      </View>
    </View>
  );

  const renderLearningSection = () => (
    <View style={styles.learningSection}>
      {/* Super vibrant header gradient with playful text */}
      <LinearGradient
        colors={['#58CC02', '#45A049', '#2E7D32']} // Duolingo green with depth
        style={styles.learningHeaderGradient}
      >
        <View style={styles.topBar}>
          <View style={styles.xpContainer}>
            <Text style={styles.xpText}>🚀 {progress.xp} XP Gems!</Text>
            <View style={styles.xpBar}>
              <Animated.View 
                style={[
                  styles.xpFill, 
                  { 
                    width: '60%',
                  }
                ]} 
              />
            </View>
          </View>
          
          <View style={styles.heartsContainer}>
            {Array.from({ length: progress.maxHearts }, (_, i) => (
              <Animated.View key={i}>
                <Text style={[
                  styles.heart,
                  i < progress.hearts && { color: '#FF4757' } // Red for full hearts
                ]}>
                  {i < progress.hearts ? '💖' : '💔'} {/* More playful hearts */}
                </Text>
              </Animated.View>
            ))}
          </View>
          
          <View style={styles.streakContainer}>
            <Text style={styles.streakText}>🔥 {progress.streakDays} Day Fire!</Text>
          </View>
        </View>
      </LinearGradient>

      {/* Daily Goal with playful animation */}
      <Animated.View style={[styles.dailyGoalContainer, { opacity: 1 }]}>
        <Text style={styles.dailyGoalText}>🎉 Daily Quest: Crush 3 Lessons! 🎉</Text>
        <View style={styles.dailyGoalBar}>
          <Animated.View 
            style={[
              styles.dailyGoalFill, 
              { width: '60%' } // Animate this on progress
            ]} 
          />
        </View>
        <TouchableOpacity style={styles.dailyGoalButton}>
          <Text style={styles.dailyGoalButtonText}>Buy Freeze? ❄️ (1 Gem)</Text>
        </TouchableOpacity>
      </Animated.View>

      <Text style={styles.sectionTitle}>Ready to Level Up? 🌈 Choose Your Adventure!</Text>
      
      {!currentLesson ? (
        <View style={styles.lessonSelection}>
          <ScrollView style={styles.lessonCardsScroll} showsVerticalScrollIndicator={false}>
            <View style={styles.lessonCards}>
              {[
                { 
                  topic: 'Stock Basics', 
                  icon: '📈', 
                  difficulty: 'Beginner',
                  xpReward: 40,
                  color: '#58CC02',
                  completed: false
                },
                { 
                  topic: 'Crypto Basics', 
                  icon: '₿', 
                  difficulty: 'Beginner',
                  xpReward: 60,
                  color: '#58CC02',
                  completed: false
                },
                { 
                  topic: 'Options Basics', 
                  icon: '📊', 
                  difficulty: 'Intermediate',
                  xpReward: 50,
                  color: '#FF9800',
                  completed: false
                },
                { 
                  topic: 'Volatility Trading', 
                  icon: '⚡', 
                  difficulty: 'Intermediate',
                  xpReward: 75,
                  color: '#FF9800',
                  completed: false
                },
                { 
                  topic: 'Risk Management', 
                  icon: '🛡️', 
                  difficulty: 'Advanced',
                  xpReward: 80,
                  color: '#F44336',
                  completed: false
                },
                { 
                  topic: 'Crypto Strategies', 
                  icon: '🔗', 
                  difficulty: 'Advanced',
                  xpReward: 90,
                  color: '#F44336',
                  completed: false
                },
                { 
                  topic: 'Technical Analysis', 
                  icon: '📉', 
                  difficulty: 'Advanced',
                  xpReward: 85,
                  color: '#F44336',
                  completed: false
                },
                { 
                  topic: 'Fundamental Analysis', 
                  icon: '📋', 
                  difficulty: 'Expert',
                  xpReward: 95,
                  color: '#9C27B0',
                  completed: false
                },
                { 
                  topic: 'Portfolio Management', 
                  icon: '💼', 
                  difficulty: 'Expert',
                  xpReward: 100,
                  color: '#9C27B0',
                  completed: false
                }
              ].map((lesson, index) => (
                <LessonCard
                  key={index}
                  lesson={lesson}
                  index={index}
                  onPress={() => {
                    console.log('🚀 Starting playful lesson:', lesson.topic);
                    startNewLesson(lesson.topic.toLowerCase());
                  }}
                />
              ))}
            </View>
          </ScrollView>
          
          {/* Floating voice orb - super playful */}
          <TouchableOpacity
            style={styles.voiceButton}
            onPress={() => {
              setIsListening(!isListening);
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Light);
            }}
          >
            <LinearGradient
              colors={['#FF6B6B', '#FF8E8E', '#FFB3B3']} // Playful pink gradient
              style={styles.voiceButtonGradient}
            >
              <Text style={styles.voiceButtonText}>
                {isListening ? '🎤 Magic Words!' : '🪄 Say a Spell!'}
              </Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={styles.lessonContainer}>
          {/* Playful back button */}
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
              setCurrentLesson(null);
              setCurrentQuiz([]);
              setCurrentQuestionIndex(0);
              setSelectedAnswers([]);
              setShowResults(false);
              setQuizResults(null);
            }}
          >
            <Text style={styles.backButtonIcon}>✨</Text>
            <Text style={styles.backButtonText}>Back to the Fun! 🎈</Text>
          </TouchableOpacity>
          
          <Text style={styles.lessonTitle}>🎊 {currentLesson.title} 🎊</Text>
          
          {/* Interactive Learning Steps */}
          {renderLearningStep()}
          
          {currentQuiz.length > 0 && !showResults && (
            <View style={styles.quizContainer}>
              {/* Progress Indicator */}
              <View style={styles.quizProgress}>
                <Text style={styles.quizProgressText}>
                  Question {currentQuestionIndex + 1} of {currentQuiz.length} ✨
                </Text>
                <View style={styles.quizProgressBar}>
                  <View style={[styles.quizProgressFill, { width: `${((currentQuestionIndex + 1) / currentQuiz.length) * 100}%` }]} />
                </View>
              </View>

              {/* Question */}
              <View style={styles.questionCard}>
                <Text style={styles.questionText}>
                  {currentQuiz[currentQuestionIndex]?.question}
                </Text>
              </View>
              
              {/* Answer Options */}
              <View style={styles.optionsContainer}>
                {currentQuiz[currentQuestionIndex]?.options.map((option: string, index: number) => (
                  <TouchableOpacity
                    key={index}
                    style={[
                      styles.optionButton,
                      selectedAnswers[currentQuestionIndex] === index && styles.selectedOption
                    ]}
                    onPress={() => {
                      handleAnswerSelect(index);
                      // Haptic feedback
                      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
                    }}
                  >
                    <View style={styles.optionContent}>
                      <Text style={styles.optionLetter}>
                        {String.fromCharCode(65 + index)}
                      </Text>
                      <Text style={styles.optionText}>{option}</Text>
                    </View>
                  </TouchableOpacity>
                ))}
              </View>
              
              {/* Quiz Controls */}
              <View style={styles.quizControls}>
                <TouchableOpacity
                  style={styles.controlButton}
                  onPress={speakCurrentQuestion}
                >
                  <Text style={styles.controlButtonText}>🔊 Repeat</Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={styles.controlButton}
                  onPress={explainCurrentAnswer}
                >
                  <Text style={styles.controlButtonText}>💡 Explain</Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={[
                    styles.controlButton, 
                    styles.primaryButton,
                    selectedAnswers[currentQuestionIndex] === undefined && styles.disabledButton
                  ]}
                  onPress={handleNextQuestion}
                  disabled={selectedAnswers[currentQuestionIndex] === undefined}
                >
                  <Text style={styles.primaryButtonText}>
                    {currentQuestionIndex < currentQuiz.length - 1 ? 'Next →' : 'Submit Quiz'}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
          
          {showResults && quizResults && (
            <View style={styles.resultsContainer}>
              {/* Celebration Animation */}
              <View style={styles.celebrationContainer}>
                <Text style={styles.celebrationEmoji}>
                  {quizResults.score >= 80 ? '🎉' : quizResults.score >= 60 ? '👍' : '💪'}
                </Text>
                <Text style={styles.resultsTitle}>
                  {quizResults.score >= 80 ? 'Excellent!' : quizResults.score >= 60 ? 'Good Job!' : 'Keep Learning!'}
                </Text>
              </View>

              {/* Score Display */}
              <View style={styles.scoreContainer}>
                <Text style={styles.scoreText}>{quizResults.score}%</Text>
                <Text style={styles.scoreLabel}>Correct</Text>
              </View>

              {/* XP Earned */}
              <View style={styles.xpEarnedContainer}>
                <Text style={styles.xpEarnedText}>+{quizResults.xpBonus} XP Earned!</Text>
                <Text style={styles.totalXpText}>Total: {quizResults.totalXp} XP</Text>
              </View>

              {/* Feedback */}
              <View style={styles.feedbackContainer}>
                <Text style={styles.feedbackText}>{quizResults.feedback}</Text>
              </View>
              
              {/* New Badges */}
              {quizResults.badgesEarned && quizResults.badgesEarned.length > 0 && (
                <View style={styles.newBadgesContainer}>
                  <Text style={styles.newBadgesTitle}>🏆 New Achievements!</Text>
                  {quizResults.badgesEarned.map((badge: string, index: number) => (
                    <View key={index} style={styles.badgeItem}>
                      <Text style={styles.badgeEmoji}>🏆</Text>
                      <Text style={styles.badgeText}>{badge}</Text>
                    </View>
                  ))}
                </View>
              )}
              
              {/* Action Buttons */}
              <View style={styles.resultsActions}>
                <TouchableOpacity
                  style={styles.continueButton}
                  onPress={() => {
                    setCurrentLesson(null);
                    setShowResults(false);
                    setQuizResults(null);
                    // Haptic feedback
                    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
                  }}
                >
                  <Text style={styles.continueButtonText}>🎯 Continue Learning</Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={styles.retryButton}
                  onPress={() => {
                    setShowResults(false);
                    setQuizResults(null);
                    setCurrentQuestionIndex(0);
                    setSelectedAnswers([]);
                  }}
                >
                  <Text style={styles.retryButtonText}>🔄 Try Again</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
        </View>
      )}

      {/* Enhanced Confetti - More particles, playful colors */}
      {showConfetti && (
        <SimpleConfetti visible={showConfetti} />
      )}
    </View>
  );

  const renderQuestSection = () => (
    <View style={styles.questSection}>
      <Text style={styles.sectionTitle}>Active Quest</Text>
      
      {currentQuest ? (
        <LinearGradient
          colors={['#667eea', '#764ba2']}
          style={styles.questCard}
        >
          <Text style={styles.questTitle}>{currentQuest.topic}</Text>
          <Text style={styles.questDescription}>{currentQuest.narration}</Text>
          
          <View style={styles.questStats}>
            <View style={styles.questStat}>
              <Text style={styles.questStatLabel}>Difficulty</Text>
              <Text style={styles.questStatValue}>{currentQuest.difficulty}</Text>
            </View>
            <View style={styles.questStat}>
              <Text style={styles.questStatLabel}>Progress</Text>
              <Text style={styles.questStatValue}>{Math.round(questProgress * 100)}%</Text>
            </View>
            <View style={styles.questStat}>
              <Text style={styles.questStatLabel}>Time Limit</Text>
              <Text style={styles.questStatValue}>{currentQuest.timeLimitMinutes}m</Text>
            </View>
          </View>
          
          <View style={styles.questProgressBar}>
            <View style={[styles.questProgressFill, { width: `${questProgress * 100}%` }]} />
          </View>
          
          <Text style={styles.questRewards}>
            Rewards: {currentQuest.rewards?.map(r => `${r.amount} ${r.type}`).join(', ')}
          </Text>
          
          <View style={styles.questScenarios}>
            <Text style={styles.questScenariosTitle}>Trading Scenarios:</Text>
            {currentQuest.scenarios?.map((scenario: any, index: number) => (
              <View key={index} style={styles.scenarioItem}>
                <Text style={styles.scenarioTitle}>
                  {index + 1}. {scenario.title}
                </Text>
                <Text style={styles.scenarioDescription}>
                  {scenario.description}
                </Text>
                <Text style={styles.scenarioReward}>
                  +{scenario.xpReward} XP
                </Text>
              </View>
            ))}
          </View>
          
          {questCompleted ? (
            <TouchableOpacity
              style={styles.completedQuestButton}
              onPress={() => {
                setCurrentQuest(null);
                setQuestProgress(0);
                setQuestCompleted(false);
                setActiveTab('learn');
              }}
            >
              <Text style={styles.completedQuestButtonText}>Quest Completed! 🎉</Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              style={styles.continueQuestButton}
              onPress={() => completeQuestScenario()}
            >
              <Text style={styles.continueQuestButtonText}>
                Start Scenario {Math.floor(questProgress * 4) + 1} 🚀
              </Text>
            </TouchableOpacity>
          )}
        </LinearGradient>
      ) : (
        <View style={styles.noQuestContainer}>
          <Text style={styles.noQuestText}>No active quest</Text>
          <TouchableOpacity
            style={styles.startNewQuestButton}
            onPress={() => {
              console.log('Start Quest button pressed!');
              // Determine difficulty based on user level
              const difficulty = progress.level >= 5 ? 'HARD' : progress.level >= 3 ? 'MEDIUM' : 'EASY';
              console.log('Starting quest with difficulty:', difficulty);
              console.log('Progress level:', progress.level);
              startQuest({ variables: { difficulty } });
            }}
          >
            <Text style={styles.startNewQuestButtonText}>Start New Quest</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );

  const renderSimulationSection = () => (
    <View style={styles.simulationSection}>
      <Text style={styles.sectionTitle}>Live Market Simulation</Text>
      
      <View style={styles.simCardsContainer}>
        {['AAPL', 'TSLA', 'NVDA', 'MSFT'].map((symbol, index) => (
          <TouchableOpacity
            key={index}
            style={styles.simCard}
            onPress={() => {
              console.log('Live simulation button pressed for:', symbol);
              startSimulation(symbol);
            }}
          >
            <Text style={styles.simSymbol}>{symbol}</Text>
            <Text style={styles.simDescription}>Paper Trading</Text>
            <Text style={styles.simStatus}>Ready to Start</Text>
          </TouchableOpacity>
        ))}
      </View>
      
      <Text style={styles.simInstruction}>
        Practice trading with real market data in a safe environment
      </Text>
    </View>
  );

  if (progressLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#667eea" />
        <Text style={styles.loadingText}>Loading your learning progress...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <View style={styles.headerText}>
            <Text style={styles.headerTitle}>AI Tutor</Text>
            <Text style={styles.headerSubtitle}>Adaptive Learning</Text>
          </View>
          <TouchableOpacity
            style={[styles.voiceToggle, voiceEnabled && styles.voiceToggleActive]}
            onPress={() => setVoiceEnabled(!voiceEnabled)}
          >
            <Text style={styles.voiceToggleIcon}>
              {voiceEnabled ? '🔊' : '🔇'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
      
      <View style={styles.tabContainer}>
        {[
          { key: 'learn', label: 'Learn', icon: '📚' },
          { key: 'quest', label: 'Quest', icon: '🎯' },
          { key: 'sim', label: 'Sim', icon: '📈' },
          { key: 'progress', label: 'Progress', icon: '📊' },
          { key: 'memequest', label: 'MemeQuest', icon: '🔥' }
        ].map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[styles.tab, activeTab === tab.key && styles.activeTab]}
            onPress={() => setActiveTab(tab.key as any)}
          >
            <Text style={styles.tabIcon}>{tab.icon}</Text>
            <Text style={[styles.tabLabel, activeTab === tab.key && styles.activeTabLabel]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
      
      {activeTab === 'learn' && renderLearningSection()}
      {activeTab === 'quest' && renderQuestSection()}
      {activeTab === 'sim' && renderSimulationSection()}
      {activeTab === 'progress' && renderProgressSection()}
      {activeTab === 'memequest' && <MemeQuestScreen />}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    padding: 20,
    backgroundColor: '#667eea',
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerText: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: 'white',
    textAlign: 'center',
  },
  headerSubtitle: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.8)',
    textAlign: 'center',
    marginTop: 5,
  },
  voiceToggle: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255,255,255,0.3)',
  },
  voiceToggleActive: {
    backgroundColor: 'rgba(255,255,255,0.3)',
    borderColor: 'rgba(255,255,255,0.5)',
  },
  voiceToggleIcon: {
    fontSize: 24,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: 'white',
    marginHorizontal: 20,
    marginTop: -10,
    borderRadius: 15,
    padding: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    flexWrap: 'wrap',
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 4,
    borderRadius: 10,
    minWidth: 60,
  },
  activeTab: {
    backgroundColor: '#667eea',
  },
  tabIcon: {
    fontSize: 20,
    marginBottom: 5,
  },
  tabLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: '#666',
    textAlign: 'center',
  },
  activeTabLabel: {
    color: 'white',
  },
  sectionTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1CB0F6',
    textAlign: 'center',
    marginVertical: 20,
    marginHorizontal: 20,
  },
  learningSection: {
    paddingVertical: 20,
    backgroundColor: '#F7F9FC',
  },
  lessonSelection: {
    marginHorizontal: 20,
  },
  instructionText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  topicButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  topicButton: {
    width: '48%',
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  topicButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    textAlign: 'center',
  },
  voiceButton: {
    backgroundColor: '#667eea',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  voiceButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
  lessonContainer: {
    marginHorizontal: 20,
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1CB0F6',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 20,
    marginBottom: 20,
    alignSelf: 'flex-start',
    marginHorizontal: 20,
  },
  backButtonIcon: {
    fontSize: 18,
    color: 'white',
    marginRight: 6,
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
  lessonTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  lessonText: {
    fontSize: 16,
    color: '#666',
    lineHeight: 24,
    marginBottom: 20,
  },
  quizContainer: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  questionText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 20,
    lineHeight: 26,
  },
  optionsContainer: {
    marginBottom: 20,
  },
  optionButton: {
    backgroundColor: '#f8f9fa',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  selectedOption: {
    borderColor: '#667eea',
    backgroundColor: '#e8f0fe',
  },
  optionText: {
    fontSize: 16,
    color: '#333',
  },
  quizControls: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  controlButton: {
    backgroundColor: '#f8f9fa',
    paddingHorizontal: 15,
    paddingVertical: 10,
    borderRadius: 8,
    flex: 1,
    marginHorizontal: 5,
    alignItems: 'center',
  },
  primaryButton: {
    backgroundColor: '#667eea',
  },
  controlButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  primaryButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: 'white',
  },
  resultsContainer: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  resultsTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
    marginBottom: 15,
  },
  scoreText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#667eea',
    textAlign: 'center',
    marginBottom: 10,
  },
  feedbackText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 15,
    lineHeight: 24,
  },
  newBadgesContainer: {
    backgroundColor: '#fff3cd',
    padding: 15,
    borderRadius: 10,
    marginBottom: 15,
  },
  newBadgesTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#856404',
    marginBottom: 10,
  },
  newBadge: {
    fontSize: 14,
    color: '#856404',
    marginBottom: 5,
  },
  continueButton: {
    backgroundColor: '#667eea',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  continueButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
  questSection: {
    paddingVertical: 20,
  },
  questCard: {
    marginHorizontal: 20,
    padding: 20,
    borderRadius: 15,
  },
  questTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 10,
  },
  questDescription: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.9)',
    marginBottom: 20,
    lineHeight: 24,
  },
  questStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  questStat: {
    alignItems: 'center',
  },
  questStatLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.7)',
    marginBottom: 5,
  },
  questStatValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'white',
  },
  startQuestButton: {
    backgroundColor: '#667eea',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 10,
    borderWidth: 2,
    borderColor: '#fff',
  },
  startQuestButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
  questProgressBar: {
    height: 8,
    backgroundColor: 'rgba(255,255,255,0.3)',
    borderRadius: 4,
    marginVertical: 10,
    overflow: 'hidden',
  },
  questProgressFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
    borderRadius: 4,
  },
  questRewards: {
    fontSize: 14,
    color: 'white',
    textAlign: 'center',
    marginVertical: 10,
  },
  questScenarios: {
    marginTop: 15,
    padding: 10,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 8
  },
  questScenariosTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 10
  },
  scenarioItem: {
    marginBottom: 12,
    padding: 8,
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 6
  },
  scenarioTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4
  },
  scenarioDescription: {
    fontSize: 12,
    color: '#E0E0E0',
    marginBottom: 4,
    lineHeight: 16
  },
  scenarioReward: {
    fontSize: 12,
    color: '#FFD700',
    fontWeight: 'bold'
  },
  continueQuestButton: {
    backgroundColor: '#4CAF50',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 10,
  },
  continueQuestButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
  completedQuestButton: {
    backgroundColor: '#FF9800',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 10,
  },
  completedQuestButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
  noQuestContainer: {
    alignItems: 'center',
    padding: 20,
  },
  noQuestText: {
    fontSize: 18,
    color: '#666',
    marginBottom: 20,
  },
  startNewQuestButton: {
    backgroundColor: '#667eea',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  startNewQuestButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
  simulationSection: {
    paddingVertical: 20,
  },
  simCardsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginHorizontal: 20,
    marginBottom: 15,
  },
  simCard: {
    width: '48%',
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  simSymbol: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  simDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  simStatus: {
    fontSize: 12,
    color: '#28a745',
    fontWeight: '600',
  },
  simInstruction: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginHorizontal: 20,
    fontStyle: 'italic',
  },
  progressSection: {
    paddingVertical: 20,
  },
  progressCard: {
    backgroundColor: 'white',
    marginHorizontal: 20,
    padding: 20,
    borderRadius: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  progressRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  progressLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  progressValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#667eea',
  },
  progressBarContainer: {
    height: 8,
    backgroundColor: '#e9ecef',
    borderRadius: 4,
    marginBottom: 15,
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#667eea',
    borderRadius: 4,
  },
  streakRow: {
    marginBottom: 15,
  },
  streakLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 5,
  },
  streakBar: {
    height: 6,
    backgroundColor: '#ff6b6b',
    borderRadius: 3,
  },
  badgesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  badge: {
    backgroundColor: '#667eea',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 15,
    marginRight: 10,
    marginBottom: 10,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: 'white',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    marginTop: 10,
  },
  
  // Duolingo-style Learning Header
  learningHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#f8f9fa',
    borderRadius: 15,
    marginBottom: 20,
  },
  xpContainer: {
    alignItems: 'center',
  },
  xpBar: {
    height: 6,
    backgroundColor: '#e0e0e0',
    borderRadius: 3,
    overflow: 'hidden',
  },
  xpFill: {
    height: '100%',
    backgroundColor: '#FF6B35',
    borderRadius: 3,
  },
  heartsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  heart: {
    fontSize: 20,
    marginHorizontal: 2,
  },
  streakContainer: {
    alignItems: 'center',
  },
  streakText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FF6B35',
  },
  
  // Duolingo-style Lesson Cards
  lessonCards: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  lessonCardWrapper: {
    width: '48%',
    marginBottom: 15,
  },
  lessonCard: {
    width: '100%',
    height: 120,
    borderRadius: 16,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    marginBottom: 15,
    justifyContent: 'center',
    alignItems: 'center',
  },
  lessonCardContent: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 15,
  },
  lessonIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  lessonCardTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: 'white',
    textAlign: 'center',
    marginBottom: 6,
  },
  lessonDifficulty: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginBottom: 10,
  },
  lessonReward: {
    backgroundColor: 'rgba(255,255,255,0.25)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    minWidth: 40,
    alignItems: 'center',
  },
  lessonRewardText: {
    fontSize: 11,
    fontWeight: 'bold',
    color: 'white',
  },
  completedBadge: {
    position: 'absolute',
    top: 10,
    right: 10,
    fontSize: 20,
    color: 'white',
    backgroundColor: 'rgba(0,0,0,0.3)',
    borderRadius: 15,
    width: 30,
    height: 30,
    textAlign: 'center',
    lineHeight: 30,
  },
  
  // Enhanced Quiz Styles
  quizProgress: {
    marginBottom: 20,
  },
  quizProgressText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 10,
  },
  quizProgressBar: {
    height: 8,
    backgroundColor: '#e0e0e0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  quizProgressFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
    borderRadius: 4,
  },
  questionCard: {
    backgroundColor: '#f8f9fa',
    padding: 20,
    borderRadius: 15,
    marginBottom: 20,
    borderLeftWidth: 4,
    borderLeftColor: '#4CAF50',
  },
  optionContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  optionLetter: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#4CAF50',
    marginRight: 15,
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#f0f0f0',
    textAlign: 'center',
    lineHeight: 30,
  },
  disabledButton: {
    opacity: 0.5,
  },
  
  // Enhanced Results Styles
  celebrationContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  celebrationEmoji: {
    fontSize: 60,
    marginBottom: 10,
  },
  scoreContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  scoreLabel: {
    fontSize: 16,
    color: '#666',
    marginTop: 5,
  },
  xpEarnedContainer: {
    backgroundColor: '#e8f5e8',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 20,
  },
  xpEarnedText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  totalXpText: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  feedbackContainer: {
    backgroundColor: '#f8f9fa',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
  },
  badgeItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  badgeEmoji: {
    fontSize: 20,
    marginRight: 10,
  },
  resultsActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  retryButton: {
    backgroundColor: '#FF9800',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    flex: 0.48,
  },
  retryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
  
  // Ultra-Playful Styles - Bolder colors, more rounded, emoji-friendly
  learningSection: {
    flex: 1,
    backgroundColor: '#FFF0F5', // Soft pink tint for playfulness
  },
  learningHeaderGradient: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderRadius: 24,
    marginHorizontal: 20,
    marginBottom: 24,
    elevation: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  xpText: {
    fontSize: 18,
    fontWeight: '800',
    color: 'white',
    textShadowColor: 'rgba(0,0,0,0.2)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
    marginBottom: 8,
  },
  xpBar: {
    height: 6,
    backgroundColor: 'rgba(255,255,255,0.3)',
    borderRadius: 3,
    overflow: 'hidden',
    width: '100%',
  },
  xpFill: {
    height: '100%',
    backgroundColor: '#FFD700',
    borderRadius: 3,
  },
  heartsContainer: {
    flexDirection: 'row',
  },
  heart: {
    fontSize: 24,
    marginHorizontal: 2,
  },
  streakContainer: {
    alignItems: 'center',
  },
  streakText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: 'white',
    textShadowColor: 'rgba(0,0,0,0.2)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  dailyGoalContainer: {
    backgroundColor: 'white',
    marginHorizontal: 20,
    padding: 20,
    borderRadius: 20,
    marginBottom: 24,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    borderWidth: 1,
    borderColor: 'rgba(88, 204, 2, 0.2)',
  },
  dailyGoalText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#333',
    textAlign: 'center',
    marginBottom: 16,
  },
  dailyGoalBar: {
    height: 8,
    backgroundColor: '#E8F5E8',
    borderRadius: 4,
    marginBottom: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#58CC02',
  },
  dailyGoalFill: {
    height: '100%',
    backgroundColor: '#58CC02',
    borderRadius: 3,
  },
  dailyGoalButton: {
    backgroundColor: '#FFF3CD',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#FFC107',
  },
  dailyGoalButtonText: {
    fontSize: 14,
    color: '#856404',
    fontWeight: '600',
  },
  sectionTitle: {
    fontSize: 26,
    fontWeight: '800',
    color: '#1A73E8',
    textAlign: 'center',
    marginVertical: 24,
    marginHorizontal: 20,
    textShadowColor: 'rgba(0,0,0,0.1)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  lessonCardsScroll: {
    maxHeight: height * 0.55,
  },
  lessonCardWrapper: {
    width: '48%',
    marginBottom: 18,
  },
  lessonCardGradient: {
    borderRadius: 24,
    elevation: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
  },
  lessonCardTouchable: {
    flex: 1,
    borderRadius: 24,
    overflow: 'hidden',
  },
  lessonCardContent: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 18,
  },
  lessonIconContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255,255,255,0.25)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 14,
    borderWidth: 2,
    borderColor: 'rgba(255,255,255,0.4)',
  },
  lessonIcon: {
    fontSize: 30,
    color: 'white',
  },
  lessonCardTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: 'white',
    textAlign: 'center',
    marginBottom: 6,
    lineHeight: 18,
  },
  lessonDifficulty: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.9)',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 14,
    fontWeight: '600',
  },
  lessonReward: {
    backgroundColor: 'rgba(255,255,255,0.3)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2,
  },
  lessonRewardText: {
    fontSize: 13,
    fontWeight: 'bold',
    color: 'white',
  },
  completedBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(255,215,0,0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 4,
  },
  completedBadgeText: {
    fontSize: 18,
    color: 'white',
  },
  voiceButton: {
    position: 'absolute',
    bottom: 30,
    left: 20,
    right: 20,
    zIndex: 10,
  },
  voiceButtonGradient: {
    paddingVertical: 16,
    paddingHorizontal: 28,
    borderRadius: 28,
    alignItems: 'center',
    elevation: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
  },
  voiceButtonText: {
    fontSize: 17,
    fontWeight: '700',
    color: 'white',
  },
  lessonTextScroll: {
    maxHeight: 200,
    marginBottom: 20,
  },
  lessonText: {
    fontSize: 16,
    color: '#666',
    lineHeight: 24,
  },
  boldText: {
    fontSize: 16,
    color: '#333',
    fontWeight: 'bold',
    lineHeight: 24,
  },
  normalText: {
    fontSize: 16,
    color: '#666',
    lineHeight: 24,
  },
  confettiContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 1000,
    pointerEvents: 'none',
  },
  confettiPiece: {
    position: 'absolute',
    top: -50,
  },
  confettiEmoji: {
    fontSize: 24,
    textAlign: 'center',
  },
  
  // Learning Step Styles
  learningStepContainer: {
    flex: 1,
    padding: 20,
  },
  stepHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: 'rgba(255,255,255,0.95)',
    borderRadius: 16,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
  },
  stepIcon: {
    fontSize: 26,
    marginRight: 14,
  },
  stepTitle: {
    fontSize: 19,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
  },
  stepCounter: {
    fontSize: 14,
    color: '#666',
    fontWeight: '600',
  },
  stepContent: {
    flex: 1,
    padding: 24,
    borderRadius: 16,
    marginBottom: 20,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  stepContentText: {
    fontSize: 16,
    lineHeight: 26,
    color: '#333',
    paddingHorizontal: 4,
  },
  stepContentScroll: {
    maxHeight: 300,
    paddingHorizontal: 8,
  },
  stepQuizContainer: {
    flex: 1,
  },
  stepQuizQuestion: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
    textAlign: 'center',
  },
  stepQuizOptions: {
    marginBottom: 20,
  },
  stepQuizOption: {
    backgroundColor: 'rgba(255,255,255,0.8)',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  stepQuizOptionSelected: {
    borderColor: '#4CAF50',
    backgroundColor: 'rgba(76,175,80,0.1)',
  },
  stepQuizOptionText: {
    fontSize: 16,
    color: '#333',
    textAlign: 'center',
  },
  stepQuizExplanation: {
    backgroundColor: 'rgba(255,255,255,0.9)',
    padding: 16,
    borderRadius: 12,
    marginTop: 10,
  },
  stepQuizExplanationText: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  stepQuizExplanationDetail: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  stepNavigation: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
  },
  stepNavButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 25,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
  },
  stepNavButtonDisabled: {
    backgroundColor: '#ccc',
  },
  stepNavButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default TutorScreen;

