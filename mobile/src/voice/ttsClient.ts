import { Platform } from 'react-native';

export type Provider = 'openai' | 'elevenlabs' | 'azure' | 'polly' | 'custom';

export interface TTSConfig {
  provider: Provider;
  baseUrl: string;
  apiKey?: string;
  voiceId?: string;
  region?: string;
  model?: string;
  format?: 'mp3' | 'wav' | 'm4a' | 'ogg';
}

export async function synthesize(text: string, cfg: TTSConfig): Promise<ArrayBuffer> {
  let url = '';
  let method = 'POST';
  let headers: Record<string, string> = {};
  let body: any = null;

  switch (cfg.provider) {
    case 'openai': {
      url = `${cfg.baseUrl.replace(/\/$/, '')}/v1/audio/speech`;
      headers = {
        Authorization: `Bearer ${cfg.apiKey ?? ''}`,
        'Content-Type': 'application/json',
      };
      body = JSON.stringify({
        model: cfg.model ?? 'gpt-4o-mini-tts',
        input: text,
        voice: cfg.voiceId ?? 'alloy',
        format: cfg.format ?? 'mp3',
      });
      break;
    }
    case 'elevenlabs': {
      if (!cfg.voiceId) throw new Error('ElevenLabs requires voiceId');
      url = `${cfg.baseUrl.replace(/\/$/, '')}/v1/text-to-speech/${cfg.voiceId}`;
      headers = {
        'xi-api-key': cfg.apiKey ?? '',
        'Content-Type': 'application/json',
        Accept: 'audio/mpeg',
      };
      body = JSON.stringify({
        text,
        model_id: cfg.model ?? 'eleven_multilingual_v2',
        voice_settings: { stability: 0.4, similarity_boost: 0.8 },
      });
      break;
    }
    case 'azure': {
      if (!cfg.region) throw new Error('Azure TTS requires region');
      url = `https://${cfg.region}.tts.speech.microsoft.com/cognitiveservices/v1`;
      headers = {
        'Ocp-Apim-Subscription-Key': cfg.apiKey ?? '',
        'Content-Type': 'application/ssml+xml',
        'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3',
      };
      const voice = cfg.voiceId ?? 'en-US-JennyNeural';
      body = `<speak version="1.0" xml:lang="en-US"><voice name="${voice}">${escapeXml(
        text,
      )}</voice></speak>`;
      break;
    }
    case 'polly': {
      // Expect a proxy route on your backend
      url = `${cfg.baseUrl.replace(/\/$/, '')}/polly/synthesize`;
      headers = {
        'Content-Type': 'application/json',
        Authorization: cfg.apiKey ?? '',
      };
      body = JSON.stringify({ text, voiceId: cfg.voiceId ?? 'Joanna', format: cfg.format ?? 'mp3' });
      break;
    }
    case 'custom': {
      // Allow overriding the path via env to match server routes
      const customPath = (process?.env as any)?.EXPO_PUBLIC_TTS_PATH || '/api/tts/speak';
      url = `${cfg.baseUrl.replace(/\/$/, '')}${customPath.startsWith('/') ? customPath : `/${customPath}`}`;
      headers = { 'Content-Type': 'application/json' };
      body = JSON.stringify({ text, voice: cfg.voiceId, format: cfg.format ?? 'mp3' });
      break;
    }
  }

  // Loud log (without secrets)
  console.log('🗣️ TTS request:', {
    provider: cfg.provider,
    url,
    method,
    headers: Object.fromEntries(
      Object.entries(headers).map(([k, v]) => [k, k.toLowerCase().includes('key') || k.toLowerCase().includes('auth') ? '***' : v]),
    ),
    bodyPreview: typeof body === 'string' ? body.slice(0, 180) : '[binary]',
    platform: Platform.OS,
  });

  const res = await fetch(url, { method, headers, body });
  if (!res.ok) {
    const textPreview = await safeReadText(res);
    throw new Error(`TTS ${res.status} ${res.statusText} @ ${url} :: ${textPreview}`);
  }
  return await res.arrayBuffer();
}

function escapeXml(s: string) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

async function safeReadText(res: Response) {
  try {
    const t = await res.text();
    return t.slice(0, 500);
  } catch {
    return '<no text body>';
  }
}


