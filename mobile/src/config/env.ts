type OptStr = string | undefined | null;
const pick = (v: OptStr) => (typeof v === 'string' ? v.trim() : '');

// Optional runtime validation with zod (won't crash if not installed)
let ENV: {
  SIGNAL_URL: string;
  WS_URL?: string;
  API_BASE_URL: string;
  AUTH_REFRESH_PATH?: string;
  AUTH_REFRESH_MODE?: string;
  TURN_URLS: string;
  TURN_USERNAME: string;
  TURN_CREDENTIAL: string;
};

try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { z } = require('zod');
  const Schema = z.object({
    EXPO_PUBLIC_SIGNAL_URL: z.string().url(),
    EXPO_PUBLIC_WS_URL: z.string().url().optional(),
    EXPO_PUBLIC_API_BASE_URL: z.string().url().optional(),
    EXPO_PUBLIC_AUTH_REFRESH_PATH: z.string().optional(),
    EXPO_PUBLIC_AUTH_REFRESH_MODE: z.enum(['cookie', 'header']).optional(),
    EXPO_PUBLIC_TURN_URLS: z.string().min(1),
    EXPO_PUBLIC_TURN_USERNAME: z.string().optional(),
    EXPO_PUBLIC_TURN_CREDENTIAL: z.string().optional(),
  });
  const raw = {
    EXPO_PUBLIC_SIGNAL_URL: process.env.EXPO_PUBLIC_SIGNAL_URL,
    EXPO_PUBLIC_WS_URL: process.env.EXPO_PUBLIC_WS_URL,
    EXPO_PUBLIC_API_BASE_URL: process.env.EXPO_PUBLIC_API_BASE_URL,
    EXPO_PUBLIC_AUTH_REFRESH_PATH: process.env.EXPO_PUBLIC_AUTH_REFRESH_PATH,
    EXPO_PUBLIC_AUTH_REFRESH_MODE: process.env.EXPO_PUBLIC_AUTH_REFRESH_MODE,
    EXPO_PUBLIC_TURN_URLS: process.env.EXPO_PUBLIC_TURN_URLS,
    EXPO_PUBLIC_TURN_USERNAME: process.env.EXPO_PUBLIC_TURN_USERNAME,
    EXPO_PUBLIC_TURN_CREDENTIAL: process.env.EXPO_PUBLIC_TURN_CREDENTIAL,
  };
  const res = Schema.safeParse(raw);
  if (!res.success) {
    if (__DEV__) console.warn('Env validation issues:', res.error.flatten().fieldErrors);
  }
  const d: any = res.success ? res.data : raw;
  ENV = {
    SIGNAL_URL: d.EXPO_PUBLIC_SIGNAL_URL || '',
    WS_URL: d.EXPO_PUBLIC_WS_URL || undefined,
    API_BASE_URL: d.EXPO_PUBLIC_API_BASE_URL || '',
    AUTH_REFRESH_PATH: d.EXPO_PUBLIC_AUTH_REFRESH_PATH || '/auth/refresh',
    AUTH_REFRESH_MODE: d.EXPO_PUBLIC_AUTH_REFRESH_MODE || 'cookie',
    TURN_URLS: d.EXPO_PUBLIC_TURN_URLS || '',
    TURN_USERNAME: d.EXPO_PUBLIC_TURN_USERNAME || '',
    TURN_CREDENTIAL: d.EXPO_PUBLIC_TURN_CREDENTIAL || '',
  };
} catch {
  ENV = {
    SIGNAL_URL: pick(process.env.EXPO_PUBLIC_SIGNAL_URL),
    WS_URL: pick(process.env.EXPO_PUBLIC_WS_URL) || undefined,
    API_BASE_URL: pick(process.env.EXPO_PUBLIC_API_BASE_URL),
    AUTH_REFRESH_PATH: pick(process.env.EXPO_PUBLIC_AUTH_REFRESH_PATH) || '/auth/refresh',
    AUTH_REFRESH_MODE: pick(process.env.EXPO_PUBLIC_AUTH_REFRESH_MODE) || 'cookie',
    TURN_URLS: (pick(process.env.EXPO_PUBLIC_TURN_URLS) || ''),
    TURN_USERNAME: pick(process.env.EXPO_PUBLIC_TURN_USERNAME) || '',
    TURN_CREDENTIAL: pick(process.env.EXPO_PUBLIC_TURN_CREDENTIAL) || '',
  };
}

export { ENV };


