import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  Animated,
  Dimensions,
} from 'react-native';
import { Audio } from 'expo-av';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import LinearGradient from 'expo-linear-gradient';

const { width: screenWidth } = Dimensions.get('window');

interface VoiceAIProps {
  text: string;
  voice?: 'default' | 'finance_expert' | 'friendly_advisor' | 'confident_analyst';
  speed?: number;
  emotion?: 'neutral' | 'confident' | 'friendly' | 'analytical' | 'encouraging';
  autoPlay?: boolean;
  onPlayStart?: () => void;
  onPlayEnd?: () => void;
  onError?: (error: string) => void;
  style?: any;
}

interface VoiceInfo {
  name: string;
  description: string;
  emotions: string[];
}

export default function VoiceAI({
  text,
  voice = 'default',
  speed = 1.0,
  emotion = 'neutral',
  autoPlay = false,
  onPlayStart,
  onPlayEnd,
  onError,
  style,
}: VoiceAIProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [sound, setSound] = useState<Audio.Sound | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [availableVoices, setAvailableVoices] = useState<Record<string, VoiceInfo>>({});
  const [pulseAnim] = useState(new Animated.Value(1));
  const [waveAnim] = useState(new Animated.Value(0));

  const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://192.168.1.236:8000';

  useEffect(() => {
    loadAvailableVoices();
    return () => {
      if (sound) {
        sound.unloadAsync();
      }
    };
  }, []);

  useEffect(() => {
    if (autoPlay && text && !isLoading && !isPlaying) {
      handlePlay();
    }
  }, [autoPlay, text]);

  const loadAvailableVoices = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/voice-ai/voices/`);
      if (response.ok) {
        const data = await response.json();
        setAvailableVoices(data.voices || {});
      }
    } catch (error) {
      console.error('Failed to load voices:', error);
    }
  };

  const synthesizeSpeech = async (): Promise<string | null> => {
    try {
      setIsLoading(true);
      
      const token = await AsyncStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/voice-ai/synthesize/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          text,
          voice,
          speed,
          emotion,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Failed to synthesize speech');
      }

      return `${API_BASE_URL}${data.audio_url}`;
    } catch (error) {
      console.error('TTS synthesis error:', error);
      onError?.(error instanceof Error ? error.message : 'Failed to generate speech');
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlay = async () => {
    try {
      if (isPlaying) {
        await handleStop();
        return;
      }

      onPlayStart?.();

      // Get or generate audio
      let currentAudioUrl = audioUrl;
      if (!currentAudioUrl) {
        currentAudioUrl = await synthesizeSpeech();
        if (!currentAudioUrl) return;
        setAudioUrl(currentAudioUrl);
      }

      // Load and play audio
      const { sound: newSound } = await Audio.Sound.createAsync(
        { uri: currentAudioUrl },
        { shouldPlay: true }
      );

      setSound(newSound);
      setIsPlaying(true);

      // Start animations
      startPulseAnimation();
      startWaveAnimation();

      // Set up playback status listener
      newSound.setOnPlaybackStatusUpdate((status) => {
        if (status.isLoaded && status.didJustFinish) {
          handlePlayEnd();
        }
      });

    } catch (error) {
      console.error('Playback error:', error);
      onError?.(error instanceof Error ? error.message : 'Failed to play audio');
      setIsPlaying(false);
    }
  };

  const handleStop = async () => {
    try {
      if (sound) {
        await sound.stopAsync();
        await sound.unloadAsync();
        setSound(null);
      }
      setIsPlaying(false);
      stopAnimations();
      onPlayEnd?.();
    } catch (error) {
      console.error('Stop error:', error);
    }
  };

  const handlePlayEnd = () => {
    setIsPlaying(false);
    stopAnimations();
    onPlayEnd?.();
  };

  const startPulseAnimation = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.2,
          duration: 800,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 800,
          useNativeDriver: true,
        }),
      ])
    ).start();
  };

  const startWaveAnimation = () => {
    Animated.loop(
      Animated.timing(waveAnim, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      })
    ).start();
  };

  const stopAnimations = () => {
    pulseAnim.stopAnimation();
    waveAnim.stopAnimation();
    pulseAnim.setValue(1);
    waveAnim.setValue(0);
  };

  const getVoiceDisplayName = () => {
    return availableVoices[voice]?.name || voice.replace('_', ' ').toUpperCase();
  };

  const getVoiceDescription = () => {
    return availableVoices[voice]?.description || 'Natural voice synthesis';
  };

  return (
    <View style={[styles.container, style]}>
      {/* Voice Info */}
      <View style={styles.voiceInfo}>
        <Text style={styles.voiceName}>{getVoiceDisplayName()}</Text>
        <Text style={styles.voiceDescription}>{getVoiceDescription()}</Text>
      </View>

      {/* Play Button */}
      <TouchableOpacity
        style={styles.playButton}
        onPress={handlePlay}
        disabled={isLoading || !text}
        activeOpacity={0.8}
      >
        <LinearGradient
          colors={isPlaying ? ['#FF6B6B', '#FF8E8E'] : ['#4ECDC4', '#44A08D']}
          style={styles.playButtonGradient}
        >
          {isLoading ? (
            <ActivityIndicator color="#FFFFFF" size="small" />
          ) : (
            <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
              <Ionicons
                name={isPlaying ? 'stop' : 'play'}
                size={24}
                color="#FFFFFF"
              />
            </Animated.View>
          )}
        </LinearGradient>
      </TouchableOpacity>

      {/* Wave Animation */}
      {isPlaying && (
        <View style={styles.waveContainer}>
          {[0, 1, 2, 3, 4].map((index) => (
            <Animated.View
              key={index}
              style={[
                styles.waveBar,
                {
                  transform: [
                    {
                      scaleY: waveAnim.interpolate({
                        inputRange: [0, 1],
                        outputRange: [0.3, 1],
                      }),
                    },
                  ],
                  opacity: waveAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0.5, 1],
                  }),
                },
              ]}
            />
          ))}
        </View>
      )}

      {/* Status Text */}
      <Text style={styles.statusText}>
        {isLoading
          ? 'Generating speech...'
          : isPlaying
          ? 'Playing...'
          : text
          ? 'Tap to play'
          : 'No text to speak'}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    marginVertical: 8,
  },
  voiceInfo: {
    alignItems: 'center',
    marginBottom: 16,
  },
  voiceName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2C3E50',
    marginBottom: 4,
  },
  voiceDescription: {
    fontSize: 12,
    color: '#7F8C8D',
    textAlign: 'center',
  },
  playButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    marginBottom: 16,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
  },
  playButtonGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
  },
  waveContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
    height: 30,
  },
  waveBar: {
    width: 4,
    height: 20,
    backgroundColor: '#4ECDC4',
    marginHorizontal: 2,
    borderRadius: 2,
  },
  statusText: {
    fontSize: 12,
    color: '#7F8C8D',
    textAlign: 'center',
  },
});
