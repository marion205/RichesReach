import * as SecureStore from 'expo-secure-store';
import { ENV } from '../config/env';

type JwtResp = { access: string };
const ACCESS_KEY = 'jwt_access';
const REFRESH_KEY = 'jwt_refresh';
const REFRESH_PATH = ENV.AUTH_REFRESH_PATH || '/auth/refresh';
const REFRESH_MODE = (ENV.AUTH_REFRESH_MODE || 'cookie') as 'cookie' | 'header';

export async function refreshJwt(): Promise<string> {
  const url = `${ENV.API_BASE_URL.replace(/\/$/, '')}${REFRESH_PATH}`;
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const init: RequestInit = { method: 'POST', headers };
  if (REFRESH_MODE === 'cookie') {
    init.credentials = 'include';
  } else {
    const refresh = (await SecureStore.getItemAsync(REFRESH_KEY)) || '';
    if (!refresh) throw new Error('missing refresh token');
    headers.Authorization = `Bearer ${refresh}`;
  }
  const r = await fetch(url, init);
  if (!r.ok) throw new Error(`refresh failed ${r.status}`);
  const data: JwtResp = await r.json();
  if (!data?.access) throw new Error('no access token in response');
  await SecureStore.setItemAsync(ACCESS_KEY, data.access);
  return data.access;
}

export async function getJwt(): Promise<string> {
  let t = await SecureStore.getItemAsync(ACCESS_KEY);
  if (!t) t = await refreshJwt();
  return t!;
}


