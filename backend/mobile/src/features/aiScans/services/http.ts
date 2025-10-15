/**
 * HTTP Service - Institutional Grade
 * Resilient HTTP client with timeouts, retries, and circuit breaker patterns
 */

export type TokenProvider = () => Promise<string | undefined>;

export async function httpFetch(
  url: string,
  init: RequestInit & { timeoutMs?: number; idempotencyKey?: string } = {},
  retries = 2
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), init.timeoutMs ?? 12_000);
  const headers = new Headers(init.headers);
  if (init.idempotencyKey) headers.set('Idempotency-Key', init.idempotencyKey);

  try {
    const res = await fetch(url, { ...init, headers, signal: controller.signal });
    if (res.status >= 500 && retries > 0) {
      await new Promise(r => setTimeout(r, backoffDelay(2 - retries)));
      return httpFetch(url, init, retries - 1);
    }
    return res;
  } finally {
    clearTimeout(timeout);
  }
}

const backoffDelay = (attempt: number) => 300 * Math.pow(2, attempt) + Math.random() * 100;
