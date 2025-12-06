/**
 * ML-Based Wake Word Service
 * Uses TensorFlow.js model for on-device "Hey Riches" detection
 */

import { Audio } from 'expo-av';
import { triggerHotword } from './VoiceHotword';
import { extractMFCC } from '../utils/audioFeatures';
import { Platform } from 'react-native';
import { Asset } from 'expo-asset';
import logger from '../utils/logger';

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
          logger.log('✅ ML wake word model loaded');
        } else {
          // Fallback: try loading from URL
          try {
            // Use centralized API config for model URL
            const { API_BASE } = await import('../config/api');
            const modelUrl2 = `${API_BASE}/media/models/wake_word_model/model.json`;
            this.model = await tf.loadLayersModel(modelUrl2);
            logger.log('✅ ML wake word model loaded from server');
          } catch (e) {
            logger.warn('⚠️ ML model not found, will use fallback detection');
            return false;
          }
        }

        // Load normalization parameters
        await this.loadNormalizationParams();

        return true;
      } catch (error) {
        logger.warn('ML model not available:', error);
        return false;
      }
    } catch (error) {
      logger.warn('TensorFlow.js not available:', error);
      return false;
    }
  }

  /**
   * Load normalization parameters
   */
  async loadNormalizationParams(): Promise<void> {
    try {
      // Use centralized API config which handles device detection
      const { API_BASE } = await import('../config/api');
      const API_BASE_URL = API_BASE;
      const response = await fetch(`${API_BASE_URL}/api/wake-word/normalization/`);
      
      if (response.ok) {
        this.normalizationParams = await response.json();
      }
    } catch (error) {
      logger.warn('Could not load normalization params:', error);
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
      logger.error('Permission request error:', error);
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
      logger.log('⚠️ ML model not available, using pattern matching fallback');
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

      logger.log('✅ ML wake word detection started');
      return true;

    } catch (error: any) {
      logger.error('❌ Failed to start ML wake word detection:', error);
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
          logger.log('🎤 "Hey Riches" detected via ML model!');
          triggerHotword();
          
          // Small pause before continuing
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      } catch (error) {
        logger.error('Error checking for wake word:', error);
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
      logger.error('Error checking audio chunk:', error);
      return false;
    }
  }

  /**
   * Extract audio data from recording
   */
  private async extractAudioData(): Promise<Float32Array | null> {
    try {
      if (!this.recording) {
        return null;
      }

      // Get recording status to access URI
      const status = await this.recording.getStatusAsync();
      if (!status.isRecording && status.uri) {
        // For React Native, we'll use a Web Audio API approach via a bridge
        // or use expo-audio-processing if available
        // For now, implement a file-based approach
        
        // Read audio file and convert to Float32Array
        // This requires native module or file system access
        const response = await fetch(status.uri);
        const arrayBuffer = await response.arrayBuffer();
        
        // Convert to Float32Array (simplified - actual implementation would decode audio)
        // For MP3/WAV files, you'd need an audio decoder
        const audioData = new Float32Array(arrayBuffer.byteLength / 4);
        const view = new DataView(arrayBuffer);
        
        for (let i = 0; i < audioData.length; i++) {
          audioData[i] = view.getFloat32(i * 4, true);
        }
        
        // Downsample to 16kHz if needed (simplified)
        if (this.sampleRate !== SAMPLE_RATE) {
          return this.downsample(audioData, this.sampleRate, SAMPLE_RATE);
        }
        
        return audioData;
      }
      
      return null;
    } catch (error) {
      logger.error('Error extracting audio data:', error);
      return null;
    }
  }

  /**
   * Downsample audio data
   */
  private downsample(buffer: Float32Array, fromSampleRate: number, toSampleRate: number): Float32Array {
    if (fromSampleRate === toSampleRate) {
      return buffer;
    }
    
    const sampleRateRatio = fromSampleRate / toSampleRate;
    const newLength = Math.round(buffer.length / sampleRateRatio);
    const result = new Float32Array(newLength);
    let offsetResult = 0;
    let offsetBuffer = 0;
    
    while (offsetResult < result.length) {
      const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
      let accum = 0;
      let count = 0;
      
      for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
        accum += buffer[i];
        count++;
      }
      
      result[offsetResult] = accum / count;
      offsetResult++;
      offsetBuffer = nextOffsetBuffer;
    }
    
    return result;
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
      logger.error('ML detection error:', error);
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
          // Check if recording object has the required methods
          if (typeof this.recording.getStatusAsync === 'function') {
            const status = await this.recording.getStatusAsync();
            if (status.isRecording && typeof this.recording.stopAndUnloadAsync === 'function') {
              await this.recording.stopAndUnloadAsync();
            } else if (typeof this.recording.unloadAsync === 'function') {
              await this.recording.unloadAsync();
            }
          } else if (typeof this.recording.unloadAsync === 'function') {
            // If getStatusAsync doesn't exist, try to unload directly
            await this.recording.unloadAsync();
          }
        } catch (e) {
          // Try to unload even if stop failed
          if (this.recording && typeof this.recording.unloadAsync === 'function') {
            try {
              await this.recording.unloadAsync();
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

      logger.log('✅ ML wake word detection stopped');
    } catch (error) {
      logger.error('Failed to stop ML wake word detection:', error);
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

