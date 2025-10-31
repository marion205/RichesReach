import { isExpoGo } from '../utils/expoGoCheck';
import { triggerHotword } from './VoiceHotword';

/**
 * Porcupine Wake Word Service
 * Handles "Hey Riches" wake word detection using Picovoice Porcupine
 * 
 * NOTE: This requires a development build - does NOT work in Expo Go
 */
class PorcupineWakeWordService {
  private porcupineManager: any = null;
  private isInitialized = false;
  private isStarted = false;

  /**
   * Initialize Porcupine with "Hey Riches" keyword
   */
  async initialize(): Promise<boolean> {
    if (isExpoGo()) {
      console.warn('⚠️ Porcupine wake word requires a development build, not Expo Go');
      return false;
    }

    if (this.isInitialized) {
      console.log('✅ Porcupine already initialized');
      return true;
    }

    try {
      // Dynamically import Porcupine (only works in dev builds)
      const { PorcupineManager } = require('@picovoice/porcupine-react-native');
      
      console.log('🎤 Initializing Porcupine wake word detection...');
      
      // Get Picovoice access key from environment or config
      // You need to sign up at https://console.picovoice.ai/ to get an access key
      const PICOVOICE_ACCESS_KEY = process.env.PICOVOICE_ACCESS_KEY || 'YOUR_ACCESS_KEY_HERE';
      
      if (PICOVOICE_ACCESS_KEY === 'YOUR_ACCESS_KEY_HERE') {
        console.warn('⚠️ PICOVOICE_ACCESS_KEY not set. Wake word detection will not work.');
        console.warn('📝 Sign up at https://console.picovoice.ai/ to get a free access key');
        return false;
      }

      // Initialize Porcupine Manager with "Hey Riches" keyword
      // Note: You'll need to create a custom keyword at https://console.picovoice.ai/
      // For now, we'll use a built-in keyword like "Hey Alexa" as fallback
      this.porcupineManager = await PorcupineManager.fromBuiltInKeywords(
        PICOVOICE_ACCESS_KEY,
        ['Hey Alexa'] // Fallback - replace with your custom "Hey Riches" keyword file path
      );

      // Set up keyword detection callback
      this.porcupineManager.on('keyword', () => {
        console.log('🎤 Wake word "Hey Riches" detected!');
        triggerHotword();
      });

      this.isInitialized = true;
      console.log('✅ Porcupine initialized successfully');
      return true;

    } catch (error) {
      console.error('❌ Failed to initialize Porcupine:', error);
      console.error('💡 Make sure:');
      console.error('   1. You have a development build (not Expo Go)');
      console.error('   2. @picovoice/porcupine-react-native is installed');
      console.error('   3. You have a valid PICOVOICE_ACCESS_KEY');
      console.error('   4. Microphone permissions are granted');
      return false;
    }
  }

  /**
   * Start listening for wake word
   */
  async start(): Promise<boolean> {
    if (!this.isInitialized) {
      const initialized = await this.initialize();
      if (!initialized) {
        return false;
      }
    }

    if (this.isStarted) {
      console.log('✅ Porcupine already started');
      return true;
    }

    try {
      await this.porcupineManager.start();
      this.isStarted = true;
      console.log('✅ Porcupine wake word detection started');
      return true;
    } catch (error) {
      console.error('❌ Failed to start Porcupine:', error);
      return false;
    }
  }

  /**
   * Stop listening for wake word
   */
  async stop(): Promise<void> {
    if (!this.isStarted) {
      return;
    }

    try {
      await this.porcupineManager.stop();
      this.isStarted = false;
      console.log('✅ Porcupine wake word detection stopped');
    } catch (error) {
      console.error('❌ Failed to stop Porcupine:', error);
    }
  }

  /**
   * Clean up and release resources
   */
  async release(): Promise<void> {
    if (this.isStarted) {
      await this.stop();
    }

    if (this.porcupineManager) {
      try {
        this.porcupineManager.delete();
        this.porcupineManager = null;
        this.isInitialized = false;
        console.log('✅ Porcupine released');
      } catch (error) {
        console.error('❌ Failed to release Porcupine:', error);
      }
    }
  }

  getStatus(): { initialized: boolean; started: boolean } {
    return {
      initialized: this.isInitialized,
      started: this.isStarted,
    };
  }
}

// Singleton instance
export const porcupineWakeWordService = new PorcupineWakeWordService();

