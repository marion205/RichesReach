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
let mediaDevices: any = null;
let MediaStream: any = null;

try {
  if (!isExpoGo()) {
    const webrtc = require('react-native-webrtc');
    RTCPeerConnection = webrtc.RTCPeerConnection;
    RTCIceCandidate = webrtc.RTCIceCandidate;
    RTCSessionDescription = webrtc.RTCSessionDescription;
    mediaDevices = webrtc.mediaDevices;
    MediaStream = webrtc.MediaStream;
  }
} catch (e) {
  console.warn('WebRTC not available in Expo Go');
}
import { connectSignal } from '../../../realtime/signal';
import { getJwt } from '../../../auth/token';
import { useRoute } from '@react-navigation/native';

export default function FiresideRoomScreen() {
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [status, setStatus] = useState<string>('Tap and hold to speak');
  const [connected, setConnected] = useState(false);
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const socketRef = useRef<any>(null);
  const route = useRoute<any>();
  const circleId = route?.params?.circleId || 'demo';

  const startRecording = async () => {
    try {
      await Audio.requestPermissionsAsync();
      await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
      const { recording } = await Audio.Recording.createAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
      setRecording(recording);
      setStatus('Listening...');
    } catch (e) {
      setStatus('Mic unavailable');
    }
  };
  const stopRecording = async () => {
    try {
      if (!recording) return;
      await recording.stopAndUnloadAsync();
    } catch {}
    setRecording(null);
    setStatus('Tap and hold to speak');
  };

  // Boot signaling + WebRTC
  useEffect(() => {
    // Skip WebRTC if not available (Expo Go)
    if (!isWebRTCAvailable() || !mediaDevices) {
      setStatus('WebRTC not available in Expo Go. Use development build for voice features.');
      return;
    }

    (async () => {
      let pc;
      try {
        pc = createPeer();
        pcRef.current = pc;
      } catch (e) {
        console.warn('Failed to create peer:', e);
        setStatus('WebRTC unavailable');
        return;
      }

      // Local mic
      try {
        const stream = await mediaDevices.getUserMedia({ audio: true, video: false });
        stream.getTracks().forEach(t => pc.addTrack(t, stream));
        setLocalStream(stream);
      } catch (e) {
        console.warn('Mic permission denied', e);
      }

      // Signaling
      const socket = connectSignal(getJwt);
      socketRef.current = socket;
      socket.on('connect', () => {
        setConnected(true);
        socket.emit('join-room', { room: `circle-${circleId}` });
      });
      socket.on('disconnect', () => setConnected(false));

      // Offers
      socket.on('offer', async (data: { from: string; offer: RTCSessionDescriptionInit }) => {
        if (!pcRef.current) return;
        await pcRef.current.setRemoteDescription(new RTCSessionDescription(data.offer));
        const answer = await pcRef.current.createAnswer();
        await pcRef.current.setLocalDescription(answer);
        socket.emit('answer', { answer, to: data.from });
      });
      socket.on('answer', async (data: { from: string; answer: RTCSessionDescriptionInit }) => {
        if (!pcRef.current) return;
        await pcRef.current.setRemoteDescription(new RTCSessionDescription(data.answer));
      });
      socket.on('ice-candidate', async (data: { candidate: RTCIceCandidateInit }) => {
        if (!pcRef.current) return;
        try { await pcRef.current.addIceCandidate(new RTCIceCandidate(data.candidate)); } catch {}
      });

      // Emit ICE candidates
      pc.onicecandidate = (event) => {
        if (event.candidate) socket.emit('ice-candidate', { candidate: event.candidate, to: 'all' });
      };
    })();

    return () => {
      try { socketRef.current?.emit?.('leave-room', { room: `circle-${circleId}` }); } catch {}
      try { socketRef.current?.disconnect?.(); } catch {}
      try { pcRef.current?.close(); } catch {}
    };
  }, [circleId]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Fireside Room</Text>
      <Text style={styles.subtitle}>{connected ? 'Connected' : 'Connecting…'}</Text>
      <View style={{ flex: 1 }} />
      <TouchableOpacity
        onPressIn={startRecording}
        onPressOut={stopRecording}
        style={[styles.ptt, recording ? styles.pttActive : null]}
      >
        <Icon name="mic" size={24} color="#fff" />
        <Text style={styles.pttText}>{status}</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa', padding: 16 },
  title: { fontSize: 20, fontWeight: '700', color: '#1C1C1E' },
  subtitle: { fontSize: 13, color: '#6B7280', marginTop: 4 },
  ptt: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, backgroundColor: '#34C759', borderRadius: 24, paddingVertical: 14, position: 'absolute', left: 16, right: 16, bottom: 24 },
  pttActive: { backgroundColor: '#16A34A' },
  pttText: { color: '#fff', fontWeight: '700' },
});


