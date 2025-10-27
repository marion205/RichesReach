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
} from 'react-native';
import { useMutation, useQuery } from '@apollo/client';
import { gql } from '@apollo/client';
import * as Speech from 'expo-speech';
import * as Haptics from 'expo-haptics';
import { useVoice } from '../../../contexts/VoiceContext';
import { LinearGradient } from 'expo-linear-gradient';

const { width, height } = Dimensions.get('window');

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
  const [activeTab, setActiveTab] = useState<'learn' | 'quest' | 'sim' | 'progress'>('learn');
  
  // Animations
  const progressAnimation = useRef(new Animated.Value(0)).current;
  const streakAnimation = useRef(new Animated.Value(0)).current;
  const xpAnimation = useRef(new Animated.Value(0)).current;
  
  // Voice context
  const { speak, parseCommand, isVoiceEnabled } = useVoice();
  
  // GraphQL hooks
  const { data: progressData, loading: progressLoading, refetch: refetchProgress } = useQuery(GET_TUTOR_PROGRESS);
  const { data: questData, loading: questLoading } = useQuery(GET_DAILY_QUEST);
  const [startLesson] = useMutation(START_LESSON);
  const [submitQuiz] = useMutation(SUBMIT_QUIZ);
  const [startLiveSim] = useMutation(START_LIVE_SIM);

  const progress = progressData?.tutorProgress;
  const dailyQuest = questData?.dailyQuest;

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
        speak("I didn't understand that command. Try saying 'start lesson' or 'next question'.");
    }
  };

  const startNewLesson = async (topic: string) => {
    try {
      const { data } = await startLesson({
        variables: { topic, regime: 'BULL' }
      });
      
      if (data?.startLesson) {
        setCurrentLesson(data.startLesson);
        setCurrentQuiz(data.startLesson.quiz);
        setCurrentQuestionIndex(0);
        setSelectedAnswers([]);
        setShowResults(false);
        
        // Voice narration
        speak(data.startLesson.text, { voice: data.startLesson.voiceNarration });
        
        // Haptic feedback
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        
        // Animate XP gain
        Animated.timing(xpAnimation, {
          toValue: data.startLesson.xpEarned / 100,
          duration: 1500,
          useNativeDriver: false,
        }).start();
      }
    } catch (error) {
      console.error('Error starting lesson:', error);
      Alert.alert('Error', 'Failed to start lesson. Please try again.');
    }
  };

  const handleAnswerSelect = (answerIndex: number) => {
    const newAnswers = [...selectedAnswers];
    newAnswers[currentQuestionIndex] = answerIndex;
    setSelectedAnswers(newAnswers);
    
    // Haptic feedback
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    
    // Voice feedback
    speak(`Selected option ${String.fromCharCode(65 + answerIndex)}`);
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
      
      speak(`${question.question}. ${options}`, {
        voice: question.voiceHint || 'Nova'
      });
    }
  };

  const explainCurrentAnswer = () => {
    if (currentQuiz[currentQuestionIndex]) {
      const question = currentQuiz[currentQuestionIndex];
      speak(question.explanation, { voice: question.voiceHint || 'Nova' });
    }
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
        speak(data.submitQuiz.feedback, { voice: 'Shimmer' });
        
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
    try {
      const { data } = await startLiveSim({
        variables: { symbol, mode: 'paper' }
      });
      
      if (data?.startLiveSim) {
        navigation.navigate('SimulationScreen', { session: data.startLiveSim });
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
              { width: progressAnimation.interpolate({
                inputRange: [0, 1],
                outputRange: ['0%', '100%']
              })}
            ]} 
          />
        </View>
        
        <View style={styles.streakRow}>
          <Text style={styles.streakLabel}>🔥 {progress?.streakDays || 0} Day Streak</Text>
          <Animated.View 
            style={[
              styles.streakBar, 
              { width: streakAnimation.interpolate({
                inputRange: [0, 1],
                outputRange: ['0%', '100%']
              })}
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
      <Text style={styles.sectionTitle}>Interactive Learning</Text>
      
      {!currentLesson ? (
        <View style={styles.lessonSelection}>
          <Text style={styles.instructionText}>
            Choose a topic to start learning, or use voice commands:
          </Text>
          
          <View style={styles.topicButtons}>
            {['Options Basics', 'Volatility Trading', 'Risk Management', 'HFT Strategies'].map((topic, index) => (
              <TouchableOpacity
                key={index}
                style={styles.topicButton}
                onPress={() => startNewLesson(topic.toLowerCase())}
              >
                <Text style={styles.topicButtonText}>{topic}</Text>
              </TouchableOpacity>
            ))}
          </View>
          
          <TouchableOpacity
            style={styles.voiceButton}
            onPress={() => setIsListening(!isListening)}
          >
            <Text style={styles.voiceButtonText}>
              {isListening ? '🎤 Listening...' : '🎤 Voice Commands'}
            </Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={styles.lessonContainer}>
          <Text style={styles.lessonTitle}>{currentLesson.title}</Text>
          <Text style={styles.lessonText}>{currentLesson.text}</Text>
          
          {currentQuiz.length > 0 && !showResults && (
            <View style={styles.quizContainer}>
              <Text style={styles.questionText}>
                {currentQuiz[currentQuestionIndex]?.question}
              </Text>
              
              <View style={styles.optionsContainer}>
                {currentQuiz[currentQuestionIndex]?.options.map((option: string, index: number) => (
                  <TouchableOpacity
                    key={index}
                    style={[
                      styles.optionButton,
                      selectedAnswers[currentQuestionIndex] === index && styles.selectedOption
                    ]}
                    onPress={() => handleAnswerSelect(index)}
                  >
                    <Text style={styles.optionText}>
                      {String.fromCharCode(65 + index)}. {option}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
              
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
                  style={[styles.controlButton, styles.primaryButton]}
                  onPress={handleNextQuestion}
                >
                  <Text style={styles.primaryButtonText}>
                    {currentQuestionIndex < currentQuiz.length - 1 ? 'Next' : 'Submit'}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
          
          {showResults && quizResults && (
            <View style={styles.resultsContainer}>
              <Text style={styles.resultsTitle}>Quiz Results</Text>
              <Text style={styles.scoreText}>Score: {quizResults.score}%</Text>
              <Text style={styles.feedbackText}>{quizResults.feedback}</Text>
              
              {quizResults.badgesEarned.length > 0 && (
                <View style={styles.newBadgesContainer}>
                  <Text style={styles.newBadgesTitle}>New Badges!</Text>
                  {quizResults.badgesEarned.map((badge: string, index: number) => (
                    <Text key={index} style={styles.newBadge}>🏆 {badge}</Text>
                  ))}
                </View>
              )}
              
              <TouchableOpacity
                style={styles.continueButton}
                onPress={() => {
                  setCurrentLesson(null);
                  setShowResults(false);
                  setQuizResults(null);
                }}
              >
                <Text style={styles.continueButtonText}>Continue Learning</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      )}
    </View>
  );

  const renderQuestSection = () => (
    <View style={styles.questSection}>
      <Text style={styles.sectionTitle}>Daily Quest</Text>
      
      {dailyQuest ? (
        <LinearGradient
          colors={['#667eea', '#764ba2']}
          style={styles.questCard}
        >
          <Text style={styles.questTitle}>{dailyQuest.title}</Text>
          <Text style={styles.questDescription}>{dailyQuest.description}</Text>
          
          <View style={styles.questStats}>
            <View style={styles.questStat}>
              <Text style={styles.questStatLabel}>XP Reward</Text>
              <Text style={styles.questStatValue}>{dailyQuest.xpReward}</Text>
            </View>
            <View style={styles.questStat}>
              <Text style={styles.questStatLabel}>Difficulty</Text>
              <Text style={styles.questStatValue}>{dailyQuest.difficulty}/5</Text>
            </View>
            <View style={styles.questStat}>
              <Text style={styles.questStatLabel}>Time Limit</Text>
              <Text style={styles.questStatValue}>{dailyQuest.timeLimitMinutes}m</Text>
            </View>
          </View>
          
          <TouchableOpacity
            style={styles.startQuestButton}
            onPress={() => startNewLesson('daily quest')}
          >
            <Text style={styles.startQuestButtonText}>Start Quest</Text>
          </TouchableOpacity>
        </LinearGradient>
      ) : (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#667eea" />
          <Text style={styles.loadingText}>Loading daily quest...</Text>
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
            onPress={() => startSimulation(symbol)}
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
        <Text style={styles.headerTitle}>AI Tutor</Text>
        <Text style={styles.headerSubtitle}>Beat Fidelity with Adaptive Learning</Text>
      </View>
      
      <View style={styles.tabContainer}>
        {[
          { key: 'learn', label: 'Learn', icon: '📚' },
          { key: 'quest', label: 'Quest', icon: '🎯' },
          { key: 'sim', label: 'Sim', icon: '📈' },
          { key: 'progress', label: 'Progress', icon: '📊' }
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
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 10,
    borderRadius: 10,
  },
  activeTab: {
    backgroundColor: '#667eea',
  },
  tabIcon: {
    fontSize: 20,
    marginBottom: 5,
  },
  tabLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
  },
  activeTabLabel: {
    color: 'white',
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
    marginHorizontal: 20,
  },
  learningSection: {
    paddingVertical: 20,
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
    backgroundColor: 'rgba(255,255,255,0.2)',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  startQuestButtonText: {
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
});

export default TutorScreen;
