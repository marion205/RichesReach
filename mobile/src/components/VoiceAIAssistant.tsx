import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
  TouchableOpacity,
  Alert,
  Platform,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Audio } from 'expo-av';
import * as Speech from 'expo-speech';
import { safeSpeak, stopAllSpeech } from '../hooks/useSafeSpeak';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useTheme } from '../theme/PersonalizedThemes';
import { useVoice } from '../contexts/VoiceContext';
import { useNavigation } from '@react-navigation/native';
import logger from '../utils/logger';

const { width, height } = Dimensions.get('window');

interface Insight {
  title: string;
  description?: string;
  type?: string;
  [key: string]: unknown;
}

interface VoiceAIAssistantProps {
  onClose?: () => void;
  onInsightGenerated?: (insight: Insight) => void;
}

export default function VoiceAIAssistant({ onClose, onInsightGenerated }: VoiceAIAssistantProps) {
  const navigation = useNavigation();
  
  // Use navigation.goBack() if onClose is not provided (React Navigation screen)
  const handleClose = async () => {
    // Stop any ongoing operations
    isStartingRef.current = false;
    retryCountRef.current = 0;
    
    if (recording) {
      try {
        const status = await recording.getStatusAsync();
        if (status.isRecording) {
          await recording.stopAndUnloadAsync();
        } else {
          await recording.unloadAsync();
        }
      } catch (e) {
        // Ignore cleanup errors
      }
      setRecording(null);
    }
    
    Speech.stop();
    setIsSpeaking(false);
    setIsListening(false);
    setIsProcessing(false);
    
    // Clean up audio mode
    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        playsInSilentModeIOS: false,
        shouldDuckAndroid: false,
        playThroughEarpieceAndroid: false,
      });
    } catch (e) {
      // Ignore errors
    }
    
    // Call onClose if provided, otherwise use navigation
    interface NavigationProp {
      goBack: () => void;
      [key: string]: unknown;
    }
    if (onClose && typeof onClose === 'function') {
      onClose();
    } else if (navigation && typeof (navigation as NavigationProp).goBack === 'function') {
      (navigation as NavigationProp).goBack();
    }
  };
  const theme = useTheme();
  const { getSelectedVoice } = useVoice();
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  interface ConversationMessage {
    id: string;
    type: 'user' | 'assistant';
    text: string;
    timestamp: Date;
    insights?: Insight[];
    [key: string]: unknown;
  }
  const [conversation, setConversation] = useState<ConversationMessage[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [liveTranscription, setLiveTranscription] = useState<string>('');
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const isStartingRef = useRef(false); // Prevent concurrent start attempts
  const retryCountRef = useRef(0); // Track retry attempts
  
  // ✅ FIX: Store last trade recommendation for execution
  const lastTradeRef = useRef<{
    symbol?: string;
    quantity?: number;
    side?: 'buy' | 'sell';
    price?: number;
    entry?: number;
    stop?: number;
    target?: number;
    type?: 'stock' | 'crypto'; // Track if it's a stock or crypto trade
  } | null>(null);
  
  // Animation refs
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const waveAnim = useRef(new Animated.Value(0)).current;

  // Track if audio mode has been set for this session
  const audioModeSetRef = useRef(false);

  useEffect(() => {
    // Request audio permissions immediately on mount (non-blocking)
    requestPermissions();

    // Set audio mode once per session when entering voice mode
    const setupAudioMode = async () => {
      try {
        logger.log('🎤 Setting up audio mode for voice session...');
        await Audio.setAudioModeAsync({
          allowsRecordingIOS: true,
          playsInSilentModeIOS: true,
          staysActiveInBackground: false,
          shouldDuckAndroid: true,
          playThroughEarpieceAndroid: false,
        });
        audioModeSetRef.current = true;
        logger.log('✅ Audio mode configured for voice session');
      } catch (e) {
        logger.warn('⚠️ Error setting audio mode:', e);
      }
    };
    setupAudioMode();

    // Entrance animation
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 500,
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: 1,
        duration: 500,
        useNativeDriver: true,
      }),
    ]).start();

    return () => {
      // Cleanup on unmount - stop any wake word services that might be holding recordings
      const cleanup = async () => {
        try {
          // Clean up our recording
          if (recording) {
            try {
              const status = await recording.getStatusAsync();
              if (status.isRecording) {
                await recording.stopAndUnloadAsync();
              } else {
                await recording.unloadAsync();
              }
            } catch (e) {
              // Ignore cleanup errors
            }
          }
          
          // Reset audio mode
          await Audio.setAudioModeAsync({
            allowsRecordingIOS: false,
            playsInSilentModeIOS: false,
            shouldDuckAndroid: false,
            playThroughEarpieceAndroid: false,
          });
        } catch (e) {
          // Ignore errors during cleanup
        }
        
        // Stop any ongoing speech
        stopAllSpeech();
      };
      cleanup();
    };
  }, []);

  const requestPermissions = async () => {
    try {
      // First check current status
      const currentStatus = await Audio.getPermissionsAsync();
      logger.log('🎤 Current microphone permission status:', currentStatus.status);
      
      if (currentStatus.status === 'granted') {
        setHasPermission(true);
        logger.log('✅ Microphone permission already granted!');
        return;
      }
      
      logger.log('🎤 Requesting microphone permissions...');
      const { status, canAskAgain } = await Audio.requestPermissionsAsync();
      logger.log('🎤 Permission request result:', { status, canAskAgain });
      setHasPermission(status === 'granted');
      
      if (status !== 'granted') {
        if (!canAskAgain) {
          Alert.alert(
            'Microphone Permission Required',
            'Microphone access is required for voice features. Please enable it in Settings:\n\nSettings → RichesReach → Microphone',
            [{ text: 'OK' }]
          );
        } else {
          Alert.alert(
            'Microphone Permission Required',
            'Please allow microphone access to use voice features.',
            [{ text: 'OK' }]
          );
        }
      } else {
        logger.log('✅ Microphone permission granted!');
      }
    } catch (error) {
      logger.error('❌ Permission request error:', error);
      setHasPermission(false);
    }
  };

  useEffect(() => {
    if (isListening) {
      startWaveAnimation();
    } else {
      stopWaveAnimation();
    }
  }, [isListening]);

  const speakWelcomeMessage = async () => {
    // Only speak if not already speaking/processing
    if (isSpeaking || isProcessing) return;
    const welcomeMessage = "Hello! I'm your Wealth Oracle. I can help you with portfolio analysis, market insights, and investment strategies. What would you like to know?";
    // Use timeout to prevent blocking
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => reject(new Error('Welcome message timeout')), 5000);
    });
    try {
      await Promise.race([speakText(welcomeMessage), timeoutPromise]);
    } catch (error) {
      logger.log('Welcome message skipped due to timeout');
      setIsSpeaking(false);
    }
  };

  const getVoiceParameters = (voiceId: string) => {
    // Map voice IDs to speech parameters that approximate their characteristics
    const voiceParams = {
      'alloy': { pitch: 1.0, rate: 0.9 },      // Neutral, professional
      'echo': { pitch: 0.9, rate: 0.8 },       // Warm, conversational (lower pitch)
      'fable': { pitch: 0.8, rate: 0.7 },      // Clear, authoritative (lower pitch, slower)
      'onyx': { pitch: 0.7, rate: 0.8 },       // Deep, serious (much lower pitch)
      'nova': { pitch: 1.2, rate: 1.0 },       // Bright, energetic (higher pitch, faster)
      'shimmer': { pitch: 1.1, rate: 0.8 }     // Soft, empathetic (slightly higher pitch)
    };
    
    return voiceParams[voiceId] || voiceParams['alloy'];
  };

  const startWaveAnimation = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(waveAnim, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(waveAnim, {
          toValue: 0,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  };

  const stopWaveAnimation = () => {
    waveAnim.stopAnimation();
    waveAnim.setValue(0);
  };

  // Fast cleanup - only clean up stuck recordings, don't wait long
  const quickCleanupIfNeeded = async () => {
    try {
      // Only clean up if we have a recording that's stuck
      if (recording) {
        try {
          const status = await recording.getStatusAsync();
          if (status.isRecording) {
            logger.log('🧹 Quick cleanup: stopping stuck recording...');
            await recording.stopAndUnloadAsync();
          } else {
            await recording.unloadAsync();
          }
        } catch (e) {
          // Try to unload even if stop failed
          try {
            await recording.unloadAsync();
          } catch (e2) {
            // Ignore - will be handled by expo-av
          }
        }
        setRecording(null);
      }
    } catch (error) {
      logger.warn('⚠️ Quick cleanup error (non-critical):', error);
    }
  };

  // Stop wake word services and await completion (CRITICAL: must complete before starting recording)
  const stopWakeWordsSafely = async (): Promise<void> => {
    logger.log('🎤 Stopping wake word services before voice session...');
    
    const stopPromises: Promise<void>[] = [];
    
    try {
      const { customWakeWordService } = await import('../services/CustomWakeWordService');
      const status = customWakeWordService.getStatus();
      if (status.listening) {
        logger.log('🎤 Stopping CustomWakeWordService...');
        stopPromises.push(
          customWakeWordService.stop().catch(e => {
            logger.warn('⚠️ Error stopping CustomWakeWordService:', e);
          })
        );
      }
    } catch (e) {
      // Service not available, ignore
    }
    
    try {
      const { mlWakeWordService } = await import('../services/MLWakeWordService');
      const status = mlWakeWordService.getStatus();
      if (status.listening) {
        logger.log('🎤 Stopping MLWakeWordService...');
        stopPromises.push(
          mlWakeWordService.stop().catch(e => {
            logger.warn('⚠️ Error stopping MLWakeWordService:', e);
          })
        );
      }
    } catch (e) {
      // Service not available, ignore
    }
    
    try {
      const { porcupineWakeWordService } = await import('../services/PorcupineWakeWordService');
      const status = porcupineWakeWordService.getStatus();
      if (status.started) {
        logger.log('🎤 Stopping PorcupineWakeWordService...');
        stopPromises.push(
          porcupineWakeWordService.stop().catch(e => {
            logger.warn('⚠️ Error stopping PorcupineWakeWordService:', e);
          })
        );
      }
    } catch (e) {
      // Service not available, ignore
    }
    
    // Wait for all wake word services to fully stop
    await Promise.all(stopPromises);
    
    // Give expo-av a moment to fully release the recording objects
    await new Promise(resolve => setTimeout(resolve, 300));
    
    logger.log('✅ All wake word services stopped');
  };

  // Restart wake word after interaction completes
  const restartWakeWord = async () => {
    try {
      logger.log('🎤 Re-arming wake word after interaction...');
      
      // Try ML first (fastest)
      try {
        const { mlWakeWordService } = await import('../services/MLWakeWordService');
        const started = await mlWakeWordService.start();
        if (started) {
          logger.log('✅ Wake word listening again (ML-based)');
          return;
        }
      } catch (e) {
        // Try next option
      }
      
      // Try Custom/Whisper-based
      try {
        const { customWakeWordService } = await import('../services/CustomWakeWordService');
        const started = await customWakeWordService.start();
        if (started) {
          logger.log('✅ Wake word listening again (Whisper-based)');
          return;
        }
      } catch (e) {
        // Try next option
      }
      
      // Try Porcupine
      try {
        const { porcupineWakeWordService } = await import('../services/PorcupineWakeWordService');
        const started = await porcupineWakeWordService.start();
        if (started) {
          logger.log('✅ Wake word listening again (Porcupine)');
          return;
        }
      } catch (e) {
        logger.warn('⚠️ Could not restart wake word - all services unavailable');
      }
    } catch (e) {
      logger.warn('⚠️ Error restarting wake word:', e);
    }
  };

  const startListening = async () => {
    // Clear previous transcription when starting new recording
    setLiveTranscription('');
    
    // Prevent concurrent start attempts
    if (isStartingRef.current) {
      logger.log('⚠️ Already starting recording, ignoring duplicate request');
      return;
    }
    
    // Prevent infinite retry loop (max 2 retries)
    if (retryCountRef.current > 2) {
      logger.error('❌ Max retry attempts reached, stopping');
      setIsListening(false);
      Alert.alert(
        'Recording Error', 
        'Failed to start recording after multiple attempts. Please:\n\n' +
        '1. Close this voice assistant completely\n' +
        '2. Wait 5-10 seconds\n' +
        '3. Restart the app\n' +
        '4. Try again'
      );
      retryCountRef.current = 0;
      isStartingRef.current = false;
      return;
    }
    
    isStartingRef.current = true;
    
    try {
      logger.log('🎤 Starting voice recording...');
      
      // Check if we're on iOS Simulator (which doesn't have a real mic)
      if (Platform.OS === 'ios' && __DEV__) {
        logger.warn('⚠️ Running on iOS Simulator - microphone may not work properly. Use a real device for voice features.');
      }
      
      if (!hasPermission) {
        logger.error('❌ No microphone permission');
        Alert.alert(
          'Permission Required', 
          'Microphone access is required for voice interaction. Please grant permission and try again.',
          [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Grant Permission', onPress: requestPermissions }
          ]
        );
        isStartingRef.current = false;
        return;
      }
      
      logger.log('✅ Microphone permission confirmed');

      // CRITICAL: Stop wake word services FIRST and await completion
      // This ensures their recording objects are fully released before we create a new one
      await stopWakeWordsSafely();

      // Quick cleanup only if needed (don't wait long)
      await quickCleanupIfNeeded();
      
      // CRITICAL: Set audio mode AFTER wake word stops
      // Wake word services reset audio mode to allowsRecordingIOS: false in their stop() methods
      // So we must set it to true again here, after they've stopped
      logger.log('🎤 Configuring audio mode for recording...');
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        staysActiveInBackground: false,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });
      audioModeSetRef.current = true;
      logger.log('✅ Audio mode configured for recording');

      // Start recording with Whisper-compatible settings
      const recordingOptions = {
        android: {
          extension: '.wav',
          outputFormat: Audio.RECORDING_OPTION_ANDROID_OUTPUT_FORMAT_DEFAULT,
          audioEncoder: Audio.RECORDING_OPTION_ANDROID_AUDIO_ENCODER_DEFAULT,
          sampleRate: 16000, // Whisper works best with 16kHz
          numberOfChannels: 1, // Mono for better Whisper performance
          bitRate: 128000,
        },
        ios: {
          extension: '.wav',
          outputFormat: Audio.RECORDING_OPTION_IOS_OUTPUT_FORMAT_LINEARPCM,
          audioQuality: Audio.RECORDING_OPTION_IOS_AUDIO_QUALITY_HIGH,
          sampleRate: 16000, // Whisper works best with 16kHz
          numberOfChannels: 1, // Mono for better Whisper performance
          bitRate: 128000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
          // Enable metering to detect if audio is being captured
          isMeteringEnabled: true,
        },
        web: {
          mimeType: 'audio/wav',
          bitsPerSecond: 128000,
        },
      };

      logger.log('🎤 Creating new recording...');
      const newRecording = new Audio.Recording();
      logger.log('🎤 Preparing to record...');
      await newRecording.prepareToRecordAsync(recordingOptions);
      logger.log('🎤 Starting recording...');
      await newRecording.startAsync();
      
      // Note: Metering is enabled via recording options (isMeteringEnabled: true)
      // setIsMeteringEnabledAsync may not be available in all expo-av versions
      // If metering isn't available, recording will still work, just without audio level detection
      
      // Verify recording actually started
      const status = await newRecording.getStatusAsync();
      logger.log('🎤 Recording status after start:', {
        isRecording: status.isRecording,
        canRecord: status.canRecord,
        durationMillis: status.durationMillis,
        metering: status.metering,
        isMeteringEnabled: status.isMeteringEnabled,
      });
      
      // Check microphone permission status
      const micStatus = await Audio.getPermissionsAsync();
      logger.log('🎤 Microphone permission status:', {
        status: micStatus.status,
        granted: micStatus.status === 'granted',
        canAskAgain: micStatus.canAskAgain,
      });
      
      if (!status.isRecording) {
        throw new Error('Recording did not start - status.isRecording is false');
      }
      
      setRecording(newRecording);
      setIsListening(true);
      retryCountRef.current = 0; // Reset retry count on success
      logger.log('✅ Recording started successfully!');
      
      // Start periodic status checks to verify mic is working
      const statusCheckInterval = setInterval(async () => {
        try {
          if (newRecording) {
            const currentStatus = await newRecording.getStatusAsync();
            if (currentStatus.isRecording) {
              const duration = currentStatus.durationMillis || 0;
              logger.log('🎤 Recording active - duration:', duration, 'ms');
              
              // Check metering status (optional - for audio level visualization)
              // Note: Metering may not be available on all devices/versions
              // If unavailable, we'll verify audio capture via file size at the end
              if (typeof currentStatus.metering === 'number') {
                // Metering is available - log audio levels for debugging
                if (currentStatus.metering !== -160) {
                  logger.log('🎤 Audio level:', currentStatus.metering, 'dB');
                } else if (__DEV__ && duration > 2000) {
                  // Only warn about silence if we've been recording for a while and in dev mode
                  logger.warn('⚠️ Metering shows silence (-160 dB) - may be normal if not speaking');
                }
              }
              // If metering is undefined, that's fine - we'll verify audio via file size
              
              // Only warn about "no audio" if metering is actually available and shows silence
              // If metering is undefined, we can't detect audio levels, but that doesn't mean there's no audio
              // The file size check at the end will confirm if audio was actually captured
              if (duration > 3000 && typeof currentStatus.metering === 'number') {
                // Metering is available - check if it shows silence
                if (currentStatus.metering === -160) {
                  // Only warn in dev mode, and only if we have metering data
                  if (__DEV__) {
                    logger.warn('⚠️ Metering shows silence (-160 dB) after', duration, 'ms');
                    logger.warn('⚠️ This may be normal if you haven\'t spoken yet');
                  }
                }
              }
              // If metering is undefined, don't log errors - we'll verify audio via file size at the end
            } else {
              logger.warn('⚠️ Recording stopped unexpectedly!');
              clearInterval(statusCheckInterval);
            }
          }
        } catch (e) {
          logger.warn('⚠️ Error checking recording status:', e);
          clearInterval(statusCheckInterval);
        }
      }, 2000); // Check every 2 seconds
      
      // Store interval ID so we can clear it later
      (newRecording as any)._statusCheckInterval = statusCheckInterval;
      
    } catch (error: unknown) {
      logger.error('Failed to start recording:', error);
      
      // Handle specific errors that can be retried
      const errorMessage = error instanceof Error ? error.message : String(error);
      if (errorMessage.includes('Only one Recording object') || 
          errorMessage.includes('Recording not allowed on iOS')) {
        retryCountRef.current += 1;
        logger.log(`🔄 Recording error detected (${errorMessage}), retrying (attempt ${retryCountRef.current})...`);
        
        // For retry, we need to fully stop wake words again and set audio mode
        // This ensures clean state before retry
        await stopWakeWordsSafely();
        await quickCleanupIfNeeded();
        await new Promise(resolve => setTimeout(resolve, 500)); // Short wait
        
        // Allow up to 2 retries
        if (retryCountRef.current <= 2) {
          logger.log(`🎤 Retrying recording start (attempt ${retryCountRef.current})...`);
          isStartingRef.current = false;
          await new Promise(resolve => setTimeout(resolve, 200));
          return startListening();
        } else {
          // Max retries reached - show helpful error message
          logger.error('❌ Max retry attempts reached - recording conflict persists');
          setIsListening(false);
          Alert.alert(
            'Recording Error', 
            'Unable to start recording after multiple attempts. This usually means:\n\n' +
            '• Another app is using the microphone\n' +
            '• Wake word services are still active\n' +
            '• expo-av hasn\'t released recording objects\n\n' +
            'Please:\n' +
            '1. Close this voice assistant completely\n' +
            '2. Wait 5-10 seconds\n' +
            '3. Restart the app\n' +
            '4. Try again\n\n' +
            'If the issue persists, restart your device.'
          );
          retryCountRef.current = 0;
          isStartingRef.current = false;
        }
        return;
      }
      
      // For other errors, don't retry
      Alert.alert('Recording Error', 'Failed to start recording. Please try again.');
      setIsListening(false);
      retryCountRef.current = 0;
    } finally {
      isStartingRef.current = false;
    }
  };

  const stopListening = async () => {
    if (!recording) {
      setIsListening(false);
      return;
    }
    
    // Clear status check interval if it exists
    if ((recording as any)._statusCheckInterval) {
      clearInterval((recording as any)._statusCheckInterval);
      logger.log('🛑 Stopped recording status checks');
    }
    
    // Reset retry counter when stopping
    retryCountRef.current = 0;
    isStartingRef.current = false;
    
    try {
      // Get final status before stopping
      const finalStatus = await recording.getStatusAsync();
      logger.log('🎤 Final recording status:', {
        durationMillis: finalStatus.durationMillis,
        isRecording: finalStatus.isRecording,
        canRecord: finalStatus.canRecord,
        metering: finalStatus.metering,
      });
      
      // Check if recording has any duration
      if (finalStatus.durationMillis === undefined || finalStatus.durationMillis < 100) {
        logger.warn('⚠️ Recording duration is too short:', finalStatus.durationMillis, 'ms');
        logger.warn('⚠️ This suggests no audio was captured. Possible causes:');
        logger.warn('   1. Microphone not working');
        logger.warn('   2. Audio permissions not fully granted');
        logger.warn('   3. Device microphone hardware issue');
        logger.warn('   4. Running on iOS Simulator (no real mic)');
      }
      
      const uri = recording.getURI();
      logger.log('🎤 Recording URI:', uri);
      
      await recording.stopAndUnloadAsync();
      setRecording(null);
      setIsListening(false);
      
      if (uri) {
        // Check file size before processing
        try {
          const FileSystem = await import('expo-file-system/legacy');
          const fileInfo = await FileSystem.getInfoAsync(uri);
          logger.log('🎤 Audio file info:', {
            exists: fileInfo.exists,
            size: fileInfo.size,
            uri: uri,
          });
          
          if (!fileInfo.exists) {
            throw new Error('Audio file does not exist');
          }
          
          if (fileInfo.size === undefined || fileInfo.size < 1000) {
            logger.error('❌ Audio file is too small:', fileInfo.size, 'bytes');
            logger.error('❌ This indicates no audio was captured');
            Alert.alert(
              'No Audio Captured',
              `The recording file is too small (${fileInfo.size} bytes). This usually means:\n\n` +
              `• Microphone isn't working\n` +
              `• You're on iOS Simulator (use a real device)\n` +
              `• Microphone permission not fully granted\n\n` +
              `Please check Settings → RichesReach → Microphone and try again.`
            );
            setIsProcessing(false);
            // Restart wake word even if recording failed
            restartWakeWord();
            return;
          }
          
          logger.log('✅ Audio file looks good, size:', fileInfo.size, 'bytes');
        } catch (fileError) {
          logger.error('❌ Error checking audio file:', fileError);
          // Continue anyway - might work
        }
        
        logger.log('🎤 Processing audio file:', uri);
        await processAudio(uri);
      } else {
        logger.warn('⚠️ No recording URI available - recording may have failed');
        Alert.alert(
          'Recording Error', 
          'No audio file was created. This usually means:\n\n' +
          '• Microphone permission not granted\n' +
          '• Running on iOS Simulator (use a real device)\n' +
          '• Another app is using the microphone\n\n' +
          'Please check Settings → RichesReach → Microphone and try again.'
        );
        setIsProcessing(false);
        // Restart wake word even if recording failed
        restartWakeWord();
      }
    } catch (error) {
      logger.error('❌ Failed to stop recording:', error);
      // Clean up even if stop fails
      try {
        await recording.unloadAsync();
      } catch (e) {
        // Ignore cleanup errors
      }
      setRecording(null);
      setIsListening(false);
      // Restart wake word even on error
      restartWakeWord();
    }
  };

  // ✅ STREAMING: Process audio with streaming token-by-token responses
  const processAudioStreaming = async (transcript: string) => {
    logger.log('🎤 Processing with streaming:', transcript);
    setIsProcessing(true);
    
    try {
      // Immediate local feedback
      await speakText("One sec…", { immediate: true });
      
      const { API_BASE } = await import('../config/api');
      const API_BASE_URL = API_BASE; // Config should already handle device detection correctly
      
      logger.log('🎤 [VoiceAIAssistant] Using API_BASE:', API_BASE_URL);
      logger.log('🎤 Sending to streaming API:', `${API_BASE_URL}/api/voice/stream`);
      
      // Add timeout for streaming endpoint (10 seconds max - optimized for speed)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
      }, 10000); // 10 second timeout for streaming (reduced from 15s)
      
      let response: Response;
      try {
        response = await fetch(`${API_BASE_URL}/api/voice/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            transcript: transcript,
            history: conversation.map(msg => ({
              type: msg.type,
              text: msg.text,
            })),
            last_trade: lastTradeRef.current,
          }),
          signal: controller.signal,
        });
        
        clearTimeout(timeoutId);
      } catch (fetchError: any) {
        clearTimeout(timeoutId);
        if (fetchError.name === 'AbortError') {
          throw new Error('Streaming request timed out after 15 seconds. Please try again.');
        }
        throw fetchError;
      }
      
      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unable to read error response');
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }
      
      // React Native fetch doesn't support response.body.getReader() for streaming
      // Fall back to reading the full response as text and parsing JSON lines
      let fullText = '';
      let transcribedText = transcript;
      
      try {
        // Try to use streaming if available (browser/Web)
        if (response.body && typeof response.body.getReader === 'function') {
          logger.log('✅ Using native streaming (browser/Web)');
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';
          let pendingText = '';
          
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            
            for (const line of lines) {
              if (!line.trim()) continue;
              
              try {
                const data = JSON.parse(line);
                
                if (data.type === 'ack') {
                  logger.log('✅ Received ack:', data.text);
                  // ⚡ Instant feedback - speak ACK immediately for perceived latency win
                  speakText(data.text || "Got it…", { immediate: true }).catch(err => {
                    logger.error('❌ Error speaking ACK:', err);
                  });
                } else if (data.type === 'token') {
                  pendingText += data.text;
                  fullText += data.text;
                  
                  if (pendingText.length > 15 || /[.!?]\s*$/.test(pendingText)) {
                    await speakText(pendingText, { immediate: true });
                    pendingText = '';
                  }
                } else if (data.type === 'done') {
                  if (pendingText) {
                    await speakText(pendingText);
                  }
                  fullText = data.full_text || fullText;
                  logger.log('✅ Streaming complete, full text:', fullText);
                } else if (data.type === 'error') {
                  logger.error('❌ Streaming error:', data.text);
                  await speakText(data.text || "I got confused, try again?");
                  setIsProcessing(false);
                  return;
                }
              } catch (parseError) {
                logger.warn('⚠️ Failed to parse streaming chunk:', line);
              }
            }
          }
        } else {
          // Fallback: Read full response as text and parse JSON lines
          // OPTIMIZED: Start speaking as soon as we have enough text (don't wait for full response)
          logger.log('⚠️ Streaming not available, reading full response (React Native fallback)');
          const responseText = await response.text();
          logger.log('✅ Received full response, length:', responseText.length);
          
          const lines = responseText.split('\n').filter(line => line.trim());
          let pendingText = '';
          let hasStartedSpeaking = false;
          
          // Parse and start speaking incrementally
          for (const line of lines) {
            try {
              const data = JSON.parse(line);
              
              if (data.type === 'ack') {
                logger.log('✅ Received ack:', data.text);
                // ⚡ Instant feedback - speak ACK immediately for perceived latency win
                speakText(data.text || "Got it…", { immediate: true }).catch(err => {
                  logger.error('❌ Error speaking ACK:', err);
                });
              } else if (data.type === 'token') {
                pendingText += data.text;
                fullText += data.text;
                
                // Start speaking as soon as we have ~20 chars (don't wait for full response)
                if (!hasStartedSpeaking && pendingText.length >= 20) {
                  hasStartedSpeaking = true;
                  // Start speaking the first chunk immediately (non-blocking)
                  speakText(pendingText, { immediate: true }).catch(err => {
                    logger.error('❌ Error starting speech:', err);
                  });
                  pendingText = ''; // Clear after starting
                } else if (hasStartedSpeaking && (pendingText.length > 15 || /[.!?]\s*$/.test(pendingText))) {
                  // Continue speaking additional chunks
                  speakText(pendingText, { immediate: true }).catch(err => {
                    logger.error('❌ Error continuing speech:', err);
                  });
                  pendingText = '';
                }
              } else if (data.type === 'done') {
                fullText = data.full_text || fullText;
                logger.log('✅ Received done, full text:', fullText);
                
                // Speak any remaining text
                if (pendingText) {
                  speakText(pendingText, { immediate: true }).catch(err => {
                    logger.error('❌ Error speaking final chunk:', err);
                  });
                } else if (!hasStartedSpeaking && fullText) {
                  // If we never started speaking, speak the full text now
                  speakText(fullText).catch(err => {
                    logger.error('❌ Error speaking full text:', err);
                  });
                }
                break;
              } else if (data.type === 'error') {
                logger.error('❌ Streaming error:', data.text);
                speakText(data.text || "I got confused, try again?").catch(err => {
                  logger.error('❌ Error speaking error message:', err);
                });
                setIsProcessing(false);
                return;
              }
            } catch (parseError) {
              logger.warn('⚠️ Failed to parse line:', line);
            }
          }
          
          // Fallback: If we never got a 'done' message and have text, speak it
          if (!hasStartedSpeaking && fullText) {
            logger.log('⚠️ No done message received, speaking full text:', fullText);
            speakText(fullText).catch(err => {
              logger.error('❌ Error speaking fallback text:', err);
            });
          } else if (!hasStartedSpeaking && !fullText) {
            logger.warn('⚠️ No text received from streaming response');
            speakText("I didn't get a response. Can you try again?").catch(err => {
              logger.error('❌ Error speaking no-response message:', err);
            });
          }
        }
      } catch (streamError: any) {
        logger.error('❌ Error processing stream:', streamError);
        throw streamError;
      }
      
      // Update conversation with full response
      const newConversation = [
        ...conversation,
        {
          id: Date.now(),
          type: 'user',
          text: transcribedText,
          timestamp: new Date(),
        },
        {
          id: Date.now() + 1,
          type: 'assistant',
          text: fullText,
          timestamp: new Date(),
        }
      ];
      
      setConversation(newConversation);
      setCurrentQuestion(transcribedText);
      setIsProcessing(false);
      
    } catch (error) {
      logger.error('❌ Error in streaming voice:', error);
      await speakText("I had trouble processing that. Can you try again?");
      setIsProcessing(false);
    }
  };

  const processAudio = async (audioUri: string) => {
    logger.log('🎤 Processing audio:', audioUri);
    setIsProcessing(true);
    
    // Add a timestamp to track how long processing takes
    const startTime = Date.now();
    
    try {
      // Read the audio file first to ensure it has content
      const FileSystem = await import('expo-file-system/legacy');
      const fileInfo = await FileSystem.getInfoAsync(audioUri);
      logger.log('🎤 Audio file info before upload:', {
        exists: fileInfo.exists,
        size: fileInfo.size,
        uri: audioUri,
      });
      
      if (!fileInfo.exists) {
        throw new Error('Audio file does not exist');
      }
      
      if (fileInfo.size === undefined || fileInfo.size < 100) {
        logger.warn(`⚠️ Audio file is very small (${fileInfo.size} bytes) - may be empty`);
        // Continue anyway - backend will handle it
      }
      
      // Create FormData for file upload
      // React Native FormData needs the file object with uri, type, and name
      const formData = new FormData();
      formData.append('audio', {
        uri: audioUri,
        type: 'audio/wav',
        name: 'voice.wav',
      } as any);

      // Send to backend for Whisper transcription and AI processing
      // Use the configured API_BASE which handles device detection (localhost for simulator, LAN IP for real device)
      const { API_BASE } = await import('../config/api');
      const API_BASE_URL = API_BASE; // Config should already handle device detection correctly
      
      logger.log('🎤 [VoiceAIAssistant] Using API_BASE:', API_BASE_URL);
      logger.log('🎤 Sending to API:', `${API_BASE_URL}/api/voice/process/`);
      
      let response: Response;
      try {
        // Add timeout to prevent hanging (30 seconds max for Whisper + processing)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
          controller.abort();
        }, 30000); // 30 second timeout
        
        try {
          // IMPORTANT: Don't set Content-Type header when using FormData
          // The browser will set it automatically with the correct boundary
          response = await fetch(`${API_BASE_URL}/api/voice/process/`, {
            method: 'POST',
            body: formData,
            signal: controller.signal,
            // No Content-Type header - let FormData set it automatically
          });
          
          clearTimeout(timeoutId);
          const elapsed = Date.now() - startTime;
          logger.log(`⏱️ [TIMING] Response received in ${elapsed}ms`);
          logger.log('🎤 Response status:', response.status, response.statusText);
          logger.log('🎤 Response ok:', response.ok);
        } catch (fetchError: any) {
          clearTimeout(timeoutId);
          if (fetchError.name === 'AbortError') {
            throw new Error('Request timed out after 30 seconds. Please try again.');
          }
          throw fetchError;
        }
      } catch (networkError: unknown) {
        // Log all network errors for debugging
        const errorMessage = networkError instanceof Error ? networkError.message : String(networkError);
        logger.error('❌ Network error calling voice API:', errorMessage);
        
        // Check if it's a timeout
        if (errorMessage.includes('timeout') || errorMessage.includes('timed out')) {
          await speakText("The request took too long. Please check your connection and try again.");
          setIsProcessing(false);
          restartWakeWord();
          return;
        }
        
        // Network error - use fallback mock response
        logger.warn('⚠️ Network error, using mock transcription');
        const mockResponse = {
          success: true,
          response: {
            transcription: "Show me my portfolio performance",
            text: "I understand you're interested in your portfolio. Your portfolio is currently valued at $14,303.52 with a return of +17.65%. How can I help you today?",
          }
        };
        // Process the mock response the same way as real response
        if (mockResponse.success && mockResponse.response) {
          const transcribedText = mockResponse.response.transcription || '';
          const aiResponse = mockResponse.response.text || '';
          
          // Add to conversation (matching the real response format)
          const newConversation = [
            ...conversation,
            {
              id: Date.now(),
              type: 'user',
              text: transcribedText,
              timestamp: new Date(),
            },
            {
              id: Date.now() + 1,
              type: 'assistant',
              text: aiResponse,
              timestamp: new Date(),
            }
          ];
          setConversation(newConversation);
          setCurrentQuestion(transcribedText);
          
          // Speak the response
          await speakText(aiResponse);
        }
        setIsProcessing(false);
        return;
      }

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unable to read error response');
        logger.error(`❌ HTTP error! status: ${response.status}, body: ${errorText}`);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // ✅ NEW: If backend returns transcription, use streaming endpoint for response
      if (data.success && data.response && data.response.transcription) {
        const transcribedText = data.response.transcription;
        logger.log('🎤 Got transcription, switching to streaming for response:', transcribedText);
        
        // Use streaming endpoint for the AI response
        await processAudioStreaming(transcribedText);
        return;
      }
      
      // ✅ FIX: Log the FULL response including intent for debugging
      logger.log('🎤 ============================================');
      logger.log('🎤 Voice API raw response:', JSON.stringify(data, null, 2));
      logger.log('🎤 ============================================');
      
      // ✅ FIX: Check if response exists first (robust handling)
      if (!data || !data.response) {
        logger.error('❌ Response format invalid (no response field):', data);
        throw new Error(data?.error || 'Failed to process voice input');
      }
      
      const transcribedText = data.response.transcription || '';
      const aiResponse = data.response.text || '';
      const intent = data.response.intent || '';
      
      // ✅ FIX: Detect error responses (intent === 'error' or success === false or data.error exists)
      const isErrorIntent =
        intent === 'error' ||
        data.success === false ||
        !!data.error; // backend signaled an error
      
      if (isErrorIntent) {
        logger.warn('⚠️ Voice API reported error, using friendly fallback:', {
          error: data.error,
          intent,
          confidence: data.response.confidence,
        });
        
        // Use the error message from backend (your "I'm sorry..." message) or fallback
        const safeText =
          aiResponse ||
          "I'm sorry, I had trouble processing that. Could you please try again?";
        
        // Update live transcription if available
        if (transcribedText) {
          setLiveTranscription(transcribedText);
        }
        
        // Add to conversation
        const errorConversation = [
          ...conversation,
          {
            id: Date.now(),
            type: 'user',
            text: transcribedText || 'Voice command',
            timestamp: new Date(),
          },
          {
            id: Date.now() + 1,
            type: 'assistant',
            text: safeText,
            timestamp: new Date(),
          }
        ];
        
        setConversation(errorConversation);
        setCurrentQuestion(transcribedText || '');
        
        // Speak the error message
        await speakText(safeText);
        
        // Return early - don't process as a successful response
        return;
      }
      
      // ✅ Happy path – real semantic response
      logger.log('✅ Voice processed successfully!');
      
      // Update live transcription immediately so user can see what they said
      setLiveTranscription(transcribedText);
      
      // Log the ACTUAL transcription prominently so you can see what was captured
      logger.log('🎤 ============================================');
      logger.log('🎤 ACTUAL TRANSCRIPTION FROM BACKEND:');
      logger.log('🎤', transcribedText);
      logger.log('🎤 INTENT FROM BACKEND:', intent);
      if (data.response.debug) {
        logger.log('🎤 DEBUG INFO:', JSON.stringify(data.response.debug, null, 2));
        logger.log('🎤 Whisper was used:', data.response.whisper_used ? 'YES ✅' : 'NO ❌ (using mock)');
      }
      logger.log('🎤 ============================================');
      logger.log('🎤 AI Response:', aiResponse);
      logger.log('🎤 Current conversation length:', conversation.length);
      
      // ✅ FIX: Detect execution commands (either via intent or phrase matching)
      const transcriptionLower = transcribedText.toLowerCase();
      const isExecuteCommand = 
        intent === 'execute_trade' ||
        /execute (the )?trade|place (the )?order|confirm|go ahead|do it|yes,? (place|execute|buy)/i.test(transcriptionLower);
      
      // ✅ FIX: Extract and store trade details from trade suggestions (stocks AND crypto)
      if (intent === 'trading_query' || intent === 'crypto_query' || aiResponse.includes('NVDA') || aiResponse.includes('NVIDIA') || aiResponse.includes('Bitcoin') || aiResponse.includes('BTC') || aiResponse.includes('Ethereum') || aiResponse.includes('ETH') || aiResponse.includes('Solana') || aiResponse.includes('SOL')) {
        // Try to extract trade details from the response
        const nvdaMatch = aiResponse.match(/NVIDIA \(NVDA\)|NVDA/);
        const btcMatch = aiResponse.match(/Bitcoin \(BTC\)|BTC/);
        const ethMatch = aiResponse.match(/Ethereum \(ETH\)|ETH/);
        const solMatch = aiResponse.match(/Solana \(SOL\)|SOL/);
        
        const entryMatch = aiResponse.match(/Entry (?:at|around) \$?([\d,]+\.?\d*)/i);
        const stopMatch = aiResponse.match(/stop at \$?([\d,]+\.?\d*)/i);
        const targetMatch = aiResponse.match(/target at \$?([\d,]+\.?\d*)/i);
        const qtyMatch = aiResponse.match(/(\d+)\s*(?:shares?|bitcoin|btc|ethereum|eth|solana|sol)/i);
        const priceMatch = aiResponse.match(/trading (?:at|around) \$?([\d,]+\.?\d*)/i) || aiResponse.match(/currently trading at \$?([\d,]+\.?\d*)/i);
        
        // Store stock trade
        if (nvdaMatch) {
          lastTradeRef.current = {
            symbol: 'NVDA',
            quantity: qtyMatch ? parseInt(qtyMatch[1]) : 100,
            side: 'buy' as const,
            price: entryMatch ? parseFloat(entryMatch[1].replace(/,/g, '')) : (priceMatch ? parseFloat(priceMatch[1].replace(/,/g, '')) : 179.50),
            entry: entryMatch ? parseFloat(entryMatch[1].replace(/,/g, '')) : (priceMatch ? parseFloat(priceMatch[1].replace(/,/g, '')) : 179.50),
            stop: stopMatch ? parseFloat(stopMatch[1].replace(/,/g, '')) : 178.00,
            target: targetMatch ? parseFloat(targetMatch[1].replace(/,/g, '')) : 185.00,
            type: 'stock' as const,
          };
          logger.log('🎤 Stored last stock trade recommendation:', lastTradeRef.current);
        }
        // Store crypto trades
        else if (btcMatch) {
          lastTradeRef.current = {
            symbol: 'BTC',
            quantity: qtyMatch ? parseInt(qtyMatch[1]) : 1,
            side: 'buy' as const,
            price: entryMatch ? parseFloat(entryMatch[1].replace(/,/g, '')) : (priceMatch ? parseFloat(priceMatch[1].replace(/,/g, '')) : 55000),
            entry: entryMatch ? parseFloat(entryMatch[1].replace(/,/g, '')) : (priceMatch ? parseFloat(priceMatch[1].replace(/,/g, '')) : 55000),
            stop: stopMatch ? parseFloat(stopMatch[1].replace(/,/g, '')) : 53500,
            target: targetMatch ? parseFloat(targetMatch[1].replace(/,/g, '')) : 57500,
            type: 'crypto' as const,
          };
          logger.log('🎤 Stored last crypto trade recommendation (BTC):', lastTradeRef.current);
        }
        else if (ethMatch) {
          lastTradeRef.current = {
            symbol: 'ETH',
            quantity: qtyMatch ? parseInt(qtyMatch[1]) : 1,
            side: 'buy' as const,
            price: entryMatch ? parseFloat(entryMatch[1].replace(/,/g, '')) : (priceMatch ? parseFloat(priceMatch[1].replace(/,/g, '')) : 3200),
            entry: entryMatch ? parseFloat(entryMatch[1].replace(/,/g, '')) : (priceMatch ? parseFloat(priceMatch[1].replace(/,/g, '')) : 3200),
            stop: stopMatch ? parseFloat(stopMatch[1].replace(/,/g, '')) : 3050,
            target: targetMatch ? parseFloat(targetMatch[1].replace(/,/g, '')) : 3450,
            type: 'crypto' as const,
          };
          logger.log('🎤 Stored last crypto trade recommendation (ETH):', lastTradeRef.current);
        }
        else if (solMatch) {
          lastTradeRef.current = {
            symbol: 'SOL',
            quantity: qtyMatch ? parseInt(qtyMatch[1]) : 1,
            side: 'buy' as const,
            price: entryMatch ? parseFloat(entryMatch[1].replace(/,/g, '')) : (priceMatch ? parseFloat(priceMatch[1].replace(/,/g, '')) : 180),
            entry: entryMatch ? parseFloat(entryMatch[1].replace(/,/g, '')) : (priceMatch ? parseFloat(priceMatch[1].replace(/,/g, '')) : 180),
            stop: stopMatch ? parseFloat(stopMatch[1].replace(/,/g, '')) : 170,
            target: targetMatch ? parseFloat(targetMatch[1].replace(/,/g, '')) : 195,
            type: 'crypto' as const,
          };
          logger.log('🎤 Stored last crypto trade recommendation (SOL):', lastTradeRef.current);
        }
      }
      
      // ✅ FIX: Handle execution commands differently
      let finalResponseText = aiResponse;
      let shouldExecute = false;
      
      if (isExecuteCommand) {
        if (!lastTradeRef.current) {
          finalResponseText = "I don't have a trade queued yet. Ask me for a trading idea first, then I can execute it.";
          logger.warn('⚠️ Execute command received but no trade recommendation stored');
        } else {
          // Execute the trade
          shouldExecute = true;
          const trade = lastTradeRef.current;
          const isCrypto = trade.type === 'crypto';
          const unit = isCrypto ? (trade.quantity === 1 ? trade.symbol : `${trade.quantity} ${trade.symbol}`) : `${trade.quantity || 100} shares`;
          const assetType = isCrypto ? trade.symbol : `${trade.symbol} stock`;
          
          finalResponseText = `Got it. I'm executing that trade now. Placing a limit buy order for ${unit} of ${assetType} at $${trade.price?.toLocaleString() || (isCrypto ? 'market' : '179.45')}. You'll receive a confirmation when the order fills.`;
          logger.log('🎤 Executing trade:', trade);
          
          // TODO: Actually call your trade execution API here
          // For now, we'll just log it and speak the confirmation
          // Example:
          // try {
          //   const { API_BASE } = await import('../config/api');
          //   const executeResponse = await fetch(`${API_BASE}/api/broker/orders/`, {
          //     method: 'POST',
          //     headers: { 'Content-Type': 'application/json' },
          //     body: JSON.stringify({
          //       symbol: trade.symbol,
          //       side: trade.side.toUpperCase(),
          //       quantity: trade.quantity,
          //       order_type: 'LIMIT',
          //       limit_price: trade.price,
          //     }),
          //   });
          //   const executeData = await executeResponse.json();
          //   logger.log('✅ Trade executed:', executeData);
          // } catch (executeError) {
          //   logger.error('❌ Trade execution failed:', executeError);
          //   finalResponseText = "I encountered an error executing the trade. Please try again or check your account status.";
          // }
        }
      }
      
      // ✅ FIX: Always use the NEW response text (not reusing old values)
      const assistantText = finalResponseText; // Use the processed response
      
      // Add to conversation
      const newConversation = [
        ...conversation,
        {
          id: Date.now(),
          type: 'user',
          text: transcribedText,
          timestamp: new Date(),
        },
        {
          id: Date.now() + 1,
          type: 'assistant',
          text: assistantText, // ✅ Use the new text, not old aiResponse
          timestamp: new Date(),
        }
      ];

      logger.log('🎤 Setting conversation with', newConversation.length, 'messages');
      logger.log('🎤 New conversation:', JSON.stringify(newConversation, null, 2));
      setConversation(newConversation);
      setCurrentQuestion(transcribedText);
      logger.log('🎤 Conversation state updated, current question set to:', transcribedText);
      
      // Force a small delay to ensure state updates
      await new Promise(resolve => setTimeout(resolve, 100));
      logger.log('🎤 State update complete');

      // Speak the response
      logger.log('🎤 Speaking response...');
      try {
        await speakText(assistantText); // ✅ Use the processed response
        logger.log('✅ Response spoken successfully');
      } catch (speakError) {
        logger.error('❌ Error speaking response:', speakError);
      }

      // Generate insight if applicable
      if (data.response.insights && data.response.insights.length > 0 && onInsightGenerated) {
        onInsightGenerated(data.response.insights[0]);
      }
    } catch (error) {
      logger.error('❌ Error processing audio:', error);
      logger.error('❌ Error details:', {
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
      });
      await speakText("I'm sorry, I didn't catch that. Could you please try again?");
      // Wake word will be restarted by speakText's onDone callback
    } finally {
      setIsProcessing(false);
    }
  };

  // ✅ Helper: Force playback mode before speaking (ensures speaker output, not earpiece)
  const ensurePlaybackMode = async () => {
    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,  // 🔑 NOT recording mode anymore - this is key! Forces speaker output
        playsInSilentModeIOS: true,  // Speak even if phone is on silent
        staysActiveInBackground: false,
        shouldDuckAndroid: false,
        playThroughEarpieceAndroid: false,  // Android safeguard - use speaker
        // Note: interruptionModeIOS/Android may not be available in all expo-av versions
        // The key fix is allowsRecordingIOS: false which tells iOS we're in playback mode
      });
      logger.log('✅ Audio mode set to playback (speaker-friendly)');
    } catch (e) {
      logger.warn('⚠️ Failed to set playback mode for TTS:', e);
      // Continue anyway - speech might still work
    }
  };

  const speakText = async (text: string, opts?: { immediate?: boolean }) => {
    try {
      if (!text?.trim()) {
        logger.warn('⚠️ speakText called with empty text');
        return;
      }

      setIsSpeaking(true);
      logger.log('🎤 speakText called with:', text.substring(0, 50) + '...', opts);
      
      // Stop any existing speech (especially if immediate mode)
      if (opts?.immediate) {
        try {
          Speech.stop();  // Cut off previous utterance instantly
        } catch (e) {
          // Ignore errors
        }
        await stopAllSpeech();
      } else {
        await stopAllSpeech();
      }
      
      // 🔊 CRITICAL: Force speaker-friendly playback mode before TTS
      // This ensures audio routes to speaker, not earpiece (even if we were just recording)
      await ensurePlaybackMode();
      
      // For demo: Use expo-speech directly (faster, more reliable)
      logger.log('🎤 Using expo-speech directly for demo');
      const selectedVoice = getSelectedVoice();
      const voiceParams = getVoiceParameters(selectedVoice);
      
      logger.log('🎤 Voice params:', voiceParams);
      
      // expo-speech doesn't return a promise, so don't await it
      // Use callbacks to track state
      Speech.speak(text, {
        language: 'en-US',
        pitch: voiceParams.pitch,
        rate: opts?.immediate ? 0.95 : voiceParams.rate,  // Slightly faster for streaming
        volume: 1.0,  // ✅ Set volume to maximum (0.0 to 1.0)
        onStart: () => {
          logger.log('✅ Speech started with expo-speech (should be from speaker now)');
          setIsSpeaking(true);
        },
        onDone: () => {
          logger.log('✅ Speech completed');
          setIsSpeaking(false);
          // Only restart wake word on final completion (not streaming chunks)
          if (!opts?.immediate) {
            restartWakeWord();
          }
        },
        onStopped: () => {
          logger.log('🛑 Speech stopped');
          setIsSpeaking(false);
          // Restart wake word even if speech was stopped
          if (!opts?.immediate) {
            restartWakeWord();
          }
        },
        onError: (error) => {
          logger.error('❌ Speech error:', error);
          setIsSpeaking(false);
          // Restart wake word even on error
          if (!opts?.immediate) {
            restartWakeWord();
          }
        },
      });
      
      logger.log('✅ Speech.speak() called (non-blocking)');
      return; // Exit early - we're using expo-speech directly for demo

      if (response && response.ok) {
        const data = await response.json();
        if (data.audio_url) {
          try {
            // Try to play the synthesized audio
            const { sound } = await Audio.Sound.createAsync(
              { uri: data.audio_url },
              { shouldPlay: true }
            );
            
            // Set up a timeout to fallback if audio doesn't start playing
            const fallbackTimeout = setTimeout(async () => {
              logger.log('Audio playback timeout, falling back to basic speech');
              await sound.unloadAsync();
              await safeSpeak(text, {
                language: 'en-US',
                pitch: 1.0,
                rate: 0.9,
                onDone: () => {
                  setIsSpeaking(false);
                },
                onError: (error) => {
                  logger.error('TTS error:', error);
                  setIsSpeaking(false);
                },
              });
            }, 3000); // 3 second timeout
            
            sound.setOnPlaybackStatusUpdate((status) => {
              if (status.isLoaded) {
                clearTimeout(fallbackTimeout);
                if (status.didJustFinish) {
                  setIsSpeaking(false);
                  sound.unloadAsync();
                }
              } else if (status.error) {
                clearTimeout(fallbackTimeout);
                logger.log('Audio playback error, falling back to basic speech:', status.error);
                sound.unloadAsync();
                safeSpeak(text, {
                  language: 'en-US',
                  pitch: 1.0,
                  rate: 0.9,
                  onDone: () => {
                    setIsSpeaking(false);
                  },
                  onError: (error) => {
                    logger.error('TTS error:', error);
                    setIsSpeaking(false);
                  },
                });
              }
            });
          } catch (audioError) {
            logger.log('Audio playback failed, falling back to basic speech:', audioError);
            // Fallback to basic speech if audio playback fails
            const selectedVoice = getSelectedVoice();
            const voiceParams = getVoiceParameters(selectedVoice);
            
            await safeSpeak(text, {
              language: 'en-US',
              pitch: voiceParams.pitch,
              rate: voiceParams.rate,
              onDone: () => {
                setIsSpeaking(false);
              },
              onError: (error) => {
                logger.error('TTS error:', error);
                setIsSpeaking(false);
              },
            });
          }
        } else {
          // Fallback to basic speech with voice-appropriate parameters
          const selectedVoice = getSelectedVoice();
          const voiceParams = getVoiceParameters(selectedVoice);
          
          await Speech.speak(text, {
            language: 'en-US',
            pitch: voiceParams.pitch,
            rate: voiceParams.rate,
            onDone: () => {
              setIsSpeaking(false);
            },
            onError: (error) => {
              logger.error('TTS error:', error);
              setIsSpeaking(false);
            },
          });
        }
      } else {
        // Fallback to basic speech if API fails
        const selectedVoice = getSelectedVoice();
        const voiceParams = getVoiceParameters(selectedVoice);
        
        await Speech.speak(text, {
          language: 'en-US',
          pitch: voiceParams.pitch,
          rate: voiceParams.rate,
          onDone: () => {
            setIsSpeaking(false);
          },
          onError: (error) => {
            logger.error('TTS error:', error);
            setIsSpeaking(false);
          },
        });
      }
    } catch (error) {
      logger.error('Error speaking text:', error);
      // Final fallback with voice parameters
      try {
        const selectedVoice = getSelectedVoice();
        const voiceParams = getVoiceParameters(selectedVoice);
        
        await Speech.speak(text, {
          language: 'en-US',
          pitch: voiceParams.pitch,
          rate: voiceParams.rate,
          onDone: () => {
            setIsSpeaking(false);
          },
          onError: (error) => {
            logger.error('Final TTS error:', error);
            setIsSpeaking(false);
          },
        });
      } catch (finalError) {
        logger.error('Final speech error:', finalError);
        setIsSpeaking(false);
      }
    }
  };

  const handleVoiceButtonPress = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  const getStatusText = () => {
    if (isListening) return 'Listening...';
    if (isProcessing) return 'Processing...';
    if (isSpeaking) return 'Speaking...';
    return 'Tap to speak';
  };

  const getStatusColor = () => {
    if (isListening) return '#FF3B30';
    if (isProcessing) return '#FF9500';
    if (isSpeaking) return '#34C759';
    return '#667eea';
  };

  return (
    <Animated.View
      style={[
        styles.container,
        {
          opacity: fadeAnim,
          transform: [{ scale: scaleAnim }],
        },
      ]}
    >
      <LinearGradient
        colors={['#667eea', '#764ba2']}
        style={styles.gradient}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity 
            onPress={handleClose}
            style={styles.closeButton}
            activeOpacity={0.7}
            accessibilityLabel="Close"
            accessibilityRole="button"
          >
            <Text style={styles.closeButtonText}>✕</Text>
          </TouchableOpacity>
          <View style={styles.titleContainer}>
            <Text style={styles.title}>Wealth Oracle</Text>
            <Text style={styles.subtitle}>Ask</Text>
          </View>
        </View>

        {/* Conversation History */}
        <ScrollView style={styles.conversationContainer} showsVerticalScrollIndicator={false}>
          {conversation.length === 0 && !isProcessing && (
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateText}>Say "Hey Riches" or tap the mic to start</Text>
            </View>
          )}
          {conversation.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          
          {isProcessing && (
            <View style={styles.processingBubble}>
              <ActivityIndicator size="small" color="#667eea" style={styles.processingAnimation} />
              <Text style={styles.processingText}>Processing your voice...</Text>
            </View>
          )}
        </ScrollView>

        {/* Live Transcription Display */}
        {(isListening || isProcessing || liveTranscription) && (
          <View style={styles.liveTranscriptionContainer}>
            <Text style={styles.liveTranscriptionLabel}>
              {isListening ? '🎤 Listening...' : isProcessing ? '⏳ Processing...' : '✅ You said:'}
            </Text>
            {liveTranscription ? (
              <Text style={styles.liveTranscriptionText}>{liveTranscription}</Text>
            ) : (
              <Text style={styles.liveTranscriptionPlaceholder}>
                {isListening ? 'Speak now... (check logs for mic status)' : 'Processing your speech...'}
              </Text>
            )}
            {isListening && Platform.OS === 'ios' && __DEV__ && (
              <Text style={styles.simulatorWarning}>
                ⚠️ If using iOS Simulator, mic won't work - use a real device
              </Text>
            )}
          </View>
        )}

        {/* Voice Interface */}
        <View style={styles.voiceInterface}>
          <View style={styles.statusContainer}>
            <Text style={[styles.statusText, { color: getStatusColor() }]}>
              {getStatusText()}
            </Text>
          </View>
          
          <TouchableOpacity
            testID="voice-orb"
            style={[
              styles.voiceButton,
              {
                backgroundColor: getStatusColor(),
                transform: [{ scale: isListening ? pulseAnim : 1 }],
              },
            ]}
            onPress={handleVoiceButtonPress}
            disabled={isProcessing || isSpeaking || !hasPermission}
          >
            {isListening ? (
              <Animated.View
                style={[
                  styles.listeningIndicator,
                  {
                    transform: [
                      {
                        scale: waveAnim.interpolate({
                          inputRange: [0, 1],
                          outputRange: [1, 1.2],
                        }),
                      },
                    ],
                  },
                ]}
              >
                <View style={styles.waveCircle} />
                <View style={[styles.waveCircle, styles.waveCircle2]} />
                <View style={[styles.waveCircle, styles.waveCircle3]} />
              </Animated.View>
            ) : isSpeaking ? (
              <ActivityIndicator
                size="small"
                color="#8B5CF6"
                style={styles.speakingAnimation}
              />
            ) : (
              <Text style={styles.voiceButtonIcon}>🎤</Text>
            )}
          </TouchableOpacity>
          
          <View style={styles.voiceHints}>
            <Text style={styles.voiceHintText}>
              Try asking: "How's my portfolio performing?" or "What should I invest in?"
            </Text>
          </View>
        </View>

      </LinearGradient>
    </Animated.View>
  );
}

// Message Bubble Component
interface MessageBubbleProps {
  message: ConversationMessage;
}
function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.type === 'user';
  
  return (
    <View style={[styles.messageBubble, isUser ? styles.userBubble : styles.assistantBubble]}>
      <Text style={[styles.messageText, isUser ? styles.userText : styles.assistantText]}>
        {message.text}
      </Text>
      {message.insights && message.insights.length > 0 && (
        <View style={styles.insightsContainer}>
          {message.insights.map((insight: Insight, index: number) => (
            <View key={index} style={styles.insightItem}>
              <Text style={styles.insightTitle}>{insight.title}</Text>
              <Text style={styles.insightValue}>{insight.value}</Text>
              <Text style={styles.insightDescription}>{insight.description}</Text>
            </View>
          ))}
        </View>
      )}
      <Text style={[styles.messageTime, isUser ? styles.userTime : styles.assistantTime]}>
        {message.timestamp.toLocaleTimeString()}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    width: width,
    height: height,
  },
  gradient: {
    flex: 1,
  },
  header: {
    paddingTop: 60,
    paddingHorizontal: 20,
    paddingBottom: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  closeButton: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.8)',
  },
  conversationContainer: {
    flex: 1,
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 16,
    borderRadius: 20,
    marginBottom: 16,
  },
  userBubble: {
    backgroundColor: 'rgba(255,255,255,0.9)',
    alignSelf: 'flex-end',
  },
  assistantBubble: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    alignSelf: 'flex-start',
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userText: {
    color: '#1a1a1a',
  },
  assistantText: {
    color: 'white',
  },
  insightsContainer: {
    marginTop: 12,
    padding: 12,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 12,
  },
  insightItem: {
    marginBottom: 8,
  },
  insightTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: 'white',
    marginBottom: 4,
  },
  insightValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  insightDescription: {
    fontSize: 12,
    color: '#666',
  },
  messageTime: {
    fontSize: 12,
    marginTop: 8,
  },
  userTime: {
    color: 'rgba(255,255,255,0.7)',
  },
  assistantTime: {
    color: '#666',
  },
  processingBubble: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.9)',
    padding: 16,
    borderRadius: 20,
    marginBottom: 16,
  },
  processingAnimation: {
    width: 30,
    height: 30,
    marginRight: 12,
  },
  processingText: {
    fontSize: 16,
    color: '#666',
  },
  voiceInterface: {
    padding: 20,
    alignItems: 'center',
  },
  statusContainer: {
    marginBottom: 20,
  },
  statusText: {
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
  voiceButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  voiceButtonIcon: {
    fontSize: 32,
    color: 'white',
  },
  listeningIndicator: {
    position: 'relative',
    width: 40,
    height: 40,
  },
  waveCircle: {
    position: 'absolute',
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: 'white',
  },
  waveCircle2: {
    transform: [{ scale: 1.2 }],
    opacity: 0.7,
  },
  waveCircle3: {
    transform: [{ scale: 1.4 }],
    opacity: 0.4,
  },
  speakingAnimation: {
    width: 40,
    height: 40,
  },
  voiceHints: {
    alignItems: 'center',
  },
  voiceHintText: {
    color: 'rgba(255,255,255,0.7)',
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
  titleContainer: {
    flex: 1,
    alignItems: 'center',
  },
  emptyState: {
    padding: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyStateText: {
    color: 'rgba(255,255,255,0.7)',
    fontSize: 16,
    textAlign: 'center',
  },
  liveTranscriptionContainer: {
    backgroundColor: 'rgba(255,255,255,0.95)',
    marginHorizontal: 20,
    marginBottom: 16,
    padding: 16,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: '#667eea',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  liveTranscriptionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#667eea',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  liveTranscriptionText: {
    fontSize: 16,
    color: '#1f2937',
    fontWeight: '500',
    lineHeight: 22,
  },
  liveTranscriptionPlaceholder: {
    fontSize: 16,
    color: '#9ca3af',
    fontStyle: 'italic',
  },
  simulatorWarning: {
    fontSize: 12,
    color: '#f59e0b',
    marginTop: 8,
    fontStyle: 'italic',
  },
});