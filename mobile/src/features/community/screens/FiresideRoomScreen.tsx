import React, { useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { Audio } from 'expo-av';
import { isExpoGo } from '../../../utils/expoGoCheck';
import { createPeer, isWebRTCAvailable } from '../../../webrtc/peer';

// Conditionally import WebRTC (not available in Expo Go)
let RTCPeerConnection: any = null;
let RTCIceCandidate: any = null;
let RTCSessionDescription: any = null;
let RTCView: any = null;
let mediaDevices: any = null;
let MediaStream: any = null;

try {
  if (!isExpoGo()) {
    const webrtc = require('react-native-webrtc');
    RTCPeerConnection = webrtc.RTCPeerConnection;
    RTCIceCandidate = webrtc.RTCIceCandidate;
    RTCSessionDescription = webrtc.RTCSessionDescription;
    RTCView = webrtc.RTCView;
    mediaDevices = webrtc.mediaDevices;
    MediaStream = webrtc.MediaStream;
  }
} catch (e) {
  console.warn('WebRTC not available in Expo Go');
}
import { connectSignal } from '../../../realtime/signal';
import { getJwt } from '../../../auth/token';
import { useRoute } from '@react-navigation/native';
import logger from '../../../utils/logger';

export default function FiresideRoomScreen() {
  console.log('[FiresideRoomScreen] Component mounted');
  logger.log('[FiresideRoomScreen] Component mounted');
  
  const [micEnabled, setMicEnabled] = useState(false);
  const [status, setStatus] = useState<string>('Connecting...');
  const [connected, setConnected] = useState(false);
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [remoteStreams, setRemoteStreams] = useState<Map<string, MediaStream>>(new Map());
  const [usersInRoom, setUsersInRoom] = useState<string[]>([]);
  const [currentSpeaker, setCurrentSpeaker] = useState<string | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const peerConnectionsRef = useRef<Map<string, RTCPeerConnection>>(new Map());
  const remoteStreamsRef = useRef<Map<string, MediaStream>>(new Map());
  const socketRef = useRef<any>(null);
  const mySocketIdRef = useRef<string | null>(null);
  const route = useRoute<any>();
  const circleId = route?.params?.circleId || 'demo';

  // Compute mic availability based on actual conditions
  // Mic should be available as long as we have a local stream, even if alone
  const micAvailable = React.useMemo(() => {
    const available = 
      connected &&
      !!localStream &&
      localStream.getAudioTracks().length > 0 &&
      localStream.getAudioTracks()[0].kind === 'audio';
    
    return available;
  }, [connected, localStream]);

  // Compute button label based on availability and state
  const micLabel = React.useMemo(() => {
    if (!micAvailable) {
      return 'Mic unavailable';
    }
    return micEnabled ? 'Mute' : 'Unmute';
  }, [micAvailable, micEnabled]);

  // Sync micEnabled state with actual track state
  React.useEffect(() => {
    if (localStream) {
      const audioTrack = localStream.getAudioTracks()[0];
      if (audioTrack) {
        setMicEnabled(audioTrack.enabled);
      }
    }
  }, [localStream]);

  const handleMicToggle = () => {
    console.log('[Fireside] Mic button pressed. available=', micAvailable);
    
    const stateSnapshot = {
      socketConnected: connected,
      hasPeerConnections: peerConnectionsRef.current.size > 0,
      hasLocalStream: !!localStream,
      localTracks: localStream ? localStream.getTracks().map(t => ({
        kind: t.kind,
        enabled: t.enabled,
        readyState: t.readyState,
      })) : null,
    };
    
    console.log('[Fireside] State snapshot:', stateSnapshot);

    if (!micAvailable) {
      // Optionally remove this once confident - but keep for debugging
      console.warn('[Fireside] Mic unavailable – conditions failed:', {
        connected,
        hasLocalStream: !!localStream,
        audioTracks: localStream?.getAudioTracks().length ?? 0,
      });
      return;
    }

    // Toggle track, which you're already doing correctly
    const audioTrack = localStream!.getAudioTracks()[0];
    const nextEnabled = !audioTrack.enabled;
    audioTrack.enabled = nextEnabled;
    setMicEnabled(nextEnabled);
    console.log('[Fireside] Mic toggled. enabled =', nextEnabled);
    
    // Update status to reflect mic state
    setStatus(nextEnabled ? 'Listening...' : 'Muted');
  };

  // Helper function to attach peer connection listeners
  const attachPeerConnectionListeners = (pc: RTCPeerConnection, peerId: string) => {
    pc.ontrack = (event: any) => {
      const [stream] = event.streams;
      if (!stream) {
        console.log('[Fireside] ontrack fired, but no streams');
        return;
      }

      console.log(
        '[Fireside] Remote track received',
        peerId,
        stream.id,
        event.track.kind,
      );

      remoteStreamsRef.current.set(peerId, stream);
      setRemoteStreams(new Map(remoteStreamsRef.current));
      setCurrentSpeaker(peerId);
      
      // Clear speaker after 2 seconds of silence (simple approach)
      setTimeout(() => {
        setCurrentSpeaker(prev => prev === peerId ? null : prev);
      }, 2000);
    };

    pc.onconnectionstatechange = () => {
      console.log('[Fireside] pc.connectionState for', peerId, pc.connectionState);
      if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed') {
        remoteStreamsRef.current.delete(peerId);
        setRemoteStreams(new Map(remoteStreamsRef.current));
        peerConnectionsRef.current.delete(peerId);
        if (currentSpeaker === peerId) {
          setCurrentSpeaker(null);
        }
      }
    };
  };

  // Helper function to create a peer connection for a specific peer
  const createPeerConnection = async (peerId: string): Promise<RTCPeerConnection | null> => {
    if (peerConnectionsRef.current.has(peerId)) {
      console.log('[Fireside] Peer connection already exists for', peerId);
      return peerConnectionsRef.current.get(peerId)!;
    }

    try {
      const pc = createPeer();
      attachPeerConnectionListeners(pc, peerId);
      
      // Set up ICE candidate handler for this specific peer
      pc.onicecandidate = (event: any) => {
        if (event.candidate && socketRef.current) {
          socketRef.current.emit('ice-candidate', {
            candidate: event.candidate,
            from: mySocketIdRef.current,
            to: peerId,
          });
        }
      };
      
      // Add local stream tracks to this peer connection
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(track => {
          pc.addTrack(track, localStreamRef.current!);
        });
      }

      peerConnectionsRef.current.set(peerId, pc);
      console.log('[Fireside] Created peer connection for', peerId);
      return pc;
    } catch (e) {
      console.warn('[Fireside] Failed to create peer connection for', peerId, e);
      return null;
    }
  };

  // Boot signaling + WebRTC
  useEffect(() => {
    console.log('[FiresideRoomScreen] useEffect triggered');
    logger.log('[FiresideRoomScreen] useEffect triggered');
    console.log('[FiresideRoomScreen] WebRTC available:', isWebRTCAvailable());
    console.log('[FiresideRoomScreen] mediaDevices available:', !!mediaDevices);
    
    // Check if WebRTC is available
    const webrtcAvailable = isWebRTCAvailable() && mediaDevices;
    
    if (!webrtcAvailable) {
      console.warn('[FiresideRoomScreen] WebRTC not available - using text-only mode');
      logger.warn('[FiresideRoomScreen] WebRTC not available - using text-only mode');
      setStatus('Text-only mode (voice requires development build)');
      
      // Still connect to Socket.io for text chat and presence
      const socket = connectSignal(getJwt);
      socketRef.current = socket;
      
      socket.on('connect', () => {
        console.log('✅ [Fireside] Connected (text-only mode)', socket.id);
        logger.log('✅ [Fireside] Connected (text-only mode)', socket.id);
        mySocketIdRef.current = socket.id;
        setConnected(true);
        socket.emit('join-room', { room: `circle-${circleId}` });
        setStatus('Connected (text-only mode)');
      });
      
      socket.on('room-joined', (data: any) => {
        console.log('✅ [Fireside] Room joined (text-only):', data);
        setStatus('Connected (text-only mode)');
      });
      
      socket.on('user-joined', (data: any) => {
        const newUserId = data.userId || data.from;
        if (newUserId && newUserId !== mySocketIdRef.current) {
          setUsersInRoom(prev => {
            if (!prev.includes(newUserId)) {
              return [...prev, newUserId];
            }
            return prev;
          });
        }
      });
      
      socket.on('user-left', (data: any) => {
        const leftUserId = data.userId || data.from;
        setUsersInRoom(prev => prev.filter(id => id !== leftUserId));
      });
      
      socket.on('connect_error', (error) => {
        console.error('❌ [Fireside] Connection error:', error);
        setStatus(`Connection error: ${error?.message || 'Unknown'}`);
      });
      
      return; // Exit early - no WebRTC setup
    }
    
    console.log('[FiresideRoomScreen] Starting connection process...');
    logger.log('[FiresideRoomScreen] Starting connection process...');

    (async () => {
      // Local mic - create stream and store it in state
      try {
        console.log('[Fireside] Requesting microphone access...');
        logger.log('[Fireside] Requesting microphone access...');
        const stream = await mediaDevices.getUserMedia({ audio: true, video: false });
        console.log('[Fireside] ✅ Local audio stream created, tracks:', stream.getAudioTracks().length);
        logger.log('[Fireside] ✅ Local audio stream created');
        stream.getTracks().forEach(t => {
          console.log('[Fireside] Track:', { kind: t.kind, enabled: t.enabled, id: t.id });
        });
        setLocalStream(stream);
        localStreamRef.current = stream;
        console.log('[Fireside] Local stream stored in state');
        logger.log('[Fireside] Local stream stored in state');
        // Update status if socket is already connected
        if (connected) {
          setStatus('Ready');
        } else {
          setStatus('Audio ready - connecting...');
        }
      } catch (e: any) {
        const errorMsg = e?.message || String(e);
        console.warn('[Fireside] ❌ Mic permission denied or getUserMedia failed:', errorMsg);
        logger.warn('[Fireside] ❌ Mic permission denied or getUserMedia failed:', errorMsg);
        if (errorMsg.includes('permission') || errorMsg.includes('Permission')) {
          setStatus('Mic unavailable: permission denied. Please enable microphone access in settings.');
        } else {
          setStatus(`Mic unavailable: ${errorMsg.substring(0, 50)}`);
        }
      }

      // Signaling
      console.log('[FiresideRoomScreen] Calling connectSignal...');
      logger.log('[FiresideRoomScreen] Calling connectSignal...');
      const socket = connectSignal(getJwt);
      socketRef.current = socket;
      console.log('[FiresideRoomScreen] Socket created, setting up listeners...');
      logger.log('[FiresideRoomScreen] Socket created, setting up listeners...');
      
      // Update status to show we're attempting connection
      setStatus('Connecting to server...');
      
      // Timeout handler - use a ref to track if we've connected
      let hasConnected = false;
      const connectionTimeout = setTimeout(() => {
        if (!hasConnected) {
          console.warn('⏱️ [Fireside] Connection timeout after 10s');
          setStatus('Connection timeout - check your network or server');
          setConnected(false);
        }
      }, 10000);
      
      // Connection handlers with better error feedback
      socket.on('connect', () => {
        hasConnected = true;
        clearTimeout(connectionTimeout);
        console.log('✅ [Fireside] WebSocket connected', socket.id);
        logger.log('✅ [Fireside] WebSocket connected', socket.id);
        mySocketIdRef.current = socket.id;
        setConnected(true);
        
        // Join the room
        socket.emit('join-room', { room: `circle-${circleId}` });
        logger.log(`[Fireside] Emitted join-room for circle-${circleId}`);
        
        // Update status based on whether we have localStream (use ref to avoid closure issue)
        if (localStreamRef.current) {
          setStatus('Ready');
        } else {
          setStatus('Connected - waiting for audio...');
        }
      });
      
      // Handle room join confirmation
      socket.on('room-joined', (data: any) => {
        console.log('✅ [Fireside] Room joined:', data);
        logger.log('✅ [Fireside] Room joined:', data);
        if (localStreamRef.current) {
          setStatus('Ready');
        } else {
          setStatus('Connected - waiting for audio...');
        }
      });
      
      socket.on('user-joined', async (data: any) => {
        console.log('[Fireside] User joined room:', data);
        const newUserId = data.userId || data.from;
        
        if (!newUserId || newUserId === mySocketIdRef.current) {
          return; // Skip self
        }
        
        // Add user to room list
        setUsersInRoom(prev => {
          if (!prev.includes(newUserId)) {
            return [...prev, newUserId];
          }
          return prev;
        });
        
        // Create peer connection for this new user
        const pc = await createPeerConnection(newUserId);
        if (pc && localStreamRef.current) {
          try {
            console.log('[Fireside] Creating offer for new user:', newUserId);
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            socket.emit('offer', {
              from: mySocketIdRef.current,
              to: newUserId,
              offer: {
                type: offer.type,
                sdp: offer.sdp,
              },
            });
            console.log('[Fireside] Offer sent to:', newUserId);
          } catch (e) {
            console.warn('[Fireside] Failed to create offer:', e);
          }
        }
        
        // Room is ready, mic should be available if we have localStream
        if (localStreamRef.current) {
          setStatus('Ready');
        }
      });
      
      socket.on('user-left', (data: any) => {
        console.log('[Fireside] User left room:', data);
        const leftUserId = data.userId || data.from;
        setUsersInRoom(prev => prev.filter(id => id !== leftUserId));
        
        // Clean up peer connection
        const pc = peerConnectionsRef.current.get(leftUserId);
        if (pc) {
          pc.close();
          peerConnectionsRef.current.delete(leftUserId);
        }
        
        // Remove their remote stream
        remoteStreamsRef.current.delete(leftUserId);
        setRemoteStreams(new Map(remoteStreamsRef.current));
        if (currentSpeaker === leftUserId) {
          setCurrentSpeaker(null);
        }
      });
      
      socket.on('disconnect', (reason) => {
        hasConnected = false;
        console.log('❌ [Fireside] WebSocket disconnected:', reason);
        setConnected(false);
        setStatus('Disconnected');
      });
      
      socket.on('connect_error', (error) => {
        hasConnected = false;
        clearTimeout(connectionTimeout);
        console.error('❌ [Fireside] WebSocket connection error:', error);
        setConnected(false);
        const errorMsg = error?.message || String(error);
        if (errorMsg.includes('ECONNREFUSED') || errorMsg.includes('Network')) {
          setStatus('Cannot reach server - check your network');
        } else if (errorMsg.includes('401') || errorMsg.includes('Unauthorized')) {
          setStatus('Authentication failed - please login again');
        } else {
          setStatus(`Connection failed: ${errorMsg}`);
        }
      });

      // WebRTC signaling handlers
      socket.on('offer', async (data: { from: string; offer: RTCSessionDescriptionInit }) => {
        const fromId = data.from;
        if (!fromId || fromId === mySocketIdRef.current) return;
        
        console.log('[Fireside] Received offer from:', fromId);
        
        // Create or get peer connection for this user
        let pc = peerConnectionsRef.current.get(fromId);
        if (!pc) {
          pc = await createPeerConnection(fromId);
        }
        
        if (!pc) {
          console.warn('[Fireside] Failed to create peer connection for offer from', fromId);
          return;
        }
        
        try {
          await pc.setRemoteDescription(new RTCSessionDescription(data.offer));
          const answer = await pc.createAnswer();
          await pc.setLocalDescription(answer);
          socket.emit('answer', {
            from: mySocketIdRef.current,
            to: fromId,
            answer: {
              type: answer.type,
              sdp: answer.sdp,
            },
          });
          console.log('[Fireside] Answer sent to:', fromId);
        } catch (e) {
          console.warn('[Fireside] Failed to handle offer:', e);
        }
      });
      
      socket.on('answer', async (data: { from: string; answer: RTCSessionDescriptionInit }) => {
        const fromId = data.from;
        if (!fromId || fromId === mySocketIdRef.current) return;
        
        console.log('[Fireside] Received answer from:', fromId);
        const pc = peerConnectionsRef.current.get(fromId);
        if (!pc) {
          console.warn('[Fireside] No peer connection for answer from', fromId);
          return;
        }
        
        try {
          await pc.setRemoteDescription(new RTCSessionDescription(data.answer));
        } catch (e) {
          console.warn('[Fireside] Failed to set remote description from answer:', e);
        }
      });
      
      socket.on('ice-candidate', async (data: { candidate: RTCIceCandidateInit; from: string }) => {
        const fromId = data.from;
        if (!fromId || fromId === mySocketIdRef.current || !data.candidate) return;
        
        const pc = peerConnectionsRef.current.get(fromId);
        if (!pc) {
          console.warn('[Fireside] No peer connection for ICE candidate from', fromId);
          return;
        }
        
        try {
          await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
        } catch (e) {
          console.warn('[Fireside] Failed to add ICE candidate:', e);
        }
      });

      // Note: ICE candidate handlers are set up in createPeerConnection for each peer
    })();

    return () => {
      try { socketRef.current?.emit?.('leave-room', { room: `circle-${circleId}` }); } catch {}
      try { socketRef.current?.disconnect?.(); } catch {}
      try { 
        localStreamRef.current?.getTracks().forEach(track => track.stop());
        localStreamRef.current = null;
      } catch {}
      // Close all peer connections
      peerConnectionsRef.current.forEach((pc, peerId) => {
        try {
          pc.close();
        } catch (e) {
          console.warn('[Fireside] Error closing peer connection for', peerId, e);
        }
      });
      peerConnectionsRef.current.clear();
      remoteStreamsRef.current.clear();
    };
  }, [circleId]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Fireside Room</Text>
      <Text style={styles.subtitle}>
        {connected 
          ? `Connected • ${usersInRoom.length} user${usersInRoom.length !== 1 ? 's' : ''}` 
          : status || 'Connecting…'}
      </Text>
      
      {/* User list */}
      {usersInRoom.length > 0 && (
        <View style={styles.userList}>
          <Text style={styles.userListTitle}>In room ({usersInRoom.length}):</Text>
          {usersInRoom.map((userId, index) => {
            const isSpeaking = currentSpeaker === userId;
            const hasStream = remoteStreams.has(userId);
            return (
              <View key={userId} style={[styles.userItem, isSpeaking && styles.userItemSpeaking]}>
                <View style={[styles.userIndicator, isSpeaking && styles.userIndicatorActive]} />
                <Text style={styles.userText}>
                  {userId === mySocketIdRef.current ? 'You' : `User ${index + 1}`}
                </Text>
                {hasStream && (
                  <Text style={styles.userStatus}>{isSpeaking ? '🎙️' : '🔊'}</Text>
                )}
              </View>
            );
          })}
        </View>
      )}
      
      {/* Remote audio playback – one RTCView per remote stream (invisible, just for audio) */}
      {RTCView && Array.from(remoteStreams.entries()).map(([peerId, stream]) => (
        <RTCView
          key={peerId}
          streamURL={stream.toURL()}
          // Tiny & transparent; just to drive audio
          style={{ width: 1, height: 1, opacity: 0, position: 'absolute' }}
          objectFit="cover"
        />
      ))}
      
      <View style={{ flex: 1 }} />
      
      {/* Info message for Expo Go users */}
      {!isWebRTCAvailable() && connected && (
        <View style={styles.infoBox}>
          <Icon name="info" size={16} color="#6B7280" />
          <Text style={styles.infoText}>
            Voice chat requires a development build. You're connected in text-only mode.
          </Text>
        </View>
      )}
      
      {/* Mic toggle button - only show if WebRTC is available */}
      {isWebRTCAvailable() && mediaDevices ? (
        <TouchableOpacity
          onPress={handleMicToggle}
          style={[styles.ptt, micEnabled ? styles.pttActive : null]}
          disabled={!micAvailable}
        >
          <Icon name={micEnabled ? "mic" : "mic-off"} size={24} color="#fff" />
          <Text style={styles.pttText}>{micLabel}</Text>
        </TouchableOpacity>
      ) : (
        <TouchableOpacity
          style={[styles.ptt, { backgroundColor: '#6B7280', opacity: 0.6 }]}
          disabled={true}
        >
          <Icon name="mic-off" size={24} color="#fff" />
          <Text style={styles.pttText}>Mic unavailable (requires dev build)</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa', padding: 16 },
  title: { fontSize: 20, fontWeight: '700', color: '#1C1C1E' },
  subtitle: { fontSize: 13, color: '#6B7280', marginTop: 4 },
  userList: { marginTop: 16, padding: 12, backgroundColor: '#fff', borderRadius: 8 },
  userListTitle: { fontSize: 14, fontWeight: '600', color: '#1C1C1E', marginBottom: 8 },
  userItem: { flexDirection: 'row', alignItems: 'center', paddingVertical: 6, paddingHorizontal: 8, borderRadius: 6 },
  userItemSpeaking: { backgroundColor: '#E8F5E9' },
  userIndicator: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#34C759', marginRight: 8 },
  userIndicatorActive: { backgroundColor: '#16A34A', width: 10, height: 10 },
  userText: { fontSize: 14, color: '#1C1C1E', flex: 1 },
  userStatus: { fontSize: 16, marginLeft: 4 },
  ptt: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, backgroundColor: '#34C759', borderRadius: 24, paddingVertical: 14, position: 'absolute', left: 16, right: 16, bottom: 24 },
  pttActive: { backgroundColor: '#16A34A' },
  pttText: { color: '#fff', fontWeight: '700' },
  infoBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F3F4F6',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
    marginHorizontal: 16,
  },
  infoText: {
    flex: 1,
    fontSize: 12,
    color: '#6B7280',
    lineHeight: 16,
  },
});


