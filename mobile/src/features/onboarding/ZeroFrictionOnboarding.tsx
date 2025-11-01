import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
  TouchableOpacity,
  Image,
  Alert,
  Platform,
  ScrollView,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { LinearGradient } from 'expo-linear-gradient';
import { PanGestureHandler, State } from 'react-native-gesture-handler';

const { width, height } = Dimensions.get('window');

interface ZeroFrictionOnboardingProps {
  onComplete: (profile: any) => void;
  onSkip: () => void;
}

export default function ZeroFrictionOnboarding({ onComplete, onSkip }: ZeroFrictionOnboardingProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [wealthProfile, setWealthProfile] = useState<any>({});
  const [loading, setLoading] = useState(false);
  
  // Animation values
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(width)).current;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;

  const steps = [
    {
      id: 'welcome',
      title: 'Welcome to Your Wealth Journey',
      subtitle: 'Let\'s get you set up in 60 seconds',
      component: WelcomeStep,
    },
    {
      id: 'kyc',
      title: 'Quick Identity Verification',
      subtitle: 'Snap a photo of your ID - we\'ll handle the rest',
      component: KYCStep,
    },
    {
      id: 'wealth_quiz',
      title: 'Your Wealth Personality',
      subtitle: 'Tell us about your goals - we\'ll personalize everything',
      component: WealthQuizStep,
    },
    {
      id: 'portfolio_preview',
      title: 'Your AI-Curated Portfolio',
      subtitle: 'Based on your profile, here\'s your personalized starter',
      component: PortfolioPreviewStep,
    },
  ];

  useEffect(() => {
    // Start entrance animation
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  useEffect(() => {
    // Update progress animation
    Animated.timing(progressAnim, {
      toValue: (currentStep + 1) / steps.length,
      duration: 300,
      useNativeDriver: false,
    }).start();
  }, [currentStep]);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = async () => {
    setLoading(true);
    try {
      // Simulate AI processing
      await new Promise(resolve => setTimeout(resolve, 2000));
      onComplete(wealthProfile);
    } catch (error) {
      Alert.alert('Error', 'Failed to complete onboarding');
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = (updates: any) => {
    setWealthProfile(prev => ({ ...prev, ...updates }));
  };

  const CurrentStepComponent = steps[currentStep].component;

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#667eea" />
        <Text style={styles.loadingText}>Setting up your personalized experience...</Text>
      </View>
    );
  }

  return (
    <Animated.View
      style={[
        styles.container,
        {
          opacity: fadeAnim,
          transform: [{ translateX: slideAnim }, { scale: scaleAnim }],
        },
      ]}
    >
      {/* Progress Bar */}
      <View style={styles.progressContainer}>
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
        <Text style={styles.progressText}>
          {currentStep + 1} of {steps.length}
        </Text>
      </View>

      {/* Step Content */}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.stepContainer}>
          <Text style={styles.title}>{steps[currentStep].title}</Text>
          <Text style={styles.subtitle}>{steps[currentStep].subtitle}</Text>
          
          <CurrentStepComponent
            profile={wealthProfile}
            updateProfile={updateProfile}
            onNext={handleNext}
            onBack={handleBack}
            hasPermission={hasPermission}
            setHasPermission={setHasPermission}
            isScanning={isScanning}
            setIsScanning={setIsScanning}
          />
        </View>
      </ScrollView>

      {/* Navigation */}
      <View style={styles.navigation}>
        {currentStep > 0 && (
          <TouchableOpacity style={styles.backButton} onPress={handleBack}>
            <Text style={styles.backButtonText}>Back</Text>
          </TouchableOpacity>
        )}
        
        <TouchableOpacity style={styles.skipButton} onPress={onSkip}>
          <Text style={styles.skipButtonText}>Skip</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.nextButton} onPress={handleNext}>
          <LinearGradient
            colors={['#667eea', '#764ba2']}
            style={styles.nextButtonGradient}
          >
            <Text style={styles.nextButtonText}>
              {currentStep === steps.length - 1 ? 'Complete' : 'Next'}
            </Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>
    </Animated.View>
  );
}

// Welcome Step Component
function WelcomeStep({ onNext }: any) {
  return (
    <View style={styles.stepContent}>
      <View style={styles.welcomeIcon}>
        <Text style={styles.welcomeEmoji}>🚀</Text>
      </View>
      
      <Text style={styles.welcomeTitle}>Ready to Build Wealth?</Text>
      <Text style={styles.welcomeDescription}>
        Our AI will analyze your goals, risk tolerance, and preferences to create a personalized investment strategy just for you.
      </Text>
      
      <View style={styles.featuresList}>
        <View style={styles.featureItem}>
          <Text style={styles.featureIcon}>⚡</Text>
          <Text style={styles.featureText}>60-second setup</Text>
        </View>
        <View style={styles.featureItem}>
          <Text style={styles.featureIcon}>🤖</Text>
          <Text style={styles.featureText}>AI-powered insights</Text>
        </View>
        <View style={styles.featureItem}>
          <Text style={styles.featureIcon}>🎯</Text>
          <Text style={styles.featureText}>Personalized portfolio</Text>
        </View>
      </View>
    </View>
  );
}

// KYC Step Component
function KYCStep({ profile, updateProfile, hasPermission, setHasPermission, isScanning, setIsScanning }: any) {
  const [idImage, setIdImage] = useState<string | null>(null);

  const requestCameraPermission = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    setHasPermission(status === 'granted');
    return status === 'granted';
  };

  const takePicture = async () => {
    const hasPermission = await requestCameraPermission();
    if (!hasPermission) {
      Alert.alert('Permission Required', 'Camera permission is needed to scan your ID');
      return;
    }

    setIsScanning(true);
    try {
      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: 'images',
        allowsEditing: true,
        aspect: [16, 10],
        quality: 0.8,
      });

      if (!result.canceled && result.assets[0]) {
        setIdImage(result.assets[0].uri);
        // Simulate AI processing
        setTimeout(() => {
          updateProfile({
            firstName: 'John',
            lastName: 'Doe',
            dob: '1990-01-01',
            address: '123 Main St',
            city: 'New York',
            state: 'NY',
            zip: '10001',
          });
          setIsScanning(false);
        }, 2000);
      }
    } catch (error: any) {
      console.error('Camera error:', error);
      Alert.alert(
        'Error', 
        error?.message || 'Failed to take picture. Please check camera permissions and try again.'
      );
      setIsScanning(false);
    } finally {
      if (!idImage) {
        setIsScanning(false);
      }
    }
  };

  return (
    <View style={styles.stepContent}>
      <View style={styles.kycContainer}>
        <Text style={styles.kycTitle}>Scan Your ID</Text>
        <Text style={styles.kycDescription}>
          We'll automatically extract your information for faster setup
        </Text>
        
        {idImage ? (
          <View style={styles.idPreview}>
            <Image source={{ uri: idImage }} style={styles.idImage} />
            <Text style={styles.idStatus}>✅ ID scanned successfully</Text>
          </View>
        ) : (
          <TouchableOpacity
            style={[styles.scanButton, isScanning && styles.scanButtonDisabled]}
            onPress={takePicture}
            disabled={isScanning}
          >
            <LinearGradient
              colors={['#667eea', '#764ba2']}
              style={styles.scanButtonGradient}
            >
              {isScanning ? (
                <ActivityIndicator size="small" color="white" />
              ) : (
                <>
                  <Text style={styles.scanButtonIcon}>📷</Text>
                  <Text style={styles.scanButtonText}>Scan ID</Text>
                </>
              )}
            </LinearGradient>
          </TouchableOpacity>
        )}
        
        <TouchableOpacity style={styles.manualEntryButton}>
          <Text style={styles.manualEntryText}>Enter manually instead</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

// Wealth Quiz Step Component
function WealthQuizStep({ profile, updateProfile }: any) {
  const [answers, setAnswers] = useState({
    experience: '',
    goals: '',
    riskTolerance: '',
    timeframe: '',
    budget: '',
  });

  const questions = [
    {
      id: 'experience',
      question: 'What\'s your investment experience?',
      options: ['Beginner', 'Some experience', 'Experienced', 'Expert'],
    },
    {
      id: 'goals',
      question: 'What are your main goals?',
      options: ['Build wealth', 'Save for retirement', 'Generate income', 'Learn investing'],
    },
    {
      id: 'riskTolerance',
      question: 'How comfortable are you with risk?',
      options: ['Very conservative', 'Conservative', 'Moderate', 'Aggressive'],
    },
    {
      id: 'timeframe',
      question: 'What\'s your investment timeframe?',
      options: ['Less than 1 year', '1-3 years', '3-5 years', '5+ years'],
    },
    {
      id: 'budget',
      question: 'How much can you invest monthly?',
      options: ['$100-500', '$500-1000', '$1000-2500', '$2500+'],
    },
  ];

  const handleAnswer = (questionId: string, answer: string) => {
    const newAnswers = { ...answers, [questionId]: answer };
    setAnswers(newAnswers);
    updateProfile({ wealthQuiz: newAnswers });
  };

  return (
    <View style={styles.stepContent}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {questions.map((question) => (
          <View key={question.id} style={styles.questionContainer}>
            <Text style={styles.questionText}>{question.question}</Text>
            <View style={styles.optionsContainer}>
              {question.options.map((option) => (
                <TouchableOpacity
                  key={option}
                  style={[
                    styles.optionButton,
                    answers[question.id as keyof typeof answers] === option && styles.optionButtonSelected,
                  ]}
                  onPress={() => handleAnswer(question.id, option)}
                >
                  <Text
                    style={[
                      styles.optionText,
                      answers[question.id as keyof typeof answers] === option && styles.optionTextSelected,
                    ]}
                  >
                    {option}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

// Portfolio Preview Step Component
function PortfolioPreviewStep({ profile }: any) {
  const mockPortfolio = {
    totalValue: 10000,
    allocation: [
      { name: 'Stocks', percentage: 60, value: 6000, color: '#667eea' },
      { name: 'Bonds', percentage: 25, value: 2500, color: '#764ba2' },
      { name: 'Crypto', percentage: 10, value: 1000, color: '#f093fb' },
      { name: 'Cash', percentage: 5, value: 500, color: '#4facfe' },
    ],
    expectedReturn: 8.5,
    riskLevel: 'Moderate',
  };

  return (
    <View style={styles.stepContent}>
      <View style={styles.portfolioContainer}>
        <Text style={styles.portfolioTitle}>Your AI-Curated Portfolio</Text>
        <Text style={styles.portfolioDescription}>
          Based on your profile, here's your personalized investment strategy
        </Text>
        
        <View style={styles.portfolioValue}>
          <Text style={styles.portfolioValueLabel}>Starting Portfolio Value</Text>
          <Text style={styles.portfolioValueAmount}>${mockPortfolio.totalValue.toLocaleString()}</Text>
        </View>
        
        <View style={styles.allocationContainer}>
          {mockPortfolio.allocation.map((item, index) => (
            <View key={index} style={styles.allocationItem}>
              <View style={styles.allocationHeader}>
                <View style={[styles.allocationColor, { backgroundColor: item.color }]} />
                <Text style={styles.allocationName}>{item.name}</Text>
                <Text style={styles.allocationPercentage}>{item.percentage}%</Text>
              </View>
              <View style={styles.allocationBar}>
                <View
                  style={[
                    styles.allocationFill,
                    { width: `${item.percentage}%`, backgroundColor: item.color },
                  ]}
                />
              </View>
            </View>
          ))}
        </View>
        
        <View style={styles.portfolioMetrics}>
          <View style={styles.metricItem}>
            <Text style={styles.metricLabel}>Expected Return</Text>
            <Text style={styles.metricValue}>{mockPortfolio.expectedReturn}%</Text>
          </View>
          <View style={styles.metricItem}>
            <Text style={styles.metricLabel}>Risk Level</Text>
            <Text style={styles.metricValue}>{mockPortfolio.riskLevel}</Text>
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    marginTop: 20,
    textAlign: 'center',
  },
  progressContainer: {
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
  },
  progressBar: {
    height: 4,
    backgroundColor: '#e0e0e0',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#667eea',
    borderRadius: 2,
  },
  progressText: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    marginTop: 8,
  },
  content: {
    flex: 1,
  },
  stepContainer: {
    padding: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1a1a1a',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 40,
  },
  stepContent: {
    flex: 1,
  },
  navigation: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingBottom: 40,
  },
  backButton: {
    paddingVertical: 12,
    paddingHorizontal: 20,
  },
  backButtonText: {
    fontSize: 16,
    color: '#667eea',
    fontWeight: '600',
  },
  skipButton: {
    paddingVertical: 12,
    paddingHorizontal: 20,
  },
  skipButtonText: {
    fontSize: 16,
    color: '#666',
  },
  nextButton: {
    borderRadius: 25,
    overflow: 'hidden',
  },
  nextButtonGradient: {
    paddingVertical: 12,
    paddingHorizontal: 30,
  },
  nextButtonText: {
    fontSize: 16,
    color: 'white',
    fontWeight: '600',
  },
  // Welcome Step Styles
  welcomeIcon: {
    alignItems: 'center',
    marginBottom: 30,
  },
  welcomeEmoji: {
    fontSize: 80,
  },
  welcomeTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
    textAlign: 'center',
    marginBottom: 16,
  },
  welcomeDescription: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 40,
  },
  featuresList: {
    gap: 20,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  featureIcon: {
    fontSize: 24,
    marginRight: 16,
  },
  featureText: {
    fontSize: 16,
    color: '#1a1a1a',
    fontWeight: '500',
  },
  // KYC Step Styles
  kycContainer: {
    alignItems: 'center',
  },
  kycTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  kycDescription: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 40,
  },
  scanButton: {
    borderRadius: 20,
    overflow: 'hidden',
    marginBottom: 20,
  },
  scanButtonDisabled: {
    opacity: 0.6,
  },
  scanButtonGradient: {
    paddingVertical: 16,
    paddingHorizontal: 40,
    alignItems: 'center',
  },
  scanButtonIcon: {
    fontSize: 24,
    marginBottom: 8,
  },
  scanButtonText: {
    fontSize: 16,
    color: 'white',
    fontWeight: '600',
  },
  idPreview: {
    alignItems: 'center',
    marginBottom: 20,
  },
  idImage: {
    width: 200,
    height: 120,
    borderRadius: 12,
    marginBottom: 12,
  },
  idStatus: {
    fontSize: 14,
    color: '#34C759',
    fontWeight: '600',
  },
  manualEntryButton: {
    paddingVertical: 12,
  },
  manualEntryText: {
    fontSize: 14,
    color: '#667eea',
    textDecorationLine: 'underline',
  },
  // Quiz Step Styles
  questionContainer: {
    marginBottom: 30,
  },
  questionText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  optionsContainer: {
    gap: 12,
  },
  optionButton: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#e0e0e0',
  },
  optionButtonSelected: {
    borderColor: '#667eea',
    backgroundColor: '#f0f4ff',
  },
  optionText: {
    fontSize: 16,
    color: '#1a1a1a',
    textAlign: 'center',
  },
  optionTextSelected: {
    color: '#667eea',
    fontWeight: '600',
  },
  // Portfolio Step Styles
  portfolioContainer: {
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  portfolioTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
    textAlign: 'center',
    marginBottom: 8,
  },
  portfolioDescription: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
  },
  portfolioValue: {
    alignItems: 'center',
    marginBottom: 24,
  },
  portfolioValueLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  portfolioValueAmount: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  allocationContainer: {
    marginBottom: 24,
  },
  allocationItem: {
    marginBottom: 16,
  },
  allocationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  allocationColor: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  allocationName: {
    fontSize: 16,
    color: '#1a1a1a',
    flex: 1,
  },
  allocationPercentage: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  allocationBar: {
    height: 8,
    backgroundColor: '#f0f0f0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  allocationFill: {
    height: '100%',
    borderRadius: 4,
  },
  portfolioMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  metricItem: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
});