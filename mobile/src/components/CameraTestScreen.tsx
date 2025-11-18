/**
 * Minimal Camera Test Component
 * Use this to isolate WebRTC camera issues
 * 
 * To test:
 * 1. Add this screen to your navigation
 * 2. Navigate to it
 * 3. Press "Start Front Camera"
 * 4. Check console for errors
 */

import React, { useEffect, useRef, useState } from 'react';
import { View, Button, Text, StyleSheet, Platform, Alert, ActivityIndicator } from 'react-native';
import { isExpoGo } from '../utils/expoGoCheck';
import { PermissionsAndroid } from 'react-native';

// Conditionally import WebRTC
let RTCView: any = null;
let mediaDevices: any = null;

try {
  if (!isExpoGo()) {
    const webrtc = require('react-native-webrtc');
    RTCView = webrtc.RTCView;
    mediaDevices = webrtc.mediaDevices;
  }
} catch (e) {
  console.warn('WebRTC not available:', e);
}

interface MediaStream {
  getTracks(): MediaStreamTrack[];
  toURL(): string;
}

interface MediaStreamTrack {
  enabled: boolean;
  stop(): void;
}

export default function CameraTestScreen() {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [isExpoGoEnv, setIsExpoGoEnv] = useState(false);

  useEffect(() => {
    setIsExpoGoEnv(isExpoGo());
    console.log('🔍 Camera Test Environment Check:');
    console.log('- Is Expo Go:', isExpoGo());
    console.log('- RTCView available:', !!RTCView);
    console.log('- mediaDevices available:', !!mediaDevices);
    console.log('- Platform:', Platform.OS);
  }, []);

  const requestPermissions = async (): Promise<boolean> => {
    if (Platform.OS === 'android') {
      try {
        const granted = await PermissionsAndroid.requestMultiple([
          PermissionsAndroid.PERMISSIONS.CAMERA,
          PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
        ]);
        
        const cameraGranted = granted[PermissionsAndroid.PERMISSIONS.CAMERA] === PermissionsAndroid.RESULTS.GRANTED;
        const audioGranted = granted[PermissionsAndroid.PERMISSIONS.RECORD_AUDIO] === PermissionsAndroid.RESULTS.GRANTED;
        
        console.log('📱 Android Permissions:', { cameraGranted, audioGranted });
        
        if (!cameraGranted || !audioGranted) {
          Alert.alert(
            'Permissions Required',
            'Camera and microphone permissions are required for live streaming.',
            [{ text: 'OK' }]
          );
          return false;
        }
        return true;
      } catch (err) {
        console.error('Permission request error:', err);
        return false;
      }
    }
    // iOS permissions are requested automatically by getUserMedia
    return true;
  };

  const startCamera = async () => {
    setError(null);
    setLoading(true);

    try {
      // Check environment
      if (isExpoGoEnv) {
        setError('WebRTC is not available in Expo Go. You must use a development build.');
        setLoading(false);
        return;
      }

      if (!mediaDevices) {
        setError('mediaDevices is not available. Check if react-native-webrtc is properly installed and linked.');
        setLoading(false);
        return;
      }

      // Request permissions (Android)
      const hasPermissions = await requestPermissions();
      if (!hasPermissions) {
        setError('Camera/microphone permissions denied');
        setLoading(false);
        return;
      }

      console.log('🎥 Requesting camera stream with front camera...');
      
      // Get user media with front camera
      const newStream = await mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 30 },
          facingMode: 'user', // Front camera
        },
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      console.log('✅ Stream acquired:', {
        hasStream: !!newStream,
        streamURL: newStream?.toURL(),
        tracks: newStream?.getTracks().length,
      });

      setStream(newStream);
      setLoading(false);
    } catch (err: any) {
      console.error('❌ getUserMedia error:', err);
      setError(err?.message || 'Failed to start camera');
      setLoading(false);
      
      Alert.alert(
        'Camera Error',
        err?.message || 'Failed to access camera. Make sure you are using a development build, not Expo Go.',
        [{ text: 'OK' }]
      );
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track: MediaStreamTrack) => {
        track.stop();
        console.log('🛑 Stopped track:', track);
      });
      setStream(null);
    }
  };

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (stream) {
        stream.getTracks().forEach((track: MediaStreamTrack) => track.stop());
      }
    };
  }, [stream]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Camera Test</Text>
        <Text style={styles.subtitle}>WebRTC Front Camera Diagnostic</Text>
      </View>

      <View style={styles.info}>
        <Text style={styles.infoText}>
          <Text style={styles.bold}>Environment:</Text> {isExpoGoEnv ? 'Expo Go (WebRTC blocked)' : 'Development Build'}
        </Text>
        <Text style={styles.infoText}>
          <Text style={styles.bold}>Platform:</Text> {Platform.OS}
        </Text>
        <Text style={styles.infoText}>
          <Text style={styles.bold}>RTCView:</Text> {RTCView ? '✅ Available' : '❌ Not Available'}
        </Text>
        <Text style={styles.infoText}>
          <Text style={styles.bold}>mediaDevices:</Text> {mediaDevices ? '✅ Available' : '❌ Not Available'}
        </Text>
        <Text style={styles.infoText}>
          <Text style={styles.bold}>Stream Status:</Text> {stream ? '✅ Active' : '❌ Not Started'}
        </Text>
      </View>

      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>⚠️ {error}</Text>
        </View>
      )}

      <View style={styles.controls}>
        {!stream ? (
          <Button
            title={loading ? 'Starting...' : 'Start Front Camera'}
            onPress={startCamera}
            disabled={loading || isExpoGoEnv}
          />
        ) : (
          <Button title="Stop Camera" onPress={stopCamera} />
        )}
      </View>

      {loading && (
        <View style={styles.loading}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Requesting camera...</Text>
        </View>
      )}

      <View style={styles.videoContainer}>
        {stream && RTCView ? (
          <RTCView
            streamURL={stream.toURL()}
            style={styles.video}
            objectFit="cover"
            mirror={true}
            zOrder={0}
          />
        ) : (
          <View style={styles.placeholder}>
            <Text style={styles.placeholderText}>
              {isExpoGoEnv
                ? '⚠️ WebRTC not available in Expo Go\n\nUse: npx expo run:ios or npx expo run:android'
                : stream
                ? 'Loading video feed...'
                : 'Press "Start Front Camera" to begin'}
            </Text>
          </View>
        )}
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          {isExpoGoEnv
            ? '❌ You are in Expo Go. WebRTC requires a development build.'
            : !RTCView || !mediaDevices
            ? '❌ WebRTC not properly installed. Run: npm install react-native-webrtc && npx expo prebuild --clean && npx expo run:ios'
            : '✅ If you see black screen, check console for errors'}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
    padding: 20,
  },
  header: {
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#999',
  },
  info: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
  },
  infoText: {
    color: '#fff',
    fontSize: 12,
    marginBottom: 4,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  bold: {
    fontWeight: 'bold',
    color: '#007AFF',
  },
  errorContainer: {
    backgroundColor: '#ff3b30',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  controls: {
    marginBottom: 16,
  },
  loading: {
    alignItems: 'center',
    marginBottom: 16,
  },
  loadingText: {
    color: '#fff',
    marginTop: 8,
  },
  videoContainer: {
    flex: 1,
    backgroundColor: '#000',
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 16,
  },
  video: {
    flex: 1,
    backgroundColor: '#000',
  },
  placeholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
  },
  placeholderText: {
    color: '#999',
    fontSize: 14,
    textAlign: 'center',
    padding: 20,
  },
  footer: {
    backgroundColor: '#1a1a1a',
    padding: 12,
    borderRadius: 8,
  },
  footerText: {
    color: '#999',
    fontSize: 11,
    textAlign: 'center',
    lineHeight: 16,
  },
});

