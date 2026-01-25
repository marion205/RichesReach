import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  FlatList,
  TextInput,
  Alert,
  Dimensions,
  StatusBar,
  KeyboardAvoidingView,
  Platform,
  Animated,
  PanResponder,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Video } from 'expo-av';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import logger from '../utils/logger';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface RichesLiveStreamingProps {
  visible: boolean;
  onClose: () => void;
  circleId: string;
  isHost: boolean;
  circleName: string;
}

interface LiveMessage {
  id: string;
  user: string;
  message: string;
  timestamp: number;
  type: 'message' | 'reaction' | 'join' | 'leave';
}

interface LiveViewer {
  id: string;
  name: string;
  avatar: string;
  isTyping?: boolean;
}

export default function RichesLiveStreaming({
  visible,
  onClose,
  circleId,
  isHost,
  circleName,
}: RichesLiveStreamingProps) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [viewerCount, setViewerCount] = useState(0);
  const [messages, setMessages] = useState<LiveMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [viewers, setViewers] = useState<LiveViewer[]>([]);
  const [showChat, setShowChat] = useState(true);
  const [showViewers, setShowViewers] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isCameraOn, setIsCameraOn] = useState(true);
  const [streamQuality, setStreamQuality] = useState<'low' | 'medium' | 'high'>('medium');
  const [error, setError] = useState<string | null>(null);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const maxRetries = 3;
  
  const videoRef = useRef<Video>(null);
  const chatInputRef = useRef<TextInput>(null);
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const slideAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const errorAnim = useRef(new Animated.Value(0)).current;

  // Retry delay with exponential backoff
  const getRetryDelay = (attempt: number) => Math.min(1000 * Math.pow(2, attempt), 30000);

  // Mock live viewers (with better avatars)
  const mockViewers: LiveViewer[] = [
    { id: '1', name: 'Alex Rivera', avatar: 'https://via.placeholder.com/40/FF0050/ffffff?text=AR' },
    { id: '2', name: 'Sarah Chen', avatar: 'https://via.placeholder.com/40/00FF00/000000?text=SC' },
    { id: '3', name: 'Marcus Johnson', avatar: 'https://via.placeholder.com/40/FFAA00/000000?text=MJ' },
    { id: '4', name: 'Dr. Maria Rodriguez', avatar: 'https://via.placeholder.com/40/9900FF/ffffff?text=MR' },
    { id: '5', name: 'James Thompson', avatar: 'https://via.placeholder.com/40/FF0000/ffffff?text=JT' },
  ];

  // Mock live messages
  const mockMessages: LiveMessage[] = [
    {
      id: '1',
      user: 'Alex Rivera',
      message: 'Great insights on the market today!',
      timestamp: Date.now() - 30000,
      type: 'message',
    },
    {
      id: '2',
      user: 'Sarah Chen',
      message: 'What do you think about NVDA?',
      timestamp: Date.now() - 25000,
      type: 'message',
    },
    {
      id: '3',
      user: 'Marcus Johnson',
      message: '🔥',
      timestamp: Date.now() - 20000,
      type: 'reaction',
    },
    {
      id: '4',
      user: 'Dr. Maria Rodriguez',
      message: 'joined the stream',
      timestamp: Date.now() - 15000,
      type: 'join',
    },
    {
      id: '5',
      user: 'James Thompson',
      message: 'Love the real-time analysis!',
      timestamp: Date.now() - 10000,
      type: 'message',
    },
  ];

  useEffect(() => {
    if (visible) {
      setViewers(mockViewers);
      setMessages(mockMessages);
      setViewerCount(mockViewers.length);
      setRetryCount(0);
      
      // Simulate live streaming
      if (isHost) {
        setIsStreaming(true);
        startLiveStream();
      } else {
        joinLiveStream();
      }

      // Pulse animation for live dot
      const pulseLoop = () => {
        pulseAnim.setValue(1);
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1.5, duration: 1000, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: 1000, useNativeDriver: true }),
        ]).start(pulseLoop);
      };
      pulseLoop();

      // Auto-hide UI after 3 seconds
      const timer = setTimeout(() => {
        Animated.timing(fadeAnim, {
          toValue: 0.3,
          duration: 500,
          useNativeDriver: true,
        }).start();
      }, 3000);

      return () => {
        clearTimeout(timer);
        pulseAnim.stopAnimation();
      };
    }
  }, [visible]);

  // Error handling function
  const handleError = (error: Error, context: string, fallbackAction?: () => void, canRetry = true) => {
    logger.error(`[${context}] Error:`, error);
    const errorMsg = `${context}: ${error.message || 'An unexpected error occurred'}`;
    setError(errorMsg);
    
    // Shake animation for error
    errorAnim.setValue(0);
    Animated.sequence([
      Animated.timing(errorAnim, { toValue: 10, duration: 100, useNativeDriver: true }),
      Animated.timing(errorAnim, { toValue: -10, duration: 100, useNativeDriver: true }),
      Animated.timing(errorAnim, { toValue: 0, duration: 100, useNativeDriver: true }),
    ]).start();

    // Show alert with retry option
    Alert.alert('Streaming Error', errorMsg, [
      { text: 'Close', onPress: endLiveStream },
      ...(canRetry ? [{ text: 'Retry', onPress: () => retryConnection(context, fallbackAction) }] : []),
    ]);

    // Auto-retry if allowed
    if (canRetry && retryCount < maxRetries) {
      const delay = getRetryDelay(retryCount);
      setIsReconnecting(true);
      setTimeout(() => {
        setRetryCount(prev => prev + 1);
        setIsReconnecting(false);
        if (fallbackAction) fallbackAction();
        // Simulate reconnection
        logger.log('🔄 Attempting reconnection...');
      }, delay);
    }
  };

  // Retry connection with exponential backoff
  const retryConnection = (context: string, fallbackAction?: () => void) => {
    setError(null);
    setRetryCount(prev => prev + 1);
    if (fallbackAction) fallbackAction();
    logger.log('🔄 Retrying connection...');
  };

  const startLiveStream = () => {
    try {
      logger.log('🎥 Starting live stream for circle:', circleName);
      // Simulate potential error
      if (Math.random() < 0.1) { // 10% chance of error for demo
        throw new Error('Camera access denied');
      }
    } catch (error) {
      handleError(error as Error, 'Start Stream Failed');
    }
  };

  const joinLiveStream = () => {
    try {
      logger.log('📺 Joining live stream for circle:', circleName);
      // Simulate potential error
      if (Math.random() < 0.1) { // 10% chance of error for demo
        throw new Error('Stream not found');
      }
    } catch (error) {
      handleError(error as Error, 'Join Stream Failed');
    }
  };

  const endLiveStream = () => {
    try {
      setIsStreaming(false);
      setError(null);
      onClose();
      logger.log('🔴 Live stream ended');
    } catch (error) {
      logger.error('End stream error:', error);
    }
  };

  const sendMessage = () => {
    if (!newMessage.trim()) return;

    const message: LiveMessage = {
      id: Date.now().toString(),
      user: 'You',
      message: newMessage.trim(),
      timestamp: Date.now(),
      type: 'message',
    };

    setMessages(prev => [...prev, message]);
    setNewMessage('');
    chatInputRef.current?.blur();
    
    // Simulate other viewers responding
    setTimeout(() => {
      const responses = [
        'Great question!',
        'I agree with that',
        'Thanks for sharing!',
        'Interesting point',
        '👍',
      ];
      const randomResponse = responses[Math.floor(Math.random() * responses.length)];
      const randomViewer = mockViewers[Math.floor(Math.random() * mockViewers.length)];
      
      const responseMessage: LiveMessage = {
        id: (Date.now() + 1).toString(),
        user: randomViewer.name,
        message: randomResponse,
        timestamp: Date.now(),
        type: 'message',
      };
      
      setMessages(prev => [...prev, responseMessage]);
    }, 1000 + Math.random() * 2000);
  };

  const sendReaction = (reaction: string) => {
    const reactionMessage: LiveMessage = {
      id: Date.now().toString(),
      user: 'You',
      message: reaction,
      timestamp: Date.now(),
      type: 'reaction',
    };

    setMessages(prev => [...prev, reactionMessage]);
  };

  const toggleMute = () => {
    try {
      setIsMuted(!isMuted);
      logger.log('🔇 Mute toggled:', !isMuted);
    } catch (error) {
      handleError(error as Error, 'Mute Toggle Failed');
    }
  };

  const toggleCamera = () => {
    try {
      setIsCameraOn(!isCameraOn);
      logger.log('📹 Camera toggled:', !isCameraOn);
    } catch (error) {
      handleError(error as Error, 'Camera Toggle Failed');
    }
  };

  const toggleChat = () => {
    setShowChat(!showChat);
    Animated.timing(slideAnim, {
      toValue: showChat ? -300 : 0,
      duration: 300,
      useNativeDriver: true,
    }).start();
  };

  const showUI = () => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 200,
      useNativeDriver: true,
    }).start();
  };

  const renderMessage = ({ item }: { item: LiveMessage }) => {
    const isReaction = item.type === 'reaction';
    const isJoinLeave = item.type === 'join' || item.type === 'leave';
    
    return (
      <View style={[styles.messageContainer, isReaction && styles.reactionContainer, isJoinLeave && styles.systemMessageContainer]}>
        <Text style={[styles.messageUser, isReaction && styles.reactionUser, isJoinLeave && styles.systemUser]}>
          {item.user}
        </Text>
        <Text style={[styles.messageText, isReaction && styles.reactionText, isJoinLeave && styles.systemText]}>
          {item.message}
        </Text>
      </View>
    );
  };

  const renderViewer = ({ item }: { item: LiveViewer }) => (
    <View style={styles.viewerItem}>
      <View style={[styles.viewerAvatar, { backgroundColor: `hsl(${Math.random() * 360}, 70%, 50%)` }]}>
        <Text style={styles.viewerAvatarText}>
          {item.name.split(' ').map(n => n[0]).join('')}
        </Text>
      </View>
      <Text style={styles.viewerName} numberOfLines={1}>{item.name}</Text>
      {item.isTyping && <View style={styles.typingIndicator} />}
    </View>
  );

  // Error Overlay
  const renderErrorOverlay = () => (
    <Animated.View style={[styles.errorOverlay, { transform: [{ translateX: errorAnim }] }]}>
      <View style={styles.errorContent}>
        <Ionicons name="alert-circle" size={48} color="#FF3B30" />
        <Text style={styles.errorTitle}>Connection Issue</Text>
        <Text style={styles.errorText}>{error}</Text>
        {isReconnecting && (
          <View style={styles.reconnectingContainer}>
            <ActivityIndicator size="small" color="#FF3B30" />
            <Text style={styles.reconnectingText}>Reconnecting...</Text>
          </View>
        )}
        <TouchableOpacity style={styles.retryButton} onPress={() => {
          setError(null);
          retryConnection('Manual Retry');
        }}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    </Animated.View>
  );

  if (!visible) return null;

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="fullScreen"
      onRequestClose={onClose}
    >
      <StatusBar barStyle="light-content" hidden />
      <View style={styles.container}>
        {/* Error Overlay */}
        {error && renderErrorOverlay()}

        {/* Main Video View */}
        <TouchableOpacity 
          style={styles.videoContainer} 
          activeOpacity={1}
          onPress={showUI}
          disabled={!!error}
        >
          {isHost ? (
            <View style={styles.hostVideoView}>
              <LinearGradient
                colors={['rgba(0,0,0,0.3)', 'rgba(26,26,26,0.8)']}
                style={styles.hostVideoGradient}
              >
                <Ionicons name={isCameraOn ? "videocam" : "videocam-off"} size={48} color="#FF3B30" style={styles.hostVideoIcon} />
                <Text style={styles.hostVideoText}>
                  {isCameraOn ? '📹 Live Camera Feed' : '📹 Camera Off'}
                </Text>
                <Text style={styles.hostVideoSubtext}>
                  {isMuted ? '🔇 Muted' : '🎤 Live Audio • HD'}
                </Text>
              </LinearGradient>
            </View>
          ) : (
            <View style={styles.viewerVideoView}>
              <LinearGradient
                colors={['rgba(0,0,0,0.3)', 'rgba(26,26,26,0.8)']}
                style={styles.viewerVideoGradient}
              >
                <Ionicons name="play-circle" size={60} color="#FF3B30" style={styles.viewerVideoIcon} />
                <Text style={styles.viewerVideoText}>
                  📺 Watching Live Stream
                </Text>
                <Text style={styles.viewerVideoSubtext}>
                  {circleName} • {viewerCount} viewers
                </Text>
              </LinearGradient>
            </View>
          )}
        </TouchableOpacity>

        {/* Top Controls - Improved with better spacing and icons */}
        <Animated.View style={[styles.topControls, { opacity: fadeAnim }]}>
          <View style={styles.topLeft}>
            <TouchableOpacity style={styles.closeButton} onPress={endLiveStream}>
              <Ionicons name="close" size={24} color="#ffffff" />
            </TouchableOpacity>
            <View style={styles.liveIndicator}>
              <Animated.View style={[styles.liveDot, { transform: [{ scale: pulseAnim }] }]} />
              <Text style={styles.liveText}>LIVE</Text>
            </View>
            <Text style={styles.viewerCount}>{viewerCount} watching</Text>
          </View>
          
          <View style={styles.topRight}>
            <TouchableOpacity 
              style={styles.controlButton} 
              onPress={() => setShowViewers(!showViewers)}
            >
              <Ionicons name="people" size={20} color="#ffffff" />
            </TouchableOpacity>
            <TouchableOpacity style={styles.controlButton} onPress={toggleChat}>
              <Ionicons name={showChat ? "chatbubble-ellipses" : "chatbubble-outline"} size={20} color="#ffffff" />
            </TouchableOpacity>
            <TouchableOpacity style={styles.settingsButton}>
              <Ionicons name="settings-outline" size={20} color="#ffffff" />
            </TouchableOpacity>
          </View>
        </Animated.View>

        {/* Host Controls - More polished with icons and better layout */}
        {isHost && (
          <Animated.View style={[styles.hostControls, { opacity: fadeAnim }]}>
            <TouchableOpacity 
              style={[styles.hostControlButton, isMuted && styles.hostControlButtonActive]} 
              onPress={toggleMute}
            >
              <Ionicons name={isMuted ? "mic-off" : "mic"} size={20} color="#ffffff" />
            </TouchableOpacity>
            <TouchableOpacity 
              style={[styles.hostControlButton, !isCameraOn && styles.hostControlButtonActive]} 
              onPress={toggleCamera}
            >
              <Ionicons name={isCameraOn ? "videocam" : "videocam-off"} size={20} color="#ffffff" />
            </TouchableOpacity>
            <TouchableOpacity style={styles.qualityButton} onPress={() => setStreamQuality(prev => prev === 'high' ? 'low' : prev === 'low' ? 'medium' : 'high')}>
              <Text style={styles.qualityText}>{streamQuality.toUpperCase()}</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.endStreamButton} onPress={endLiveStream}>
              <LinearGradient colors={['#FF3B30', '#FF6B6B']} style={styles.endStreamGradient}>
                <Ionicons name="close-circle" size={20} color="#ffffff" />
                <Text style={styles.endStreamText}>End</Text>
              </LinearGradient>
            </TouchableOpacity>
          </Animated.View>
        )}

        {/* Chat Panel - Improved with better scrolling and typing indicator */}
        <Animated.View 
          style={[
            styles.chatPanel, 
            { 
              opacity: fadeAnim,
              transform: [{ translateX: slideAnim }]
            }
          ]}
        >
          <View style={styles.chatHeader}>
            <View style={styles.chatHeaderLeft}>
              <Ionicons name="chatbubble-ellipses" size={20} color="#ffffff" />
              <Text style={styles.chatTitle}>Live Chat ({messages.length})</Text>
            </View>
            <TouchableOpacity onPress={toggleChat}>
              <Ionicons name="close" size={20} color="#ffffff" />
            </TouchableOpacity>
          </View>
          
          <FlatList
            data={messages}
            renderItem={renderMessage}
            keyExtractor={(item) => item.id}
            style={styles.messagesList}
            showsVerticalScrollIndicator={false}
            inverted
            contentContainerStyle={styles.messagesContent}
          />
          
          {/* Typing Indicator */}
          {Math.random() > 0.7 && (
            <View style={styles.typingIndicatorContainer}>
              <View style={styles.typingDots}>
                <Animated.View style={[styles.dot, styles.dot1, { transform: [{ scale: pulseAnim }] }]} />
                <Animated.View style={[styles.dot, styles.dot2, { transform: [{ scale: pulseAnim }] }]} />
                <Animated.View style={[styles.dot, styles.dot3, { transform: [{ scale: pulseAnim }] }]} />
              </View>
              <Text style={styles.typingText}>Someone is typing...</Text>
            </View>
          )}
          
          <View style={styles.chatInputContainer}>
            <TextInput
              ref={chatInputRef}
              style={styles.chatInput}
              placeholder="Say something..."
              placeholderTextColor="#999"
              value={newMessage}
              onChangeText={setNewMessage}
              onSubmitEditing={sendMessage}
              multiline
              maxLength={200}
            />
            <TouchableOpacity style={styles.sendButton} onPress={sendMessage} disabled={!newMessage.trim()}>
              <Ionicons name="send" size={20} color={newMessage.trim() ? "#ffffff" : "#666"} />
            </TouchableOpacity>
          </View>
        </Animated.View>

        {/* Quick Reactions - More emojis, better layout */}
        <Animated.View style={[styles.reactionsPanel, { opacity: fadeAnim }]}>
          {['❤️', '🔥', '👍', '😂', '💯', '🎉'].map((emoji, index) => (
            <TouchableOpacity 
              key={emoji} 
              style={styles.reactionButton} 
              onPress={() => sendReaction(emoji)}
              activeOpacity={0.7}
            >
              <Text style={styles.reactionText}>{emoji}</Text>
            </TouchableOpacity>
          ))}
        </Animated.View>

        {/* Viewers Panel - Improved with search and online status */}
        {showViewers && (
          <Animated.View style={[styles.viewersPanel, { opacity: fadeAnim }]}>
            <View style={styles.viewersHeader}>
              <View style={styles.viewersHeaderLeft}>
                <Ionicons name="people" size={20} color="#ffffff" />
                <Text style={styles.viewersTitle}>Viewers ({viewerCount})</Text>
              </View>
              <TouchableOpacity onPress={() => setShowViewers(false)}>
                <Ionicons name="close" size={20} color="#ffffff" />
              </TouchableOpacity>
            </View>
            <FlatList
              data={viewers}
              renderItem={renderViewer}
              keyExtractor={(item) => item.id}
              style={styles.viewersList}
              showsVerticalScrollIndicator={false}
              contentContainerStyle={styles.viewersContent}
            />
          </Animated.View>
        )}
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  videoContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  hostVideoView: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  hostVideoGradient: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  hostVideoIcon: {
    marginBottom: 16,
  },
  hostVideoText: {
    fontSize: 24,
    color: '#ffffff',
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  hostVideoSubtext: {
    fontSize: 16,
    color: '#cccccc',
    textAlign: 'center',
  },
  viewerVideoView: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  viewerVideoGradient: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  viewerVideoIcon: {
    marginBottom: 16,
  },
  viewerVideoText: {
    fontSize: 24,
    color: '#ffffff',
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  viewerVideoSubtext: {
    fontSize: 16,
    color: '#cccccc',
    textAlign: 'center',
  },
  topControls: {
    position: 'absolute',
    top: StatusBar.currentHeight || 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 10,
    zIndex: 10,
  },
  topLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  closeButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  closeButtonText: {
    color: '#ffffff',
    fontSize: 24,
    fontWeight: 'bold',
  },
  liveIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,59,48,0.9)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 16,
  },
  liveDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#ffffff',
    marginRight: 6,
  },
  liveText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold',
    textTransform: 'uppercase',
  },
  viewerCount: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  topRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  controlButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 12,
  },
  controlButtonText: {
    color: '#ffffff',
    fontSize: 20,
  },
  settingsButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 12,
  },
  hostControls: {
    position: 'absolute',
    bottom: 120,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
    zIndex: 10,
  },
  hostControlButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 12,
    borderWidth: 2,
    borderColor: 'rgba(255,255,255,0.3)',
  },
  hostControlButtonActive: {
    backgroundColor: '#FF3B30',
    borderColor: '#FF6B6B',
  },
  hostControlButtonText: {
    color: '#ffffff',
    fontSize: 24,
  },
  qualityButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 12,
  },
  qualityText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  endStreamButton: {
    marginLeft: 24,
  },
  endStreamGradient: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 20,
    flexDirection: 'row',
    alignItems: 'center',
  },
  endStreamText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 6,
  },
  chatPanel: {
    position: 'absolute',
    right: 0,
    top: 100,
    bottom: 120,
    width: 320,
    backgroundColor: 'rgba(0,0,0,0.85)',
    borderLeftWidth: 1,
    borderLeftColor: 'rgba(255,255,255,0.1)',
    zIndex: 10,
    shadowColor: '#000',
    shadowOffset: { width: -2, height: 0 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 5,
  },
  chatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  chatHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  chatTitle: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  chatCloseButton: {
    color: '#999',
    fontSize: 20,
    fontWeight: 'bold',
  },
  messagesList: {
    flex: 1,
    paddingHorizontal: 16,
  },
  messagesContent: {
    paddingBottom: 16,
  },
  messageContainer: {
    marginBottom: 12,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 16,
    maxWidth: '85%',
  },
  reactionContainer: {
    backgroundColor: 'rgba(255,193,7,0.3)',
    alignSelf: 'center',
    paddingHorizontal: 16,
    paddingVertical: 4,
  },
  systemMessageContainer: {
    backgroundColor: 'rgba(0,122,255,0.2)',
    alignSelf: 'center',
    fontStyle: 'italic',
  },
  messageUser: {
    color: '#1d9bf0',
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 2,
  },
  reactionUser: {
    color: '#FFD700',
  },
  systemUser: {
    color: '#007AFF',
  },
  messageText: {
    color: '#ffffff',
    fontSize: 14,
    lineHeight: 18,
  },
  systemText: {
    fontStyle: 'italic',
  },
  typingIndicatorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: 'rgba(0,122,255,0.1)',
    borderRadius: 16,
    marginBottom: 8,
  },
  typingDots: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 8,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#007AFF',
    marginRight: 4,
  },
  dot1: {
    opacity: 1,
  },
  dot2: {
    opacity: 0.5,
  },
  dot3: {
    opacity: 0.2,
  },
  typingText: {
    color: '#007AFF',
    fontSize: 12,
    fontStyle: 'italic',
  },
  chatInputContainer: {
    flexDirection: 'row',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.1)',
    backgroundColor: 'rgba(0,0,0,0.2)',
  },
  chatInput: {
    flex: 1,
    backgroundColor: 'rgba(255,255,255,0.15)',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    color: '#ffffff',
    fontSize: 14,
    marginRight: 12,
    maxHeight: 80,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#1d9bf0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  reactionsPanel: {
    position: 'absolute',
    bottom: 140,
    left: 20,
    flexDirection: 'row',
    zIndex: 10,
  },
  reactionButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
    borderWidth: 2,
    borderColor: 'rgba(255,255,255,0.3)',
  },
  reactionText: {
    fontSize: 24,
    color: '#ffffff',
  },
  viewersPanel: {
    position: 'absolute',
    left: 0,
    top: 100,
    bottom: 120,
    width: 280,
    backgroundColor: 'rgba(0,0,0,0.85)',
    borderRightWidth: 1,
    borderRightColor: 'rgba(255,255,255,0.1)',
    zIndex: 10,
    shadowColor: '#000',
    shadowOffset: { width: 2, height: 0 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 5,
  },
  viewersHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  viewersHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  viewersTitle: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  viewersCloseButton: {
    color: '#999',
    fontSize: 20,
    fontWeight: 'bold',
  },
  viewersList: {
    flex: 1,
    padding: 16,
  },
  viewersContent: {
    paddingBottom: 16,
  },
  viewerItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.05)',
  },
  viewerAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  viewerAvatarText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  viewerName: {
    color: '#ffffff',
    fontSize: 14,
    flex: 1,
  },
  typingIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#1d9bf0',
  },
  // Error overlay styles
  errorOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  errorContent: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 20,
    padding: 30,
    alignItems: 'center',
    maxWidth: '80%',
  },
  errorTitle: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: 'bold',
    marginTop: 16,
    marginBottom: 8,
  },
  errorText: {
    color: '#cccccc',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 20,
  },
  reconnectingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  reconnectingText: {
    color: '#FF3B30',
    fontSize: 14,
    marginLeft: 8,
  },
  retryButton: {
    backgroundColor: '#FF3B30',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 20,
  },
  retryButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});