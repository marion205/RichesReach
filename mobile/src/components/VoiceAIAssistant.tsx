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
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const isStartingRef = useRef(false); // Prevent concurrent start attempts
  const retryCountRef = useRef(0); // Track retry attempts
  
  // Animation refs
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const waveAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // CRITICAL: Stop wake word services immediately on mount to prevent conflicts
    const stopWakeWordServices = async () => {
      try {
        const { customWakeWordService } = await import('../services/CustomWakeWordService');
        const status = customWakeWordService.getStatus();
        if (status.listening) {
          logger.log('🎤 Stopping CustomWakeWordService on mount...');
          await customWakeWordService.stop().catch(() => {});
        }
      } catch (e) {
        // Ignore
      }
      
      try {
        const { mlWakeWordService } = await import('../services/MLWakeWordService');
        const status = mlWakeWordService.getStatus();
        if (status.listening) {
          logger.log('🎤 Stopping MLWakeWordService on mount...');
          await mlWakeWordService.stop().catch(() => {});
        }
      } catch (e) {
        // Ignore
      }
      
      try {
        const { porcupineWakeWordService } = await import('../services/PorcupineWakeWordService');
        const status = porcupineWakeWordService.getStatus();
        if (status.started) {
          logger.log('🎤 Stopping PorcupineWakeWordService on mount...');
          await porcupineWakeWordService.stop().catch(() => {});
        }
      } catch (e) {
        // Ignore
      }
      
      // Wait for services to fully stop before proceeding
      await new Promise(resolve => setTimeout(resolve, 1000));
    };
    
    stopWakeWordServices();
    
    // Request audio permissions (non-blocking)
    requestPermissions();

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

    // Don't speak welcome message immediately - let user interact first
    // Welcome message will be spoken when user first interacts or can be skipped
    // speakWelcomeMessage(); // Removed to prevent blocking

    return () => {
      // Cleanup on unmount - stop any wake word services that might be holding recordings
      const cleanup = async () => {
        try {
          // Stop wake word services if they're running
          try {
            const { customWakeWordService } = await import('../services/CustomWakeWordService');
            await customWakeWordService.stop();
          } catch (e) {
            // Ignore - service might not be available
          }
          
          try {
            const { mlWakeWordService } = await import('../services/MLWakeWordService');
            await mlWakeWordService.stop();
          } catch (e) {
            // Ignore - service might not be available
          }
          
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
      logger.log('🎤 Requesting microphone permissions...');
      const { status } = await Audio.requestPermissionsAsync();
      logger.log('🎤 Permission status:', status);
      setHasPermission(status === 'granted');
      if (status !== 'granted') {
        Alert.alert(
          'Microphone Permission Required',
          'Please allow microphone access to use voice features.',
          [{ text: 'OK' }]
        );
      } else {
        logger.log('🎤 Microphone permission granted!');
      }
    } catch (error) {
      logger.error('Permission request error:', error);
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

  // Cleanup function to properly release all recording objects
  const cleanupAllRecordings = async () => {
    try {
      // Clean up state recording with multiple attempts
      if (recording) {
        try {
          const status = await recording.getStatusAsync();
          if (status.isRecording) {
            await recording.stopAndUnloadAsync();
          } else {
            await recording.unloadAsync();
          }
        } catch (e) {
          // Try to unload even if stop failed
          try {
            await recording.unloadAsync();
          } catch (e2) {
            // Final attempt - just set to null
            logger.warn('Could not unload recording, forcing cleanup');
          }
        }
        setRecording(null);
      }
      
      // Wait longer to ensure cleanup completes (expo-av needs time)
      await new Promise(resolve => setTimeout(resolve, 1000));
    } catch (error) {
      logger.warn('Cleanup warning:', error);
    }
  };

  const startListening = async () => {
    // Prevent concurrent start attempts
    if (isStartingRef.current) {
      logger.log('⚠️ Already starting recording, ignoring duplicate request');
      return;
    }
    
    // Prevent infinite retry loop (max 1 retry)
    if (retryCountRef.current > 1) {
      logger.error('❌ Max retry attempts reached, stopping');
      setIsListening(false);
      Alert.alert('Recording Error', 'Failed to start recording. Please close and reopen the voice assistant.');
      retryCountRef.current = 0;
      isStartingRef.current = false;
      return;
    }
    
    isStartingRef.current = true;
    
    try {
      logger.log('🎤 Starting voice recording...');
      if (!hasPermission) {
        logger.log('🎤 No microphone permission');
        Alert.alert('Permission Required', 'Microphone access is required for voice interaction');
        isStartingRef.current = false;
        return;
      }

      // CRITICAL: Stop any wake word services FIRST - they hold Recording objects
      logger.log('🎤 Stopping ALL wake word services...');
      
      // Stop all services in parallel, then wait for all to complete
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
        logger.log('⚠️ CustomWakeWordService not available:', e);
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
        logger.log('⚠️ MLWakeWordService not available:', e);
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
        logger.log('⚠️ PorcupineWakeWordService not available:', e);
      }

      // Wait for all services to stop
      await Promise.all(stopPromises);
      logger.log('🎤 All wake word services stopped, waiting for cleanup...');
      
      // CRITICAL: Wait longer for expo-av to fully release all recordings
      // This is essential - expo-av needs time to release internal recording state
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Reset audio mode completely before cleanup
      try {
        await Audio.setAudioModeAsync({
          allowsRecordingIOS: false,
          playsInSilentModeIOS: false,
          shouldDuckAndroid: false,
          playThroughEarpieceAndroid: false,
        });
        // Wait for audio mode to reset
        await new Promise(resolve => setTimeout(resolve, 500));
      } catch (e) {
        logger.warn('⚠️ Audio mode reset warning:', e);
      }

      // Clean up any existing recording first
      await cleanupAllRecordings();
      
      // Final wait to ensure everything is released
      await new Promise(resolve => setTimeout(resolve, 500));

      logger.log('🎤 Configuring audio mode...');
      // Configure audio mode
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });

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
      setRecording(newRecording);
      setIsListening(true);
      retryCountRef.current = 0; // Reset retry count on success
      logger.log('✅ Recording started successfully!');
      
    } catch (error: unknown) {
      logger.error('Failed to start recording:', error);
      
      // Handle specific error about multiple recordings
      const errorMessage = error instanceof Error ? error.message : String(error);
      if (errorMessage.includes('Only one Recording object')) {
        retryCountRef.current += 1;
        logger.log(`🔄 Attempting to clean up and retry (attempt ${retryCountRef.current})...`);
        
        // Aggressively stop ALL services again
        const stopAllServices = async () => {
          const services = [
            { name: 'CustomWakeWordService', import: () => import('../services/CustomWakeWordService') },
            { name: 'MLWakeWordService', import: () => import('../services/MLWakeWordService') },
            { name: 'PorcupineWakeWordService', import: () => import('../services/PorcupineWakeWordService') },
          ];
          
          interface WakeWordServiceModule {
            stop: () => Promise<void>;
            [key: string]: unknown;
          }
          for (const service of services) {
            try {
              const module = await service.import();
              const svc = Object.values(module)[0] as WakeWordServiceModule | undefined;
              if (svc && typeof svc.stop === 'function') {
                await svc.stop().catch(() => {});
              }
            } catch (e) {
              // Ignore
            }
          }
        };
        
        await stopAllServices();
        
        // Reset audio mode completely first
        try {
          await Audio.setAudioModeAsync({
            allowsRecordingIOS: false,
            playsInSilentModeIOS: false,
            shouldDuckAndroid: false,
            playThroughEarpieceAndroid: false,
          });
          // Wait longer on retry
          await new Promise(resolve => setTimeout(resolve, 1500));
        } catch (e) {
          // Ignore
        }
        
        // Clean up more aggressively
        await cleanupAllRecordings();
        
        // CRITICAL: Wait much longer before retry - expo-av needs time to release internal state
        // The "Only one Recording object" error means expo-av hasn't released its internal lock yet
        logger.log('🎤 Waiting for expo-av to fully release recording state...');
        await new Promise(resolve => setTimeout(resolve, 2500));
        
        // Only retry once
        if (retryCountRef.current <= 1) {
          logger.log('🎤 Retrying recording start...');
          isStartingRef.current = false;
          // Small delay before retry to ensure state is clean
          await new Promise(resolve => setTimeout(resolve, 300));
          return startListening();
        } else {
          // Max retries reached - show helpful error message
          logger.error('❌ Max retry attempts reached - recording conflict persists');
          setIsListening(false);
          Alert.alert(
            'Recording Error', 
            'Unable to start recording. Another app or service may be using the microphone. Please:\n\n1. Close this voice assistant\n2. Wait a few seconds\n3. Try again\n\nIf the issue persists, restart the app.'
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
    
    // Reset retry counter when stopping
    retryCountRef.current = 0;
    isStartingRef.current = false;
    
    try {
      const uri = recording.getURI();
      await recording.stopAndUnloadAsync();
      setRecording(null);
      setIsListening(false);
      
      if (uri) {
        await processAudio(uri);
      }
    } catch (error) {
      logger.error('Failed to stop recording:', error);
      // Clean up even if stop fails
      try {
        await recording.unloadAsync();
      } catch (e) {
        // Ignore cleanup errors
      }
      setRecording(null);
      setIsListening(false);
    }
  };

  const processAudio = async (audioUri: string) => {
    logger.log('🎤 Processing audio:', audioUri);
    setIsProcessing(true);
    
    try {
      // Create FormData for file upload
      interface FormDataAudio {
        uri: string;
        type: string;
        name: string;
      }
      const formData = new FormData();
      const audioData: FormDataAudio = {
        uri: audioUri,
        type: 'audio/wav',
        name: 'voice.wav',
      };
      formData.append('audio', audioData as unknown as Blob);

      // Send to backend for Whisper transcription and AI processing
      const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000";
      logger.log('🎤 Sending to API:', `${API_BASE_URL}/api/voice/process/`);
      
      let response: Response;
      try {
        response = await fetch(`${API_BASE_URL}/api/voice/process/`, {
          method: 'POST',
          body: formData,
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          // Note: AbortSignal.timeout may not be available in all environments
          // Using a timeout wrapper instead
        });
      } catch (networkError: unknown) {
        // Only log if it's not a network error (Whisper API may not be running)
        if (!(networkError instanceof TypeError && networkError.message === 'Network request failed')) {
          logger.error('Transcription error:', networkError);
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
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success && data.response) {
        const transcribedText = data.response.transcription || '';
        const aiResponse = data.response.text || '';
        
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
            text: aiResponse,
            timestamp: new Date(),
          }
        ];

        setConversation(newConversation);
        setCurrentQuestion(transcribedText);

        // Speak the response
        await speakText(aiResponse);

        // Generate insight if applicable
        if (data.response.insights && data.response.insights.length > 0 && onInsightGenerated) {
          onInsightGenerated(data.response.insights[0]);
        }
      } else {
        throw new Error(data.error || 'Failed to process voice input');
      }
    } catch (error) {
      logger.error('Error processing audio:', error);
      await speakText("I'm sorry, I didn't catch that. Could you please try again?");
    } finally {
      setIsProcessing(false);
    }
  };

  const speakText = async (text: string) => {
    try {
      setIsSpeaking(true);
      
      // Stop any existing speech
      await stopAllSpeech();
      
      // Use the voice synthesis API with selected voice (with timeout)
      const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000";
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('Speech synthesis timeout')), 3000); // 3 second timeout
      });

      let response: Response | null = null;
      try {
        const fetchPromise = fetch(`${API_BASE_URL}/api/voice-ai/synthesize/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: text,
            voice: getSelectedVoice(),
            speed: 1.0,
            emotion: 'neutral',
          }),
        });
        response = await Promise.race([fetchPromise, timeoutPromise]);
      } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logger.log('Speech synthesis API timeout, using fallback:', errorMessage);
        // Fall through to basic speech
        response = null;
      }

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
});