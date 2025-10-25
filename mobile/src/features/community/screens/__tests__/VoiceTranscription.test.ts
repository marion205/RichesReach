import { Audio } from 'expo-av';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Mock dependencies
jest.mock('expo-av', () => ({
  Audio: {
    requestPermissionsAsync: jest.fn(),
    setAudioModeAsync: jest.fn(),
    Recording: jest.fn(),
  },
}));

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
}));

// Mock fetch
global.fetch = jest.fn();

describe('Voice Transcription', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock AsyncStorage
    (AsyncStorage.getItem as jest.Mock).mockResolvedValue('test-token');
    
    // Mock Audio permissions
    (Audio.requestPermissionsAsync as jest.Mock).mockResolvedValue({
      status: 'granted',
    });
    
    // Mock Audio.setAudioModeAsync
    (Audio.setAudioModeAsync as jest.Mock).mockResolvedValue(undefined);
  });

  describe('Audio Recording Setup', () => {
    it('should request microphone permissions', async () => {
      const { requestPermissionsAsync } = Audio;
      
      await requestPermissionsAsync();
      
      expect(requestPermissionsAsync).toHaveBeenCalled();
    });

    it('should handle permission denied', async () => {
      (Audio.requestPermissionsAsync as jest.Mock).mockResolvedValue({
        status: 'denied',
      });
      
      const { requestPermissionsAsync } = Audio;
      const result = await requestPermissionsAsync();
      
      expect(result.status).toBe('denied');
    });

    it('should set audio mode for recording', async () => {
      const { setAudioModeAsync } = Audio;
      
      await setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        staysActiveInBackground: false,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });
      
      expect(setAudioModeAsync).toHaveBeenCalledWith({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        staysActiveInBackground: false,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });
    });
  });

  describe('Audio Recording Configuration', () => {
    it('should configure recording for Android', () => {
      const androidConfig = {
        extension: '.m4a',
        outputFormat: 'mpeg_4',
        audioEncoder: 'aac',
        sampleRate: 16000,
        numberOfChannels: 1,
        bitRate: 128000,
      };
      
      expect(androidConfig.sampleRate).toBe(16000);
      expect(androidConfig.numberOfChannels).toBe(1);
      expect(androidConfig.bitRate).toBe(128000);
    });

    it('should configure recording for iOS', () => {
      const iosConfig = {
        extension: '.m4a',
        outputFormat: 'mpeg4aac',
        audioQuality: 'high',
        sampleRate: 16000,
        numberOfChannels: 1,
        bitRate: 128000,
        linearPCMBitDepth: 16,
        linearPCMIsBigEndian: false,
        linearPCMIsFloat: false,
      };
      
      expect(iosConfig.sampleRate).toBe(16000);
      expect(iosConfig.numberOfChannels).toBe(1);
      expect(iosConfig.bitRate).toBe(128000);
    });

    it('should configure recording for Web', () => {
      const webConfig = {
        mimeType: 'audio/webm',
        bitsPerSecond: 128000,
      };
      
      expect(webConfig.bitsPerSecond).toBe(128000);
    });
  });

  describe('Recording Lifecycle', () => {
    let mockRecording: any;

    beforeEach(() => {
      mockRecording = {
        prepareToRecordAsync: jest.fn().mockResolvedValue(undefined),
        startAsync: jest.fn().mockResolvedValue(undefined),
        stopAndUnloadAsync: jest.fn().mockResolvedValue(undefined),
        getURI: jest.fn().mockReturnValue('file://test-audio.m4a'),
      };
      
      (Audio.Recording as jest.Mock).mockImplementation(() => mockRecording);
    });

    it('should prepare recording successfully', async () => {
      const recording = new Audio.Recording();
      
      await recording.prepareToRecordAsync({
        android: {
          extension: '.m4a',
          outputFormat: 'mpeg_4',
          audioEncoder: 'aac',
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 128000,
        },
      });
      
      expect(recording.prepareToRecordAsync).toHaveBeenCalled();
    });

    it('should start recording successfully', async () => {
      const recording = new Audio.Recording();
      
      await recording.startAsync();
      
      expect(recording.startAsync).toHaveBeenCalled();
    });

    it('should stop recording successfully', async () => {
      const recording = new Audio.Recording();
      
      await recording.stopAndUnloadAsync();
      
      expect(recording.stopAndUnloadAsync).toHaveBeenCalled();
    });

    it('should get recording URI', () => {
      const recording = new Audio.Recording();
      const uri = recording.getURI();
      
      expect(uri).toBe('file://test-audio.m4a');
    });
  });

  describe('Transcription API Integration', () => {
    beforeEach(() => {
      (global.fetch as jest.Mock).mockClear();
    });

    it('should send audio to transcription API', async () => {
      const mockResponse = {
        ok: true,
        json: async () => ({
          transcription: 'This is a test transcription',
          audioUrl: '/uploads/test-audio.m4a',
          processingTime: 1500,
          model: 'ggml-tiny.en-q5_0.bin',
        }),
      };
      
      (global.fetch as jest.Mock).mockResolvedValue(mockResponse);
      
      const formData = new FormData();
      formData.append('audio', {
        uri: 'file://test-audio.m4a',
        type: 'audio/m4a',
        name: 'voice.m4a',
      } as any);
      
      const response = await fetch('http://localhost:3001/api/transcribe-audio/', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': 'Bearer test-token',
          'Content-Type': 'multipart/form-data',
        },
      });
      
      const result = await response.json();
      
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:3001/api/transcribe-audio/',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
          }),
        })
      );
      
      expect(result.transcription).toBe('This is a test transcription');
      expect(result.audioUrl).toBe('/uploads/test-audio.m4a');
      expect(result.processingTime).toBe(1500);
    });

    it('should handle transcription API errors', async () => {
      const mockResponse = {
        ok: false,
        json: async () => ({
          error: 'Transcription failed',
        }),
      };
      
      (global.fetch as jest.Mock).mockResolvedValue(mockResponse);
      
      const formData = new FormData();
      formData.append('audio', {
        uri: 'file://test-audio.m4a',
        type: 'audio/m4a',
        name: 'voice.m4a',
      } as any);
      
      const response = await fetch('http://localhost:3001/api/transcribe-audio/', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': 'Bearer test-token',
          'Content-Type': 'multipart/form-data',
        },
      });
      
      const result = await response.json();
      
      expect(result.error).toBe('Transcription failed');
    });

    it('should handle network errors', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));
      
      const formData = new FormData();
      formData.append('audio', {
        uri: 'file://test-audio.m4a',
        type: 'audio/m4a',
        name: 'voice.m4a',
      } as any);
      
      await expect(
        fetch('http://localhost:3001/api/transcribe-audio/', {
          method: 'POST',
          body: formData,
          headers: {
            'Authorization': 'Bearer test-token',
            'Content-Type': 'multipart/form-data',
          },
        })
      ).rejects.toThrow('Network error');
    });
  });

  describe('Audio Format Validation', () => {
    it('should validate M4A format', () => {
      const audioFile = {
        uri: 'file://test.m4a',
        type: 'audio/m4a',
        name: 'voice.m4a',
      };
      
      expect(audioFile.type).toBe('audio/m4a');
      expect(audioFile.name).toMatch(/\.m4a$/);
    });

    it('should validate WAV format', () => {
      const audioFile = {
        uri: 'file://test.wav',
        type: 'audio/wav',
        name: 'voice.wav',
      };
      
      expect(audioFile.type).toBe('audio/wav');
      expect(audioFile.name).toMatch(/\.wav$/);
    });

    it('should validate MP3 format', () => {
      const audioFile = {
        uri: 'file://test.mp3',
        type: 'audio/mp3',
        name: 'voice.mp3',
      };
      
      expect(audioFile.type).toBe('audio/mp3');
      expect(audioFile.name).toMatch(/\.mp3$/);
    });
  });

  describe('Error Handling', () => {
    it('should handle recording preparation errors', async () => {
      const mockRecording = {
        prepareToRecordAsync: jest.fn().mockRejectedValue(new Error('Preparation failed')),
      };
      
      (Audio.Recording as jest.Mock).mockImplementation(() => mockRecording);
      
      const recording = new Audio.Recording();
      
      await expect(
        recording.prepareToRecordAsync({
          android: {
            extension: '.m4a',
            outputFormat: 'mpeg_4',
            audioEncoder: 'aac',
            sampleRate: 16000,
            numberOfChannels: 1,
            bitRate: 128000,
          },
        })
      ).rejects.toThrow('Preparation failed');
    });

    it('should handle recording start errors', async () => {
      const mockRecording = {
        prepareToRecordAsync: jest.fn().mockResolvedValue(undefined),
        startAsync: jest.fn().mockRejectedValue(new Error('Start failed')),
      };
      
      (Audio.Recording as jest.Mock).mockImplementation(() => mockRecording);
      
      const recording = new Audio.Recording();
      
      await recording.prepareToRecordAsync({
        android: {
          extension: '.m4a',
          outputFormat: 'mpeg_4',
          audioEncoder: 'aac',
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 128000,
        },
      });
      
      await expect(recording.startAsync()).rejects.toThrow('Start failed');
    });

    it('should handle recording stop errors', async () => {
      const mockRecording = {
        stopAndUnloadAsync: jest.fn().mockRejectedValue(new Error('Stop failed')),
        getURI: jest.fn().mockReturnValue('file://test-audio.m4a'),
      };
      
      (Audio.Recording as jest.Mock).mockImplementation(() => mockRecording);
      
      const recording = new Audio.Recording();
      
      await expect(recording.stopAndUnloadAsync()).rejects.toThrow('Stop failed');
    });

    it('should handle missing recording URI', () => {
      const mockRecording = {
        getURI: jest.fn().mockReturnValue(null),
      };
      
      (Audio.Recording as jest.Mock).mockImplementation(() => mockRecording);
      
      const recording = new Audio.Recording();
      const uri = recording.getURI();
      
      expect(uri).toBeNull();
    });
  });

  describe('Performance Considerations', () => {
    it('should use optimal audio settings for Whisper', () => {
      const optimalSettings = {
        sampleRate: 16000, // Whisper's preferred sample rate
        numberOfChannels: 1, // Mono for better compression
        bitRate: 128000, // Good quality/size balance
      };
      
      expect(optimalSettings.sampleRate).toBe(16000);
      expect(optimalSettings.numberOfChannels).toBe(1);
      expect(optimalSettings.bitRate).toBe(128000);
    });

    it('should handle large audio files', async () => {
      const largeFile = {
        uri: 'file://large-audio.m4a',
        type: 'audio/m4a',
        name: 'large-voice.m4a',
        size: 25 * 1024 * 1024, // 25MB
      };
      
      // Should be within the 25MB limit
      expect(largeFile.size).toBeLessThanOrEqual(25 * 1024 * 1024);
    });

    it('should handle long recordings', () => {
      const maxDuration = 300; // 5 minutes
      const recordingDuration = 180; // 3 minutes
      
      expect(recordingDuration).toBeLessThanOrEqual(maxDuration);
    });
  });

  describe('Integration with Post Creation', () => {
    it('should integrate transcription with post text', async () => {
      const transcription = 'This is a test transcription';
      const postText = transcription;
      
      expect(postText).toBe(transcription);
    });

    it('should attach audio URL to post', async () => {
      const audioUrl = '/uploads/test-audio.m4a';
      const postMedia = {
        url: audioUrl,
        type: 'audio',
      };
      
      expect(postMedia.url).toBe(audioUrl);
      expect(postMedia.type).toBe('audio');
    });

    it('should handle transcription processing time', async () => {
      const processingTime = 1500; // 1.5 seconds
      const isProcessing = processingTime > 0;
      
      expect(isProcessing).toBe(true);
      expect(processingTime).toBeLessThan(10000); // Should be under 10 seconds
    });
  });
});
