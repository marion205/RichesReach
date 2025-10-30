import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  TextInput,
  FlatList,
  Alert,
  Dimensions,
  StatusBar,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { RTCView, RTCPeerConnection, RTCIceCandidate, RTCSessionDescription, mediaDevices } from 'react-native-webrtc';
import io from 'socket.io-client';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width, height } = Dimensions.get('window');

interface MediasoupLiveStreamingProps {
  visible: boolean;
  onClose: () => void;
  circleId: string;
  isHost: boolean;
}

interface ChatMessage {
  id: string;
  message: string;
  userId: string;
  userName: string;
  timestamp: string;
}

interface Reaction {
  id: string;
  emoji: string;
  userId: string;
  userName: string;
  timestamp: string;
}

interface Transport {
  id: string;
  direction: 'send' | 'recv';
  transport: any;
}

interface Producer {
  id: string;
  kind: string;
  producer: any;
}

interface Consumer {
  id: string;
  kind: string;
  consumer: any;
}

const MediasoupLiveStreaming: React.FC<MediasoupLiveStreamingProps> = ({
  visible,
  onClose,
  circleId,
  isHost,
}) => {
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [remoteStreams, setRemoteStreams] = useState<Map<string, MediaStream>>(new Map());
  const [viewerCount, setViewerCount] = useState(0);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [reactions, setReactions] = useState<Reaction[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoEnabled, setIsVideoEnabled] = useState(true);
  const [showChat, setShowChat] = useState(true);
  const [streamTitle, setStreamTitle] = useState('Live Stream');

  const socketRef = useRef<any>(null);
  const transportsRef = useRef<Map<string, Transport>>(new Map());
  const producersRef = useRef<Map<string, Producer>>(new Map());
  const consumersRef = useRef<Map<string, Consumer>>(new Map());
  const localStreamRef = useRef<MediaStream | null>(null);

  const SFU_SERVER_URL = process.env.EXPO_PUBLIC_SFU_SERVER_URL || 'http://localhost:8000';

  useEffect(() => {
    if (visible) {
      initializeStreaming();
    } else {
      cleanup();
    }

    return () => {
      cleanup();
    };
  }, [visible]);

  const initializeStreaming = useCallback(async () => {
    try {
      // Connect to SFU server
      const token = await AsyncStorage.getItem('authToken') || 'demo-token';
      const userName = await AsyncStorage.getItem('userName') || 'User';
      
      socketRef.current = io(SFU_SERVER_URL, {
        auth: { token, userName },
        transports: ['websocket', 'polling']
      });
      
      setupSocketHandlers();
      
      // Join live room
      socketRef.current.emit('join-live', { circleId, isHost });
      
      if (isHost) {
        await startHostStreaming();
      }
    } catch (error) {
      console.error('Error initializing streaming:', error);
      Alert.alert('Error', 'Failed to initialize live streaming');
    }
  }, [isHost, circleId]);

  const startHostStreaming = async () => {
    try {
      // Get user media
      const stream = await mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 30 }
        },
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      
      setLocalStream(stream);
      localStreamRef.current = stream;
      setIsStreaming(true);

      // Create send transport
      socketRef.current.emit('create-transport', { direction: 'send', circleId });

      console.log('🎥 Host streaming started');
    } catch (error) {
      console.error('Error starting host stream:', error);
      Alert.alert('Error', 'Failed to start streaming. Check camera and microphone permissions.');
    }
  };

  const setupSocketHandlers = useCallback(() => {
    if (!socketRef.current) return;

    // Transport created
    socketRef.current.on('transport-created', async ({ id, iceParameters, iceCandidates, dtlsParameters, direction }) => {
      try {
        await handleTransportCreated(id, iceParameters, iceCandidates, dtlsParameters, direction);
      } catch (error) {
        console.error('Error handling transport created:', error);
      }
    });

    // New producer (for viewers)
    socketRef.current.on('new-producer', async ({ producerId, kind, userId, userName }) => {
      try {
        await handleNewProducer(producerId, kind, userId, userName);
      } catch (error) {
        console.error('Error handling new producer:', error);
      }
    });

    // Consumer created
    socketRef.current.on('consumer-created', async ({ id, producerId, kind, rtpParameters }) => {
      try {
        await handleConsumerCreated(id, producerId, kind, rtpParameters);
      } catch (error) {
        console.error('Error handling consumer created:', error);
      }
    });

    // Viewer joined
    socketRef.current.on('viewer-joined', ({ userId, userName, viewerCount }) => {
      setViewerCount(viewerCount);
      console.log(`👀 ${userName} joined (${viewerCount} viewers)`);
    });

    // Viewer left
    socketRef.current.on('viewer-left', ({ userId, userName, viewerCount }) => {
      setViewerCount(viewerCount);
      console.log(`👋 ${userName} left (${viewerCount} viewers)`);
    });

    // Viewer count update
    socketRef.current.on('viewer-count', ({ count }) => {
      setViewerCount(count);
    });

    // Chat message
    socketRef.current.on('chat-message', (message: ChatMessage) => {
      setChatMessages(prev => [...prev, message]);
    });

    // Reaction
    socketRef.current.on('reaction', (reaction: Reaction) => {
      setReactions(prev => [...prev, reaction]);
      
      // Remove reaction after 3 seconds
      setTimeout(() => {
        setReactions(prev => prev.filter(r => r.id !== reaction.id));
      }, 3000);
    });

    // Host joined
    socketRef.current.on('host-joined', ({ hostId, hostName }) => {
      console.log(`🎥 Host ${hostName} joined`);
    });

    // Producer closed
    socketRef.current.on('producer-closed', ({ producerId }) => {
      console.log(`📹 Producer ${producerId} closed`);
      // Handle producer cleanup if needed
    });

    // Error handling
    socketRef.current.on('error', ({ message }) => {
      console.error('Socket error:', message);
      Alert.alert('Streaming Error', message);
    });

    // Disconnect
    socketRef.current.on('disconnect', () => {
      console.log('🔌 Disconnected from SFU server');
    });
  }, []);

  const handleTransportCreated = async (id: string, iceParameters: any, iceCandidates: any[], dtlsParameters: any, direction: string) => {
    try {
      // Create RTCPeerConnection for transport
      const pc = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' }
        ]
      });

      // Set ICE parameters
      await pc.setRemoteDescription({
        type: 'offer',
        sdp: createSDPFromIceParameters(iceParameters, iceCandidates)
      });

      // Create answer
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);

      // Connect transport
      socketRef.current.emit('connect-transport', {
        transportId: id,
        dtlsParameters: dtlsParameters
      });

      // Store transport
      const transport: Transport = {
        id,
        direction: direction as 'send' | 'recv',
        transport: pc
      };
      transportsRef.current.set(id, transport);

      // If this is a send transport and we're the host, produce
      if (direction === 'send' && isHost && localStreamRef.current) {
        await produceStream(id);
      }

      console.log(`🚚 Transport ${id} created and connected`);
    } catch (error) {
      console.error('Error handling transport created:', error);
    }
  };

  const produceStream = async (transportId: string) => {
    try {
      if (!localStreamRef.current) return;

      const transport = transportsRef.current.get(transportId);
      if (!transport) return;

      // Add tracks to peer connection
      localStreamRef.current.getTracks().forEach(track => {
        transport.transport.addTrack(track, localStreamRef.current!);
      });

      // Create offer for production
      const offer = await transport.transport.createOffer();
      await transport.transport.setLocalDescription(offer);

      // Get RTP parameters (simplified - in real implementation, you'd extract from SDP)
      const rtpParameters = {
        codecs: [
          {
            mimeType: 'video/VP8',
            clockRate: 90000,
            channels: 0,
            parameters: {}
          }
        ],
        headerExtensions: [],
        encodings: [
          {
            ssrc: Math.floor(Math.random() * 1000000),
            rtx: { ssrc: Math.floor(Math.random() * 1000000) }
          }
        ],
        rtcp: { cname: 'mediasoup-client' }
      };

      // Produce stream
      socketRef.current.emit('produce', {
        kind: 'video',
        rtpParameters,
        circleId
      });

      console.log('📹 Stream produced');
    } catch (error) {
      console.error('Error producing stream:', error);
    }
  };

  const handleNewProducer = async (producerId: string, kind: string, userId: string, userName: string) => {
    try {
      // Create receive transport if we don't have one
      let recvTransport = Array.from(transportsRef.current.values())
        .find(t => t.direction === 'recv');

      if (!recvTransport) {
        socketRef.current.emit('create-transport', { direction: 'recv', circleId });
        return; // Will be handled when transport is created
      }

      // Consume the producer
      socketRef.current.emit('consume', {
        rtpCapabilities: getRtpCapabilities(),
        circleId,
        producerId
      });

      console.log(`👀 Consuming producer ${producerId} from ${userName}`);
    } catch (error) {
      console.error('Error handling new producer:', error);
    }
  };

  const handleConsumerCreated = async (id: string, producerId: string, kind: string, rtpParameters: any) => {
    try {
      const recvTransport = Array.from(transportsRef.current.values())
        .find(t => t.direction === 'recv');

      if (!recvTransport) return;

      // Create consumer (simplified - in real implementation, you'd create proper consumer)
      const consumer: Consumer = {
        id,
        kind,
        consumer: null // Would be actual mediasoup consumer
      };
      consumersRef.current.set(id, consumer);

      // Resume consumer
      socketRef.current.emit('resume-consumer', { consumerId: id });

      console.log(`👀 Consumer ${id} created`);
    } catch (error) {
      console.error('Error handling consumer created:', error);
    }
  };

  const getRtpCapabilities = () => {
    return {
      codecs: [
        {
          kind: 'audio',
          mimeType: 'audio/opus',
          clockRate: 48000,
          channels: 2,
          parameters: {}
        },
        {
          kind: 'video',
          mimeType: 'video/VP8',
          clockRate: 90000,
          channels: 0,
          parameters: {}
        }
      ],
      headerExtensions: [],
      fecMechanisms: []
    };
  };

  const createSDPFromIceParameters = (iceParameters: any, iceCandidates: any[]) => {
    // Simplified SDP creation - in real implementation, you'd create proper SDP
    return `v=0\r\no=- 0 0 IN IP4 ${process.env.EXPO_PUBLIC_API_BASE_URL?.replace('http://', '') || '192.168.1.236'}\r\ns=-\r\nt=0 0\r\na=ice-ufrag:${iceParameters.usernameFragment}\r\na=ice-pwd:${iceParameters.password}\r\n`;
  };

  const sendChatMessage = useCallback(() => {
    if (!newMessage.trim() || !socketRef.current) return;

    socketRef.current.emit('chat-message', {
      message: newMessage.trim(),
      circleId
    });

    setNewMessage('');
  }, [newMessage, circleId]);

  const sendReaction = useCallback((reaction: string) => {
    if (!socketRef.current) return;

    socketRef.current.emit('reaction', {
      emoji: reaction,
      circleId
    });
  }, [circleId]);

  const toggleMute = useCallback(() => {
    if (localStreamRef.current) {
      const audioTracks = localStreamRef.current.getAudioTracks();
      audioTracks.forEach(track => {
        track.enabled = isMuted;
      });
      setIsMuted(!isMuted);
    }
  }, [isMuted]);

  const toggleVideo = useCallback(() => {
    if (localStreamRef.current) {
      const videoTracks = localStreamRef.current.getVideoTracks();
      videoTracks.forEach(track => {
        track.enabled = isVideoEnabled;
      });
      setIsVideoEnabled(!isVideoEnabled);
    }
  }, [isVideoEnabled]);

  const endStream = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.emit('leave-live', { circleId });
    }
    onClose();
  }, [circleId, onClose]);

  const cleanup = useCallback(() => {
    // Stop local stream
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => track.stop());
    }

    // Close transports
    transportsRef.current.forEach(transport => {
      transport.transport.close();
    });
    transportsRef.current.clear();

    // Close producers
    producersRef.current.forEach(producer => {
      if (producer.producer) {
        producer.producer.close();
      }
    });
    producersRef.current.clear();

    // Close consumers
    consumersRef.current.forEach(consumer => {
      if (consumer.consumer) {
        consumer.consumer.close();
      }
    });
    consumersRef.current.clear();

    // Disconnect socket
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }

    // Reset state
    setLocalStream(null);
    setRemoteStreams(new Map());
    setViewerCount(0);
    setChatMessages([]);
    setReactions([]);
    setIsStreaming(false);
  }, []);

  const renderChatMessage = ({ item }: { item: ChatMessage }) => (
    <View style={styles.chatMessage}>
      <Text style={styles.chatUserName}>{item.userName}</Text>
      <Text style={styles.chatMessageText}>{item.message}</Text>
    </View>
  );

  const renderReaction = ({ item }: { item: Reaction }) => (
    <View style={styles.reactionContainer}>
      <Text style={styles.reactionText}>{item.emoji}</Text>
    </View>
  );

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="fullScreen"
      onRequestClose={onClose}
    >
      <StatusBar hidden />
      <View style={styles.container}>
        {/* Video Stream */}
        <View style={styles.videoContainer}>
          {isHost && localStream && (
            <RTCView
              streamURL={localStream.toURL()}
              style={styles.localVideo}
              objectFit="cover"
              mirror={true}
            />
          )}
          
          {!isHost && remoteStreams.size > 0 && (
            <RTCView
              streamURL={Array.from(remoteStreams.values())[0].toURL()}
              style={styles.remoteVideo}
              objectFit="cover"
            />
          )}

          {/* Stream Info Overlay */}
          <View style={styles.streamInfoOverlay}>
            <View style={styles.streamHeader}>
              <Text style={styles.streamTitle}>{streamTitle}</Text>
              <View style={styles.viewerCount}>
                <Text style={styles.viewerCountText}>👁️ {viewerCount}</Text>
              </View>
            </View>
          </View>

          {/* Reactions Overlay */}
          <View style={styles.reactionsOverlay}>
            <FlatList
              data={reactions}
              renderItem={renderReaction}
              keyExtractor={(item) => item.id}
              horizontal
              showsHorizontalScrollIndicator={false}
            />
          </View>

          {/* Host Controls */}
          {isHost && (
            <View style={styles.hostControls}>
              <TouchableOpacity onPress={toggleMute} style={styles.controlButton}>
                <Text style={styles.controlButtonText}>
                  {isMuted ? '🔇' : '🎤'}
                </Text>
              </TouchableOpacity>
              
              <TouchableOpacity onPress={toggleVideo} style={styles.controlButton}>
                <Text style={styles.controlButtonText}>
                  {isVideoEnabled ? '📹' : '📷'}
                </Text>
              </TouchableOpacity>
              
              <TouchableOpacity onPress={endStream} style={styles.endStreamButton}>
                <Text style={styles.endStreamButtonText}>🔚</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Viewer Controls */}
          {!isHost && (
            <View style={styles.viewerControls}>
              <TouchableOpacity onPress={onClose} style={styles.closeButton}>
                <Text style={styles.closeButtonText}>✕</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Chat Section */}
        {showChat && (
          <View style={styles.chatContainer}>
            <View style={styles.chatHeader}>
              <Text style={styles.chatTitle}>Live Chat</Text>
              <TouchableOpacity onPress={() => setShowChat(false)}>
                <Text style={styles.chatToggleText}>−</Text>
              </TouchableOpacity>
            </View>
            
            <FlatList
              data={chatMessages}
              renderItem={renderChatMessage}
              keyExtractor={(item) => item.id}
              style={styles.chatMessages}
              showsVerticalScrollIndicator={false}
            />
            
            <View style={styles.chatInput}>
              <TextInput
                style={styles.chatInputField}
                placeholder="Type a message..."
                value={newMessage}
                onChangeText={setNewMessage}
                onSubmitEditing={sendChatMessage}
                multiline
              />
              <TouchableOpacity onPress={sendChatMessage} style={styles.sendButton}>
                <Text style={styles.sendButtonText}>Send</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Reaction Buttons */}
        {!isHost && (
          <View style={styles.reactionButtons}>
            <TouchableOpacity onPress={() => sendReaction('👍')} style={styles.reactionButton}>
              <Text style={styles.reactionButtonText}>👍</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => sendReaction('❤️')} style={styles.reactionButton}>
              <Text style={styles.reactionButtonText}>❤️</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => sendReaction('🔥')} style={styles.reactionButton}>
              <Text style={styles.reactionButtonText}>🔥</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => sendReaction('💎')} style={styles.reactionButton}>
              <Text style={styles.reactionButtonText}>💎</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Chat Toggle Button */}
        {!showChat && (
          <TouchableOpacity
            onPress={() => setShowChat(true)}
            style={styles.chatToggleButton}
          >
            <Text style={styles.chatToggleText}>💬</Text>
          </TouchableOpacity>
        )}
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  videoContainer: {
    flex: 1,
    position: 'relative',
  },
  localVideo: {
    flex: 1,
  },
  remoteVideo: {
    flex: 1,
  },
  streamInfoOverlay: {
    position: 'absolute',
    top: 50,
    left: 0,
    right: 0,
    paddingHorizontal: 20,
  },
  streamHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  streamTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    backgroundColor: 'rgba(0,0,0,0.5)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  viewerCount: {
    backgroundColor: 'rgba(0,0,0,0.5)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  viewerCountText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  reactionsOverlay: {
    position: 'absolute',
    top: 100,
    left: 20,
    right: 20,
  },
  reactionContainer: {
    backgroundColor: 'rgba(0,0,0,0.5)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    marginRight: 8,
  },
  reactionText: {
    color: '#fff',
    fontSize: 20,
  },
  hostControls: {
    position: 'absolute',
    bottom: 100,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  controlButton: {
    backgroundColor: 'rgba(0,0,0,0.5)',
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 10,
  },
  controlButtonText: {
    color: '#fff',
    fontSize: 20,
  },
  endStreamButton: {
    backgroundColor: 'rgba(255,59,48,0.8)',
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 10,
  },
  endStreamButtonText: {
    color: '#fff',
    fontSize: 20,
  },
  viewerControls: {
    position: 'absolute',
    top: 50,
    right: 20,
  },
  closeButton: {
    backgroundColor: 'rgba(0,0,0,0.5)',
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  chatContainer: {
    height: 300,
    backgroundColor: 'rgba(0,0,0,0.9)',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
  },
  chatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  chatTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  chatToggleText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  chatMessages: {
    flex: 1,
    paddingHorizontal: 20,
  },
  chatMessage: {
    marginVertical: 4,
  },
  chatUserName: {
    color: '#007AFF',
    fontSize: 12,
    fontWeight: '600',
  },
  chatMessageText: {
    color: '#fff',
    fontSize: 14,
  },
  chatInput: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 15,
    alignItems: 'flex-end',
  },
  chatInputField: {
    flex: 1,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: 10,
    color: '#fff',
    marginRight: 10,
    maxHeight: 80,
  },
  sendButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
  },
  sendButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  reactionButtons: {
    position: 'absolute',
    bottom: 20,
    right: 20,
    flexDirection: 'row',
  },
  reactionButton: {
    backgroundColor: 'rgba(0,0,0,0.5)',
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  reactionButtonText: {
    fontSize: 18,
  },
  chatToggleButton: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    backgroundColor: 'rgba(0,0,0,0.5)',
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default MediasoupLiveStreaming;
