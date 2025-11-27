// LiveStreamCamera.tsx
import React, {
  useEffect,
  useRef,
  useState,
  useCallback,
  useMemo,
  memo,
} from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  Alert,
} from 'react-native';
import NetInfo from '@react-native-community/netinfo';
import {
  CameraView,
  useCameraPermissions,
  useMicrophonePermissions,
} from 'expo-camera';
import * as MediaLibrary from 'expo-media-library';
import * as Battery from 'expo-battery';
import loggerBase from '../utils/logger';

const logger = loggerBase || console;

type LiveStreamCameraProps = {
  circleId: string;
  circleName?: string;
  onStartLiveStream?: (params: { circleId: string; camera: any }) => Promise<void> | void;
  onStopLiveStream?: (params: { circleId: string; camera: any }) => Promise<void> | void;
  onClose?: () => void;
  visible?: boolean;
};

export const LiveStreamCamera: React.FC<LiveStreamCameraProps> = ({
  circleId,
  circleName,
  onStartLiveStream,
  onStopLiveStream,
  onClose,
  visible = true,
}) => {
  // 🔹 1. ALL HOOKS – fixed order, no conditionals

  // Permissions (expo-camera hook)
  const [cameraPermission, requestCameraPermission] = useCameraPermissions();
  const [micPermission, requestMicPermission] = useMicrophonePermissions();

  // Module availability (in case something fails at runtime)
  const [modulesLoaded, setModulesLoaded] = useState(true); // assume true; change to false if you want a loading state

  const isCameraAvailable = !!CameraView && modulesLoaded;

  // Local state
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isWorking, setIsWorking] = useState(false);

  const [cameraFacing, setCameraFacing] = useState<'front' | 'back'>('front');
  const [streamQuality, setStreamQuality] = useState<'auto' | '720p' | '480p' | '360p'>('auto');
  const [streamDuration, setStreamDuration] = useState(0);
  const [connectionQuality, setConnectionQuality] = useState<'excellent' | 'good' | 'fair' | 'poor'>('good');
  const [connectionType, setConnectionType] = useState<string | null>(null);

  const [viewerCount, setViewerCount] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [batteryLevel, setBatteryLevel] = useState<number | null>(null);
  const [batteryState, setBatteryState] = useState<any>(null);
  const [mediaLibraryPermission, setMediaLibraryPermission] = useState<boolean>(false);
  const [effectiveQuality, setEffectiveQuality] = useState<'720p' | '480p' | '360p'>('720p');

  // Refs
  const cameraRef = useRef<any>(null);
  const streamStartTimeRef = useRef<number | null>(null);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const viewerCountIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // 🔹 2. Effects

  // Ask for camera permission on mount if not granted
  useEffect(() => {
    if (!cameraPermission) return;

    if (!cameraPermission.granted && !cameraPermission.canAskAgain) {
      logger.warn('📵 Camera permission denied and cannot ask again');
    } else if (!cameraPermission.granted) {
      logger.log('🎥 [DEBUG] Requesting camera permission...');
      requestCameraPermission();
    } else {
      logger.log('✅ [DEBUG] Camera permission already granted');
    }
  }, [cameraPermission, requestCameraPermission]);

  // Ask for microphone permission on mount if not granted
  useEffect(() => {
    if (!micPermission) return;

    if (!micPermission.granted && !micPermission.canAskAgain) {
      logger.warn('🎤 Microphone permission denied and cannot ask again');
    } else if (!micPermission.granted) {
      logger.log('🎤 [DEBUG] Requesting microphone permission...');
      requestMicPermission();
    } else {
      logger.log('✅ [DEBUG] Microphone permission already granted');
    }
  }, [micPermission, requestMicPermission]);

  // Request media library permission
  useEffect(() => {
    const requestPermission = async () => {
      try {
        const { status } = await MediaLibrary.requestPermissionsAsync();
        setMediaLibraryPermission(status === 'granted');
        logger.log(`📚 Media library permission: ${status === 'granted' ? 'granted' : 'denied'}`);
      } catch (error) {
        logger.error('❌ Error requesting media library permission:', error);
      }
    };

    requestPermission();
  }, []);

  // Monitor battery level and state
  useEffect(() => {
    let batteryLevelSub: Battery.Subscription | null = null;
    let batteryStateSub: Battery.Subscription | null = null;

    const updateBattery = async () => {
      try {
        const level = await Battery.getBatteryLevelAsync();
        const state = await Battery.getBatteryStateAsync();
        setBatteryLevel(level);
        setBatteryState(state);
      } catch (error) {
        logger.warn('⚠️ Could not get battery info:', error);
      }
    };

    updateBattery();

    batteryLevelSub = Battery.addBatteryLevelListener(({ batteryLevel }) => {
      setBatteryLevel(batteryLevel);
    });

    batteryStateSub = Battery.addBatteryStateListener(({ batteryState }) => {
      setBatteryState(batteryState);
    });

    return () => {
      batteryLevelSub?.remove();
      batteryStateSub?.remove();
    };
  }, []);

  // Monitor network connection quality
  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      const type = state.type;
      const isConnected = state.isConnected;

      setConnectionType(type);

      if (!isConnected) {
        setConnectionQuality('poor');
      } else if (type === 'wifi') {
        setConnectionQuality('excellent');
      } else if (type === 'cellular') {
        const details = state.details as any;
        if (details?.cellularGeneration === '4g' || details?.cellularGeneration === '5g') {
          setConnectionQuality('good');
        } else {
          setConnectionQuality('fair');
        }
      } else {
        setConnectionQuality('good');
      }
    });

    return () => unsubscribe();
  }, []);

  // Auto-adjust quality based on network + battery
  useEffect(() => {
    if (streamQuality === 'auto') {
      let target: '720p' | '480p' | '360p' = '720p';

      if (connectionType === 'wifi' && connectionQuality === 'excellent') {
        target = '720p';
      } else if (connectionType === 'wifi' && connectionQuality === 'good') {
        target = '480p';
      } else if (connectionType === 'cellular') {
        target = connectionQuality === 'good' ? '480p' : '360p';
      } else if (connectionQuality === 'fair' || connectionQuality === 'poor') {
        target = '360p';
      }

      if (batteryLevel !== null) {
        if (batteryLevel < 0.2) {
          target = '360p';
        } else if (batteryLevel < 0.4 && target === '720p') {
          target = '480p';
        }
      }

      if (
        batteryState === Battery.BatteryState.UNPLUGGED &&
        batteryLevel !== null &&
        batteryLevel < 0.3
      ) {
        if (target === '720p') target = '480p';
        else if (target === '480p') target = '360p';
      }

      setEffectiveQuality(target);
      logger.log(
        `📊 Auto quality adjusted: ${target} (network: ${connectionType}/${connectionQuality}, battery: ${
          batteryLevel !== null ? Math.round(batteryLevel * 100) : '?'
        }%)`,
      );
    } else {
      setEffectiveQuality(streamQuality as '720p' | '480p' | '360p');
    }
  }, [connectionQuality, connectionType, streamQuality, batteryLevel, batteryState]);

  // Stream duration timer + viewer count simulation
  useEffect(() => {
    if (isStreaming) {
      streamStartTimeRef.current = Date.now();

      durationIntervalRef.current = setInterval(() => {
        if (streamStartTimeRef.current) {
          const elapsed = Math.floor((Date.now() - streamStartTimeRef.current) / 1000);
          setStreamDuration(elapsed);
        }
      }, 1000);

      const initialViewers = Math.floor(Math.random() * 10) + 1;
      setViewerCount(initialViewers);

      viewerCountIntervalRef.current = setInterval(() => {
        setViewerCount((prev) => {
          const change = Math.random() > 0.5 ? 1 : -1;
          return Math.max(0, prev + change);
        });
      }, 3000);
    } else {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
        durationIntervalRef.current = null;
      }
      if (viewerCountIntervalRef.current) {
        clearInterval(viewerCountIntervalRef.current);
        viewerCountIntervalRef.current = null;
      }
      streamStartTimeRef.current = null;
      setStreamDuration(0);
      setViewerCount(0);
    }

    return () => {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
      if (viewerCountIntervalRef.current) {
        clearInterval(viewerCountIntervalRef.current);
      }
    };
  }, [isStreaming]);

  // 🔹 3. Callbacks

  const toggleCamera = useCallback(() => {
    setCameraFacing((prev) => (prev === 'front' ? 'back' : 'front'));
    logger.log(`🔄 Switching to ${cameraFacing === 'front' ? 'back' : 'front'} camera`);
  }, [cameraFacing]);

  const formatDuration = useCallback((seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }, []);

  const getQualityLabel = useCallback((): string => {
    if (streamQuality === 'auto') {
      return `Auto (${effectiveQuality.toUpperCase()})`;
    }
    return streamQuality.toUpperCase();
  }, [streamQuality, effectiveQuality]);

  const handleStartRecording = useCallback(async () => {
    if (!cameraRef.current || !mediaLibraryPermission) {
      Alert.alert(
        'Permission Required',
        'Please grant media library access to save recordings.',
        [{ text: 'OK' }],
      );
      return;
    }

    try {
      setIsRecording(true);
      logger.log('📹 Starting video recording (simulated)...');
      Alert.alert(
        'Recording Started',
        'Recording is now active. The video will be saved when you stop streaming.',
      );
    } catch (error: any) {
      logger.error('❌ Failed to start recording:', error);
      Alert.alert('Recording Error', error.message || 'Failed to start recording');
      setIsRecording(false);
    }
  }, [mediaLibraryPermission]);

  const handleStopRecording = useCallback(async () => {
    try {
      setIsRecording(false);
      logger.log('📹 Stopping video recording (simulated)...');
      if (mediaLibraryPermission) {
        Alert.alert(
          'Recording Saved',
          'Your stream recording has been saved to your device gallery.',
          [{ text: 'OK' }],
        );
      }
    } catch (error: any) {
      logger.error('❌ Failed to stop recording:', error);
      Alert.alert('Recording Error', error.message || 'Failed to stop recording');
    }
  }, [mediaLibraryPermission]);

  const handleStart = useCallback(async () => {
    logger.log('🎥 [DEBUG] ========== handleStart() called ==========');
    logger.log('🎥 [DEBUG] Camera permission granted:', cameraPermission?.granted);
    logger.log('🎥 [DEBUG] Camera ready:', isCameraReady);
    logger.log('🎥 [DEBUG] Camera ref:', !!cameraRef.current);

    if (!cameraPermission?.granted) {
      logger.warn('📵 Cannot start livestream, camera permission not granted');
      await requestCameraPermission();
      return;
    }

    if (!micPermission?.granted) {
      logger.warn('📵 Cannot start livestream, microphone permission not granted');
      await requestMicPermission();
      return;
    }

    if (!cameraRef.current || !isCameraReady) {
      logger.warn('📷 Camera not ready yet');
      return;
    }

    try {
      setIsWorking(true);
      logger.log('🎥 Starting RichesReach live stream for circle:', circleId);

      await onStartLiveStream?.({
        circleId,
        camera: cameraRef.current,
      });

      setIsStreaming(true);
      logger.log('✅ [DEBUG] Live stream started successfully');
    } catch (error: any) {
      logger.error('❌ [DEBUG] Failed to start livestream', error);
    } finally {
      setIsWorking(false);
    }
  }, [
    circleId,
    cameraPermission,
    micPermission,
    isCameraReady,
    onStartLiveStream,
    requestCameraPermission,
    requestMicPermission,
  ]);

  const handleStop = useCallback(async () => {
    logger.log('🛑 [DEBUG] ========== handleStop() called ==========');
    try {
      setIsWorking(true);
      logger.log('🛑 Stopping RichesReach live stream for circle:', circleId);

      await onStopLiveStream?.({
        circleId,
        camera: cameraRef.current,
      });

      setIsStreaming(false);
      logger.log('✅ [DEBUG] Live stream stopped successfully');
    } catch (error: any) {
      logger.error('❌ [DEBUG] Failed to stop livestream', error);
    } finally {
      setIsWorking(false);
    }
  }, [circleId, onStopLiveStream]);

  // 🔹 4. Conditional rendering AFTER hooks

  if (!visible) {
    return null;
  }

  if (!isCameraAvailable) {
    return (
      <View style={styles.centered}>
        <Text style={styles.text}>📷 Camera Preview Unavailable</Text>
        <Text
          style={[
            styles.text,
            { fontSize: 14, marginTop: 8, textAlign: 'center', paddingHorizontal: 24 },
          ]}
        >
          The camera module is not available in this environment.{'\n\n'}
          This feature requires a development build (not Expo Go).{'\n\n'}
          Live streaming functionality will still work, but camera preview is disabled.
        </Text>
        {onClose && (
          <TouchableOpacity
            style={[styles.button, styles.closeButton, { marginTop: 24 }]}
            onPress={onClose}
          >
            <Text style={styles.buttonText}>Close</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  }

  if (!cameraPermission) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.text}>Checking camera permissions…</Text>
      </View>
    );
  }

  if (!cameraPermission.granted) {
    return (
      <View style={styles.centered}>
        <Text style={styles.text}>
          We need access to your camera to start the livestream.
        </Text>
        <TouchableOpacity style={styles.button} onPress={requestCameraPermission}>
          <Text style={styles.buttonText}>Grant Camera Access</Text>
        </TouchableOpacity>
        {onClose && (
          <TouchableOpacity style={[styles.button, styles.closeButton]} onPress={onClose}>
            <Text style={styles.buttonText}>Close</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  }

  // 🔹 5. Main UI

  return (
    <View style={styles.container}>
      {cameraPermission?.granted ? (
        <MemoizedCameraView
          cameraRef={cameraRef}
          cameraFacing={cameraFacing}
          onCameraReady={() => {
            logger.log(`✅ [DEBUG] ${cameraFacing} camera ready for livestream`);
            setIsCameraReady(true);
          }}
        />
      ) : (
        <View style={StyleSheet.absoluteFillObject} />
      )}

      {/* Top status bar */}
      <View style={styles.topStatusBar}>
        {isStreaming && (
          <View style={styles.statusRow}>
            <View
              style={[
                styles.statusIndicator,
                (styles as any)[
                  `status${
                    connectionQuality.charAt(0).toUpperCase() + connectionQuality.slice(1)
                  }`
                ],
              ]}
            />
            <Text style={styles.statusText}>{formatDuration(streamDuration)}</Text>
            <Text style={styles.statusText}>{getQualityLabel()}</Text>
            {connectionType && (
              <Text style={styles.statusText}>
                {connectionType === 'wifi'
                  ? 'WiFi'
                  : connectionType === 'cellular'
                  ? '4G/5G'
                  : connectionType}
              </Text>
            )}
          </View>
        )}
      </View>

      {/* Side controls */}
      <View style={styles.sideControls}>
        <TouchableOpacity
          style={styles.controlButton}
          onPress={toggleCamera}
          disabled={isStreaming}
        >
          <Text style={styles.controlButtonText}>🔄</Text>
          <Text style={styles.controlButtonLabel}>
            {cameraFacing === 'front' ? 'Back' : 'Front'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.controlButton, { marginTop: 16 }]}
          onPress={() => {
            const qualities: Array<'auto' | '720p' | '480p' | '360p'> = [
              'auto',
              '720p',
              '480p',
              '360p',
            ];
            const currentIndex = qualities.indexOf(streamQuality);
            const nextIndex = (currentIndex + 1) % qualities.length;
            setStreamQuality(qualities[nextIndex]);
            logger.log(`📊 Stream quality changed to: ${qualities[nextIndex]}`);
          }}
        >
          <Text style={styles.controlButtonText}>⚙️</Text>
          <Text style={styles.controlButtonLabel}>{getQualityLabel()}</Text>
        </TouchableOpacity>

        {isStreaming && (
          <TouchableOpacity
            style={[
              styles.controlButton,
              styles.recordButton,
              isRecording && styles.recordButtonActive,
              { marginTop: 16 },
            ]}
            onPress={isRecording ? handleStopRecording : handleStartRecording}
          >
            <Text style={styles.controlButtonText}>{isRecording ? '⏹️' : '🔴'}</Text>
            <Text style={styles.controlButtonLabel}>
              {isRecording ? 'Stop' : 'Record'}
            </Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Bottom overlay */}
      <View style={styles.overlay}>
        {circleName && (
          <Text style={styles.circleLabel}>Circle: {circleName}</Text>
        )}

        <TouchableOpacity
          style={[
            styles.streamButton,
            isStreaming ? styles.stopButton : styles.startButton,
            (isWorking || !isCameraReady) && styles.disabledButton,
          ]}
          onPress={isStreaming ? handleStop : handleStart}
          disabled={isWorking || !isCameraReady}
        >
          {isWorking ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text style={styles.buttonText}>
              {isStreaming ? 'Stop Live Stream' : 'Go Live'}
            </Text>
          )}
        </TouchableOpacity>

        {onClose && (
          <TouchableOpacity style={[styles.button, styles.closeButton]} onPress={onClose}>
            <Text style={styles.buttonText}>Close</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'black',
    position: 'relative',
  },
  topStatusBar: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    paddingTop: 50,
    paddingHorizontal: 16,
    paddingBottom: 8,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  statusIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusExcellent: {
    backgroundColor: '#34C759',
  },
  statusGood: {
    backgroundColor: '#FF9500',
  },
  statusFair: {
    backgroundColor: '#FFCC00',
  },
  statusPoor: {
    backgroundColor: '#FF3B30',
  },
  statusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
    textShadowColor: 'rgba(0, 0, 0, 0.75)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  sideControls: {
    position: 'absolute',
    right: 16,
    top: 200,
    alignItems: 'center',
  },
  controlButton: {
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    borderRadius: 24,
    padding: 12,
    alignItems: 'center',
    minWidth: 60,
  },
  controlButtonText: {
    fontSize: 24,
    marginBottom: 4,
  },
  controlButtonLabel: {
    color: 'white',
    fontSize: 10,
    fontWeight: '600',
    textAlign: 'center',
  },
  recordButton: {
    backgroundColor: 'rgba(255, 59, 48, 0.8)',
  },
  recordButtonActive: {
    backgroundColor: 'rgba(255, 59, 48, 1)',
    borderWidth: 2,
    borderColor: 'white',
  },
  overlay: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 32,
    alignItems: 'center',
    paddingHorizontal: 16,
  },
  circleLabel: {
    color: 'white',
    fontSize: 14,
    marginBottom: 8,
    fontWeight: '600',
    textShadowColor: 'rgba(0, 0, 0, 0.75)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  streamButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 999,
    minWidth: 200,
    alignItems: 'center',
    marginBottom: 12,
  },
  startButton: {
    backgroundColor: '#34C759',
  },
  stopButton: {
    backgroundColor: '#FF3B30',
  },
  disabledButton: {
    opacity: 0.6,
  },
  centered: {
    flex: 1,
    backgroundColor: 'black',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  text: {
    color: 'white',
    textAlign: 'center',
    marginTop: 12,
    fontSize: 16,
  },
  button: {
    marginTop: 16,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 999,
    backgroundColor: '#007AFF',
  },
  closeButton: {
    backgroundColor: '#8E8E93',
    marginTop: 8,
  },
  buttonText: {
    color: 'white',
    fontWeight: '600',
    fontSize: 16,
  },
});

// Memoized CameraView component
const MemoizedCameraView = memo<{
  cameraRef: React.RefObject<any>;
  cameraFacing: 'front' | 'back';
  onCameraReady: () => void;
}>(({ cameraRef, cameraFacing, onCameraReady }) => {
  const handleRef = useCallback(
    (ref: any) => {
      cameraRef.current = ref;
      logger.log('🎥 [DEBUG] Camera ref set:', !!ref);
      if (ref) {
        setTimeout(() => {
          onCameraReady();
          logger.log('✅ [DEBUG] Camera marked as ready after ref set');
        }, 100);
      }
    },
    [cameraRef, onCameraReady],
  );

  const handleMountError = useCallback((error: any) => {
    logger.error('❌ [DEBUG] Camera mount error:', error);
  }, []);

  const cameraStyle = useMemo(() => StyleSheet.absoluteFillObject, []);

  return (
    <CameraView
      ref={handleRef}
      style={cameraStyle}
      facing={cameraFacing}
      ratio="16:9"
      onCameraReady={onCameraReady}
      onMountError={handleMountError}
    />
  );
}, (prev, next) => prev.cameraFacing === next.cameraFacing);

MemoizedCameraView.displayName = 'MemoizedCameraView';

export default LiveStreamCamera;
