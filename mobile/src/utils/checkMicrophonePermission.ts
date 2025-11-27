/**
 * Microphone Permission Checker
 * Utility to check and log microphone permission status
 */

import { Audio } from 'expo-av';
import logger from './logger';

export interface MicrophonePermissionStatus {
  granted: boolean;
  canAskAgain: boolean;
  status: 'granted' | 'denied' | 'undetermined';
  message: string;
}

/**
 * Check current microphone permission status
 */
export async function checkMicrophonePermission(): Promise<MicrophonePermissionStatus> {
  try {
    const { status, canAskAgain } = await Audio.getPermissionsAsync();
    
    const result: MicrophonePermissionStatus = {
      granted: status === 'granted',
      canAskAgain: canAskAgain ?? true,
      status: status as 'granted' | 'denied' | 'undetermined',
      message: getPermissionMessage(status, canAskAgain),
    };

    logger.log('🎤 Microphone Permission Status:', {
      granted: result.granted,
      status: result.status,
      canAskAgain: result.canAskAgain,
    });

    return result;
  } catch (error) {
    logger.error('❌ Error checking microphone permission:', error);
    return {
      granted: false,
      canAskAgain: false,
      status: 'undetermined',
      message: 'Error checking permission status',
    };
  }
}

/**
 * Request microphone permission
 */
export async function requestMicrophonePermission(): Promise<MicrophonePermissionStatus> {
  try {
    logger.log('🎤 Requesting microphone permission...');
    const { status, canAskAgain } = await Audio.requestPermissionsAsync();
    
    const result: MicrophonePermissionStatus = {
      granted: status === 'granted',
      canAskAgain: canAskAgain ?? true,
      status: status as 'granted' | 'denied' | 'undetermined',
      message: getPermissionMessage(status, canAskAgain),
    };

    if (result.granted) {
      logger.log('✅ Microphone permission granted!');
    } else {
      logger.warn('⚠️ Microphone permission denied');
      if (!result.canAskAgain) {
        logger.warn('⚠️ Permission cannot be asked again - user must enable in Settings');
      }
    }

    return result;
  } catch (error) {
    logger.error('❌ Error requesting microphone permission:', error);
    return {
      granted: false,
      canAskAgain: false,
      status: 'undetermined',
      message: 'Error requesting permission',
    };
  }
}

/**
 * Get user-friendly permission message
 */
function getPermissionMessage(
  status: string,
  canAskAgain: boolean | null
): string {
  switch (status) {
    case 'granted':
      return 'Microphone permission is granted ✅';
    case 'denied':
      if (canAskAgain === false) {
        return 'Microphone permission denied. Please enable in Settings → RichesReach → Microphone';
      }
      return 'Microphone permission denied. The app will ask again.';
    case 'undetermined':
      return 'Microphone permission not yet requested';
    default:
      return `Unknown permission status: ${status}`;
  }
}

/**
 * Check if microphone permission is granted
 */
export async function hasMicrophonePermission(): Promise<boolean> {
  const status = await checkMicrophonePermission();
  return status.granted;
}

