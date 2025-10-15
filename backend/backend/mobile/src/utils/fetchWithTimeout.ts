/**
 * Cross-platform fetch with timeout for React Native
 * Replaces AbortSignal.timeout which is not available in RN
 */

export async function fetchWithTimeout(
  input: RequestInfo, 
  init: RequestInit = {}, 
  ms = 12000
): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), ms);
  
  try {
    const res = await fetch(input, { ...init, signal: controller.signal });
    return res;
  } finally {
    clearTimeout(id);
  }
}