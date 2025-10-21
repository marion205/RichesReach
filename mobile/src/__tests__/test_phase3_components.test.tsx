/**
 * Unit tests for Phase 3 React Native components:
 * - PersonalizationDashboardScreen
 * - BehavioralAnalyticsScreen
 * - DynamicContentScreen
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';

// Mock the AI client
jest.mock('../../services/aiClient', () => ({
  trackBehavior: jest.fn(),
  getEngagementProfile: jest.fn(),
  getChurnPrediction: jest.fn(),
  getBehaviorPatterns: jest.fn(),
  adaptContent: jest.fn(),
  generatePersonalizedContent: jest.fn(),
  getContentRecommendations: jest.fn(),
  getPersonalizationScore: jest.fn(),
}));

// Mock react-native-vector-icons
jest.mock('react-native-vector-icons/Feather', () => 'Icon');

// Import components
import PersonalizationDashboardScreen from '../features/personalization/screens/PersonalizationDashboardScreen';
import BehavioralAnalyticsScreen from '../features/personalization/screens/BehavioralAnalyticsScreen';
import DynamicContentScreen from '../features/personalization/screens/DynamicContentScreen';

describe('PersonalizationDashboardScreen', () => {
  const mockNavigateTo = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly with initial state', () => {
    const { getByText, getByTestId } = render(
      <PersonalizationDashboardScreen navigateTo={mockNavigateTo} />
    );

    expect(getByText('Personalization Dashboard')).toBeTruthy();
    expect(getByText('Your AI-powered learning experience')).toBeTruthy();
    expect(getByTestId('overview-tab')).toBeTruthy();
    expect(getByTestId('recommendations-tab')).toBeTruthy();
    expect(getByTestId('settings-tab')).toBeTruthy();
  });

  it('displays personalization overview', async () => {
    const mockOverview = {
      personalization_score: 0.87,
      content_adaptations: 45,
      recommendations_clicked: 23,
      engagement_improvement: 0.18
    };

    const { getPersonalizationScore } = require('../../services/aiClient');
    getPersonalizationScore.mockResolvedValue(mockOverview);

    const { getByTestId, getByText } = render(
      <PersonalizationDashboardScreen navigateTo={mockNavigateTo} />
    );

    const overviewTab = getByTestId('overview-tab');
    fireEvent.press(overviewTab);

    await waitFor(() => {
      expect(getByText('87%')).toBeTruthy(); // Personalization score
      expect(getByText('45')).toBeTruthy(); // Content adaptations
      expect(getByText('23')).toBeTruthy(); // Recommendations clicked
      expect(getByText('18%')).toBeTruthy(); // Engagement improvement
    });
  });

  it('displays content recommendations', async () => {
    const mockRecommendations = [
      {
        content_id: 'rec_1',
        title: 'Advanced Options Strategies',
        type: 'learning_module',
        match_score: 0.92,
        engagement_prediction: 0.88
      },
      {
        content_id: 'rec_2',
        title: 'Risk Management Quiz',
        type: 'quiz',
        match_score: 0.85,
        engagement_prediction: 0.80
      }
    ];

    const { getContentRecommendations } = require('../../services/aiClient');
    getContentRecommendations.mockResolvedValue(mockRecommendations);

    const { getByTestId, getByText } = render(
      <PersonalizationDashboardScreen navigateTo={mockNavigateTo} />
    );

    const recommendationsTab = getByTestId('recommendations-tab');
    fireEvent.press(recommendationsTab);

    await waitFor(() => {
      expect(getByText('Advanced Options Strategies')).toBeTruthy();
      expect(getByText('Risk Management Quiz')).toBeTruthy();
      expect(getByText('92% match')).toBeTruthy();
      expect(getByText('88% engagement')).toBeTruthy();
    });
  });

  it('allows viewing recommended content', () => {
    const { getByTestId } = render(
      <PersonalizationDashboardScreen navigateTo={mockNavigateTo} />
    );

    const recommendationsTab = getByTestId('recommendations-tab');
    fireEvent.press(recommendationsTab);

    const viewContentButton = getByTestId('view-content-button-0');
    fireEvent.press(viewContentButton);
    // Should navigate to content
  });

  it('displays personalization settings', () => {
    const { getByText, getByTestId } = render(
      <PersonalizationDashboardScreen navigateTo={mockNavigateTo} />
    );

    const settingsTab = getByTestId('settings-tab');
    fireEvent.press(settingsTab);

    expect(getByText('Personalization Settings')).toBeTruthy();
    expect(getByText('Enable AI Personalization')).toBeTruthy();
    expect(getByText('Content Adaptation Level')).toBeTruthy();
  });

  it('allows toggling personalization settings', () => {
    const { getByTestId } = render(
      <PersonalizationDashboardScreen navigateTo={mockNavigateTo} />
    );

    const settingsTab = getByTestId('settings-tab');
    fireEvent.press(settingsTab);

    const personalizationToggle = getByTestId('personalization-toggle');
    fireEvent(personalizationToggle, 'onValueChange', false);
    // Should update personalization setting
  });
});

describe('BehavioralAnalyticsScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly with initial state', () => {
    const { getByText, getByTestId } = render(<BehavioralAnalyticsScreen />);

    expect(getByText('Behavioral Analytics')).toBeTruthy();
    expect(getByText('AI-powered insights into user behavior')).toBeTruthy();
    expect(getByTestId('patterns-tab')).toBeTruthy();
    expect(getByTestId('profile-tab')).toBeTruthy();
    expect(getByTestId('churn-tab')).toBeTruthy();
  });

  it('displays behavior patterns', () => {
    const { getByText, getByTestId } = render(<BehavioralAnalyticsScreen />);

    const patternsTab = getByTestId('patterns-tab');
    fireEvent.press(patternsTab);

    expect(getByText('Passive Learner')).toBeTruthy();
    expect(getByText('Risk-Averse Explorer')).toBeTruthy();
    expect(getByText('News-Driven Trader')).toBeTruthy();
    expect(getByText('Prefers consuming content over interactive exercises')).toBeTruthy();
    expect(getByText('Confidence: 85%')).toBeTruthy();
  });

  it('displays engagement profile', () => {
    const { getByText, getByTestId } = render(<BehavioralAnalyticsScreen />);

    const profileTab = getByTestId('profile-tab');
    fireEvent.press(profileTab);

    expect(getByText('Engagement Profile')).toBeTruthy();
    expect(getByText('Learning Style:')).toBeTruthy();
    expect(getByText('Visual & Auditory')).toBeTruthy();
    expect(getByText('Risk Tolerance:')).toBeTruthy();
    expect(getByText('Moderate')).toBeTruthy();
    expect(getByText('Active Days (last 30):')).toBeTruthy();
    expect(getByText('25')).toBeTruthy();
  });

  it('displays churn prediction', () => {
    const { getByText, getByTestId } = render(<BehavioralAnalyticsScreen />);

    const churnTab = getByTestId('churn-tab');
    fireEvent.press(churnTab);

    expect(getByText('Churn Prediction')).toBeTruthy();
    expect(getByText('Risk Level: Low')).toBeTruthy();
    expect(getByText('High engagement with core features, consistent login')).toBeTruthy();
    expect(getByText('Retention Strategies:')).toBeTruthy();
    expect(getByText('Continue personalized content delivery')).toBeTruthy();
  });

  it('shows loading state when fetching data', async () => {
    const { getEngagementProfile } = require('../../services/aiClient');
    getEngagementProfile.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));

    const { getByTestId, getByText } = render(<BehavioralAnalyticsScreen />);

    const profileTab = getByTestId('profile-tab');
    fireEvent.press(profileTab);

    await waitFor(() => {
      expect(getByText('Loading...')).toBeTruthy();
    });
  });

  it('handles errors gracefully', async () => {
    const { getEngagementProfile } = require('../../services/aiClient');
    getEngagementProfile.mockRejectedValue(new Error('Network error'));

    const { getByTestId, getByText } = render(<BehavioralAnalyticsScreen />);

    const profileTab = getByTestId('profile-tab');
    fireEvent.press(profileTab);

    await waitFor(() => {
      expect(getByText('Failed to load profile')).toBeTruthy();
    });
  });
});

describe('DynamicContentScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly with initial state', () => {
    const { getByText, getByTestId } = render(<DynamicContentScreen />);

    expect(getByText('Dynamic Content')).toBeTruthy();
    expect(getByText('Real-time content adaptation')).toBeTruthy();
    expect(getByTestId('adapted-tab')).toBeTruthy();
    expect(getByTestId('personalized-tab')).toBeTruthy();
    expect(getByTestId('recommendations-tab')).toBeTruthy();
    expect(getByTestId('settings-tab')).toBeTruthy();
  });

  it('displays adapted content', () => {
    const { getByText, getByTestId } = render(<DynamicContentScreen />);

    const adaptedTab = getByTestId('adapted-tab');
    fireEvent.press(adaptedTab);

    expect(getByText('Understanding Options Spreads')).toBeTruthy();
    expect(getByText('Original: Long-form Article')).toBeTruthy();
    expect(getByText('Adapted: Interactive Module with Calculator')).toBeTruthy();
    expect(getByText('User prefers interactive learning and practical application')).toBeTruthy();
  });

  it('displays personalized content', () => {
    const { getByText, getByTestId } = render(<DynamicContentScreen />);

    const personalizedTab = getByTestId('personalized-tab');
    fireEvent.press(personalizedTab);

    expect(getByText('Advanced Options Strategies for Volatile Markets')).toBeTruthy();
    expect(getByText('Type: Learning Module')).toBeTruthy();
    expect(getByText('Match Score: 92%')).toBeTruthy();
    expect(getByText('Engagement Prediction: 88%')).toBeTruthy();
  });

  it('allows viewing personalized content', () => {
    const { getByTestId } = render(<DynamicContentScreen />);

    const personalizedTab = getByTestId('personalized-tab');
    fireEvent.press(personalizedTab);

    const viewContentButton = getByTestId('view-content-button-0');
    fireEvent.press(viewContentButton);
    // Should navigate to content
  });

  it('allows generating more personalized content', () => {
    const { getByTestId } = render(<DynamicContentScreen />);

    const personalizedTab = getByTestId('personalized-tab');
    fireEvent.press(personalizedTab);

    const generateMoreButton = getByTestId('generate-more-button');
    fireEvent.press(generateMoreButton);
    // Should trigger content generation
  });

  it('displays content recommendations', () => {
    const { getByText, getByTestId } = render(<DynamicContentScreen />);

    const recommendationsTab = getByTestId('recommendations-tab');
    fireEvent.press(recommendationsTab);

    expect(getByText('Advanced Options Strategies for Volatile Markets')).toBeTruthy();
    expect(getByText('Community Discussion: Impact of Fed Rate Hikes')).toBeTruthy();
    expect(getByText('Quiz: Test Your Macroeconomics Knowledge')).toBeTruthy();
  });

  it('displays personalization settings', () => {
    const { getByText, getByTestId } = render(<DynamicContentScreen />);

    const settingsTab = getByTestId('settings-tab');
    fireEvent.press(settingsTab);

    expect(getByText('Personalization Settings')).toBeTruthy();
    expect(getByText('Enable Dynamic Content Adaptation')).toBeTruthy();
    expect(getByText('Personalization Level')).toBeTruthy();
  });

  it('allows toggling personalization settings', () => {
    const { getByTestId } = render(<DynamicContentScreen />);

    const settingsTab = getByTestId('settings-tab');
    fireEvent.press(settingsTab);

    const adaptationToggle = getByTestId('adaptation-toggle');
    fireEvent(adaptationToggle, 'onValueChange', false);
    // Should update adaptation setting
  });

  it('allows changing personalization level', () => {
    const { getByTestId } = render(<DynamicContentScreen />);

    const settingsTab = getByTestId('settings-tab');
    fireEvent.press(settingsTab);

    const levelSelector = getByTestId('personalization-level-selector');
    fireEvent(levelSelector, 'onValueChange', 'high');
    // Should update personalization level
  });
});

// Integration tests for Phase 3 components
describe('Phase 3 Integration Tests', () => {
  it('behavioral analytics drives content recommendations', async () => {
    const mockProfile = {
      learning_style: 'visual',
      preferred_content_types: ['interactive', 'video'],
      engagement_score: 0.85
    };

    const mockRecommendations = [
      {
        content_id: 'rec_1',
        title: 'Visual Options Tutorial',
        match_score: 0.95,
        engagement_prediction: 0.90
      }
    ];

    const { getEngagementProfile, getContentRecommendations } = require('../../services/aiClient');
    getEngagementProfile.mockResolvedValue(mockProfile);
    getContentRecommendations.mockResolvedValue(mockRecommendations);

    const { getByTestId, getByText } = render(<BehavioralAnalyticsScreen />);

    // Get engagement profile
    const profileTab = getByTestId('profile-tab');
    fireEvent.press(profileTab);

    await waitFor(() => {
      expect(getByText('Visual & Auditory')).toBeTruthy();
    });

    // Switch to recommendations
    const { getByTestId: getByTestId2 } = render(<DynamicContentScreen />);
    const recommendationsTab = getByTestId2('recommendations-tab');
    fireEvent.press(recommendationsTab);

    await waitFor(() => {
      expect(getByText('Visual Options Tutorial')).toBeTruthy();
    });
  });

  it('content adaptation improves personalization score', async () => {
    const mockAdaptedContent = {
      adapted_content_id: 'adapted_1',
      adaptation_reason: 'User prefers interactive content',
      personalization_score: 0.90
    };

    const mockScore = {
      overall_score: 0.87,
      content_adaptation_score: 0.90,
      engagement_improvement: 0.18
    };

    const { adaptContent, getPersonalizationScore } = require('../../services/aiClient');
    adaptContent.mockResolvedValue(mockAdaptedContent);
    getPersonalizationScore.mockResolvedValue(mockScore);

    const { getByTestId, getByText } = render(<DynamicContentScreen />);

    const adaptedTab = getByTestId('adapted-tab');
    fireEvent.press(adaptedTab);

    await waitFor(() => {
      expect(getByText('User prefers interactive learning and practical application')).toBeTruthy();
    });

    // Check personalization score
    const { getByTestId: getByTestId2 } = render(<PersonalizationDashboardScreen navigateTo={jest.fn()} />);
    const overviewTab = getByTestId2('overview-tab');
    fireEvent.press(overviewTab);

    await waitFor(() => {
      expect(getByText('87%')).toBeTruthy();
    });
  });

  it('churn prediction triggers retention content', async () => {
    const mockChurn = {
      risk_level: 'high',
      confidence: 0.85,
      retention_strategies: ['engagement_boost', 'personalized_content']
    };

    const mockRetentionContent = {
      content_id: 'retention_1',
      title: 'Motivational Trading Journey',
      type: 'engagement_boost',
      personalization_score: 0.95
    };

    const { getChurnPrediction, generatePersonalizedContent } = require('../../services/aiClient');
    getChurnPrediction.mockResolvedValue(mockChurn);
    generatePersonalizedContent.mockResolvedValue(mockRetentionContent);

    const { getByTestId, getByText } = render(<BehavioralAnalyticsScreen />);

    const churnTab = getByTestId('churn-tab');
    fireEvent.press(churnTab);

    await waitFor(() => {
      expect(getByText('Risk Level: High')).toBeTruthy();
    });

    // Generate retention content
    const generateButton = getByTestId('generate-retention-content-button');
    fireEvent.press(generateButton);

    await waitFor(() => {
      expect(generatePersonalizedContent).toHaveBeenCalledWith({
        user_id: 'user_123',
        content_type: 'engagement_boost',
        user_context: {
          risk_factors: mockChurn.retention_strategies
        }
      });
    });
  });
});
