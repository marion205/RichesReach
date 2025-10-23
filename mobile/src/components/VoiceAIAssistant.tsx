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
// import { BlurView } from 'expo-blur'; // Removed for Expo Go compatibility
// import { Audio } from 'expo-av'; // Removed for Expo Go compatibility
// import * as Speech from 'expo-speech'; // Removed for Expo Go compatibility
// import LottieView from 'lottie-react-native'; // Removed for Expo Go compatibility
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
  
  // Audio and animation refs
  const recording = useRef<any>(null); // Mock for Expo Go compatibility
  const sound = useRef<any>(null); // Mock for Expo Go compatibility
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const waveAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
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
      if (recording.current) {
        recording.current.stopAndUnloadAsync();
      }
      if (sound.current) {
        sound.current.unloadAsync();
      }
    };
  }, []);

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
      // Request permissions
      // Mock permission request for Expo Go compatibility
      const status = 'granted';
      if (status !== 'granted') {
        Alert.alert('Permission Required', 'Microphone access is required for voice interaction');
        return;
      }

      // Configure audio mode
      // Mock audio mode setup for Expo Go compatibility
      console.log('Audio mode set for recording');

      // Start recording
      const recordingOptions = {
        android: {
          extension: '.m4a',
          outputFormat: 'mpeg_4', // Mock for Expo Go compatibility
          audioEncoder: 'aac', // Mock for Expo Go compatibility
          sampleRate: 44100,
          numberOfChannels: 2,
          bitRate: 128000,
        },
        ios: {
          extension: '.m4a',
          outputFormat: 'mpeg4aac', // Mock for Expo Go compatibility
          audioQuality: 'high', // Mock for Expo Go compatibility
          sampleRate: 44100,
          numberOfChannels: 2,
          bitRate: 128000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
      };

      // Mock recording creation for Expo Go compatibility
      recording.current = { 
        prepareToRecordAsync: () => Promise.resolve(),
        startAsync: () => Promise.resolve(), 
        stopAndUnloadAsync: () => Promise.resolve(),
        getURI: () => 'mock://recording.m4a'
      };
      await recording.current.prepareToRecordAsync(recordingOptions);
      await recording.current.startAsync();
      
      setIsListening(true);
      
    } catch (error) {
      console.error('Error starting recording:', error);
      Alert.alert('Error', 'Failed to start voice recording');
    }
  };

  const stopListening = async () => {
    try {
      if (!recording.current) return;

      await recording.current.stopAndUnloadAsync();
      const uri = recording.current.getURI();
      
      setIsListening(false);
      setIsProcessing(true);

      // Process the audio
      if (uri) {
        await processAudio(uri);
      }

    } catch (error) {
      console.error('Error stopping recording:', error);
      setIsListening(false);
      setIsProcessing(false);
    }
  };

  const processAudio = async (audioUri: string) => {
    try {
      // Simulate audio processing and AI response
      // In a real implementation, you would:
      // 1. Send audio to speech-to-text service
      // 2. Process the text with AI
      // 3. Generate response
      
      const mockTranscription = "What's my portfolio performance this month?";
      const mockResponse = {
        text: "Your portfolio is up 8.5% this month, outperforming the S&P 500 by 2.3%. Your top performers are technology stocks, particularly your AI and semiconductor holdings. Would you like me to analyze any specific positions or suggest rebalancing opportunities?",
        insights: [
          {
            type: 'performance',
            title: 'Strong Monthly Performance',
            value: '+8.5%',
            description: 'Outperforming benchmark by 2.3%'
          },
          {
            type: 'sector',
            title: 'Technology Leading',
            value: 'Tech +12.3%',
            description: 'AI and semiconductor stocks driving gains'
          }
        ]
      };

      // Add to conversation
      const newConversation = [
        ...conversation,
        {
          id: Date.now(),
          type: 'user',
          text: mockTranscription,
          timestamp: new Date(),
        },
        {
          id: Date.now() + 1,
          type: 'assistant',
          text: mockResponse.text,
          insights: mockResponse.insights,
          timestamp: new Date(),
        }
      ];

      setConversation(newConversation);
      setCurrentQuestion(mockTranscription);

      // Speak the response
      await speakText(mockResponse.text);

      // Generate insight if applicable
      if (mockResponse.insights.length > 0) {
        onInsightGenerated(mockResponse.insights[0]);
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
      // Mock speech stop for Expo Go compatibility
      console.log('Speech stopped');
      
      // Mock speech for Expo Go compatibility
      console.log('Speaking:', text);
      // Simulate speech duration
      setTimeout(() => setIsSpeaking(false), 2000);

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
      <View intensity={30} style={styles.blurContainer}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <View style={styles.oracleAvatar}>
              <Text style={styles.oracleEmoji}>🔮</Text>
            </View>
            <View>
              <Text style={styles.headerTitle}>Wealth Oracle</Text>
              <Text style={styles.headerSubtitle}>Voice Assistant</Text>
            </View>
          </View>
          
          <TouchableOpacity style={styles.closeButton} onPress={onClose}>
            <Text style={styles.closeButtonText}>✕</Text>
          </TouchableOpacity>
        </View>

        {/* Conversation */}
        <ScrollView style={styles.conversationContainer} showsVerticalScrollIndicator={false}>
          {conversation.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          
          {isProcessing && (
            <View style={styles.processingBubble}>
              <ActivityIndicator
                size="small"
                color="#8B5CF6"
                style={styles.processingAnimation}
              />
              <Text style={styles.processingText}>Oracle is thinking...</Text>
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
            disabled={isProcessing || isSpeaking}
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
      </View>
    </Animated.View>
  );
}

// Message Bubble Component
function MessageBubble({ message }: { message: any }) {
  const isUser = message.type === 'user';
  
  return (
    <View style={[styles.messageContainer, isUser ? styles.userMessage : styles.assistantMessage]}>
      <View style={[styles.messageBubble, isUser ? styles.userBubble : styles.assistantBubble]}>
        <Text style={[styles.messageText, isUser ? styles.userText : styles.assistantText]}>
          {message.text}
        </Text>
        
        {message.insights && (
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
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 1000,
  },
  blurContainer: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 60,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  oracleAvatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#667eea',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  oracleEmoji: {
    fontSize: 24,
  },
  headerTitle: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
  },
  headerSubtitle: {
    color: 'rgba(255,255,255,0.7)',
    fontSize: 14,
    marginTop: 2,
  },
  closeButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeButtonText: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
  },
  conversationContainer: {
    flex: 1,
    paddingHorizontal: 20,
  },
  messageContainer: {
    marginBottom: 16,
  },
  userMessage: {
    alignItems: 'flex-end',
  },
  assistantMessage: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 16,
    borderRadius: 20,
  },
  userBubble: {
    backgroundColor: '#667eea',
  },
  assistantBubble: {
    backgroundColor: 'rgba(255,255,255,0.9)',
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userText: {
    color: 'white',
  },
  assistantText: {
    color: '#1a1a1a',
  },
  insightsContainer: {
    marginTop: 12,
  },
  insightItem: {
    backgroundColor: 'rgba(102, 126, 234, 0.1)',
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
  },
  insightTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#667eea',
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
