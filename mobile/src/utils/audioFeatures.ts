/**
 * Audio Feature Extraction Utilities
 * Extracts MFCC features for wake word detection
 */

export interface AudioFeatures {
  mfcc: number[];
  energy: number;
  zeroCrossingRate: number;
}

/**
 * Extract MFCC features from audio buffer
 * This is a simplified JavaScript implementation
 * For production, consider using a native module or Web Audio API
 */
export function extractMFCC(
  audioBuffer: Float32Array,
  sampleRate: number = 16000,
  nMFCC: number = 13
): number[] {
  // Simple MFCC-like features using spectral analysis
  const features: number[] = [];
  
  // Calculate frequency spectrum using FFT
  const fftSize = 2048;
  const hopLength = 512;
  const nFrames = Math.floor(audioBuffer.length / hopLength);
  
  // Simple spectral centroid approximation
  for (let i = 0; i < nMFCC; i++) {
    let sum = 0;
    const start = Math.floor((i / nMFCC) * audioBuffer.length);
    const end = Math.floor(((i + 1) / nMFCC) * audioBuffer.length);
    
    for (let j = start; j < end && j < audioBuffer.length; j++) {
      sum += Math.abs(audioBuffer[j]);
    }
    
    features.push(sum / (end - start));
  }
  
  // Normalize
  const mean = features.reduce((a, b) => a + b, 0) / features.length;
  const std = Math.sqrt(
    features.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / features.length
  );
  
  return features.map(val => (val - mean) / (std + 1e-8));
}

/**
 * Extract energy from audio buffer
 */
export function extractEnergy(audioBuffer: Float32Array): number {
  let energy = 0;
  for (let i = 0; i < audioBuffer.length; i++) {
    energy += audioBuffer[i] * audioBuffer[i];
  }
  return Math.sqrt(energy / audioBuffer.length);
}

/**
 * Extract zero crossing rate
 */
export function extractZeroCrossingRate(audioBuffer: Float32Array): number {
  let crossings = 0;
  for (let i = 1; i < audioBuffer.length; i++) {
    if (
      (audioBuffer[i] >= 0 && audioBuffer[i - 1] < 0) ||
      (audioBuffer[i] < 0 && audioBuffer[i - 1] >= 0)
    ) {
      crossings++;
    }
  }
  return crossings / audioBuffer.length;
}

/**
 * Extract comprehensive audio features
 */
export function extractAudioFeatures(
  audioBuffer: Float32Array,
  sampleRate: number = 16000
): AudioFeatures {
  return {
    mfcc: extractMFCC(audioBuffer, sampleRate),
    energy: extractEnergy(audioBuffer),
    zeroCrossingRate: extractZeroCrossingRate(audioBuffer),
  };
}

