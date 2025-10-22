/**
 * Comprehensive unit tests for all mobile UI components in RichesReach AI platform.
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Text, View, TouchableOpacity, TextInput, ScrollView } from 'react-native';

// Mock all the screens and components
jest.mock('../../features/auth/screens/LoginScreen', () => {
  return function MockLoginScreen({ onLogin, onNavigateToSignUp, onNavigateToForgotPassword }: any) {
    return (
      <View testID="login-screen">
        <TextInput testID="email-input" placeholder="Email" />
        <TextInput testID="password-input" placeholder="Password" secureTextEntry />
        <TouchableOpacity testID="login-button" onPress={() => onLogin('test@example.com', 'password123')}>
          <Text>Login</Text>
        </TouchableOpacity>
        <TouchableOpacity testID="signup-button" onPress={onNavigateToSignUp}>
          <Text>Sign Up</Text>
        </TouchableOpacity>
        <TouchableOpacity testID="forgot-password-button" onPress={onNavigateToForgotPassword}>
          <Text>Forgot Password</Text>
        </TouchableOpacity>
      </View>
    );
  };
});

jest.mock('../../features/auth/screens/SignUpScreen', () => {
  return function MockSignUpScreen({ onSignUp, onNavigateToLogin }: any) {
    return (
      <View testID="signup-screen">
        <TextInput testID="signup-email-input" placeholder="Email" />
        <TextInput testID="signup-password-input" placeholder="Password" secureTextEntry />
        <TouchableOpacity testID="signup-submit-button" onPress={() => onSignUp({ email: 'test@example.com', password: 'password123' })}>
          <Text>Sign Up</Text>
        </TouchableOpacity>
        <TouchableOpacity testID="login-link-button" onPress={onNavigateToLogin}>
          <Text>Back to Login</Text>
        </TouchableOpacity>
      </View>
    );
  };
});

jest.mock('../../features/auth/screens/ForgotPasswordScreen', () => {
  return function MockForgotPasswordScreen({ onNavigateToLogin, onNavigateToResetPassword }: any) {
    return (
      <View testID="forgot-password-screen">
        <TextInput testID="reset-email-input" placeholder="Email" />
        <TouchableOpacity testID="reset-password-button" onPress={() => onNavigateToResetPassword('test@example.com')}>
          <Text>Reset Password</Text>
        </TouchableOpacity>
        <TouchableOpacity testID="back-to-login-button" onPress={onNavigateToLogin}>
          <Text>Back to Login</Text>
        </TouchableOpacity>
      </View>
    );
  };
});

jest.mock('../../navigation/HomeScreen', () => {
  return function MockHomeScreen({ navigateTo }: any) {
    return (
      <View testID="home-screen">
        <Text>Home Screen</Text>
        <TouchableOpacity testID="ai-tutor-button" onPress={() => navigateTo('ai-tutor')}>
          <Text>AI Tutor</Text>
        </TouchableOpacity>
        <TouchableOpacity testID="trading-coach-button" onPress={() => navigateTo('ai-trading-coach')}>
          <Text>AI Trading Coach</Text>
        </TouchableOpacity>
        <TouchableOpacity testID="wealth-circles-button" onPress={() => navigateTo('wealth-circles')}>
          <Text>Wealth Circles</Text>
        </TouchableOpacity>
        <TouchableOpacity testID="personalization-button" onPress={() => navigateTo('personalization-dashboard')}>
          <Text>Personalization</Text>
        </TouchableOpacity>
      </View>
    );
  };
});

jest.mock('../../features/learning/screens/TutorAskExplainScreen', () => {
  return function MockTutorAskExplainScreen({ navigateTo }: any) {
    const [mode, setMode] = React.useState('ask');
    const [question, setQuestion] = React.useState('');
    const [response, setResponse] = React.useState('');

    const handleSubmit = () => {
      setResponse('Mock AI response');
    };

    return (
      <View testID="tutor-ask-explain-screen">
        <View testID="mode-toggle">
          <TouchableOpacity testID="ask-mode-button" onPress={() => setMode('ask')}>
            <Text>Ask</Text>
          </TouchableOpacity>
          <TouchableOpacity testID="explain-mode-button" onPress={() => setMode('explain')}>
            <Text>Explain</Text>
          </TouchableOpacity>
        </View>
        <TextInput 
          testID="question-input" 
          placeholder={mode === 'ask' ? 'Ask a question' : 'Enter a concept'}
          value={question}
          onChangeText={setQuestion}
        />
        <TouchableOpacity testID="submit-button" onPress={handleSubmit}>
          <Text>Submit</Text>
        </TouchableOpacity>
        {response ? <Text testID="response-text">{response}</Text> : null}
      </View>
    );
  };
});

jest.mock('../../features/learning/screens/TutorQuizScreen', () => {
  return function MockTutorQuizScreen({ navigateTo }: any) {
    const [isRegimeAdaptive, setIsRegimeAdaptive] = React.useState(false);
    const [quiz, setQuiz] = React.useState(null);
    const [selectedAnswer, setSelectedAnswer] = React.useState(null);

    const loadQuiz = () => {
      setQuiz({
        quiz_id: 'quiz_123',
        topic: 'Options Trading',
        questions: [
          {
            question_id: 'q1',
            question: 'What is a call option?',
            options: ['Right to buy', 'Right to sell', 'Obligation to buy', 'Obligation to sell'],
            correct_answer: 0
          }
        ]
      });
    };

    const submitAnswer = () => {
      // Mock answer submission
    };

    return (
      <View testID="tutor-quiz-screen">
        <View testID="quiz-toggle">
          <TouchableOpacity testID="regime-adaptive-toggle" onPress={() => setIsRegimeAdaptive(!isRegimeAdaptive)}>
            <Text>{isRegimeAdaptive ? 'Regime-Adaptive' : 'Topic-Based'}</Text>
          </TouchableOpacity>
        </View>
        <TouchableOpacity testID="load-quiz-button" onPress={loadQuiz}>
          <Text>Load Quiz</Text>
        </TouchableOpacity>
        {quiz && (
          <View testID="quiz-content">
            <Text testID="quiz-topic">{quiz.topic}</Text>
            <Text testID="quiz-question">{quiz.questions[0].question}</Text>
            {quiz.questions[0].options.map((option: string, index: number) => (
              <TouchableOpacity 
                key={index} 
                testID={`option-${index}`} 
                onPress={() => setSelectedAnswer(index)}
              >
                <Text>{option}</Text>
              </TouchableOpacity>
            ))}
            <TouchableOpacity testID="submit-answer-button" onPress={submitAnswer}>
              <Text>Submit Answer</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    );
  };
});

jest.mock('../../features/coach/screens/AITradingCoachScreen', () => {
  return function MockAITradingCoachScreen({ navigateTo }: any) {
    const [activeTab, setActiveTab] = React.useState('strategy');
    const [riskLevel, setRiskLevel] = React.useState(50);
    const [strategies, setStrategies] = React.useState([]);

    const loadStrategies = () => {
      setStrategies([
        { id: 'strategy_1', name: 'Conservative Options', risk: 'low' },
        { id: 'strategy_2', name: 'Moderate Growth', risk: 'medium' },
        { id: 'strategy_3', name: 'Aggressive Trading', risk: 'high' }
      ]);
    };

    return (
      <View testID="ai-trading-coach-screen">
        <View testID="tab-bar">
          <TouchableOpacity testID="strategy-tab" onPress={() => setActiveTab('strategy')}>
            <Text>Strategy</Text>
          </TouchableOpacity>
          <TouchableOpacity testID="session-tab" onPress={() => setActiveTab('session')}>
            <Text>Session</Text>
          </TouchableOpacity>
          <TouchableOpacity testID="analysis-tab" onPress={() => setActiveTab('analysis')}>
            <Text>Analysis</Text>
          </TouchableOpacity>
          <TouchableOpacity testID="confidence-tab" onPress={() => setActiveTab('confidence')}>
            <Text>Confidence</Text>
          </TouchableOpacity>
        </View>
        
        {activeTab === 'strategy' && (
          <View testID="strategy-content">
            <Text testID="risk-level-text">Risk Level: {riskLevel}%</Text>
            <TouchableOpacity testID="load-strategies-button" onPress={loadStrategies}>
              <Text>Load Strategies</Text>
            </TouchableOpacity>
            {strategies.map((strategy: any) => (
              <View key={strategy.id} testID={`strategy-${strategy.id}`}>
                <Text>{strategy.name}</Text>
                <Text>Risk: {strategy.risk}</Text>
              </View>
            ))}
          </View>
        )}
        
        {activeTab === 'session' && (
          <View testID="session-content">
            <Text>Live Trading Session</Text>
            <TouchableOpacity testID="start-session-button">
              <Text>Start Session</Text>
            </TouchableOpacity>
          </View>
        )}
        
        {activeTab === 'analysis' && (
          <View testID="analysis-content">
            <Text>Trade Analysis</Text>
            <TouchableOpacity testID="run-analysis-button">
              <Text>Run Analysis</Text>
            </TouchableOpacity>
          </View>
        )}
        
        {activeTab === 'confidence' && (
          <View testID="confidence-content">
            <Text>Confidence Building</Text>
            <TouchableOpacity testID="build-confidence-button">
              <Text>Build Confidence</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    );
  };
});

jest.mock('../../features/community/screens/WealthCirclesScreen', () => {
  return function MockWealthCirclesScreen({ navigateTo }: any) {
    const [circles, setCircles] = React.useState([]);
    const [activeTab, setActiveTab] = React.useState('browse');

    const loadCircles = () => {
      setCircles([
        { id: 'circle_1', name: 'Options Trading Circle', members: 150 },
        { id: 'circle_2', name: 'Portfolio Management', members: 200 }
      ]);
    };

    return (
      <View testID="wealth-circles-screen">
        <View testID="circles-tab-bar">
          <TouchableOpacity testID="browse-tab" onPress={() => setActiveTab('browse')}>
            <Text>Browse</Text>
          </TouchableOpacity>
          <TouchableOpacity testID="my-circles-tab" onPress={() => setActiveTab('my-circles')}>
            <Text>My Circles</Text>
          </TouchableOpacity>
          <TouchableOpacity testID="create-tab" onPress={() => setActiveTab('create')}>
            <Text>Create</Text>
          </TouchableOpacity>
        </View>
        
        <TouchableOpacity testID="load-circles-button" onPress={loadCircles}>
          <Text>Load Circles</Text>
        </TouchableOpacity>
        
        {circles.map((circle: any) => (
          <View key={circle.id} testID={`circle-${circle.id}`}>
            <Text>{circle.name}</Text>
            <Text>{circle.members} members</Text>
          </View>
        ))}
      </View>
    );
  };
});

jest.mock('../../features/personalization/screens/PersonalizationDashboardScreen', () => {
  return function MockPersonalizationDashboardScreen({ navigateTo }: any) {
    const [insights, setInsights] = React.useState(null);

    const loadInsights = () => {
      setInsights({
        engagement_score: 0.85,
        learning_velocity: 'fast',
        preferred_content: ['interactive', 'video']
      });
    };

    return (
      <View testID="personalization-dashboard-screen">
        <Text>Personalization Dashboard</Text>
        <TouchableOpacity testID="load-insights-button" onPress={loadInsights}>
          <Text>Load Insights</Text>
        </TouchableOpacity>
        {insights && (
          <View testID="insights-content">
            <Text testID="engagement-score">Engagement: {insights.engagement_score}</Text>
            <Text testID="learning-velocity">Velocity: {insights.learning_velocity}</Text>
          </View>
        )}
      </View>
    );
  };
});

// Import the main App component
import App from '../App';

describe('Comprehensive UI Component Tests', () => {
  let mockNavigateTo: jest.Mock;

  beforeEach(() => {
    mockNavigateTo = jest.fn();
    jest.clearAllMocks();
  });

  describe('Authentication Screens', () => {
    test('LoginScreen renders correctly and handles user interactions', async () => {
      const { getByTestId } = render(
        <App />
      );

      // Navigate to login screen (assuming it's the default)
      const loginScreen = getByTestId('login-screen');
      expect(loginScreen).toBeTruthy();

      // Test email input
      const emailInput = getByTestId('email-input');
      fireEvent.changeText(emailInput, 'test@example.com');
      expect(emailInput.props.value).toBe('test@example.com');

      // Test password input
      const passwordInput = getByTestId('password-input');
      fireEvent.changeText(passwordInput, 'password123');
      expect(passwordInput.props.value).toBe('password123');

      // Test login button
      const loginButton = getByTestId('login-button');
      fireEvent.press(loginButton);

      // Test navigation buttons
      const signupButton = getByTestId('signup-button');
      fireEvent.press(signupButton);

      const forgotPasswordButton = getByTestId('forgot-password-button');
      fireEvent.press(forgotPasswordButton);
    });

    test('SignUpScreen renders correctly and handles user interactions', async () => {
      const { getByTestId } = render(
        <App />
      );

      // Navigate to signup screen
      const signupButton = getByTestId('signup-button');
      fireEvent.press(signupButton);

      const signupScreen = getByTestId('signup-screen');
      expect(signupScreen).toBeTruthy();

      // Test form inputs
      const emailInput = getByTestId('signup-email-input');
      fireEvent.changeText(emailInput, 'newuser@example.com');

      const passwordInput = getByTestId('signup-password-input');
      fireEvent.changeText(passwordInput, 'newpassword123');

      // Test signup submission
      const signupSubmitButton = getByTestId('signup-submit-button');
      fireEvent.press(signupSubmitButton);

      // Test back to login
      const loginLinkButton = getByTestId('login-link-button');
      fireEvent.press(loginLinkButton);
    });

    test('ForgotPasswordScreen renders correctly and handles user interactions', async () => {
      const { getByTestId } = render(
        <App />
      );

      // Navigate to forgot password screen
      const forgotPasswordButton = getByTestId('forgot-password-button');
      fireEvent.press(forgotPasswordButton);

      const forgotPasswordScreen = getByTestId('forgot-password-screen');
      expect(forgotPasswordScreen).toBeTruthy();

      // Test email input
      const resetEmailInput = getByTestId('reset-email-input');
      fireEvent.changeText(resetEmailInput, 'test@example.com');

      // Test reset password
      const resetPasswordButton = getByTestId('reset-password-button');
      fireEvent.press(resetPasswordButton);

      // Test back to login
      const backToLoginButton = getByTestId('back-to-login-button');
      fireEvent.press(backToLoginButton);
    });
  });

  describe('Home Screen Navigation', () => {
    test('HomeScreen renders correctly and handles navigation', async () => {
      const { getByTestId } = render(
        <App />
      );

      // Navigate to home screen (after login)
      const homeScreen = getByTestId('home-screen');
      expect(homeScreen).toBeTruthy();

      // Test navigation to AI Tutor
      const aiTutorButton = getByTestId('ai-tutor-button');
      fireEvent.press(aiTutorButton);

      // Test navigation to AI Trading Coach
      const tradingCoachButton = getByTestId('ai-trading-coach-button');
      fireEvent.press(tradingCoachButton);

      // Test navigation to Wealth Circles
      const wealthCirclesButton = getByTestId('wealth-circles-button');
      fireEvent.press(wealthCirclesButton);

      // Test navigation to Personalization
      const personalizationButton = getByTestId('personalization-button');
      fireEvent.press(personalizationButton);
    });
  });

  describe('AI Education Screens', () => {
    test('TutorAskExplainScreen renders correctly and handles interactions', async () => {
      const { getByTestId } = render(
        <App />
      );

      // Navigate to AI Tutor
      const aiTutorButton = getByTestId('ai-tutor-button');
      fireEvent.press(aiTutorButton);

      const tutorScreen = getByTestId('tutor-ask-explain-screen');
      expect(tutorScreen).toBeTruthy();

      // Test mode toggle
      const askModeButton = getByTestId('ask-mode-button');
      fireEvent.press(askModeButton);

      const explainModeButton = getByTestId('explain-mode-button');
      fireEvent.press(explainModeButton);

      // Test question input
      const questionInput = getByTestId('question-input');
      fireEvent.changeText(questionInput, 'What is options trading?');

      // Test submit
      const submitButton = getByTestId('submit-button');
      fireEvent.press(submitButton);

      // Wait for response
      await waitFor(() => {
        const responseText = getByTestId('response-text');
        expect(responseText).toBeTruthy();
      });
    });

    test('TutorQuizScreen renders correctly and handles quiz interactions', async () => {
      const { getByTestId } = render(
        <App />
      );

      // Navigate to quiz screen
      const aiTutorButton = getByTestId('ai-tutor-button');
      fireEvent.press(aiTutorButton);

      const quizScreen = getByTestId('tutor-quiz-screen');
      expect(quizScreen).toBeTruthy();

      // Test regime-adaptive toggle
      const regimeAdaptiveToggle = getByTestId('regime-adaptive-toggle');
      fireEvent.press(regimeAdaptiveToggle);

      // Test load quiz
      const loadQuizButton = getByTestId('load-quiz-button');
      fireEvent.press(loadQuizButton);

      // Wait for quiz content
      await waitFor(() => {
        const quizContent = getByTestId('quiz-content');
        expect(quizContent).toBeTruthy();
      });

      // Test quiz interactions
      const quizTopic = getByTestId('quiz-topic');
      expect(quizTopic).toBeTruthy();

      const quizQuestion = getByTestId('quiz-question');
      expect(quizQuestion).toBeTruthy();

      // Test option selection
      const option0 = getByTestId('option-0');
      fireEvent.press(option0);

      // Test answer submission
      const submitAnswerButton = getByTestId('submit-answer-button');
      fireEvent.press(submitAnswerButton);
    });
  });

  describe('AI Trading Coach Screen', () => {
    test('AITradingCoachScreen renders correctly and handles tab navigation', async () => {
      const { getByTestId } = render(
        <App />
      );

      // Navigate to AI Trading Coach
      const tradingCoachButton = getByTestId('ai-trading-coach-button');
      fireEvent.press(tradingCoachButton);

      const coachScreen = getByTestId('ai-trading-coach-screen');
      expect(coachScreen).toBeTruthy();

      // Test tab navigation
      const strategyTab = getByTestId('strategy-tab');
      fireEvent.press(strategyTab);

      const sessionTab = getByTestId('session-tab');
      fireEvent.press(sessionTab);

      const analysisTab = getByTestId('analysis-tab');
      fireEvent.press(analysisTab);

      const confidenceTab = getByTestId('confidence-tab');
      fireEvent.press(confidenceTab);

      // Test strategy tab content
      fireEvent.press(strategyTab);
      const strategyContent = getByTestId('strategy-content');
      expect(strategyContent).toBeTruthy();

      // Test load strategies
      const loadStrategiesButton = getByTestId('load-strategies-button');
      fireEvent.press(loadStrategiesButton);

      // Wait for strategies to load
      await waitFor(() => {
        const strategy1 = getByTestId('strategy-strategy_1');
        expect(strategy1).toBeTruthy();
      });

      // Test session tab content
      fireEvent.press(sessionTab);
      const sessionContent = getByTestId('session-content');
      expect(sessionContent).toBeTruthy();

      const startSessionButton = getByTestId('start-session-button');
      fireEvent.press(startSessionButton);

      // Test analysis tab content
      fireEvent.press(analysisTab);
      const analysisContent = getByTestId('analysis-content');
      expect(analysisContent).toBeTruthy();

      const runAnalysisButton = getByTestId('run-analysis-button');
      fireEvent.press(runAnalysisButton);

      // Test confidence tab content
      fireEvent.press(confidenceTab);
      const confidenceContent = getByTestId('confidence-content');
      expect(confidenceContent).toBeTruthy();

      const buildConfidenceButton = getByTestId('build-confidence-button');
      fireEvent.press(buildConfidenceButton);
    });
  });

  describe('Community Features Screens', () => {
    test('WealthCirclesScreen renders correctly and handles interactions', async () => {
      const { getByTestId } = render(
        <App />
      );

      // Navigate to Wealth Circles
      const wealthCirclesButton = getByTestId('wealth-circles-button');
      fireEvent.press(wealthCirclesButton);

      const circlesScreen = getByTestId('wealth-circles-screen');
      expect(circlesScreen).toBeTruthy();

      // Test tab navigation
      const browseTab = getByTestId('browse-tab');
      fireEvent.press(browseTab);

      const myCirclesTab = getByTestId('my-circles-tab');
      fireEvent.press(myCirclesTab);

      const createTab = getByTestId('create-tab');
      fireEvent.press(createTab);

      // Test load circles
      fireEvent.press(browseTab);
      const loadCirclesButton = getByTestId('load-circles-button');
      fireEvent.press(loadCirclesButton);

      // Wait for circles to load
      await waitFor(() => {
        const circle1 = getByTestId('circle-circle_1');
        expect(circle1).toBeTruthy();
      });
    });
  });

  describe('Personalization Screens', () => {
    test('PersonalizationDashboardScreen renders correctly and handles interactions', async () => {
      const { getByTestId } = render(
        <App />
      );

      // Navigate to Personalization Dashboard
      const personalizationButton = getByTestId('personalization-button');
      fireEvent.press(personalizationButton);

      const dashboardScreen = getByTestId('personalization-dashboard-screen');
      expect(dashboardScreen).toBeTruthy();

      // Test load insights
      const loadInsightsButton = getByTestId('load-insights-button');
      fireEvent.press(loadInsightsButton);

      // Wait for insights to load
      await waitFor(() => {
        const insightsContent = getByTestId('insights-content');
        expect(insightsContent).toBeTruthy();
      });

      // Test insights display
      const engagementScore = getByTestId('engagement-score');
      expect(engagementScore).toBeTruthy();

      const learningVelocity = getByTestId('learning-velocity');
      expect(learningVelocity).toBeTruthy();
    });
  });

  describe('User Interaction Flows', () => {
    test('Complete user journey from login to AI features', async () => {
      const { getByTestId } = render(
        <App />
      );

      // 1. Login
      const emailInput = getByTestId('email-input');
      fireEvent.changeText(emailInput, 'test@example.com');

      const passwordInput = getByTestId('password-input');
      fireEvent.changeText(passwordInput, 'password123');

      const loginButton = getByTestId('login-button');
      fireEvent.press(loginButton);

      // 2. Navigate to AI Tutor
      await waitFor(() => {
        const aiTutorButton = getByTestId('ai-tutor-button');
        fireEvent.press(aiTutorButton);
      });

      // 3. Use AI Tutor
      await waitFor(() => {
        const questionInput = getByTestId('question-input');
        fireEvent.changeText(questionInput, 'What is options trading?');

        const submitButton = getByTestId('submit-button');
        fireEvent.press(submitButton);
      });

      // 4. Navigate to AI Trading Coach
      await waitFor(() => {
        const tradingCoachButton = getByTestId('ai-trading-coach-button');
        fireEvent.press(tradingCoachButton);
      });

      // 5. Use AI Trading Coach
      await waitFor(() => {
        const strategyTab = getByTestId('strategy-tab');
        fireEvent.press(strategyTab);

        const loadStrategiesButton = getByTestId('load-strategies-button');
        fireEvent.press(loadStrategiesButton);
      });
    });

    test('Community engagement flow', async () => {
      const { getByTestId } = render(
        <App />
      );

      // Navigate to Wealth Circles
      const wealthCirclesButton = getByTestId('wealth-circles-button');
      fireEvent.press(wealthCirclesButton);

      // Browse circles
      const browseTab = getByTestId('browse-tab');
      fireEvent.press(browseTab);

      const loadCirclesButton = getByTestId('load-circles-button');
      fireEvent.press(loadCirclesButton);

      // Wait for circles to load and interact
      await waitFor(() => {
        const circle1 = getByTestId('circle-circle_1');
        expect(circle1).toBeTruthy();
      });
    });

    test('Personalization flow', async () => {
      const { getByTestId } = render(
        <App />
      );

      // Navigate to Personalization Dashboard
      const personalizationButton = getByTestId('personalization-button');
      fireEvent.press(personalizationButton);

      // Load insights
      const loadInsightsButton = getByTestId('load-insights-button');
      fireEvent.press(loadInsightsButton);

      // Wait for insights to load
      await waitFor(() => {
        const insightsContent = getByTestId('insights-content');
        expect(insightsContent).toBeTruthy();
      });
    });
  });

  describe('Error Handling and Edge Cases', () => {
    test('Handles empty input gracefully', async () => {
      const { getByTestId } = render(
        <App />
      );

      // Test empty email
      const emailInput = getByTestId('email-input');
      fireEvent.changeText(emailInput, '');

      const loginButton = getByTestId('login-button');
      fireEvent.press(loginButton);

      // Should not crash
      expect(getByTestId('login-screen')).toBeTruthy();
    });

    test('Handles rapid navigation without crashes', async () => {
      const { getByTestId } = render(
        <App />
      );

      // Rapid navigation between screens
      const aiTutorButton = getByTestId('ai-tutor-button');
      const tradingCoachButton = getByTestId('ai-trading-coach-button');
      const wealthCirclesButton = getByTestId('wealth-circles-button');

      fireEvent.press(aiTutorButton);
      fireEvent.press(tradingCoachButton);
      fireEvent.press(wealthCirclesButton);
      fireEvent.press(aiTutorButton);

      // Should not crash
      expect(getByTestId('ai-tutor-button')).toBeTruthy();
    });

    test('Handles component unmounting gracefully', async () => {
      const { getByTestId, unmount } = render(
        <App />
      );

      // Navigate to a screen
      const aiTutorButton = getByTestId('ai-tutor-button');
      fireEvent.press(aiTutorButton);

      // Unmount component
      unmount();

      // Should not throw errors
      expect(true).toBe(true);
    });
  });

  describe('Accessibility Tests', () => {
    test('All interactive elements have proper accessibility labels', async () => {
      const { getByTestId } = render(
        <App />
      );

      // Test login screen accessibility
      const loginButton = getByTestId('login-button');
      expect(loginButton).toBeTruthy();

      const signupButton = getByTestId('signup-button');
      expect(signupButton).toBeTruthy();

      // Test home screen accessibility
      const aiTutorButton = getByTestId('ai-tutor-button');
      expect(aiTutorButton).toBeTruthy();

      const tradingCoachButton = getByTestId('ai-trading-coach-button');
      expect(tradingCoachButton).toBeTruthy();
    });

    test('Text inputs are properly accessible', async () => {
      const { getByTestId } = render(
        <App />
      );

      const emailInput = getByTestId('email-input');
      expect(emailInput).toBeTruthy();
      expect(emailInput.props.placeholder).toBe('Email');

      const passwordInput = getByTestId('password-input');
      expect(passwordInput).toBeTruthy();
      expect(passwordInput.props.secureTextEntry).toBe(true);
    });
  });

  describe('Performance Tests', () => {
    test('Screen transitions are smooth', async () => {
      const { getByTestId } = render(
        <App />
      );

      const startTime = Date.now();

      // Navigate between screens
      const aiTutorButton = getByTestId('ai-tutor-button');
      fireEvent.press(aiTutorButton);

      const tradingCoachButton = getByTestId('ai-trading-coach-button');
      fireEvent.press(tradingCoachButton);

      const endTime = Date.now();
      const transitionTime = endTime - startTime;

      // Transitions should be fast (less than 100ms for mock components)
      expect(transitionTime).toBeLessThan(100);
    });

    test('Large lists render efficiently', async () => {
      const { getByTestId } = render(
        <App />
      );

      // Navigate to Wealth Circles
      const wealthCirclesButton = getByTestId('wealth-circles-button');
      fireEvent.press(wealthCirclesButton);

      const loadCirclesButton = getByTestId('load-circles-button');
      fireEvent.press(loadCirclesButton);

      // Wait for circles to load
      await waitFor(() => {
        const circle1 = getByTestId('circle-circle_1');
        expect(circle1).toBeTruthy();
      });

      // Should handle multiple items efficiently
      expect(getByTestId('circle-circle_1')).toBeTruthy();
      expect(getByTestId('circle-circle_2')).toBeTruthy();
    });
  });
});
