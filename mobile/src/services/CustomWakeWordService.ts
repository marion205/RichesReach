/**
 * Custom Wake Word Service
 * Uses continuous audio recording + Whisper for "Hey Riches" detection
 * No external API required - uses your existing Whisper server
 */

import { Audio } from 'expo-av';
import { triggerHotword } from './VoiceHotword';
import { Platform } from 'react-native';
import logger from '../utils/logger';

const WHISPER_API_URL = process.env.EXPO_PUBLIC_WHISPER_API_URL || 'http://localhost:3001';
const WAKE_WORD = 'hey riches';
const CHECK_INTERVAL = 3000; // Check every 3 seconds
const MIN_CONFIDENCE = 0.7; // Minimum confidence threshold

class CustomWakeWordService {
  private recording: Audio.Recording | null = null;
  private isListening = false;
  private checkInterval: NodeJS.Timeout | null = null;
  private hasPermission = false;

  /**
   * Request microphone permissions
   */
  async requestPermissions(): Promise<boolean> {
    try {
      const { status } = await Audio.requestPermissionsAsync();
      this.hasPermission = status === 'granted';
      
      if (!this.hasPermission) {
        logger.warn('⚠️ Microphone permission not granted for wake word detection');
      }
      
      return this.hasPermission;
    } catch (error) {
      logger.error('Permission request error:', error);
      return false;
    }
  }

  /**
   * Start continuous recording and checking for wake word
   */
  async start(): Promise<boolean> {
    if (this.isListening) {
      logger.log('✅ Wake word detection already active');
      return true;
    }

    if (!this.hasPermission) {
      const granted = await this.requestPermissions();
      if (!granted) {
        return false;
      }
    }

    try {
      logger.log('🎤 Starting custom wake word detection...');
      
      // Configure audio recording for wake word detection
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        staysActiveInBackground: false,
      });

      // Start continuous recording
      const recording = new Audio.Recording();
      
      await recording.prepareToRecordAsync({
        android: {
          extension: '.m4a',
          outputFormat: 2, // Audio.RECORDING_OPTION_ANDROID_OUTPUT_FORMAT_MPEG_4
          audioEncoder: 3, // Audio.RECORDING_OPTION_ANDROID_AUDIO_ENCODER_AAC
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 128000,
        },
        ios: {
          extension: '.m4a',
          outputFormat: 0, // Audio.RECORDING_OPTION_IOS_OUTPUT_FORMAT_MPEG4AAC
          audioQuality: 127, // Audio.RECORDING_OPTION_IOS_AUDIO_QUALITY_MEDIUM
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 128000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
        web: {
          mimeType: 'audio/webm',
          bitsPerSecond: 128000,
        },
      });

      await recording.startAsync();
      this.recording = recording;
      this.isListening = true;

      // Start periodic checking
      this.startPeriodicCheck();

      logger.log('✅ Custom wake word detection started');
      return true;

    } catch (error) {
      logger.error('❌ Failed to start wake word detection:', error);
      this.isListening = false;
      return false;
    }
  }

  /**
   * Periodically check audio chunks for wake word
   */
  private startPeriodicCheck(): void {
    this.checkInterval = setInterval(async () => {
      if (!this.isListening || !this.recording) {
        return;
      }

      try {
        // Get current recording URI
        const uri = this.recording.getURI();
        if (!uri) {
          return;
        }

        // Send to Whisper for transcription
        const transcript = await this.transcribeAudio(uri);
        
        if (transcript) {
          // Check if wake word is in transcript
          const detected = this.detectWakeWord(transcript);
          
          if (detected) {
            logger.log('🎤 "Hey Riches" detected in transcript:', transcript);
            triggerHotword();
            
            // Restart recording for next check
            await this.restartRecording();
          }
        }
      } catch (error) {
        logger.error('Error checking for wake word:', error);
      }
    }, CHECK_INTERVAL);
  }

  /**
   * Transcribe audio using Whisper server
   */
  private async transcribeAudio(uri: string): Promise<string | null> {
    try {
      // Create FormData
      const formData = new FormData();
      formData.append('audio', {
        uri: uri,
        type: 'audio/m4a',
        name: 'wake_word_check.m4a',
      } as any);

      const response = await fetch(`${WHISPER_API_URL}/api/transcribe-audio/`, {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (!response.ok) {
        return null;
      }

      const data = await response.json();
      return data.transcript?.toLowerCase() || null;

    } catch (error) {
      // Silently handle network errors - Whisper API may not be running
      // The calling code should handle null gracefully
      // Only log if it's not a network error (unexpected errors)
      if (error instanceof TypeError && error.message === 'Network request failed') {
        // Expected - Whisper API not available, don't log
        return null;
      }
      logger.error('Transcription error:', error);
      return null;
    }
  }

  /**
   * Detect wake word in transcript
   */
  private detectWakeWord(transcript: string): boolean {
    if (!transcript) {
      return false;
    }

    const normalized = transcript.toLowerCase().trim();
    
    // Simple keyword matching
    if (normalized.includes(WAKE_WORD)) {
      return true;
    }

    // Fuzzy matching for variations
    const variations = [
      'hey rich',
      'hey riches',
      'hey reach',
      'hey rich is',
      'hey riches is',
    ];

    for (const variation of variations) {
      if (normalized.includes(variation)) {
        return true;
      }
    }

    return false;
  }

  /**
   * Restart recording after wake word detected
   */
  private async restartRecording(): Promise<void> {
    try {
      if (this.recording) {
        await this.recording.stopAndUnloadAsync();
        this.recording = null;
      }

      // Small delay before restarting
      await new Promise(resolve => setTimeout(resolve, 500));

      // Start new recording
      const recording = new Audio.Recording();
      await recording.prepareToRecordAsync({
        android: {
          extension: '.m4a',
          outputFormat: 2, // Audio.RECORDING_OPTION_ANDROID_OUTPUT_FORMAT_MPEG_4
          audioEncoder: 3, // Audio.RECORDING_OPTION_ANDROID_AUDIO_ENCODER_AAC
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 128000,
        },
        ios: {
          extension: '.m4a',
          outputFormat: 0, // Audio.RECORDING_OPTION_IOS_OUTPUT_FORMAT_MPEG4AAC
          audioQuality: 127, // Audio.RECORDING_OPTION_IOS_AUDIO_QUALITY_MEDIUM
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 128000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
        web: {
          mimeType: 'audio/webm',
          bitsPerSecond: 128000,
        },
      });

      await recording.startAsync();
      this.recording = recording;

    } catch (error) {
      logger.error('Failed to restart recording:', error);
    }
  }

  /**
   * Stop wake word detection
   */
  async stop(): Promise<void> {
    if (!this.isListening && !this.recording) {
      return;
    }

    try {
      this.isListening = false;

      if (this.checkInterval) {
        clearInterval(this.checkInterval);
        this.checkInterval = null;
      }

      if (this.recording) {
        try {
          // Check if recording object has the required methods
          if (typeof this.recording.getStatusAsync === 'function') {
            const status = await this.recording.getStatusAsync();
            if (status.isRecording && typeof this.recording.stopAndUnloadAsync === 'function') {
              await this.recording.stopAndUnloadAsync();
            } else if (this.recording) {
              await (this.recording as any).stopAndUnloadAsync?.();
            }
          } else if (this.recording) {
            // If getStatusAsync doesn't exist, try to stop and unload directly
            await (this.recording as any).stopAndUnloadAsync?.();
          }
        } catch (e) {
          // Try to stop and unload even if stop failed
          if (this.recording) {
            try {
              await (this.recording as any).stopAndUnloadAsync?.();
            } catch (e2) {
              logger.warn('Could not unload recording:', e2);
            }
          }
        }
        this.recording = null;
      }

      // Wait for recording to be fully released
      await new Promise(resolve => setTimeout(resolve, 500));

      // Reset audio mode to ensure clean state
      try {
        await Audio.setAudioModeAsync({
          allowsRecordingIOS: false,
          playsInSilentModeIOS: false,
          staysActiveInBackground: false,
        });
      } catch (e) {
        // Ignore errors
      }

      logger.log('✅ Wake word detection stopped');
    } catch (error) {
      logger.error('Failed to stop wake word detection:', error);
      // Ensure recording is null even on error
      this.recording = null;
      this.isListening = false;
    }
  }

  /**
   * Get current status
   */
  getStatus(): { listening: boolean; hasPermission: boolean } {
    return {
      listening: this.isListening,
      hasPermission: this.hasPermission,
    };
  }
}

// Singleton instance
export const customWakeWordService = new CustomWakeWordService();

