import { isExpoGo } from '../utils/expoGoCheck';
import { triggerHotword } from './VoiceHotword';
import logger from '../utils/logger';

/**
 * Porcupine Wake Word Service
 * Handles "Hey Riches" wake word detection using Picovoice Porcupine
 * 
 * NOTE: This requires a development build - does NOT work in Expo Go
 * NOTE: Requires @picovoice/react-native-voice-processor to be installed
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
      logger.warn('⚠️ Porcupine wake word requires a development build, not Expo Go');
      return false;
    }

    if (this.isInitialized) {
      logger.log('✅ Porcupine already initialized');
      return true;
    }

    try {
      // Import Porcupine - dependency is now installed
      let PorcupineManager: any;
      
      try {
        // Try to require Porcupine - should work now that dependencies are installed
        const porcupineModule = require('@picovoice/porcupine-react-native');
        PorcupineManager = porcupineModule?.PorcupineManager;
      } catch (importError: any) {
        // Handle any import errors gracefully
        const errorMsg = importError?.message || String(importError);
        if (errorMsg.includes('@picovoice/react-native-voice-processor') || 
            errorMsg.includes('MODULE_NOT_FOUND') ||
            errorMsg.includes('Unable to resolve')) {
          logger.log('ℹ️ Porcupine dependencies not available (using fallback services)');
          return false;
        }
        logger.error('❌ Unexpected error loading Porcupine:', importError);
        return false;
      }
      
      if (!PorcupineManager) {
        logger.warn('⚠️ PorcupineManager not found in package');
        return false;
      }
      
      logger.log('🎤 Initializing Porcupine wake word detection...');
      
      // Get Picovoice access key from environment or config
      // You need to sign up at https://console.picovoice.ai/ to get an access key
      const PICOVOICE_ACCESS_KEY = process.env.PICOVOICE_ACCESS_KEY || 'YOUR_ACCESS_KEY_HERE';
      
      if (PICOVOICE_ACCESS_KEY === 'YOUR_ACCESS_KEY_HERE') {
        logger.warn('⚠️ PICOVOICE_ACCESS_KEY not set. Wake word detection will not work.');
        logger.warn('📝 Sign up at https://console.picovoice.ai/ to get a free access key');
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
        logger.log('🎤 Wake word "Hey Riches" detected!');
        triggerHotword();
      });

      this.isInitialized = true;
      logger.log('✅ Porcupine initialized successfully');
      return true;

    } catch (error) {
      logger.error('❌ Failed to initialize Porcupine:', error);
      logger.error('💡 Make sure:');
      logger.error('   1. You have a development build (not Expo Go)');
      logger.error('   2. @picovoice/porcupine-react-native is installed');
      logger.error('   3. You have a valid PICOVOICE_ACCESS_KEY');
      logger.error('   4. Microphone permissions are granted');
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
      logger.log('✅ Porcupine already started');
      return true;
    }

    try {
      await this.porcupineManager.start();
      this.isStarted = true;
      logger.log('✅ Porcupine wake word detection started');
      return true;
    } catch (error) {
      logger.error('❌ Failed to start Porcupine:', error);
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
      logger.log('✅ Porcupine wake word detection stopped');
    } catch (error) {
      logger.error('❌ Failed to stop Porcupine:', error);
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
        logger.log('✅ Porcupine released');
      } catch (error) {
        logger.error('❌ Failed to release Porcupine:', error);
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

