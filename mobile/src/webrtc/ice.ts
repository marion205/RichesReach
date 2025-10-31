import { ENV } from '../config/env';

const ALLOWED_SCHEMES = new Set(['stun:', 'turn:', 'turns:']);

function splitUrls(raw: string): string[] {
  // Accept commas, whitespace, semicolons, newlines
  return raw.split(/[\s,;]+/g).map(s => s.trim()).filter(Boolean);
}

function isAllowed(url: string): boolean {
  const lower = url.toLowerCase();
  return Array.from(ALLOWED_SCHEMES).some(s => lower.startsWith(s));
}

function dedupe<T>(arr: T[]): T[] {
  return Array.from(new Set(arr));
}

export function buildIceServers(opts?: {
  urls?: string | string[];
  username?: string;
  credential?: string;
}): RTCIceServer[] {
  const rawUrls = (Array.isArray(opts?.urls) ? opts?.urls.join(',') : opts?.urls) ?? ENV.TURN_URLS;
  let list = splitUrls(rawUrls || '').filter(isAllowed);
  if (list.length === 0) list = ['stun:stun.l.google.com:19302'];

  const stunUrls: string[] = [];
  const turnUrls: string[] = [];
  for (const u of list) (u.toLowerCase().startsWith('stun:') ? stunUrls : turnUrls).push(u);

  const stunServer: RTCIceServer | undefined = stunUrls.length ? { urls: dedupe(stunUrls) } : undefined;
  const username = (opts?.username ?? ENV.TURN_USERNAME) || '';
  const credential = (opts?.credential ?? ENV.TURN_CREDENTIAL) || '';
  const turnServer: RTCIceServer | undefined = turnUrls.length
    ? username && credential
      ? { urls: dedupe(turnUrls), username, credential }
      : { urls: dedupe(turnUrls) }
    : undefined;

  const iceServers = [stunServer, turnServer].filter(Boolean) as RTCIceServer[];
  try {
    const redacted = iceServers.map(s => ({ urls: s.urls, username: s.username ? '***' : undefined, credential: s.credential ? '***' : undefined }));
    console.log('[ICE] servers', JSON.stringify(redacted, null, 2));
  } catch {}
  return iceServers;
}

export function buildRtcConfig(): RTCConfiguration {
  return { iceServers: buildIceServers(), iceTransportPolicy: 'all' };
}


