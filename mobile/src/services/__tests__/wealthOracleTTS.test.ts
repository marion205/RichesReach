/**
 * Unit Tests for Wealth Oracle TTS Service
 * Tests TTS API calls and audio playback
 */

import { Audio } from 'expo-av';
import { playWealthOracle, stopWealthOracle } from '../wealthOracleTTS';
import { StockMoment } from '../../components/charts/ChartWithMoments';
import { TTS_API_BASE_URL } from '../../config/api';

// Mock expo-av
jest.mock('expo-av', () => ({
  Audio: {
    Sound: {
      createAsync: jest.fn(),
    },
  },
}));

// Mock config
jest.mock('../../config/api', () => ({
  TTS_API_BASE_URL: 'http://localhost:8001',
}));

// Mock fetch
global.fetch = jest.fn();

describe('wealthOracleTTS', () => {
  const mockMoment: StockMoment = {
    id: '1',
    symbol: 'AAPL',
    timestamp: '2024-01-01T00:00:00Z',
    category: 'EARNINGS',
    title: 'Earnings Beat',
    quickSummary: 'Beat estimates',
    deepSummary: 'Detailed earnings analysis',
  };

  const mockSound = {
    stopAsync: jest.fn().mockResolvedValue(undefined),
    unloadAsync: jest.fn().mockResolvedValue(undefined),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (Audio.Sound.createAsync as jest.Mock).mockResolvedValue({
      sound: mockSound,
    });
  });

  it('calls TTS API with correct parameters', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        audio_url: 'http://localhost:8001/media/test.mp3',
      }),
    });

    await playWealthOracle('Test text', 'AAPL', mockMoment);

    expect(global.fetch).toHaveBeenCalledWith(
      `${TTS_API_BASE_URL}/tts`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: 'Test text',
          voice: 'wealth_oracle_v1',
          symbol: 'AAPL',
          moment_id: '1',
        }),
      }
    );
  });

  it('plays audio from returned URL', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        audio_url: 'http://localhost:8001/media/test.mp3',
      }),
    });

    await playWealthOracle('Test text', 'AAPL', mockMoment);

    expect(Audio.Sound.createAsync).toHaveBeenCalledWith(
      { uri: 'http://localhost:8001/media/test.mp3' },
      { shouldPlay: true }
    );
  });

  it('stops current sound before playing new one', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        audio_url: 'http://localhost:8001/media/test1.mp3',
      }),
    });

    // First call
    await playWealthOracle('Text 1', 'AAPL', mockMoment);

    // Second call should stop first
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        audio_url: 'http://localhost:8001/media/test2.mp3',
      }),
    });

    await playWealthOracle('Text 2', 'AAPL', mockMoment);

    expect(mockSound.stopAsync).toHaveBeenCalled();
    expect(mockSound.unloadAsync).toHaveBeenCalled();
  });

  it('handles TTS API errors gracefully', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 500,
    });

    await expect(
      playWealthOracle('Test text', 'AAPL', mockMoment)
    ).resolves.not.toThrow();

    expect(Audio.Sound.createAsync).not.toHaveBeenCalled();
  });

  it('handles missing audio_url in response', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({}), // Missing audio_url
    });

    await expect(
      playWealthOracle('Test text', 'AAPL', mockMoment)
    ).resolves.not.toThrow();

    expect(Audio.Sound.createAsync).not.toHaveBeenCalled();
  });

  it('handles network errors gracefully', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(
      new Error('Network error')
    );

    await expect(
      playWealthOracle('Test text', 'AAPL', mockMoment)
    ).resolves.not.toThrow();
  });

  it('stops current sound when stopWealthOracle is called', async () => {
    // First play to set current sound
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        audio_url: 'http://localhost:8001/media/test.mp3',
      }),
    });

    await playWealthOracle('Test text', 'AAPL', mockMoment);

    // Now stop
    await stopWealthOracle();

    expect(mockSound.stopAsync).toHaveBeenCalled();
    expect(mockSound.unloadAsync).toHaveBeenCalled();
  });

  it('handles stop when no sound is playing', async () => {
    await expect(stopWealthOracle()).resolves.not.toThrow();
  });

  it('handles stop errors gracefully', async () => {
    mockSound.stopAsync.mockRejectedValue(new Error('Stop error'));

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        audio_url: 'http://localhost:8001/media/test.mp3',
      }),
    });

    await playWealthOracle('Test text', 'AAPL', mockMoment);

    await expect(stopWealthOracle()).resolves.not.toThrow();
  });
});

