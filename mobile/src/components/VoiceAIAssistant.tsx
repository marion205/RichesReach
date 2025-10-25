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
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useTheme } from '../theme/PersonalizedThemes';

const { width, height } = Dimensions.get('window');

interface VoiceAIAssistantProps {
  onClose: () => void;
  onInsightGenerated: (insight: any) => void;
}

export default function VoiceAIAssistant({ onClose, onInsightGenerated }: VoiceAIAssistantProps) {
  const theme = useTheme();
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [conversation, setConversation] = useState<any[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  
  // Animation refs
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const waveAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Request audio permissions
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

    // Start with welcome message
    speakWelcomeMessage();

    return () => {
      // Cleanup
      if (recording) {
        recording.stopAndUnloadAsync();
      }
    };
  }, []);

  const requestPermissions = async () => {
    try {
      console.log('🎤 Requesting microphone permissions...');
      const { status } = await Audio.requestPermissionsAsync();
      console.log('🎤 Permission status:', status);
      setHasPermission(status === 'granted');
      if (status !== 'granted') {
        Alert.alert(
          'Microphone Permission Required',
          'Please allow microphone access to use voice features.',
          [{ text: 'OK' }]
        );
      } else {
        console.log('🎤 Microphone permission granted!');
      }
    } catch (error) {
      console.error('Permission request error:', error);
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
    const welcomeMessage = "Hello! I'm your Wealth Oracle. I can help you with portfolio analysis, market insights, and investment strategies. What would you like to know?";
    await speakText(welcomeMessage);
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

  const startListening = async () => {
    try {
      console.log('🎤 Starting voice recording...');
      if (!hasPermission) {
        console.log('🎤 No microphone permission');
        Alert.alert('Permission Required', 'Microphone access is required for voice interaction');
        return;
      }

      console.log('🎤 Configuring audio mode...');
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

      console.log('🎤 Creating new recording...');
      const newRecording = new Audio.Recording();
      console.log('🎤 Preparing to record...');
      await newRecording.prepareToRecordAsync(recordingOptions);
      console.log('🎤 Starting recording...');
      await newRecording.startAsync();
      setRecording(newRecording);
      setIsListening(true);
      console.log('🎤 Recording started successfully!');
      
    } catch (error) {
      console.error('Failed to start recording:', error);
      Alert.alert('Recording Error', 'Failed to start recording. Please try again.');
    }
  };

  const stopListening = async () => {
    if (!recording) return;
    
    try {
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      setRecording(null);
      setIsListening(false);
      
      if (uri) {
        await processAudio(uri);
      }
    } catch (error) {
      console.error('Failed to stop recording:', error);
      setIsListening(false);
    }
  };

  const processAudio = async (audioUri: string) => {
    console.log('🎤 Processing audio:', audioUri);
    setIsProcessing(true);
    
    try {
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('audio', {
        uri: audioUri,
        type: 'audio/wav',
        name: 'voice.wav',
      } as any);

      // Send to backend for Whisper transcription and AI processing
      const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';
      console.log('🎤 Sending to API:', `${API_BASE_URL}/api/voice/process/`);
      const response = await fetch(`${API_BASE_URL}/api/voice/process/`, {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

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
        if (data.response.insights && data.response.insights.length > 0) {
          onInsightGenerated(data.response.insights[0]);
        }
      } else {
        throw new Error(data.error || 'Failed to process voice input');
      }
    } catch (error) {
      console.error('Error processing audio:', error);
      await speakText("I'm sorry, I didn't catch that. Could you please try again?");
    } finally {
      setIsProcessing(false);
    }
  };

  const speakText = async (text: string) => {
    try {
      setIsSpeaking(true);
      
      // Stop any existing speech
      Speech.stop();
      
      // Speak the text
      await Speech.speak(text, {
        language: 'en-US',
        pitch: 1.0,
        rate: 0.9,
        onDone: () => {
          setIsSpeaking(false);
        },
        onError: (error) => {
          console.error('TTS error:', error);
          setIsSpeaking(false);
        },
      });
    } catch (error) {
      console.error('Error speaking text:', error);
      setIsSpeaking(false);
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
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Text style={styles.closeButtonText}>✕</Text>
          </TouchableOpacity>
          <Text style={styles.title}>Wealth Oracle</Text>
          <Text style={styles.subtitle}>Your AI Financial Assistant</Text>
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
function MessageBubble({ message }: { message: any }) {
  const isUser = message.type === 'user';
  
  return (
    <View style={[styles.messageBubble, isUser ? styles.userBubble : styles.assistantBubble]}>
      <Text style={[styles.messageText, isUser ? styles.userText : styles.assistantText]}>
        {message.text}
      </Text>
      {message.insights && message.insights.length > 0 && (
        <View style={styles.insightsContainer}>
          {message.insights.map((insight: any, index: number) => (
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
    alignItems: 'center',
  },
  closeButton: {
    position: 'absolute',
    top: 60,
    right: 20,
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
});