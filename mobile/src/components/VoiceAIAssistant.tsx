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
import Constants from 'expo-constants';
import { safeSpeak, stopAllSpeech } from '../hooks/useSafeSpeak';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useTheme } from '../theme/PersonalizedThemes';
import { useVoice } from '../contexts/VoiceContext';
import { useNavigation } from '@react-navigation/native';
import { useMutation, gql } from '@apollo/client';
import logger from '../utils/logger';

const PLACE_ORDER = gql`
  mutation PlaceOrder($order: OrderInput!) {
    placeOrder(order: $order) {
      success
      message
      orderId
      order { id symbol side type quantity price status }
    }
  }
`;

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
  const [placeOrderMutation] = useMutation(PLACE_ORDER);
  
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
          // recording.unloadAsync() doesn't exist - use stopAndUnloadAsync() or just stop
          await recording.stopAndUnloadAsync();
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
  const welcomeTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const statusCheckIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const streamingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const processingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const fallbackTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const retryTimeoutRefs = useRef<Set<NodeJS.Timeout>>(new Set());
  const delayTimeoutRefs = useRef<Set<NodeJS.Timeout>>(new Set());
  
  // Cleanup all timeouts on unmount
  useEffect(() => {
    return () => {
      if (welcomeTimeoutRef.current) {
        clearTimeout(welcomeTimeoutRef.current);
        welcomeTimeoutRef.current = null;
      }
      if (statusCheckIntervalRef.current) {
        clearInterval(statusCheckIntervalRef.current);
        statusCheckIntervalRef.current = null;
      }
      if (streamingTimeoutRef.current) {
        clearTimeout(streamingTimeoutRef.current);
        streamingTimeoutRef.current = null;
      }
      if (processingTimeoutRef.current) {
        clearTimeout(processingTimeoutRef.current);
        processingTimeoutRef.current = null;
      }
      if (fallbackTimeoutRef.current) {
        clearTimeout(fallbackTimeoutRef.current);
        fallbackTimeoutRef.current = null;
      }
      retryTimeoutRefs.current.forEach(timeoutId => {
        clearTimeout(timeoutId);
      });
      retryTimeoutRefs.current.clear();
      delayTimeoutRefs.current.forEach(timeoutId => {
        clearTimeout(timeoutId);
      });
      delayTimeoutRefs.current.clear();
    };
  }, []);
  
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
  
  // Enhanced animation refs
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.9)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const waveAnim = useRef(new Animated.Value(0)).current;
  const glowAnim = useRef(new Animated.Value(0)).current;
  const rippleAnim = useRef(new Animated.Value(0)).current;

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

    // Enhanced entrance animation
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        friction: 8,
        tension: 40,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 600,
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
                // recording.unloadAsync() doesn't exist - use stopAndUnloadAsync() or just stop
          await recording.stopAndUnloadAsync();
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
      startPulseAnimation();
      startGlowAnimation();
      startRippleAnimation();
    } else {
      stopWaveAnimation();
      stopPulseAnimation();
      stopGlowAnimation();
      stopRippleAnimation();
    }
  }, [isListening]);

  const speakWelcomeMessage = async () => {
    // Only speak if not already speaking/processing
    if (isSpeaking || isProcessing) return;
    const welcomeMessage = "Hello! I'm your Wealth Oracle. I can help you with portfolio analysis, market insights, and investment strategies. What would you like to know?";
    // Use timeout to prevent blocking
    let timeoutId: NodeJS.Timeout | null = null;
    const timeoutPromise = new Promise<never>((_, reject) => {
      timeoutId = setTimeout(() => {
        reject(new Error('Welcome message timeout'));
        timeoutId = null;
      }, 5000);
      welcomeTimeoutRef.current = timeoutId;
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

  const startPulseAnimation = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.15,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  };

  const stopPulseAnimation = () => {
    pulseAnim.stopAnimation();
    Animated.timing(pulseAnim, {
      toValue: 1,
      duration: 300,
      useNativeDriver: true,
    }).start();
  };

  const startGlowAnimation = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: 1,
          duration: 1500,
          useNativeDriver: true,
        }),
        Animated.timing(glowAnim, {
          toValue: 0,
          duration: 1500,
          useNativeDriver: true,
        }),
      ])
    ).start();
  };

  const stopGlowAnimation = () => {
    glowAnim.stopAnimation();
    glowAnim.setValue(0);
  };

  const startRippleAnimation = () => {
    Animated.loop(
      Animated.timing(rippleAnim, {
        toValue: 1,
        duration: 2000,
        useNativeDriver: true,
      })
    ).start();
  };

  const stopRippleAnimation = () => {
    rippleAnim.stopAnimation();
    rippleAnim.setValue(0);
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
            // recording.unloadAsync() doesn't exist - use stopAndUnloadAsync() or just stop
          await recording.stopAndUnloadAsync();
          }
        } catch (e) {
          // Try to unload even if stop failed
          try {
            // recording.unloadAsync() doesn't exist - use stopAndUnloadAsync() or just stop
          await recording.stopAndUnloadAsync();
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
  // Simplified audio release - presets are more reliable, don't need nuclear option
  // This is kept for compatibility but uses faster cleanup

  const stopWakeWordsSafely = async (): Promise<void> => {
    logger.log('🎤 Stopping wake word services before voice session...');
    
    const stopPromises: Promise<void>[] = [];
    
    // Stop all services in parallel
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
    
    // Reduced wait - presets are more reliable, don't need as much time
    logger.log('🎤 Waiting for wake word services to fully release...');
    await new Promise(resolve => setTimeout(resolve, 300)); // Reduced from 1000ms to 300ms
    
    // Simplified audio release - presets handle format issues
    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        playsInSilentModeIOS: false,
        staysActiveInBackground: false,
        shouldDuckAndroid: false,
        playThroughEarpieceAndroid: false,
      });
      await new Promise(resolve => setTimeout(resolve, 200)); // Reduced from 2000ms
    } catch (e) {
      // Ignore errors
    }
    
    logger.log('✅ All wake word services stopped and audio session released');
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
    
    // CRITICAL: Clean up any existing recording object first
    // This prevents audio session conflicts
    if (recording) {
      try {
        logger.log('🎤 Cleaning up existing recording object...');
        const status = await recording.getStatusAsync();
        if (status.isRecording) {
          await recording.stopAndUnloadAsync();
        } else {
          // Try to unload even if not recording
          try {
            await (recording as any).unloadAsync?.();
          } catch {
            // If unloadAsync doesn't exist, try stopAndUnloadAsync
            await recording.stopAndUnloadAsync();
          }
        }
        setRecording(null);
        // Wait for cleanup to complete
        await new Promise(resolve => setTimeout(resolve, 300));
      } catch (e) {
        logger.warn('⚠️ Error cleaning up existing recording:', e);
        setRecording(null);
      }
    }
    
    // Detect iOS Simulator - only check device name (more reliable)
    // Constants.isDevice can be unreliable, so we only check deviceName
    const isIOSSimulator = Platform.OS === 'ios' && (
      Constants.deviceName?.toLowerCase().includes('simulator') ||
      Constants.deviceName?.toLowerCase().includes('iphone simulator') ||
      Constants.deviceName?.toLowerCase().includes('ipad simulator')
    );
    
    // Prevent infinite retry loop (max 2 retries)
    if (retryCountRef.current > 2) {
      logger.error('❌ Max retry attempts reached, stopping');
      setIsListening(false);
      
      // Show different message for simulator
      if (isIOSSimulator) {
        Alert.alert(
          'Simulator Limitation', 
          'Voice recording is not available on iOS Simulator.\n\n' +
          'Please use a real iOS device to test voice features.\n\n' +
          'The simulator does not have access to a real microphone.'
        );
      } else {
        Alert.alert(
          'Recording Error', 
          'Failed to start recording after multiple attempts. Please:\n\n' +
          '1. Close this voice assistant completely\n' +
          '2. Wait 5-10 seconds\n' +
          '3. Restart the app\n' +
          '4. Try again'
        );
      }
      retryCountRef.current = 0;
      isStartingRef.current = false;
      return;
    }
    
    isStartingRef.current = true;
    
    try {
      logger.log('🎤 Starting voice recording...');
      
      // Check if we're on iOS Simulator (which doesn't have a real mic)
      if (isIOSSimulator) {
        logger.warn('⚠️ Running on iOS Simulator - microphone is not available. Use a real device for voice features.');
        // Don't block, but warn that it may fail
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

      // CRITICAL: Stop wake word services FIRST - they hold recording objects
      logger.log('🎤 Stopping wake word services to release audio session...');
      await stopWakeWordsSafely();
      
      // ☢️☢️☢️ ULTIMATE FIX: Disable and re-enable Audio module ☢️☢️☢️
      // This forces expo-av to release ALL recording objects internally
      logger.log('☢️ ULTIMATE FIX: Resetting Audio module to release all recordings...');
      
      try {
        // Check if setIsEnabledAsync exists (available in newer expo-av versions)
        if (typeof (Audio as any).setIsEnabledAsync === 'function') {
          // Disable audio completely
          logger.log('☢️ Disabling Audio module...');
          await (Audio as any).setIsEnabledAsync(false);
          logger.log('✅ Audio disabled');
          
          // Wait for it to fully shut down
          await new Promise(resolve => setTimeout(resolve, 500));
          
          // Re-enable audio
          logger.log('☢️ Re-enabling Audio module...');
          await (Audio as any).setIsEnabledAsync(true);
          logger.log('✅ Audio re-enabled');
          
          // Wait for it to fully initialize
          await new Promise(resolve => setTimeout(resolve, 500));
        } else {
          logger.log('⚠️ setIsEnabledAsync not available, using aggressive cleanup instead...');
          // Fallback: Multiple audio mode resets (nuclear option)
          for (let i = 0; i < 5; i++) {
            await Audio.setAudioModeAsync({
              allowsRecordingIOS: false,
              playsInSilentModeIOS: false,
            });
            await new Promise(resolve => setTimeout(resolve, 300));
          }
          // Extra wait for garbage collection
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      } catch (e) {
        logger.warn('⚠️ Error in ultimate cleanup:', e);
        // Fallback: Aggressive audio mode resets
        logger.log('🔄 Using fallback: aggressive audio mode resets...');
        try {
          for (let i = 0; i < 5; i++) {
            await Audio.setAudioModeAsync({
              allowsRecordingIOS: false,
              playsInSilentModeIOS: false,
            });
            await new Promise(resolve => setTimeout(resolve, 300));
          }
          await new Promise(resolve => setTimeout(resolve, 1000));
        } catch (fallbackError) {
          logger.warn('⚠️ Fallback cleanup also failed:', fallbackError);
        }
      }

      // ✅ MINIMAL + RELIABLE: Use Expo preset (records .m4a on iOS, perfect for transcription)
      logger.log('🎤 Setting up audio mode and creating recording with Expo preset...');
      
      try {
        // Set audio mode (minimal, reliable)
        await Audio.setAudioModeAsync({
          allowsRecordingIOS: true,
          playsInSilentModeIOS: true,
        });
        
        // Wait longer to ensure audio session is fully ready after nuclear reset
        await new Promise(resolve => setTimeout(resolve, 500));

        // ✅ Use Expo's createAsync with HIGH_QUALITY preset (handles everything)
        const { recording: newRecording } = await Audio.Recording.createAsync(
          Audio.RecordingOptionsPresets.HIGH_QUALITY
        );
        
        logger.log('✅ Recording created successfully with Expo preset');
        setRecording(newRecording);
        setIsListening(true);
        
        // Log file info for debugging
        const FileSystem = await import('expo-file-system/legacy');
        const uri = newRecording.getURI();
        if (uri) {
          const fileInfo = await FileSystem.getInfoAsync(uri);
          logger.log('🎤 Recording file info:', {
            uri,
            exists: fileInfo.exists,
            size: (fileInfo as any).size,
          });
        }
      
      // Verify recording actually started
      const status = await newRecording.getStatusAsync();
      logger.log('🎤 Recording status after start:', {
        isRecording: status.isRecording,
        canRecord: status.canRecord,
        durationMillis: status.durationMillis,
        metering: status.metering,
        isMeteringEnabled: (status as any).isMeteringEnabled || false,
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
              // This is expected when wake word service stops recording
              // Only log if we're actually in a recording session (not wake word)
              if (isListening && recording) {
                logger.warn('⚠️ Recording stopped unexpectedly during active session!');
              if (statusCheckIntervalRef.current) {
                clearInterval(statusCheckIntervalRef.current);
                statusCheckIntervalRef.current = null;
              }
              }
              // Otherwise, it's just the wake word service cycling - ignore it
            }
          }
        } catch (e) {
          logger.warn('⚠️ Error checking recording status:', e);
          if (statusCheckIntervalRef.current) {
            clearInterval(statusCheckIntervalRef.current);
            statusCheckIntervalRef.current = null;
          }
        }
      }, 2000); // Check every 2 seconds
      
      // Store interval ID so we can clear it later
        statusCheckIntervalRef.current = statusCheckInterval;
      
    } catch (error: unknown) {
      logger.error('Failed to start recording:', error);
      
      // Handle specific errors that can be retried
      const errorMessage = error instanceof Error ? error.message : String(error);
      const errorCode = (error as any)?.code || '';
      
      // Check for iOS audio session error (1718449215)
      const isAudioSessionError = errorCode === 1718449215 || 
                                    errorCode === '1718449215' ||
                                    errorMessage.includes('NSOSStatusErrorDomain') ||
                                    errorMessage.includes('Code=1718449215') ||
                                    errorMessage.includes('Prepare encountered an error');
      
      // Check for "Recording not allowed" error specifically
      const isRecordingNotAllowed = errorMessage.includes('Recording not allowed on iOS') ||
                                    errorMessage.includes('Enable with Audio.setAudioModeAsync');
      
        // Detect iOS Simulator - only check device name (more reliable)
      const isIOSSimulator = Platform.OS === 'ios' && (
        Constants.deviceName?.toLowerCase().includes('simulator') ||
        Constants.deviceName?.toLowerCase().includes('iphone simulator') ||
          Constants.deviceName?.toLowerCase().includes('ipad simulator')
      );
      
      // On iOS Simulator, don't retry - show clear message instead
      if (isIOSSimulator && (isAudioSessionError || isRecordingNotAllowed)) {
        logger.error('❌ Recording failed on iOS Simulator - microphone not available');
        setIsListening(false);
        isStartingRef.current = false;
        retryCountRef.current = 0;
        Alert.alert(
          'Simulator Limitation', 
          'Voice recording is not available on iOS Simulator.\n\n' +
          'The simulator does not have access to a real microphone.\n\n' +
          'Please use a real iOS device to test voice features.'
        );
        return;
      }
      
      if (errorMessage.includes('Only one Recording object') || 
          isRecordingNotAllowed ||
          isAudioSessionError) {
        retryCountRef.current += 1;
        logger.log(`🔄 Recording error detected (${errorMessage}), retrying (attempt ${retryCountRef.current})...`);
        
        // CRITICAL: Stop wake words and clean up before retry
        logger.log('🎤 Stopping wake word services before retry...');
        await stopWakeWordsSafely();
        
        // ☢️ ULTIMATE FIX: Try to disable/enable audio again for retry
        logger.log('☢️ ULTIMATE FIX: Resetting Audio module before retry...');
        try {
          if (typeof (Audio as any).setIsEnabledAsync === 'function') {
            await (Audio as any).setIsEnabledAsync(false);
            await new Promise(resolve => setTimeout(resolve, 1000));
            await (Audio as any).setIsEnabledAsync(true);
            await new Promise(resolve => setTimeout(resolve, 1000));
          } else {
            // Fallback: Aggressive audio mode resets
            for (let i = 0; i < 5; i++) {
              await Audio.setAudioModeAsync({
                allowsRecordingIOS: false,
                playsInSilentModeIOS: false,
              });
              await new Promise(resolve => setTimeout(resolve, 300));
            }
            await new Promise(resolve => setTimeout(resolve, 1000));
          }
        } catch (retryCleanupError) {
          logger.warn('⚠️ Error in retry cleanup:', retryCleanupError);
          // Fallback: Simple reset
          try {
            await Audio.setAudioModeAsync({
              allowsRecordingIOS: false,
              playsInSilentModeIOS: false,
            });
            await new Promise(resolve => setTimeout(resolve, 1000));
          } catch (fallbackError) {
            logger.warn('⚠️ Fallback retry cleanup failed:', fallbackError);
          }
        }
        
        // CRITICAL: If "Recording not allowed" error, we MUST re-set audio mode to allow recording
        if (isRecordingNotAllowed) {
          logger.log('🎤 Re-setting audio mode to allow recording (recording was not allowed)...');
          for (let i = 0; i < 2; i++) {
            try {
              await Audio.setAudioModeAsync({
                allowsRecordingIOS: true,
                playsInSilentModeIOS: true,
                staysActiveInBackground: false,
                shouldDuckAndroid: true,
                playThroughEarpieceAndroid: false,
              });
              logger.log(`✅ Audio mode re-set to allow recording (attempt ${i + 1})`);
              if (i === 0) {
                await new Promise(resolve => setTimeout(resolve, 200));
              }
            } catch (e) {
              logger.warn(`⚠️ Error re-setting audio mode (attempt ${i + 1}):`, e);
            }
          }
        }
        
        await new Promise(resolve => setTimeout(resolve, 200)); // Additional wait
        
        // Allow up to 3 retries (increased from 2)
        if (retryCountRef.current <= 3) {
          logger.log(`🎤 Retrying recording start (attempt ${retryCountRef.current})...`);
          isStartingRef.current = false;
          
            // Much longer delay for retries - iOS needs significant time to release audio session
            // Also perform additional cleanup before retrying
            logger.log('🔄 Performing additional cleanup before retry...');
            try {
              // Multiple audio mode resets
              for (let i = 0; i < 3; i++) {
                await Audio.setAudioModeAsync({
                  allowsRecordingIOS: false,
                  playsInSilentModeIOS: false,
                  staysActiveInBackground: false,
                  shouldDuckAndroid: false,
                  playThroughEarpieceAndroid: false,
                });
                await new Promise(resolve => setTimeout(resolve, 400));
              }
            } catch (cleanupErr) {
              logger.warn('⚠️ Error in pre-retry cleanup:', cleanupErr);
            }
            
            await new Promise(resolve => setTimeout(resolve, 2000)); // Increased from 1000ms to 2000ms
          
          return startListening();
        } else {
          // Max retries reached - show helpful error message
          logger.error('❌ Max retry attempts reached - recording conflict persists');
          setIsListening(false);
          
          // Final attempt: completely disable wake word services and try one more time
          logger.log('🎤 Final attempt: completely disabling wake word services...');
          try {
            // Import and stop all wake word services one more time
            const { customWakeWordService } = await import('../services/CustomWakeWordService');
            const { mlWakeWordService } = await import('../services/MLWakeWordService');
            const { porcupineWakeWordService } = await import('../services/PorcupineWakeWordService');
            
            await Promise.all([
              customWakeWordService.stop().catch(() => {}),
              mlWakeWordService.stop().catch(() => {}),
              porcupineWakeWordService.stop().catch(() => {}),
            ]);
            
            // Wait longer for final cleanup
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // Reset audio mode multiple times
            for (let i = 0; i < 3; i++) {
              await Audio.setAudioModeAsync({
                allowsRecordingIOS: false,
                playsInSilentModeIOS: false,
                staysActiveInBackground: false,
                shouldDuckAndroid: false,
                playThroughEarpieceAndroid: false,
              });
              await new Promise(resolve => setTimeout(resolve, 300));
            }
            
            // One final attempt
            logger.log('🎤 Making final recording attempt...');
            isStartingRef.current = false;
            retryCountRef.current = 0; // Reset counter for final attempt
            await new Promise(resolve => setTimeout(resolve, 500));
            return startListening();
          } catch (finalError) {
            logger.error('❌ Final attempt also failed:', finalError);
          }
          
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
      }
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
            size: (fileInfo as any).size,
            uri: uri,
          });
          
          if (!fileInfo.exists) {
            throw new Error('Audio file does not exist');
          }
          
          if ((fileInfo as any).size === undefined || (fileInfo as any).size < 1000) {
            logger.error('❌ Audio file is too small:', (fileInfo as any).size, 'bytes');
            logger.error('❌ This indicates no audio was captured');
            Alert.alert(
              'No Audio Captured',
              `The recording file is too small (${(fileInfo as any).size} bytes). This usually means:\n\n` +
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
          
          logger.log('✅ Audio file looks good, size:', (fileInfo as any).size, 'bytes');
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
        // recording.unloadAsync() doesn't exist - use stopAndUnloadAsync() or just stop
        await recording.stopAndUnloadAsync();
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
      
      // Voice endpoints are on port 8000 (Django), same as main API
      const { API_BASE } = await import('../config/api');
      const API_BASE_URL = API_BASE; // Use main API URL (port 8000)
      
      logger.log('🎤 [VoiceAIAssistant] Using API_BASE for streaming:', API_BASE_URL);
      logger.log('🎤 Sending to streaming API:', `${API_BASE_URL}/api/voice/stream`);
      
      // Add timeout for streaming endpoint (10 seconds max - optimized for speed)
      const controller = new AbortController();
      if (streamingTimeoutRef.current) {
        clearTimeout(streamingTimeoutRef.current);
      }
      const timeoutId = setTimeout(() => {
        controller.abort();
        streamingTimeoutRef.current = null;
      }, 10000); // 10 second timeout for streaming (reduced from 15s)
      streamingTimeoutRef.current = timeoutId;
      
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
          id: String(Date.now()),
          type: 'user',
          text: transcribedText,
          timestamp: new Date(),
        },
        {
          id: String(Date.now() + 1),
          type: 'assistant',
          text: fullText,
          timestamp: new Date(),
        }
      ];
      
      setConversation(newConversation as ConversationMessage[]);
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
    
    // ⚡ INSTANT FEEDBACK - Start speaking immediately for perceived speed
    logger.log('⚡ Providing instant feedback while processing...');
    speakText("Got it, let me check that...", { immediate: true }).catch(err => {
      logger.warn('⚠️ Error providing instant feedback:', err);
    });
    
    // Add a timestamp to track how long processing takes
    const startTime = Date.now();
    
    try {
      // Read the audio file first to ensure it has content
      const FileSystem = await import('expo-file-system/legacy');
      const fileInfo = await FileSystem.getInfoAsync(audioUri);
      logger.log('🎤 Audio file info before upload:', {
        exists: fileInfo.exists,
        size: (fileInfo as any).size,
        uri: audioUri,
      });
      
      if (!fileInfo.exists) {
        throw new Error('Audio file does not exist');
      }
      
      if ((fileInfo as any).size === undefined || (fileInfo as any).size < 100) {
        logger.warn(`⚠️ Audio file is very small (${(fileInfo as any).size} bytes) - may be empty`);
        // Continue anyway - backend will handle it
      }
      
      // Create FormData for file upload
      // React Native FormData needs the file object with uri, type, and name
      const formData = new FormData();
      // Use m4a format (works on iOS) - Whisper backend handles it fine
      const audioExtension = Platform.OS === 'ios' ? '.m4a' : '.wav';
      const audioMimeType = Platform.OS === 'ios' ? 'audio/x-m4a' : 'audio/wav';
      
      formData.append('audio', {
        uri: audioUri,
        type: audioMimeType,
        name: `voice${audioExtension}`,
      } as any);

      // Send to backend for Whisper transcription and AI processing
      // Voice endpoints are on port 8000 (Django), same as main API
      const { API_BASE } = await import('../config/api');
      const API_BASE_URL = API_BASE; // Use main API URL (port 8000)
      
      logger.log('🎤 [VoiceAIAssistant] Using API_BASE:', API_BASE_URL);
      logger.log('🎤 Sending to API:', `${API_BASE_URL}/api/voice/process/`);
      
      let response: Response;
      try {
        // Add timeout to prevent hanging (30 seconds max for Whisper + processing)
        const controller = new AbortController();
        if (processingTimeoutRef.current) {
          clearTimeout(processingTimeoutRef.current);
        }
        processingTimeoutRef.current = setTimeout(() => {
          controller.abort();
          processingTimeoutRef.current = null;
        }, 60000); // 60 second timeout (Whisper can take longer)
        
        try {
          // IMPORTANT: Don't set Content-Type header when using FormData
          // The browser will set it automatically with the correct boundary
          response = await fetch(`${API_BASE_URL}/api/voice/process/`, {
            method: 'POST',
            body: formData,
            signal: controller.signal,
            // No Content-Type header - let FormData set it automatically
          });
          
          // Clear timeout if request succeeded
          if (processingTimeoutRef.current) {
            clearTimeout(processingTimeoutRef.current);
            processingTimeoutRef.current = null;
          }
          const elapsed = Date.now() - startTime;
          logger.log(`⏱️ [TIMING] Response received in ${elapsed}ms`);
          logger.log('🎤 Response status:', response.status, response.statusText);
          logger.log('🎤 Response ok:', response.ok);
        } catch (fetchError: any) {
          // Clear timeout on error
          if (processingTimeoutRef.current) {
            clearTimeout(processingTimeoutRef.current);
            processingTimeoutRef.current = null;
          }
          if (fetchError.name === 'AbortError') {
            throw new Error('Request timed out after 60 seconds. The server may be processing your audio - please try again.');
          }
          throw fetchError;
        }
      } catch (networkError: unknown) {
        // Log all network errors for debugging
        const errorMessage = networkError instanceof Error ? networkError.message : String(networkError);
        const errorStack = networkError instanceof Error ? networkError.stack : undefined;
        logger.error('❌ Network error calling voice API:', {
          message: errorMessage,
          stack: errorStack,
          url: `${API_BASE_URL}/api/voice/process/`,
          apiBase: API_BASE_URL,
        });
        
        // Check if it's a timeout - provide helpful mock response for testing
        if (errorMessage.includes('timeout') || errorMessage.includes('timed out')) {
          logger.warn('⚠️ Backend timeout, using mock response for testing');
          
          // Use a helpful mock response instead of just an error
          const mockResponse = {
            success: true,
            response: {
              transcription: "Voice command",
              text: "I heard you! The backend is currently processing slowly, but your recording works perfectly! This is a timeout issue - the backend may be taking longer than expected to process your audio. Try speaking a shorter command or check if the backend is running properly.",
            }
          };
          
          // Process mock response
          const transcribedText = mockResponse.response.transcription || '';
          const aiResponse = mockResponse.response.text || '';
          
          const newConversation = [
            ...conversation,
            {
              id: String(Date.now()),
              type: 'user',
              text: transcribedText,
              timestamp: new Date(),
            },
            {
              id: String(Date.now() + 1),
              type: 'assistant',
              text: aiResponse,
              timestamp: new Date(),
            }
          ];
          
          setConversation(newConversation as ConversationMessage[]);
          await speakText(aiResponse);
          setIsProcessing(false);
          restartWakeWord();
          return;
        }
        
        // Check for connection refused (backend not running)
        if (errorMessage.includes('Failed to connect') || 
            errorMessage.includes('Network request failed') ||
            errorMessage.includes('ECONNREFUSED') ||
            errorMessage.includes('fetch failed')) {
          const errorText = `I can't reach the server at ${API_BASE_URL}. Please make sure the backend is running on port 8000 or 8002.`;
          logger.error('❌ Connection failed:', errorText);
          await speakText("I can't connect to the server. Please make sure the backend is running.");
          setIsProcessing(false);
          restartWakeWord();
          return;
        }
        
        // Network error - use generic fallback that doesn't assume intent
        logger.warn('⚠️ Network error, using generic fallback');
        const mockResponse = {
          success: true,
          response: {
            transcription: "Connection error",
            text: `I'm having trouble connecting to the server. Error: ${errorMessage}. Please check your connection and make sure the backend is running.`,
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
              id: String(Date.now()),
              type: 'user',
              text: transcribedText,
              timestamp: new Date(),
            },
            {
              id: String(Date.now() + 1),
              type: 'assistant',
              text: aiResponse,
              timestamp: new Date(),
            }
          ];
          setConversation(newConversation as ConversationMessage[]);
          setCurrentQuestion(transcribedText);
          
          // Speak the response
          await speakText(aiResponse);
        }
        setIsProcessing(false);
        restartWakeWord();
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
        
        // CRITICAL: Log what was actually transcribed
        logger.log('🎤 ============================================');
        logger.log('🎤 TRANSCRIPTION FROM BACKEND:', transcribedText);
        logger.log('🎤 Whisper was used:', data.response.whisper_used ? 'YES ✅' : 'NO ❌ (MOCK)');
        if (!data.response.whisper_used) {
          logger.error('❌ WARNING: Backend used MOCK transcription, not real Whisper!');
          logger.error('❌ This means your actual words were NOT captured.');
          logger.error('❌ Check backend logs to see why Whisper failed.');
        }
        logger.log('🎤 ============================================');
        
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
            id: String(Date.now()),
            type: 'user',
            text: transcribedText || 'Voice command',
            timestamp: new Date(),
          },
          {
            id: String(Date.now() + 1),
            type: 'assistant',
            text: safeText,
            timestamp: new Date(),
          }
        ];
        
        setConversation(errorConversation as ConversationMessage[]);
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
      logger.log('🎤', transcribedText || '[EMPTY - No transcription received]');
      logger.log('🎤 INTENT FROM BACKEND:', intent);
      if (data.response.debug) {
        logger.log('🎤 DEBUG INFO:', JSON.stringify(data.response.debug, null, 2));
        logger.log('🎤 Whisper was used:', data.response.whisper_used ? 'YES ✅' : 'NO ❌ (using mock)');
      }
      
      // Warn if transcription is empty or looks like a mock
      if (!transcribedText || transcribedText.trim() === '') {
        logger.error('❌ TRANSCRIPTION IS EMPTY! Backend did not capture what you said.');
      } else if (transcribedText.includes('Show me') || transcribedText.includes('Find me') || transcribedText.includes('Buy')) {
        logger.warn('⚠️ WARNING: This looks like a mock transcription, not what you actually said!');
        logger.warn('⚠️ Check backend logs to see if Whisper API is working.');
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
          try {
            const orderInput = {
              symbol: (trade.symbol || '').toUpperCase(),
              side: (trade.side || 'buy').toUpperCase(),
              type: 'LIMIT',
              quantity: trade.quantity || (isCrypto ? 1 : 100),
              price: trade.price ?? (isCrypto ? undefined : 179.45),
              timeInForce: 'DAY',
            };
            const executeResult = await placeOrderMutation({ variables: { order: orderInput } });
            if (executeResult.data?.placeOrder?.success) {
              logger.log('✅ Trade executed:', executeResult.data.placeOrder);
              finalResponseText = `Order placed successfully. ${executeResult.data.placeOrder.orderId ? `Order ID: ${executeResult.data.placeOrder.orderId}.` : ''} You'll get a confirmation when it fills.`;
            } else {
              const msg = executeResult.data?.placeOrder?.message || 'Order was not placed.';
              logger.warn('⚠️ Place order result:', msg);
              finalResponseText = `I couldn't complete the order: ${msg}. Please try again or check your account.`;
            }
          } catch (executeError: any) {
            logger.error('❌ Trade execution failed:', executeError);
            finalResponseText = "I encountered an error executing the trade. Please try again or check your account status.";
          }
        }
      }
      
      // ✅ FIX: Always use the NEW response text (not reusing old values)
      const assistantText = finalResponseText; // Use the processed response
      
      // Add to conversation
      const newConversation = [
        ...conversation,
        {
          id: String(Date.now()),
          type: 'user',
          text: transcribedText,
          timestamp: new Date(),
        },
        {
          id: String(Date.now() + 1),
          type: 'assistant',
          text: assistantText, // ✅ Use the new text, not old aiResponse
          timestamp: new Date(),
        }
      ];

      logger.log('🎤 Setting conversation with', newConversation.length, 'messages');
      logger.log('🎤 New conversation:', JSON.stringify(newConversation, null, 2));
      setConversation(newConversation as ConversationMessage[]);
      setCurrentQuestion(transcribedText);
      logger.log('🎤 Conversation state updated, current question set to:', transcribedText);
      
      // Force a small delay to ensure state updates
      await new Promise<void>(resolve => {
        const timeoutId = setTimeout(() => {
          resolve();
          retryTimeoutRefs.current.delete(timeoutId);
        }, 100);
        retryTimeoutRefs.current.add(timeoutId);
      });
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
          transform: [{ scale: scaleAnim }, { translateY: slideAnim }],
        },
      ]}
    >
      <LinearGradient
        colors={['#1a1a2e', '#16213e', '#0f3460']}
        style={styles.gradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        {/* Animated background particles */}
        <View style={styles.particlesContainer}>
          {[...Array(20)].map((_, i) => (
            <View
              key={i}
              style={[
                styles.particle,
                {
                  left: `${Math.random() * 100}%`,
                  top: `${Math.random() * 100}%`,
                  opacity: 0.1 + Math.random() * 0.3,
                },
              ]}
            />
          ))}
        </View>
        {/* Header with glassmorphism effect */}
        <View style={styles.headerBlur}>
        <View style={styles.header}>
          <TouchableOpacity 
            onPress={handleClose}
            style={styles.closeButton}
            activeOpacity={0.7}
            accessibilityLabel="Close"
            accessibilityRole="button"
            >
              <LinearGradient
                colors={['rgba(255,255,255,0.15)', 'rgba(255,255,255,0.05)']}
                style={styles.closeButtonGradient}
          >
            <Text style={styles.closeButtonText}>✕</Text>
              </LinearGradient>
          </TouchableOpacity>
            
          <View style={styles.titleContainer}>
              <View style={styles.titleRow}>
                <View style={styles.titleTextContainer}>
            <Text style={styles.title}>Wealth Oracle</Text>
                  <Text style={styles.subtitle}>Your AI Financial Assistant</Text>
                </View>
                <View style={styles.logoContainer}>
                  <LinearGradient
                    colors={['#667eea', '#764ba2']}
                    style={styles.logoGradient}
                  >
                    <Text style={styles.logoIcon}>🔮</Text>
                  </LinearGradient>
                </View>
              </View>
            </View>
          </View>
        </View>

        {/* Conversation History */}
        <ScrollView 
          style={styles.conversationContainer} 
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.conversationContent}
        >
          {conversation.length === 0 && !isProcessing && (
            <View style={styles.emptyState}>
              <View style={styles.emptyStateIconContainer}>
                <LinearGradient
                  colors={['rgba(102,126,234,0.2)', 'rgba(118,75,162,0.2)']}
                  style={styles.emptyStateIcon}
                >
                  <Text style={styles.emptyStateEmoji}>👋</Text>
                </LinearGradient>
              </View>
              <Text style={styles.emptyStateTitle}>Ready to assist you</Text>
              <Text style={styles.emptyStateText}>
                Ask me about your portfolio, market trends, or investment strategies
              </Text>
              <View style={styles.suggestionChips}>
                <View style={[styles.chip, { marginRight: 8, marginBottom: 8 }]}>
                  <Text style={styles.chipText}>📊 Portfolio analysis</Text>
                </View>
                <View style={[styles.chip, { marginRight: 8, marginBottom: 8 }]}>
                  <Text style={styles.chipText}>💡 Investment ideas</Text>
                </View>
                <View style={[styles.chip, { marginBottom: 8 }]}>
                  <Text style={styles.chipText}>📈 Market trends</Text>
                </View>
              </View>
            </View>
          )}
          
          {conversation.map((message, index) => (
            <MessageBubble 
              key={message.id} 
              message={message} 
              isLast={index === conversation.length - 1}
            />
          ))}
          
          {isProcessing && (
            <View style={styles.processingBubble}>
              <View style={styles.processingDots}>
                <View style={[styles.dot, styles.dot1, { marginRight: 8 }]} />
                <View style={[styles.dot, styles.dot2, { marginRight: 8 }]} />
                <View style={[styles.dot, styles.dot3]} />
              </View>
              <Text style={styles.processingText}>Analyzing your request...</Text>
            </View>
          )}
        </ScrollView>

        {/* Live Transcription */}
        {(isListening || isProcessing || liveTranscription) && (
          <View style={styles.transcriptionBlur}>
          <View style={styles.liveTranscriptionContainer}>
              <View style={styles.transcriptionHeader}>
                <View style={[styles.statusDot, { backgroundColor: getStatusColor() }]} />
            <Text style={styles.liveTranscriptionLabel}>
                  {isListening ? 'Listening' : isProcessing ? 'Processing' : 'You said'}
            </Text>
              </View>
            {liveTranscription ? (
              <Text style={styles.liveTranscriptionText}>{liveTranscription}</Text>
            ) : (
              <Text style={styles.liveTranscriptionPlaceholder}>
                  {isListening ? 'Start speaking...' : 'Processing your speech...'}
              </Text>
            )}
            </View>
          </View>
        )}

        {/* Voice Interface */}
        <View style={styles.voiceInterface}>
          <View style={styles.statusContainer}>
            <Text style={[styles.statusText, { color: getStatusColor() }]}>
              {getStatusText()}
            </Text>
          </View>
          
          {/* Voice button with ripple effects */}
          <View style={styles.voiceButtonContainer}>
            {isListening && (
              <>
                {[0, 1, 2].map((index) => (
              <Animated.View
                    key={index}
                style={[
                      styles.ripple,
                  {
                        opacity: rippleAnim.interpolate({
                          inputRange: [0, 1],
                          outputRange: [0.5, 0],
                        }),
                    transform: [
                      {
                            scale: rippleAnim.interpolate({
                          inputRange: [0, 1],
                              outputRange: [1, 2 + index * 0.3],
                        }),
                      },
                    ],
                      },
                    ]}
                  />
                ))}
              </>
            )}
            
            <Animated.View
              style={[
                styles.voiceButtonOuter,
                {
                  transform: [{ scale: pulseAnim }],
                  opacity: glowAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0.3, 0.6],
                  }),
                  },
                ]}
              >
              <LinearGradient
                colors={
                  isListening
                    ? ['#FF3B30', '#FF6B6B']
                    : isProcessing
                    ? ['#FF9500', '#FFB347']
                    : isSpeaking
                    ? ['#34C759', '#5FD068']
                    : ['#667eea', '#764ba2']
                }
                style={styles.voiceButtonGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <TouchableOpacity
                  testID="voice-orb"
                  style={styles.voiceButton}
                  onPress={handleVoiceButtonPress}
                  disabled={isProcessing || isSpeaking || !hasPermission}
                  activeOpacity={0.8}
                >
                  {isListening ? (
                    <View style={styles.listeningIndicator}>
                      <View style={styles.soundWave}>
                        {[0, 1, 2, 3, 4].map((i) => (
                          <View key={i} style={[styles.soundBar, { marginRight: i < 4 ? 4 : 0 }]} />
                        ))}
                      </View>
                    </View>
            ) : isSpeaking ? (
                    <Text style={styles.voiceButtonIcon}>🔊</Text>
                  ) : isProcessing ? (
                    <ActivityIndicator size="large" color="white" />
            ) : (
              <Text style={styles.voiceButtonIcon}>🎤</Text>
            )}
          </TouchableOpacity>
              </LinearGradient>
            </Animated.View>
          </View>
          
          {!hasPermission && (
            <TouchableOpacity 
              style={styles.permissionButton}
              onPress={requestPermissions}
            >
              <LinearGradient
                colors={['rgba(102,126,234,0.2)', 'rgba(118,75,162,0.2)']}
                style={styles.permissionButtonGradient}
              >
                <Text style={styles.permissionButtonText}>
                  🔒 Enable Microphone
                </Text>
              </LinearGradient>
            </TouchableOpacity>
          )}
          
          <View style={styles.voiceHints}>
            <Text style={styles.voiceHintText}>
              {hasPermission 
                ? "Tap and speak, or say 'Hey Riches' to activate"
                : "Grant microphone access to get started"}
            </Text>
          </View>
        </View>

      </LinearGradient>
    </Animated.View>
  );
}

// Message Bubble Component
interface MessageBubbleProps {
  message: {
    id: string;
    type: 'user' | 'assistant';
    text: string;
    timestamp: Date;
    insights?: Insight[];
    [key: string]: unknown;
  };
  isLast?: boolean;
}

function MessageBubble({ message, isLast }: MessageBubbleProps) {
  const isUser = message.type === 'user';
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 400,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 400,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);
  
  return (
    <Animated.View
      style={[
        styles.messageBubbleContainer,
        isUser ? styles.userBubbleContainer : styles.assistantBubbleContainer,
        {
          opacity: fadeAnim,
          transform: [{ translateY: slideAnim }],
        },
      ]}
    >
      {!isUser && (
        <View style={styles.avatarContainer}>
          <LinearGradient
            colors={['#667eea', '#764ba2']}
            style={styles.avatar}
          >
            <Text style={styles.avatarText}>🔮</Text>
          </LinearGradient>
        </View>
      )}
      
    <View style={[styles.messageBubble, isUser ? styles.userBubble : styles.assistantBubble]}>
        {!isUser && (
          <LinearGradient
            colors={['rgba(102,126,234,0.1)', 'rgba(118,75,162,0.05)']}
            style={StyleSheet.absoluteFill}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          />
        )}
        
      <Text style={[styles.messageText, isUser ? styles.userText : styles.assistantText]}>
        {message.text}
      </Text>
        
      {message.insights && message.insights.length > 0 && (
        <View style={styles.insightsContainer}>
          {message.insights.map((insight: Insight, index: number) => (
              <View key={index} style={[styles.insightCard, { marginBottom: 8 }]}>
                <LinearGradient
                  colors={['rgba(102,126,234,0.15)', 'rgba(118,75,162,0.1)']}
                  style={styles.insightGradient}
                >
              <Text style={styles.insightTitle}>{insight.title}</Text>
              <Text style={styles.insightValue}>{String(insight.value)}</Text>
                  {insight.description && (
              <Text style={styles.insightDescription}>{insight.description}</Text>
                  )}
                </LinearGradient>
            </View>
          ))}
        </View>
      )}
        
      <Text style={[styles.messageTime, isUser ? styles.userTime : styles.assistantTime]}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </Text>
    </View>
      
      {isUser && (
        <View style={styles.avatarContainer}>
          <View style={styles.userAvatar}>
            <Text style={styles.userAvatarText}>👤</Text>
          </View>
        </View>
      )}
    </Animated.View>
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
  particlesContainer: {
    ...StyleSheet.absoluteFillObject,
    overflow: 'hidden',
  },
  particle: {
    position: 'absolute',
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: '#667eea',
  },
  headerBlur: {
    paddingTop: Platform.OS === 'ios' ? 20 : 10,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
    backgroundColor: 'rgba(26,26,46,0.8)',
  },
  header: {
    paddingTop: 0,
    paddingHorizontal: 20,
    paddingBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  closeButton: {
    position: 'absolute',
    top: Platform.OS === 'ios' ? 10 : 0,
    left: 20,
    zIndex: 10,
  },
  closeButtonGradient: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)',
  },
  closeButtonText: {
    color: 'white',
    fontSize: 20,
    fontWeight: '600',
  },
  titleContainer: {
    alignItems: 'center',
    width: '100%',
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
  },
  titleTextContainer: {
    alignItems: 'center',
    flex: 1,
    marginRight: 16,
  },
  logoContainer: {
    marginBottom: 0,
  },
  logoGradient: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#667eea',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  logoIcon: {
    fontSize: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.6)',
    fontWeight: '500',
  },
  conversationContainer: {
    flex: 1,
  },
  conversationContent: {
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 20,
    flexGrow: 1,
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
  },
  insightCard: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  insightGradient: {
    padding: 12,
  },
  insightTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: 'rgba(255,255,255,0.8)',
    marginBottom: 6,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  insightValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 4,
  },
  insightDescription: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.7)',
    lineHeight: 18,
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
    flexDirection: 'column',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.08)',
    padding: 20,
    borderRadius: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  processingDots: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#667eea',
  },
  dot1: {
    opacity: 0.4,
  },
  dot2: {
    opacity: 0.6,
  },
  dot3: {
    opacity: 0.8,
  },
  processingText: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.7)',
    fontWeight: '500',
  },
  voiceInterface: {
    paddingHorizontal: 20,
    paddingBottom: Platform.OS === 'ios' ? 40 : 20,
    alignItems: 'center',
  },
  statusContainer: {
    marginBottom: 24,
  },
  statusText: {
    fontSize: 18,
    fontWeight: '700',
    textAlign: 'center',
    letterSpacing: 0.5,
  },
  voiceButtonContainer: {
    position: 'relative',
    marginBottom: 20,
  },
  ripple: {
    position: 'absolute',
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#667eea',
    top: '50%',
    left: '50%',
    marginLeft: -60,
    marginTop: -60,
  },
  voiceButtonOuter: {
    shadowColor: '#667eea',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 16,
    elevation: 12,
  },
  voiceButtonGradient: {
    width: 120,
    height: 120,
    borderRadius: 60,
    padding: 3,
  },
  voiceButton: {
    flex: 1,
    borderRadius: 58,
    backgroundColor: 'rgba(255,255,255,0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  voiceButtonIcon: {
    fontSize: 48,
  },
  listeningIndicator: {
    width: 60,
    height: 60,
    justifyContent: 'center',
    alignItems: 'center',
  },
  soundWave: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 40,
  },
  soundBar: {
    width: 4,
    backgroundColor: 'white',
    borderRadius: 2,
    height: 20,
  },
  permissionButton: {
    marginBottom: 16,
    borderRadius: 12,
    overflow: 'hidden',
  },
  permissionButtonGradient: {
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderWidth: 1,
    borderColor: 'rgba(102,126,234,0.3)',
    borderRadius: 12,
  },
  permissionButtonText: {
    color: 'white',
    fontSize: 15,
    fontWeight: '600',
    textAlign: 'center',
  },
  voiceHints: {
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  voiceHintText: {
    color: 'rgba(255,255,255,0.6)',
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
    fontWeight: '500',
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'flex-start',
    paddingTop: 40,
    paddingBottom: 20,
    minHeight: height * 0.5,
  },
  emptyStateIconContainer: {
    marginBottom: 20,
  },
  emptyStateIcon: {
    width: 100,
    height: 100,
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(102,126,234,0.3)',
  },
  emptyStateEmoji: {
    fontSize: 48,
  },
  emptyStateTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 8,
  },
  emptyStateText: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.6)',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
    paddingHorizontal: 40,
  },
  suggestionChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  chip: {
    backgroundColor: 'rgba(102,126,234,0.2)',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(102,126,234,0.3)',
  },
  chipText: {
    color: 'rgba(255,255,255,0.9)',
    fontSize: 13,
    fontWeight: '600',
  },
  messageBubbleContainer: {
    flexDirection: 'row',
    marginBottom: 16,
    alignItems: 'flex-end',
  },
  userBubbleContainer: {
    justifyContent: 'flex-end',
  },
  assistantBubbleContainer: {
    justifyContent: 'flex-start',
  },
  avatarContainer: {
    marginHorizontal: 8,
  },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 18,
  },
  userAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)',
  },
  userAvatarText: {
    fontSize: 18,
  },
  transcriptionBlur: {
    marginHorizontal: 20,
    marginBottom: 20,
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)',
    backgroundColor: 'rgba(26,26,46,0.9)',
  },
  liveTranscriptionContainer: {
    padding: 16,
  },
  transcriptionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  liveTranscriptionLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.9)',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  liveTranscriptionText: {
    fontSize: 17,
    color: 'white',
    fontWeight: '500',
    lineHeight: 26,
  },
  liveTranscriptionPlaceholder: {
    fontSize: 17,
    color: 'rgba(255,255,255,0.5)',
    fontStyle: 'italic',
  },
});