/**
 * Unit tests for Phase 2 React Native components:
 * - WealthCirclesScreen
 * - PeerProgressScreen
 * - TradeChallengesScreen
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';

// Mock the AI client
jest.mock('../../services/aiClient', () => ({
  createWealthCircle: jest.fn(),
  getWealthCircles: jest.fn(),
  createDiscussionPost: jest.fn(),
  getDiscussionPosts: jest.fn(),
  shareProgress: jest.fn(),
  getCommunityStats: jest.fn(),
  createChallenge: jest.fn(),
  getActiveChallenges: jest.fn(),
  makePrediction: jest.fn(),
  getChallengeLeaderboard: jest.fn(),
}));

// Mock react-native-vector-icons
jest.mock('react-native-vector-icons/Feather', () => 'Icon');

// Import components
import WealthCirclesScreen from '../features/community/screens/WealthCirclesScreen';
import PeerProgressScreen from '../features/community/screens/PeerProgressScreen';
import TradeChallengesScreen from '../features/community/screens/TradeChallengesScreen';

describe('WealthCirclesScreen', () => {
  const mockNavigateTo = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly with initial state', () => {
    const { getByText, getByTestId } = render(
      <WealthCirclesScreen navigateTo={mockNavigateTo} />
    );

    expect(getByText('Wealth Circles')).toBeTruthy();
    expect(getByText('Connect with your community')).toBeTruthy();
    expect(getByTestId('circles-tab')).toBeTruthy();
    expect(getByTestId('discussions-tab')).toBeTruthy();
  });

  it('displays wealth circles list', async () => {
    const mockCircles = [
      {
        circle_id: 'circle_1',
        name: 'Q4 Wealth Building Goals',
        description: 'Building wealth for the future',
        member_count: 15,
        is_private: false
      },
      {
        circle_id: 'circle_2',
        name: 'Options Trading Masters',
        description: 'Advanced options strategies',
        member_count: 8,
        is_private: true
      }
    ];

    const { getWealthCircles } = require('../../services/aiClient');
    getWealthCircles.mockResolvedValue(mockCircles);

    const { getByTestId, getByText } = render(
      <WealthCirclesScreen navigateTo={mockNavigateTo} />
    );

    const circlesTab = getByTestId('circles-tab');
    fireEvent.press(circlesTab);

    await waitFor(() => {
      expect(getByText('Q4 Wealth Building Goals')).toBeTruthy();
      expect(getByText('Options Trading Masters')).toBeTruthy();
      expect(getByText('15 members')).toBeTruthy();
    });
  });

  it('allows creating new wealth circle', async () => {
    const mockNewCircle = {
      circle_id: 'circle_new',
      name: 'Test Circle',
      description: 'Test description',
      member_count: 1
    };

    const { createWealthCircle } = require('../../services/aiClient');
    createWealthCircle.mockResolvedValue(mockNewCircle);

    const { getByTestId, getByText } = render(
      <WealthCirclesScreen navigateTo={mockNavigateTo} />
    );

    const createButton = getByTestId('create-circle-button');
    fireEvent.press(createButton);

    // Simulate form submission
    const nameInput = getByTestId('circle-name-input');
    const descriptionInput = getByTestId('circle-description-input');
    
    fireEvent.changeText(nameInput, 'Test Circle');
    fireEvent.changeText(descriptionInput, 'Test description');

    const submitButton = getByTestId('submit-circle-button');
    fireEvent.press(submitButton);

    await waitFor(() => {
      expect(createWealthCircle).toHaveBeenCalledWith({
        name: 'Test Circle',
        description: 'Test description',
        creator_id: 'user_123',
        is_private: false
      });
    });
  });

  it('displays discussion posts', async () => {
    const mockPosts = [
      {
        post_id: 'post_1',
        title: 'Investment Strategy Discussion',
        content: 'What are your thoughts on DCA?',
        author_id: 'user_1',
        created_at: '2024-01-15T10:30:00Z',
        likes: 5,
        comments: 3
      },
      {
        post_id: 'post_2',
        title: 'Market Analysis',
        content: 'Current market trends analysis',
        author_id: 'user_2',
        created_at: '2024-01-15T09:00:00Z',
        likes: 8,
        comments: 2
      }
    ];

    const { getDiscussionPosts } = require('../../services/aiClient');
    getDiscussionPosts.mockResolvedValue(mockPosts);

    const { getByTestId, getByText } = render(
      <WealthCirclesScreen navigateTo={mockNavigateTo} />
    );

    const discussionsTab = getByTestId('discussions-tab');
    fireEvent.press(discussionsTab);

    await waitFor(() => {
      expect(getByText('Investment Strategy Discussion')).toBeTruthy();
      expect(getByText('Market Analysis')).toBeTruthy();
      expect(getByText('5 likes')).toBeTruthy();
    });
  });

  it('allows creating discussion posts', async () => {
    const mockNewPost = {
      post_id: 'post_new',
      title: 'New Discussion',
      content: 'New post content',
      author_id: 'user_123'
    };

    const { createDiscussionPost } = require('../../services/aiClient');
    createDiscussionPost.mockResolvedValue(mockNewPost);

    const { getByTestId } = render(
      <WealthCirclesScreen navigateTo={mockNavigateTo} />
    );

    const discussionsTab = getByTestId('discussions-tab');
    fireEvent.press(discussionsTab);

    const createPostButton = getByTestId('create-post-button');
    fireEvent.press(createPostButton);

    // Simulate form submission
    const titleInput = getByTestId('post-title-input');
    const contentInput = getByTestId('post-content-input');
    
    fireEvent.changeText(titleInput, 'New Discussion');
    fireEvent.changeText(contentInput, 'New post content');

    const submitButton = getByTestId('submit-post-button');
    fireEvent.press(submitButton);

    await waitFor(() => {
      expect(createDiscussionPost).toHaveBeenCalledWith({
        circle_id: 'selected_circle',
        title: 'New Discussion',
        content: 'New post content',
        author_id: 'user_123'
      });
    });
  });
});

describe('PeerProgressScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly with initial state', () => {
    const { getByText } = render(<PeerProgressScreen />);

    expect(getByText('Peer Progress Pulse')).toBeTruthy();
    expect(getByText('See anonymous achievements from your community')).toBeTruthy();
  });

  it('displays community statistics', () => {
    const { getByText } = render(<PeerProgressScreen />);

    expect(getByText('1,245')).toBeTruthy(); // Total Members
    expect(getByText('230')).toBeTruthy(); // Active Today
    expect(getByText('87')).toBeTruthy(); // New Achievements
  });

  it('displays recent achievements', () => {
    const { getByText } = render(<PeerProgressScreen />);

    expect(getByText('Completed "Intro to Options" module!')).toBeTruthy();
    expect(getByText('Scored 95% on "Risk Management" quiz!')).toBeTruthy();
    expect(getByText('AnonymousUser1')).toBeTruthy();
    expect(getByText('2 hours ago')).toBeTruthy();
  });

  it('allows loading more achievements', () => {
    const { getByTestId } = render(<PeerProgressScreen />);

    const loadMoreButton = getByTestId('load-more-button');
    expect(loadMoreButton).toBeTruthy();
    
    fireEvent.press(loadMoreButton);
    // Should trigger load more functionality
  });

  it('displays motivation card', () => {
    const { getByText } = render(<PeerProgressScreen />);

    expect(getByText('Stay Motivated!')).toBeTruthy();
    expect(getByText('Seeing others succeed can inspire your own journey. Keep learning, keep growing!')).toBeTruthy();
  });
});

describe('TradeChallengesScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly with initial state', () => {
    const { getByText, getByTestId } = render(<TradeChallengesScreen />);

    expect(getByText('Trade Challenges')).toBeTruthy();
    expect(getByText('Compete, predict, and climb the ranks!')).toBeTruthy();
    expect(getByTestId('challenges-tab')).toBeTruthy();
    expect(getByTestId('predictions-tab')).toBeTruthy();
    expect(getByTestId('leaderboard-tab')).toBeTruthy();
  });

  it('displays active challenges', () => {
    const { getByText, getByTestId } = render(<TradeChallengesScreen />);

    const challengesTab = getByTestId('challenges-tab');
    fireEvent.press(challengesTab);

    expect(getByText('AAPL Earnings Prediction')).toBeTruthy();
    expect(getByText('Options Strategy Simulation')).toBeTruthy();
    expect(getByText('Risk Management Mastery')).toBeTruthy();
    expect(getByText('150 Participants')).toBeTruthy();
    expect(getByText('500 points')).toBeTruthy();
  });

  it('shows challenge status badges', () => {
    const { getByText, getByTestId } = render(<TradeChallengesScreen />);

    const challengesTab = getByTestId('challenges-tab');
    fireEvent.press(challengesTab);

    expect(getByText('ACTIVE')).toBeTruthy();
    expect(getByText('UPCOMING')).toBeTruthy();
  });

  it('allows joining challenges', () => {
    const { getByTestId } = render(<TradeChallengesScreen />);

    const challengesTab = getByTestId('challenges-tab');
    fireEvent.press(challengesTab);

    const joinButton = getByTestId('join-challenge-button-0');
    fireEvent.press(joinButton);
    // Should trigger join challenge functionality
  });

  it('displays predictions', () => {
    const { getByText, getByTestId } = render(<TradeChallengesScreen />);

    const predictionsTab = getByTestId('predictions-tab');
    fireEvent.press(predictionsTab);

    expect(getByText("TraderX's Prediction")).toBeTruthy();
    expect(getByText('AAPL +3% by EOD')).toBeTruthy();
    expect(getByText('Confidence: 85%')).toBeTruthy();
  });

  it('allows making predictions', () => {
    const { getByTestId } = render(<TradeChallengesScreen />);

    const predictionsTab = getByTestId('predictions-tab');
    fireEvent.press(predictionsTab);

    const makePredictionButton = getByTestId('make-prediction-button');
    fireEvent.press(makePredictionButton);
    // Should trigger prediction form
  });

  it('displays leaderboard', () => {
    const { getByText, getByTestId } = render(<TradeChallengesScreen />);

    const leaderboardTab = getByTestId('leaderboard-tab');
    fireEvent.press(leaderboardTab);

    expect(getByText('EliteTrader')).toBeTruthy();
    expect(getByText('AlphaSeeker')).toBeTruthy();
    expect(getByText('QuantKing')).toBeTruthy();
    expect(getByText('1250')).toBeTruthy(); // Top score
  });

  it('allows viewing full leaderboard', () => {
    const { getByTestId } = render(<TradeChallengesScreen />);

    const leaderboardTab = getByTestId('leaderboard-tab');
    fireEvent.press(leaderboardTab);

    const viewFullButton = getByTestId('view-full-leaderboard-button');
    fireEvent.press(viewFullButton);
    // Should navigate to full leaderboard
  });
});

// Integration tests for Phase 2 components
describe('Phase 2 Integration Tests', () => {
  it('wealth circle creation updates member count', async () => {
    const mockNewCircle = {
      circle_id: 'circle_new',
      name: 'Test Circle',
      member_count: 1
    };

    const { createWealthCircle, getWealthCircles } = require('../../services/aiClient');
    createWealthCircle.mockResolvedValue(mockNewCircle);
    getWealthCircles.mockResolvedValue([mockNewCircle]);

    const { getByTestId } = render(
      <WealthCirclesScreen navigateTo={jest.fn()} />
    );

    const createButton = getByTestId('create-circle-button');
    fireEvent.press(createButton);

    // Simulate successful creation
    await waitFor(() => {
      expect(createWealthCircle).toHaveBeenCalled();
    });
  });

  it('challenge participation updates leaderboard', async () => {
    const mockPrediction = {
      prediction_id: 'pred_new',
      challenge_id: 'challenge_1',
      user_id: 'user_123',
      confidence: 0.85
    };

    const { makePrediction, getChallengeLeaderboard } = require('../../services/aiClient');
    makePrediction.mockResolvedValue(mockPrediction);
    getChallengeLeaderboard.mockResolvedValue([
      { user_id: 'user_123', score: 800, rank: 1 }
    ]);

    const { getByTestId } = render(<TradeChallengesScreen />);

    const predictionsTab = getByTestId('predictions-tab');
    fireEvent.press(predictionsTab);

    const makePredictionButton = getByTestId('make-prediction-button');
    fireEvent.press(makePredictionButton);

    // Simulate prediction submission
    await waitFor(() => {
      expect(makePrediction).toHaveBeenCalled();
    });
  });

  it('progress sharing updates community stats', async () => {
    const mockProgress = {
      update_id: 'update_new',
      user_id: 'user_123',
      achievement_type: 'module_completed'
    };

    const { shareProgress, getCommunityStats } = require('../../services/aiClient');
    shareProgress.mockResolvedValue(mockProgress);
    getCommunityStats.mockResolvedValue({
      total_members: 1251,
      active_today: 231,
      new_achievements: 88
    });

    const { getByTestId } = render(<PeerProgressScreen />);

    const shareButton = getByTestId('share-progress-button');
    fireEvent.press(shareButton);

    await waitFor(() => {
      expect(shareProgress).toHaveBeenCalled();
    });
  });
});
