import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import logger from '../utils/logger';

interface VoiceSettings {
  selectedVoice: string;
  speed: number;
  emotion: string;
}

interface VoiceContextType {
  voiceSettings: VoiceSettings;
  updateVoiceSettings: (settings: Partial<VoiceSettings>) => Promise<void>;
  getSelectedVoice: () => string;
  selectedVoice: { id: string; name: string; description: string };
  getVoiceParameters: (voiceId: string) => { pitch: number; rate: number };
}

const VoiceContext = createContext<VoiceContextType | undefined>(undefined);

const defaultVoiceSettings: VoiceSettings = {
  selectedVoice: 'alloy',
  speed: 1.0,
  emotion: 'neutral',
};

interface VoiceProviderProps {
  children: ReactNode;
}

export function VoiceProvider({ children }: VoiceProviderProps) {
  const [voiceSettings, setVoiceSettings] = useState<VoiceSettings>(defaultVoiceSettings);

  useEffect(() => {
    loadVoiceSettings();
  }, []);

  const loadVoiceSettings = async () => {
    try {
      const saved = await AsyncStorage.getItem('voice_settings');
      if (saved) {
        const settings = JSON.parse(saved);
        setVoiceSettings({ ...defaultVoiceSettings, ...settings });
      }
    } catch (error) {
      logger.error('Failed to load voice settings:', error);
    }
  };

  const updateVoiceSettings = async (newSettings: Partial<VoiceSettings>) => {
    try {
      const updatedSettings = { ...voiceSettings, ...newSettings };
      await AsyncStorage.setItem('voice_settings', JSON.stringify(updatedSettings));
      setVoiceSettings(updatedSettings);
    } catch (error) {
      logger.error('Failed to save voice settings:', error);
    }
  };

  const getSelectedVoice = () => {
    return voiceSettings.selectedVoice;
  };

  const getVoiceParameters = (voiceId: string) => {
    // Return default voice parameters based on voice ID
    const voiceParams: { [key: string]: { pitch: number; rate: number } } = {
      'alloy': { pitch: 1.0, rate: 1.0 },
      'echo': { pitch: 1.1, rate: 0.9 },
      'fable': { pitch: 0.9, rate: 1.1 },
      'onyx': { pitch: 0.8, rate: 0.9 },
      'nova': { pitch: 1.2, rate: 1.1 },
      'shimmer': { pitch: 1.1, rate: 0.8 },
    };
    return voiceParams[voiceId] || { pitch: 1.0, rate: 1.0 };
  };

  const selectedVoice = voiceOptions.find(voice => voice.id === voiceSettings.selectedVoice) || voiceOptions[0];

  return (
    <VoiceContext.Provider
      value={{
        voiceSettings,
        updateVoiceSettings,
        getSelectedVoice,
        selectedVoice,
        getVoiceParameters,
      }}
    >
      {children}
    </VoiceContext.Provider>
  );
}

export function useVoice() {
  const context = useContext(VoiceContext);
  if (context === undefined) {
    throw new Error('useVoice must be used within a VoiceProvider');
  }
  return context;
}

export const voiceOptions = [
  { id: 'alloy', name: 'Alloy', description: 'Neutral, professional voice' },
  { id: 'echo', name: 'Echo', description: 'Warm, conversational voice' },
  { id: 'fable', name: 'Fable', description: 'Clear, authoritative voice' },
  { id: 'onyx', name: 'Onyx', description: 'Deep, serious voice' },
  { id: 'nova', name: 'Nova', description: 'Bright, energetic voice' },
  { id: 'shimmer', name: 'Shimmer', description: 'Soft, empathetic voice' },
];
