import { isExpoGo } from '../utils/expoGoCheck';

// WebRTC is not available in Expo Go - make conditional
let RTCPeerConnection: any = null;

try {
  if (!isExpoGo()) {
    // Only import in development build
    const webrtc = require('react-native-webrtc');
    RTCPeerConnection = webrtc.RTCPeerConnection;
  }
} catch (e) {
  console.warn('react-native-webrtc not available (Expo Go mode)');
}

import { buildRtcConfig } from './ice';

export function createPeer() {
  if (!RTCPeerConnection) {
    throw new Error('WebRTC not available in Expo Go. Build a development client to use WebRTC features.');
  }
  
  const pc = new RTCPeerConnection(buildRtcConfig());
  pc.onicecandidate = e => {
    // Hook up to signaling in screen/service
    console.log('[RTC] candidate', e.candidate ? 'present' : 'null');
  };
  pc.onconnectionstatechange = () => {
    console.log('[RTC] state:', pc.connectionState);
  };
  return pc;
}

// Export check function
export const isWebRTCAvailable = () => RTCPeerConnection !== null;


