/**
 * Unit Tests for MomentStoryPlayer Component
 * Tests story playback, voice narration, analytics, and intro slide
 */

// CRITICAL: Import React FIRST to ensure ReactCurrentOwner is initialized
import React from 'react';

// Ensure React is globally available before importing test libraries
if (typeof global !== 'undefined') {
  global.React = React;
}

// Load jest-native matchers if available (after PixelRatio mock is set up)
if (typeof global.loadJestNativeMatchers === 'function') {
  global.loadJestNativeMatchers();
}

// Now safe to import test libraries that depend on React internals
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import MomentStoryPlayer, { MomentAnalyticsEvent } from '../MomentStoryPlayer';
import { StockMoment } from '../ChartWithMoments';
import * as Speech from 'expo-speech';
import * as Haptics from 'expo-haptics';

// Mock expo-speech
jest.mock('expo-speech', () => ({
  speak: jest.fn(),
  stop: jest.fn(),
}));

// Mock expo-haptics
jest.mock('expo-haptics', () => ({
  impactAsync: jest.fn(),
  selectionAsync: jest.fn(),
  notificationAsync: jest.fn(),
  ImpactFeedbackStyle: {
    Light: 0,
    Medium: 1,
    Heavy: 2,
  },
  NotificationFeedbackType: {
    Success: 0,
    Warning: 1,
    Error: 2,
  },
}));

describe('MomentStoryPlayer', () => {
  const mockMoments: StockMoment[] = [
    {
      id: '1',
      symbol: 'AAPL',
      timestamp: '2024-01-01T00:00:00Z',
      category: 'EARNINGS',
      title: 'Earnings Beat',
      quickSummary: 'Beat estimates',
      deepSummary: 'Apple reported strong earnings that exceeded analyst expectations.',
    },
    {
      id: '2',
      symbol: 'AAPL',
      timestamp: '2024-01-02T00:00:00Z',
      category: 'NEWS',
      title: 'Product Launch',
      quickSummary: 'New product',
      deepSummary: 'Apple announced a new product line with innovative features.',
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('renders when visible is true', () => {
    const { getByText } = render(
      <MomentStoryPlayer
        visible={true}
        symbol="AAPL"
        moments={mockMoments}
      />
    );

    expect(getByText('Story Mode')).toBeTruthy();
  });

  it('does not render when visible is false', () => {
    const { queryByText } = render(
      <MomentStoryPlayer
        visible={false}
        symbol="AAPL"
        moments={mockMoments}
      />
    );

    expect(queryByText('Story Mode')).toBeNull();
  });

  it('starts playing when opened with intro enabled', () => {
    render(
      <MomentStoryPlayer
        visible={true}
        symbol="AAPL"
        moments={mockMoments}
        enableIntro={true}
      />
    );

    // Should start speaking intro text
    expect(Speech.speak).toHaveBeenCalled();
  });

  it('skips intro when enableIntro is false', () => {
    render(
      <MomentStoryPlayer
        visible={true}
        symbol="AAPL"
        moments={mockMoments}
        enableIntro={false}
        initialIndex={0}
      />
    );

    // Should start with first real moment, not intro
    expect(Speech.speak).toHaveBeenCalled();
    const callArgs = (Speech.speak as jest.Mock).mock.calls[0];
    expect(callArgs[0]).toBe(mockMoments[0].deepSummary);
  });

  it('calls onAnalyticsEvent when story opens', () => {
    const onAnalytics = jest.fn();
    render(
      <MomentStoryPlayer
        visible={true}
        symbol="AAPL"
        moments={mockMoments}
        onAnalyticsEvent={onAnalytics}
      />
    );

    expect(onAnalytics).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'story_open',
        symbol: 'AAPL',
        totalMoments: 2,
      })
    );
  });

  it('calls onAnalyticsEvent when story closes', () => {
    const onAnalytics = jest.fn();
    const { getByText } = render(
      <MomentStoryPlayer
        visible={true}
        symbol="AAPL"
        moments={mockMoments}
        onAnalyticsEvent={onAnalytics}
      />
    );

    const closeButton = getByText('Close');
    fireEvent.press(closeButton);

    expect(onAnalytics).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'story_close',
        symbol: 'AAPL',
        totalMoments: 2,
      })
    );
  });

  it('calls onMomentChange when moment changes', async () => {
    const onMomentChange = jest.fn();
    render(
      <MomentStoryPlayer
        visible={true}
        symbol="AAPL"
        moments={mockMoments}
        enableIntro={false}
        initialIndex={0}
        onMomentChange={onMomentChange}
      />
    );

    await waitFor(() => {
      expect(onMomentChange).toHaveBeenCalledWith(mockMoments[0]);
    });
  });

  it('triggers haptic feedback on moment change', async () => {
    render(
      <MomentStoryPlayer
        visible={true}
        symbol="AAPL"
        moments={mockMoments}
        enableIntro={false}
        initialIndex={0}
      />
    );

    await waitFor(() => {
      expect(Haptics.impactAsync).toHaveBeenCalledWith(
        Haptics.ImpactFeedbackStyle.Light
      );
    });
  });

  it('toggles play/pause when play button is pressed', () => {
    const { getByText } = render(
      <MomentStoryPlayer
        visible={true}
        symbol="AAPL"
        moments={mockMoments}
        enableIntro={false}
        initialIndex={0}
      />
    );

    const playButton = getByText('Pause');
    fireEvent.press(playButton);

    expect(Speech.stop).toHaveBeenCalled();
    expect(getByText('Play')).toBeTruthy();
  });

  it('navigates to next moment when next button is pressed', () => {
    const onMomentChange = jest.fn();
    const { getByText } = render(
      <MomentStoryPlayer
        visible={true}
        symbol="AAPL"
        moments={mockMoments}
        enableIntro={false}
        initialIndex={0}
        onMomentChange={onMomentChange}
      />
    );

    const nextButton = getByText('▶');
    fireEvent.press(nextButton);

    expect(Speech.stop).toHaveBeenCalled();
    expect(onMomentChange).toHaveBeenCalledWith(mockMoments[1]);
  });

  it('navigates to previous moment when previous button is pressed', () => {
    const onMomentChange = jest.fn();
    const { getByText } = render(
      <MomentStoryPlayer
        visible={true}
        symbol="AAPL"
        moments={mockMoments}
        enableIntro={false}
        initialIndex={1}
        onMomentChange={onMomentChange}
      />
    );

    const prevButton = getByText('◀');
    fireEvent.press(prevButton);

    expect(Speech.stop).toHaveBeenCalled();
    expect(onMomentChange).toHaveBeenCalledWith(mockMoments[0]);
  });

  it('uses custom speakFn when provided', async () => {
    const speakFn = jest.fn().mockResolvedValue(undefined);
    render(
      <MomentStoryPlayer
        visible={true}
        symbol="AAPL"
        moments={mockMoments}
        enableIntro={false}
        initialIndex={0}
        speakFn={speakFn}
      />
    );

    await waitFor(() => {
      expect(speakFn).toHaveBeenCalledWith(
        mockMoments[0].deepSummary,
        mockMoments[0]
      );
      expect(Speech.speak).not.toHaveBeenCalled();
    });
  });

  it('uses custom stopFn when provided', () => {
    const stopFn = jest.fn();
    const { getByText } = render(
      <MomentStoryPlayer
        visible={true}
        symbol="AAPL"
        moments={mockMoments}
        stopFn={stopFn}
      />
    );

    const closeButton = getByText('Close');
    fireEvent.press(closeButton);

    expect(stopFn).toHaveBeenCalled();
  });

  it('tracks listened moments', async () => {
    const { getByText } = render(
      <MomentStoryPlayer
        visible={true}
        symbol="AAPL"
        moments={mockMoments}
        enableIntro={false}
        initialIndex={0}
      />
    );

    // Simulate speech completion
    const speakCall = (Speech.speak as jest.Mock).mock.calls[0];
    const onDone = speakCall[1].onDone;
    onDone();

    await waitFor(() => {
      // Should show listened count
      expect(getByText(/Listened 1\/2/)).toBeTruthy();
    });
  });

  it('shows success haptic when story completes', async () => {
    render(
      <MomentStoryPlayer
        visible={true}
        symbol="AAPL"
        moments={mockMoments}
        enableIntro={false}
        initialIndex={0}
      />
    );

    // Complete first moment
    const speakCall = (Speech.speak as jest.Mock).mock.calls[0];
    const onDone = speakCall[1].onDone;
    onDone();

    // Complete second moment
    await waitFor(() => {
      const secondCall = (Speech.speak as jest.Mock).mock.calls[1];
      if (secondCall) {
        secondCall[1].onDone();
      }
    });

    await waitFor(() => {
      expect(Haptics.notificationAsync).toHaveBeenCalledWith(
        Haptics.NotificationFeedbackType.Success
      );
    });
  });

  it('displays custom intro text when provided', () => {
    const customIntro = 'Custom intro text';
    const { getByText } = render(
      <MomentStoryPlayer
        visible={true}
        symbol="AAPL"
        moments={mockMoments}
        enableIntro={true}
        introText={customIntro}
      />
    );

    expect(getByText(customIntro)).toBeTruthy();
  });

  it('handles empty moments array', () => {
    const { getByText } = render(
      <MomentStoryPlayer
        visible={true}
        symbol="AAPL"
        moments={[]}
      />
    );

    expect(getByText('No moments')).toBeTruthy();
  });
});

