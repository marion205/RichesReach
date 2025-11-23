/**
 * Helper function to get front camera stream for WebRTC
 * 
 * This is for use with react-native-webrtc (requires dev build, not Expo Go)
 * 
 * Usage:
 *   import { getFrontCameraStream } from './services/liveStream/getFrontCameraStream';
 *   const stream = await getFrontCameraStream();
 */
import { isExpoGo } from '../../utils/expoGoCheck';
import logger from '../../utils/logger';

// Conditionally import WebRTC (not available in Expo Go)
let mediaDevices: any = null;
let MediaStream: any = null;

try {
  if (!isExpoGo()) {
    const webrtc = require('react-native-webrtc');
    mediaDevices = webrtc.mediaDevices;
    MediaStream = webrtc.MediaStream;
  }
} catch (e) {
  logger.warn('react-native-webrtc not available (Expo Go mode)');
}

export interface CameraStreamOptions {
  width?: { min: number; ideal: number; max: number };
  height?: { min: number; ideal: number; max: number };
  frameRate?: { min: number; ideal: number; max: number };
}

/**
 * Get front camera stream for WebRTC
 * 
 * This function:
 * 1. Enumerates devices to find front camera
 * 2. Forces front camera using facingMode: 'user'
 * 3. Falls back to deviceId if facingMode doesn't work
 * 
 * @param options - Optional camera constraints
 * @returns Promise<MediaStream> - Front camera stream
 * @throws Error if WebRTC is not available or camera access fails
 */
export async function getFrontCameraStream(
  options?: CameraStreamOptions
): Promise<MediaStream> {
  if (!mediaDevices || !MediaStream) {
    throw new Error(
      'react-native-webrtc is not available. This requires a dev build, not Expo Go.'
    );
  }

  logger.log('🎥 [getFrontCameraStream] Starting front camera stream...');

  try {
    // Step 1: Enumerate devices to find front camera
    logger.log('🎥 [getFrontCameraStream] Enumerating devices...');
    const devices = await mediaDevices.enumerateDevices();
    const videoDevices = devices.filter(
      (d: any) => d.kind === 'videoinput'
    );

    logger.log(
      `🎥 [getFrontCameraStream] Found ${videoDevices.length} video devices`
    );

    // Find front camera by label or facing property
    const frontCamera = videoDevices.find(
      (device: any) =>
        (device.label || '').toLowerCase().includes('front') ||
        (device.label || '').toLowerCase().includes('facing') ||
        device.facing === 'front' ||
        device.facing === 'user'
    );

    // Step 2: Build constraints with front camera preference
    const videoConstraints: any = {
      width: options?.width || { min: 640, ideal: 1280, max: 1920 },
      height: options?.height || { min: 480, ideal: 720, max: 1080 },
      frameRate: options?.frameRate || { min: 15, ideal: 30, max: 30 },
      facingMode: 'user', // Primary method: force front camera
    };

    // If we found a specific front camera device, use its deviceId for precision
    if (frontCamera && frontCamera.deviceId) {
      videoConstraints.deviceId = { exact: frontCamera.deviceId };
      // Remove facingMode if deviceId is used to avoid conflicts
      delete videoConstraints.facingMode;
      logger.log(
        `✅ [getFrontCameraStream] Using specific front camera: ${frontCamera.label || 'NO LABEL'}`
      );
    } else {
      logger.log(
        '⚠️ [getFrontCameraStream] No specific front camera found, using facingMode: user'
      );
    }

    logger.log(
      `🎥 [getFrontCameraStream] Video constraints:`,
      JSON.stringify(videoConstraints, null, 2)
    );

    // Step 3: Get user media with front camera constraints
    const stream = await mediaDevices.getUserMedia({
      video: videoConstraints,
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    logger.log('✅ [getFrontCameraStream] Front camera stream obtained');
    logger.log(`✅ [getFrontCameraStream] Stream ID: ${stream.id}`);

    // Log stream tracks for debugging
    stream.getTracks().forEach((track: any) => {
      logger.log(
        `✅ [getFrontCameraStream] Track: kind=${track.kind}, id=${track.id}, enabled=${track.enabled}, readyState=${track.readyState}`
      );
      if (track.kind === 'video') {
        const settings = track.getSettings();
        logger.log(
          `✅ [getFrontCameraStream] Video settings: facingMode=${settings.facingMode}, deviceId=${settings.deviceId?.substring(0, 20) + '...'}, width=${settings.width}, height=${settings.height}`
        );
      }
    });

    return stream;
  } catch (error: any) {
    logger.error('❌ [getFrontCameraStream] Failed to get front camera stream');
    logger.error('❌ [getFrontCameraStream] Error:', error?.message || error);
    throw new Error(
      `Failed to get front camera stream: ${error?.message || 'Unknown error'}`
    );
  }
}

/**
 * Check if WebRTC front camera is available
 * 
 * @returns boolean - True if WebRTC is available and can access front camera
 */
export function isFrontCameraAvailable(): boolean {
  return !isExpoGo() && mediaDevices !== null && MediaStream !== null;
}

