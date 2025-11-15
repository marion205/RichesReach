// src/services/wealthOracleTTS.ts
import { Audio } from "expo-av";
import * as Speech from "expo-speech";
import { TTS_API_BASE_URL } from "../config/api";
import type { StockMoment } from "../components/charts/ChartWithMoments";

let currentSound: Audio.Sound | null = null;
let currentSpeechId: string | null = null;

// Wealth Oracle persona options for expo-speech fallback
const wealthOracleVoiceOptions: Speech.SpeechOptions = {
  language: "en-US",
  rate: 0.9,
  pitch: 1.05,
};

export async function playWealthOracle(
  text: string,
  symbol: string,
  moment: StockMoment,
): Promise<void> {
  // Stop anything currently playing
  await stopWealthOracle();

  // Call your TTS microservice
  try {
    console.log(`[WealthOracleTTS] Attempting to call TTS service: ${TTS_API_BASE_URL}/tts`);
    
    const res = await fetch(`${TTS_API_BASE_URL}/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        voice: "wealth_oracle_v1",
        symbol,
        moment_id: moment.id,
      }),
    });

    if (!res.ok) {
      console.warn(`[WealthOracleTTS] TTS request failed (${res.status}), falling back to expo-speech`);
      // Fallback to expo-speech
      return fallbackToExpoSpeech(text);
    }

    const data = await res.json();
    const audioUrl: string | undefined = data.audio_url;
    if (!audioUrl) {
      console.warn("[WealthOracleTTS] TTS response missing audio_url, falling back to expo-speech");
      // Fallback to expo-speech
      return fallbackToExpoSpeech(text);
    }

    // Load and play audio
    const { sound } = await Audio.Sound.createAsync(
      { uri: audioUrl },
      { shouldPlay: true },
    );
    currentSound = sound;
    
    // Listen for playback finish
    sound.setOnPlaybackStatusUpdate((status) => {
      if (status.isLoaded && status.didJustFinish) {
        currentSound = null;
      }
    });
    
    console.log("[WealthOracleTTS] Playing audio from TTS service");
  } catch (error) {
    console.error("[WealthOracleTTS] Error calling TTS service, falling back to expo-speech:", error);
    // Fallback to expo-speech
    return fallbackToExpoSpeech(text);
  }
}

/**
 * Fallback to expo-speech when TTS service is unavailable
 */
function fallbackToExpoSpeech(text: string): void {
  try {
    console.log("[WealthOracleTTS] Using expo-speech fallback");
    Speech.speak(text, {
      ...wealthOracleVoiceOptions,
      onDone: () => {
        console.log("[WealthOracleTTS] Speech completed");
        currentSpeechId = null;
      },
      onError: (error) => {
        console.error("[WealthOracleTTS] Speech error:", error);
        currentSpeechId = null;
      },
    });
    // Note: expo-speech doesn't return an ID, but we track it for stopping
    currentSpeechId = "speech_active";
  } catch (error) {
    console.error("[WealthOracleTTS] Failed to use expo-speech fallback:", error);
  }
}

export async function stopWealthOracle(): Promise<void> {
  // Stop audio playback
  if (currentSound) {
    try {
      await currentSound.stopAsync();
      await currentSound.unloadAsync();
      console.log("[WealthOracleTTS] Stopped audio playback");
    } catch (error) {
      console.warn("[WealthOracleTTS] Error stopping audio:", error);
    }
    currentSound = null;
  }
  
  // Always try to stop expo-speech (in case it's active from fallback)
  try {
    const isSpeaking = await Speech.isSpeakingAsync();
    if (isSpeaking) {
      Speech.stop();
      console.log("[WealthOracleTTS] Stopped expo-speech");
    }
  } catch (error) {
    // Ignore errors - speech might not be active
  }
  currentSpeechId = null;
}

