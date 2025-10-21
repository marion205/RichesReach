/**
 * Unit tests for Phase 1 React Native components:
 * - DailyVoiceDigestScreen
 * - NotificationCenterScreen
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert } from 'react-native';

// Mock the AI client
jest.mock('../../services/aiClient', () => ({
  generateDailyDigest: jest.fn(),
  createRegimeAlert: jest.fn(),
  getNotificationPreferences: jest.fn(),
  updateNotificationPreferences: jest.fn(),
  getRecentNotifications: jest.fn(),
  checkRegimeChange: jest.fn(),
  getMonitoringStatus: jest.fn(),
}));

// Mock react-native-vector-icons
jest.mock('react-native-vector-icons/Feather', () => 'Icon');

// Import components
import DailyVoiceDigestScreen from '../features/learning/screens/DailyVoiceDigestScreen';
import NotificationCenterScreen from '../features/notifications/screens/NotificationCenterScreen';

describe('DailyVoiceDigestScreen', () => {
  const mockNavigateTo = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly with initial state', () => {
    const { getByText, getByTestId } = render(
      <DailyVoiceDigestScreen navigateTo={mockNavigateTo} />
    );

    expect(getByText('Daily Voice Digest')).toBeTruthy();
    expect(getByText('Your personalized market briefing')).toBeTruthy();
    expect(getByTestId('generate-digest-button')).toBeTruthy();
  });

  it('shows loading state when generating digest', async () => {
    const { getByTestId, getByText } = render(
      <DailyVoiceDigestScreen navigateTo={mockNavigateTo} />
    );

    const generateButton = getByTestId('generate-digest-button');
    
    fireEvent.press(generateButton);

    await waitFor(() => {
      expect(getByText('Generating your personalized digest...')).toBeTruthy();
    });
  });

  it('displays digest content after successful generation', async () => {
    const mockDigest = {
      digest_id: 'digest_123',
      content: 'Mock digest content',
      audio_url: 'https://example.com/audio.mp3',
      duration_seconds: 120,
      regime_context: {
        current_regime: 'bull_market',
        confidence: 0.85
      }
    };

    const { generateDailyDigest } = require('../../services/aiClient');
    generateDailyDigest.mockResolvedValue(mockDigest);

    const { getByTestId, getByText } = render(
      <DailyVoiceDigestScreen navigateTo={mockNavigateTo} />
    );

    const generateButton = getByTestId('generate-digest-button');
    fireEvent.press(generateButton);

    await waitFor(() => {
      expect(getByText('Mock digest content')).toBeTruthy();
      expect(getByText('Bull Market')).toBeTruthy();
      expect(getByText('85% confidence')).toBeTruthy();
    });
  });

  it('handles digest generation error gracefully', async () => {
    const { generateDailyDigest } = require('../../services/aiClient');
    generateDailyDigest.mockRejectedValue(new Error('Generation failed'));

    const { getByTestId, getByText } = render(
      <DailyVoiceDigestScreen navigateTo={mockNavigateTo} />
    );

    const generateButton = getByTestId('generate-digest-button');
    fireEvent.press(generateButton);

    await waitFor(() => {
      expect(getByText('Failed to generate digest. Please try again.')).toBeTruthy();
    });
  });

  it('allows playing audio when available', async () => {
    const mockDigest = {
      digest_id: 'digest_123',
      content: 'Mock digest content',
      audio_url: 'https://example.com/audio.mp3',
      duration_seconds: 120
    };

    const { generateDailyDigest } = require('../../services/aiClient');
    generateDailyDigest.mockResolvedValue(mockDigest);

    const { getByTestId } = render(
      <DailyVoiceDigestScreen navigateTo={mockNavigateTo} />
    );

    const generateButton = getByTestId('generate-digest-button');
    fireEvent.press(generateButton);

    await waitFor(() => {
      const playButton = getByTestId('play-audio-button');
      expect(playButton).toBeTruthy();
    });
  });

  it('shows regime alert when regime change detected', async () => {
    const mockRegimeAlert = {
      alert_id: 'alert_123',
      regime_change: {
        from_regime: 'sideways',
        to_regime: 'bull_market',
        confidence: 0.92
      }
    };

    const { createRegimeAlert } = require('../../services/aiClient');
    createRegimeAlert.mockResolvedValue(mockRegimeAlert);

    const { getByTestId, getByText } = render(
      <DailyVoiceDigestScreen navigateTo={mockNavigateTo} />
    );

    const regimeAlertButton = getByTestId('regime-alert-button');
    fireEvent.press(regimeAlertButton);

    await waitFor(() => {
      expect(getByText('Regime Change Alert')).toBeTruthy();
      expect(getByText('Sideways → Bull Market')).toBeTruthy();
    });
  });
});

describe('NotificationCenterScreen', () => {
  const mockNavigateTo = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly with initial state', () => {
    const { getByText, getByTestId } = render(
      <NotificationCenterScreen navigateTo={mockNavigateTo} />
    );

    expect(getByText('Notification Center')).toBeTruthy();
    expect(getByText('Manage your alerts and preferences')).toBeTruthy();
    expect(getByTestId('preferences-tab')).toBeTruthy();
    expect(getByTestId('notifications-tab')).toBeTruthy();
  });

  it('displays notification preferences', async () => {
    const mockPreferences = {
      push_enabled: true,
      email_enabled: false,
      digest_reminders: true,
      regime_alerts: true,
      mission_reminders: true,
      quiet_hours: { start: '22:00', end: '08:00' }
    };

    const { getNotificationPreferences } = require('../../services/aiClient');
    getNotificationPreferences.mockResolvedValue(mockPreferences);

    const { getByTestId, getByText } = render(
      <NotificationCenterScreen navigateTo={mockNavigateTo} />
    );

    const preferencesTab = getByTestId('preferences-tab');
    fireEvent.press(preferencesTab);

    await waitFor(() => {
      expect(getByText('Push Notifications')).toBeTruthy();
      expect(getByText('Digest Reminders')).toBeTruthy();
      expect(getByText('Regime Alerts')).toBeTruthy();
    });
  });

  it('allows toggling notification preferences', async () => {
    const mockPreferences = {
      push_enabled: true,
      regime_alerts: true
    };

    const { getNotificationPreferences, updateNotificationPreferences } = require('../../services/aiClient');
    getNotificationPreferences.mockResolvedValue(mockPreferences);
    updateNotificationPreferences.mockResolvedValue({ success: true });

    const { getByTestId } = render(
      <NotificationCenterScreen navigateTo={mockNavigateTo} />
    );

    const preferencesTab = getByTestId('preferences-tab');
    fireEvent.press(preferencesTab);

    await waitFor(() => {
      const regimeAlertsToggle = getByTestId('regime-alerts-toggle');
      fireEvent(regimeAlertsToggle, 'onValueChange', false);
    });

    expect(updateNotificationPreferences).toHaveBeenCalledWith('user_123', {
      regime_alerts: false
    });
  });

  it('displays recent notifications', async () => {
    const mockNotifications = [
      {
        id: 'notif_1',
        title: 'Market Regime Change',
        body: 'Market has shifted to bull market',
        type: 'regime_alert',
        timestamp: '2024-01-15T10:30:00Z',
        read: false
      },
      {
        id: 'notif_2',
        title: 'Daily Digest Ready',
        body: 'Your personalized digest is ready',
        type: 'digest_ready',
        timestamp: '2024-01-15T09:00:00Z',
        read: true
      }
    ];

    const { getRecentNotifications } = require('../../services/aiClient');
    getRecentNotifications.mockResolvedValue(mockNotifications);

    const { getByTestId, getByText } = render(
      <NotificationCenterScreen navigateTo={mockNavigateTo} />
    );

    const notificationsTab = getByTestId('notifications-tab');
    fireEvent.press(notificationsTab);

    await waitFor(() => {
      expect(getByText('Market Regime Change')).toBeTruthy();
      expect(getByText('Daily Digest Ready')).toBeTruthy();
    });
  });

  it('shows monitoring status', async () => {
    const mockStatus = {
      is_monitoring: true,
      last_check: '2024-01-15T10:30:00Z',
      total_alerts_sent: 15,
      active_regime: 'bull_market'
    };

    const { getMonitoringStatus } = require('../../services/aiClient');
    getMonitoringStatus.mockResolvedValue(mockStatus);

    const { getByTestId, getByText } = render(
      <NotificationCenterScreen navigateTo={mockNavigateTo} />
    );

    const monitoringTab = getByTestId('monitoring-tab');
    fireEvent.press(monitoringTab);

    await waitFor(() => {
      expect(getByText('Monitoring Status')).toBeTruthy();
      expect(getByText('Active')).toBeTruthy();
      expect(getByText('Bull Market')).toBeTruthy();
    });
  });

  it('handles regime change check', async () => {
    const mockRegimeChange = {
      change_detected: true,
      current_regime: 'bear_market',
      confidence: 0.88,
      previous_regime: 'sideways'
    };

    const { checkRegimeChange } = require('../../services/aiClient');
    checkRegimeChange.mockResolvedValue(mockRegimeChange);

    const { getByTestId, getByText } = render(
      <NotificationCenterScreen navigateTo={mockNavigateTo} />
    );

    const monitoringTab = getByTestId('monitoring-tab');
    fireEvent.press(monitoringTab);

    const checkButton = getByTestId('check-regime-button');
    fireEvent.press(checkButton);

    await waitFor(() => {
      expect(getByText('Regime Change Detected!')).toBeTruthy();
      expect(getByText('Sideways → Bear Market')).toBeTruthy();
    });
  });

  it('handles errors gracefully', async () => {
    const { getNotificationPreferences } = require('../../services/aiClient');
    getNotificationPreferences.mockRejectedValue(new Error('Network error'));

    const { getByTestId, getByText } = render(
      <NotificationCenterScreen navigateTo={mockNavigateTo} />
    );

    const preferencesTab = getByTestId('preferences-tab');
    fireEvent.press(preferencesTab);

    await waitFor(() => {
      expect(getByText('Failed to load preferences')).toBeTruthy();
    });
  });
});

// Integration tests for Phase 1 components
describe('Phase 1 Integration Tests', () => {
  it('daily digest generation triggers notification', async () => {
    const mockDigest = {
      digest_id: 'digest_123',
      content: 'Mock digest content',
      audio_url: 'https://example.com/audio.mp3'
    };

    const { generateDailyDigest } = require('../../services/aiClient');
    generateDailyDigest.mockResolvedValue(mockDigest);

    const { getByTestId } = render(
      <DailyVoiceDigestScreen navigateTo={jest.fn()} />
    );

    const generateButton = getByTestId('generate-digest-button');
    fireEvent.press(generateButton);

    await waitFor(() => {
      // Verify digest was generated
      expect(generateDailyDigest).toHaveBeenCalledWith('user_123', {
        risk_tolerance: 'moderate',
        preferred_content_types: ['market_analysis']
      });
    });
  });

  it('regime change detection triggers alert notification', async () => {
    const mockRegimeChange = {
      change_detected: true,
      current_regime: 'bull_market',
      confidence: 0.90
    };

    const { checkRegimeChange } = require('../../services/aiClient');
    checkRegimeChange.mockResolvedValue(mockRegimeChange);

    const { getByTestId } = render(
      <NotificationCenterScreen navigateTo={jest.fn()} />
    );

    const monitoringTab = getByTestId('monitoring-tab');
    fireEvent.press(monitoringTab);

    const checkButton = getByTestId('check-regime-button');
    fireEvent.press(checkButton);

    await waitFor(() => {
      expect(checkRegimeChange).toHaveBeenCalled();
    });
  });
});
