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
import * as FileSystem from 'expo-file-system';
import { synthesize, TTSConfig } from '../voice/ttsClient';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LinearGradient } from 'expo-linear-gradient';
import { useVoice } from '../contexts/VoiceContext';

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
  voice,
  speed = 1.0,
  emotion = 'neutral',
  autoPlay = false,
  onPlayStart,
  onPlayEnd,
  onError,
  style,
}: VoiceAIProps) {
  const { getSelectedVoice } = useVoice();
  const selectedVoice = voice || getSelectedVoice();
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [sound, setSound] = useState<Audio.Sound | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [availableVoices, setAvailableVoices] = useState<Record<string, VoiceInfo>>({});
  const [pulseAnim] = useState(new Animated.Value(1));
  const [waveAnim] = useState(new Animated.Value(0));

  const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000";

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
      const voicesPath = (process.env.EXPO_PUBLIC_TTS_VOICES_PATH || '/api/voices/').replace(/^\/?/, '/');
      const response = await fetch(`${API_BASE_URL}${voicesPath}`);
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
      const cfg: TTSConfig = {
        provider: (process.env.EXPO_PUBLIC_TTS_PROVIDER as any) || 'polly',
        baseUrl: process.env.EXPO_PUBLIC_TTS_BASE_URL || API_BASE_URL,
        apiKey: process.env.EXPO_PUBLIC_TTS_API_KEY,
        voiceId: process.env.EXPO_PUBLIC_TTS_VOICE || 'Joanna',
        model: process.env.EXPO_PUBLIC_TTS_MODEL,
        format: 'mp3',
      };
      const buf = await synthesize(text, cfg);
      const b64 = arrayBufferToBase64(buf);
      const path = FileSystem.cacheDirectory + `tts_${Date.now()}.mp3`;
      await FileSystem.writeAsStringAsync(path, b64, { encoding: FileSystem.EncodingType.Base64 });
      return path;
    } catch (error: any) {
      console.error('TTS synthesis error:', error?.message || String(error));
      onError?.(error?.message || 'Failed to generate speech');
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const previewVoice = async (): Promise<string | null> => {
    try {
      const token = await AsyncStorage.getItem('token');
      const previewPath = (process.env.EXPO_PUBLIC_TTS_PREVIEW_PATH || '/api/preview/').replace(/^[^/]/, (m) => `/${m}`);
      const response = await fetch(`${API_BASE_URL}${previewPath}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          // Many backends expect voiceId instead of voice; include both
          voiceId: selectedVoice,
          voice: selectedVoice,
          speed,
          emotion,
          sample: process.env.EXPO_PUBLIC_TTS_PREVIEW_SAMPLE || 'This is a quick voice preview.',
          text: process.env.EXPO_PUBLIC_TTS_PREVIEW_SAMPLE || 'This is a quick voice preview.',
          format: 'mp3'
        }),
      });

      if (!response.ok) {
        try {
          const errText = await response.text();
          console.error('Voice preview server error:', errText.slice(0, 600));
        } catch {}
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Failed to generate preview');
      }

      return `${API_BASE_URL}${data.audio_url}`;
    } catch (error) {
      console.error('Voice preview error:', error);
      return null;
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
    return availableVoices[selectedVoice]?.name || selectedVoice.replace('_', ' ').toUpperCase();
  };

  const getVoiceDescription = () => {
    return availableVoices[selectedVoice]?.description || 'Natural voice synthesis';
  };

  function arrayBufferToBase64(buffer: ArrayBuffer) {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) binary += String.fromCharCode(bytes[i]);
    // @ts-ignore
    return typeof btoa === 'function' ? btoa(binary) : Buffer.from(binary, 'binary').toString('base64');
  }

  return (
    <View style={[styles.container, style]}>
      {/* Voice Info */}
      <View style={styles.voiceInfo}>
        <Text style={styles.voiceName}>{getVoiceDisplayName()}</Text>
        <Text style={styles.voiceDescription}>{getVoiceDescription()}</Text>
      </View>

      {/* Play Buttons */}
      <View style={styles.buttonContainer}>
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

        {/* Preview Button (fallback to synthesize if preview route fails) */}
        <TouchableOpacity
          style={styles.previewButton}
          onPress={async () => {
            try {
              // Try server preview first
              const previewUrl = await previewVoice();
              if (previewUrl) {
                const { sound: previewSound } = await Audio.Sound.createAsync(
                  { uri: previewUrl },
                  { shouldPlay: true }
                );
                previewSound.setOnPlaybackStatusUpdate((status) => {
                  if (status.isLoaded && status.didJustFinish) {
                    previewSound.unloadAsync();
                  }
                });
                return;
              }
            } catch (e) {
              // Fallback to direct synthesize of a short sample
              try {
                const cfg: TTSConfig = {
                  provider: (process.env.EXPO_PUBLIC_TTS_PROVIDER as any) || 'polly',
                  baseUrl: process.env.EXPO_PUBLIC_TTS_BASE_URL || API_BASE_URL,
                  apiKey: process.env.EXPO_PUBLIC_TTS_API_KEY,
                  voiceId: process.env.EXPO_PUBLIC_TTS_VOICE || selectedVoice || 'Joanna',
                  model: process.env.EXPO_PUBLIC_TTS_MODEL,
                  format: 'mp3',
                };
                const sample = process.env.EXPO_PUBLIC_TTS_PREVIEW_SAMPLE || 'This is a quick voice preview.';
                const buf = await synthesize(sample, cfg);
                const b64 = arrayBufferToBase64(buf);
                const path = FileSystem.cacheDirectory + `tts_preview_${Date.now()}.mp3`;
                await FileSystem.writeAsStringAsync(path, b64, { encoding: FileSystem.EncodingType.Base64 });
                const { sound: previewSound } = await Audio.Sound.createAsync(
                  { uri: path },
                  { shouldPlay: true }
                );
                previewSound.setOnPlaybackStatusUpdate((status) => {
                  if (status.isLoaded && status.didJustFinish) {
                    previewSound.unloadAsync();
                  }
                });
                return;
              } catch (fallbackErr) {
                console.error('Preview fallback synth error:', fallbackErr);
              }
            }
          }}
          disabled={isLoading}
          activeOpacity={0.8}
        >
          <LinearGradient
            colors={['#6C5CE7', '#A29BFE']}
            style={styles.previewButtonGradient}
          >
            <Ionicons name="headset" size={20} color="#FFFFFF" />
          </LinearGradient>
        </TouchableOpacity>
      </View>

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
  buttonContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    gap: 16,
  },
  playButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
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
  previewButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
  },
  previewButtonGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 25,
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
