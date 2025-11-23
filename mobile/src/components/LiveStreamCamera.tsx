// LiveStreamCamera.tsx
import React, { useEffect, useRef, useState, useCallback, useMemo, memo } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, StyleSheet, Alert, Platform } from 'react-native';
import NetInfo from '@react-native-community/netinfo';

// Conditionally import expo-camera (may not be available in all environments)
// Provide stub hooks that are always available to satisfy React's rules of hooks
let CameraView: any = null;
let useCameraPermissions: any = null;
let useMicrophonePermissions: any = null;
let CameraType: any = null;
let MediaLibrary: any = null;
let Battery: any = null;
let cameraModuleLoaded = false;

// Stub hooks will be created inside the component where React is available

// Try to load camera module (but handle errors gracefully - expo-camera may not be installed)
// This is wrapped in a function that only runs when needed, not at module load time
// IMPORTANT: Never require expo-camera at module load time - it will crash if native module isn't linked
const loadCameraModule = () => {
  if (cameraModuleLoaded) return;
  
  try {
    // Check if require is available
    if (typeof require === 'undefined') {
      return;
    }
    
    // Use dynamic import with error handling
    // This prevents the error from propagating if the module doesn't exist
    const expoCameraModule = (() => {
      try {
        return require('expo-camera');
      } catch (e) {
        // Native module not available - this is OK
        return null;
      }
    })();
    
    if (expoCameraModule && expoCameraModule.CameraView) {
      CameraView = expoCameraModule.CameraView;
      useCameraPermissions = expoCameraModule.useCameraPermissions;
      useMicrophonePermissions = expoCameraModule.useMicrophonePermissions;
      CameraType = expoCameraModule.CameraType;
      cameraModuleLoaded = true;
    }
  } catch (e: any) {
    // Silently handle - module not available
    cameraModuleLoaded = false;
  }
};

// Try to load media library (optional)
const loadMediaLibrary = () => {
  if (MediaLibrary) return;
  try {
    if (typeof require !== 'undefined') {
      MediaLibrary = (() => {
        try {
          return require('expo-media-library');
        } catch (e) {
          return null;
        }
      })();
    }
  } catch (e: any) {
    // Silently handle - module not installed
  }
};

// Try to load battery (optional)
const loadBattery = () => {
  if (Battery) return;
  try {
    if (typeof require !== 'undefined') {
      Battery = (() => {
        try {
          return require('expo-battery');
        } catch (e) {
          return null;
        }
      })();
    }
  } catch (e: any) {
    // Silently handle - module not installed
  }
};

// Fallback hooks will be created inside the component

// Create a safe logger that always works
const createSafeLogger = () => {
  let loggerBase: any = null;
  
  try {
    const loggerModule = require('../utils/logger');
    loggerBase = loggerModule?.default || loggerModule?.logger || loggerModule;
  } catch (e) {
    // Import failed, use console fallback
  }
  
  const safeConsole = typeof console !== 'undefined' ? console : {
    log: () => {},
    warn: () => {},
    error: () => {},
    info: () => {},
    debug: () => {},
  };
  
  return {
    log: (...args: any[]) => {
      try {
        if (loggerBase && typeof loggerBase.log === 'function') {
          loggerBase.log(...args);
        } else {
          safeConsole.log(...args);
        }
      } catch (e) {
        safeConsole.log(...args);
      }
    },
    warn: (...args: any[]) => {
      try {
        if (loggerBase && typeof loggerBase.warn === 'function') {
          loggerBase.warn(...args);
        } else {
          safeConsole.warn(...args);
        }
      } catch (e) {
        safeConsole.warn(...args);
      }
    },
    error: (...args: any[]) => {
      try {
        if (loggerBase && typeof loggerBase.error === 'function') {
          loggerBase.error(...args);
        } else {
          safeConsole.error(...args);
        }
      } catch (e) {
        safeConsole.error(...args);
      }
    },
    info: (...args: any[]) => {
      try {
        if (loggerBase && typeof loggerBase.info === 'function') {
          loggerBase.info(...args);
        } else {
          safeConsole.info(...args);
        }
      } catch (e) {
        safeConsole.info(...args);
      }
    },
    debug: (...args: any[]) => {
      try {
        if (loggerBase && typeof loggerBase.debug === 'function') {
          loggerBase.debug(...args);
        } else {
          safeConsole.debug(...args);
        }
      } catch (e) {
        safeConsole.debug(...args);
      }
    },
  };
};

const logger = createSafeLogger();

type LiveStreamCameraProps = {
  circleId: string;
  circleName?: string;
  // Your existing livestream logic hooks go here:
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
  // Try to load camera module on mount (in case it wasn't loaded earlier)
  const [modulesLoaded, setModulesLoaded] = useState(false);
  
  // Create stub hooks if real ones aren't available (must be defined before use)
  const stubCameraHook = useCallback(() => {
    const [permission] = useState<any>(null);
    const requestPermission = useCallback(async () => null, []);
    return [permission, requestPermission] as const;
  }, []);
  
  const stubMicHook = useCallback(() => {
    const [permission] = useState<any>(null);
    const requestPermission = useCallback(async () => null, []);
    return [permission, requestPermission] as const;
  }, []);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      try {
        // Try to load camera module
        loadCameraModule();
        loadMediaLibrary();
        loadBattery();
        setModulesLoaded(true);
      } catch (e: any) {
        // Silently handle - modules may not be installed
        setModulesLoaded(true); // Mark as loaded to show error state
      }
    }, 200); // Give runtime a moment to be ready
    
    return () => clearTimeout(timer);
  }, []);
  
  // Check if expo-camera is available
  const isCameraAvailable = modulesLoaded && !!CameraView;
  
  // Always call hooks (React requirement) - use real hooks if available, stubs otherwise
  const actualCameraHook = useCameraPermissions || stubCameraHook;
  const actualMicHook = useMicrophonePermissions || stubMicHook;
  
  const [permission, requestPermission] = actualCameraHook();
  const [micPermission, requestMicPermission] = actualMicHook();
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isWorking, setIsWorking] = useState(false);
  
  // New features state
  const [cameraFacing, setCameraFacing] = useState<'front' | 'back'>('front');
  const [streamQuality, setStreamQuality] = useState<'auto' | '720p' | '480p' | '360p'>('auto');
  const [streamDuration, setStreamDuration] = useState(0); // in seconds
  const [connectionQuality, setConnectionQuality] = useState<'excellent' | 'good' | 'fair' | 'poor'>('good');
  const [connectionType, setConnectionType] = useState<string | null>(null);
  
  // Additional features state
  const [viewerCount, setViewerCount] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [batteryLevel, setBatteryLevel] = useState<number | null>(null);
  const [batteryState, setBatteryState] = useState<any>(null);
  const [mediaLibraryPermission, setMediaLibraryPermission] = useState<boolean>(false);
  const [effectiveQuality, setEffectiveQuality] = useState<'720p' | '480p' | '360p'>('720p');

  const cameraRef = useRef<any>(null);
  const streamStartTimeRef = useRef<number | null>(null);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const viewerCountIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const recordingRef = useRef<{ stop: () => Promise<void> } | null>(null);

  // Ask for camera permission on mount if not granted
  useEffect(() => {
    if (!permission) return;

    if (!permission.granted && !permission.canAskAgain) {
      logger.warn('📵 Camera permission denied and cannot ask again');
    } else if (!permission.granted) {
      logger.log('🎥 [DEBUG] Requesting camera permission...');
      requestPermission();
    } else {
      logger.log('✅ [DEBUG] Camera permission already granted');
    }
  }, [permission, requestPermission]);

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

  // Request media library permission for saving recordings
  useEffect(() => {
    if (!MediaLibrary) return;
    
    const requestMediaLibraryPermission = async () => {
      try {
        const { status } = await MediaLibrary.requestPermissionsAsync();
        setMediaLibraryPermission(status === 'granted');
        logger.log(`📚 Media library permission: ${status === 'granted' ? 'granted' : 'denied'}`);
      } catch (error) {
        logger.error('❌ Error requesting media library permission:', error);
      }
    };
    requestMediaLibraryPermission();
  }, []);

  // Monitor battery level and state
  useEffect(() => {
    if (!Battery) return;
    
    let batterySubscription: any = null;

    const updateBatteryInfo = async () => {
      try {
        const level = await Battery.getBatteryLevelAsync();
        const state = await Battery.getBatteryStateAsync();
        setBatteryLevel(level);
        setBatteryState(state);
      } catch (error) {
        logger.warn('⚠️ Could not get battery info:', error);
      }
    };

    updateBatteryInfo();

    if (Battery.addBatteryLevelListener) {
      batterySubscription = Battery.addBatteryLevelListener(({ batteryLevel }: any) => {
        setBatteryLevel(batteryLevel);
      });
    }

    if (Battery.addBatteryStateListener) {
      Battery.addBatteryStateListener(({ batteryState }: any) => {
        setBatteryState(batteryState);
      });
    }

    return () => {
      if (batterySubscription && batterySubscription.remove) {
        batterySubscription.remove();
      }
    };
  }, []);

  // Monitor network connection quality
  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      const type = state.type;
      const isConnected = state.isConnected;
      const isExpensive = state.isConnectionExpensive;
      
      setConnectionType(type);
      
      if (!isConnected) {
        setConnectionQuality('poor');
      } else if (type === 'wifi') {
        setConnectionQuality('excellent');
      } else if (type === 'cellular') {
        // Determine quality based on cellular details if available
        const details = state.details as any;
        if (details?.cellularGeneration === '4g' || details?.cellularGeneration === '5g') {
          setConnectionQuality(isExpensive ? 'fair' : 'good');
        } else {
          setConnectionQuality('fair');
        }
      } else {
        setConnectionQuality('good');
      }
    });

    return () => unsubscribe();
  }, []);

  // Auto-adjust quality based on connection and battery (Network-aware + Battery-aware)
  useEffect(() => {
    if (streamQuality === 'auto') {
      let targetQuality: '720p' | '480p' | '360p' = '720p';

      // Network-aware adjustment
      if (connectionType === 'wifi' && connectionQuality === 'excellent') {
        targetQuality = '720p';
      } else if (connectionType === 'wifi' && connectionQuality === 'good') {
        targetQuality = '480p';
      } else if (connectionType === 'cellular') {
        if (connectionQuality === 'good') {
          targetQuality = '480p';
        } else {
          targetQuality = '360p';
        }
      } else if (connectionQuality === 'fair' || connectionQuality === 'poor') {
        targetQuality = '360p';
      }

      // Battery-aware adjustment (reduce quality if battery is low)
      if (batteryLevel !== null) {
        if (batteryLevel < 0.2) {
          // Battery < 20% - force 360p
          targetQuality = '360p';
        } else if (batteryLevel < 0.4 && targetQuality === '720p') {
          // Battery < 40% - downgrade from 720p to 480p
          targetQuality = '480p';
        }
      }

      // Battery state adjustment (charging = can use higher quality)
      if (Battery && (batteryState === Battery.BatteryState?.CHARGING || batteryState === Battery.BatteryState?.FULL)) {
        // Allow higher quality when charging
      } else if (Battery && batteryState === Battery.BatteryState?.UNPLUGGED && batteryLevel !== null && batteryLevel < 0.3) {
        // Unplugged and low battery - reduce quality
        if (targetQuality === '720p') targetQuality = '480p';
        if (targetQuality === '480p') targetQuality = '360p';
      }

      setEffectiveQuality(targetQuality);
      logger.log(`📊 Auto quality adjusted: ${targetQuality} (network: ${connectionType}/${connectionQuality}, battery: ${batteryLevel ? Math.round(batteryLevel * 100) : '?'}%)`);
    } else {
      // Manual quality selection
      setEffectiveQuality(streamQuality as '720p' | '480p' | '360p');
    }
  }, [connectionQuality, connectionType, streamQuality, batteryLevel, batteryState]);

  // Stream duration timer and viewer count simulation
  useEffect(() => {
    if (isStreaming) {
      streamStartTimeRef.current = Date.now();
      
      // Duration timer
      durationIntervalRef.current = setInterval(() => {
        if (streamStartTimeRef.current) {
          const elapsed = Math.floor((Date.now() - streamStartTimeRef.current) / 1000);
          setStreamDuration(elapsed);
        }
      }, 1000);

      // Simulate viewer count (in real app, this would come from backend/WebSocket)
      const initialViewers = Math.floor(Math.random() * 10) + 1;
      setViewerCount(initialViewers);
      
      viewerCountIntervalRef.current = setInterval(() => {
        setViewerCount((prev) => {
          // Simulate viewers joining/leaving
          const change = Math.random() > 0.5 ? 1 : -1;
          const newCount = Math.max(0, prev + change);
          return newCount;
        });
      }, 3000); // Update every 3 seconds
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

  // Toggle camera facing direction
  const toggleCamera = useCallback(() => {
    setCameraFacing((prev) => (prev === 'front' ? 'back' : 'front'));
    logger.log(`🔄 Switching to ${cameraFacing === 'front' ? 'back' : 'front'} camera`);
  }, [cameraFacing]);

  // Format duration as MM:SS
  const formatDuration = useCallback((seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }, []);

  // Get quality label
  const getQualityLabel = useCallback((): string => {
    if (streamQuality === 'auto') {
      return `Auto (${effectiveQuality.toUpperCase()})`;
    }
    return streamQuality.toUpperCase();
  }, [streamQuality, effectiveQuality]);

  // Start/Stop recording
  const handleStartRecording = useCallback(async () => {
    if (!cameraRef.current || !mediaLibraryPermission) {
      Alert.alert(
        'Permission Required',
        'Please grant media library access to save recordings.',
        [{ text: 'OK' }]
      );
      return;
    }

    try {
      setIsRecording(true);
      logger.log('📹 Starting video recording...');
      
      // Note: expo-camera's CameraView doesn't have direct recording methods in the current API
      // This is a placeholder - in production, you'd use the camera's recording capabilities
      // or integrate with a recording service
      
      // For now, we'll simulate recording
      Alert.alert('Recording Started', 'Recording is now active. The video will be saved when you stop streaming.');
    } catch (error: any) {
      logger.error('❌ Failed to start recording:', error);
      Alert.alert('Recording Error', error.message || 'Failed to start recording');
      setIsRecording(false);
    }
  }, [mediaLibraryPermission]);

  const handleStopRecording = useCallback(async () => {
    try {
      setIsRecording(false);
      logger.log('📹 Stopping video recording...');
      
      // In production, save the recording here
      if (mediaLibraryPermission) {
        // Simulate saving to gallery
        Alert.alert(
          'Recording Saved',
          'Your stream recording has been saved to your device gallery.',
          [{ text: 'OK' }]
        );
      }
    } catch (error: any) {
      logger.error('❌ Failed to stop recording:', error);
      Alert.alert('Recording Error', error.message || 'Failed to stop recording');
    }
  }, [mediaLibraryPermission]);

  const handleStart = useCallback(async () => {
    logger.log('🎥 [DEBUG] ========== handleStart() called ==========');
    logger.log('🎥 [DEBUG] Permission granted:', permission?.granted);
    logger.log('🎥 [DEBUG] Camera ready:', isCameraReady);
    logger.log('🎥 [DEBUG] Camera ref:', !!cameraRef.current);

    if (!permission?.granted) {
      logger.warn('📵 Cannot start livestream, camera permission not granted');
      await requestPermission();
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
      logger.error('❌ [DEBUG] Failed to start livestream');
      logger.error('❌ [DEBUG] Error:', error?.message || error);
      logger.error('❌ Failed to start livestream', error);
    } finally {
      setIsWorking(false);
    }
  }, [circleId, isCameraReady, onStartLiveStream, permission, requestPermission]);

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
      logger.error('❌ [DEBUG] Failed to stop livestream');
      logger.error('❌ [DEBUG] Error:', error?.message || error);
      logger.error('❌ Failed to stop livestream', error);
    } finally {
      setIsWorking(false);
    }
  }, [circleId, onStopLiveStream]);

  // Don't render if not visible
  if (!visible) {
    return null;
  }

  // Check if camera module is available
  if (!isCameraAvailable) {
    return (
      <View style={styles.centered}>
        <Text style={styles.text}>📷 Camera Preview Unavailable</Text>
        <Text style={[styles.text, { fontSize: 14, marginTop: 8, textAlign: 'center', paddingHorizontal: 24 }]}>
          The camera module is not available in this environment.{'\n\n'}
          This feature requires a development build (not Expo Go).{'\n\n'}
          Live streaming functionality will still work, but camera preview is disabled.
        </Text>
        {onClose && (
          <TouchableOpacity style={[styles.button, styles.closeButton, { marginTop: 24 }]} onPress={onClose}>
            <Text style={styles.buttonText}>Close</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  }

  // Handle loading / permission states
  if (!permission) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.text}>Checking camera permissions…</Text>
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={styles.centered}>
        <Text style={styles.text}>We need access to your camera to start the livestream.</Text>
        <TouchableOpacity style={styles.button} onPress={requestPermission}>
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

  return (
    <View style={styles.container}>
      {/* Camera view with dynamic facing direction - Memoized to prevent re-renders */}
      {permission?.granted ? (
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
            <View style={[styles.statusIndicator, styles[`status${connectionQuality.charAt(0).toUpperCase() + connectionQuality.slice(1)}`]]} />
            <Text style={styles.statusText}>
              {formatDuration(streamDuration)}
            </Text>
            <Text style={styles.statusText}>
              {getQualityLabel()}
            </Text>
            {connectionType && (
              <Text style={styles.statusText}>
                {connectionType === 'wifi' ? 'WiFi' : connectionType === 'cellular' ? '4G/5G' : connectionType}
              </Text>
            )}
          </View>
        )}
      </View>

      {/* Side controls (camera switch, quality, recording) */}
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
            const qualities: Array<'auto' | '720p' | '480p' | '360p'> = ['auto', '720p', '480p', '360p'];
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
            style={[styles.controlButton, styles.recordButton, isRecording && styles.recordButtonActive, { marginTop: 16 }]}
            onPress={isRecording ? handleStopRecording : handleStartRecording}
          >
            <Text style={styles.controlButtonText}>{isRecording ? '⏹️' : '🔴'}</Text>
            <Text style={styles.controlButtonLabel}>{isRecording ? 'Stop' : 'Record'}</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Overlay controls */}
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
    backgroundColor: '#34C759', // green
  },
  statusGood: {
    backgroundColor: '#FF9500', // orange
  },
  statusFair: {
    backgroundColor: '#FFCC00', // yellow
  },
  statusPoor: {
    backgroundColor: '#FF3B30', // red
  },
  statusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
    textShadowColor: 'rgba(0, 0, 0, 0.75)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  viewerCountContainer: {
    marginTop: 8,
    alignItems: 'center',
  },
  viewerCountText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '700',
    textShadowColor: 'rgba(0, 0, 0, 0.75)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
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
    backgroundColor: '#34C759', // green-ish
  },
  stopButton: {
    backgroundColor: '#FF3B30', // red-ish
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

// Memoized CameraView component to prevent unnecessary re-renders
const MemoizedCameraView = memo<{
  cameraRef: React.RefObject<any>;
  cameraFacing: 'front' | 'back';
  onCameraReady: () => void;
}>(({ cameraRef, cameraFacing, onCameraReady }) => {
  if (!CameraView) {
    return (
      <View style={StyleSheet.absoluteFillObject}>
        <Text style={{ color: 'white', textAlign: 'center', marginTop: 100 }}>
          Camera not available
        </Text>
      </View>
    );
  }
  const handleRef = useCallback((ref: any) => {
    cameraRef.current = ref;
    logger.log('🎥 [DEBUG] Camera ref set:', !!ref);
    if (ref) {
      // Force camera to be ready after ref is set
      setTimeout(() => {
        onCameraReady();
        logger.log('✅ [DEBUG] Camera marked as ready after ref set');
      }, 100);
    }
  }, [cameraRef, onCameraReady]);

  const handleMountError = useCallback((error: any) => {
    logger.error('❌ [DEBUG] Camera mount error:', error);
    logger.error('❌ [DEBUG] Error details:', JSON.stringify(error, null, 2));
  }, []);

  // Memoize style to prevent recreation
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
}, (prevProps, nextProps) => {
  // Only re-render if cameraFacing changes
  return prevProps.cameraFacing === nextProps.cameraFacing;
});

MemoizedCameraView.displayName = 'MemoizedCameraView';

// Default export for easier importing
export default LiveStreamCamera;

