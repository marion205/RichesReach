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

// Max text length for TTS (prevent accidentally passing novels)
const MAX_TTS_LENGTH = 1500;

// Request timeout in milliseconds (very fast for immediate fallback)
const TTS_TIMEOUT_MS = 2000; // 2 seconds max

// Cache TTS service availability to avoid repeated failed requests
let ttsServiceAvailable: boolean | null = null;
let ttsHealthCheckTime: number = 0;
const TTS_HEALTH_CHECK_TTL = 60000; // Check every 60 seconds

/**
 * Quick health check for TTS service (very fast - 500ms max)
 */
async function checkTTSServiceHealth(): Promise<boolean> {
  const now = Date.now();
  
  // Use cached result if recent
  if (ttsServiceAvailable !== null && (now - ttsHealthCheckTime) < TTS_HEALTH_CHECK_TTL) {
    return ttsServiceAvailable;
  }

  // Fast health check with very short timeout
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 500); // Very fast - 500ms max
    
    const res = await fetch(`${TTS_API_BASE_URL}/health`, {
      method: "GET",
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    ttsServiceAvailable = res.ok;
    ttsHealthCheckTime = now;
    return ttsServiceAvailable;
  } catch (error) {
    // If health check fails, assume service is down
    ttsServiceAvailable = false;
    ttsHealthCheckTime = now;
    return false;
  }
}

export async function playWealthOracle(
  text: string,
  symbol: string,
  moment: StockMoment,
): Promise<void> {
  // Stop anything currently playing
  await stopWealthOracle();

  // Guard: Truncate text if too long
  const truncatedText = text.length > MAX_TTS_LENGTH 
    ? text.substring(0, MAX_TTS_LENGTH) + "..."
    : text;
  
  if (text.length > MAX_TTS_LENGTH) {
    console.warn(`[WealthOracleTTS] Text truncated from ${text.length} to ${MAX_TTS_LENGTH} chars`);
  }

  // Skip health check on first call - just try TTS directly with fast timeout
  // This eliminates the health check delay entirely
  // Only use cached health check result if we have one
  
  const useCachedHealth = ttsServiceAvailable !== null && 
    (Date.now() - ttsHealthCheckTime) < TTS_HEALTH_CHECK_TTL;
  
  if (useCachedHealth && !ttsServiceAvailable) {
    // We know service is down from cache, skip immediately
    console.log(`[WealthOracleTTS] TTS service known to be unavailable, using expo-speech immediately`);
    return fallbackToExpoSpeech(truncatedText);
  }

  // Try TTS directly with very fast timeout - no health check delay
  try {
    console.log(`[WealthOracleTTS] Attempting TTS service: ${TTS_API_BASE_URL}/tts`);
    
    // Create abort controller with fast timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TTS_TIMEOUT_MS);
    
    const res = await fetch(`${TTS_API_BASE_URL}/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: truncatedText,
        voice: "wealth_oracle_v1",
        symbol,
        moment_id: moment.id,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      // Cache that service is down
      ttsServiceAvailable = false;
      ttsHealthCheckTime = Date.now();
      console.warn(`[WealthOracleTTS] TTS request failed (${res.status}), falling back to expo-speech`);
      return fallbackToExpoSpeech(truncatedText);
    }
    
    // Cache that service is up
    ttsServiceAvailable = true;
    ttsHealthCheckTime = Date.now();

    const data = await res.json();
    const audioUrl: string | undefined = data.audio_url;
    if (!audioUrl) {
      console.warn("[WealthOracleTTS] TTS response missing audio_url, falling back to expo-speech");
      ttsServiceAvailable = false;
      ttsHealthCheckTime = Date.now();
      return fallbackToExpoSpeech(truncatedText);
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
    // Cache that service is down
    ttsServiceAvailable = false;
    ttsHealthCheckTime = Date.now();
    
    // Handle timeout specifically
    if (error instanceof Error && error.name === 'AbortError') {
      console.warn("[WealthOracleTTS] TTS request timed out (2s), falling back to expo-speech immediately");
    } else {
      console.warn("[WealthOracleTTS] TTS error, falling back to expo-speech:", error instanceof Error ? error.message : error);
    }
    // Fallback to expo-speech immediately
    return fallbackToExpoSpeech(truncatedText);
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

