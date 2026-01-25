/**
 * useSafeSpeak Hook
 * Prevents TTS memory leaks and crashes by:
 * - Ensuring only one speech at a time
 * - Proper cleanup on unmount
 * - Guarding against render loops
 */

import { useEffect, useRef } from 'react';
import * as Speech from 'expo-speech';
import logger from '../utils/logger';

interface SpeakOptions {
  language?: string;
  pitch?: number;
  rate?: number;
  voice?: string;
  onDone?: () => void;
  onStopped?: () => void;
  onError?: (error: any) => void;
}

export function useSafeSpeak(text?: string, deps: any[] = []) {
  const speaking = useRef(false);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      if (speaking.current) {
        try {
          Speech.stop();
        } catch (e) {
          // Ignore errors during cleanup
        }
        speaking.current = false;
      }
    };
  }, []);

  useEffect(() => {
    if (!text || !mounted.current) return;
    
    let cancelled = false;

    (async () => {
      try {
        // Check if already speaking
        if (speaking.current) {
          try {
            const isSpeaking = await Speech.isSpeakingAsync();
            if (isSpeaking) {
              await Speech.stop();
              // Small delay to let stop complete
              await new Promise(resolve => setTimeout(resolve, 100));
            }
          } catch (e) {
            // Ignore errors checking speaking status
          }
        }

        if (cancelled || !mounted.current) return;

        speaking.current = true;
        
        await Speech.speak(text, {
          language: 'en-US',
          pitch: 1.0,
          rate: 0.9,
          onDone: () => {
            if (mounted.current) {
              speaking.current = false;
            }
          },
          onStopped: () => {
            if (mounted.current) {
              speaking.current = false;
            }
          },
          onError: () => {
            if (mounted.current) {
              speaking.current = false;
            }
          },
        });
      } catch (error) {
        logger.warn('[useSafeSpeak] Error:', error);
        if (mounted.current) {
          speaking.current = false;
        }
      }
    })();

    return () => {
      cancelled = true;
      if (speaking.current) {
        try {
          Speech.stop();
        } catch (e) {
          // Ignore cleanup errors
        }
        speaking.current = false;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps.length > 0 ? deps : [text]);
}

/**
 * Safe speak function - use this instead of direct Speech.speak()
 */
let globalSpeaking = false;
let globalSpeechQueue: Array<{ text: string; options?: SpeakOptions }> = [];

export async function safeSpeak(text: string, options?: SpeakOptions): Promise<void> {
  if (!text) return;

  try {
    // If already speaking, stop current speech first
    if (globalSpeaking) {
      try {
        const isSpeaking = await Speech.isSpeakingAsync();
        if (isSpeaking) {
          await Speech.stop();
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      } catch (e) {
        // Ignore errors
      }
    }

    globalSpeaking = true;

    await Speech.speak(text, {
      language: 'en-US',
      pitch: 1.0,
      rate: 0.9,
      ...options,
      onDone: () => {
        globalSpeaking = false;
        options?.onDone?.();
      },
      onStopped: () => {
        globalSpeaking = false;
        options?.onStopped?.();
      },
      onError: (error) => {
        globalSpeaking = false;
        options?.onError?.(error);
      },
    });
  } catch (error) {
    logger.warn('[safeSpeak] Error:', error);
    globalSpeaking = false;
    options?.onError?.(error);
  }
}

/**
 * Stop all speech immediately
 */
export async function stopAllSpeech(): Promise<void> {
  try {
    globalSpeaking = false;
    await Speech.stop();
  } catch (e) {
    // Ignore errors
  }
}

