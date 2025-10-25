import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  ScrollView,
  Alert,
  Switch,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import LinearGradient from 'expo-linear-gradient';
import VoiceAI from './VoiceAI';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface VoiceAIIntegrationProps {
  visible: boolean;
  onClose: () => void;
  text: string;
  onVoiceSettingsChange?: (settings: VoiceSettings) => void;
}

interface VoiceSettings {
  enabled: boolean;
  voice: string;
  speed: number;
  emotion: string;
  autoPlay: boolean;
}

const defaultVoiceSettings: VoiceSettings = {
  enabled: true,
  voice: 'default',
  speed: 1.0,
  emotion: 'neutral',
  autoPlay: false,
};

export default function VoiceAIIntegration({
  visible,
  onClose,
  text,
  onVoiceSettingsChange,
}: VoiceAIIntegrationProps) {
  const [voiceSettings, setVoiceSettings] = useState<VoiceSettings>(defaultVoiceSettings);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadVoiceSettings();
  }, []);

  const loadVoiceSettings = async () => {
    try {
      const saved = await AsyncStorage.getItem('voice_ai_settings');
      if (saved) {
        const settings = JSON.parse(saved);
        setVoiceSettings({ ...defaultVoiceSettings, ...settings });
      }
    } catch (error) {
      console.error('Failed to load voice settings:', error);
    }
  };

  const saveVoiceSettings = async (newSettings: VoiceSettings) => {
    try {
      await AsyncStorage.setItem('voice_ai_settings', JSON.stringify(newSettings));
      setVoiceSettings(newSettings);
      onVoiceSettingsChange?.(newSettings);
    } catch (error) {
      console.error('Failed to save voice settings:', error);
    }
  };

  const updateSetting = (key: keyof VoiceSettings, value: any) => {
    const newSettings = { ...voiceSettings, [key]: value };
    saveVoiceSettings(newSettings);
  };

  const voiceOptions = [
    {
      id: 'default',
      name: 'Default Finance Voice',
      description: 'Professional, neutral tone',
      icon: 'business',
    },
    {
      id: 'finance_expert',
      name: 'Finance Expert',
      description: 'Authoritative market analysis',
      icon: 'trending-up',
    },
    {
      id: 'friendly_advisor',
      name: 'Friendly Advisor',
      description: 'Warm, approachable guidance',
      icon: 'heart',
    },
    {
      id: 'confident_analyst',
      name: 'Confident Analyst',
      description: 'Strong trading recommendations',
      icon: 'analytics',
    },
  ];

  const emotionOptions = [
    { id: 'neutral', name: 'Neutral', icon: 'remove' },
    { id: 'confident', name: 'Confident', icon: 'checkmark-circle' },
    { id: 'friendly', name: 'Friendly', icon: 'happy' },
    { id: 'analytical', name: 'Analytical', icon: 'calculator' },
    { id: 'encouraging', name: 'Encouraging', icon: 'thumbs-up' },
  ];

  const speedOptions = [
    { value: 0.7, label: 'Slow' },
    { value: 0.9, label: 'Relaxed' },
    { value: 1.0, label: 'Normal' },
    { value: 1.2, label: 'Quick' },
    { value: 1.5, label: 'Fast' },
  ];

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Ionicons name="close" size={24} color="#2C3E50" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Voice AI Settings</Text>
          <View style={styles.placeholder} />
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Voice AI Toggle */}
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="volume-high" size={20} color="#4ECDC4" />
              <Text style={styles.sectionTitle}>Voice AI</Text>
            </View>
            <View style={styles.toggleRow}>
              <Text style={styles.toggleLabel}>Enable Natural Voice</Text>
              <Switch
                value={voiceSettings.enabled}
                onValueChange={(value) => updateSetting('enabled', value)}
                trackColor={{ false: '#E0E0E0', true: '#4ECDC4' }}
                thumbColor={voiceSettings.enabled ? '#FFFFFF' : '#FFFFFF'}
              />
            </View>
          </View>

          {/* Voice Selection */}
          {voiceSettings.enabled && (
            <>
              <View style={styles.section}>
                <View style={styles.sectionHeader}>
                  <Ionicons name="person" size={20} color="#4ECDC4" />
                  <Text style={styles.sectionTitle}>Voice Selection</Text>
                </View>
                {voiceOptions.map((option) => (
                  <TouchableOpacity
                    key={option.id}
                    style={[
                      styles.voiceOption,
                      voiceSettings.voice === option.id && styles.voiceOptionSelected,
                    ]}
                    onPress={() => updateSetting('voice', option.id)}
                  >
                    <View style={styles.voiceOptionContent}>
                      <Ionicons
                        name={option.icon as any}
                        size={24}
                        color={voiceSettings.voice === option.id ? '#4ECDC4' : '#7F8C8D'}
                      />
                      <View style={styles.voiceOptionText}>
                        <Text
                          style={[
                            styles.voiceOptionName,
                            voiceSettings.voice === option.id && styles.voiceOptionNameSelected,
                          ]}
                        >
                          {option.name}
                        </Text>
                        <Text style={styles.voiceOptionDescription}>
                          {option.description}
                        </Text>
                      </View>
                      {voiceSettings.voice === option.id && (
                        <Ionicons name="checkmark-circle" size={20} color="#4ECDC4" />
                      )}
                    </View>
                  </TouchableOpacity>
                ))}
              </View>

              {/* Emotion Selection */}
              <View style={styles.section}>
                <View style={styles.sectionHeader}>
                  <Ionicons name="happy" size={20} color="#4ECDC4" />
                  <Text style={styles.sectionTitle}>Emotion Tone</Text>
                </View>
                <View style={styles.emotionGrid}>
                  {emotionOptions.map((emotion) => (
                    <TouchableOpacity
                      key={emotion.id}
                      style={[
                        styles.emotionOption,
                        voiceSettings.emotion === emotion.id && styles.emotionOptionSelected,
                      ]}
                      onPress={() => updateSetting('emotion', emotion.id)}
                    >
                      <Ionicons
                        name={emotion.icon as any}
                        size={20}
                        color={voiceSettings.emotion === emotion.id ? '#FFFFFF' : '#7F8C8D'}
                      />
                      <Text
                        style={[
                          styles.emotionOptionText,
                          voiceSettings.emotion === emotion.id && styles.emotionOptionTextSelected,
                        ]}
                      >
                        {emotion.name}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              {/* Speed Selection */}
              <View style={styles.section}>
                <View style={styles.sectionHeader}>
                  <Ionicons name="speedometer" size={20} color="#4ECDC4" />
                  <Text style={styles.sectionTitle}>Speech Speed</Text>
                </View>
                <View style={styles.speedGrid}>
                  {speedOptions.map((speed) => (
                    <TouchableOpacity
                      key={speed.value}
                      style={[
                        styles.speedOption,
                        voiceSettings.speed === speed.value && styles.speedOptionSelected,
                      ]}
                      onPress={() => updateSetting('speed', speed.value)}
                    >
                      <Text
                        style={[
                          styles.speedOptionText,
                          voiceSettings.speed === speed.value && styles.speedOptionTextSelected,
                        ]}
                      >
                        {speed.label}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              {/* Auto-play Toggle */}
              <View style={styles.section}>
                <View style={styles.sectionHeader}>
                  <Ionicons name="play-circle" size={20} color="#4ECDC4" />
                  <Text style={styles.sectionTitle}>Auto-play</Text>
                </View>
                <View style={styles.toggleRow}>
                  <Text style={styles.toggleLabel}>Automatically play AI responses</Text>
                  <Switch
                    value={voiceSettings.autoPlay}
                    onValueChange={(value) => updateSetting('autoPlay', value)}
                    trackColor={{ false: '#E0E0E0', true: '#4ECDC4' }}
                    thumbColor={voiceSettings.autoPlay ? '#FFFFFF' : '#FFFFFF'}
                  />
                </View>
              </View>

              {/* Preview */}
              {text && (
                <View style={styles.section}>
                  <View style={styles.sectionHeader}>
                    <Ionicons name="headset" size={20} color="#4ECDC4" />
                    <Text style={styles.sectionTitle}>Preview</Text>
                  </View>
                  <View style={styles.previewContainer}>
                    <Text style={styles.previewText} numberOfLines={3}>
                      {text}
                    </Text>
                    <VoiceAI
                      text={text}
                      voice={voiceSettings.voice as any}
                      speed={voiceSettings.speed}
                      emotion={voiceSettings.emotion as any}
                      style={styles.previewVoiceAI}
                    />
                  </View>
                </View>
              )}
            </>
          )}
        </ScrollView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  closeButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#2C3E50',
  },
  placeholder: {
    width: 40,
  },
  content: {
    flex: 1,
    paddingHorizontal: 16,
  },
  section: {
    marginVertical: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2C3E50',
    marginLeft: 8,
  },
  toggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  toggleLabel: {
    fontSize: 14,
    color: '#2C3E50',
  },
  voiceOption: {
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 8,
    marginBottom: 8,
    padding: 12,
  },
  voiceOptionSelected: {
    borderColor: '#4ECDC4',
    backgroundColor: '#F0FDFC',
  },
  voiceOptionContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  voiceOptionText: {
    flex: 1,
    marginLeft: 12,
  },
  voiceOptionName: {
    fontSize: 14,
    fontWeight: '500',
    color: '#2C3E50',
    marginBottom: 2,
  },
  voiceOptionNameSelected: {
    color: '#4ECDC4',
  },
  voiceOptionDescription: {
    fontSize: 12,
    color: '#7F8C8D',
  },
  emotionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  emotionOption: {
    width: '48%',
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    marginBottom: 8,
  },
  emotionOptionSelected: {
    borderColor: '#4ECDC4',
    backgroundColor: '#4ECDC4',
  },
  emotionOptionText: {
    fontSize: 12,
    color: '#7F8C8D',
    marginTop: 4,
  },
  emotionOptionTextSelected: {
    color: '#FFFFFF',
  },
  speedGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  speedOption: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    marginHorizontal: 2,
  },
  speedOptionSelected: {
    borderColor: '#4ECDC4',
    backgroundColor: '#4ECDC4',
  },
  speedOptionText: {
    fontSize: 12,
    color: '#7F8C8D',
  },
  speedOptionTextSelected: {
    color: '#FFFFFF',
  },
  previewContainer: {
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 8,
    padding: 12,
  },
  previewText: {
    fontSize: 14,
    color: '#2C3E50',
    marginBottom: 12,
    lineHeight: 20,
  },
  previewVoiceAI: {
    marginVertical: 0,
  },
});
