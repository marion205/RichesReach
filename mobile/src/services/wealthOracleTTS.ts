// src/services/wealthOracleTTS.ts
import { Audio } from "expo-av";
import * as Speech from "expo-speech";
import { TTS_API_BASE_URL } from "../config/api";
import type { StockMoment } from "../components/charts/ChartWithMoments";
import logger from "../utils/logger";

let currentSound: Audio.Sound | null = null;
let currentSpeechId: string | null = null;
let isPlaying = false; // Track if we're currently playing to prevent double playback

// Wealth Oracle persona options for expo-speech fallback
const wealthOracleVoiceOptions: Speech.SpeechOptions = {
  language: "en-US",
  rate: 0.9,
  pitch: 1.05,
};

// Max text length for TTS (prevent accidentally passing novels)
// Increased to allow full paragraphs to be read
const MAX_TTS_LENGTH = 5000; // ~800 words, enough for most story moments

// Request timeout in milliseconds
// Increased for longer text (5000 chars can take 5-10 seconds to generate)
const TTS_TIMEOUT_MS = 15000; // 15 seconds - enough for 5000 char audio generation

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
  onComplete?: () => void,
): Promise<void> {
  // CRITICAL: Stop anything currently playing FIRST
  // This prevents double playback
  await stopWealthOracle();
  
  // Set playing flag to prevent race conditions
  isPlaying = true;

  // Guard: Truncate text if too long
  const truncatedText = text.length > MAX_TTS_LENGTH 
    ? text.substring(0, MAX_TTS_LENGTH) + "..."
    : text;
  
  if (text.length > MAX_TTS_LENGTH) {
    logger.warn(`[WealthOracleTTS] Text truncated from ${text.length} to ${MAX_TTS_LENGTH} chars`);
  }

  // Skip health check on first call - just try TTS directly with fast timeout
  // This eliminates the health check delay entirely
  // Only use cached health check result if we have one
  
  const useCachedHealth = ttsServiceAvailable !== null && 
    (Date.now() - ttsHealthCheckTime) < TTS_HEALTH_CHECK_TTL;
  
  if (useCachedHealth && !ttsServiceAvailable) {
    // We know service is down from cache, skip immediately
    logger.log(`[WealthOracleTTS] TTS service known to be unavailable, using expo-speech immediately`);
    return fallbackToExpoSpeech(truncatedText, onComplete);
  }

  // Try TTS directly with very fast timeout - no health check delay
  try {
    logger.log(`[WealthOracleTTS] Attempting TTS service: ${TTS_API_BASE_URL}/tts`);
    logger.log(`[WealthOracleTTS] Text length: ${text.length} chars, truncated: ${truncatedText.length} chars`);
    
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
      logger.warn(`[WealthOracleTTS] TTS request failed (${res.status}), falling back to expo-speech`);
      // IMPORTANT: Stop any audio that might be playing before fallback
      await stopWealthOracle();
      return fallbackToExpoSpeech(truncatedText, onComplete);
    }
    
    // Cache that service is up
    ttsServiceAvailable = true;
    ttsHealthCheckTime = Date.now();

    const data = await res.json();
    const audioUrl: string | undefined = data.audio_url;
    if (!audioUrl) {
      logger.warn("[WealthOracleTTS] TTS response missing audio_url, falling back to expo-speech");
      ttsServiceAvailable = false;
      ttsHealthCheckTime = Date.now();
      // IMPORTANT: Stop any audio that might be playing before fallback
      await stopWealthOracle();
      return fallbackToExpoSpeech(truncatedText, onComplete);
    }

    // IMPORTANT: Stop expo-speech before playing TTS service audio
    // This prevents both voices from playing simultaneously
    try {
      const isSpeaking = await Speech.isSpeakingAsync();
      if (isSpeaking) {
        Speech.stop();
        logger.log("[WealthOracleTTS] Stopped expo-speech before playing TTS service audio");
      }
    } catch (error) {
      // Ignore errors
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
        isPlaying = false;
        // Notify completion callback
        if (onComplete) {
          logger.log("[WealthOracleTTS] Audio playback completed, calling onComplete");
          onComplete();
        }
      }
    });
    
    logger.log("[WealthOracleTTS] Playing audio from TTS service");
    // Don't reset isPlaying here - let it reset when audio finishes or stops
  } catch (error) {
    // Cache that service is down
    ttsServiceAvailable = false;
    ttsHealthCheckTime = Date.now();
    
    // Handle timeout specifically
    if (error instanceof Error && error.name === 'AbortError') {
      logger.warn("[WealthOracleTTS] TTS request timed out (2s), falling back to expo-speech immediately");
    } else {
      logger.warn("[WealthOracleTTS] TTS error, falling back to expo-speech:", error instanceof Error ? error.message : error);
    }
    // IMPORTANT: Stop any audio that might be playing before fallback
    await stopWealthOracle();
    // Fallback to expo-speech immediately
    return fallbackToExpoSpeech(truncatedText, onComplete);
  }
}

/**
 * Fallback to expo-speech when TTS service is unavailable
 */
function fallbackToExpoSpeech(text: string, onComplete?: () => void): void {
  try {
    // IMPORTANT: Stop any TTS service audio before using expo-speech
    // This prevents both voices from playing simultaneously
    if (currentSound) {
      currentSound.stopAsync().catch(() => {});
      currentSound.unloadAsync().catch(() => {});
      currentSound = null;
      logger.log("[WealthOracleTTS] Stopped TTS service audio before using expo-speech fallback");
    }
    
    // Only proceed if we're still supposed to be playing
    if (!isPlaying) {
      logger.log("[WealthOracleTTS] Not playing anymore, skipping expo-speech fallback");
      return;
    }
    
    logger.log("[WealthOracleTTS] Using expo-speech fallback");
    logger.log(`[WealthOracleTTS] Fallback text length: ${text.length} chars`);
    Speech.speak(text, {
      ...wealthOracleVoiceOptions,
      onDone: () => {
        logger.log("[WealthOracleTTS] Speech completed");
        currentSpeechId = null;
        isPlaying = false;
        // Notify completion callback
        if (onComplete) {
          logger.log("[WealthOracleTTS] Expo-speech completed, calling onComplete");
          onComplete();
        }
      },
      onError: (error) => {
        logger.error("[WealthOracleTTS] Speech error:", error);
        currentSpeechId = null;
        isPlaying = false;
        // Still call onComplete on error so story can advance
        if (onComplete) {
          onComplete();
        }
      },
    });
    // Note: expo-speech doesn't return an ID, but we track it for stopping
    currentSpeechId = "speech_active";
  } catch (error) {
    logger.error("[WealthOracleTTS] Failed to use expo-speech fallback:", error);
    isPlaying = false;
  }
}

export async function stopWealthOracle(): Promise<void> {
  // Set flag first to prevent new playback
  isPlaying = false;
  
  // Stop audio playback
  if (currentSound) {
    try {
      await currentSound.stopAsync();
      await currentSound.unloadAsync();
      logger.log("[WealthOracleTTS] Stopped audio playback");
    } catch (error) {
      logger.warn("[WealthOracleTTS] Error stopping audio:", error);
    }
    currentSound = null;
  }
  
  // Always try to stop expo-speech (in case it's active from fallback)
  try {
    const isSpeaking = await Speech.isSpeakingAsync();
    if (isSpeaking) {
      Speech.stop();
      logger.log("[WealthOracleTTS] Stopped expo-speech");
    }
  } catch (error) {
    // Ignore errors - speech might not be active
  }
  currentSpeechId = null;
}

