import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface VoiceSettings {
  selectedVoice: string;
  speed: number;
  emotion: string;
}

interface VoiceContextType {
  voiceSettings: VoiceSettings;
  updateVoiceSettings: (settings: Partial<VoiceSettings>) => Promise<void>;
  getSelectedVoice: () => string;
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
      console.error('Failed to load voice settings:', error);
    }
  };

  const updateVoiceSettings = async (newSettings: Partial<VoiceSettings>) => {
    try {
      const updatedSettings = { ...voiceSettings, ...newSettings };
      await AsyncStorage.setItem('voice_settings', JSON.stringify(updatedSettings));
      setVoiceSettings(updatedSettings);
    } catch (error) {
      console.error('Failed to save voice settings:', error);
    }
  };

  const getSelectedVoice = () => {
    return voiceSettings.selectedVoice;
  };

  return (
    <VoiceContext.Provider
      value={{
        voiceSettings,
        updateVoiceSettings,
        getSelectedVoice,
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
