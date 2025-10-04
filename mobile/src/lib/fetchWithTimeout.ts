// fetchWithTimeout - Wraps fetch with timeout and abort controller
// React Native's fetch has no built-in timeout, so we implement it here

export async function fetchWithTimeout(
  input: RequestInfo | URL,
  init: RequestInit = {},
  timeoutMs = 8000
): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  
  try {
    const response = await fetch(input, { 
      ...init, 
      signal: controller.signal 
    });
    return response;
  } finally {
    clearTimeout(id);
  }
}
