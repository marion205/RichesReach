/**
 * ML-Based Wake Word Service
 * Uses TensorFlow.js model for on-device "Hey Riches" detection
 */

import { Audio } from 'expo-av';
import { triggerHotword } from './VoiceHotword';
import { extractMFCC } from '../utils/audioFeatures';
import { Platform } from 'react-native';
import { Asset } from 'expo-asset';

// Model configuration
const MODEL_PATH = '../assets/models/wake_word_model'; // Path to TensorFlow.js model
const DETECTION_THRESHOLD = 0.7; // Confidence threshold
const CHECK_INTERVAL = 500; // Check every 500ms (faster than Whisper)
const AUDIO_CHUNK_DURATION = 1.0; // 1 second chunks
const SAMPLE_RATE = 16000;

class MLWakeWordService {
  private recording: Audio.Recording | null = null;
  private isListening = false;
  private checkInterval: NodeJS.Timeout | null = null;
  private hasPermission = false;
  private model: any = null;
  private normalizationParams: { mean: number[]; std: number[] } | null = null;
  private audioContext: AudioContext | null = null;

  /**
   * Load TensorFlow.js model
   */
  async loadModel(): Promise<boolean> {
    try {
      // Dynamic import to avoid loading if not needed
      const tf = await import('@tensorflow/tfjs');
      await tf.ready();

      // Try to load model (if available)
      try {
        // Model would be bundled with app or loaded from server
        const modelUrl = Platform.select({
          ios: require('../../assets/models/wake_word_model/model.json'),
          android: require('../../assets/models/wake_word_model/model.json'),
          default: null,
        });

        if (modelUrl) {
          this.model = await tf.loadLayersModel(modelUrl);
          console.log('✅ ML wake word model loaded');
        } else {
          // Fallback: try loading from URL
          const modelUrl2 = 'http://localhost:8000/media/models/wake_word_model/model.json';
          try {
            this.model = await tf.loadLayersModel(modelUrl2);
            console.log('✅ ML wake word model loaded from server');
          } catch (e) {
            console.warn('⚠️ ML model not found, will use fallback detection');
            return false;
          }
        }

        // Load normalization parameters
        await this.loadNormalizationParams();

        return true;
      } catch (error) {
        console.warn('ML model not available:', error);
        return false;
      }
    } catch (error) {
      console.warn('TensorFlow.js not available:', error);
      return false;
    }
  }

  /**
   * Load normalization parameters
   */
  async loadNormalizationParams(): Promise<void> {
    try {
      const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/wake-word/normalization/`);
      
      if (response.ok) {
        this.normalizationParams = await response.json();
      }
    } catch (error) {
      console.warn('Could not load normalization params:', error);
    }
  }

  /**
   * Request microphone permissions
   */
  async requestPermissions(): Promise<boolean> {
    try {
      const { status } = await Audio.requestPermissionsAsync();
      this.hasPermission = status === 'granted';
      return this.hasPermission;
    } catch (error) {
      console.error('Permission request error:', error);
      return false;
    }
  }

  /**
   * Start wake word detection
   */
  async start(): Promise<boolean> {
    if (this.isListening) {
      return true;
    }

    if (!this.hasPermission) {
      const granted = await this.requestPermissions();
      if (!granted) {
        return false;
      }
    }

    // Try to load model
    const modelLoaded = await this.loadModel();
    if (!modelLoaded) {
      console.log('⚠️ ML model not available, using pattern matching fallback');
    }

    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        staysActiveInBackground: false,
      });

      const recording = new Audio.Recording();
      
      await recording.prepareToRecordAsync({
        android: {
          extension: '.m4a',
          outputFormat: Audio.RECORDING_OPTION_ANDROID_OUTPUT_FORMAT_MPEG_4,
          audioEncoder: Audio.RECORDING_OPTION_ANDROID_AUDIO_ENCODER_AAC,
          sampleRate: SAMPLE_RATE,
          numberOfChannels: 1,
          bitRate: 128000,
        },
        ios: {
          extension: '.m4a',
          outputFormat: Audio.RECORDING_OPTION_IOS_OUTPUT_FORMAT_MPEG4AAC,
          audioQuality: Audio.RECORDING_OPTION_IOS_AUDIO_QUALITY_MEDIUM,
          sampleRate: SAMPLE_RATE,
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

      console.log('✅ ML wake word detection started');
      return true;

    } catch (error: any) {
      console.error('❌ Failed to start ML wake word detection:', error);
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
        const detected = await this.checkAudioChunk();
        
        if (detected) {
          console.log('🎤 "Hey Riches" detected via ML model!');
          triggerHotword();
          
          // Small pause before continuing
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      } catch (error) {
        console.error('Error checking for wake word:', error);
      }
    }, CHECK_INTERVAL);
  }

  /**
   * Check audio chunk for wake word
   */
  private async checkAudioChunk(): Promise<boolean> {
    try {
      if (!this.recording) {
        return false;
      }

      // Get current recording status
      const status = await this.recording.getStatusAsync();
      
      if (!status.isRecording || !status.metering) {
        return false;
      }

      // Extract features from audio buffer
      // Note: This is simplified - in production, you'd extract actual audio data
      const audioData = await this.extractAudioData();
      
      if (!audioData) {
        return false;
      }

      // If ML model is available, use it
      if (this.model) {
        return await this.detectWithModel(audioData);
      } else {
        // Fallback: pattern matching (simplified)
        return this.detectWithPatternMatching(audioData);
      }

    } catch (error) {
      console.error('Error checking audio chunk:', error);
      return false;
    }
  }

  /**
   * Extract audio data from recording
   */
  private async extractAudioData(): Promise<Float32Array | null> {
    try {
      // This is a placeholder - actual implementation would:
      // 1. Get audio buffer from recording
      // 2. Convert to Float32Array
      // 3. Downsample to 16kHz if needed
      
      // For now, we'll need to use a different approach
      // Since expo-av doesn't expose raw audio buffers directly,
      // we might need to record to file and process it
      
      return null; // Placeholder
    } catch (error) {
      console.error('Error extracting audio data:', error);
      return null;
    }
  }

  /**
   * Detect wake word using ML model
   */
  private async detectWithModel(audioData: Float32Array): Promise<boolean> {
    try {
      const tf = await import('@tensorflow/tfjs');
      
      // Extract MFCC features
      const mfccFeatures = extractMFCC(audioData, SAMPLE_RATE);
      
      // Normalize features
      let normalizedFeatures = mfccFeatures;
      if (this.normalizationParams) {
        normalizedFeatures = mfccFeatures.map((val, idx) => {
          const mean = this.normalizationParams!.mean[idx] || 0;
          const std = this.normalizationParams!.std[idx] || 1;
          return (val - mean) / (std + 1e-8);
        });
      }

      // Convert to tensor
      const inputTensor = tf.tensor2d([normalizedFeatures]);

      // Predict
      const prediction = this.model.predict(inputTensor) as any;
      const confidence = await prediction.data();
      
      // Cleanup
      inputTensor.dispose();
      prediction.dispose();

      // Check threshold
      return confidence[0] > DETECTION_THRESHOLD;

    } catch (error) {
      console.error('ML detection error:', error);
      return false;
    }
  }

  /**
   * Fallback pattern matching detection
   */
  private detectWithPatternMatching(audioData: Float32Array): boolean {
    // Simple energy-based detection
    let energy = 0;
    for (let i = 0; i < audioData.length; i++) {
      energy += Math.abs(audioData[i]);
    }
    energy = energy / audioData.length;

    // Basic threshold (this is very simplified)
    return energy > 0.1;
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
          const status = await this.recording.getStatusAsync();
          if (status.isRecording) {
            await this.recording.stopAndUnloadAsync();
          } else {
            await this.recording.unloadAsync();
          }
        } catch (e) {
          // Try to unload even if stop failed
          try {
            await this.recording.unloadAsync();
          } catch (e2) {
            console.warn('Could not unload recording:', e2);
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

      console.log('✅ ML wake word detection stopped');
    } catch (error) {
      console.error('Failed to stop ML wake word detection:', error);
      // Ensure recording is null even on error
      this.recording = null;
      this.isListening = false;
    }
  }

  getStatus(): { listening: boolean; hasPermission: boolean; modelLoaded: boolean } {
    return {
      listening: this.isListening,
      hasPermission: this.hasPermission,
      modelLoaded: this.model !== null,
    };
  }
}

// Singleton instance
export const mlWakeWordService = new MLWakeWordService();

